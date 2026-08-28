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

TOP_SENTENCES = 6                # total ranked blocks in the final bundle
PER_SOURCE_TOP = 2               # strongest candidates kept from any ONE source
CONTEXT_WINDOW = 1               # sentences either side of the best block per source
MIN_QUERY_TOKENS = 3             # below this a claim cannot be ranked on, only escalated
MIN_COVERAGE_RATIO = 0.35        # share of the claim's own IDF mass the best sentence
                                 # must match. A ratio, not an absolute score, because an
                                 # absolute one is a function of corpus size.
SOURCE_RELEVANCE_RATIO = 0.12    # a source earns a slot by matching the claim, not by
                                 # existing: below this share of the claim's IDF mass it
                                 # contributes nothing.
CONFLICT_MIN_SHARED = 2          # subject anchors a rival statement must share
MAX_CONFLICT_BLOCKS = 2
FULL_SOURCE_CHARS = 6_000        # halved after the full-source fallback was measured
                                 # producing false UNSUPPORTED verdicts: 9k of anchor
                                 # prose buried the sentence that answered the claim.
FOCUSED_EXCERPT_SENTENCES = 8    # the rung between ranked blocks and whole-source bulk
FULL_PACK_CHARS = 40_000         # the pack's own budget: full-pack fallback is bounded

RETRIEVED = "RETRIEVED"
FALLBACK_EXCERPT = "FALLBACK_FOCUSED_EXCERPT"
FALLBACK_SOURCE = "FALLBACK_FULL_SOURCE"
FALLBACK_PACK = "FALLBACK_FULL_PACK"
INCOMPLETE = "EVIDENCE_RETRIEVAL_INCOMPLETE"

