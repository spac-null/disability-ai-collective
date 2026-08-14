#!/usr/bin/env python3
"""
release_preflight_test.py — static test suite for release_preflight.py.

Builds real, throwaway local git repos (a bare "remote" plus two working
clones -- one standing in for the engineer's release branch, one standing
in for the content bot pushing straight to main) under a temp directory for
every scenario, so this exercises real `git` subprocess calls end to end,
not a mocked git layer. Zero network -- the "remote" is a local bare repo
reached by filesystem path, which is what makes this deterministic and
offline-safe (`git fetch`/`git clone` against a local path never touch the
network).

Covers the 8 scenarios from docs/production-release-procedure.md's own
test-scenario list:
  A. remote unchanged (release ahead, nothing pushed yet)
  B. remote content-only commits, no overlap -> SAFE_REBASE_REQUIRED
  C. remote code commit, no file overlap -> UNKNOWN_REMOTE_CHANGE
  D. remote content commit overlapping release content -> OVERLAPPING_REMOTE_CHANGE
  E. remote code change overlapping release -> OVERLAPPING_REMOTE_CHANGE
  F. dirty local worktree -> DIRTY_WORKTREE
  G. release already current (nothing to push, nothing to rebase)
  H. remote advances twice (rebase, then a second content commit lands)

USAGE: python3 automation/release_preflight_test.py
Exit code 0 = all pass. Exit code 1 = at least one failure (printed).
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AUTOMATION_DIR = Path(__file__).parent
sys.path.insert(0, str(AUTOMATION_DIR))

from release_preflight import (  # noqa: E402
    run_preflight,
    classify_paths,
    CLASSIFICATION_SAFE,
    CLASSIFICATION_CODE,
    CLASSIFICATION_UNRECOGNIZED,
    STATUS_DIRTY_WORKTREE,
    STATUS_CLEAN_FAST_FORWARD,
    STATUS_SAFE_REBASE_REQUIRED,
    STATUS_OVERLAPPING_REMOTE_CHANGE,
    STATUS_UNKNOWN_REMOTE_CHANGE,
)

FAILURES = []


def check(name, condition):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}")
        FAILURES.append(name)


def sh(cwd, *args, check_ok=True):
    result = subprocess.run(
        ["git", "-C", str(cwd)] + list(args), capture_output=True, text=True
    )
    if check_ok and result.returncode != 0:
        raise RuntimeError(f"git {args} in {cwd} failed: {result.stderr}")
    return result.stdout


def write(repo, relpath, content):
    p = Path(repo) / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)


def commit(repo, relpath, content, message, author_email="test@example.com", author_name="Test"):
    write(repo, relpath, content)
    sh(repo, "add", relpath)
    sh(repo, "-c", f"user.email={author_email}", "-c", f"user.name={author_name}",
       "commit", "-m", message)
    return sh(repo, "rev-parse", "HEAD").strip()


class Fixture:
    """One bare remote + two clones (release engineer's, and the bot's),
    both starting from the same initial commit."""

    def __init__(self, tmp):
        self.tmp = Path(tmp)
        self.remote = self.tmp / "remote.git"
        self.release = self.tmp / "release_clone"
        self.bot = self.tmp / "bot_clone"

        sh(self.tmp, "init", "--bare", str(self.remote))

        sh(self.tmp, "clone", str(self.remote), str(self.release))
        commit(self.release, "_posts/2026-01-01-initial.md", "initial post\n", "initial commit")
        sh(self.release, "push", "origin", "HEAD:main")

        sh(self.tmp, "clone", str(self.remote), str(self.bot))
        sh(self.bot, "fetch", "origin")
        sh(self.bot, "checkout", "main")

    def bot_commits(self, *specs):
        """specs: list of (relpath, content, message) to commit+push from the
        bot clone, simulating the content bot advancing origin/main directly."""
        for relpath, content, message in specs:
            commit(self.bot, relpath, content, message,
                   author_email="contact@disability-ai-collective.org",
                   author_name="Disability-AI Collective Bot")
        sh(self.bot, "push", "origin", "HEAD:main")

    def release_commits(self, *specs):
        for relpath, content, message in specs:
            commit(self.release, relpath, content, message)


def with_fixture(fn):
    def wrapper():
        tmp = tempfile.mkdtemp(prefix="release_preflight_test_")
        try:
            fx = Fixture(tmp)
            fn(fx)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return wrapper


# ---------------------------------------------------------------------------
# Unit-level: classify_paths
# ---------------------------------------------------------------------------

def case_classify_paths_unit():
    check("all _posts/_drafts/_reviews/assets/_social paths -> SAFE_ROUTINE_CONTENT",
          classify_paths(["_posts/x.md", "_drafts/y.md", "_reviews/x-review.md",
                           "assets/x.jpg", "_social/x.json"]) == CLASSIFICATION_SAFE)
    check("_drafts/_archive/ sub-path still SAFE (matches _drafts/ prefix)",
          classify_paths(["_drafts/_archive/old.md"]) == CLASSIFICATION_SAFE)
    check("one orchestrator file among safe paths -> whole commit CODE_OR_INFRASTRUCTURE",
          classify_paths(["_posts/x.md", "automation/orchestrator/gate.py"]) == CLASSIFICATION_CODE)
    check("reader-lab-worker path -> CODE_OR_INFRASTRUCTURE (not a content path at all)",
          classify_paths(["reader-lab-worker/src/index.js"]) == CLASSIFICATION_CODE)
    check("empty path list -> UNRECOGNIZED, never defaults to SAFE",
          classify_paths([]) == CLASSIFICATION_UNRECOGNIZED)
    check("unfamiliar top-level dir -> CODE_OR_INFRASTRUCTURE, not silently SAFE",
          classify_paths(["some_new_dir/file.md"]) == CLASSIFICATION_CODE)


# ---------------------------------------------------------------------------
# A. remote unchanged (release ahead, nothing pushed yet)
# ---------------------------------------------------------------------------

@with_fixture
def case_A_remote_unchanged(fx):
    fx.release_commits(("automation/orchestrator/gate.py", "# release change\n", "release: gate fix"))
    v = run_preflight(repo=fx.release, remote_ref="origin/main", fetch=True)
    check("A. remote unchanged: status is CLEAN_FAST_FORWARD", v.status == STATUS_CLEAN_FAST_FORWARD)
    check("A. remote unchanged: safe_to_proceed True", v.safe_to_proceed)
    check("A. remote unchanged: release-only commit recorded", len(v.release_only_commits) == 1)


# ---------------------------------------------------------------------------
# B. remote content-only commits, no overlap -> SAFE_REBASE_REQUIRED
# ---------------------------------------------------------------------------

@with_fixture
def case_B_content_only_no_overlap(fx):
    fx.bot_commits(("_posts/2026-08-14-new-article.md", "new article\n", "Add new article: x"))
    fx.release_commits(("automation/orchestrator/gate.py", "# release change\n", "release: gate fix"))
    v = run_preflight(repo=fx.release, remote_ref="origin/main", fetch=True)
    check("B. content-only, no overlap: status is SAFE_REBASE_REQUIRED", v.status == STATUS_SAFE_REBASE_REQUIRED)
    check("B. content-only, no overlap: safe_to_proceed True", v.safe_to_proceed)
    check("B. content-only, no overlap: origin-only commit classified SAFE_ROUTINE_CONTENT",
          v.origin_only_commits[0].classification == CLASSIFICATION_SAFE)
    check("B. content-only, no overlap: known bot author flagged",
          v.origin_only_commits[0].known_bot_author)


# ---------------------------------------------------------------------------
# C. remote code commit, no file overlap -> UNKNOWN_REMOTE_CHANGE
# ---------------------------------------------------------------------------

@with_fixture
def case_C_code_commit_no_overlap(fx):
    fx.bot_commits(("automation/some_other_script.py", "# unreviewed\n", "quick infra tweak"))
    fx.release_commits(("automation/orchestrator/gate.py", "# release change\n", "release: gate fix"))
    v = run_preflight(repo=fx.release, remote_ref="origin/main", fetch=True)
    check("C. code commit, no overlap: status is UNKNOWN_REMOTE_CHANGE", v.status == STATUS_UNKNOWN_REMOTE_CHANGE)
    check("C. code commit, no overlap: safe_to_proceed False", not v.safe_to_proceed)
    check("C. code commit, no overlap: no overlapping files recorded (this is the distinguishing fact)",
          v.overlapping_files == [])
    check("C. code commit, no overlap: origin-only commit classified CODE_OR_INFRASTRUCTURE",
          v.origin_only_commits[0].classification == CLASSIFICATION_CODE)


# ---------------------------------------------------------------------------
# D. remote content commit overlapping release content -> OVERLAPPING_REMOTE_CHANGE
# ---------------------------------------------------------------------------

@with_fixture
def case_D_content_overlap(fx):
    fx.bot_commits(("_posts/2026-08-14-shared.md", "bot version\n", "Add new article: shared"))
    fx.release_commits(("_posts/2026-08-14-shared.md", "release version\n", "release: touches same article path"))
    v = run_preflight(repo=fx.release, remote_ref="origin/main", fetch=True)
    check("D. content overlap: status is OVERLAPPING_REMOTE_CHANGE", v.status == STATUS_OVERLAPPING_REMOTE_CHANGE)
    check("D. content overlap: safe_to_proceed False", not v.safe_to_proceed)
    check("D. content overlap: overlapping file recorded", "_posts/2026-08-14-shared.md" in v.overlapping_files)
    check("D. content overlap: overlap detected even though origin commit is SAFE_ROUTINE_CONTENT",
          v.origin_only_commits[0].classification == CLASSIFICATION_SAFE)


# ---------------------------------------------------------------------------
# E. remote code change overlapping release -> OVERLAPPING_REMOTE_CHANGE
# ---------------------------------------------------------------------------

@with_fixture
def case_E_code_overlap(fx):
    fx.bot_commits(("automation/orchestrator/gate.py", "# unrelated bot-side edit\n", "hotfix on main directly"))
    fx.release_commits(("automation/orchestrator/gate.py", "# release change\n", "release: gate fix"))
    v = run_preflight(repo=fx.release, remote_ref="origin/main", fetch=True)
    check("E. code overlap: status is OVERLAPPING_REMOTE_CHANGE", v.status == STATUS_OVERLAPPING_REMOTE_CHANGE)
    check("E. code overlap: safe_to_proceed False", not v.safe_to_proceed)
    check("E. code overlap: overlapping file recorded",
          "automation/orchestrator/gate.py" in v.overlapping_files)


# ---------------------------------------------------------------------------
# F. dirty local worktree -> DIRTY_WORKTREE
# ---------------------------------------------------------------------------

@with_fixture
def case_F_dirty_worktree(fx):
    fx.release_commits(("automation/orchestrator/gate.py", "# release change\n", "release: gate fix"))
    # Uncommitted change to a tracked file (the initial post), not part of the release.
    write(fx.release, "_posts/2026-01-01-initial.md", "edited, uncommitted\n")
    v = run_preflight(repo=fx.release, remote_ref="origin/main", fetch=True)
    check("F. dirty worktree: status is DIRTY_WORKTREE", v.status == STATUS_DIRTY_WORKTREE)
    check("F. dirty worktree: safe_to_proceed False", not v.safe_to_proceed)
    check("F. dirty worktree: dirty file recorded", "_posts/2026-01-01-initial.md" in v.dirty_files)
    # Untracked files must never trigger DIRTY_WORKTREE.
    write(fx.release, "scratch_notes.txt", "not tracked\n")
    v2 = run_preflight(repo=fx.release, remote_ref="origin/main", fetch=False)
    check("F. dirty worktree: untracked scratch file does not itself change the verdict",
          v2.status == STATUS_DIRTY_WORKTREE and "scratch_notes.txt" not in v2.dirty_files)


# ---------------------------------------------------------------------------
# G. release already current (nothing to push, nothing to rebase)
# ---------------------------------------------------------------------------

@with_fixture
def case_G_already_current(fx):
    v = run_preflight(repo=fx.release, remote_ref="origin/main", fetch=True)
    check("G. already current: status is CLEAN_FAST_FORWARD", v.status == STATUS_CLEAN_FAST_FORWARD)
    check("G. already current: safe_to_proceed True", v.safe_to_proceed)
    check("G. already current: no origin-only commits", v.origin_only_commits == [])
    check("G. already current: no release-only commits", v.release_only_commits == [])


# ---------------------------------------------------------------------------
# H. remote advances twice (rebase once, then a second content commit lands)
# ---------------------------------------------------------------------------

@with_fixture
def case_H_remote_advances_twice(fx):
    fx.bot_commits(("_posts/2026-08-13-first.md", "first\n", "Add new article: first"))
    fx.release_commits(("automation/orchestrator/gate.py", "# release change\n", "release: gate fix"))

    v1 = run_preflight(repo=fx.release, remote_ref="origin/main", fetch=True)
    check("H. round 1: SAFE_REBASE_REQUIRED", v1.status == STATUS_SAFE_REBASE_REQUIRED)

    # Simulate performing the rebase for real (this is release_preflight's own
    # test proving the tool's diagnosis was actually correct -- a real rebase
    # here must be conflict-free).
    sh(fx.release, "rebase", "origin/main")

    # A second, independent bot commit lands before the (now rebased) release
    # gets pushed -- exactly the "advances twice" scenario.
    fx.bot_commits(("_posts/2026-08-14-second.md", "second\n", "Add new article: second"))

    v2 = run_preflight(repo=fx.release, remote_ref="origin/main", fetch=True)
    check("H. round 2 after rebase: SAFE_REBASE_REQUIRED again", v2.status == STATUS_SAFE_REBASE_REQUIRED)
    check("H. round 2: exactly one new origin-only commit (the second bot commit, not the first)",
          len(v2.origin_only_commits) == 1
          and v2.origin_only_commits[0].subject == "Add new article: second")

    sh(fx.release, "rebase", "origin/main")
    v3 = run_preflight(repo=fx.release, remote_ref="origin/main", fetch=True)
    check("H. round 3 after second rebase: CLEAN_FAST_FORWARD, ready to push",
          v3.status == STATUS_CLEAN_FAST_FORWARD and v3.safe_to_proceed)


if __name__ == "__main__":
    case_classify_paths_unit()
    case_A_remote_unchanged()
    case_B_content_only_no_overlap()
    case_C_code_commit_no_overlap()
    case_D_content_overlap()
    case_E_code_overlap()
    case_F_dirty_worktree()
    case_G_already_current()
    case_H_remote_advances_twice()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    else:
        print("ALL PASS")
        sys.exit(0)
