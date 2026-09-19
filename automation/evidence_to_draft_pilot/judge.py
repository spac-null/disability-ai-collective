"""
judge.py -- blind evaluation of the A/B/C variants (section 16).

WHAT IS BLINDED, AND HOW. Each subject's variants are relabelled with neutral identifiers
derived from a per-subject salt, so the label carries no ordering information and the same
arm is not always the same letter across subjects. A reviewer sees:

    the source evidence, the rubric, and the variants under neutral labels

and does NOT see: which arm produced which variant, which model wrote or edited it, the
historical production outcome, the other reviewer's review, or any owner label. The
shuffle map is written to disk under the experiment root and is read only by the analysis.

TWO REVIEWERS, DELIBERATELY DIFFERENT. One Claude via subscription, one Codex via
subscription. Each is a FRESH isolated session -- `--no-session-persistence` on the Claude
side, `--ephemeral --ignore-user-config` on the Codex side -- so no verdict, benchmark
label or previous cell can be resumed into the context.

THESE ARE MODEL ASSESSMENTS, NOT VERDICTS. Section 16 is explicit and the output labels
itself accordingly: `assessment_not_owner_judgement` and `not_independent_fact_checking`
ride on every review. A factual objection is only usable if it carries an exact article
span and an exact source passage, so a reviewer's unsupported assertion can be told apart
from a located one.

DISAGREEMENTS ARE NOT VOTED ON. `reconcile` records agreement and disagreement and, where
the two reviewers differ on a MATERIAL factual objection, routes the case to the owner
review set. It never resolves a factual disagreement by majority, and never by preferring
the verdict that would permit publication.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
AUTOMATION = HERE.parent
if str(AUTOMATION) not in sys.path:
    sys.path.insert(0, str(AUTOMATION))

PROMPT_VERSION = "blind-review-v1"

NEUTRAL_LABELS = ("VARIANT-K", "VARIANT-M", "VARIANT-T")

REVIEW_SYSTEM = """You are reviewing candidate articles written from a fixed set of
sources. You are an editorial reviewer, not a publisher, and your reply is an assessment.

You are given the source material and two or three candidate articles under neutral
labels. You do not know who or what produced them, and there is no correct answer key.

Judge each candidate on:
  1. MATERIAL UNSUPPORTED CLAIMS -- a claim the sources do not carry. For each one you
     must quote the EXACT article span and name the source passage that fails to carry
     it. An objection without both is not usable and will be discarded.
  2. ATTRIBUTION AND QUALIFIERS -- did an attributed or hedged claim become a flat
     finding?
  3. QUOTATION FIDELITY -- is every quoted phrase in the sources, unaltered?
  4. EVENT, TIME, PLACE AND CAUSAL RELATIONSHIPS -- are two true facts joined into a
     relationship the sources never assert?
  5. ORIGINALITY BEYOND THE SOURCES -- does the article add understanding the strongest
     single source does not already give a reader?
  6. CONCRETE NARRATIVE DEVELOPMENT -- does material carry the argument, or does the
     article announce its own structure?
  7. ACCESSIBLE INTERNATIONAL READING -- would a reader outside the country follow it?
     Name any institution, acronym or local term left unexplained.
  8. REPETITION AND SOURCE-BOOKKEEPING PROSE.
  9. USEFUL EVIDENCE OMITTED -- something in the sources the article needed and dropped.

A LOW STYLE SCORE IS NOT A MATERIAL FACTUAL DEFECT, and a fluent article is not thereby
supported. Keep the two judgements apart. Minor imperfections are not material errors.

Reply with ONE JSON object:

{"reviews": [
  {"label": "VARIANT-K",
   "material_unsupported_claims": [
     {"article_span": "exact quote from the article",
      "why": "what the sources do not carry",
      "source_passage": "the passage that fails to carry it, or NONE_FOUND"}],
   "attribution_or_qualifier_losses": [{"article_span": "...", "why": "..."}],
   "quotation_problems": [{"article_span": "...", "why": "..."}],
   "relationship_problems": [{"article_span": "...", "why": "..."}],
   "unexplained_for_international_reader": ["..."],
   "useful_evidence_omitted": ["..."],
   "repetition_notes": ["..."],
   "originality_beyond_sources": "NONE|SOME|CLEAR, with one sentence of reason",
   "readability": "POOR|ADEQUATE|GOOD, with one sentence of reason",
   "material_defect_count": 0}],
 "preference": {"best": "VARIANT-K", "worst": "VARIANT-M",
                "reason": "one or two sentences",
                "confidence": "LOW|MEDIUM|HIGH"}}

