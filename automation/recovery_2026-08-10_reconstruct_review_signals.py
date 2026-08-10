#!/usr/bin/env python3
"""
recovery_2026-08-10_reconstruct_review_signals.py — one-time recovery tool.

Rebuilds the review_signals table in automation/engagement.db from the 129
git-tracked _reviews/*.md sidecars, after automation/engagement.db was
accidentally overwritten by an rsync command that synced an empty local stub
over trident's real, populated copy. See
.claude/2026-08-10-engagement-db-incident.md for the full incident report.

Every field this script reconstructs is also present in the human-readable
sidecar (see review.py's validate_article, the `lines = [...]` block that
writes the sidecar, for the exact template this parser matches against) --
this is why review_signals was fully reconstructable while article_plans
(raw JSON never rendered into the sidecar) was not.

CRITICAL SEMANTIC CORRECTION, not a straight replay: plan_follow_read and
pre_rewrite_plan_follow_read are NOT parsed from the old sidecar text.
_plan_follow_read was fixed the same day (2026-08-10, see review.py) after
a confirmed live bug: given the full article and a rubric describing real
correction/resisting moments, the model answered CORRECTION: YES and
RESISTING: YES -- quoting real passages -- for an article that had NO
persisted plan at all, honoring the "answer N/A, don't guess" instruction
for only one of three fields. Some of the 129 sidecars carry exactly that
bogus signal. Since article_plans is empty after this recovery (the raw
briefs were not recoverable -- see the incident report), the true, correct
value for every reconstructed row is the fixed function's own deterministic
answer: no plan on file, so N/A. Restoring the old sidecar's verdict
verbatim would reintroduce, in the database, the identical epistemic error
the code fix eliminated in the live check the same day.

USAGE:
    python3 automation/recovery_2026-08-10_reconstruct_review_signals.py --dry-run
    python3 automation/recovery_2026-08-10_reconstruct_review_signals.py --commit
"""
import argparse
import re
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
REVIEWS_DIR = REPO_ROOT / "_reviews"
DB_PATH = REPO_ROOT / "automation" / "engagement.db"

_PLAN_FOLLOW_NA = (
    "CORRECTION: N/A\nRESISTING: N/A\nOPENING_SHAPE: N/A\n"
    "(no plan recorded for this article -- not evaluated)"
)


def _find_article_file(slug):
    for d in ("_posts", "_drafts"):
        p = REPO_ROOT / d / f"{slug}.md"
        if p.exists():
            return p
    return None


def _extract_author(slug):
    article = _find_article_file(slug)
    if not article:
        return None
    text = article.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'^author:\s*"?([^"\n]+)"?', text, re.MULTILINE)
    return m.group(1).strip() if m else None


def _extract_block(text, start_marker, end_marker):
    """Text strictly between the line containing start_marker and the line
    containing end_marker, matching how the sidecar template joins blocks
    with a blank line on each side (see review.py's `lines` list)."""
    start = text.find(start_marker)
    if start == -1:
        return None
    start = text.find("\n", start) + 1
    end = text.find(end_marker, start)
    if end == -1:
        return None
    block = text[start:end].strip("\n")
    return block if block else None


