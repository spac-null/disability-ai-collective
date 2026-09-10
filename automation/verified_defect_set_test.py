#!/usr/bin/env python3
"""verified_defect_set_test.py -- the defects an independent audit found and production
confirmed, each pinned by the reproduction that established it.

PROVENANCE. Two independent read-only audits of deployed d96b7f8 (one diagnostic, one
forensic verification) plus my own artifact checks. Every defect here was reproduced
against retained production artifacts or deterministically offline BEFORE it was fixed,
and every test below is the reproduction, not a restatement of the fix.

WHAT IS NOT HERE. Nothing about Grounding calibration, TRUE_UNCERTAIN, Worth, the Ledger's
authority, Reader thresholds or publication eligibility. None of those moved.

Offline: real code, deterministic fixtures, no provider, no network, no model calls.
"""
from __future__ import annotations

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import composition as CP                            # noqa: E402
from new_engine_v1 import story as ST                                  # noqa: E402

FAILURES: list = []


def check(label, ok, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- %s" % (detail,)))
    if not ok:
        FAILURES.append(label)


# ── V5. entity extraction skipped the first MATCH, not the sentence opener ────────
def _old_entities(text, skip_sentence_initial=True):
    """The implementation as deployed at d96b7f8, kept so the differential is provable
    rather than asserted."""
    out = set()
    for s in re.split(r"(?<=[.!?])\s+", text):
        toks = re.findall(r"\b[A-Z][A-Za-z'’.-]{2,}\b", s)
        for tok in (toks[1:] if skip_sentence_initial else toks):
            tok = tok.rstrip(".,")
            out.add(tok)
            out.add(re.sub(r"['’]s$", "", tok))
            for part in re.split(r"[-.]", tok):
                if len(part) > 2:
                    out.add(part)
    return out


def test_a_real_name_after_lowercase_words_is_no_longer_dropped():
    """The defect WEAKENED factual safety: a proper name that happened to be the first
    capitalised match in its segment was skipped, so a newly introduced entity could evade
    the unapproved-entity comparison purely because of the capitalisation before it."""
    for text, name in (("a visit to Georgetown.", "Georgetown"),
                       ("the council commissioned Avanti Architects.", "Avanti"),
                       ("delivered in May by Avanti.", "May")):
        old, new = _old_entities(text), ST._entities(text)
        check("%r: %s was dropped, now caught" % (text[:38], name),
              name not in old and name in new, (sorted(old), sorted(new)))


def test_grammatical_capitals_are_still_skipped_and_the_approved_set_is_unchanged():
    """The intended behaviour is preserved exactly: a capital that genuinely opens a
    sentence is not evidence of a name, and the approved-set path never skipped anything."""
    for text in ("Where people stand matters.", "That threshold is met with help.",
                 "The editor filed it."):
        check("%r yields no spurious entity" % text[:34],
              not ({"Where", "That", "The"} & ST._entities(text)), sorted(ST._entities(text)))
    check("a name mid-sentence is still caught",
          "Georgetown" in ST._entities("The editor works at Georgetown."), "")
    for text in ("a visit to Georgetown.", "The NHS owns Finsbury Health Centre.",
                 "Avanti Architects delivered it in May."):
        check("approved-set path (skip=False) is byte-identical for %r" % text[:30],
              _old_entities(text, False) == ST._entities(text, False), "")


# ── V2. a package blocker vanished from an article-only recheck and paid for it ──
def test_an_untouched_package_blocker_cannot_supply_shrink_credit():
    """Finsbury attempt A iteration 5 accepted on 4 -> 2 while the SOCIAL_HOOK blocker in
    `blockers_before` was simply absent from `blockers_after` -- with the package never
    edited. The article repair was credited for forgetting a live package defect."""
    import grounding_completion_test as T
    pkg = {"title": "A room made of salt",
           "dek": "The chair was carved in 1991 according to the catalogue entry.",
           "homepage_excerpt": "", "meta_description": "", "social_hook": ""}
    pkg_finding = T._finding("P1", pkg["dek"])
    restore, _ = T._ground_seq([T._ground_reply([T._finding("N1", "The room was painted in 1994.")])])
    try:
        res = CP.grounding_completion_loop(
            T._LoopProvider([T.EDIT1]), T.LOOP_ARTICLE, pkg,
            T._initial([T.F1, pkg_finding]), T.LOOP_LEDGER, T.LOOP_PACKET, T.LOOP_ARCH,
            T.LOOP_PACK, "src", "sha", T._pass_audit, max_iterations=1)
    finally:
        restore()
    h = res["grounding_completion_history"][0]
    check("the candidate is REJECTED, not credited with a false shrink",
          h["outcome"] == "no_progress", h.get("outcome"))
    check("and the arithmetic is honest (2 -> 2, not 2 -> 1)",
          "2 -> 2" in str(h.get("reason")), h.get("reason"))
    after = h.get("blockers_after") or []
    check("the untouched package blocker survives the recheck",
          any(b["surface"] != CP.ARTICLE_SURFACE for b in after),
          [(b["surface"], b["quote"][:30]) for b in after])
    check("and it is still in the loop's final blocking set",
          any(CP.surface_of(str(f.get("quote") or ""), pkg) != CP.ARTICLE_SURFACE
              for f in res["blocking"]), "")
    check("strict shrink itself is untouched -- still one comparison on the whole set",
          (HERE / "new_engine_v1" / "composition.py").read_text()
          .split("def grounding_completion_loop")[1].split("\ndef ")[0]
          .count('len(candidate_grounding["blocking"]) < before_count') == 1, "")


# ── V4. an attributed negative the architecture REQUIRED could not be licensed ────
F39 = {"claim_type": "ATTRIBUTION",
       "proposition": "A multimodal deep learning study of pediatric mTBI states that "
                      "there is no objective clinical biomarker for reliably identifying "
                      "mTBI or predicting recovery trajectories in injured children.",
       "support_span": "there is no objective clinical biomarker for reliably "
                       "identifying mTBI"}


def test_an_explicitly_attributed_negative_is_licensable():
    """production-20260910T073435Z-703b7b90: Architecture beat B2 REQUIRED this exact
    statement, F39 licensed it, F39 was in use_facts -- and negative_permissions() excluded
    it solely because ATTRIBUTION is not in NEGATIVE_TYPES. The packet then said "Nothing
    else. A negative claim with no id here has no permission," and the run died on
    UNSUPPORTED_NEGATIVES. Two frozen instructions that could not both be satisfied."""
    led = {"F39": F39}
    check("the real production fact is now licensable",
          "F39" in CP.negative_permissions({"use_facts": ["F39"]}, led), "")
    check("but only when the architecture actually selected it",
          CP.negative_permissions({"use_facts": []}, led) == {}, "")
    check("a proposition negative where the SOURCE SPAN is not stays refused",
          not CP.attributed_negative_is_explicit(
              dict(F39, support_span="biomarker research continues at pace")), "")
    check("a span negative where the PROPOSITION is not stays refused",
          not CP.attributed_negative_is_explicit(
              dict(F39, proposition="The study enrolled 775 children.")), "")
    check("an ordinary attributed claim stays refused",
          not CP.attributed_negative_is_explicit(
              {"claim_type": "ATTRIBUTION", "proposition": "The report describes three "
               "cohorts.", "support_span": "three cohorts were enrolled"}), "")
    check("a missing span is refused rather than assumed",
          not CP.attributed_negative_is_explicit(dict(F39, support_span="")), "")
    check("the shape test is the audit's OWN single owner, not a second definition",
          "negative_shape_of" in (HERE / "new_engine_v1" / "composition.py").read_text()
          .split("def attributed_negative_is_explicit")[1].split("\ndef ")[0], "")
    check("and the enforcing audit uses that same owner",
          "negative_shape_of" in (HERE / "new_engine_v1" / "story.py").read_text()
          .split("def negative_claim_scan")[1].split("\ndef ")[0], "")


# ── suggested_patch was substituted verbatim, instructions included ──────────────
def test_an_instruction_is_never_written_into_the_article():
    """The patch is substituted character for character. When the Grounder answered with
    an editorial instruction, the instruction became prose: retained run
    production-20260910T084202Z-09d602f1 attempt B iteration 2 shows Grounding quoting
    "(delete the trailing fragment; the preceding sentenc..." as ARTICLE surface."""
    art = "The room was painted in 1990. The chair is old."
    for patch in ("(delete the trailing fragment; the preceding sentence says it)",
                  "delete the trailing fragment", "Remove the unsupported clause",
                  "replace with a narrower phrase", "rephrase to avoid the causal claim",
                  "the preceding sentence already carries it"):
        f = {"id": "F1", "quote": "painted in 1990", "suggested_patch": patch}
        check("refused: %r" % patch[:44],
              CP.suggested_patch_edit(art, f) is None, "")
    for patch in ("painted at some point", "national survey data collected in 2022",
                  "land surface temperature, derived from satellite imagery",
                  "a report published on 13 August 2026"):
        f = {"id": "F1", "quote": "painted in 1990", "suggested_patch": patch}
        check("still builds a real edit: %r" % patch[:40],
              CP.suggested_patch_edit(art, f) is not None, "")


# ── V3/V9. the audit on record must describe the article that won ───────────────
def test_the_accepted_repair_becomes_the_safety_record():
    """The candidate's Safety verdict was READ but never RECORDED, so SAFETY_AUDIT.json and
    SAFETY_REPLAY.json kept describing the PRE-repair article. Measured on retained runs the
    audited hash disagreed with the final article hash in 5 of 6 locations. Nothing
    re-audits anything -- the candidate was already audited correctly inside the loop.

    BEHAVIOURAL, not a source scan: drive the real pipeline to a run whose Grounding repair
    is accepted, persist it, and read the hashes back off disk. A grep for `record(SAFETY,
    ...)` would pass on code that recorded the WRONG audit.
    """
    import hashlib
    import json
    import tempfile
    import story_architecture_composition_test as H

    # G1 is an article-surface blocker; FIX_G1 is its accepted repair. The second
    # Grounding reply is the post-repair recheck, which comes back clean.
    ground_seq = [dict(H.GROUND_DIRTY), dict(H.GROUND_CLEAN)]
    import new_engine_v1.stages as S
    real = S.ground
    seq = list(ground_seq)
    S.ground = lambda *a, **k: dict(seq.pop(0) if seq else H.GROUND_CLEAN)
    try:
        with tempfile.TemporaryDirectory() as d:
            out_dir = pathlib.Path(d) / "run"
            res = CP.run_story_architecture_composition(
                H.Scripted(H.full_script()[:5] + [H.FIX_G1] + [H.READER_OK]),
                pack=H.PACK, source_text=H.S0, source_sha="x", subject=H.PACK["subject"],
                fact_check_fn=lambda a: dict(H.FC_CLEAN), out_dir=out_dir)
            check("the run accepted a Grounding repair",
                  (res.get("repairs_by_stage") or {}).get(CP.GROUNDING, 0) >= 1,
                  res.get("repairs_by_stage"))
            final_sha = hashlib.sha256(
                (out_dir / "ARTICLE_FINAL.md").read_text().encode()).hexdigest()
            sa = json.loads((out_dir / "SAFETY_AUDIT.json").read_text())
            check("the persisted Safety audit describes the article that won",
                  sa.get("audited_text_sha256") == final_sha,
                  (str(sa.get("audited_text_sha256"))[:12], final_sha[:12]))
            sr = out_dir / "SAFETY_REPLAY.json"
            if sr.exists():
                rep = json.loads(sr.read_text())
                aud = rep.get("audited_text_sha256") or (rep.get("payload") or {}).get(
                    "audited_text_sha256")
                check("and so does the persisted Safety replay", aud == final_sha,
                      (str(aud)[:12], final_sha[:12]))
            check("the article really was repaired (not trivially equal to the draft)",
                  (out_dir / "ARTICLE_FINAL.md").read_text()
                  != (out_dir / "WRITER_DRAFT.md").read_text(), "")
    finally:
        S.ground = real

    # V9: the repackage recheck counted one call twice and discarded the prior total.
    src = (HERE / "new_engine_v1" / "composition.py").read_text()
    rp = src.split("def repackage_if_only_the_furniture_failed")[1].split("\n        g = ")[0]
    check("the repackage recheck no longer double-counts its own call",
          "calls[GROUNDING] = calls.get(GROUNDING, 0) + 1" not in rp, "")
    check("and it adds that call to the total already accumulated",
          "g_calls_before + g_new.get(" in rp, "")


def main() -> int:
    for fn in (test_a_real_name_after_lowercase_words_is_no_longer_dropped,
               test_grammatical_capitals_are_still_skipped_and_the_approved_set_is_unchanged,
               test_an_untouched_package_blocker_cannot_supply_shrink_credit,
               test_an_explicitly_attributed_negative_is_licensable,
               test_an_instruction_is_never_written_into_the_article,
               test_the_accepted_repair_becomes_the_safety_record):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        return 1
    print("ALL VERIFIED-DEFECT-SET TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
