"""
evidence.py -- deterministic evidence retrieval over the frozen Research Pack.
SHADOW ONLY. No model, no network, no embeddings.

WHY DETERMINISTIC
The measured question was whether a claim's supporting or conflicting span can be found
without a model. On the frozen Minnie Evans pack, TF-IDF sentence retrieval with a
one-sentence context window found 10 of 11 hand-annotated evidence needles, including
both sides of a genuine source conflict, while sending ~7k characters per claim instead
of the pack's 40k.

WHY THE FALLBACK MATTERS MORE THAN THE RECALL
The one miss was "Evans was self-taught" -- four words, one content word, nothing rare
to match on. A short claim is not a false claim, and a retrieval miss must never reach a
classifier as evidence of absence. So retrieval reports its own confidence, escalates
deterministically when it is low, and can say EVIDENCE_RETRIEVAL_INCOMPLETE instead of
handing over thin evidence and letting UNSUPPORTED be inferred from it.
"""
from __future__ import annotations

import math
import re

TOP_SENTENCES = 6
CONTEXT_WINDOW = 1               # sentences either side of a hit
MIN_QUERY_TOKENS = 3             # below this a claim cannot be retrieved on, only escalated
MIN_COVERAGE_RATIO = 0.35        # share of the claim's own IDF mass the best sentence
                                 # must match. A ratio, not an absolute score, because an
                                 # absolute one is a function of corpus size: the same
                                 # claim scores differently against a 5-sentence pack and
                                 # a 150-sentence one, and the question ("did we actually
                                 # find this claim's distinctive words?") is the same.
FULL_SOURCE_CHARS = 12_000       # a whole source, the pack's own per-source cap
FULL_PACK_CHARS = 40_000         # the pack's own budget: full-pack fallback is bounded

RETRIEVED = "RETRIEVED"
FALLBACK_SOURCE = "FALLBACK_FULL_SOURCE"
FALLBACK_PACK = "FALLBACK_FULL_PACK"
INCOMPLETE = "EVIDENCE_RETRIEVAL_INCOMPLETE"

_STOP = set("the a an of in on at to is are was were be been being and or but for nor so "
            "that this these those it its as by with from into over under about after "
            "before while when where which who whom whose they them their she her he him "
            "his we us our you your i me my not no also then than there here".split())


def _tokens(text):
    return [w for w in re.findall(r"[a-z0-9']+", (text or "").lower())
            if w not in _STOP and len(w) > 2]


def _sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text or ""))
            if len(s.split()) > 3]


class PackIndex:
    """Sentence-level index over the pack's carried source text. Deterministic and
    replayable: same pack in, same index and same ranking out."""

    def __init__(self, pack: dict):
        self.pack = pack or {}
        self.units = []                      # (source_id, sentence, position)
        for src in self.pack.get("sources", []):
            for i, sent in enumerate(_sentences(src.get("text", ""))):
                self.units.append((src["source_id"], sent, i))
        self.df = {}
        for _, sent, _ in self.units:
            for w in set(_tokens(sent)):
                self.df[w] = self.df.get(w, 0) + 1
        self.n = max(1, len(self.units))
        self.by_source = {}
        for idx, (sid, _, _) in enumerate(self.units):
            self.by_source.setdefault(sid, []).append(idx)

    def _score(self, query_tokens, sentence):
        overlap = set(query_tokens) & set(_tokens(sentence))
        return sum(math.log(self.n / (1 + self.df.get(w, 0))) for w in overlap)

    def retrieve(self, claim: str) -> dict:
        """Evidence for ONE claim, with its own confidence and an escalation ladder.

        Ladder, in order, each step bounded: ranked sentences + context -> the full text
        of the best-scoring source -> the whole pack (bounded at its own 40k budget) ->
        EVIDENCE_RETRIEVAL_INCOMPLETE. Escalation is a coverage decision, never a
        verdict: nothing here may conclude that a claim is unsupported.
        """
        q = _tokens(claim)
        if not self.units:
            return {"status": INCOMPLETE, "reason": "pack carries no indexable text",
                    "blocks": [], "top_score": 0.0, "query_tokens": len(q)}
        scored = sorted(((self._score(q, sent), i) for i, (_, sent, _) in enumerate(self.units)),
                        reverse=True)
        top_score = round(scored[0][0], 3) if scored else 0.0
        q_mass = sum(math.log(self.n / (1 + self.df.get(w, 0))) for w in set(q)) or 1.0
        ratio = round(top_score / q_mass, 3)

        if len(q) >= MIN_QUERY_TOKENS and ratio >= MIN_COVERAGE_RATIO:
            keep, seen = [], set()
            for sc, i in scored[:TOP_SENTENCES]:
                if sc <= 0:
                    continue
                sid = self.units[i][0]
                for j in range(max(0, i - CONTEXT_WINDOW), min(len(self.units), i + CONTEXT_WINDOW + 1)):
                    if j in seen or self.units[j][0] != sid:
                        continue
                    seen.add(j)
                    keep.append({"source_id": sid, "exact_span": self.units[j][1],
                                 "position": self.units[j][2], "score": round(sc, 3)})
            if keep:
                return {"status": RETRIEVED, "blocks": keep, "top_score": top_score,
                        "coverage_ratio": ratio, "query_tokens": len(q), "reason": ""}

        # Low signal or weak match: escalate rather than answer thinly.
        best_sid = self.units[scored[0][1]][0] if scored and scored[0][0] > 0 else None
        if best_sid:
            src = next((s for s in self.pack["sources"] if s["source_id"] == best_sid), None)
            if src and src.get("text"):
                return {"status": FALLBACK_SOURCE, "top_score": top_score,
                        "coverage_ratio": ratio, "query_tokens": len(q),
                        "reason": "claim too short or match too weak to rank on; "
                                  "supplying the whole best-scoring source",
                        "blocks": [{"source_id": best_sid,
                                    "exact_span": src["text"][:FULL_SOURCE_CHARS],
                                    "position": -1, "score": top_score}]}
        total = sum(len(s.get("text", "")) for s in self.pack.get("sources", []))
        if 0 < total <= FULL_PACK_CHARS:
            return {"status": FALLBACK_PACK, "top_score": top_score,
                    "coverage_ratio": ratio, "query_tokens": len(q),
                    "reason": "no lexical match anywhere; supplying the whole bounded pack",
                    "blocks": [{"source_id": s["source_id"], "exact_span": s.get("text", ""),
                                "position": -1, "score": 0.0}
                               for s in self.pack.get("sources", []) if s.get("text")]}
        return {"status": INCOMPLETE, "top_score": top_score, "coverage_ratio": ratio,
                "query_tokens": len(q),
                "reason": "no evidence could be assembled within the pack budget",
                "blocks": []}


def render(evidence: dict, per_block_chars: int = 1_200) -> str:
    """The evidence block the classifier sees. Source-labelled, verbatim, bounded."""
    out = []
    for b in evidence.get("blocks", []):
        out.append("[%s]\n%s" % (b["source_id"], (b["exact_span"] or "")[:per_block_chars]))
    return "\n\n".join(out)