def parse_sidecar(path):
    """Returns a dict matching _persist_review_signals's columns, or raises
    ValueError with a reason if the sidecar doesn't match the expected shape."""
    text = path.read_text(encoding="utf-8", errors="replace")
    slug = path.stem[:-len("-review")] if path.stem.endswith("-review") else path.stem

    m = re.search(r"^Generated:\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2})", text, re.MULTILINE)
    if not m:
        raise ValueError("no 'Generated:' line found")
    reviewed_at = m.group(1) + ":00"  # sidecar only records minute precision

    engagement_verdict = _extract_block(
        text, "docstring in review.py for why this exists.", "## Shadow Checks"
    )
    if engagement_verdict:
        engagement_verdict = engagement_verdict.strip()

    m = re.search(r"Bullet points / numbered lists in body:\s*(\d+) found", text)
    shadow_bullet_hits = int(m.group(1)) if m else 0

    m = re.search(r"Forbidden academic jargon:\s*(\d+) found(?: — (.+))?", text)
    academic_jargon = [w.strip() for w in m.group(2).split(",")] if m and m.group(2) else []

    m = re.search(r"Forbidden corporate/journalese clich[ée]s:\s*(\d+) found(?: — (.+))?", text)
    corporate_cliches = [w.strip() for w in m.group(2).split(",")] if m and m.group(2) else []

    m = re.search(r"Ending looks truncated:\s*(.+)", text)
    shadow_truncated_ending = None
    if m and not m.group(1).strip().lower().startswith("no"):
        shadow_truncated_ending = m.group(1).strip()

    m = re.search(r"Seam phrases.*?:\s*(\d+) found(?: — (.+))?", text)
    shadow_seam_hits = [w.strip() for w in m.group(2).split(",")] if m and m.group(2) else []

    agent = _extract_author(slug)

    return {
        "slug": slug,
        "agent": agent,
        "reviewed_at": reviewed_at,
        "engagement_verdict": engagement_verdict,
        "shadow_bullet_hits": shadow_bullet_hits,
        "shadow_academic_jargon": academic_jargon,
        "shadow_corporate_cliches": corporate_cliches,
        "shadow_truncated_ending": shadow_truncated_ending,
        # Deliberately NOT parsed from the sidecar -- see module docstring.
        "plan_follow_read": _PLAN_FOLLOW_NA,
        "shadow_seam_hits": shadow_seam_hits,
        "pre_rewrite_plan_follow_read": _PLAN_FOLLOW_NA,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", action="store_true", help="Actually write to engagement.db (default is dry-run)")
    parser.add_argument("--dry-run", action="store_true", help="Explicit no-op -- this is the default behavior")
    args = parser.parse_args()

    # _persist_review_signals (review.py) was only added 2026-08-09 -- Stage B
    # of the anchor-architecture blueprint, same commit that added
    # _persist_article_plan. Sidecars from before that date were written by
    # validate_article, but review_signals was never called for them, so they
    # never had a row in the real table. Reconstructing them anyway would
    # fabricate 126+ historical rows that never existed. Only sidecars dated
    # on or after 2026-08-09 are in scope for this recovery.
    all_sidecars = sorted(REVIEWS_DIR.glob("*-review.md"))
    sidecars = []
    out_of_scope = 0
    for path in all_sidecars:
        text = path.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^Generated:\s*(\d{4}-\d{2}-\d{2})", text, re.MULTILINE)
        if m and m.group(1) >= "2026-08-09":
            sidecars.append(path)
        else:
            out_of_scope += 1

    parsed, skipped, malformed = [], [], []

    for path in sidecars:
        try:
            record = parse_sidecar(path)
            parsed.append(record)
        except Exception as e:
            malformed.append((path.name, str(e)))

    print(f"{len(all_sidecars)} total sidecars found, {out_of_scope} predate review_signals "
          f"(2026-08-09) and are correctly excluded")
    print(f"{len(sidecars)} sidecars in scope")
    print(f"{len(parsed)} parsed successfully")
    print(f"{len(malformed)} malformed:")
    for name, reason in malformed:
        print(f"  - {name}: {reason}")

    n_engagement = sum(1 for r in parsed if r["engagement_verdict"])
    n_plan_follow = sum(1 for r in parsed if r["plan_follow_read"])  # always true -- see note below
    print(f"{n_engagement} engagement-read records")
    print(f"{len(parsed)} plan-follow records (all reconstructed as N/A -- see module docstring, "
          f"NOT the same as {n_plan_follow} original real verdicts)")

    slugs = [r["slug"] for r in parsed]
    dupes = {s for s in slugs if slugs.count(s) > 1}
    if dupes:
        print(f"REFUSING: {len(dupes)} conflicting duplicate slug(s), each sidecar should be unique: {dupes}")
        return 1
    print("0 conflicting duplicate keys")

    if not args.commit:
        print("\nDRY RUN -- nothing written. Re-run with --commit to write.")
        for r in parsed[:3]:
            print(f"  sample: {r['slug']} | agent={r['agent']} | reviewed_at={r['reviewed_at']} | "
                  f"engagement_verdict={'yes' if r['engagement_verdict'] else 'no'}")
        return 0

    conn = sqlite3.connect(DB_PATH)
    written = 0
    for r in parsed:
        import json
        conn.execute(
            "INSERT OR REPLACE INTO review_signals "
            "(slug, agent, reviewed_at, engagement_verdict, shadow_bullet_hits, "
            "shadow_academic_jargon, shadow_corporate_cliches, shadow_truncated_ending, "
            "plan_follow_read, shadow_seam_hits, pre_rewrite_plan_follow_read) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                r["slug"], r["agent"], r["reviewed_at"], r["engagement_verdict"],
                r["shadow_bullet_hits"], json.dumps(r["shadow_academic_jargon"]),
                json.dumps(r["shadow_corporate_cliches"]), r["shadow_truncated_ending"],
                r["plan_follow_read"], json.dumps(r["shadow_seam_hits"]),
                r["pre_rewrite_plan_follow_read"],
            ),
        )
        written += 1
    conn.commit()
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    count = conn.execute("SELECT COUNT(*) FROM review_signals").fetchone()[0]
    conn.close()
    print(f"\nWrote {written} rows. Table now has {count} rows. integrity_check: {integrity}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
