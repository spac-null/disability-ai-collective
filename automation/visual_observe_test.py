#!/usr/bin/env python3
"""
visual_observe_test.py -- offline tests for the visual-observation utility.

No network, no model, no image bytes required except the tiny generated ones. Every test
here is about the two things the 2026-09-07 benchmark proved this module has to get right:
a drawing is never batched, and a number that came out of a picture never leaves.
"""
from __future__ import annotations

import io
import json
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).parent))

import visual_observe as V

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print("PASS %s" % name)
    else:
        print("FAIL %s %s" % (name, detail))
        FAILURES.append(name)


# ── the numeric guard ─────────────────────────────────────────────────────────
def test_numbers_are_dropped():
    kept, rej = V.apply_guards({
        "visual_id": "T-1", "type": "drawing",
        "observable_facts": [
            "A space is labelled OBSERVATORIO DE AVES.",              # survives
            "Printed level labels read +2.60 and -0.80.",              # digit
            "A scale bar is present.",                                 # scale language
            "The wall is three metres from the stair.",                # spelled measure
            "Two building volumes are separated by an uncovered gap.",  # spelled count, allowed
        ],
        "spatial_relationships": ["The upper space sits above the lower one."],
        "not_established": ["Whether this is the only route is not established.",
                            "Whether the drawing shows all 3 levels is not established."],
        "questions_raised": ["What do the unlabelled spaces hold?"],
    })
    facts = kept["observable_facts"]
    check("printed word label survives",
          "A space is labelled OBSERVATORIO DE AVES." in facts)
    check("spelled count survives",
          "Two building volumes are separated by an uncovered gap." in facts)
    check("digit observation dropped",
          not any("2.60" in f for f in facts))
    check("scale language dropped", not any("scale" in f.lower() for f in facts))
    check("spelled measurement dropped", not any("three metres" in f for f in facts))
    check("three dropped, two kept", len(facts) == 2 and kept["guard_dropped"] >= 3,
          str(facts))
    reasons = {r["reason"] for r in rej}
    check("reasons recorded",
          {"vision_read_number", "measurement_language"} <= reasons, str(reasons))
    # NOT_ESTABLISHED is exempt from the numeric guard on purpose.
    check("not_established keeps its only-route disclaimer",
          any("only route" in n for n in kept["not_established"]),
          str(kept["not_established"]))
    check("not_established keeps a numbered unknown",
          any("3 levels" in n for n in kept["not_established"]),
          str(kept["not_established"]))


def test_prohibited_inferences_are_dropped():
    cases = {
        "The entrance is inaccessible.": "accessibility_conclusion",
        "This does not meet the standard.": "compliance_conclusion",
        "The layout does not comply with the ADA.": "legal_framework",
        "A wheelchair user could not pass the threshold.": "wheelchair_conclusion",
        "The stair is the only route to the upper level.": "route_exclusivity",
        "There is no alternative route into the volume.": "route_exclusivity",
        "The upper room cannot be reached from the deck.": "reachability_conclusion",
        "The unprotected edge is dangerous.": "safety_verdict",
        "The gap is intended for planting.": "intent_claim",
    }
    bad = []
    for text, want in cases.items():
        got = V.guard("observable_facts", text)
        if got != want:
            bad.append((text, want, got))
    check("every prohibited shape is caught with the right reason", not bad, str(bad))
    # ...and NOT_ESTABLISHED is guarded for these too, unlike numbers.
    kept, rej = V.apply_guards({
        "visual_id": "T-2", "type": "photograph",
        "observable_facts": [], "spatial_relationships": [],
        "not_established": ["The building is inaccessible."],
        "questions_raised": [],
    })
    check("prohibited text dropped even in not_established",
          kept["not_established"] == [] and rej[0]["reason"] == "accessibility_conclusion")


# ── the call policy ───────────────────────────────────────────────────────────
def test_drawings_are_never_batched():
    items = [{"type_hint": t} for t in
             ("PHOTO", "PHOTO", "PLAN", "SECTION", "PHOTO", "MAP", "OTHER")]
    calls = V.plan_calls(items)
    drawing_calls = [c for c in calls if V.is_drawing(c[0].get("type_hint"))]
    check("every drawing is alone in its call",
          all(len(c) == 1 for c in drawing_calls) and len(drawing_calls) == 3,
          str([[i["type_hint"] for i in c] for c in calls]))
    check("a drawing never shares a call with a photograph",
          all(len({V.is_drawing(i["type_hint"]) for i in c}) == 1 for c in calls))


def test_photo_batch_is_bounded():
    calls = V.plan_calls([{"type_hint": "PHOTO"}] * 12)
    check("photo batches respect PHOTO_BATCH_MAX",
          all(len(c) <= V.PHOTO_BATCH_MAX for c in calls) and len(calls) == 3,
          str([len(c) for c in calls]))


def test_job_size_is_bounded():
    try:
        V.observe([{"path": "/nonexistent"}] * (V.MAX_VISUALS_PER_JOB + 1))
        check("oversize job refused", False)
    except ValueError:
        check("oversize job refused", True)


