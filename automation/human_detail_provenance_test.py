#!/usr/bin/env python3
"""
human_detail_provenance_test.py — regression suite for
automation/orchestrator/human_detail_provenance.py (human-detail provenance
audit, 2026-08-14).

Uses the two CONFIRMED real incidents found during this audit as regression
fixtures (paraphrased, not the live published files, so this suite never
depends on those articles remaining unfixed):
- _posts/2026-05-04-the-floor-plan-they-can-t-read.md's claimed phone call
  with "Reaktor Education facilitators" -- verified directly (WebFetch) to
  have zero grounding in its actual primary source.
- _posts/2026-05-20-sixty-four-dollars-an-hour-is-museum-language-for-we.md's
  "public records request" quote attributed to a Tacoma Art Museum manager
  -- verified directly to have zero relationship to its actual primary
  source (a Hyperallergic piece about Seattle Art Museum, containing only a
  collective union quote and a CEO quote).

Also covers synthetic fixtures A-E from the audit brief and the corpus-
derived false-positive shape (metaphorical "told me" with an inanimate
subject). Zero network, zero model calls.

USAGE: python3 automation/human_detail_provenance_test.py
Exit code 0 = all pass. Exit code 1 = at least one failure (printed).
"""
import inspect
import sys
from pathlib import Path

AUTOMATION_DIR = Path(__file__).parent
sys.path.insert(0, str(AUTOMATION_DIR))

from orchestrator.human_detail_provenance import (  # noqa: E402
    find_personal_contact_claims, check_provenance,
    REASON_GROUNDED_QUOTE, REASON_UNGROUNDED_QUOTE,
    REASON_UNVERIFIABLE_PARAPHRASE, REASON_NO_SOURCE_AVAILABLE,
)
from orchestrator.generate import GenerateMixin  # noqa: E402
from orchestrator.gate import GateMixin  # noqa: E402

FAILURES = []


def check(name, condition):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}")
        FAILURES.append(name)


# ── Confirmed real incidents (paraphrased, not the live files) ────────────

_FLOORPLAN_INCIDENT = (
    "Three Canadian provinces released AI literacy frameworks this spring. "
    "Their facilitators told me, in a February 2024 call, that their strongest "
    "students were consistently the ones with ADHD or autism diagnoses."
)
_FLOORPLAN_REAL_SOURCE = (
    "Three provinces released AI literacy frameworks this spring, each "
    "referencing UNESCO and ISTE guidance for classroom AI curricula, with no "
    "mention of any facilitator interviews or student diagnosis data."
)

_MUSEUM_INCIDENT = (
    'The Tacoma Art Museum workers won union recognition in 2023. One manager '
    'said it in a staff meeting, recorded in meeting notes I obtained through a '
    'public records request: "We offer an experience most people would pay to have."'
)
_MUSEUM_REAL_SOURCE = (
    'Seattle Art Museum staff submitted their unionization letter on May 13, 2025. '
    'The union letter said: "The challenges we face, such as unsustainable wages, '
    'subpar health benefits, and siloed, top-down decision-making, are undeniable, '
    'systemic, and have persisted across administrations." CEO Scott Stulen '
    'responded that the museum values its staff.'
)


def case_floorplan_incident_flagged_ungrounded():
    result = check_provenance(_FLOORPLAN_INCIDENT, _FLOORPLAN_REAL_SOURCE)
    check("floor-plan incident: personal-contact claim detected and flagged "
          "against its REAL primary source (no quote mark -> unverifiable paraphrase)",
          len(result) == 1 and result[0]["reason"] == REASON_UNVERIFIABLE_PARAPHRASE)


def case_museum_incident_flagged_ungrounded_quote():
    result = check_provenance(_MUSEUM_INCIDENT, _MUSEUM_REAL_SOURCE)
    check("museum incident: quoted claim detected, quote text absent from the "
          "real primary source -> UNGROUNDED_QUOTE",
          len(result) == 1 and result[0]["reason"] == REASON_UNGROUNDED_QUOTE
          and result[0]["quoted_span"] == "We offer an experience most people would pay to have.")


# ── Synthetic fixtures A-E (instruction 7) ─────────────────────────────────

def case_A_source_backed_quote():
    article = 'A caseworker told me: "The new system is beautiful. My clients cannot find anything."'
    source = 'A caseworker told the paper: "The new system is beautiful. My clients cannot find anything."'
    result = check_provenance(article, source)
    check("A. source-backed quote (verbatim text present in source) -> GROUNDED_QUOTE",
          len(result) == 1 and result[0]["reason"] == REASON_GROUNDED_QUOTE)