# A claim's "value tokens" are the specific things sources disagree about: quantities,
# years, ordinals. They are deliberately EXCLUDED from the query used to hunt for a
# rival statement -- searching for "nearly 100" cannot find "more than 100", and the
# conflicting value is the thing we do not know yet. The subject anchors are what stay.
_VALUE = re.compile(r"^(?:\d[\d,.]*|nearly|almost|about|around|approximately|more|over|"
                    r"under|fewer|less|least|most|first|second|third|last)$")

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

    def _subject_anchors(self, claim: str) -> set:
        """The claim's NON-value tokens: what it is about, not what it says the number
        is. Deliberately NOT filtered by document frequency -- a rival statement of the
        same proposition shares exactly the common subject words ("retrospective",
        "pieces"), so filtering them out is filtering out the thing being matched on.
        Precision comes from the rival-value requirement below, not from rarity."""
        return {w for w in _tokens(claim) if not _VALUE.match(w)}

    def _values(self, text: str) -> set:
        return {w for w in _tokens(text) if _VALUE.match(w)}

    def _per_source_candidates(self, q, q_mass):
        """Score inside each source and keep its strongest few. Global ranking let one
        verbose source take every slot -- measured: a season-listing page contributed
        most of the bundle for a claim whose rival statement sat in another source."""
        out = {}
        for sid, idxs in self.by_source.items():
            scored = sorted(((self._score(q, self.units[i][1]), i) for i in idxs), reverse=True)
            top = [(sc, i) for sc, i in scored[:PER_SOURCE_TOP] if sc > 0]
            if top and (top[0][0] / q_mass) >= SOURCE_RELEVANCE_RATIO:
                out[sid] = top
        return out

    def _block(self, i, score, context=False):
        sid, sent, pos = self.units[i]
        blocks = [{"source_id": sid, "exact_span": sent, "position": pos,
                   "score": round(score, 3)}]
        if context:
            for j in (i - 1, i + 1):
                if 0 <= j < len(self.units) and self.units[j][0] == sid:
                    blocks.append({"source_id": self.units[j][0],
                                   "exact_span": self.units[j][1],
                                   "position": self.units[j][2], "score": round(score, 3)})
        return blocks

    def _conflict_candidates(self, claim, chosen_ids, q_mass):
        """Look for a source stating the SAME proposition with a DIFFERENT specific
        value. Deterministic and general: it never looks for a particular word pair, it
        looks for shared subject anchors plus a value token the claim does not have --
        which is as true of dates, titles and institutions as of counts."""
        anchors = self._subject_anchors(claim)
        if len(anchors) < CONFLICT_MIN_SHARED:
            return []
        claim_values = self._values(claim)
        out = []
        for sid, idxs in self.by_source.items():
            best = None
            for i in idxs:
                sent = self.units[i][1]
                sent_values = self._values(sent)
                shared = anchors & set(_tokens(sent))
                # A SHARED value counts as a subject anchor too. Two sentences that name
                # the same magnitude and differ only in the qualifier -- "nearly 100" and
                # "more than 100" -- are talking about the same proposition, and that
                # agreement is itself the strongest evidence they are comparable.
                signal = len(shared) + len(claim_values & sent_values)
                if signal < CONFLICT_MIN_SHARED:
                    continue
                rival = sent_values - claim_values
                if not rival:
                    continue
                sc = self._score(list(anchors), sent)
                if best is None or sc > best[0]:
                    best = (sc, i, sorted(rival)[:4])
            # No relevance-ratio gate here on purpose. The ranked path uses that gate to
            # keep irrelevant sources out of the bundle; this path is looking for a
            # source that says the SAME thing differently, and such a source can score
            # low precisely because it does not repeat the claim's own wording. Its
            # precision control is the pair of requirements already met: enough shared
            # subject anchors, and a specific value the claim does not carry.
            if best and best[0] > 0:
                out.append(best)
        out.sort(reverse=True)
        return out[:MAX_CONFLICT_BLOCKS]

    def retrieve(self, claim: str) -> dict:
        """Evidence for ONE claim, source-aware, conflict-sensitive, with an escalation
        ladder. Escalation is a coverage decision and never a verdict: nothing here may
        conclude that a claim is unsupported."""
        q = _tokens(claim)
        if not self.units:
            return {"status": INCOMPLETE, "reason": "pack carries no indexable text",
                    "blocks": [], "top_score": 0.0, "coverage_ratio": 0.0,
                    "query_tokens": len(q), "sources": [], "conflict_sources": []}
        q_mass = sum(math.log(self.n / (1 + self.df.get(w, 0))) for w in set(q)) or 1.0
        per_source = self._per_source_candidates(q, q_mass)
        flat = sorted(((sc, i, sid) for sid, top in per_source.items() for sc, i in top),
                      reverse=True)
        top_score = round(flat[0][0], 3) if flat else 0.0
        ratio = round(top_score / q_mass, 3)

        conflicts = self._conflict_candidates(claim, set(per_source), q_mass)
        conflict_ids = []

        if len(q) >= MIN_QUERY_TOKENS and ratio >= MIN_COVERAGE_RATIO and flat:
            blocks, seen, best_per_source = [], set(), set()
            for sc, i, sid in flat[:TOP_SENTENCES]:
                for b in self._block(i, sc, context=(sid not in best_per_source)):
                    key = (b["source_id"], b["position"])
                    if key not in seen:
                        seen.add(key)
                        blocks.append(b)
                best_per_source.add(sid)
            for sc, i, rival in conflicts:
                key = (self.units[i][0], self.units[i][2])
                if key not in seen:
                    seen.add(key)
                    b = self._block(i, sc)[0]
                    b["conflict_candidate"] = True
                    b["rival_values"] = rival
                    blocks.append(b)
                    conflict_ids.append(b["source_id"])
            if blocks:
                return {"status": RETRIEVED, "blocks": blocks, "top_score": top_score,
                        "coverage_ratio": ratio, "query_tokens": len(q), "reason": "",
                        "sources": sorted({b["source_id"] for b in blocks}),
                        "conflict_sources": sorted(set(conflict_ids))}

        # Not rankable: escalate by the smallest step that could carry the answer.
        best_sid = flat[0][2] if flat else (
            max(((self._score(q, s), sid) for sid, s, _ in self.units), default=(0, None))[1])
        if best_sid:
            idxs = self.by_source.get(best_sid, [])
            # Ranked by score, not by position. Taking the first N touching sentences is
            # a positional bias, and it cost a real needle: the sentence answering a
            # claim about a Bible sat late in the source, and the excerpt stopped short
            # of it while carrying six earlier sentences that shared only a name.
            touched = sorted(((self._score(q, self.units[i][1]), i) for i in idxs
                              if set(_tokens(self.units[i][1])) & set(q)), reverse=True)
            if touched:
                blocks = [self._block(i, sc)[0]
                          for sc, i in touched[:FOCUSED_EXCERPT_SENTENCES]]
                return {"status": FALLBACK_EXCERPT, "blocks": blocks, "top_score": top_score,
                        "coverage_ratio": ratio, "query_tokens": len(q),
                        "reason": "claim too short or match too weak to rank on; "
                                  "supplying the sentences of the best source that touch it",
                        "sources": [best_sid], "conflict_sources": []}
            src = next((s for s in self.pack["sources"] if s["source_id"] == best_sid), None)
            if src and src.get("text"):
                return {"status": FALLBACK_SOURCE, "top_score": top_score,
                        "coverage_ratio": ratio, "query_tokens": len(q),
                        "reason": "no sentence in the best source shares a token with the "
                                  "claim; supplying that source, bounded",
                        "sources": [best_sid], "conflict_sources": [],
                        "blocks": [{"source_id": best_sid,
                                    "exact_span": src["text"][:FULL_SOURCE_CHARS],
                                    "position": -1, "score": top_score}]}
        total = sum(len(s.get("text", "")) for s in self.pack.get("sources", []))
        if 0 < total <= FULL_PACK_CHARS:
            return {"status": FALLBACK_PACK, "top_score": top_score, "coverage_ratio": ratio,
                    "query_tokens": len(q),
                    "reason": "no lexical match anywhere; supplying the whole bounded pack",
                    "sources": [s["source_id"] for s in self.pack.get("sources", [])],
                    "conflict_sources": [],
                    "blocks": [{"source_id": s["source_id"], "exact_span": s.get("text", ""),
                                "position": -1, "score": 0.0}
                               for s in self.pack.get("sources", []) if s.get("text")]}
        return {"status": INCOMPLETE, "top_score": top_score, "coverage_ratio": ratio,
                "query_tokens": len(q), "sources": [], "conflict_sources": [],
                "reason": "no evidence could be assembled within the pack budget",
                "blocks": []}


def render(evidence: dict, per_block_chars: int = 1_200) -> str:
    """The evidence block the classifier sees. Source-labelled, verbatim, bounded. A
    block found by the conflict probe is marked as such: the classifier is told that a
    source states this proposition differently, and left to judge whether it matters."""
    out = []
    for b in evidence.get("blocks", []):
        tag = "  (states this differently)" if b.get("conflict_candidate") else ""
        out.append("[%s]%s\n%s" % (b["source_id"], tag, (b["exact_span"] or "")[:per_block_chars]))
    return "\n\n".join(out)