# ── parsing ───────────────────────────────────────────────────────────────────
def test_parse_recovers_blocks():
    text = ("VISUAL_ID: TO-2\n"
            "TYPE: Architectural drawing; floor plan\n"
            "OBSERVABLE_FACTS:\n"
            "- A key lists room names.\n"
            "- Spaces are labelled COURTYARD.\n"
            "SPATIAL_RELATIONSHIPS: A courtyard separates two volumes.\n"
            "NOT_ESTABLISHED: Whether a covered passage exists is not established.\n"
            "QUESTIONS_RAISED: Which volume holds the bedrooms?\n"
            "\nVISUAL_ID: TO-3\nTYPE: Section\n"
            "OBSERVABLE_FACTS: The ground slopes. The volumes step down it.\n"
            "SPATIAL_RELATIONSHIPS: Each volume sits lower than the last.\n"
            "NOT_ESTABLISHED: Whether every level is shown is not established.\n"
            "QUESTIONS_RAISED: What is under the lowest volume?\n")
    recs = V.parse_blocks(text)
    check("both blocks parsed", [r["visual_id"] for r in recs] == ["TO-2", "TO-3"],
          str([r["visual_id"] for r in recs]))
    check("bullets become discrete observations",
          len(recs[0]["observable_facts"]) == 2, str(recs[0]["observable_facts"]))
    check("prose splits into sentences",
          len(recs[1]["observable_facts"]) == 2, str(recs[1]["observable_facts"]))
    check("type carried", recs[1]["type"] == "Section")


def test_parse_tolerates_markdown():
    recs = V.parse_blocks("**VISUAL_ID:** X-1\n**TYPE:** Photograph\n"
                          "**OBSERVABLE_FACTS:** A stair rises beside a wall.\n")
    check("markdown labels parsed",
          recs and recs[0]["visual_id"] == "X-1"
          and recs[0]["observable_facts"] == ["A stair rises beside a wall."],
          str(recs))


# ── the sidecar ───────────────────────────────────────────────────────────────
def test_dry_run_writes_a_declared_non_claim_sidecar():
    from PIL import Image
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        p = d / "img.jpg"
        Image.new("RGB", (40, 30), (200, 200, 200)).save(p)
        out = V.observe([{"path": str(p), "visual_id": "D-1", "type_hint": "PLAN"}],
                        out_dir=d, dry_run=True)
        written = json.loads((d / V.SIDECAR_NAME).read_text())
    check("sidecar name is VISUAL_OBSERVATIONS.json",
          V.SIDECAR_NAME == "VISUAL_OBSERVATIONS.json")
    check("sidecar declares itself non-claim-bearing",
          written["status"] == "NON_CLAIM_BEARING" and "No stage reads" in written["notice"])
    check("no observation record carries a publisher caption field",
          all("caption" not in o for o in written["observations"])
          and "caption" not in written["call_policy"])
    check("call policy is recorded", written["call_policy"]["drawing_batch"] == 1
          and written["call_policy"]["retries"] == 0)
    check("sidecar version is its own, not the engine schema",
          written["sidecar_version"] == 1 and "schema_version" not in written)
    check("dry run sent nothing", out["observations"] == [] and out["usage"][0]["dry_run"])


# ── the isolation claims in the docstring ─────────────────────────────────────
def test_module_is_unwired():
    src = pathlib.Path(__file__).parent / "visual_observe.py"
    text = src.read_text()
    # Code tokens, not prose: the docstring names Recraft, gen_images and the ledger in
    # order to disclaim them, and a test that forbade the words would forbid the promise.
    code = "\n".join(l for l in text.splitlines()
                     if not l.lstrip().startswith("#")) 
    for forbidden in ("import gen_images", "from gen_images", "import contracts",
                      "from contracts", "import ledger", "from ledger",
                      "import pytesseract", "recraft/", "RESEARCH_PACK["):
        check("module does not call %s" % forbidden, forbidden not in code, forbidden)
    repo = src.parent
    importers = [p.name for p in repo.rglob("*.py")
                 if p.name not in (src.name, pathlib.Path(__file__).name)
                 and "visual_observe" in p.read_text()]
    check("no other module imports it", not importers, str(importers))



# ── printed key entries (added after the Tollymore proof) ─────────────────────
def test_printed_key_entry_survives_as_identifier():
    kept, rej = V.apply_guards({
        "visual_id": "T-3", "type": "plan",
        "observable_facts": [
            "A key is present, listing labels for various spaces: 01 COURTYARD, "
            "02 TERRACE, 03 FLEXIBLE ROOM, 04 WC, 05 GUEST BEDROOM",
            "A scale bar is present, labelled \"100 N\".",
            "Eleven rooms are numbered.",
        ],
        "spatial_relationships": [], "not_established": [], "questions_raised": [],
    })
    labels = {l["label"] for l in kept["printed_labels"]}
    check("room vocabulary recovered from the key",
          {"COURTYARD", "TERRACE", "FLEXIBLE ROOM", "GUEST BEDROOM"} <= labels, str(labels))
    check("no prose observation survives with a numeral",
          all(not any(c.isdigit() for c in f) for f in kept["observable_facts"]),
          str(kept["observable_facts"]))
    check("the key sentence itself is still dropped", kept["observable_facts"] == [])
    check("a scale bar is never harvested as a label",
          not any(l["label"].startswith("N") for l in kept["printed_labels"]))
    check("a count is not a label",
          V.harvest_printed_labels("Eleven rooms are numbered.") == []
          and V.guard("observable_facts", "Eleven rooms are numbered.") == "label_count")
    check("a count of visible things is still allowed",
          V.guard("observable_facts",
                  "Two building volumes are separated by an uncovered gap.") == "")
    check("every drop is still recorded for audit", len(rej) == 3)

for fn in (test_numbers_are_dropped, test_prohibited_inferences_are_dropped,
           test_drawings_are_never_batched, test_photo_batch_is_bounded,
           test_job_size_is_bounded, test_parse_recovers_blocks,
           test_parse_tolerates_markdown,
           test_dry_run_writes_a_declared_non_claim_sidecar, test_module_is_unwired,
           test_printed_key_entry_survives_as_identifier):
    fn()

print("\n%s -- %d failure(s)" % ("FAIL" if FAILURES else "ALL PASS", len(FAILURES)))
sys.exit(1 if FAILURES else 0)