If two candidates are indistinguishable in quality, say so in the reason and set
confidence LOW. Do not invent a difference."""


def shuffle_map(subject_id: str, arms: list) -> dict:
    """Deterministic per-subject relabelling. Reproducible, and not arm-ordered."""
    order = sorted(arms, key=lambda a: hashlib.sha256(
        ("%s|%s" % (subject_id, a)).encode()).hexdigest())
    return {NEUTRAL_LABELS[i]: arm for i, arm in enumerate(order)}


def sources_block(sources: list, per_source_chars: int = 5000) -> str:
    return "\n\n".join(
        "--- SOURCE %s | %s | %s\n%s"
        % (s.get("source_id"), s.get("publisher") or "", s.get("title") or "",
           (s.get("text") or "")[:per_source_chars])
        for s in sources)


def review_prompt(subject: str, sources: list, labelled: dict) -> str:
    parts = ["THE COMMISSIONING SUBJECT\n%s" % subject,
             "THE SOURCE MATERIAL\n%s" % sources_block(sources)]
    for label in sorted(labelled):
        parts.append("=== %s ===\n%s" % (label, labelled[label]))
    parts.append("Review every candidate above. Reply with one JSON object.")
    return "\n\n".join(parts)


def parse_review(reply: str) -> tuple:
    txt = (reply or "").strip()
    if txt.startswith("```"):
        txt = re.sub(r"^```[a-zA-Z]*\n?", "", txt)
        txt = re.sub(r"\n?```\s*$", "", txt)
    i, j = txt.find("{"), txt.rfind("}")
    if i < 0 or j <= i:
        return None, ["review reply carries no JSON object"]
    try:
        return json.loads(txt[i:j + 1]), []
    except Exception as exc:                                       # noqa: BLE001
        return None, ["review reply is not valid JSON: %s" % exc]


def usable_objections(review: dict) -> dict:
    """Keep only factual objections that carry BOTH an article span and a source passage.

    Section 16 requires exact spans for factual objections; an objection missing one is
    not discarded silently, it is counted separately so the reviewer's unlocated
    assertions are visible rather than folded into the defect count.
    """
    out = {}
    for r in review.get("reviews") or []:
        label = r.get("label")
        located, unlocated = [], []
        for c in r.get("material_unsupported_claims") or []:
            if (c.get("article_span") and c.get("source_passage")):
                located.append(c)
            else:
                unlocated.append(c)
        out[label] = {
            "located_material_objections": located,
            "unlocated_material_objections": unlocated,
            "located_count": len(located),
            "unlocated_count": len(unlocated),
            "attribution_or_qualifier_losses": r.get("attribution_or_qualifier_losses") or [],
            "quotation_problems": r.get("quotation_problems") or [],
            "relationship_problems": r.get("relationship_problems") or [],
            "unexplained_for_international_reader":
                r.get("unexplained_for_international_reader") or [],
            "useful_evidence_omitted": r.get("useful_evidence_omitted") or [],
            "originality_beyond_sources": r.get("originality_beyond_sources"),
            "readability": r.get("readability"),
        }
    return out


def review_variants(provider, *, subject_id: str, subject: str, sources: list,
                    variants: dict) -> dict:
    """One review call over all variants of one subject."""
    smap = shuffle_map(subject_id, sorted(variants))
    labelled = {label: variants[arm] for label, arm in smap.items()}
    prompt = review_prompt(subject, sources, labelled)
    comp = provider.complete(REVIEW_SYSTEM, prompt)
    review, errs = parse_review(comp.text)
    out = {
        "prompt_version": PROMPT_VERSION,
        "provider": comp.identity() if hasattr(comp, "identity") else {},
        "model_calls": 1,
        "parse_errors": errs,
        "shuffle_map": smap,
        "review": review,
        # Section 16, carried on the object rather than left to a report to remember.
        "assessment_not_owner_judgement": True,
        "not_independent_fact_checking": True,
    }
    if review is None:
        out["status"] = "REVIEW_REPLY_UNUSABLE"
        return out
    out["status"] = "OK"
    out["by_label"] = usable_objections(review)
    # De-blind for the analysis only. The reviewer never saw this mapping.
    out["by_arm"] = {smap[label]: v for label, v in out["by_label"].items()
                     if label in smap}
    pref = review.get("preference") or {}
    out["preference_by_arm"] = {
        "best": smap.get(pref.get("best")),
        "worst": smap.get(pref.get("worst")),
        "reason": pref.get("reason"),
        "confidence": pref.get("confidence"),
    }
    return out


def reconcile(review_a: dict, review_b: dict) -> dict:
    """Agreement, disagreement, and what the owner has to settle.

    A factual disagreement is NEVER resolved here -- not by majority, not by the verdict
    that would permit publication. It is routed.
    """
    out = {"reviewers": ["claude", "codex"], "per_arm": {}, "owner_review_needed": []}
    a_by = review_a.get("by_arm") or {}
    b_by = review_b.get("by_arm") or {}
    for arm in sorted(set(a_by) | set(b_by)):
        a, b = a_by.get(arm) or {}, b_by.get(arm) or {}
        an, bn = a.get("located_count", 0), b.get("located_count", 0)
        row = {
            "claude_located_material_objections": an,
            "codex_located_material_objections": bn,
            "agree_on_material_defects": an == bn,
            "claude_readability": a.get("readability"),
            "codex_readability": b.get("readability"),
            "claude_originality": a.get("originality_beyond_sources"),
            "codex_originality": b.get("originality_beyond_sources"),
        }
        if (an == 0) != (bn == 0):
            # One reviewer found a material defect and the other found none. This is the
            # disagreement that matters and it is the owner's to settle.
            row["unresolved_substantive_disagreement"] = True
            out["owner_review_needed"].append({
                "arm": arm,
                "claude_objections": a.get("located_material_objections") or [],
                "codex_objections": b.get("located_material_objections") or [],
                "why": "one reviewer reports a located material defect and the other "
                       "reports none; not settled by vote",
            })
        else:
            row["unresolved_substantive_disagreement"] = False
        out["per_arm"][arm] = row

    pa = (review_a.get("preference_by_arm") or {}).get("best")
    pb = (review_b.get("preference_by_arm") or {}).get("best")
    out["preference"] = {"claude_best": pa, "codex_best": pb, "agree": pa == pb}
    out["settled_by_vote"] = False
    return out
