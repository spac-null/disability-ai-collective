#!/usr/bin/env python3
"""
opening_template_corpus_sweep.py — offline calibration sweep for the
deterministic opening-template detector (article-quality evidence pass,
2026-08-14). Runs the detector's core matching function across every locally
published article as if each were a candidate against every other -- the
same all-pairs analysis used to derive DEFAULT_MIN_SHARED_SHINGLES in
opening_template_detector.py. Read-only. Zero network, zero model calls.

USAGE: python3 automation/opening_template_corpus_sweep.py
"""
import sys
from pathlib import Path

AUTOMATION_DIR = Path(__file__).parent
REPO_ROOT = AUTOMATION_DIR.parent
sys.path.insert(0, str(AUTOMATION_DIR))

from orchestrator.opening_template_detector import (  # noqa: E402
    normalize_opening, shared_shingle_count, DEFAULT_MIN_SHARED_SHINGLES,
)


def main():
    files = sorted((REPO_ROOT / "_posts").glob("*.md"))
    openings = {f.stem: normalize_opening(f.read_text(encoding="utf-8")) for f in files}
    names = list(openings.keys())

    hits = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            n, shared = shared_shingle_count(openings[a], openings[b])
            if n >= DEFAULT_MIN_SHARED_SHINGLES:
                hits.append((n, a, b, shared))
    hits.sort(key=lambda h: -h[0])

    print(f"Articles scanned: {len(names)}")
    print(f"Threshold: >= {DEFAULT_MIN_SHARED_SHINGLES} shared shingles")
    print(f"Total candidate pairs: {len(hits)}")
    print()

    # Group into clusters via union-find on the pair graph.
    parent = {n: n for n in names}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    for n, a, b, shared in hits:
        union(a, b)

    clusters = {}
    for n, a, b, shared in hits:
        root = find(a)
        clusters.setdefault(root, set()).update([a, b])

    print(f"Number of candidate clusters: {len(clusters)}")
    for root, members in sorted(clusters.items(), key=lambda kv: -len(kv[1])):
        print(f"\n  Cluster ({len(members)} articles):")
        for m in sorted(members):
            print(f"    {m}")

    print("\nAll pairs, strongest first:")
    for n, a, b, shared in hits:
        phrases = ", ".join(" ".join(s) for s in list(shared)[:3])
        print(f"  {n:2d}  {a}  <->  {b}")
        print(f"       shared: {phrases}")


if __name__ == "__main__":
    main()
