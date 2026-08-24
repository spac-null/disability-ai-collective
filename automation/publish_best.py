#!/usr/bin/env python3
"""
publish_best.py — promote the top-scoring draft to _posts/ every 2 days.

Candidate pool: drafts dated within the last AGE_WINDOW_DAYS days that pass
the promotion gate below. A draft that ages out of that window without ever
being selected is archived to _drafts/_archive/ rather than left to compete
forever.

Promotion gate (legacy-draft auto-promotion fail-closed closure, 2026-08-16):
a draft must show BOTH an explicit fact_check_status: verified (bullet A,
_ordinary_eligibility_ok) AND a publication_safety_version proving it was
generated under -- and cleared -- the CURRENT publication-safety contract
(bullet B, _current_safety_contract_ok), not just some past pipeline version.
Anything failing either bullet is HELD (NEEDS_CURRENT_REVALIDATION): left on
disk in _drafts/, untouched, excluded from this cycle's scoring, never
archived or rewritten by this gate alone. UNKNOWN safety != safe -- see
REQUIRED_SAFETY_VERSION's own comment for the incident this responds to.

Selection weights (applied only to drafts that pass the promotion gate):
  - draft_score (0-10 editorial score from Opus, or default 7.0 if missing): 60%
    NOTE (2026-08-06 audit): production_orchestrator.py only writes draft_score
    when its conditional editorial pass fires (~1 in 3 articles) — in practice
    this term is DEFAULT_SCORE (a constant) for the large majority of real
    candidates, so freshness/rotation/aging usually do the actual deciding
    despite the 60% weight on paper. Tracked as an open decision (make the
    editorial pass unconditional, at the cost of an extra Opus call/article, or
    treat this weight as aspirational) — not resolved by this note.
  - topic freshness (1.0 if topic not seen in last 14 days, 0.5 if seen):     25%
  - persona rotation (1.0 if persona not in last 5 published, 0.5 if in last 2,
    0.75 if in last 5 but not last 2, 0.0 if in last 1): 15%
  - aging bonus: +0.15 per prior losing cycle (tracked via publish_attempts
    in front matter), capped at +0.6 — prevents a merely-decent draft from
    being perpetually outcompeted by fresher entries and archived without
    ever really winning a fair fight.

Cron (trident): 0 8 */2 * * python3 /srv/scripts/ops/publish_best.py

Usage:
  publish_best.py            Run for real: publish the best draft, archive expired ones.
  publish_best.py --dry-run  Show the scoring table and what would happen. No writes,
                              no git actions, no moves. Safe to run to inspect state.
"""

import argparse, pathlib, re, shutil, subprocess, sys
from datetime import datetime, timedelta

REPO = pathlib.Path(__file__).parent.parent
DRAFTS = REPO / "_drafts"
POSTS = REPO / "_posts"
ARCHIVE = DRAFTS / "_archive"
DEFAULT_SCORE = 7.0
TOPIC_WINDOW_DAYS = 14
PERSONA_WINDOW = 5  # look at last N published articles for persona rotation
AGE_WINDOW_DAYS = 7  # drafts older than this without being picked get archived
LOSS_BONUS = 0.15    # per prior losing cycle
LOSS_BONUS_CAP = 0.6

# Legacy-draft auto-promotion fail-closed closure (2026-08-16 -- see the
# "Reached by Boat or Plane" remediation audit: an Era-D draft generated
# 2026-08-11, three days before AP1/APE2 and five before PS1 existed,
# promoted itself on 2026-08-15 on nothing but a five-day-old
# fact_check_status: verified stamp, with zero re-check against whatever
# safety code was current at promotion time). Mirrors generate.py's
# PUBLICATION_SAFETY_CONTRACT_VERSION -- kept as a separate constant rather
# than a shared import, matching this script's existing standalone-script
# style (it has never imported anything from automation.orchestrator, by
# design; see _fire_pending_social's subprocess call for how it reaches the
# orchestrator instead, only AFTER promotion, only to fire social posts).
REQUIRED_SAFETY_VERSION = 1


