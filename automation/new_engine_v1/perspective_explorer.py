"""
perspective_explorer.py -- one bounded fallback call for when the Lens Probe finds
nothing.

WHY THIS EXISTS. The Lens Probe (research.py, LENS_PROBE_SYSTEM) is a single, cheap,
bounded pass that is right to say "none" most of the time -- most subjects assume
nothing about anybody, and a probe that invents a reading to avoid saying so teaches
the gate downstream to accept an analogy. That restraint is worth keeping exactly as
it is.

But a real trial (retained at .claude/perspective-trials/, branch
experiment/perspective-real-trial-001, trial-006) showed the Lens Probe's single bounded
pass can miss a real, researchable question that a genuinely different way of asking
finds -- not by searching harder, but by asking a different kind of question: what would
a form of attention this subject never expected to meet notice about it? That trial ran
by hand, subject by subject, with a human choosing seeds and methods and reading primary
sources between steps. This module is the bounded, single-call production version of
only the QUESTION-GENERATION step of that process -- not the research, not the writing,
not the judgment of whether the result is worth publishing. Those remain exactly where
they already are: targeted research fetches and verifies its own sources same as ever,
WORTH_SYSTEM (composition.py) decides publishability same as ever, and the frozen Ledger
is the only source of factual permission, same as ever.

WHAT IT DOES. Runs ONLY when the Lens Probe ran and returned no carrier hypothesis. One
model call internally: reads the same anchor and already-collected material the Lens
Probe read; is shown a small, fixed index of the reviewed disability-rooted Perspective
Library (14 axes, 16 durable instruments -- PERSPECTIVE_MATERIAL below) and one reviewed,
primary-derived seed card; selects up to three EPISTEMIC METHODS relevant to the subject
(one native to the subject's own field, one or two genuinely orthogonal to it -- never a
persona, never a name, never a first-person professional voice); has them state their own
blind spots; checks whether they actually disagree in a way that implies different
evidence, causation, unit of analysis, scale, timing or interpretation (not just different
vocabulary for the same claim); applies the same PERSON-ASSUMPTION test the trial's own
v1.1 checkpoint used; and returns AT MOST ONE hypothesis in the same shape the Lens Probe
already returns, so the caller in research.py can treat it exactly like a probe result --
fetch what it names, verify it like anything else, and hand it to assessment with no
special authority.

WHAT IT DELIBERATELY DOES NOT DO.
  - It is not evidence. Nothing this call returns may appear in an article as a fact. It
    names a question and, if it can, where a discriminating answer might be found; only a
    target-specific source fetched afterward and verified verbatim can establish anything.
  - It is not a debate. One model call reasons through the method contrast internally; it
    does not spawn agents, personas, or a simulated panel, and never invents a biography,
    a name, or first-person professional experience for a method.
  - It does not run twice. One call, at most, per research() run. If it errors, returns
    invalid shape, or produces only an institution-shaped or analogy-shaped result, that
    is NOTHING -- the run holds exactly the value it already had, and nothing retries.
  - It does not touch the Ledger, Worth, or anything past research(). Everything it
    returns is audit material once a hypothesis exists or does not; downstream reads
    fetched, verified sources the same way whether they arrived via the Lens Probe, this
    module, or ordinary search.
"""
from __future__ import annotations

from .provider import parse_json_object

PERSPECTIVE_EXPLORER_ENV = "CRIPMINDS_PERSPECTIVE_EXPLORER"
PERSPECTIVE_EXPLORER_MAX_QUERIES = 2
PERSPECTIVE_EXPLORER_MAX_URLS = 3
PERSPECTIVE_EXPLORER_MAX_SOURCES = 2


def perspective_explorer_enabled(env=None) -> bool:
    """On by default, same convention as LENS_PROBE_ENV -- an operator can take it out
    of the path without a deploy."""
    import os
    v = (env if env is not None else os.environ).get(PERSPECTIVE_EXPLORER_ENV, "").strip().lower()
    return v not in ("0", "off", "false", "no")


