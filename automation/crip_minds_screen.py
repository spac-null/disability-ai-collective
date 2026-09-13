#!/usr/bin/env python3
"""crip_minds_screen.py -- the LIGHT commissioning screen, before expensive Research.

WHY THIS EXISTS. The 2026-09-13 09:00 run is the whole argument. Selector V2 ranked a
Verge story about schools and Big Tech top of the pool on exactly the properties it is
good at -- concrete subject, narrative material, source depth, researchability,
freshness -- and every one of those readings was correct. Research passed it. The Ledger
granted 92 facts. Then Worth said GREAT_GENERAL_STORY_WRONG_PUBLICATION and production
stopped, which is Worth working, not failing.

What that sequence cost is the point: a full targeted Research pass and a 92-fact Ledger
were spent to discover something that could have been asked in one bounded call before
any of it. The selector optimises for whether a story is WRITEABLE. Nothing upstream of
Research asked whether it is COMMISSIONABLE BY THIS PUBLICATION.

This asks that, once, cheaply, and only that.

WHAT IT IS NOT.
  * NOT a Ledger. It grants ZERO factual permission. Nothing it returns may reach the
    Writer, appear in prose, or be treated as established. It is shown the seed's own
    headline and a bounded slice of the already-acquired source text, and it produces a
    QUESTION -- the same hard boundary the Perspective Library has always had: perspective
    knowledge licenses a question, never a fact.
  * NOT Research. It fetches nothing, searches nothing, and verifies nothing. Whether the
    hypothesis it names is TRUE is Research's decision, and whether the article was earned
    is still Worth's. This moves no standard downstream and relaxes none.
  * NOT a second Worth. A PASS here is permission to spend Research, nothing more. Worth
    must still be allowed to kill everything this lets through, and it is.

WHAT IT DOES ASK (the brief's six questions, in one call):
  1. is there a concrete carrier -- a person, event, object, practice, artwork, discovery?
  2. is there a plausible NON-OBVIOUS Crip Minds question?
  3. which hidden assumption may be operating?
  4. does disability-rooted knowledge potentially CONTRIBUTE something here, rather than
     merely expose a lack of accessibility?
  5. is this primarily an access/compliance/infrastructure story? (NO_ACCESS_ORIGIN)
  6. is there likely enough evidence depth to TEST the hypothesis -- or kill it?

The axis vocabulary and the hard boundary are not re-authored here. They are the compact
Perspective Library that perspective_explorer.py already carries and that four owner
review passes already settled, imported rather than copied so the two cannot drift.
"""
from __future__ import annotations

import os

from new_engine_v1.perspective_explorer import PERSPECTIVE_MATERIAL
from new_engine_v1.provider import parse_json_object

SCREEN_ENV = "CRIPMINDS_COMMISSIONING_SCREEN"

PASS = "PASS"
REJECT = "REJECT"

# Reject reasons this module emits itself, so the desk can count them without parsing
# model prose.
NO_CARRIER = "NO_CARRIER"
NO_QUESTION = "NO_QUESTION"
ACCESS_ORIGIN = "ACCESS_ORIGIN"
THIN_EVIDENCE = "THIN_EVIDENCE"
SCREEN_UNAVAILABLE = "SCREEN_UNAVAILABLE"

MAX_SOURCE_CHARS = 4_000


def screen_enabled(env=None) -> bool:
    """On by default, the same convention as perspective_explorer_enabled -- an operator
    can take it out of the path without a deploy, and an unset variable changes nothing
    about the intended behaviour."""
    v = (env if env is not None else os.environ).get(SCREEN_ENV, "").strip().lower()
    return v not in ("0", "off", "false", "no")


