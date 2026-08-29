#!/usr/bin/env python3
"""
publish_best_staging_test.py -- the publisher commits what it changed, and nothing else.

On 2026-08-29 the 08:00 publisher archived one stale draft and, via `git add -A _drafts`,
also committed two files it had never touched: a draft from the 27th and the 28 August
candidate the owner had declined and held. Neither was published, but a declined article
entered a public repository because staging trusted a directory instead of a record of
what the run actually did.

These tests run a real git repository in a temp dir. No network, no publication path
beyond the script's own, no production DB.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import publish_best as PB                                        # noqa: E402

FAILURES: list = []


def check(label, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- " + str(detail)[:220]))
    if not ok:
        FAILURES.append(label)


def _git(repo, *args, check_rc=True):
    r = subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True)
    if check_rc and r.returncode != 0 and args[0] not in ("commit",):
        raise RuntimeError("git %s: %s" % (" ".join(args), r.stderr[:200]))
    return r.stdout.strip()


def _draft(day_offset, name, extra="", eligible=True):
    """A draft the promotion gate will accept (`eligible`) or hold. An ineligible one is
    still a real file under _drafts that the publisher must leave completely alone."""
    day = (datetime.now() - timedelta(days=day_offset)).strftime("%Y-%m-%d")
    gate = ("fact_check_status: verified\npublication_safety_version: 1\n"
            if eligible else "")
    body = ('---\nlayout: "post"\ntitle: "%s"\nauthor: "Maya Flux"\ndate: "%s"\n%s%s---\n\nBody.\n'
            % (name, day, gate, extra))
    return "%s-%s.md" % (day, name), body


def _tracked(root, relpath):
    r = subprocess.run(["git", "ls-files", "--error-unmatch", relpath],
                       cwd=str(root), capture_output=True, text=True)
    return r.returncode == 0


def _repo(drafts=(), archived=(), posts=()):
    """A git repo shaped like the real one. `drafts`/`archived`/`posts` are
    (filename, body, tracked) triples."""
    root = pathlib.Path(tempfile.mkdtemp())
    (root / "_drafts" / "_archive").mkdir(parents=True)
    (root / "_posts").mkdir()
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "test@example.org")
    _git(root, "config", "user.name", "Test")
    (root / "README.md").write_text("seed\n")
    _git(root, "add", "README.md")
    _git(root, "commit", "-q", "-m", "init")
    for sub, items in (("_drafts", drafts), ("_drafts/_archive", archived),
                       ("_posts", posts)):
        for name, body, tracked in items:
            (root / sub / name).write_text(body)
            if tracked:
                _git(root, "add", "%s/%s" % (sub, name))
    if _git(root, "status", "--porcelain"):
        _git(root, "commit", "-q", "-m", "fixtures")
    PB.REPO, PB.DRAFTS, PB.POSTS, PB.ARCHIVE = (
        root, root / "_drafts", root / "_posts", root / "_drafts" / "_archive")
    return root


def _run(root):
    """Run the publisher for real. Its push fails (no remote) AFTER the commit, which
    is the part under test."""
    PB.main(dry_run=False)
    return _git(root, "show", "--name-status", "--format=%s", "HEAD")


# ── A + B: untracked files are never swept in ─────────────────────────────────
def test_unrelated_untracked_drafts_are_not_committed():
    stale_name, stale_body = _draft(9, "stale-one")
    # Both are files the publisher has no business touching: one an ineligible draft
    # someone left in the directory, one a declined candidate held in _archive.
    loose_name, loose_body = _draft(1, "someone-elses-draft", eligible=False)
    held_name, held_body = _draft(2, "declined-and-held", eligible=False)
    root = _repo(drafts=[(stale_name, stale_body, True),
                         (loose_name, loose_body, False)],
                 archived=[(held_name, held_body, False)])
    out = _run(root)
    check("the run archived the stale draft", stale_name in out, out)
    check("an unrelated untracked draft is NOT in the commit",
          loose_name not in out, out)
    check("an unrelated untracked file in _drafts/_archive is NOT in the commit",
          held_name not in out, out)
    check("the unrelated draft is still untracked",
          not _tracked(root, "_drafts/%s" % loose_name))
    check("the held candidate is still untracked",
          not _tracked(root, "_drafts/_archive/%s" % held_name))
    check("and both still exist on disk",
          (root / "_drafts" / loose_name).exists()
          and (root / "_drafts" / "_archive" / held_name).exists())


# ── C: unrelated tracked edits are not swept in ───────────────────────────────
def test_unrelated_tracked_modification_is_not_committed():
    stale_name, stale_body = _draft(9, "stale-two")
    other_name, other_body = _draft(1, "tracked-but-untouched", eligible=False)
    root = _repo(drafts=[(stale_name, stale_body, True), (other_name, other_body, True)])
    (root / "_drafts" / other_name).write_text(other_body + "\nEdited by a human.\n")
    out = _run(root)
    check("the stale draft was archived", stale_name in out, out)
    check("an unrelated tracked edit is NOT in the commit", other_name not in out, out)
    status = _git(root, "status", "--porcelain")
    check("that edit is still uncommitted in the working tree",
          "_drafts/%s" % other_name in status, status)
    check("the held draft was not published either",
          not (root / "_posts" / other_name).exists())


# ── D: archival stages both ends of the move ──────────────────────────────────
def test_archival_stages_source_and_destination():
    stale_name, stale_body = _draft(9, "stale-three")
    root = _repo(drafts=[(stale_name, stale_body, True)])
    out = _run(root)
    lines = [l for l in out.splitlines() if "\t" in l]
    paths = {f for l in lines for f in l.split("\t")[1:]}
    check("the archive destination is staged",
          "_drafts/_archive/%s" % stale_name in paths, paths)
    check("the vacated draft path is staged too (git records the move as a rename)",
          "_drafts/%s" % stale_name in paths, lines)
    check("nothing else is in the commit", paths == {
        "_drafts/%s" % stale_name, "_drafts/_archive/%s" % stale_name}, paths)


# ── E + F: publication stages exactly its own paths ───────────────────────────
def test_publication_stages_exactly_what_it_moved():
    # Which of two eligible drafts wins is the selector's business, not this test's:
    # it asserts that whatever the run did, the commit contains only that.
    win_name, win_body = _draft(1, "candidate-one")
    lose_name, lose_body = _draft(2, "candidate-two")
    loose_name, loose_body = _draft(1, "untouched-untracked", eligible=False)
    root = _repo(drafts=[(win_name, win_body, True), (lose_name, lose_body, True),
                         (loose_name, loose_body, False)])
    out = _run(root)
    lines = [l for l in out.splitlines() if "\t" in l]
    paths = {f for l in lines for f in l.split("\t")[1:]}
    published = [p for p in paths if p.startswith("_posts/")]
    check("exactly one post was created", len(published) == 1, paths)
    promoted = published[0].split("/")[-1]
    demoted = lose_name if promoted == win_name else win_name
    check("the promoted draft's old path is staged", "_drafts/%s" % promoted in paths, paths)
    check("the other candidate's aging bump is staged",
          "_drafts/%s" % demoted in paths, paths)
    check("the untouched untracked draft is NOT staged",
          "_drafts/%s" % loose_name not in paths, paths)
    check("the commit contains exactly the run's own mutations",
          paths == {"_posts/%s" % promoted, "_drafts/%s" % promoted,
                    "_drafts/%s" % demoted}, paths)
    check("the untracked file is still untracked afterwards",
          not _tracked(root, "_drafts/%s" % loose_name))


# ── G: the broad staging is gone and no glob replaced it ──────────────────────
def test_no_broad_staging_remains():
    src = (HERE / "publish_best.py").read_text()
    for banned in ('"-A", str(DRAFTS)', '"-A", str(ARCHIVE)', '"-A", str(POSTS)',
                   '"git", "add", str(ARCHIVE)', '"git", "add", "."', '"add", "-A"]'):
        check("no broad staging: %s" % banned, banned not in src)
    check("staging is driven by a recorded mutation set",
          "mutated" in src and 'subprocess.run(["git", "add", "-A", "--", *sorted(set(mutated))]' in src)
    check("every add call is path-scoped",
          all("--" in line for line in src.splitlines()
              if '"git", "add"' in line or '["git", "add"' in line))


def main():
    for fn in (test_unrelated_untracked_drafts_are_not_committed,
               test_unrelated_tracked_modification_is_not_committed,
               test_archival_stages_source_and_destination,
               test_publication_stages_exactly_what_it_moved,
               test_no_broad_staging_remains):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL PUBLISH_BEST STAGING TESTS PASSED")


if __name__ == "__main__":
    main()
