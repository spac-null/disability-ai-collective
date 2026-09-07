#!/usr/bin/env python3
"""
publish_best.py — the deterministic publisher, and the legacy/manual backlog selector.

TWO JOBS, AND THEY ARE NOT THE SAME JOB (2026-09-07).

(1) PUBLICATION MECHANICS, for both engines. promote_candidate() moves one settled
    article into _posts and does everything publication requires of it — date, art
    direction, illustration, exact-run audit retention with its rollback — and
    _commit_and_push() stages exactly what was mutated and pushes it. publish_candidate()
    is the deterministic entry point: ONE named accepted CURRENT_ENGINE article, no pool,
    no score, no comparison, called by new_engine_production the moment the engine
    accepts it. Editorial eligibility is decided upstream and consumed here; see
    terminal_authorization for the four assertions that is allowed to make.

(2) THE LEGACY/MANUAL BACKLOG SELECTOR — main(), everything below, unchanged. Drafts
    that predate the CURRENT_ENGINE bridge have no upstream verdict to consume, so for
    them the pool, the promotion gate and the scoring below are still the only thing
    standing between a stale draft and the public site. CURRENT_ENGINE articles are
    excluded from all of it (CURRENT_ENGINE_DIRECT_PUBLISH_ONLY) — not scored, not aged,
    not archived. Recovering the existing CURRENT_ENGINE backlog is a separate owner
    decision and this cron does not take it.

Everything from here down describes (2).

Candidate pool: legacy/manual drafts dated within the last AGE_WINDOW_DAYS days that
pass the promotion gate below. A draft that ages out of that window without ever
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

import argparse, json, pathlib, re, shutil, subprocess, sys
from datetime import datetime, timedelta

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

# The publication audit store. A sibling module in this same directory, imported the
# way this standalone script imports gen_images: no orchestrator dependency.
import publication_audit as PA                                       # noqa: E402

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


# ── STAGING WHAT THIS RUN ACTUALLY MUTATED ──────────────────────────────────────────
# Every path this run changes is recorded in `mutated` and staged from that list alone.
# The list holds BOTH sides of every move: the destination that now exists, and the
# source that no longer does. That is deliberate -- for a TRACKED source, git only
# records the removal if the old path is named -- but it is also what crashed the
# publisher (2026-09-07).
#
# CURRENT_ENGINE drafts are persisted UNTRACKED. After `shutil.move` the old _drafts
# path is gone AND was never in the index, so `git add -A -- <that path>` is a pathspec
# matching nothing on disk and nothing in the index: git exits 128, the commit never
# happens, and the article is left sitting in _posts/ untracked. Two articles were
# stranded that way.
#
# The rule below fixes it without going back to `git add -A _drafts`, which is the
# other failure (2026-08-29, ab322bb: staging a directory swept two untracked drafts
# the publisher had never touched into a public commit). Per path, exactly:
#
#   exists after the mutation            -> stage it
#   gone, but WAS tracked                -> stage it, so the deletion/move is recorded
#   gone, and was NEVER tracked          -> do not hand it to git at all
#
# So an untracked CURRENT_ENGINE move stages only its destination, a tracked legacy
# move still stages its deletion, and nothing this run did not touch can enter the
# commit either way.

def _git_tracked(path):
    """Is this path in git's index? A file that has just been moved away is still
    tracked -- `ls-files` reads the index, not the working tree -- which is exactly the
    distinction the staging rule needs."""
    return subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", str(path)],
        cwd=str(REPO), capture_output=True,
    ).returncode == 0


def stageable_paths(mutated):
    """The subset of `mutated` that git can be given as a pathspec without failing."""
    out = []
    for raw in sorted(set(mutated)):
        if pathlib.Path(raw).exists() or _git_tracked(raw):
            out.append(raw)
    return out


def _current_engine_direct_publish_only(fm):
    """CURRENT_ENGINE articles do not compete for publication (2026-09-07).

    THE OWNERSHIP CHANGE. CURRENT_ENGINE decides editorial eligibility, and an ACCEPT
    that the publication-safety bridge marked eligible is published directly by the
    production run that composed it -- see publish_candidate, called from
    new_engine_production. By the time such an article could appear in this pool, the
    question this pool asks has already been answered by someone entitled to answer it.

    WHY EXCLUSION AND NOT JUST "IT WILL NEVER GET HERE". Two reasons, both real. A
    direct publication that failed mechanically leaves its candidate in _drafts/, and
    that candidate must not be silently swept into a competition it was never meant to
    enter -- a mechanical failure is not an editorial demotion. And the existing
    CURRENT_ENGINE backlog, including whatever the thirteen blocked runs left behind,
    must not start auto-publishing the moment the retention gate stops refusing it:
    recovering those is a separate owner decision, deliberately not taken here.

    So: skipped, named, and left completely alone. Not scored, not aged, not archived,
    not rewritten. Legacy and manual drafts keep the pool exactly as it was.
    """
    if not PA.is_current_engine(fm):
        return False, ""
    return True, ("CURRENT_ENGINE articles are published directly by the run that "
                  "composed them (engine_run=%r, engine_decision=%r, "
                  "publication_eligible=%r); this selector is the legacy/manual "
                  "backlog only and does not publish them"
                  % (str(fm.get("engine_run", "") or ""),
                     str(fm.get("engine_decision", "") or ""),
                     fm.get("publication_eligible")))


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


def _current_engine_strict_fact_check_missing(fm):
    """CURRENT_ENGINE-only defense in depth (2026-08-25). Metadata validation only --
    this re-runs NO fact check, it just refuses to trust an unsupported claim.

    The bridge already refuses to stamp publication_eligible/fact_check_status without a
    real strict world-relative fact check. This is the second lock on the same door: a
    CURRENT_ENGINE candidate must ALSO carry the strict evidence itself --
    fact_check_extraction_status: ok and fact_check_claims_extracted > 0. A candidate
    written by an older/unfixed bridge, hand-edited, or copied from another run cannot
    satisfy that, so `verified` alone can no longer buy selection.

    Why it exists: on 2026-08-25 a candidate carried publication_eligible: true and
    fact_check_status: verified while its claim extraction had actually raised. Both of
    those fields were true-looking and unearned. The selector had no way to tell.

    Legacy candidates (no engine_generation) are untouched -- they return (False, "")
    before any field here is read, and keep their existing eligibility semantics exactly.
    """
    if str(fm.get("engine_generation", "")).strip() != "CURRENT_ENGINE":
        return False, ""
    raw_status = fm.get("fact_check_extraction_status")
    if str(raw_status or "").strip().lower() != "ok":
        return True, ("fact_check_extraction_status=%r (CURRENT_ENGINE requires \"ok\" -- "
                      "positive proof the strict world-relative claim extraction actually "
                      "succeeded; an extraction failure must never read as verified)"
                      % (raw_status,))
    raw_n = fm.get("fact_check_claims_extracted")
    try:
        n = int(raw_n)
    except (TypeError, ValueError):
        n = 0
    if n <= 0:
        return True, ("fact_check_claims_extracted=%r (CURRENT_ENGINE requires > 0 -- zero "
                      "claims means nothing was checked against the world)" % (raw_n,))
    return False, ""


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


def _retention_ok(fm):
    """Bullet (C) of the promotion gate (published run retention, 2026-09-06, issue #91).

    A CURRENT_ENGINE draft may only be promoted if the run that produced it still exists
    can genuinely be retained -- it resolves, it reads, there is something in it to keep.
    Two live articles had already been published with no retainable run at all, and
    neither could have its factual path reconstructed afterwards by anyone. A published
    article whose producing run cannot be kept is a state this publisher refuses to
    enter.

    What it does NOT require (corrected 2026-09-07) is that the run carry one
    composition engine's Safety filenames. As a precondition that was impossible: no
    recorded production run has ever satisfied it, so this bullet refused every
    CURRENT_ENGINE candidate that reached it. The run is retained in full either way and
    the bundle manifest states plainly whether deterministic Safety replay is possible
    from it.

    Held, not archived and not rewritten, exactly like the two bullets above it: the
    draft stays in _drafts/ and an operator can see why. Legacy drafts -- no
    `engine_generation: CURRENT_ENGINE` -- pass straight through, because the era they
    were written in genuinely had no run to retain and inventing one would be worse than
    admitting it.
    """
    return PA.retention_feasible(fm)


# ── ART DIRECTION, AT THIS SAME BOUNDARY ────────────────────────────────────────────
# art_director.py shipped dormant: a validated module with no caller, which on this site
# is indistinguishable from a module that does not work. This is the whole of its wiring.
#
# WHY HERE AND NOWHERE ELSE. Illustration already happens at promotion, for both engines,
# in one place. Putting art direction anywhere upstream would make it a composition stage
# -- something an article's text could depend on -- and it is not one. It reads the
# settled article and returns a brief for the images that article is about to get.
#
# SAME RUN OR NOTHING. Architecture and the visual sidecar are read from the exact run
# this article names in its own front matter, resolved through the publication-audit
# resolver the promotion gate already used. There is no search for a latest run and no
# scan of run history: an architecture borrowed from a different article is worse than no
# architecture, because it is confidently about the wrong world.


def _same_run_dir(fm):
    """The one run that produced THIS article, or None. Never a nearest match."""
    if not PA.is_current_engine(fm):
        return None
    run_id = str(fm.get("engine_run", "") or "").strip()
    if not run_id:
        return None
    return PA.find_run_dir(run_id)


def _run_json(run_dir, name):
    """Optional context. Missing, unreadable and malformed are one answer: absent."""
    if run_dir is None:
        return None
    try:
        data = json.loads((run_dir / name).read_text(encoding="utf-8", errors="replace"))
    except Exception:                                                 # noqa: BLE001
        return None
    return data if isinstance(data, dict) else None


def article_body(text):
    """The settled prose, as published. Not reconstructed from the writer, the
    architecture or any earlier draft -- the bytes that are about to go live."""
    m = re.match(r"^---\n.*?\n---\n?", text, re.DOTALL)
    return (text[m.end():] if m else text).strip()


def art_direct_for(post_path, provider=None):
    """ONE art-direction call for one canonical publication. Returns (brief, arch, note).

    `brief is None` means the caller takes the legacy image path, which is byte-for-byte
    what it was before this function existed. Art direction improves an image set; its
    absence is never a reason an article does not publish, so every failure here -- no
    run, no provider, a refused brief, a transport fault -- returns None and says why.

    A brief with `image_count: 0` is NOT one of those failures. It is the art director
    answering that this article wants no illustration, and it is returned as the brief it
    is. Reading zero as failure would restore the fixed three-image recipe on exactly the
    articles the module was built to spare.
    """
    text = post_path.read_text(encoding="utf-8", errors="replace")
    fm = parse_frontmatter(text)
    run_dir = _same_run_dir(fm)
    if run_dir is None:
        return None, None, "no resolvable CURRENT_ENGINE run — legacy image path"
    arch = _run_json(run_dir, "ARCHITECTURE.json")
    sidecar = _run_json(run_dir, "VISUAL_OBSERVATIONS.json")
    try:
        import art_director as AD
        if provider is None:
            from new_engine_v1 import provider as NEP
            provider = NEP.Provider()
        out = AD.art_direct(provider, article_body(text),
                            title=fm.get("title", ""), dek=fm.get("dek", ""),
                            arch=arch, persona=fm.get("author", ""),
                            visual_sidecar=sidecar)
    except Exception as e:                                            # noqa: BLE001
        return None, None, "unavailable (%s: %s) — legacy image path" % (
            type(e).__name__, str(e)[:120])
    if not isinstance(out, dict) or not out.get("ok") \
            or not isinstance(out.get("brief"), dict):
        # `out` is checked for shape as well as verdict: an art director that returns
        # None instead of its envelope must fall back here, not raise into the caller
        # and cost the article its images on the way past.
        reason = out.get("reason") if isinstance(out, dict) else None
        return None, None, "no usable brief (%s) — legacy image path" % (
            reason or "art director returned none")
    brief = out["brief"]
    return brief, arch, "run %s — %s image(s), architecture=%s visual_context=%s" % (
        fm.get("engine_run", ""), brief.get("image_count"),
        "yes" if arch else "no", "yes" if brief.get("visual_context_used") else "no")


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



# ── THE DETERMINISTIC PUBLICATION MECHANICS, OWNED IN ONE PLACE ─────────────────────
# Extracted verbatim from main()'s promotion branch (2026-09-07) so that a CURRENT_ENGINE
# article, which no longer competes in any pool, reaches EXACTLY the same mechanics the
# selector has always used. Not a reimplementation and deliberately not a second one:
# the alternative is two publication paths that drift, and the site would then carry
# articles published two different ways with no way to tell which.
#
# This function decides NOTHING editorial. It is handed one settled article and moves it.

def promote_candidate(draft, dest, now):
    """Move ONE named draft into _posts and do everything publication requires of it.

    Returns {"ok", "dest", "mutated", "assets", "image_failure", "reason"}. On a
    retention failure it performs the existing rollback -- the post goes back to
    _drafts/, this run's generated assets are removed -- and returns ok False. It never
    stages, never commits and never pushes: that is the caller's half, because the
    caller is the one that knows what else belongs in the same commit.
    """
    generated_assets: list[str] = []
    image_failure = None
    mutated: list[str] = []
    shutil.move(str(draft), str(dest))
    set_publish_date(dest, now)
    mutated += [str(dest), str(draft)]      # created, and moved out of

    # ILLUSTRATE HERE, AT THE ONE BOUNDARY BOTH ENGINES CROSS. Illustration used
    # to live inside the legacy composition path (orchestrator/generate.py calls
    # generate_images, orchestrator/publish.py calls _insert_images_balanced).
    # Story Architecture has neither call, so from the 2026-09-05 cutover every
    # CURRENT_ENGINE article published unillustrated and nothing said so.
    #
    # Doing it at promotion rather than inside either engine means one
    # implementation serves both. It cannot double-generate: gen_images skips a
    # post that already carries an `image:` field, and illustrate_post leaves a
    # body that already has figures alone -- so a legacy article that illustrated
    # itself upstream passes straight through untouched.
    try:
        import gen_images
        if gen_images.has_image_field(dest.read_text()):
            print("  images: already illustrated upstream — leaving as is")
        else:
            # ONE art-direction call, and only for a resolvable CURRENT_ENGINE
            # publication. No brief -- for any reason -- and the next line is the
            # one that has always been here.
            ad_brief, ad_arch, ad_note = art_direct_for(dest)
            print("  art direction: %s" % ad_note)
            if ad_brief is None:
                res = gen_images.illustrate_post(dest)
            else:
                res = gen_images.illustrate_post(dest, brief=ad_brief, arch=ad_arch)
            if res["ok"]:
                print("  images: %d generated, %d placed in body"
                      % (len(res["assets"]), res["figures"]))
                mutated += res["assets"]
                generated_assets += res["assets"]
            else:
                # NEVER SILENT. Illustrations are part of the normal publication
                # contract, so an article going out without them is reported here
                # and on stderr rather than discovered weeks later on the site.
                image_failure = res["reason"]
                print("  images: FAILED — %s" % image_failure)
                print("PUBLISHING WITHOUT ILLUSTRATIONS: %s (%s)"
                      % (dest.name, image_failure), file=sys.stderr)
    except Exception as e:                                # noqa: BLE001
        image_failure = "%s: %s" % (type(e).__name__, str(e)[:160])
        print("  images: FAILED — %s" % image_failure)
        print("PUBLISHING WITHOUT ILLUSTRATIONS: %s (%s)"
              % (dest.name, image_failure), file=sys.stderr)

    # ── PUBLISHED RUN RETENTION, AT THE BOUNDARY ────────────────────────
    # Here, and not earlier: the bundle must be assembled from the bytes that
    # actually publish, which means after the date rewrite and after the
    # illustrations went into the body. The promotion gate has already proved
    # the run exists and carries what Safety takes, so this is the copy, not
    # the decision.
    #
    # FAIL CLOSED. If the bundle cannot be written, the publication is UNDONE:
    # the post goes back to _drafts/, the assets this run generated are
    # removed, nothing is committed and nothing is pushed. An article on the
    # site whose factual path cannot be re-audited is the failure this exists
    # to prevent, and publishing one anyway because the copy step broke would
    # be that failure with a log line attached.
    try:
        man = PA.retain(dest)
        print("  audit: retained %s (%s) — safety re-audit: %s"
              % (man["bundle_id"], man["class"],
                 man["reaudit"]["SAFETY"]["kind"]))
        mutated.append(str(dest))       # the pointer was stamped into it
    except Exception as e:                                    # noqa: BLE001
        print("  audit: RETENTION FAILED — %s: %s"
              % (type(e).__name__, str(e)[:300]), file=sys.stderr)
        shutil.move(str(dest), str(draft))
        for a in generated_assets:
            try:
                pathlib.Path(a).unlink()
            except OSError:
                pass
        print("PUBLICATION ROLLED BACK: %s returned to _drafts/ — an article "
              "whose audit inputs cannot be retained is not published."
              % draft.name, file=sys.stderr)
        return {"ok": False, "dest": None, "mutated": [], "assets": [],
                "image_failure": image_failure,
                "reason": "retention failed: %s: %s" % (type(e).__name__, str(e)[:300])}
    return {"ok": True, "dest": dest, "mutated": mutated, "assets": generated_assets,
            "image_failure": image_failure, "reason": ""}


# ── TERMINAL AUTHORIZATION FOR A DIRECT CURRENT_ENGINE PUBLICATION ──────────────────
# ONE OWNER OF EDITORIAL ELIGIBILITY, AND IT IS NOT THIS FILE. CURRENT_ENGINE decides
# whether an article may be published; by the time a candidate reaches here that
# decision is already made, recorded in the run, and stamped into the article's own
# front matter. What this checks is that the object handed to the publisher IS that
# decided object -- not whether the decision was correct.
#
# So the contract is four assertions and none of them re-derive editorial judgement:
#
#   this is a CURRENT_ENGINE article
#   engine_decision is ACCEPT
#   publication_eligible is an explicit true
#   the exact engine_run resolves AND is retainable
#
# The last one is publication INTEGRITY, not editorial re-judgement: an article whose
# producing run cannot be kept is one nobody can ever audit, and that is a property of
# the filesystem, not of the article's quality.
#
# WHAT IS DELIBERATELY ABSENT. _ordinary_eligibility_ok, _current_safety_contract_ok,
# _current_engine_strict_fact_check_missing and _interlocked are NOT consulted here.
# Each of them reconstructs, from front-matter fields, a judgement an upstream stage
# already made -- which is right for the legacy pool, where the drafts predate the
# bridge and nothing upstream can be trusted to have run at all, and wrong here, where
# a second jury reading the same evidence can only ever disagree with the first.
# publication_eligible IS the bridge's verdict. Consuming it is the contract.

def terminal_authorization(fm, *, roots=None):
    """(ok, reason). The accepted object, or a refusal naming which assertion failed."""
    if not PA.is_current_engine(fm):
        return False, ("not a CURRENT_ENGINE article -- direct publication is the "
                       "CURRENT_ENGINE path only; legacy/manual articles go through "
                       "the backlog selector")
    decision = str(fm.get("engine_decision", "") or "").strip()
    if decision != "ACCEPT":
        return False, "engine_decision=%r (direct publication requires ACCEPT)" % (decision,)
    v = fm.get("publication_eligible")
    if not (v is True or (isinstance(v, str) and v.strip().lower() == "true")):
        return False, ("CURRENT_ENGINE_NOT_ELIGIBLE: publication_eligible=%r -- the "
                       "publication-safety bridge did not grant eligibility" % (v,))
    ok, why = PA.retention_feasible(fm, roots=roots)
    if not ok:
        return False, "NEEDS_AUDIT_RETENTION: %s" % (why,)
    return True, "run %s: ACCEPT, eligible, retainable" % (fm.get("engine_run") or "?",)


def _commit_and_push(mutated, msg_parts):
    """Stage exactly what was mutated, commit, rebase, push. Shared by both callers so
    the staging rule cannot be right in one path and wrong in the other."""
    staged = stageable_paths(mutated)
    for d in sorted(set(mutated) - set(staged)):
        print("  staging: skipping %s (moved away, never tracked)" % (d,))
    if staged:
        subprocess.run(["git", "add", "-A", "--", *staged], cwd=str(REPO), check=True)
    subprocess.run(["git", "commit", "-m", " | ".join(msg_parts)],
                   cwd=str(REPO), check=True)
    subprocess.run(["git", "pull", "--rebase", "origin", "main"], cwd=str(REPO), check=True)
    subprocess.run(["git", "push", "origin", "main"], cwd=str(REPO), check=True)
    print("Pushed to GitHub — site building now.")


def publish_candidate(draft_path, now=None, roots=None):
    """Publish ONE exact accepted CURRENT_ENGINE candidate. Returns 0 on success.

    THE WHOLE POINT: no pool, no score, no window, no comparison with another article,
    no waiting for the every-two-days cron. The engine accepted this article; this
    publishes THIS article. There is one attempt and there is no fallback -- a
    mechanical failure is reported as a mechanical failure and the candidate is left
    where it is. It is never quietly demoted into the backlog competition, and an
    ACCEPT is never rewritten into an editorial HOLD by a filesystem error.
    """
    draft = pathlib.Path(draft_path)
    now = now or datetime.now()
    if not draft.is_file():
        print("DIRECT PUBLISH REFUSED: %s does not exist" % (draft,), file=sys.stderr)
        return 1

    fm = parse_frontmatter(draft.read_text(encoding="utf-8", errors="replace"))
    ok, why = terminal_authorization(fm, roots=roots)
    if not ok:
        print("DIRECT PUBLISH REFUSED: %s — %s" % (draft.name, why), file=sys.stderr)
        return 1
    print("\nPublishing (CURRENT_ENGINE, direct): %s" % (draft.name,))
    print("  Title: %s" % (fm.get("title", draft.stem),))
    print("  Persona: %s" % (fm.get("author", ""),))
    print("  Authorization: %s" % (why,))

    dest = POSTS / draft.name
    if dest.exists():
        print("DIRECT PUBLISH REFUSED: %s already exists in _posts/ — refusing to "
              "overwrite." % (dest.name,), file=sys.stderr)
        return 1
    POSTS.mkdir(parents=True, exist_ok=True)

    res = promote_candidate(draft, dest, now)
    if not res["ok"]:
        print("DIRECT PUBLISH FAILED: %s — %s" % (draft.name, res["reason"]),
              file=sys.stderr)
        return 1

    msg_parts = ["publish: %s" % (dest.stem,)]
    if res["image_failure"]:
        msg_parts.append("published without illustrations: %s" % (res["image_failure"],))
    try:
        _commit_and_push(res["mutated"], msg_parts)
    except subprocess.CalledProcessError as e:
        print("DIRECT PUBLISH FAILED: git error after promotion: %s" % (e,),
              file=sys.stderr)
        print("The article is in _posts/ and was NOT committed. It is left exactly as "
              "it is for an operator: undoing a retained, frozen publication bundle is "
              "not a decision this path makes on its own.", file=sys.stderr)
        return 1

    _fire_pending_social(dest.stem, dest)
    return 0


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
        # A CURRENT_ENGINE draft is not this selector's to archive either. Ageing one
        # out would quietly dispose of an article whose recovery is an open owner
        # decision, and it would do it on a clock that no longer means anything for
        # that engine.
        if PA.is_current_engine(parse_frontmatter(
                draft.read_text(encoding="utf-8", errors="replace"))):
            in_window.append(draft)
            continue
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
        # CURRENT_ENGINE LEAVES THIS COMPETITION (2026-09-07). Checked before every
        # other predicate so that no CURRENT_ENGINE article is ever read for a
        # draft_score, a freshness comparison, a persona rotation or an aging bump --
        # not merely excluded from winning, but never entered.
        _dp, _dp_why = _current_engine_direct_publish_only(fm)
        if _dp:
            print(f"  {draft.name}: SKIPPED (CURRENT_ENGINE_DIRECT_PUBLISH_ONLY) — {_dp_why}")
            continue
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
        # CURRENT_ENGINE strict fact-check evidence (defense in depth, 2026-08-25).
        # Checked here rather than folded into _current_engine_ineligible so the skip
        # reason names WHICH claim was unsupported. Legacy candidates fall straight
        # through. No fact check is re-run; this reads metadata only.
        _fc_bad, _fc_why = _current_engine_strict_fact_check_missing(fm)
        if _fc_bad:
            print(f"  {draft.name}: SKIPPED (CURRENT_ENGINE_FACT_CHECK_UNPROVEN) — {_fc_why}; "
                  f"fact_check_status={fm.get('fact_check_status')!r} and "
                  f"publication_eligible={fm.get('publication_eligible')!r} are NOT sufficient "
                  f"without strict extraction evidence")
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
        _ret_ok, _ret_why = _retention_ok(fm)
        if not _ret_ok:
            print(f"  {draft.name}: HELD (NEEDS_AUDIT_RETENTION) — {_ret_why}; remains in "
                  f"_drafts/ for later remediation, not archived or altered")
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
    # Declared before the promotion block that sets it: an assignment placed
    # after that block would reset the flag and lose the failure it records.
    image_failure = None
    dest = None
    # Every path this run intentionally changes, recorded as it changes. Staging is
    # built from THIS list and nothing else. The alternative -- staging a directory and
    # trusting that only intended files live in it -- is what put a declined candidate
    # into a public commit on 2026-08-29 (ab322bb): `git add -A _drafts` swept two
    # untracked drafts the publisher had never touched into an archive commit.
    mutated: list[str] = []
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
            res = promote_candidate(best_draft, dest, now)
            if not res["ok"]:
                print("PUBLICATION FAILED: %s — %s" % (best_draft.name, res["reason"]),
                      file=sys.stderr)
                return 1
            published = True
            image_failure = res["image_failure"]
            mutated += res["mutated"]

            # Every other in-window candidate just lost this cycle — bump its aging counter.
            for _score, draft, *_rest, fm in candidates[1:]:
                bump_attempts(draft, fm)
                mutated.append(str(draft))               # front matter rewritten
    else:
        print("No scoreable drafts in the last %d days." % AGE_WINDOW_DAYS)

    archived = []
    for draft in expired:
        verb = "Would archive" if dry_run else "Archiving"
        print(f"{verb} (unpublished after {AGE_WINDOW_DAYS}+ days): {draft.name}")
        if not dry_run:
            archive_draft(draft)
            archived.append(draft.name)
            mutated += [str(draft), str(ARCHIVE / draft.name)]   # moved out of, moved into

    if dry_run:
        return 0

    if not published and not archived:
        return 0

    msg_parts = []
    if published:
        msg_parts.append(f"publish: {dest.stem}")
    if archived:
        msg_parts.append(f"archive {len(archived)} draft(s) unpublished after {AGE_WINDOW_DAYS}d")
    if image_failure:
        msg_parts.append("published without illustrations: %s" % image_failure)
    try:
        # The SAME staging/commit/push the direct CURRENT_ENGINE path uses. Shared on
        # purpose: the pathspec rule that got two articles stranded must not be able to
        # be right in one publication path and wrong in the other.
        _commit_and_push(mutated, msg_parts)
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