# ── the reviewed material this call is shown (index, never evidence) ──────────────────
# Kept small and fixed on purpose: this is a compact production representation of
# material already owner-reviewed in .claude/crip-minds-perspective-doctrine.md and
# .claude/perspective-research/. It is not a new framework -- it is the smallest
# canonical summary that lets one bounded call use what four review passes already
# settled, without reading the source documents at runtime and without depending on
# any experiment or trial directory.
PERSPECTIVE_MATERIAL = (
    "FOURTEEN AXES (a hidden assumption an ordinary reading would not ask about; use "
    "only where the subject itself supplies a real carrier, never because the "
    "vocabulary is available):\n"
    "  1  BODIES/NORMAL FUNCTIONING -- what body does this assume it is for, and where "
    "is that recorded rather than stated?\n"
    "  2  PERCEPTION/SENSORY PROCESSING -- what perceptual range is this defined over, "
    "and what falls outside it by construction?\n"
    "  3  COMMUNICATION/TRANSLATION/MEDIATION -- what sits between this and the "
    "version that arrives, and what does that layer change while appearing to "
    "preserve?\n"
    "  4  TIMING AND SIMULTANEITY -- whose pace does this assume, and who receives the "
    "same information one beat later as a structural consequence?\n"
    "  5  INDEPENDENCE AND ASSISTANCE -- what assistance is built in so thoroughly the "
    "action counts as independent, and who must ask for the rest?\n"
    "  6  CARE AND INTERDEPENDENCE -- who performs the unbooked labour that makes this "
    "work, and what does the accounting do with it?\n"
    "  7  NAVIGATION/SPATIAL DEPENDENCE -- what movement does this space or process "
    "take for granted, and what happens to that in ordinary operation?\n"
    "  8  COGNITION AND CAPACITY -- what does this system take competence to be, and "
    "what does it do with a capacity it has no way of seeing?\n"
    "  9  ENDURANCE/PACE/ACCUMULATED COST -- what is the cost in duration rather than "
    "incident, and who has been paying it while the institution decided?\n"
    "  10 PARTICIPATION AND AUTHORSHIP -- who authored the conditions here, and who "
    "was admitted to conditions someone else settled?\n"
    "  11 CLASSIFICATION AND DIAGNOSIS -- what must this classification decide, what "
    "does it make invisible, who is authorised to apply it?\n"
    "  12 MEASUREMENT/WHAT A SYSTEM CAN REGISTER -- what does this instrument treat as "
    "signal or normal variation, and what is absent by construction rather than "
    "oversight?\n"
    "  13 GAZE AND SOCIAL PERCEPTION -- what is fully present and still not "
    "registered, before anything is measured?\n"
    "  14 ACCESS AS A PROCESS, NOT A STATE -- is this a state a document can certify, "
    "or a process that has to keep being performed?\n"
    "\n"
    "SIXTEEN APPROVED_DURABLE INSTRUMENTS (short name, axes): The category enters the "
    "measurement (11) - Classification changes the available action (11,5) - "
    "Technology participates in making ability (5,1,12) - Legibility enables and "
    "constrains (12,11,10) - The name becomes the explanation (11) - Access can "
    "expire (4,3) - Pace is part of the interface (4,3,2) - Synchrony is a resource "
    "(4,2) - Delay changes the state it waits on (9,12) - Recovery is part of the "
    "task (9,6,5) - Autonomy has a maintenance layer (5,14,9) - The route to a "
    "setting can change whether support is used (5,12,10) - Who defines the option "
    "set (10,11,5) - Which channel is treated as the original (2,3,12) - The "
    "mediator assigns a register to the mediated (3,13) - When it doesn't fit, which "
    "one changes? (14,10,5).\n"
    "\n"
    "ONE REVIEWED PRIMARY-DERIVED SEED (a method, not evidence; do not reuse its own "
    "subject matter as a target -- it generates questions elsewhere):\n"
    "  Christine Sun Kim, direct artist interview (ASL-interpreted, Walker Art "
    "Center, 'A Practice of Many'), distinguishing interpretation (fast, real-time, "
    "'the gist is there, hopefully') from translation (slower, 'with the luxury of "
    "time... accuracy') as two different, equally legitimate epistemic modes -- not "
    "a good answer and a defective one. Transferable question: when a system "
    "produces a fast, provisional output and a slower, more accurate one about the "
    "same event, does it mark which kind of claim each one is -- or does whichever "
    "arrives first quietly become 'the record' the accurate one must then displace, "
    "rather than simply complete? Sharpens axes 3 and 12 and the 'which channel is "
    "treated as the original' and 'legibility enables and constrains' instruments "
    "above without duplicating either -- the addition is the claim that the fast "
    "output is a different KIND of legitimate claim, not a worse version of the "
    "accurate one.\n"
    "\n"
    "HARD BOUNDARY, unchanged from the doctrine this material is drawn from: "
    "perspective knowledge may license a QUESTION, never a FACT. Refuse rather than "
    "reach -- a hypothesis that cannot fail, or that is offered only because the "
    "vocabulary was available, is not a hypothesis. NO PROXIES: another "
    "marginalised group's situation does not license a reading about this one, and "
    "vice versa. An accessibility fact is evidence, never automatically an insight. "
    "GENERIC_DOMAIN_KNOWLEDGE (the target field would already explain this itself, "
    "using its own ordinary methods) is a normal, common, non-disqualifying outcome "
    "for the *description* of what happened here -- it does not mean the hypothesis "
    "is wrong to have named, only that naming it did not require this method. "
    "Whether a surviving hypothesis is worth an article is not this call's decision "
    "at all; it is the Worth gate's, applied to whatever target research actually "
    "finds.\n"
    "\n"
    "EPISTEMIC METHOD EXAMPLES (illustrative only -- choose whatever methods actually "
    "fit the subject in front of you, not this list): measurement/instrumentation, "
    "ecology/dependency, performance/sequence, information design, "
    "translation/linguistics, maintenance/logistics, law/governance, "
    "economics/incentives, historical reconstruction, materials/engineering, "
    "classification/diagnosis, behavioural decision science."
)