SCREEN_SYSTEM = (
    "You are the commissioning desk for Crip Minds, before any research has been done.\n"
    "\n"
    "WHAT CRIP MINDS IS. Not 'find a mainstream story and attach a disability angle'. It "
    "reads the world THROUGH disability as a way of knowing. The standing question is: "
    "what has disability already taught, invented, noticed, or made visible about the "
    "ordinary world? Disabled ways of perceiving, communicating, making, classifying, "
    "navigating, depending, attending, timing, sensing, remembering, interpreting, "
    "authoring and participating have produced knowledge, art, technique, intellectual "
    "practice, and different models of ordinary things. That is the territory.\n"
    "\n"
    "YOUR JOB. You are shown ONE candidate story that a general news selector ranked "
    "highly for narrative richness and researchability. Those judgements are already made "
    "and you are not repeating them. You answer ONE question: is it worth spending a full "
    "targeted research pass on this for THIS publication? You are generating a "
    "HYPOTHESIS, not a finding. You establish nothing, and everything you name will be "
    "independently researched afterwards and dropped if research cannot support it.\n"
    "\n"
    "ANSWER THESE, IN ORDER:\n"
    "\n"
    "1. CARRIER. Is there a concrete person, event, object, practice, artwork, "
    "experiment, controversy or discovery carrying this story? A theme is not a story. A "
    "trend is not a story. A press release is not a story. If there is no carrier with "
    "people, time, change, tension and consequence, REJECT.\n"
    "\n"
    "2. QUESTION. Is there a plausible NON-OBVIOUS Crip Minds question here -- one this "
    "subject genuinely supplies a carrier for, not one the vocabulary merely allows? It "
    "must be able to come back NOTHING from real research. A question that cannot fail is "
    "not a question.\n"
    "\n"
    "3. ASSUMPTION. Which hidden assumption may be operating -- about perception, "
    "communication, timing, classification, cognition, assistance, dependence, sensory "
    "knowledge, legibility, autonomy, participation, or normal functioning?\n"
    "\n"
    "4. CONTRIBUTION. Does disability-rooted knowledge potentially CONTRIBUTE something "
    "here -- a technique, a way of knowing, an authorship, a different model of the "
    "ordinary -- rather than merely expose that something is inaccessible? If the only "
    "thing disability does in this story is reveal a lack, that is not a contribution.\n"
    "\n"
    "5. NO_ACCESS_ORIGIN -- THE ABSOLUTE RULE. Access service, accommodation, compliance "
    "and built-environment provision may be EVIDENCE inside a story. They may never be "
    "the ORIGIN of one. Ramps, stairs, lifts, transit access, building accessibility, "
    "compliance announcements, 'this product is now accessible', generic platform "
    "accessibility, vendor feature announcements and product release notes are NOT Crip "
    "Minds insights by themselves.\n"
    "  APPLY THIS TEST: remove the accessibility and compliance language from your "
    "proposed question. If the question disappears, set access_origin true and REJECT -- "
    "UNLESS there is a genuinely surprising deeper mechanism that survives the removal, "
    "in which case name that mechanism explicitly in why_this_might_matter.\n"
    "\n"
    "6. EVIDENCE DEPTH. Is there likely enough documented material -- named people, "
    "records, primary sources, institutional documents -- for research to TEST this "
    "hypothesis and, if it is wrong, to kill it? If the honest answer is that research "
    "would find only the one article in front of you, REJECT.\n"
    "\n"
    "NO PROXIES, AND THE REJECTIONS THAT MATTER MOST. Never reason that imperfection is "
    "disability, that friction is accessibility, that another marginalised group's "
    "situation licenses a reading about this one, or that difficulty is Crip Minds. "
    "Mainstream tech-policy friction, platform governance, product releases and generic "
    "business or education coverage are NOT Crip Minds stories merely because the "
    "mechanism is interesting -- a great general story belongs in a general publication, "
    "and saying so here costs nothing and saves a full research pass.\n"
    "\n"
    "REJECTING IS THE COMMON, CORRECT ANSWER. Most candidates are not Crip Minds stories. "
    "You lose nothing by refusing one and you cost the publication a great deal by "
    "manufacturing a question so that something can proceed. Do not reach.\n"
    "\n"
    "REFERENCE MATERIAL -- the reviewed Perspective Library, in compact index form. It is "
    "an index, never evidence about the subject in front of you, and nothing in it may "
    "become a claim about this subject:\n%s"
)

SCREEN_SCHEMA = (
    "Reply with ONE JSON object and no prose outside it:\n"
    '{"carrier": "the concrete person, event, object, practice, artwork or discovery '
    'this rests on -- or \\"none\\"",\n'
    ' "question": "one sentence: the non-obvious Crip Minds question this subject could '
    'carry -- or \\"none\\"",\n'
    ' "perspective_or_axis": "which axis or library instrument this draws on, or '
    '\\"none\\" if the question came from the subject alone",\n'
    ' "assumption": "one sentence: the hidden assumption that may be operating",\n'
    ' "why_this_might_matter": "one sentence: what disability-rooted knowledge would '
    'CONTRIBUTE here, beyond exposing a lack of access",\n'
    ' "access_origin": true or false,\n'
    ' "evidence_depth": "one sentence: what documented material research would likely '
    'find that could confirm OR kill this",\n'
    ' "likely_testable": true or false,\n'
    ' "verdict": "PASS" or "REJECT",\n'
    ' "reject_reason": "one sentence if REJECT, else empty string"}'
)