def case_B_unsupported_attributed_quote():
    article = 'She told me directly: "Nobody at the agency ever called back."'
    source = "The agency processed 400 requests last year according to public records."
    result = check_provenance(article, source)
    check("B. unsupported attributed quote (quote text not in source) -> UNGROUNDED_QUOTE",
          len(result) == 1 and result[0]["reason"] == REASON_UNGROUNDED_QUOTE)


def case_C_unsupported_anecdote_no_quote():
    article = "A former employee told me that the office had quietly stopped answering calls by noon."
    source = "The office's official hours are 9am to 5pm, Monday through Friday."
    result = check_provenance(article, source)
    check("C. unsupported 'X told me...' anecdote, no quote marks -> UNVERIFIABLE_PARAPHRASE",
          len(result) == 1 and result[0]["reason"] == REASON_UNVERIFIABLE_PARAPHRASE)


def case_D_named_person_fact_with_external_source_excluded():
    article = 'Liz Carr said in a 2015 BBC interview: "We are not brave for getting out of bed."'
    source = "This article is about a completely different topic and mentions no interview."
    result = check_provenance(article, source)
    check("D. real named-person fact citing an independent, dated, named external "
          "source ('in a 2015 BBC interview') -> excluded entirely, not flagged "
          "(lower-risk citation pattern, not a personal-contact claim)",
          result == [])


def case_E_generic_background_fact_no_claim():
    article = ("The Australian Bureau of Statistics reported that primary carers "
               "were overwhelmingly female in 2022. Fifty-two billion dollars is the "
               "widely cited figure for annual NDIS spending.")
    source = "Unrelated source text about a different subject entirely."
    result = check_provenance(article, source)
    check("E. generic background/statistical fact with no personal-contact claim "
          "at all -> nothing flagged (this module does not govern general knowledge)",
          result == [])


# ── No-source and false-positive shapes ────────────────────────────────────

def case_no_source_available():
    article = 'An architect I spoke with in Rotterdam told me: "The building never worked."'
    result = check_provenance(article, None)
    check("no source_text available at all (article has no fetched primary source) "
          "-> NO_SOURCE_AVAILABLE, not silently skipped",
          len(result) == 1 and result[0]["reason"] == REASON_NO_SOURCE_AVAILABLE)


def case_metaphorical_told_me_not_flagged_as_personal_contact():
    # Confirmed corpus false-positive shape: inanimate-subject "told me" is
    # NOT a personal-contact claim about a human source. This regex-only
    # harvester does not filter these by subject -- documented limitation,
    # not silently pretended away.
    article = "The pitch of rail vibration told me which train was coming before it rounded the bend."
    claims = find_personal_contact_claims(article)
    check("KNOWN LIMITATION, documented not hidden: metaphorical 'told me' with an "
          "inanimate subject (rail vibration) IS matched by this deterministic "
          "harvester (no subject-of-verb analysis) -- recorded here so this stays "
          "a known, accepted false-positive shape, not a silent surprise",
          len(claims) == 1)


def case_no_personal_contact_claim_no_flag():
    article = "This article discusses museum funding policy without quoting anyone directly."
    result = check_provenance(article, "Some source text.")
    check("an article with zero personal-contact claims -> nothing flagged "
          "(the common, expected, healthy case)", result == [])


def case_never_raises_on_malformed_input():
    try:
        check_provenance(None, None)
        find_personal_contact_claims(12345)
        raised = False
    except Exception:
        raised = True
    check("malformed input never raises", raised is False)


# ── Authority ───────────────────────────────────────────────────────────────

def case_never_reaches_should_block():
    src = inspect.getsource(GenerateMixin._compute_should_block)
    check("_compute_should_block's source never references human_detail_provenance",
          "human_detail" not in src.lower() and "provenance" not in src.lower())


def case_never_reaches_pre_commit_gate():
    src = inspect.getsource(GateMixin._pre_commit_gate)
    check("gate.py's _pre_commit_gate never references human_detail_provenance",
          "human_detail" not in src.lower() and "provenance" not in src.lower())


if __name__ == "__main__":
    case_floorplan_incident_flagged_ungrounded()
    case_museum_incident_flagged_ungrounded_quote()
    case_A_source_backed_quote()
    case_B_unsupported_attributed_quote()
    case_C_unsupported_anecdote_no_quote()
    case_D_named_person_fact_with_external_source_excluded()
    case_E_generic_background_fact_no_claim()
    case_no_source_available()
    case_metaphorical_told_me_not_flagged_as_personal_contact()
    case_no_personal_contact_claim_no_flag()
    case_never_raises_on_malformed_input()
    case_never_reaches_should_block()
    case_never_reaches_pre_commit_gate()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    else:
        print("ALL PASS")
        sys.exit(0)