PERSPECTIVE_EXPLORER_SYSTEM = (
    "The bounded Lens Probe already ran on this subject and found nothing -- no "
    "assumption it could state before knowing what a search would return. You are a "
    "second, different kind of pass, not a retry of the same one: not a search for "
    "keywords, but a question generated by putting two or three genuinely different "
    "FORMS OF ATTENTION into contact with the same material and keeping only what "
    "survives their disagreement with each other.\n"
    "\n"
    "You are shown PERSPECTIVE_MATERIAL below: the reviewed disability-rooted "
    "Perspective Library, in compact index form, and one reviewed, primary-derived "
    "seed. This is REFERENCE MATERIAL, not a rule to apply mechanically, and not "
    "evidence about the subject in front of you -- nothing in it may become a claim "
    "about this subject. Use it only where the subject genuinely supplies its own "
    "carrier for one of these ideas; do not reach for an axis or the seed because the "
    "vocabulary is available.\n"
    "\n"
    "DO THIS INTERNALLY, IN ONE PASS, AND RETURN ONLY THE RESULT:\n"
    "\n"
    "1. Read the subject and the material already in front of you (the anchor and "
    "whatever has already been fetched). Do not invent facts about the subject "
    "beyond what is given.\n"
    "\n"
    "2. Choose up to three EPISTEMIC METHODS relevant to THIS subject: exactly one "
    "must be a method NATIVE to the subject's own field (the discipline that would "
    "ordinarily study this kind of thing), and one or two must be genuinely "
    "ORTHOGONAL to it -- a different unit of attention, a different idea of what "
    "counts as strong evidence. These are METHODS, never personas: never write 'you "
    "are a [profession]', never invent a name, a biography, or first-person "
    "professional experience. State each method as a method: its unit of attention, "
    "what it treats as strong evidence, and its own likely blind spot on this "
    "subject.\n"
    "\n"
    "3. Ask what each method would notice about this subject, independently, before "
    "letting them respond to each other.\n"
    "\n"
    "4. Then check whether they actually DISAGREE in a way that implies a real "
    "difference -- different evidence, different causal explanation, a different "
    "unit of analysis, a different scale, a different temporal order, a different "
    "interpretation, or a different predicted observation. Different VOCABULARY for "
    "the same claim does not count, and neither does simple agreement: if the "
    "methods converge on the same ordinary explanation, that is CONVERGENCE, and "
    "there is no question here -- do not force disagreement that is not real.\n"
    "\n"
    "5. If, and only if, a real disagreement produces a question none of the methods "
    "would have asked alone, apply the PERSON-ASSUMPTION CHECK: does the surviving "
    "question identify an assumption about a PERSON's body, perception, sensory "
    "processing, communication, timing, simultaneity, dependence or assistance, "
    "navigation, cognition or capacity, endurance or pace, participation or "
    "authorship, classification or diagnosis, or normal functioning -- or does it "
    "only identify an interesting mechanism about an institution, a process, a "
    "system, governance, or generic organisational behaviour, wearing that "
    "vocabulary without a person behind it? If only the latter: this is NOTHING. Do "
    "not return it.\n"
    "\n"
    "6. If a question survives both checks, state ONE -- the strongest, not a list -- "
    "as a hypothesis in exactly the shape the Lens Probe already uses: what this "
    "subject is being asked to reveal, and where a subject-specific record of it "
    "might exist. It must be able to come back NOTHING from real research; a "
    "hypothesis that cannot fail is not one.\n"
    "\n"
    "ANSWER NOTHING IF THERE IS NOTHING: no real methodological disagreement, no "
    "question that survives the person-assumption check, or a question that is only "
    "an analogy, a proxy for another group's situation, or an institution-shaped "
    "observation wearing a person-shaped axis's vocabulary -- all of these are "
    "NOTHING, and saying so costs nothing.\n"
    "\n"
    "PERSPECTIVE_MATERIAL:\n%s"
)