def parse_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm


def post_date(p):
    """Real publication date: front-matter `date:` (rewritten by set_publish_date
    on promotion), falling back to the filename's YYYY-MM-DD prefix if missing or
    malformed. The filename prefix is the draft's *write* date, not publication
    order — set_publish_date rewrites `date:` but never renames the file, so a
    draft written days before it wins its scoring cycle keeps an old filename
    while carrying its real publish date only in front matter."""
    fm = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
    d = fm.get("date", "")[:10]
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", d):
        d = p.name[:10]
    return d


def recent_posts(n=None):
    posts = sorted(POSTS.glob("*.md"), key=post_date, reverse=True)
    return posts if n is None else posts[:n]


def published_titles_since(days):
    cutoff = datetime.now() - timedelta(days=days)
    titles = set()
    for p in recent_posts():
        try:
            pub_date = datetime.strptime(post_date(p), "%Y-%m-%d")
        except ValueError:
            continue
        if pub_date < cutoff:
            break
        fm = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
        title = fm.get("title", "").lower()
        if title:
            titles.add(title)
    return titles


def recent_personas(n):
    personas = []
    for p in recent_posts(n):
        fm = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
        author = fm.get("author", "")
        if author:
            personas.append(author)
    return personas


def topic_keywords(title):
    stopwords = {"the", "a", "an", "of", "in", "on", "at", "to", "is", "are",
                 "and", "or", "but", "for", "not", "this", "that", "with", "from"}
    words = re.findall(r"[a-z]+", title.lower())
    return {w for w in words if w not in stopwords and len(w) > 3}


def topic_freshness(draft_title, published_titles):
    draft_kws = topic_keywords(draft_title)
    for pub_title in published_titles:
        pub_kws = topic_keywords(pub_title)
        if len(draft_kws & pub_kws) >= 2:
            return 0.5
    return 1.0


def persona_score(draft_persona, last_personas):
    # last_personas holds up to PERSONA_WINDOW entries — the module docstring
    # promises "1.0 if persona not in last 5 published", but this used to only
    # ever look at the first two, so a persona seen 3-5 publications back scored
    # a full 1.0, identical to one never seen at all.
    if not last_personas:
        return 1.0
    if last_personas[0] == draft_persona:
        return 0.0  # same as most recent — penalise heavily
    if draft_persona in last_personas[:2]:
        return 0.5
    if draft_persona in last_personas:
        return 0.75  # seen within the window, but not recently
    return 1.0


def composite_score(editorial, freshness, persona, aging_bonus=0.0):
    # All components on 0-10 scale: editorial is already 0-10,
    # freshness and persona (0-1) scaled ×10 before weighting. Max total = 10.
    return editorial * 0.6 + freshness * 10 * 0.25 + persona * 10 * 0.15 + aging_bonus


def draft_date(path):
    """Parse the YYYY-MM-DD prefix from a draft filename. Returns None if absent/invalid."""
    m = re.match(r"(\d{4}-\d{2}-\d{2})", path.name)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%Y-%m-%d")
    except ValueError:
        return None


def bump_attempts(path, fm):
    """Increment publish_attempts in a draft's front matter (adds the field if missing)."""
    try:
        attempts = int(fm.get("publish_attempts", 0) or 0)
    except (ValueError, TypeError):
        attempts = 0
    attempts += 1
    text = path.read_text(encoding="utf-8", errors="replace")
    if re.search(r"^publish_attempts:.*$", text, re.MULTILINE):
        text = re.sub(r"^publish_attempts:.*$", f"publish_attempts: {attempts}", text, count=1, flags=re.MULTILINE)
    else:
        text = re.sub(r"^---\n", f"---\npublish_attempts: {attempts}\n", text, count=1)
    path.write_text(text, encoding="utf-8")


def archive_draft(path):
    ARCHIVE.mkdir(exist_ok=True)
    shutil.move(str(path), str(ARCHIVE / path.name))


