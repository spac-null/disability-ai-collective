#!/usr/bin/env python3
"""
release_preflight.py — diagnose-only release-concurrency checker.

Built 2026-08-14 after the A-M reconciliation release hit real concurrency
with the daily content-publishing bot mid-release (see
docs/production-release-procedure.md for the full story and the procedure
this tool is one step of).

WHAT THIS DOES: compares a local release ref (default: HEAD) against a
remote-tracking ref (default: origin/main) and reports which of five states
you're in. It NEVER rebases, pushes, deploys, or deletes a branch/ref --
v1 is diagnosis only, on purpose (see docs/production-release-procedure.md,
"What this procedure deliberately does NOT automate (yet)").

STATES (see `Verdict.status`):
  DIRTY_WORKTREE          -- uncommitted tracked changes present. Checked
                             first; nothing else is evaluated until this
                             is resolved (stash or commit).
  CLEAN_FAST_FORWARD      -- remote-ref has no commits release-ref lacks.
                             Either nothing to do, or a plain `git push`
                             is safe right now.
  SAFE_REBASE_REQUIRED    -- remote-ref moved, but every commit it gained
                             is SAFE_ROUTINE_CONTENT (see classify_commit)
                             and none of those commits' files overlap any
                             file the release itself changed. `git rebase
                             origin/main` is expected to be conflict-free.
  OVERLAPPING_REMOTE_CHANGE -- an origin-only commit touched a file the
                             release also touched, regardless of that
                             commit's own classification. STOP -- a human
                             needs to look at this.
  UNKNOWN_REMOTE_CHANGE   -- an origin-only commit doesn't classify as
                             SAFE_ROUTINE_CONTENT (unrecognized path shape,
                             or a real code/infrastructure file), but
                             doesn't overlap the release's own files
                             either. STOP -- still requires human review;
                             "no file collision" is not the same claim as
                             "safe to rebase past unreviewed."

USAGE:
    python3 automation/release_preflight.py [RELEASE_REF] [options]

    RELEASE_REF           positional, default HEAD -- the ref containing
                          your prepared-but-unpushed release commits.

    --remote-ref REF      default origin/main -- what to compare against.
    --repo PATH           default "." -- run against a different repo (used
                          by release_preflight_test.py's fixtures).
    --skip-fetch          don't run `git fetch` before comparing (tests set
                          up their own fixture remotes and fetch explicitly
                          when they want fresh state; real usage should NOT
                          pass this).
    --json                emit only the machine-readable JSON verdict (for
                          scripting); default is JSON + a human summary.

Exit code 0 = CLEAN_FAST_FORWARD or SAFE_REBASE_REQUIRED (safe to proceed
per docs/production-release-procedure.md). Exit code 1 = anything else
(stop and look).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Bot-commit classification -- see docs/production-release-procedure.md's
# "Bot-commit classification" section. Path-based, never trusts the commit
# message alone. Kept as simple prefix checks (not a full glob engine) since
# every real content path in this repo is a fixed top-level directory.
# ---------------------------------------------------------------------------

SAFE_CONTENT_PREFIXES = (
    "_posts/",
    "_drafts/",  # includes _drafts/_archive/ as a sub-prefix
    "_reviews/",
    "assets/",
    "_social/",
)

KNOWN_BOT_AUTHOR_EMAILS = (
    "contact@disability-ai-collective.org",
)

CLASSIFICATION_SAFE = "SAFE_ROUTINE_CONTENT"
CLASSIFICATION_CODE = "CODE_OR_INFRASTRUCTURE"
CLASSIFICATION_UNRECOGNIZED = "UNRECOGNIZED"

STATUS_DIRTY_WORKTREE = "DIRTY_WORKTREE"
STATUS_CLEAN_FAST_FORWARD = "CLEAN_FAST_FORWARD"
STATUS_SAFE_REBASE_REQUIRED = "SAFE_REBASE_REQUIRED"
STATUS_OVERLAPPING_REMOTE_CHANGE = "OVERLAPPING_REMOTE_CHANGE"
STATUS_UNKNOWN_REMOTE_CHANGE = "UNKNOWN_REMOTE_CHANGE"

# Only these two states mean "safe to proceed" per the documented procedure.
SAFE_STATUSES = (STATUS_CLEAN_FAST_FORWARD, STATUS_SAFE_REBASE_REQUIRED)


def _is_safe_content_path(path):
    return any(path.startswith(prefix) for prefix in SAFE_CONTENT_PREFIXES)


def classify_paths(paths):
    """A commit is SAFE_ROUTINE_CONTENT only if EVERY file it touched is a
    safe content path -- one non-content file anywhere in the commit is
    enough to classify the whole commit as CODE_OR_INFRASTRUCTURE. An empty
    path list (should not happen for a real commit, but defensively) is
    UNRECOGNIZED, not SAFE -- never default to safe on missing information.
    """
    if not paths:
        return CLASSIFICATION_UNRECOGNIZED
    if all(_is_safe_content_path(p) for p in paths):
        return CLASSIFICATION_SAFE
    # At least one path fell outside the safe allowlist. Distinguish
    # "clearly code/infra" from "just don't recognize this shape" only for
    # reporting clarity -- both are treated identically by the overall
    # verdict (require human review), see classify_commit's own docstring.
    return CLASSIFICATION_CODE


@dataclass
class CommitInfo:
    sha: str
    subject: str
    author_email: str
    paths: list
    classification: str
    known_bot_author: bool

    def to_dict(self):
        return {
            "sha": self.sha,
            "subject": self.subject,
            "author_email": self.author_email,
            "paths": self.paths,
            "classification": self.classification,
            "known_bot_author": self.known_bot_author,
        }


@dataclass
class Verdict:
    status: str
    origin_ref: str
    release_ref: str
    origin_only_commits: list = field(default_factory=list)
    release_only_commits: list = field(default_factory=list)
    overlapping_files: list = field(default_factory=list)
    dirty_files: list = field(default_factory=list)
    reason: str = ""

    @property
    def safe_to_proceed(self):
        return self.status in SAFE_STATUSES

    def recommended_action(self):
        return {
            STATUS_DIRTY_WORKTREE: (
                "Protect unrelated uncommitted changes (git stash push -m ... -- <path>), "
                "then re-run preflight."
            ),
            STATUS_CLEAN_FAST_FORWARD: "Safe to push directly (git push origin main).",
            STATUS_SAFE_REBASE_REQUIRED: (
                "Safe to rebase (git rebase " + self.origin_ref + "), then rerun the full "
                "test suite before pushing."
            ),
            STATUS_OVERLAPPING_REMOTE_CHANGE: (
                "STOP. A remote commit touches a file this release also touches -- "
                "requires human review, not an automatic rebase."
            ),
            STATUS_UNKNOWN_REMOTE_CHANGE: (
                "STOP. A remote commit doesn't classify as routine content -- requires "
                "human review before rebasing past it, even though no file overlap was found."
            ),
        }[self.status]

    def to_dict(self):
        return {
            "status": self.status,
            "safe_to_proceed": self.safe_to_proceed,
            "origin_ref": self.origin_ref,
            "release_ref": self.release_ref,
            "origin_only_commits": [c.to_dict() for c in self.origin_only_commits],
            "release_only_commits": [c.to_dict() for c in self.release_only_commits],
            "overlapping_files": self.overlapping_files,
            "dirty_files": self.dirty_files,
            "reason": self.reason,
            "recommended_action": self.recommended_action(),
        }


class GitError(RuntimeError):
    pass


def _run_git(repo, args):
    result = subprocess.run(
        ["git", "-C", str(repo)] + args,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def _dirty_tracked_files(repo):
    # Only tracked-file modifications matter for rebase safety -- untracked
    # files (this repo's own known pre-existing artifacts on Trident, or
    # anyone's scratch files) never block a rebase and are never reported
    # here. `git status --porcelain` prefixes untracked with '??'; every
    # other prefix is a tracked change of some kind.
    out = _run_git(repo, ["status", "--porcelain"])
    dirty = []
    for line in out.splitlines():
        if not line or line.startswith("??"):
            continue
        dirty.append(line[3:].strip())
    return dirty


def _commit_paths(repo, sha):
    out = _run_git(repo, ["diff-tree", "--no-commit-id", "--name-only", "-r", sha])
    return [p for p in out.splitlines() if p]


def _commit_info(repo, sha):
    subject = _run_git(repo, ["log", "-1", "--format=%s", sha]).strip()
    author_email = _run_git(repo, ["log", "-1", "--format=%ae", sha]).strip()
    paths = _commit_paths(repo, sha)
    classification = classify_paths(paths)
    return CommitInfo(
        sha=sha,
        subject=subject,
        author_email=author_email,
        paths=paths,
        classification=classification,
        known_bot_author=author_email in KNOWN_BOT_AUTHOR_EMAILS,
    )


def _commit_shas(repo, range_expr):
    out = _run_git(repo, ["log", "--format=%H", range_expr])
    return [s for s in out.splitlines() if s]


def run_preflight(repo=".", release_ref="HEAD", remote_ref="origin/main", fetch=True):
    """Pure diagnosis. Never mutates the repo (fetch is the only network/ref-
    updating operation, and only touches the remote-tracking ref, never any
    local branch). Returns a Verdict."""
    repo = Path(repo)

    dirty = _dirty_tracked_files(repo)
    if dirty:
        return Verdict(
            status=STATUS_DIRTY_WORKTREE,
            origin_ref=remote_ref,
            release_ref=release_ref,
            dirty_files=dirty,
            reason=f"{len(dirty)} tracked file(s) have uncommitted changes.",
        )

    if fetch:
        # Fetch only updates remote-tracking refs (e.g. refs/remotes/origin/main),
        # never a local branch -- safe to call unconditionally.
        remote_name = remote_ref.split("/", 1)[0] if "/" in remote_ref else remote_ref
        try:
            _run_git(repo, ["fetch", remote_name])
        except GitError as e:
            return Verdict(
                status=STATUS_UNKNOWN_REMOTE_CHANGE,
                origin_ref=remote_ref,
                release_ref=release_ref,
                reason=f"git fetch failed, cannot verify remote state safely: {e}",
            )

    origin_only_shas = _commit_shas(repo, f"{release_ref}..{remote_ref}")
    release_only_shas = _commit_shas(repo, f"{remote_ref}..{release_ref}")

    if not origin_only_shas:
        return Verdict(
            status=STATUS_CLEAN_FAST_FORWARD,
            origin_ref=remote_ref,
            release_ref=release_ref,
            release_only_commits=[_commit_info(repo, s) for s in release_only_shas],
            reason=(
                f"{remote_ref} has no commits {release_ref} lacks."
                + (" Nothing to push." if not release_only_shas else " Safe to push directly.")
            ),
        )

    origin_only = [_commit_info(repo, s) for s in origin_only_shas]
    release_only = [_commit_info(repo, s) for s in release_only_shas]

    origin_paths = {p for c in origin_only for p in c.paths}
    release_paths = {p for c in release_only for p in c.paths}
    overlap = sorted(origin_paths & release_paths)

    if overlap:
        return Verdict(
            status=STATUS_OVERLAPPING_REMOTE_CHANGE,
            origin_ref=remote_ref,
            release_ref=release_ref,
            origin_only_commits=origin_only,
            release_only_commits=release_only,
            overlapping_files=overlap,
            reason=(
                f"{len(overlap)} file(s) touched by both an origin-only commit and a "
                "release commit."
            ),
        )

    non_safe = [c for c in origin_only if c.classification != CLASSIFICATION_SAFE]
    if non_safe:
        return Verdict(
            status=STATUS_UNKNOWN_REMOTE_CHANGE,
            origin_ref=remote_ref,
            release_ref=release_ref,
            origin_only_commits=origin_only,
            release_only_commits=release_only,
            reason=(
                f"{len(non_safe)} origin-only commit(s) are not classified "
                f"{CLASSIFICATION_SAFE} (no file overlap, but still unreviewed)."
            ),
        )

    return Verdict(
        status=STATUS_SAFE_REBASE_REQUIRED,
        origin_ref=remote_ref,
        release_ref=release_ref,
        origin_only_commits=origin_only,
        release_only_commits=release_only,
        reason=(
            f"{len(origin_only)} origin-only commit(s), all {CLASSIFICATION_SAFE}, "
            "zero file overlap with the release."
        ),
    )


def _human_summary(v: Verdict) -> str:
    lines = [
        f"STATUS: {v.status}",
        f"  {v.reason}",
        f"  origin_ref={v.origin_ref}  release_ref={v.release_ref}",
    ]
    if v.dirty_files:
        lines.append(f"  dirty tracked files: {', '.join(v.dirty_files)}")
    if v.origin_only_commits:
        lines.append(f"  origin-only commits ({len(v.origin_only_commits)}):")
        for c in v.origin_only_commits:
            bot = " [known bot]" if c.known_bot_author else ""
            lines.append(f"    {c.sha[:10]}  [{c.classification}]{bot}  {c.subject}")
    if v.release_only_commits:
        lines.append(f"  release-only commits ({len(v.release_only_commits)}):")
        for c in v.release_only_commits:
            lines.append(f"    {c.sha[:10]}  {c.subject}")
    if v.overlapping_files:
        lines.append(f"  overlapping files: {', '.join(v.overlapping_files)}")
    lines.append(f"  recommended action: {v.recommended_action()}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("release_ref", nargs="?", default="HEAD")
    parser.add_argument("--remote-ref", default="origin/main")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--skip-fetch", action="store_true")
    parser.add_argument("--json", action="store_true", help="emit only JSON, no human summary")
    args = parser.parse_args()

    try:
        verdict = run_preflight(
            repo=args.repo,
            release_ref=args.release_ref,
            remote_ref=args.remote_ref,
            fetch=not args.skip_fetch,
        )
    except GitError as e:
        print(json.dumps({"status": "ERROR", "reason": str(e)}, indent=2))
        sys.exit(1)

    payload = verdict.to_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(json.dumps(payload, indent=2))
        print()
        print(_human_summary(verdict))

    sys.exit(0 if verdict.safe_to_proceed else 1)


if __name__ == "__main__":
    main()
