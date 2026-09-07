#!/usr/bin/env python3
"""
architecture_visual_context_test.py -- Phase 2B: the ONE stage that may read a sidecar.

No network, no credentials, no real model. The ledger/architecture/worth fixture is
imported from `story_architecture_composition_test`, which is guarded by a `__main__`
block and so is safe to import: reusing its fixture means these tests run against an
architecture that passes the REAL merged validators, not a hand-waved one.

What has to be true, and is tested here rather than trusted:
  1. no sidecar  -> the architect's prompt is byte-identical to the pre-2B prompt;
  2. a sidecar   -> printed labels and a spatial question reach the architect;
  3. the guard is reapplied at this boundary, so a tampered sidecar cannot smuggle an
     accessibility conclusion, a route-exclusivity claim or a measurement through;
  4. nothing visual reaches Worth, the Ledger, the Writer's packet, Grounding or the
     Fact Check -- proved on a full scripted run by scanning every prompt sent;
  5. the integration itself makes no model call and opens no socket.
"""
from __future__ import annotations

import ast
import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

from new_engine_v1 import composition as CP                    # noqa: E402
import story_architecture_composition_test as FIX               # noqa: E402

FAILURES: list = []


def check(label, ok, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- %r" % (detail,)))
    if not ok:
        FAILURES.append(label)


# ── a real sidecar, trimmed from the Tollymore Phase 2A proof ─────────────────
# These are the actual strings the utility produced and its guard passed, plus the
# printed_labels it harvested from the plan's own key.
TOLLYMORE_SIDECAR = {
    "sidecar_version": 1,
    "status": "NON_CLAIM_BEARING",
    "observations": [
        {"visual_id": "TO-PLAN", "type": "Architectural plan",
         "printed_labels": [{"index": "01", "label": "COURTYARD"},
                            {"index": "02", "label": "TERRACE"},
                            {"index": "03", "label": "FLEXIBLE ROOM"},
                            {"index": "05", "label": "GUEST BEDROOM"},
                            {"index": "08", "label": "LIVING"},
                            {"index": "09", "label": "DINING"},
                            {"index": "17", "label": "BEDROOM"}],
         "observable_facts": [
             "The drawing depicts a building complex with multiple enclosed spaces and "
             "open areas.",
             "A body of water with a textured surface is visible along one side of the "
             "complex."],
         "spatial_relationships": [
             "Multiple courtyards and terraces are integrated into the building's "
             "layout.",
             "The building appears to be composed of several interconnected volumes."],
         "not_established": [
             "Whether this is the only route between the volumes is not established.",
             "The drawing does not establish the number of levels in the building."],
         "questions_raised": [
             "Which volume holds the bedrooms, and what lies between it and the living "
             "spaces?"]},
        {"visual_id": "TO-SECT", "type": "Architectural drawing",
         "printed_labels": [],
         "observable_facts": [
             "All three views show a building situated on a sloped terrain."],
         "spatial_relationships": [
             "The building appears to step down the slope."],
         "not_established": ["The function of the internal spaces is not established."],
         "questions_raised": ["What is the purpose of the chimney-like feature?"]},
    ],
}


def sidecar_dir(payload) -> str:
    d = tempfile.mkdtemp()
    (pathlib.Path(d) / CP.VISUAL_SIDECAR_NAME).write_text(json.dumps(payload))
    return d


class Capture:
    """A provider that answers the architect once and remembers the prompt."""

    model = "test"
    url = "http://127.0.0.1:0/v1"

    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def complete(self, system, user, max_tokens=3000, timeout=180, temperature=None,
                 deadline=None):
        self.calls.append({"system": system, "user": user})

        class R:
            text = json.dumps(self.reply) if not isinstance(self.reply, str) \
                else self.reply
            model = "test"
            requested_model = "test"
            duration_ms = 1
            usage: dict = {}
        return R()


def architect_prompt(visual_context="") -> str:
    prov = Capture(FIX.ARCH)
    CP.architect(prov, FIX.LEDGER, FIX.WORTH, "The Oaken Tiltroom catalogue",
                 visual_context=visual_context)
    return prov.calls[0]["user"]


# ── 1. no sidecar: nothing moves ──────────────────────────────────────────────
def test_no_sidecar_is_byte_identical():
    base = architect_prompt()
    check("an empty visual context changes not one byte of the prompt",
          architect_prompt("") == base)
    check("a missing sidecar yields no context",
          CP.load_visual_context(tempfile.mkdtemp()) == "")
    check("out_dir=None yields no context", CP.load_visual_context(None) == "")
    check("an unparseable sidecar yields no context, and does not raise",
          CP.load_visual_context(sidecar_dir("not a dict")) == "")
    bad = dict(TOLLYMORE_SIDECAR)
    bad = {**bad, "status": "SOMETHING_ELSE"}
    check("a sidecar that does not declare itself NON_CLAIM_BEARING is refused",
          CP.load_visual_context(sidecar_dir(bad)) == "")
    check("an empty observations list yields no block",
          CP.visual_context_block({"status": "NON_CLAIM_BEARING",
                                   "observations": []}) == "")
    check("and the delimiter never appears without a sidecar",
          CP.VISUAL_CONTEXT_OPEN not in base)


# ── 2. a Tollymore-like sidecar reaches the architect ─────────────────────────
def test_tollymore_labels_and_question_reach_the_architect():
    block = CP.load_visual_context(sidecar_dir(TOLLYMORE_SIDECAR))
    prompt = architect_prompt(block)
    for label in ("LIVING", "BEDROOM", "COURTYARD", "GUEST BEDROOM", "TERRACE"):
        check("the architect can see the printed label %s" % label, label in prompt)
    check("the spatial question about sequence is shown",
          "what lies between it and the living spaces" in prompt.lower())
    check("broad spatial relationships are shown",
          "interconnected volumes" in prompt)
    check("the not-established disclaimer survives",
          "only route between the volumes is not established" in prompt.lower())
    check("it is delimited, opened and closed",
          CP.VISUAL_CONTEXT_OPEN in prompt and CP.VISUAL_CONTEXT_CLOSE in prompt)
    check("the permission text travels inside the delimiters",
          "THIS IS NON-CLAIM-BEARING VISUAL CONTEXT" in
          prompt.split(CP.VISUAL_CONTEXT_OPEN, 1)[1].split(CP.VISUAL_CONTEXT_CLOSE)[0])
    check("the architect is told it may not make a fact of it",
          "YOU MAY NOT make a fact of any of it" in prompt)
    check("and that a label is not a position",
          "They do not say where it sits" in prompt)
    check("the ledger still comes before it, keeping the last word on what exists",
          prompt.index("THE FROZEN LEDGER") < prompt.index(CP.VISUAL_CONTEXT_OPEN))
    check("the block stays compact", len(block) <= CP.MAX_VISUAL_BLOCK_CHARS, len(block))
    check("a printed label's index is dropped -- words only",
          "01 COURTYARD" not in block and "COURTYARD" in block)


# ── 3. the boundary re-guards a tampered sidecar ──────────────────────────────
def test_a_tampered_sidecar_cannot_smuggle_a_conclusion():
    tampered = json.loads(json.dumps(TOLLYMORE_SIDECAR))
    tampered["observations"][0]["observable_facts"] += [
        "A stair is visible beside the wall.",                      # legitimate, survives
        "Stairs are the only route to the bedrooms.",               # route exclusivity
        "The courtyard crossing is inaccessible.",                  # accessibility
        "A wheelchair user could not cross the courtyard.",         # wheelchair
        "The layout does not comply with the ADA.",                 # legal
        "The plinth is three metres high.",                         # measurement
        "The scale bar reads 1:100.",                               # scale + digits
        "Level labels read +2.60 and -0.80.",                       # vision-read numbers
        "The gap is intended for planting.",                        # intent
        "The unprotected edge is dangerous.",                       # safety verdict
    ]
    tampered["observations"][0]["printed_labels"] += [
        {"index": "99", "label": "ACCESSIBLE WC"}]                   # label-shaped leak
    block = CP.load_visual_context(sidecar_dir(tampered))
    check("the legitimate observation survives",
          "A stair is visible beside the wall." in block)
    for leak in ("Stairs are the only route", "inaccessible", "wheelchair", "ADA",
                 "three metres", "1:100", "+2.60", "intended for", "dangerous",
                 "ACCESSIBLE WC"):
        check("refused at the boundary: %s" % leak, leak not in block)
    # "only route" itself is NOT a forbidden string: the not-established disclaimer is
    # entitled to say it, and this is where the two uses have to be told apart.
    check("the phrase survives only in the named unknown",
          "only route" in block
          and "only route" not in block.split("EXPLICITLY NOT ESTABLISHED")[0])
    check("no digit reaches the architect outside a named unknown",
          not any(c.isdigit() for c in
                  block.split("EXPLICITLY NOT ESTABLISHED")[0]), block[:400])
    # And the same strings are refused whichever field carries them.
    tampered2 = json.loads(json.dumps(TOLLYMORE_SIDECAR))
    tampered2["observations"][0]["spatial_relationships"] = [
        "The stair is the only way up.", "A courtyard separates two volumes."]
    b2 = CP.visual_context_block(tampered2)
    check("a relationship claiming exclusivity is refused too",
          "only way up" not in b2 and "A courtyard separates two volumes." in b2)


# ── 4. nothing visual reaches any other stage ────────────────────────────────
def test_no_visual_content_leaks_into_another_stage():
    d = sidecar_dir(TOLLYMORE_SIDECAR)
    prov, out = FIX.run(FIX.full_script(), out_dir=d)
    check("the run still completes", out["status"] == CP.PASS, out.get("failure_stage"))
    arch_prompts = [c for c in prov.calls if CP.VISUAL_CONTEXT_OPEN in c["user"]]
    check("exactly one prompt in the whole run carries the visual block",
          len(arch_prompts) == 1, len(arch_prompts))
    check("and it is the architect's",
          arch_prompts and "THE STORY THAT WAS APPROVED" in arch_prompts[0]["user"])
    # The distinctive strings, hunted through every OTHER call the run made.
    others = [c["user"] for c in prov.calls if CP.VISUAL_CONTEXT_OPEN not in c["user"]]
    for needle in ("GUEST BEDROOM", "KITCHENETTE", "interconnected volumes",
                   "NON-CLAIM-BEARING"):
        check("no other stage sees %r" % needle,
              not any(needle in u for u in others))
    # The Writer's packet is built from the architecture and the ledger, so prove it
    # carries nothing visual even though the architect had seen the block.
    arch = out["detail"][CP.ARCHITECTURE]["architecture"]
    packet, prompt = CP.writer_packet(arch, out["detail"][CP.LEDGER]["ledger"],
                                     out["detail"][CP.CUT_TERMS].get("prohibitions"))
    for needle in ("COURTYARD", "GUEST BEDROOM", "NON-CLAIM-BEARING",
                   CP.VISUAL_CONTEXT_OPEN):
        check("the writer packet is free of %r" % needle,
              needle not in json.dumps(packet) and needle not in prompt)
    check("the ARCHITECTURE artifact is still the architecture object only",
          "visual_context" not in json.dumps(arch)
          and CP.VISUAL_CONTEXT_OPEN not in json.dumps(arch))
    check("usage is observable on the stage payload",
          out["detail"][CP.ARCHITECTURE].get("visual_context_chars", 0) > 0)


def test_the_repair_prompt_carries_no_visual_context():
    src = (HERE / "new_engine_v1" / "composition.py").read_text()
    tree = ast.parse(src)
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "architect")
    body = ast.get_source_segment(src, fn) or ""
    repair = body.split("while errs and repairs", 1)
    check("the repair loop exists", len(repair) == 2)
    check("and never appends the visual block",
          "visual_context" not in repair[1].split("if errs:")[0])