def _current_engine_ineligible(fm):
    """CURRENT_ENGINE candidates must carry an EXPLICIT publication_eligible: true.

    Legacy candidates are untouched by this rule -- they have no engine_generation and
    keep their existing eligibility semantics exactly. For a CURRENT_ENGINE candidate,
    anything other than a clear true (false, missing, malformed, a stray string) means
    the publication-safety bridge did not grant eligibility, so the selector skips it.
    Fail-closed by construction: the ONLY passing value is an explicit true.
    """
    if str(fm.get("engine_generation", "")).strip() != "CURRENT_ENGINE":
        return False, ""
    v = fm.get("publication_eligible")
    if v is True or (isinstance(v, str) and v.strip().lower() == "true"):
        return False, ""
    return True, ("publication_eligible=%r (CURRENT_ENGINE requires an explicit true "
                  "granted by the publication-safety bridge)" % (v,))


def _interlocked(fm):
    """True if a draft is explicitly withheld from publication by the cutover interlock.

    Reads BOTH fields so either one alone is sufficient, and treats the string forms
    YAML frontmatter can yield ("true"/"false") the same as real booleans -- the
    eligible-flag lesson from the legacy commission contract: a representation
    difference must not decide a safety question.
    """
    def _is_true(v):
        return v is True or (isinstance(v, str) and v.strip().lower() == "true")

    def _is_false(v):
        return v is False or (isinstance(v, str) and v.strip().lower() == "false")

    return _is_true(fm.get("cutover_rehearsal")) or _is_false(fm.get("publication_eligible"))


def _ordinary_eligibility_ok(fm):
    """Bullet (A) of the promotion gate (legacy-draft auto-promotion
    fail-closed closure, 2026-08-16): fact_check_status must be the EXPLICIT
    literal "verified" -- not merely "anything other than blocked". A missing
    field, a typo'd value, or any other legacy value all now read as NOT
    eligible, never as an implicit pass. This replaces the old bare
    `!= "blocked"` check, which is what let a draft with no fact_check_status
    at all -- or a five-day-stale "verified" from a since-superseded safety
    regime -- promote unexamined. UNKNOWN must never read as SAFE."""
    return fm.get("fact_check_status") == "verified"


def _current_safety_contract_ok(fm):
    """Bullet (B) of the promotion gate: the draft must carry a
    publication_safety_version stamped by generate.py's CURRENT code (i.e.
    an integer >= REQUIRED_SAFETY_VERSION), proving every mandatory
    authoritative check in TODAY's safety contract (fable_brief, gate_llm,
    the persona-biography fail-closed check, the fact-check pass) actually
    ran and resolved clean on THIS draft -- not merely that some past
    pipeline version, possibly missing checks that exist today, once
    approved it. Missing/unparseable/too-low all read as NOT current-safe;
    there is no implicit-pass path here either."""
    try:
        version = int(fm.get("publication_safety_version", "") or "0")
    except (ValueError, TypeError):
        version = 0
    return version >= REQUIRED_SAFETY_VERSION


def set_publish_date(path, when):
    """Rewrite the front matter `date:` field to the actual promotion date.

    Drafts keep their original write date until promoted — without this, a
    draft written days ago and picked today keeps sorting (and permalinking,
    per :year/:month/:day in _config.yml) at its old date, so it never shows
    as the newest post despite going live today.
    """
    new_date = when.strftime("%Y-%m-%d")
    text = path.read_text(encoding="utf-8", errors="replace")
    if re.search(r"^date:.*$", text, re.MULTILINE):
        text = re.sub(r"^date:.*$", f"date: {new_date}", text, count=1, flags=re.MULTILINE)
    else:
        text = re.sub(r"^---\n", f"---\ndate: {new_date}\n", text, count=1)
    path.write_text(text, encoding="utf-8")


