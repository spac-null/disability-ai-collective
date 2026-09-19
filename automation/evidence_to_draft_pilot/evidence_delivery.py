"""
evidence_delivery.py -- build the reviewer's evidence view, and PROVE what was in it.

THE DEFECT THIS REPAIRS. Evaluation v1 built the reviewer prompt with
`judge.sources_block(sources, per_source_chars=5000)`. Every source was silently cut to
its first 5,000 characters, and the prompt said nothing about it. Reviewers were then
asked whether the articles were supported by "the source material" and answered against
between 52% and 72% of it.

Measured on the two subjects the independent audit named:

    9381ae93  S2 retained 12,000 chars, delivered 5,000. The Claude review quotes the
              source as ending "the envier's destroying his r" -- exactly S2[:5000].
              Material called unsupported sits at 5369 (F52), 5545 (F51), 8063 (F58).
    9381ae93  S3 retained 13,534, delivered 5,000; the guilt-as-burden passage is at
              5066 (F71).
    09d602f1  S0 retained 9,470, delivered 5,000; Cheadle at 7576, Chi at 6197,
              figure-drawing at 5758.

A capped evidence view is not automatically wrong. Presenting it as the complete record,
and then scoring an article's factual support against it, is.

WHAT THIS MODULE DOES DIFFERENTLY.

  * Delivers the WHOLE retained text of every frozen source when it fits the budget,
    rather than a fixed prefix of each.
  * When something must still be dropped, says so IN THE PROMPT the reviewer reads, and
    records `INSUFFICIENT_EVIDENCE_VIEW` on the manifest, so a resulting objection can
    never be scored as a confirmed fabrication.
  * Writes an EVIDENCE_DELIVERY_MANIFEST.json carrying, per source: id, hash, retained
    length, delivered ranges, truncation status and source version -- plus the request
    hash AND the sanitised request text itself, because a hash alone does not let anyone
    inspect what the reviewer actually saw.

THE BUDGET IS STILL A BUDGET. It is set high enough that all six frozen subjects fit
whole (the largest is 40,000 characters of source plus two articles), so for this
re-evaluation nothing is dropped -- which the manifest states as a fact rather than an
assumption.
"""
from __future__ import annotations

import hashlib
import json
import pathlib

# Generous on purpose: every frozen subject's complete source set is 40,000 characters,
# and two articles add roughly 12,000 more. Nothing in this pilot needs truncating.
DEFAULT_TOTAL_BUDGET_CHARS = 200_000

FULL = "FULL"
TRUNCATED = "TRUNCATED"
INSUFFICIENT = "INSUFFICIENT_EVIDENCE_VIEW"
NOT_DELIVERED = "EVIDENCE_NOT_DELIVERED"


def sha256_text(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()


def build_sources_block(sources: list, *, total_budget: int = DEFAULT_TOTAL_BUDGET_CHARS
                        ) -> tuple:
    """Return (block_text, per_source_records).

    Allocation is proportional and only engages if the whole set does not fit. Each
    record says exactly which byte ranges the reviewer received.
    """
    lengths = {s.get("source_id"): len(s.get("text") or "") for s in sources}
    total = sum(lengths.values())
    allow = dict(lengths)
    if total > total_budget:
        # Proportional, with a floor so no source vanishes entirely.
        floor = min(2000, total_budget // max(1, len(sources)))
        allow = {}
        for sid, n in lengths.items():
            allow[sid] = max(floor, int(total_budget * (n / total)))

    parts, records = [], []
    for s in sources:
        sid = s.get("source_id")
        text = s.get("text") or ""
        n = min(len(text), allow.get(sid, len(text)))
        delivered = text[:n]
        status = FULL if n >= len(text) else TRUNCATED
        header = ("--- SOURCE %s | %s | %s\n"
                  % (sid, s.get("publisher") or "", s.get("title") or ""))
        if status == TRUNCATED:
            header += ("[NOTE TO REVIEWER: this source is %d characters long and you "
                       "are seeing the first %d. Material may exist beyond this point. "
                       "If a claim would be supported by text you cannot see, say "
                       "EVIDENCE_NOT_VISIBLE rather than calling it unsupported.]\n"
                       % (len(text), n))
        parts.append(header + delivered)
        records.append({
            "source_id": sid,
            "source_sha256": s.get("sha256"),
            "delivered_text_sha256": sha256_text(delivered),
            "retained_chars": len(text),
            "delivered_chars": n,
            "delivered_ranges": [[0, n]],
            "truncation_status": status,
            "url": s.get("url"),
            "title": s.get("title"),
            "publisher": s.get("publisher"),
        })
    return "\n\n".join(parts), records


def evidence_view(subject: dict, *, total_budget: int = DEFAULT_TOTAL_BUDGET_CHARS
                  ) -> dict:
    """The complete evidence view for one subject, plus its manifest fragment."""
    gi = subject["generation_inputs"]
    block, records = build_sources_block(gi["sources"], total_budget=total_budget)
    truncated = [r for r in records if r["truncation_status"] != FULL]
    return {
        "subject_id": subject["subject_id"],
        "source_set_hash": subject["source_set_hash"],
        "sources_block": block,
        "records": records,
        "evidence_view_status": INSUFFICIENT if truncated else FULL,
        "sources_truncated": [r["source_id"] for r in truncated],
        "retained_total_chars": sum(r["retained_chars"] for r in records),
        "delivered_total_chars": sum(r["delivered_chars"] for r in records),
        "v1_would_have_delivered_chars": sum(min(5000, r["retained_chars"])
                                             for r in records),
    }


def write_manifest(out_dir, entries: list) -> pathlib.Path:
    d = pathlib.Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    p = d / "EVIDENCE_DELIVERY_MANIFEST.json"
    payload = {
        "evaluation_version": 2,
        "what_this_records": "exactly what each reviewer was given, per source, with "
                             "the request text retained so it can be inspected rather "
                             "than only hashed",
        "v1_defect": {
            "function": "evidence_to_draft_pilot/judge.py:sources_block",
            "line": 106,
            "behaviour": "per_source_chars=5000 applied silently to every source",
            "effect": "reviewers saw 52-72% of the retained evidence and were not told",
        },
        "subjects": entries,
    }
    p.write_text(json.dumps(payload, indent=1, ensure_ascii=False))
    return p
