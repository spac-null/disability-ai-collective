"""A claim the run is testing, proposed before the evidence exists.

THE ORDER THIS CHANGES, AND WHY

The engine reports in this order:

    Research -> Ledger (freeze every fact) -> Worth (find a lens IN the pile) ->
    Architecture (select facts) -> Writer

Worth runs AFTER the evidence is frozen and asks what reading can be found in whatever
happens to be there. A lens discovered inside a pile can only DESCRIBE the pile. That is
a report by construction, and it explains three separately measured defects at once:

  REGISTER    SOUNDS_LIKE_REPORT is the owner's most-pressed reaction, 7 times across 10
              reading sessions, ahead of LIST_OF_FACTS at 4 and NO_STORY at 3.
  DENSITY     engine drafts carry 4.7 proper nouns and 1.2 numbers per 100 words against
              3.0 and 0.7 in this publication's own PUBLISHED articles, in 25% less
              space. Without a claim, every fact is equally admissible, so nothing
              selects. Overload is not a writing failure; it is a missing criterion.
  JOINS       the same unlicensed join survived five independent controls on 2026-09-29.
              The Writer was manufacturing the tension the pipeline never supplied.

Hypothesis-driven reporting is the established remedy and its discipline is explicit: the
hypothesis may be amended whenever the evidence requires, and the reporter must stay open
to evidence that contradicts it. The claim exists first; the facts are recruited to test
it and are free to refuse.

WHAT A HYPOTHESIS IS HERE

    {"claim":            "a sentence that could be false",
     "refuted_if":       "the finding that would kill it",
     "matters_because":  "what changes for a reader if it holds"}

A SUBJECT IS NOT A CLAIM. "The Prinzhorn collection's inventory book" is a topic;
"the inventory book recorded a person more completely than it recorded their work" is a
claim, because evidence could show the opposite. The checks below refuse the first kind
as far as a deterministic test can: a claim that merely restates its own subject, or one
with no stated way to be wrong, is not a hypothesis.

WHAT THIS MODULE DOES NOT DO

It does not judge whether a claim is TRUE -- that is what the run is for, and a refuted
hypothesis is a good outcome and often the better story. It does not score interest. It
refuses only what is deterministically refusable, the same posture as every other gate
here.
"""

from __future__ import annotations

import re

# A claim has to be able to be wrong. These are the shapes that cannot be: a question has
# no truth value, and a bare topic asserts nothing.
_QUESTION = re.compile(r"^\s*(?:who|what|when|where|why|how|is|are|does|do|did|can|could|"
                       r"should|would|will)\b.*\?\s*$", re.I)
_MIN_CLAIM_WORDS = 6
_MIN_REFUTED_WORDS = 4

# A claim needs a verb to assert anything. Deliberately crude and deliberately generous:
# this refuses a noun phrase, not a sentence it merely dislikes.
_HAS_VERB = re.compile(
    r"\b(?:is|are|was|were|has|have|had|does|do|did|makes?|made|records?|recorded|"
    r"shows?|showed|holds?|held|gives?|gave|takes?|took|treats?|treated|counts?|"
    r"counted|leaves?|left|keeps?|kept|turns?|turned|becomes?|became|carries|carried|"
    r"produces?|produced|allows?|allowed|refuses?|refused|names?|named|decides?|"
    r"decided|appears?|appeared|remains?|remained|costs?|cost|fails?|failed)\b", re.I)


def _words(text: str) -> list:
    return re.findall(r"[a-zA-ZÀ-ɏ]+", str(text or ""))


def _overlap(a: str, b: str) -> float:
    """Content-word overlap, as a fraction of the shorter side."""
    STOP = {"the", "a", "an", "of", "and", "or", "to", "in", "on", "for", "that", "this",
            "with", "from", "by", "as", "at", "its", "it", "was", "were", "is", "are"}
    sa = {w.lower() for w in _words(a) if len(w) > 3 and w.lower() not in STOP}
    sb = {w.lower() for w in _words(b) if len(w) > 3 and w.lower() not in STOP}
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / min(len(sa), len(sb))