def screen_prompt(title: str, summary: str, source_name: str, source_text: str) -> str:
    body = (source_text or "").strip()[:MAX_SOURCE_CHARS]
    return "\n".join([
        "CANDIDATE STORY",
        "  source:  %s" % (source_name or "unknown"),
        "  headline: %s" % (title or "(untitled)"),
        "  summary:  %s" % (summary or "(none)")[:600],
        "",
        "WHAT THE SOURCE SAYS (already acquired; an excerpt, not the whole article):",
        "<<<SOURCE",
        body or "(no source text available)",
        "SOURCE>>>",
        "",
        SCREEN_SCHEMA,
    ])


def _none(v) -> bool:
    return str(v or "").strip().lower() in ("", "none", "no", "n/a", "null")


def screen(provider, *, title: str = "", summary: str = "", source_name: str = "",
           source_text: str = "") -> dict:
    """ONE model call. Returns a verdict record; licenses nothing.

    A TECHNICAL FAILURE IS NOT AN EDITORIAL REJECTION, and the two must not arrive at the
    caller looking alike -- that is the exact failure knowledge_first.SearchUnavailable was
    created to stop, where a 403 and 'the world has nothing' were both reported as
    scarcity. A call that could not run returns REJECT with `technical_failure` set, and
    the desk escalates it to an operator instead of quietly trying the next candidate as
    though this one had been judged.
    """
    rec = {"ran": False, "verdict": REJECT, "carrier": "", "question": "",
           "perspective_or_axis": "", "assumption": "", "why_this_might_matter": "",
           "access_origin": False, "evidence_depth": "", "likely_testable": False,
           "reject_reason": "", "technical_failure": False, "model_calls": 0}
    try:
        comp = provider.complete(
            system=SCREEN_SYSTEM % PERSPECTIVE_MATERIAL,
            user=screen_prompt(title, summary, source_name, source_text),
            max_tokens=1_200)
        obj = parse_json_object(comp.text)
    except Exception as e:                                              # noqa: BLE001
        rec["technical_failure"] = True
        rec["reject_reason"] = SCREEN_UNAVAILABLE
        rec["error"] = "%s: %s" % (type(e).__name__, str(e)[:200])
        return rec

    rec["ran"] = True
    rec["model_calls"] = 1
    rec["_provider"] = comp.identity() if hasattr(comp, "identity") else {}
    for k in ("carrier", "question", "perspective_or_axis", "assumption",
              "why_this_might_matter", "evidence_depth"):
        rec[k] = "" if _none(obj.get(k)) else str(obj.get(k)).strip()
    rec["access_origin"] = bool(obj.get("access_origin"))
    rec["likely_testable"] = bool(obj.get("likely_testable"))

    # THE VERDICT IS RE-DERIVED HERE, NOT TRUSTED. The model's own "verdict" field is read
    # only as a rejection it may add; it can never overturn one the structure already
    # implies. A reply that says PASS while naming no carrier, no question, or its own
    # access origin is not a disagreement to be weighed -- it is a reply that failed its
    # own stated test, and the four gates below are the ones the brief actually specifies.
    if not rec["carrier"]:
        rec["reject_reason"] = NO_CARRIER
    elif not rec["question"]:
        rec["reject_reason"] = NO_QUESTION
    elif rec["access_origin"] and not rec["why_this_might_matter"]:
        # NO_ACCESS_ORIGIN. An access/compliance/infrastructure origin is refused unless
        # the reply named a deeper mechanism that survives removing the access language.
        rec["reject_reason"] = ACCESS_ORIGIN
    elif not rec["likely_testable"]:
        rec["reject_reason"] = THIN_EVIDENCE
    elif str(obj.get("verdict") or "").strip().upper() == REJECT:
        rec["reject_reason"] = (str(obj.get("reject_reason") or "").strip()
                                or "screen rejected without a stated reason")
    rec["verdict"] = REJECT if rec["reject_reason"] else PASS
    return rec
