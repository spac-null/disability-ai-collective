#!/usr/bin/env python3
"""
publish_best_pathspec_staging_test.py -- the publisher must not hand git a path that
never existed in git.

THE INCIDENT (2026-09-07). CURRENT_ENGINE candidates are persisted UNTRACKED into
_drafts/. The publisher records both ends of every move in `mutated` and stages from
that list, which is right for a TRACKED source -- git only records the removal if the
old path is named. For an untracked source it is fatal: after `shutil.move` the old
_drafts path is gone from the working tree AND was never in the index, so

    git add -A -- <that path> ...

matches nothing anywhere and git exits 128. The commit never ran. Two articles were
moved into _posts/ and left there untracked, published nowhere and staged nowhere:

    _posts/2026-09-01-roman-launches-with-its-data-pipeline-built-in.md
    _posts/2026-09-03-a-conservation-centre-built-around-a-blocked-journey.md

(Those two files are evidence and are not touched by this repair or by these tests.)

THE FIX UNDER TEST. Per mutated path: stage it if it exists; stage it if it is gone but
WAS tracked, so a real deletion/move is still recorded; do not hand it to git at all if
it is gone and was never tracked. What it must NOT do is go back to `git add -A` over a
whole directory -- that is the OTHER failure, 2026-08-29 (ab322bb), where staging a
directory swept two untracked drafts the publisher had never touched into a public
commit. publish_best_staging_test.py guards that side; this file guards this one.

Real git repositories in temp dirs. No network, no provider, no production DB.

USAGE: python3 automation/publish_best_pathspec_staging_test.py
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import types
from datetime import datetime

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import publish_best as PB                                            # noqa: E402
import publication_audit_test as PAT                                 # noqa: E402
import publication_retention_feasibility_test as RFT                 # noqa: E402

FAILURES: list = []


def check(label, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- " + str(detail)[:240]))
    if not ok:
        FAILURES.append(label)


def _git(repo, *args):
    return subprocess.run(["git", *args], cwd=str(repo),
                          capture_output=True, text=True)


def _out(repo, *args):
    r = _git(repo, *args)
    if r.returncode != 0:
        raise RuntimeError("git %s: %s" % (" ".join(args), r.stderr[:200]))
    return r.stdout.strip()


def _tracked(repo, rel):
    return _git(repo, "ls-files", "--error-unmatch", "--", rel).returncode == 0


def _repo() -> pathlib.Path:
    root = pathlib.Path(tempfile.mkdtemp(prefix="pathspec-staging-"))
    (root / "_drafts" / "_archive").mkdir(parents=True)
    (root / "_posts").mkdir()
    _out(root, "init", "-q", "-b", "main")
    _out(root, "config", "user.email", "test@example.org")
    _out(root, "config", "user.name", "Test")
    (root / "README.md").write_text("seed\n")
    _out(root, "add", "README.md")
    _out(root, "commit", "-q", "-m", "init")
    PB.REPO, PB.DRAFTS, PB.POSTS, PB.ARCHIVE = (
        root, root / "_drafts", root / "_posts", root / "_drafts" / "_archive")
    return root


def _current_engine_draft(root, name, run_id, tracked=False):
    """A CURRENT_ENGINE candidate exactly as new_engine_candidate.persist_candidate
    writes one: dated today so it is in the scoring window, and UNTRACKED unless the
    test explicitly asks for the legacy tracked shape."""
    today = datetime.now().strftime("%Y-%m-%d")
    body = (PAT.POST.replace(PAT.RUN_ID, run_id)
                    .replace("date: 2026-09-06", "date: %s" % today)
                    .replace('title: "A pavilion on six columns"', 'title: "%s"' % name))
    p = root / "_drafts" / ("%s-%s.md" % (today, name))
    p.write_text(body, encoding="utf-8")
    if tracked:
        _out(root, "add", "--", str(p))
        _out(root, "commit", "-q", "-m", "track %s" % name)
    return p


class _Recorder:
    """Delegates to the real subprocess but keeps every argv, so a test can assert what
    git was actually handed -- not merely that the run finished."""

    def __init__(self):
        self.calls = []
        self.CalledProcessError = subprocess.CalledProcessError
        self.DEVNULL = subprocess.DEVNULL

    def run(self, args, **kw):
        self.calls.append(list(args))
        if args[:2] == ["git", "push"] or args[:2] == ["git", "pull"]:
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")
        return subprocess.run(args, **kw)

    def add_pathspecs(self):
        for c in self.calls:
            if c[:3] == ["git", "add", "-A"]:
                return c[c.index("--") + 1:]
        return None


def _publish(root, run_id_dirs):
    """Run the real publisher over the temp repo with a temp evidence root and store."""
    ev = root / ".evidence"
    store = root / ".store"
    for rid in run_id_dirs:
        RFT.build_legacy_composition_run(ev, rid)
    os.environ["NEW_ENGINE_EVIDENCE_ROOT"] = str(ev)
    os.environ["CRIPMINDS_PUBLICATION_AUDIT_ROOT"] = str(store)
    fake = types.ModuleType("gen_images")
    fake.has_image_field = lambda _t: True
    fake.illustrate_post = lambda _p, **_k: {"ok": True, "assets": [], "figures": 0}
    sys.modules["gen_images"] = fake
    rec = _Recorder()
    saved_sp = PB.subprocess
    PB.subprocess = rec
    try:
        rc = PB.main(dry_run=False)
    finally:
        PB.subprocess = saved_sp
        sys.modules.pop("gen_images", None)
    return rc, rec


# ── 0. the mechanism, stated plainly ────────────────────────────────────────────────
def test_git_really_does_exit_128_on_a_vanished_untracked_pathspec():
    root = _repo()
    ghost = root / "_drafts" / "never-existed-in-git.md"
    ghost.write_text("x\n")          # untracked
    ghost.unlink()                   # and now gone, as after shutil.move
    r = _git(root, "add", "-A", "--", str(ghost))
    check("git add -A over a vanished untracked path exits 128", r.returncode == 128,
          "rc=%s %s" % (r.returncode, r.stderr[:120]))
    check("and it is a pathspec error, which is what killed the publisher",
          "did not match any files" in r.stderr, r.stderr[:160])
    shutil.rmtree(root, ignore_errors=True)


# ── 1. the rule, unit level ─────────────────────────────────────────────────────────
def test_stageable_paths_rule():
    root = _repo()
    exists_untracked = root / "_posts" / "a.md"
    exists_untracked.write_text("a\n")
    exists_tracked = root / "_drafts" / "b.md"
    exists_tracked.write_text("b\n")
    _out(root, "add", "--", str(exists_tracked))
    _out(root, "commit", "-q", "-m", "b")

    gone_tracked = root / "_drafts" / "c.md"
    gone_tracked.write_text("c\n")
    _out(root, "add", "--", str(gone_tracked))
    _out(root, "commit", "-q", "-m", "c")
    gone_tracked.unlink()

    gone_untracked = root / "_drafts" / "d.md"
    gone_untracked.write_text("d\n")
    gone_untracked.unlink()

    got = set(PB.stageable_paths([str(exists_untracked), str(exists_tracked),
                                  str(gone_tracked), str(gone_untracked)]))
    check("a path that exists is staged (tracked or not)",
          str(exists_untracked) in got and str(exists_tracked) in got, got)
    check("a path that is gone but WAS tracked is staged, so the deletion is recorded",
          str(gone_tracked) in got, got)
    check("a path that is gone and was NEVER tracked is not handed to git",
          str(gone_untracked) not in got, got)
    shutil.rmtree(root, ignore_errors=True)


# ── 2. the untracked CURRENT_ENGINE move: the actual bug ────────────────────────────
def test_untracked_current_engine_draft_is_published():
    root = _repo()
    rid = "production-20260901T090000Z-11111111"
    draft = _current_engine_draft(root, "roman-launches", rid, tracked=False)
    check("the candidate starts untracked, as persist_candidate leaves it",
          not _tracked(root, str(draft)))

    rc, rec = _publish(root, [rid])
    dest = root / "_posts" / draft.name

    check("the publisher returned success", rc == 0, "rc=%s" % rc)
    specs = rec.add_pathspecs()
    check("git add was called with an explicit pathspec list", specs is not None, rec.calls)
    check("the destination in _posts was staged", str(dest) in (specs or []), specs)
    check("the vanished untracked _drafts source was NOT handed to git",
          str(draft) not in (specs or []), specs)
    check("the article really is in _posts", dest.is_file())
    check("and it is committed, not stranded untracked",
          _tracked(root, str(dest)))
    head = _out(root, "show", "--name-status", "--format=%s", "HEAD")
    check("the commit is the publication", "publish:" in head, head[:120])
    check("nothing is left uncommitted that the run created",
          "_posts/" not in _out(root, "status", "--porcelain"),
          _out(root, "status", "--porcelain"))
    shutil.rmtree(root, ignore_errors=True)


# ── 3. the tracked legacy move still records its deletion ───────────────────────────
def test_tracked_draft_move_still_stages_the_deletion():
    root = _repo()
    rid = "production-20260902T090000Z-22222222"
    draft = _current_engine_draft(root, "a-tracked-candidate", rid, tracked=True)
    check("this candidate is tracked before the move", _tracked(root, str(draft)))

    rc, rec = _publish(root, [rid])
    dest = root / "_posts" / draft.name
    specs = rec.add_pathspecs()

    check("the publisher returned success", rc == 0, "rc=%s" % rc)
    check("the tracked source path WAS handed to git", str(draft) in (specs or []), specs)
    check("the destination was too", str(dest) in (specs or []), specs)
    head = _out(root, "show", "--name-status", "--format=%s", "HEAD")
    paths = {f for l in head.splitlines() if "\t" in l for f in l.split("\t")[1:]}
    check("git recorded the move (both ends appear in the commit)",
          {"_drafts/%s" % draft.name, "_posts/%s" % draft.name} <= paths, paths)
    check("the old draft path is gone from the index",
          not _tracked(root, "_drafts/%s" % draft.name))
    shutil.rmtree(root, ignore_errors=True)


# ── 4. archive bookkeeping, same mechanism, same rule ───────────────────────────────
def test_archive_move_of_an_untracked_draft():
    root = _repo()
    old = "2026-08-01-an-untracked-stale-draft.md"
    (root / "_drafts" / old).write_text(
        '---\nlayout: "post"\ntitle: "stale"\nauthor: "Maya Flux"\n'
        'date: "2026-08-01"\n---\n\nBody.\n', encoding="utf-8")
    check("the stale draft is untracked", not _tracked(root, "_drafts/%s" % old))

    rc, rec = _publish(root, [])
    specs = rec.add_pathspecs()

    check("the publisher returned success", rc == 0, "rc=%s" % rc)
    check("the archive destination was staged",
          str(root / "_drafts" / "_archive" / old) in (specs or []), specs)
    check("the vanished untracked source was NOT handed to git",
          str(root / "_drafts" / old) not in (specs or []), specs)
    check("the archived file is committed",
          _tracked(root, "_drafts/_archive/%s" % old))
    head = _out(root, "show", "--name-status", "--format=%s", "HEAD")
    check("the commit is the archival", "archive" in head, head[:120])
    shutil.rmtree(root, ignore_errors=True)


def test_archive_move_of_a_tracked_draft_still_records_the_deletion():
    root = _repo()
    old = "2026-08-01-a-tracked-stale-draft.md"
    p = root / "_drafts" / old
    p.write_text('---\nlayout: "post"\ntitle: "stale"\nauthor: "Maya Flux"\n'
                 'date: "2026-08-01"\n---\n\nBody.\n', encoding="utf-8")
    _out(root, "add", "--", str(p))
    _out(root, "commit", "-q", "-m", "track stale")

    rc, rec = _publish(root, [])
    specs = rec.add_pathspecs()
    check("the publisher returned success", rc == 0, "rc=%s" % rc)
    check("the tracked source path WAS handed to git", str(p) in (specs or []), specs)
    head = _out(root, "show", "--name-status", "--format=%s", "HEAD")
    paths = {f for l in head.splitlines() if "\t" in l for f in l.split("\t")[1:]}
    check("git recorded both ends of the archival",
          {"_drafts/%s" % old, "_drafts/_archive/%s" % old} <= paths, paths)
    shutil.rmtree(root, ignore_errors=True)


# ── 5. the 2026-08-29 failure must not come back ────────────────────────────────────
def test_unrelated_untracked_files_are_never_swept_in():
    root = _repo()
    rid = "production-20260903T090000Z-33333333"
    draft = _current_engine_draft(root, "the-winner", rid, tracked=False)

    bystanders = {
        "_drafts/a-declined-candidate.md": root / "_drafts" / "a-declined-candidate.md",
        "_drafts/_archive/held-by-the-owner.md":
            root / "_drafts" / "_archive" / "held-by-the-owner.md",
        "_posts/a-post-nobody-staged.md": root / "_posts" / "a-post-nobody-staged.md",
    }
    for rel, p in bystanders.items():
        p.write_text('---\nlayout: "post"\ntitle: "%s"\nauthor: "Maya Flux"\n'
                     'date: "2026-08-20"\n---\n\nNot this run\'s business.\n' % rel,
                     encoding="utf-8")

    rc, rec = _publish(root, [rid])
    specs = set(rec.add_pathspecs() or [])
    head = _out(root, "show", "--name-status", "--format=%s", "HEAD")

    check("the publisher returned success", rc == 0, "rc=%s" % rc)
    for rel, p in bystanders.items():
        check("not handed to git: %s" % rel, str(p) not in specs, specs)
        check("still untracked afterwards: %s" % rel, not _tracked(root, rel))
        check("and still on disk: %s" % rel, p.exists())
    check("the commit holds only the publication",
          {f for l in head.splitlines() if "\t" in l for f in l.split("\t")[1:]}
          == {"_posts/%s" % draft.name}, head)
    check("no add call names a bare directory",
          all(not any(s.rstrip("/").endswith(("_drafts", "_posts", "_drafts/_archive"))
                      for s in (c[c.index("--") + 1:] if "--" in c else c[2:]))
              for c in rec.calls if c[:2] == ["git", "add"]), rec.calls)
    shutil.rmtree(root, ignore_errors=True)


def main():
    saved_env = dict(os.environ)
    saved_pb = (PB.REPO, PB.DRAFTS, PB.POSTS, PB.ARCHIVE, PB.subprocess)
    try:
        for fn in (test_git_really_does_exit_128_on_a_vanished_untracked_pathspec,
                   test_stageable_paths_rule,
                   test_untracked_current_engine_draft_is_published,
                   test_tracked_draft_move_still_stages_the_deletion,
                   test_archive_move_of_an_untracked_draft,
                   test_archive_move_of_a_tracked_draft_still_records_the_deletion,
                   test_unrelated_untracked_files_are_never_swept_in):
            print("\n" + fn.__name__)
            fn()
    finally:
        PB.REPO, PB.DRAFTS, PB.POSTS, PB.ARCHIVE, PB.subprocess = saved_pb
        os.environ.clear()
        os.environ.update(saved_env)

    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        return 1
    print("ALL PATHSPEC STAGING TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
