#!/usr/bin/env python3
"""
publish_best.py — promote the top-scoring draft to _posts/ every 2 days.

Candidate pool: drafts dated within the last AGE_WINDOW_DAYS days. A draft
that ages out of that window without ever being selected is archived to
_drafts/_archive/ rather than left to compete forever.

Selection weights:
  - draft_score (0-10 editorial score from Opus, or default 7.0 if missing): 60%
  - topic freshness (1.0 if topic not seen in last 14 days, 0.5 if seen):     25%
  - persona rotation (1.0 if persona not in last 5 published, 0.5 if in last 2, 0.0 if in last 1): 15%
  - aging bonus: +0.15 per prior losing cycle (tracked via publish_attempts
    in front matter), capped at +0.6 — prevents a merely-decent draft from
    being perpetually outcompeted by fresher entries and archived without
    ever really winning a fair fight.

Cron (trident): 0 8 */2 * * python3 /srv/scripts/ops/publish_best.py
"""

import pathlib, re, shutil, subprocess, sys
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


def recent_posts(n=None):
    posts = sorted(POSTS.glob("*.md"), reverse=True)
    return posts if n is None else posts[:n]


def published_titles_since(days):
    cutoff = datetime.now() - timedelta(days=days)
    titles = set()
    for p in recent_posts():
        # Date from filename: YYYY-MM-DD-slug.md
        m = re.match(r"(\d{4}-\d{2}-\d{2})", p.name)
        if not m:
            continue
        try:
            pub_date = datetime.strptime(m.group(1), "%Y-%m-%d")
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
    if not last_personas:
        return 1.0
    if last_personas[0] == draft_persona:
        return 0.0  # same as most recent — penalise heavily
    if draft_persona in last_personas[:2]:
        return 0.5
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


def main():
    drafts = sorted(d for d in DRAFTS.glob("*.md") if d.is_file())
    if not drafts:
        print("No drafts to publish.")
        return 0

    now = datetime.now()
    in_window, expired = [], []
    for draft in drafts:
        age = draft_date(draft)
        if age is not None and (now - age).days > AGE_WINDOW_DAYS:
            expired.append(draft)
        else:
            in_window.append(draft)

    pub_titles = published_titles_since(TOPIC_WINDOW_DAYS)
    last_personas = recent_personas(PERSONA_WINDOW)

    candidates = []
    for draft in in_window:
        text = draft.read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(text)
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
        print(f"\nPublishing: {best_draft.name}")
        print(f"  Title: {title}")
        print(f"  Persona: {persona}")
        print(f"  Score: editorial={editorial:.1f} freshness={fresh:.1f} rotation={prot:.1f} → {best_score:.2f}")

        if dest.exists():
            print(f"ERROR: {dest.name} already exists in _posts/ — aborting to avoid overwrite.", file=sys.stderr)
            return 1

        shutil.move(str(best_draft), str(dest))
        published = True

        # Every other in-window candidate just lost this cycle — bump its aging counter.
        for _score, draft, *_rest, fm in candidates[1:]:
            bump_attempts(draft, fm)
    else:
        print("No scoreable drafts in the last %d days." % AGE_WINDOW_DAYS)

    archived = []
    for draft in expired:
        print(f"Archiving (unpublished after {AGE_WINDOW_DAYS}+ days): {draft.name}")
        archive_draft(draft)
        archived.append(draft.name)

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
        data["pending_social"] = False
        social_file.write_text(_json.dumps(data, indent=2))
    else:
        print(f"Social posting failed (non-critical): {result.stderr[:200]}")


if __name__ == "__main__":
    sys.exit(main())
