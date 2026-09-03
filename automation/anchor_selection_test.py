#!/usr/bin/env python3
"""
anchor_selection_test.py -- the anchor is chosen by id, so it cannot be written.

Four production runs on 3 September 2026 held with DISCOVERY_SOURCE_ANCHOR_NOT_IN_SOURCE,
and the frozen artefacts (fixtures/discovery-anchor-2026-09-03/) say the model was not
failing to copy: in all four the quote was a verbatim span of AUTHORISED material, taken
from the RESEARCH PACK block instead of the ANCHOR SOURCE block. The prompt carried both
and said "the source above"; the validator accepted only the first. One of the four
anchor sources was a 702-char gallery page with nothing quotable in it at all.

So the fix is not "make the model copy better". Discovery now receives bounded exact
spans of the anchor source and returns an id. The text comes from that mapping.

These tests are behavioural and structural. There is no provider and no model output to
reproduce: what is asserted is that a paraphrase has nowhere to go, that a span from
another source was never on the menu, and that every way a choice can fail is a HOLD.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import anchors as AN            # noqa: E402
from new_engine_v1 import invariants as INV        # noqa: E402
from new_engine_v1 import stages as S              # noqa: E402

FX = HERE / "fixtures" / "discovery-anchor-2026-09-03"
CASES = json.loads((FX / "cases.json").read_text())
FAILURES: list = []


def check(label, ok, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- %r" % (detail,)))
    if not ok:
        FAILURES.append(label)


def source(name) -> str:
    return (FX / ("%s.source.txt" % name)).read_text()


# ── the four frozen failures ─────────────────────────────────────────────────
def test_the_four_frozen_holds_would_now_have_a_valid_anchor():
    """Not 'force all four through' -- the criterion is that a commissionable source is
    no longer lost because the anchor came out of the wrong box."""
    for name, case in sorted(CASES.items()):
        src = source(name)
        cands = AN.candidates(src, case["subject_span"])
        verdict = "VALID_ANCHOR_AVAILABLE" if cands else "LEGITIMATE_NO_ANCHOR"
        check("%-16s %s (%d candidates)" % (name, verdict, len(cands)), bool(cands))
        # the old model anchor was verbatim SOMEWHERE, just not in the anchor source
        old = INV.normalize(case["old_model_anchor"]).strip('"\'')
        check("  %s: the old anchor really was absent from the anchor source" % name,
              old not in INV.normalize(src))
        # and it is not selectable now, because it was never a candidate
        check("  %s: the old pack-sourced anchor is not on the menu" % name,
              all(c["exact_span"] != old for c in cands))


def test_every_candidate_satisfies_the_validator_that_held_those_runs():
    for name in sorted(CASES):
        src = source(name)
        cands = AN.candidates(src, CASES[name]["subject_span"])
        bad = [c["anchor_id"] for c in cands
               if not INV.check_anchor({INV.ANCHOR_FIELD: c["exact_span"]}, src)[0]]
        check("%-16s all %d candidates pass check_anchor" % (name, len(cands)),
              not bad, bad)


# ── the mapping is the only source of anchor text ────────────────────────────
def test_a_selected_id_returns_the_exact_source_span():
    src = source("nasa-link")
    cands = AN.candidates(src)
    for c in cands:
        p = {"source_anchor_id": c["anchor_id"]}
        ok, code, _ = AN.resolve(p, cands)
        if not ok or p[INV.ANCHOR_FIELD] != c["exact_span"]:
            check("%s resolves to its own exact span" % c["anchor_id"], False, code)
            return
    check("every id resolves to its own exact span (%d ids)" % len(cands), True)
    check("and each resolved span is a substring of the normalised source",
          all(c["exact_span"] in INV.normalize(src) for c in cands))


def test_a_model_supplied_paraphrase_cannot_override_the_selected_text():
    src = source("nasa-link")
    cands = AN.candidates(src)
    payload = {"source_anchor_id": "A002",
               # the model volunteers prose in the authoritative field as well
               INV.ANCHOR_FIELD: "LINK basically stopped working after launch, sadly."}
    ok, _, _ = AN.resolve(payload, cands)
    want = [c for c in cands if c["anchor_id"] == "A002"][0]["exact_span"]
    check("resolution succeeds on the id", ok)
    check("the paraphrase is discarded, not kept",
          payload[INV.ANCHOR_FIELD] == want, payload[INV.ANCHOR_FIELD][:60])
    check("and the surviving text is a real span of the source",
          payload[INV.ANCHOR_FIELD] in INV.normalize(src))
    check("so the validator passes on it",
          INV.check_anchor(payload, src)[0])
    check("selection is recorded", payload.get("source_anchor_selected") is True)


def test_the_model_cannot_supply_anchor_text_at_all():
    """The strong invariant: with no id, volunteered prose does not become the anchor."""
    src = source("rice-moody")
    cands = AN.candidates(src)
    payload = {INV.ANCHOR_FIELD: "A sentence that is plausible but nobody wrote."}
    ok, code, _ = AN.resolve(payload, cands)
    check("no id -> not ok", not ok)
    check("  the reason is the missing id", code == INV.ANCHOR_ID_MISSING, code)
    check("  and the volunteered prose was stripped",
          INV.ANCHOR_FIELD not in payload, payload.get(INV.ANCHOR_FIELD))


# ── every way a choice can fail is a HOLD ────────────────────────────────────
def test_each_selection_failure_is_an_explicit_hold():
    src = source("rice-moody")
    cands = AN.candidates(src)
    for label, payload, want in (
            ("an unknown id", {"source_anchor_id": "A999"}, INV.ANCHOR_ID_UNKNOWN),
            ("a malformed id", {"source_anchor_id": {"a": 1}}, INV.ANCHOR_ID_MISSING),
            ("an empty id", {"source_anchor_id": "   "}, INV.ANCHOR_ID_MISSING),
            ("no field at all", {}, INV.ANCHOR_ID_MISSING),
            ("an explicit NONE", {"source_anchor_id": "NONE"}, INV.NO_VALID_ANCHOR),
            ("lowercase none", {"source_anchor_id": "none"}, INV.NO_VALID_ANCHOR)):
        ok, code, detail = AN.resolve(dict(payload), cands)
        check("%s -> HOLD %s" % (label, want), (not ok) and code == want, code)
    ok, code, _ = AN.resolve({"source_anchor_id": "A001"}, [])
    check("an empty menu -> HOLD %s" % INV.NO_ANCHOR_CANDIDATES,
          (not ok) and code == INV.NO_ANCHOR_CANDIDATES, code)
    for label, payload in (("unknown", {"source_anchor_id": "A999"}),
                           ("absent", {}),
                           ("NONE", {"source_anchor_id": "NONE"}),
                           ("with volunteered prose",
                            {"source_anchor_id": "A999",
                             INV.ANCHOR_FIELD: "invented text"})):
        pl = dict(payload)
        AN.resolve(pl, cands)
        check("  a %s failure leaves no anchor behind" % label,
              INV.ANCHOR_FIELD not in pl, pl.get(INV.ANCHOR_FIELD))


def test_ids_are_unique_and_unambiguous():
    for name in sorted(CASES):
        cands = AN.candidates(source(name), CASES[name]["subject_span"])
        ids = [c["anchor_id"] for c in cands]
        check("%-16s ids unique (%d)" % (name, len(ids)), len(ids) == len(set(ids)))
        check("  %s: ids are contiguous A001.." % name,
              ids == ["A%03d" % (i + 1) for i in range(len(ids))])
        spans = [c["exact_span"] for c in cands]
        check("  %s: no duplicate span text" % name, len(spans) == len(set(spans)))


# ── the menu can only come from the anchor source ────────────────────────────
def test_candidates_cannot_reference_another_source():
    anchor = source("rice-moody")
    other = source("nasa-link")
    cands = AN.candidates(anchor)
    norm_anchor = INV.normalize(anchor)
    check("every candidate is a substring of the anchor source",
          all(c["exact_span"] in norm_anchor for c in cands))
    leaked = [c["anchor_id"] for c in cands
              if c["exact_span"] not in norm_anchor
              or c["exact_span"] in INV.normalize(other) and len(c["exact_span"]) > 40]
    check("no candidate carries text from a different source", not leaked, leaked)


def test_a_changed_source_cannot_validate_an_old_selection():
    """Stands in for a source-hash mismatch: text selected from one snapshot must not
    pass against a different one. check_anchor is the backstop and it holds."""
    src = source("nasa-link")
    cands = AN.candidates(src)
    p = {"source_anchor_id": cands[3]["anchor_id"]}
    AN.resolve(p, cands)
    check("the selection validates against its own source", INV.check_anchor(p, src)[0])
    ok, code, _ = INV.check_anchor(p, source("rice-moody"))
    check("and fails against a different source", not ok)
    check("  with the anchor-not-in-source code",
          code == INV.ANCHOR_NOT_IN_SOURCE, code)


# ── no text is invented, and none is mutated beyond the shared normaliser ────
def test_no_candidate_text_is_fabricated_or_mutated():
    for name in sorted(CASES):
        src = source(name)
        norm = INV.normalize(src)
        for c in AN.candidates(src, CASES[name]["subject_span"]):
            if c["exact_span"] not in norm:
                check("%s %s is real source text" % (name, c["anchor_id"]), False,
                      c["exact_span"][:60])
                return
    check("every candidate of every fixture is literal source text", True)
    # the normaliser is the one check_anchor already uses, and it is idempotent
    weird = 'He said “the – thing” is  odd.  And it stays odd here too.'
    check("normalisation is idempotent",
          INV.normalize(INV.normalize(weird)) == INV.normalize(weird))
    check("curly quotes/dashes fold, wording does not change",
          '"the - thing"' in INV.normalize(weird), INV.normalize(weird))
    for c in AN.candidates(weird):
        check("  unicode candidate %s is still source text" % c["anchor_id"],
              c["exact_span"] in INV.normalize(weird))
    check("a paraphrase still fails the validator",
          not INV.check_anchor(
              {INV.ANCHOR_FIELD: "He mentioned that the thing is unusual, and remains so."},
              weird)[0])


# ── bounds, and what the prompt now says ─────────────────────────────────────
def test_the_menu_is_bounded():
    long_src = " ".join(
        "Sentence number %03d carries enough characters to be a candidate span." % i
        for i in range(400))
    cands = AN.candidates(long_src)
    check("candidate count is capped at %d" % AN.MAX_CANDIDATES,
          len(cands) <= AN.MAX_CANDIDATES, len(cands))
    total = sum(len(c["exact_span"]) for c in cands)
    check("candidate block is capped at %d chars" % AN.MAX_CANDIDATE_BLOCK_CHARS,
          total <= AN.MAX_CANDIDATE_BLOCK_CHARS, total)
    check("no span exceeds %d chars" % AN.MAX_SPAN_CHARS,
          all(len(c["exact_span"]) <= AN.MAX_SPAN_CHARS for c in cands))
    check("no span is below the anchor minimum",
          all(len(c["exact_span"]) >= INV.MIN_ANCHOR_CHARS for c in cands))
    check("candidates are deterministic",
          [c["exact_span"] for c in AN.candidates(long_src)]
          == [c["exact_span"] for c in cands])
    # the two caps bind independently: with long sentences the CHAR cap stops the list
    # first, so a source of short ones is needed to exercise the COUNT cap at all.
    short_src = " ".join("Short span number %03d is just long enough." % i
                         for i in range(300))
    short = AN.candidates(short_src)
    check("with short spans the count cap is what binds",
          len(short) == AN.MAX_CANDIDATES, len(short))
    check("  and it stays under the char cap while doing so",
          sum(len(c["exact_span"]) for c in short) < AN.MAX_CANDIDATE_BLOCK_CHARS,
          sum(len(c["exact_span"]) for c in short))
    wide_src = " ".join("Span %03d then %s ends here." % (i, "padding words " * 22)
                        for i in range(60))
    wide = AN.candidates(wide_src)
    check("with genuinely long spans the char cap is what binds",
          len(wide) < AN.MAX_CANDIDATES
          and sum(len(c["exact_span"]) for c in wide) <= AN.MAX_CANDIDATE_BLOCK_CHARS,
          (len(wide), sum(len(c["exact_span"]) for c in wide)))


def test_the_subject_span_narrows_the_menu():
    """A candidate outside the researched subject would only be rejected later by
    check_subject_scope, so it is not offered."""
    src = ("First subject sentence with plenty of characters in it. "
           "Second subject sentence also long enough to qualify. "
           "A THIRD item nobody researched at all, quite long as well.")
    subject = ("First subject sentence with plenty of characters in it. "
               "Second subject sentence also long enough to qualify.")
    cands = AN.candidates(src, subject)
    check("every candidate lies inside the researched subject",
          all(c["exact_span"] in INV.normalize(subject) for c in cands))
    check("the unresearched item is not offered",
          not any("THIRD item" in c["exact_span"] for c in cands))
    payload = {"source_anchor_id": cands[0]["anchor_id"]}
    AN.resolve(payload, cands)
    ok, _, _ = INV.check_subject_scope(payload, subject, src)
    check("and the selection passes subject scope by construction", ok)


def test_the_prompt_asks_for_an_id_and_rules_the_pack_out():
    src = source("rice-moody")
    cands = AN.candidates(src)
    def _src(sid, role, text):
        return {"source_id": sid, "role": role, "text": text, "url": "https://x/%s" % sid,
                "publisher": "p", "accessed_at": "t", "fetch_status": "ok",
                "content_length": len(text), "sha256": "", "excerpts": []}
    pack = {"sources": [_src("S0", "ANCHOR", src),
                        _src("S1", "PRIMARY",
                             "Pack material the anchor may not be taken from.")]}
    p = S.discovery_prompt(src, "a" * 40, pack, cands)
    check("the schema asks for source_anchor_id", '"source_anchor_id"' in p)
    check("it no longer asks the model to copy an anchor quote",
          "copied CHARACTER-FOR-CHARACTER" not in p)
    check("the candidate block is rendered", "ANCHOR CANDIDATES" in p)
    check("every id appears in the prompt",
          all(c["anchor_id"] in p for c in cands))
    check("the prompt says pack spans are not eligible",
          "RESEARCH PACK are NOT eligible" in p)
    check("NONE is offered as a legitimate answer", '"NONE"' in p)


def test_the_generative_repair_path_is_gone():
    check("invariants no longer exposes repair_anchor",
          not hasattr(INV, "repair_anchor"))
    rsrc = (HERE / "new_engine_v1" / "runner.py").read_text()
    check("the runner makes no repair call", "repair_anchor(" not in rsrc)
    check("the runner builds candidates before discovery",
          rsrc.index("AN.candidates(") < rsrc.index("S.discover("))
    check("and passes them to discovery",
          "S.discover(provider, src, sha, pack, anchor_cands)" in rsrc)
    check("an empty menu holds explicitly",
          "INV.NO_ANCHOR_CANDIDATES" in rsrc)
    check("the anchor field is still validated as the backstop",
          "INV.check_anchor(d, src)" in rsrc)


def main() -> None:
    for fn in (test_the_four_frozen_holds_would_now_have_a_valid_anchor,
               test_every_candidate_satisfies_the_validator_that_held_those_runs,
               test_a_selected_id_returns_the_exact_source_span,
               test_a_model_supplied_paraphrase_cannot_override_the_selected_text,
               test_the_model_cannot_supply_anchor_text_at_all,
               test_each_selection_failure_is_an_explicit_hold,
               test_ids_are_unique_and_unambiguous,
               test_candidates_cannot_reference_another_source,
               test_a_changed_source_cannot_validate_an_old_selection,
               test_no_candidate_text_is_fabricated_or_mutated,
               test_the_menu_is_bounded,
               test_the_subject_span_narrows_the_menu,
               test_the_prompt_asks_for_an_id_and_rules_the_pack_out,
               test_the_generative_repair_path_is_gone):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL ANCHOR SELECTION TESTS PASSED")


if __name__ == "__main__":
    main()
