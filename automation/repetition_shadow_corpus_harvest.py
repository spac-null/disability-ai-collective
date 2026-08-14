#!/usr/bin/env python3
"""
repetition_shadow_corpus_harvest.py — offline evidence harvest for G's
repetition shadow check (A-M reconciliation item G, 2026-08-14).

_check_repetition_shadow (review.py) is deliberately SHADOW ONLY — no
promotion before 2026-08-28, per its own docstring. This script does not
change that. It runs the existing detector across every committed,
published article in _posts/ (a safe local corpus — already public,
already committed, zero live secrets, zero network calls) and reports
descriptive statistics: article count, candidate-pair count, similarity-
score distribution, and the highest-scoring examples by article/paragraph,
so a human (or a future promotion decision) has real numbers instead of
the single similarity_threshold=0.35 guess the check shipped with.

Does NOT tune the threshold. Does NOT change shadow/blocking status.
Read-only: opens files, never writes.

USAGE: python3 automation/repetition_shadow_corpus_harvest.py
"""
import sys
from pathlib import Path
from collections import Counter

AUTOMATION_DIR = Path(__file__).parent
REPO_ROOT = AUTOMATION_DIR.parent
sys.path.insert(0, str(AUTOMATION_DIR))

from orchestrator.review import ReviewMixin  # noqa: E402

POSTS_DIR = REPO_ROOT / "_posts"


def main():
    files = sorted(POSTS_DIR.glob("*.md"))
    total_articles = 0
    total_candidates = 0
    all_similarities = []
    per_article_counts = Counter()
    high_score_examples = []  # (similarity, slug, i, j, shared_terms)
    zero_candidate_articles = 0
    error_articles = []

    for f in files:
        total_articles += 1
        try:
            content = f.read_text(encoding="utf-8")
        except Exception as e:
            error_articles.append((f.name, str(e)))
            continue
        try:
            candidates = ReviewMixin._check_repetition_shadow(content)
        except Exception as e:
            error_articles.append((f.name, str(e)))
            continue

        if not candidates:
            zero_candidate_articles += 1
            continue

        per_article_counts[f.stem] = len(candidates)
        total_candidates += len(candidates)
        for c in candidates:
            all_similarities.append(c["similarity"])
            high_score_examples.append(
                (c["similarity"], f.stem, c["paragraph_pair"][0], c["paragraph_pair"][1], c["shared_terms"])
            )

    print(f"Articles scanned: {total_articles}")
    print(f"Articles with zero candidates: {zero_candidate_articles} "
          f"({100*zero_candidate_articles/total_articles:.1f}%)" if total_articles else "")
    print(f"Articles with 1+ candidates: {total_articles - zero_candidate_articles - len(error_articles)}")
    print(f"Errors (unreadable/crashed): {len(error_articles)}")
    for name, err in error_articles:
        print(f"  ERROR {name}: {err}")
    print(f"Total candidate pairs across corpus: {total_candidates}")
    if total_articles:
        print(f"Mean candidate pairs per article: {total_candidates/total_articles:.2f}")

    if all_similarities:
        all_similarities.sort()
        n = len(all_similarities)
        print(f"\nSimilarity score distribution (n={n}, threshold=0.35 -- everything here is >= that):")
        print(f"  min={all_similarities[0]:.2f}  "
              f"p25={all_similarities[n//4]:.2f}  "
              f"median={all_similarities[n//2]:.2f}  "
              f"p75={all_similarities[3*n//4]:.2f}  "
              f"max={all_similarities[-1]:.2f}")
        buckets = Counter()
        for s in all_similarities:
            buckets[round(s, 1)] += 1
        print("  Histogram (rounded to 0.1):")
        for k in sorted(buckets):
            print(f"    {k:.1f}: {'#' * buckets[k]} ({buckets[k]})")

    print(f"\nArticles with the MOST candidate pairs (top 10):")
    for slug, count in per_article_counts.most_common(10):
        print(f"  {count:2d}  {slug}")

    print(f"\nHighest-similarity examples (top 15, for manual false-positive review):")
    high_score_examples.sort(key=lambda x: -x[0])
    for sim, slug, i, j, shared in high_score_examples[:15]:
        print(f"  sim={sim:.2f}  {slug}  paragraphs {i}&{j}  shared: {', '.join(shared[:6])}")


if __name__ == "__main__":
    main()