def main(dry_run=False):
    if dry_run:
        print("[DRY RUN — no files will be moved, no git actions will run]\n")

    drafts = sorted(d for d in DRAFTS.glob("*.md") if d.is_file())
    if not drafts:
        print("No drafts to publish.")
        return 0

    now = datetime.now()
    in_window, expired = [], []
    for draft in drafts:
        age = draft_date(draft)
        # draft_date() is midnight, so a draft written exactly AGE_WINDOW_DAYS ago
        # yields .days == AGE_WINDOW_DAYS, which a strict > lets survive one extra
        # cycle despite the log/commit message both promising "Nd" as the cutoff.
        if age is not None and (now - age).days >= AGE_WINDOW_DAYS:
            expired.append(draft)
        else:
            in_window.append(draft)

    pub_titles = published_titles_since(TOPIC_WINDOW_DAYS)
    last_personas = recent_personas(PERSONA_WINDOW)

    candidates = []
    for draft in in_window:
        text = draft.read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(text)
        if fm.get("fact_check_status") == "blocked":
            print(f"  {draft.name}: SKIPPED — fact_check_status: blocked "
                  f"(quote attributed to a real person not found in any source; needs human review)")
            continue
        # PUBLICATION-SAFETY INTERLOCK (cutover preparation, 2026-08-24).
        # An EXPLICIT deterministic exclusion, checked before anything else. A
        # NEW_ENGINE_V1 candidate written during cutover rehearsal carries
        # cutover_rehearsal: true and publication_eligible: false. Those drafts are
        # also missing fact_check_status/publication_safety_version and would be held
        # anyway -- but exclusion must not depend on a field HAPPENING to be absent,
        # so it is stated positively here. Cadence and ranking are untouched.
        _ce_bad, _ce_why = _current_engine_ineligible(fm)
        if _ce_bad:
            print(f"  {draft.name}: SKIPPED (CURRENT_ENGINE_NOT_ELIGIBLE) — {_ce_why}; "
                  f"engine={fm.get('editorial_engine')} "
                  f"profile={fm.get('publication_safety_profile')}")
            continue
        if _interlocked(fm):
            print(f"  {draft.name}: SKIPPED (PUBLICATION_INTERLOCK) — "
                  f"cutover_rehearsal={fm.get('cutover_rehearsal')!r} "
                  f"publication_eligible={fm.get('publication_eligible')!r}; "
                  f"engine={fm.get('editorial_engine') or 'legacy'}; not selector-eligible")
            continue
        if not _ordinary_eligibility_ok(fm):
            print(f"  {draft.name}: HELD (NEEDS_CURRENT_REVALIDATION) — fact_check_status is "
                  f"{fm.get('fact_check_status')!r}, not the required explicit \"verified\"; "
                  f"remains in _drafts/ for later remediation, not archived or altered")
            continue
        if not _current_safety_contract_ok(fm):
            print(f"  {draft.name}: HELD (NEEDS_CURRENT_REVALIDATION) — publication_safety_version="
                  f"{fm.get('publication_safety_version')!r} (requires >= {REQUIRED_SAFETY_VERSION}); "
                  f"generated before, or not fully checked under, the current publication-safety "
                  f"contract; remains in _drafts/ for later remediation, not archived or altered")
            continue
        try:
            editorial = float(fm.get("draft_score", DEFAULT_SCORE))
        except (ValueError, TypeError):
            editorial = DEFAULT_SCORE
        try:
            attempts = int(fm.get("publish_attempts", 0) or 0)
        except (ValueError, TypeError):
            attempts = 0
        title = fm.get("title", draft.stem)
        persona = fm.get("author", "")
        fresh = topic_freshness(title, pub_titles)
        prot = persona_score(persona, last_personas)
        aging_bonus = min(attempts * LOSS_BONUS, LOSS_BONUS_CAP)
        score = composite_score(editorial, fresh, prot, aging_bonus)
        candidates.append((score, draft, editorial, fresh, prot, title, persona, fm))
        print(f"  {draft.name}: editorial={editorial:.1f} fresh={fresh:.1f} persona_rot={prot:.1f} "
              f"aging=+{aging_bonus:.2f} (attempts={attempts}) → {score:.2f}")

    published = False
    dest = None
    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        best_score, best_draft, editorial, fresh, prot, title, persona, _fm = candidates[0]

        dest = POSTS / best_draft.name
        verb = "Would publish" if dry_run else "Publishing"
        print(f"\n{verb}: {best_draft.name}")
        print(f"  Title: {title}")
        print(f"  Persona: {persona}")
        print(f"  Score: editorial={editorial:.1f} freshness={fresh:.1f} rotation={prot:.1f} → {best_score:.2f}")

        if dest.exists():
            print(f"ERROR: {dest.name} already exists in _posts/ — aborting to avoid overwrite.", file=sys.stderr)
            return 1

        if dry_run:
            print(f"  (dry-run: {len(candidates) - 1} other candidate(s) would have their aging counter bumped)")
        else:
            shutil.move(str(best_draft), str(dest))
            set_publish_date(dest, now)
            published = True

            # Every other in-window candidate just lost this cycle — bump its aging counter.
            for _score, draft, *_rest, fm in candidates[1:]:
                bump_attempts(draft, fm)
    else:
        print("No scoreable drafts in the last %d days." % AGE_WINDOW_DAYS)

    archived = []
    for draft in expired:
        verb = "Would archive" if dry_run else "Archiving"
        print(f"{verb} (unpublished after {AGE_WINDOW_DAYS}+ days): {draft.name}")
        if not dry_run:
            archive_draft(draft)
            archived.append(draft.name)

    if dry_run:
        return 0

    if not published and not archived:
        return 0

    try:
        if dest:
            subprocess.run(["git", "add", str(dest)], cwd=str(REPO), check=True)
        if archived:
            subprocess.run(["git", "add", str(ARCHIVE)], cwd=str(REPO), check=True)
        # Stage deletions/moves in _drafts (moved-out files show as deletes) and
        # the publish_attempts bumps on any remaining drafts.
        subprocess.run(["git", "add", "-A", str(DRAFTS)], cwd=str(REPO), check=False)

        msg_parts = []
        if published:
            msg_parts.append(f"publish: {dest.stem}")
        if archived:
            msg_parts.append(f"archive {len(archived)} draft(s) unpublished after {AGE_WINDOW_DAYS}d")
        subprocess.run(
            ["git", "commit", "-m", " | ".join(msg_parts)],
            cwd=str(REPO), check=True
        )
        # Pull --rebase then push
        subprocess.run(["git", "pull", "--rebase", "origin", "main"], cwd=str(REPO), check=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=str(REPO), check=True)
        print("Pushed to GitHub — site building now.")
    except subprocess.CalledProcessError as e:
        print(f"Git error: {e}", file=sys.stderr)
        return 1

    # Fire social posts now that the article is live
    if published:
        _fire_pending_social(dest.stem, dest)

    return 0


