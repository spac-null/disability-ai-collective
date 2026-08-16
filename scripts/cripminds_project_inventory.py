#!/usr/bin/env python3
"""Read-only physical-state snapshot generator for CripMinds.

Writes .claude/project-manifest.json. Performs ONLY read operations against
git, the local filesystem, and (optionally, best-effort) Trident over SSH.
Never mutates git state, the filesystem outside its own output file, any
remote, or any database. Safe to run at any time, including from cron.

Usage: python3 scripts/cripminds_project_inventory.py [--out PATH] [--no-trident]
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(
    subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True
    ).stdout.strip()
)

MAC_PRESERVATION_ROOT = str(Path.home() / "code" / "cripminds-preservation")
TRIDENT_PRESERVATION_ROOT = "/srv/data/hermes/preservation/cripminds"
TRIDENT_PRODUCTION_CHECKOUT = "/srv/data/hermes/workspace/disability-ai-collective"
TRIDENT_EVALUATIONS_ROOT = "/srv/data/hermes/evaluations"
TRIDENT_SSH_HOST = "jascha@trident.tail630536.ts.net"

# Hand-classified lifecycle status per branch, current as of 2026-08-16 Phase 3.
# This is the ONE piece of human judgment baked into an otherwise-generated file.
# Re-review when branches are added/removed/merged; do not silently trust old entries.
LIFECYCLE_STATUS = {
    "main": "ACTIVE",
    "proto/story-rejection-v1": "FROZEN",
    "audit/story-rejection-design": "SAFE-TO-ARCHIVE-LATER",
    "integration-observability-2026-08-14": "SAFE-TO-ARCHIVE-LATER",
    "integration-first-work-persona-safety-2026-08-15": "SAFE-TO-ARCHIVE-LATER",
    "persona-safety-fail-closed-2026-08-16": "SUPERSEDED",
    "author-persona-biography-provenance-2026-08-14": "SUPERSEDED",
    "article-quality-next-2026-08-14": "PARKED",
    "format-lab-v0-2026-08-14": "PARKED",
    "format-lab-v1-generative-media-2026-08-14": "PARKED",
    "format-lab-v2-what-the-room-heard-2026-08-14": "PARKED",
    "human-detail-provenance-2026-08-14": "PARKED",
    "opening-quality-shadow-2026-08-14": "PARKED",
    "ops-release-hardening-2026-08-14": "PARKED",
    "publication-surface-production-candidate-2026-08-14": "PARKED",
    "publication-model-v1-2026-08-14": "PARKED",
    "publication-surface-v1-2026-08-14": "PARKED",
    "testimony-architecture-2026-08-14": "PARKED",
    "production-editorial-upgrade-v1-2026-08-14": "PARKED",
}
# Detached-HEAD worktrees have no branch name; map by worktree dir name instead.
LIFECYCLE_STATUS_DETACHED = {
    "disability-collective-ai-base-build": "SAFE-TO-ARCHIVE-LATER",
    "disability-collective-ai-eval-batch-1": "SAFE-TO-ARCHIVE-LATER",
}

OFF_MAIN_DOCS = {
    "format-lab-v0-2026-08-14": [".claude/cripminds-format-lab-v0-2026-08-14.md"],
    "format-lab-v1-generative-media-2026-08-14": [
        ".claude/cripminds-format-lab-v1-generative-media-2026-08-14.md"
    ],
    "format-lab-v2-what-the-room-heard-2026-08-14": [
        ".claude/cripminds-format-lab-v2-what-the-room-heard-2026-08-14.md"
    ],
    "publication-model-v1-2026-08-14": [".claude/cripminds-publication-model-v1-2026-08-14.md"],
    "publication-surface-v1-2026-08-14": [
        ".claude/cripminds-publication-surface-v1-2026-08-14.md"
    ],
    "production-editorial-upgrade-v1-2026-08-14": [
        ".claude/production-editorial-upgrade-v1-2026-08-14.md",
        ".claude/production-formula-root-cause-audit-2026-08-14.md",
    ],
    "testimony-architecture-2026-08-14": [".claude/testimony-L1-L2-audit-2026-08-14.md"],
}


def git(args, cwd=None):
    result = subprocess.run(
        ["git"] + args, cwd=cwd or REPO_ROOT, capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def git_lines(args, cwd=None):
    out = git(args, cwd=cwd)
    return out.splitlines() if out else []


def rev_count(base, head):
    out = git(["rev-list", "--count", f"{base}..{head}"])
    return int(out) if out and out.isdigit() else None


def is_ancestor(sha, of_sha):
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", sha, of_sha],
        cwd=REPO_ROOT,
        capture_output=True,
    )
    return result.returncode == 0


def get_worktrees():
    """Parse `git worktree list --porcelain` into structured entries."""
    raw = git_lines(["worktree", "list", "--porcelain"])
    entries = []
    current = {}
    for line in raw:
        if line.startswith("worktree "):
            if current:
                entries.append(current)
            current = {"path": line.split(" ", 1)[1]}
        elif line.startswith("HEAD "):
            current["head"] = line.split(" ", 1)[1]
        elif line.startswith("branch "):
            current["branch"] = line.split(" ", 1)[1].replace("refs/heads/", "")
            current["detached"] = False
        elif line == "detached":
            current["detached"] = True
            current["branch"] = None
    if current:
        entries.append(current)
    return entries


def status_counts(path):
    """untracked_status_entries = git-status-visible lines;
    untracked_recursive_files = actual files recursively under untracked entries.
    dirty_tracked = modified/staged tracked-file lines."""
    lines = git_lines(["status", "--porcelain"], cwd=path)
    untracked_status_entries = 0
    dirty_tracked = 0
    untracked_recursive_files = 0
    for line in lines:
        code, rest = line[:2], line[3:]
        if code == "??":
            untracked_status_entries += 1
            p = Path(path) / rest
            if p.is_dir():
                untracked_recursive_files += sum(1 for f in p.rglob("*") if f.is_file())
            elif p.exists():
                untracked_recursive_files += 1
        else:
            dirty_tracked += 1
    return {
        "untracked_status_entries": untracked_status_entries,
        "untracked_recursive_files": untracked_recursive_files,
        "dirty_tracked": dirty_tracked,
    }


def build_worktrees(main_head):
    out = []
    for wt in get_worktrees():
        path = wt["path"]
        head = wt.get("head")
        branch = wt.get("branch")
        name = Path(path).name
        counts = status_counts(path)
        unique_commits_vs_main = None
        behind_main = None
        if head:
            unique_commits_vs_main = rev_count(main_head, head)
            behind_main = rev_count(head, main_head)
        lifecycle = LIFECYCLE_STATUS.get(branch) or LIFECYCLE_STATUS_DETACHED.get(name, "UNKNOWN")
        out.append(
            {
                "path": path,
                "branch": branch,
                "detached": wt.get("detached", False),
                "head": head,
                "dirty_tracked": counts["dirty_tracked"],
                "untracked_status_entries": counts["untracked_status_entries"],
                "untracked_recursive_files": counts["untracked_recursive_files"],
                "unique_commits_vs_main": unique_commits_vs_main,
                "commits_behind_main": behind_main,
                "lifecycle_status": lifecycle,
                "off_main_docs": OFF_MAIN_DOCS.get(branch, []),
            }
        )
    return out


def build_local_branches(main_head):
    out = []
    for line in git_lines(["for-each-ref", "refs/heads", "--format=%(refname:short)|%(objectname)"]):
        name, sha = line.split("|", 1)
        upstream = git(["rev-parse", "--abbrev-ref", f"{name}@{{upstream}}"]) or None
        ahead = rev_count(main_head, sha)
        behind = rev_count(sha, main_head)
        merged = is_ancestor(sha, main_head) if sha else False
        out.append(
            {
                "name": name,
                "head": sha,
                "upstream": upstream,
                "ahead_of_main": ahead,
                "behind_main": behind,
                "merged_into_main": merged,
            }
        )
    return out


def build_remote_refs():
    out = []
    for line in git_lines(
        ["for-each-ref", "refs/remotes", "--format=%(refname:short)|%(objectname)"]
    ):
        name, sha = line.split("|", 1)
        if name.endswith("/HEAD"):
            continue
        out.append({"name": name, "head": sha})
    return out


def build_preservation_refs():
    return git_lines(
        ["for-each-ref", "refs/cripminds-preserve", "--format=%(refname)|%(objectname)"]
    )


def load_preservation_manifest_summary():
    manifest_path = Path(MAC_PRESERVATION_ROOT) / "PRESERVATION-MANIFEST.json"
    if not manifest_path.exists():
        return {"present": False, "path": str(manifest_path)}
    try:
        data = json.loads(manifest_path.read_text())
    except Exception:
        return {"present": True, "path": str(manifest_path), "parse_error": True}
    bundle = None
    for artifact in data.get("artifacts", []):
        if "bundle" in artifact.get("artifact", "").lower():
            bundle = {
                "path": artifact.get("preserved_location"),
                "sha256": artifact.get("sha256"),
                "size_bytes": artifact.get("size_bytes"),
            }
            break
    return {
        "present": True,
        "path": str(manifest_path),
        "generated_at": data.get("generated_at"),
        "bundle": bundle,
    }


def check_trident(skip):
    if skip:
        return {"reachable": False, "skipped": True}
    try:
        result = subprocess.run(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=5",
                TRIDENT_SSH_HOST,
                f"cd {TRIDENT_PRODUCTION_CHECKOUT} && git rev-parse HEAD",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return {"reachable": False, "error": result.stderr.strip()[:200]}
        return {"reachable": True, "production_checkout_head": result.stdout.strip()}
    except Exception as exc:
        return {"reachable": False, "error": str(exc)[:200]}


def check_broken_document_references():
    """Scan WORK.md for `.claude/*.md` path mentions and check existence on main."""
    work_md = REPO_ROOT / ".claude" / "WORK.md"
    if not work_md.exists():
        return []
    import re

    text = work_md.read_text()
    paths = set(re.findall(r"`(\.claude/[A-Za-z0-9_\-./]+\.md)`", text))
    broken = []
    for p in sorted(paths):
        if not (REPO_ROOT / p).exists():
            broken.append(p)
    return broken


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(REPO_ROOT / ".claude" / "project-manifest.json"))
    parser.add_argument("--no-trident", action="store_true")
    args = parser.parse_args()

    main_head = git(["rev-parse", "main"])
    origin_main_head = git(["rev-parse", "origin/main"])

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "canonical_repo": str(REPO_ROOT),
        "origin_main_head": origin_main_head,
        "local_main_head": main_head,
        "worktrees": build_worktrees(main_head),
        "local_branches": build_local_branches(main_head),
        "remote_refs": build_remote_refs(),
        "preservation_refs": [
            {"ref": r.split("|")[0], "sha": r.split("|")[1]} for r in build_preservation_refs()
        ],
        "preservation": {
            "mac_root": MAC_PRESERVATION_ROOT,
            "trident_root": TRIDENT_PRESERVATION_ROOT,
            "manifest": load_preservation_manifest_summary(),
        },
        "evidence_locations": {
            "five_article_evaluation_trident_original": (
                f"{TRIDENT_EVALUATIONS_ROOT}/cripminds-five-article-2026-08-16/"
            ),
            "five_article_evaluation_mac_preservation_copy": (
                f"{MAC_PRESERVATION_ROOT}/evaluations/cripminds-five-article-2026-08-16/"
            ),
            "reader_lab_in_flight": f"{REPO_ROOT}/reader-lab/rounds/drafts/RL-2026-003.json",
            "cj1_cj2_engineering_preserved": f"{MAC_PRESERVATION_ROOT}/engineering/cj1-cj2-2026-08-16/",
            "production_db_authority": (
                f"{TRIDENT_PRODUCTION_CHECKOUT}/disability_findings.db (Trident is authoritative; "
                "Mac copy is a separate, unreconciled, gitignored file)"
            ),
        },
        "broken_document_references": check_broken_document_references(),
        "active_prototypes": [
            {
                "name": "Story Rejection V1",
                "branch": "proto/story-rejection-v1",
                "worktree": f"{REPO_ROOT.parent}/disability-collective-ai-srv1",
                "head": git(["rev-parse", "proto/story-rejection-v1"]),
                "status": "FROZEN — AWAITING PRFV1",
            }
        ],
        "trident": check_trident(args.no_trident),
    }

    out_path = Path(args.out)
    out_path.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n")
    print(f"Wrote {out_path} ({out_path.stat().st_size} bytes)", file=sys.stderr)


if __name__ == "__main__":
    main()