def perspective_explorer_prompt(subject: str, anchor_text: str, sources: list) -> str:
    have = "\n".join("  %s  %s  %s" % (s["source_id"], s.get("publisher", ""),
                                       (s.get("title") or s["url"])[:110])
                     for s in sources) or "  (nothing beyond the anchor)"
    return (
        "SUBJECT: %s\n\nWHAT THE ANCHOR SAYS:\n<<<ANCHOR\n%s\nANCHOR>>>\n\n"
        "MATERIAL ALREADY COLLECTED:\n%s\n\n"
        "Reply with JSON only:\n"
        '{"methods_selected": [{"method": "short name", "native": true or false,\n'
        '                       "unit_of_attention": "...", "strong_evidence": "...",\n'
        '                       "blind_spot": "..."}],\n'
        ' "convergence": true or false,   // true if the methods agree with no real\n'
        '                                 // disagreement -- if true, everything below\n'
        '                                 // is "none" and nothing else is required\n'
        ' "collision": "one or two sentences: what the methods actually disagree '
        'about, in terms of evidence, causation, unit, scale, timing or '
        'interpretation -- or empty string if convergence is true",\n'
        ' "person_assumption_check": "one sentence: is this about a person, or only '
        'an institution/process wearing a person-shaped axis\'s vocabulary",\n'
        ' "assumption": "one sentence: what does this subject take a person to be, '
        'named only if the person-assumption check passed, or \\"none\\"",\n'
        ' "carrier_hypothesis": "one sentence naming the subject-specific record you '
        'believe exists and would show that assumption operating, or \\"none\\"",\n'
        ' "seed_or_instrument_used": "which library item or seed this drew on, if '
        'any, or \\"none\\" if the question came from the method collision alone",\n'
        ' "why_question_survived": "one sentence: what one method could not have '
        'seen without the other(s), or \\"none\\"",\n'
        ' "queries": ["at most %d search queries, each naming this subject"],\n'
        ' "urls": ["at most %d exact URLs you believe would record it"]}\n'
        "If there is nothing -- no real disagreement, or nothing that passes the "
        "person-assumption check -- reply with convergence or the appropriate field "
        "set to make that clear, \"assumption\": \"none\", \"carrier_hypothesis\": "
        "\"none\", \"queries\": [], \"urls\": [], and nothing else."
        % (subject, anchor_text[:4000], have,
           PERSPECTIVE_EXPLORER_MAX_QUERIES, PERSPECTIVE_EXPLORER_MAX_URLS))


def perspective_explorer(provider, subject: str, anchor_text: str, sources: list) -> dict:
    """ONE model call, run only when the Lens Probe found nothing. Returns what to
    look for, never a fact -- same contract as lens_probe()."""
    try:
        comp = provider.complete(
            system=PERSPECTIVE_EXPLORER_SYSTEM % PERSPECTIVE_MATERIAL,
            user=perspective_explorer_prompt(subject, anchor_text, sources),
            max_tokens=1200)
        obj = parse_json_object(comp.text)
    except Exception as e:                                            # noqa: BLE001
        # Same fail-closed contract as the Lens Probe: a call that cannot run costs
        # the run nothing, and a transport failure here must not turn a workable pack
        # into a held one, nor retry.
        return {"ran": False, "error": "%s: %s" % (type(e).__name__, str(e)[:160]),
                "carrier_hypothesis": "", "queries": [], "urls": []}

    hyp = str(obj.get("carrier_hypothesis") or "").strip()
    none = hyp.lower() in ("", "none", "no", "n/a")
    convergence = bool(obj.get("convergence"))
    result = {
        "ran": True,
        "convergence": convergence,
        "assumption": "" if convergence else str(obj.get("assumption") or "").strip(),
        "carrier_hypothesis": "" if (none or convergence) else hyp,
        "hypothesis_before_search": True,
        "queries": [] if (none or convergence) else
                   [str(q) for q in (obj.get("queries") or [])][:PERSPECTIVE_EXPLORER_MAX_QUERIES],
        "urls": [] if (none or convergence) else
                [str(u) for u in (obj.get("urls") or []) if str(u).startswith("http")]
                [:PERSPECTIVE_EXPLORER_MAX_URLS],
        # Audit metadata only. Never read by Ledger, Worth, or anything that writes
        # prose -- kept so a human can inspect why a question was or was not raised,
        # exactly the record trial-006 kept by hand.
        "methods_selected": obj.get("methods_selected") or [],
        "collision": str(obj.get("collision") or "").strip(),
        "person_assumption_check": str(obj.get("person_assumption_check") or "").strip(),
        "seed_or_instrument_used": str(obj.get("seed_or_instrument_used") or "").strip(),
        "why_question_survived": str(obj.get("why_question_survived") or "").strip(),
        "_provider": comp.identity() if hasattr(comp, "identity") else {},
    }
    return result