def test_only_the_architecture_path_reads_a_sidecar():
    src = (HERE / "new_engine_v1" / "composition.py").read_text()
    tree = ast.parse(src)
    readers = []
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef):
            seg = ast.get_source_segment(src, n) or ""
            if "load_visual_context(" in seg and n.name != "load_visual_context":
                readers.append(n.name)
    check("exactly one function loads the sidecar",
          readers == ["run_story_architecture_composition"], readers)
    # Grounding, fact check and worth must not mention it at all.
    for name in ("worth_gate", "write_article", "safety_audit"):
        fn = next((n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == name), None)
        if fn is None:
            continue
        seg = ast.get_source_segment(src, fn) or ""
        check("%s does not mention visual context" % name, "visual_context" not in seg)


# ── 5. the integration adds no call and no socket ────────────────────────────
def test_the_integration_itself_makes_no_call():
    d = sidecar_dir(TOLLYMORE_SIDECAR)
    prov_with, out_with = FIX.run(FIX.full_script(), out_dir=d)
    prov_without, out_without = FIX.run(FIX.full_script(), out_dir=tempfile.mkdtemp())
    check("the same number of model calls, with and without a sidecar",
          len(prov_with.calls) == len(prov_without.calls),
          (len(prov_with.calls), len(prov_without.calls)))
    check("the architecture stage still makes exactly one call plus its repairs",
          out_with["detail"][CP.ARCHITECTURE]["model_calls"]
          == out_without["detail"][CP.ARCHITECTURE]["model_calls"])
    src = (HERE / "new_engine_v1" / "composition.py").read_text()
    tree = ast.parse(src)
    imports = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imports |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            imports.add(n.module.split(".")[0])
    for banned in ("urllib", "socket", "requests", "visual_observe"):
        check("the package still does not import %s" % banned, banned not in imports)


def main() -> None:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            print("\n%s" % name)
            fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("%d FAILURE(S):" % len(FAILURES))
        for f in FAILURES:
            print("  - %s" % f)
        sys.exit(1)
    print("ALL ARCHITECTURE VISUAL CONTEXT TESTS PASSED")


if __name__ == "__main__":
    main()