def from_instrument(question: dict) -> dict:
    """The run's claim, taken from the approved instrument it already drew.

    NOT INVENTED. An earlier version of this module asked a model to propose a claim with
    a refutation attached -- while 48 owner-reviewed instruments, each carrying its own
    MECHANISM and 43 of them a DISCONFIRMING SHAPE, were being loaded and then parsed past
    four lines into `knowledge_first.load_questions`. The claim was always there. Reading
    it costs nothing, invents nothing, and the hypothesis is the owner's rather than a
    model's guess at one.

    Returns {} when the instrument carries no mechanism, so a run with nothing to test
    behaves exactly as it did before any of this existed.
    """
    q = question or {}
    claim = str(q.get("mechanism") or "").strip()
    if not claim:
        return {}
    return {"claim": claim,
            "refuted_if": str(q.get("disconfirming_shape") or "").strip(),
            "matters_because": str(q.get("what_this_adds") or "").strip(),
            "instrument": str(q.get("id") or "")}


def validate(hypothesis: dict, subject: str = "") -> list:
    """Failures that make this not a testable claim. Empty means usable."""
    errs = []
    if not isinstance(hypothesis, dict):
        return ["hypothesis is not an object"]

    claim = str(hypothesis.get("claim") or "").strip()
    refuted = str(hypothesis.get("refuted_if") or "").strip()
    matters = str(hypothesis.get("matters_because") or "").strip()

    if len(_words(claim)) < _MIN_CLAIM_WORDS:
        errs.append("claim is too short to assert anything (%d words, floor %d)"
                    % (len(_words(claim)), _MIN_CLAIM_WORDS))
    if _QUESTION.match(claim):
        errs.append("claim is a question; a question has no truth value to test")
    if claim and not _HAS_VERB.search(claim):
        errs.append("claim has no verb -- it names a topic rather than asserting "
                    "something about it")
    if len(_words(refuted)) < _MIN_REFUTED_WORDS:
        errs.append("refuted_if does not say what would kill the claim; a claim that "
                    "cannot be wrong is not a hypothesis")
    if not matters:
        errs.append("matters_because is empty -- a true claim nobody is changed by is "
                    "not worth the run")

    # A CLAIM THAT RESTATES ITS SUBJECT IS A TOPIC IN A SENTENCE'S CLOTHING. This is the
    # deterministic half of falsifiability: if the claim says nothing the subject did not
    # already say, there is nothing for evidence to contradict.
    if subject and claim and _overlap(claim, subject) > 0.8:
        errs.append("claim restates the subject (%.0f%% of its content words) rather "
                    "than asserting something about it" % (100 * _overlap(claim, subject)))
    if claim and refuted and _overlap(claim, refuted) > 0.9:
        errs.append("refuted_if restates the claim instead of naming evidence against it")
    return errs


def block(hypothesis: dict) -> str:
    """The claim as later stages see it. Empty when there is none.

    Phrased so a stage reads it as something to TEST, never as something established.
    The engine's whole safety posture is that nothing unproved may be asserted, and a
    hypothesis is by definition unproved -- so it arrives labelled as such.
    """
    if not isinstance(hypothesis, dict):
        return ""
    claim = str(hypothesis.get("claim") or "").strip()
    if not claim:
        return ""
    lines = ["",
             "THE CLAIM THIS RUN IS TESTING. It comes from the approved instrument this",
             "run drew, written by the owner before any evidence was read.",
             "It is NOT established. The evidence may support it, refuse it, or",
             "complicate it, and all three are real outcomes -- a refusal is often the",
             "better story.",
             "  claim        : %s" % claim]
    if hypothesis.get("refuted_if"):
        lines.append("  refuted if   : %s" % str(hypothesis["refuted_if"]).strip())
    if hypothesis.get("matters_because"):
        lines.append("  matters      : %s" % str(hypothesis["matters_because"]).strip())
    return "\n".join(lines)
