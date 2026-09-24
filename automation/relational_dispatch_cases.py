"""The hand-reviewed flagged commitments, with their expected dispatch FROZEN BEFORE the
classifier was changed.

This module is data. It holds no rule and imports nothing from the dispatch layer, so the
labels below cannot drift toward whatever the implementation happens to do. They were read off
the evidence -- gloss, span, declared evidence propositions and support spans -- and written
down first; the commit that introduces this file precedes the commit that changes the rule.

WHY EACH LABEL, from the evidence and not from the code:

  bandgap -> cutoff        RELATIONAL.  F86 licenses the cadmium fraction engineering a
                           bandgap energy; F87 licenses the cadmium fraction being tuned for a
                           desired cutoff wavelength. Two substantive concepts, each licensed
                           on its own, sharing a middle variable, and nothing ties them to each
                           other. The missing thing is the relation.

  minutes away             NON_RELATIONAL.  F46 says "imminent"; the gloss says "minutes away".
                           "minutes" is a value the evidence does not reach. There is no second
                           concept -- a quantity is not an endpoint.

  belongings               NON_RELATIONAL.  F48 says the project *focuses on* "gathering a
                           limited selection of possessions"; the gloss says people *were asked
                           to* gather "belongings". What is unsupported is the instruction and
                           the noun, and the only proposition carrying any of that vocabulary is
                           F48, which is itself a statement about the term. Nothing stands on
                           its own at the far end.
                           NOT pre-typed in the branch record -- reviewed here, before
                           implementation, and reported separately in the confusion table.

  fixed seat               NON_RELATIONAL.  F63 says "dedicated seat"; the gloss says "fixed".
                           "seat" belongs to the term "transfer-to-seat" itself, and "fixed"
                           appears nowhere in the declared evidence. An attribute, not a
                           relation.

  carry an audience        NON_RELATIONAL.  Neither "carry" nor "audience" appears in F32 or
                           F09. The gloss infers a receiver the evidence never names.

  smallest block group     NON_RELATIONAL.  A superlative over the term's own head noun.
                           "smallest" is absent from F19. Nothing at the far end.

  ISO attribution          NON_RELATIONAL.  F23 and F25 establish that a resolution names
                           ISO-compliant microphones and that interpreters were working with
                           non-compliant sound. Neither says the interpreting services are the
                           party the standards are worked to. The unsupported content is an
                           attribution -- who adheres -- not a relation between two licensed
                           concepts.

The five clean definitions in the same frozen runs -- dark current, sensor chip assembly (SCA),
plein air, East meets East, Utsuroi -- carry no flagged commitment, so they never reach the
dispatcher at all. CLEAN_DEFINITIONS records them so that can be asserted rather than assumed.
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
FIX = HERE / "fixtures" / "relational-dispatch-2026-09-24"

RELATIONAL = "RELATIONAL"
NON_RELATIONAL = "NON_RELATIONAL"
AMBIGUOUS = "AMBIGUOUS"


def _ledger(path):
    l = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if isinstance(l, dict) and "facts" in l:
        l = l["facts"]
    return l if isinstance(l, dict) else {f["fact_id"]: f for f in l}


def _arch(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def _block_group_plan():
    """Rebuilt exactly as /srv/data/cripminds-dcs-calibration/calibrate.py built it for unit 5.

    That architecture predates definition_evidence and declares none, so F19 was assigned by
    hand and marked HISTORICAL. Reproduced verbatim rather than improved: the classifier has to
    be judged on the input the detector was actually given.
    """
    full = _arch(FIX / "held-out-block-group/ARCHITECTURE.json")
    return {"article_type": "NARRATIVE_ARTICLE",
            "definitions": {"block group": full["definitions"]["block group"]},
            "definition_evidence": {"block group": ["F19"]}}


def load():
    """[(case, term, span, arch, ledger, human_type, expected)] -- the frozen acceptance set."""
    b2r1 = (_arch(FIX / "b2-run1/ARCHITECTURE.json"), _ledger(FIX / "b2-run1/LEDGER.json"))
    b2r2 = (_arch(FIX / "b2-run2/ARCHITECTURE.json"), _ledger(FIX / "b2-run2/LEDGER.json"))
    pr = (_arch(FIX / "pr106-run1/ARCHITECTURE.json"), _ledger(FIX / "pr106-run1/LEDGER.json"))
    bg = (_block_group_plan(), _ledger(FIX / "held-out-block-group/FINAL_EVIDENCE_MANIFEST.json"))
    iso = (_arch(FIX / "iso-20260924/ARCHITECTURE.json"), _ledger(FIX / "iso-20260924/LEDGER.json"))
    return [
        ("bandgap->cutoff", "cutoff wavelength", "set by the bandgap energy",
         b2r2[0], b2r2[1], "RELATIONAL", RELATIONAL),
        ("minutes away", "Dressing for Evacuation", "were minutes away",
         pr[0], pr[1], "VALUE_OVERSPECIFICATION", NON_RELATIONAL),
        ("belongings", "Dressing for Evacuation",
         "and to gather a limited selection of belongings",
         pr[0], pr[1], "ATTRIBUTION_OR_INFERENCE_OVERSPECIFICATION", NON_RELATIONAL),
        ("fixed seat", "transfer-to-seat", "fixed seat",
         b2r1[0], b2r1[1], "ATTRIBUTE_OVERSPECIFICATION", NON_RELATIONAL),
        ("carry an audience", "Aufguss", "to carry an audience",
         b2r1[0], b2r1[1], "ATTRIBUTE_OR_INFERENCE_OVERSPECIFICATION", NON_RELATIONAL),
        ("smallest block group", "block group", "the smallest",
         bg[0], bg[1], "SUPERLATIVE_OVERSPECIFICATION", NON_RELATIONAL),
        ("ISO attribution", "ISO-compliant microphone", "the interpreting services work to",
         iso[0], iso[1], "ATTRIBUTION_OVERSPECIFICATION", NON_RELATIONAL),
    ]


# (run fixture, term) pairs whose definitions the detector found wholly supported. No flagged
# commitment, therefore no dispatch, therefore no call.
CLEAN_DEFINITIONS = [
    ("b2-run2", "dark current"),
    ("b2-run2", "sensor chip assembly (SCA)"),
    ("pr106-run1", "fictional participatory scenario"),
]

# Not pre-typed in the branch record; reviewed for the first time here, before the rule
# changed. Reported apart from the six so the pre-existing set stays legible.
NEWLY_REVIEWED = {"belongings"}