def _fire_pending_social(stem, article_file):
    """Trigger social posting via orchestrator for the newly promoted article."""
    social_file = REPO / "_social" / f"{stem[11:]}.json"  # strip YYYY-MM-DD- prefix
    if not social_file.exists():
        return
    import json as _json
    try:
        data = _json.loads(social_file.read_text())
    except Exception:
        return
    if not data.get("pending_social"):
        return
    print("Firing social posts via orchestrator...")
    result = subprocess.run(
        ["python3", str(REPO / "automation" / "production_orchestrator.py"),
         "--post-social", str(article_file)],
        cwd=str(REPO), capture_output=True, text=True
    )
    if result.returncode == 0:
        print("Social posts sent.")
        # Re-read: the subprocess (_store_social_uri) just wrote bsky_uri/agent
        # into this file. Reusing the pre-subprocess `data` here would clobber
        # that write back to its pre-post state.
        try:
            data = _json.loads(social_file.read_text())
        except Exception:
            pass
        data["pending_social"] = False
        social_file.write_text(_json.dumps(data, indent=2))
    else:
        print(f"Social posting failed (non-critical): {result.stderr[:200]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Promote the top-scoring draft to _posts/ every 2 days."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show the scoring table and what would happen. No writes, no git actions."
    )
    args = parser.parse_args()
    sys.exit(main(dry_run=args.dry_run))
