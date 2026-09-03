#!/usr/bin/env python3
"""
identification_batching_test.py -- 16 sentences to a typing call, and the same coverage.

After PR #59 batched the classifier, identification was the slower half: 48.5s in 5
calls against 56.9s in 8, on the frozen Langrug article. So the same move, sized from
that article's own backbone rather than by analogy -- 40 sentences averaging 90
characters, peaking at 256, which puts a 16-sentence batch at 1,460 characters, a
quarter of the character cap. The bound that mattered was sentence count, not prompt
size.

Two things this must not quietly do, and both are tested here rather than trusted:
raise the coverage ceiling, and let a larger reply truncate. 8x8 was 64 sentences an
article and 16x4 is the same 64; and identification emits a measured 122 output tokens
per sentence, so 1,600 for 16 sentences would have needed ~1,946 and been cut off --
arriving as UNRESOLVED_BOUNDARY, which is truncation wearing the costume of a quality
failure.

No provider. The six-trial real-model gate lives in the PR description.
"""
from __future__ import annotations

import ast
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import claims as CL                                # noqa: E402
from new_engine_v1 import grounding_v2 as GV2                         # noqa: E402
from grounding_v2_shadow_test import StubProvider                     # noqa: E402

FAILURES: list = []
ARTICLE = (HERE / "fixtures" / "langrug-2026-09-03" / "article.md").read_text()


def check(label: str, ok: bool, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- %r" % (detail,)))
    if not ok:
        FAILURES.append(label)


def sentences(n, chars=60):
    """n synthetic sentences of a known length, so a cap can be aimed at."""
    return " ".join("Sentence %03d asserts %s." % (i, "x" * chars) for i in range(n))


# ── the declared bounds ──────────────────────────────────────────────────────
def test_the_bounds_are_what_the_measurements_support():
    check("16 sentences per batch", CL.MAX_SENTENCES_PER_BATCH == 16)
    check("character cap unchanged at 6,000", CL.MAX_BATCH_CHARS == 6_000)
    check("output cap 3,200", CL.BATCH_MAX_TOKENS == 3_200)
    check("batch ceiling 4", CL.MAX_BATCHES_PER_ARTICLE == 4)
    check("output cap scales with the batch, keeping the old per-sentence headroom",
          CL.BATCH_MAX_TOKENS / CL.MAX_SENTENCES_PER_BATCH == 1_600 / 8)
    check("the 122 output tokens/sentence measured would have truncated at 1,600",
          16 * 122 > 1_600)
    check("and fits inside 3,200 with headroom", 16 * 122 < CL.BATCH_MAX_TOKENS)


# ── the coverage ceiling must not move ───────────────────────────────────────
def test_the_coverage_ceiling_is_unchanged():
    check("still 64 sentences an article",
          CL.MAX_SENTENCES_PER_BATCH * CL.MAX_BATCHES_PER_ARTICLE == 64,
          CL.MAX_SENTENCES_PER_BATCH * CL.MAX_BATCHES_PER_ARTICLE)
    check("which is what 8 x 8 was", 8 * 8 == 64)
    # behavioural: a 64-sentence article is fully batched, a 65th is not
    got = CL._batches(CL.segment(sentences(64)))
    check("64 sentences fit in the ceiling",
          sum(len(b) for b in got) == 64 and len(got) <= CL.MAX_BATCHES_PER_ARTICLE,
          (len(got), [len(b) for b in got]))
    over = CL._batches(CL.segment(sentences(72)))
    check("72 sentences are capped at the ceiling, not silently widened",
          len(over) == CL.MAX_BATCHES_PER_ARTICLE
          and sum(len(b) for b in over) == 64, (len(over), sum(len(b) for b in over)))


# ── call counts, from the real frozen article ────────────────────────────────
def test_the_frozen_article_needs_three_batches():
    sents = CL.segment(ARTICLE)
    check("the fixture segments to 40 sentences", len(sents) == 40, len(sents))
    check("backbone verifies", CL.verify_backbone(ARTICLE, sents) == [],
          CL.verify_backbone(ARTICLE, sents))
    b = CL._batches(sents)
    check("3 identification batches, was 5", len(b) == 3, [len(x) for x in b])
    check("filled 16 / 16 / 8", [len(x) for x in b] == [16, 16, 8], [len(x) for x in b])
    check("every sentence appears exactly once, in order",
          [s["sentence_id"] for x in b for s in x]
          == [s["sentence_id"] for s in sents])
    widest = max(sum(len(s["exact_span"]) for s in x) for x in b)
    check("the widest batch is far inside the char cap (%d of %d)"
          % (widest, CL.MAX_BATCH_CHARS), widest < CL.MAX_BATCH_CHARS / 2, widest)


# ── the char cap is still the safety valve ───────────────────────────────────
def test_long_sentences_still_split_a_batch_early():
    # 16 sentences of ~600 chars each would be ~9,600 -- past the cap
    long_art = sentences(16, chars=560)
    sents = CL.segment(long_art)
    b = CL._batches(sents)
    check("a batch of long sentences is split by the CHAR cap, not the count",
          len(b) > 1, [len(x) for x in b])
    for x in b:
        size = sum(len(s["exact_span"]) for s in x)
        check("  each batch stays inside the char cap (%d)" % size,
              size <= CL.MAX_BATCH_CHARS or len(x) == 1, size)
    check("and no sentence is dropped by the split",
          sum(len(x) for x in b) == len(sents), (sum(len(x) for x in b), len(sents)))


# ── determinism of the batching itself ──────────────────────────────────────
def test_batching_is_deterministic_and_order_preserving():
    sents = CL.segment(ARTICLE)
    a = [[s["sentence_id"] for s in x] for x in CL._batches(sents)]
    b = [[s["sentence_id"] for s in x] for x in CL._batches(sents)]
    check("same input, same batches", a == b)
    flat = [i for x in a for i in x]
    check("ids ascend with no gaps", flat == sorted(flat, key=lambda s: int(s[1:])))
    # AST, not a substring: _batches must contain no sort/sorted/reverse call at all.
    fn = [n for n in ast.walk(ast.parse((HERE / "new_engine_v1" / "claims.py")
                                        .read_text()))
          if isinstance(n, ast.FunctionDef) and n.name == "_batches"]
    check("_batches is a single function", len(fn) == 1, len(fn))
    called = {getattr(c.func, "id", "") or getattr(c.func, "attr", "")
              for c in ast.walk(fn[0]) if isinstance(c, ast.Call)}
    check("_batches calls nothing that could reorder",
          not (called & {"sort", "sorted", "reverse", "reversed", "min", "max"}),
          sorted(called))
    # behavioural: hand it sentences in a deliberately non-ascending order and the
    # batches must come back in exactly that order, not repaired into id order.
    scrambled = list(reversed(sents))
    out = [s["sentence_id"] for x in CL._batches(scrambled) for s in x]
    check("input order is preserved, never sorted",
          out == [s["sentence_id"] for s in scrambled], out[:5])


# ── the failure contract: coverage survives every malformation ──────────────
def test_no_sentence_can_disappear_however_the_reply_breaks():
    sents = CL.segment(sentences(20))
    ids = [s["sentence_id"] for s in sents]

    def records(provider):
        r = CL.identify(provider, sentences(20), sents)
        return r, [x["sentence_id"] for x in r["records"]]

    good = {"sentences": [{"sentence_id": i, "type": "EMPIRICAL",
                           "atoms": [{"claim": "c", "verbatim": False,
                                      "claim_type": "EMPIRICAL"}]} for i in ids]}
    for label, typing in (
            ("a missing sentence_id",
             {"sentences": good["sentences"][:-3]}),
            ("a duplicated sentence_id",
             {"sentences": good["sentences"] + [good["sentences"][0]]}),
            ("an unknown sentence_id",
             {"sentences": good["sentences"][:-1]
              + [{"sentence_id": "S999", "type": "EMPIRICAL", "atoms": []}]}),
            ("a truncated reply", '{"sentences": [{"sentence_id": "S001",'),
            ("prose instead of JSON", "I cannot label these sentences."),
            ("an empty object", {}),
            ("a provider failure", None)):
        p = (StubProvider(fail_typing=True) if typing is None
             else StubProvider(typing=typing))
        r, got = records(p)
        check("%s -> every sentence still has a record" % label,
              got == ids, (len(got), len(ids)))
        check("  and nothing was invented",
              set(got) == set(ids) and len(got) == len(set(got)))
        unres = [x for x in r["records"] if x["type"] == CL.UNRESOLVED]
        check("  the unaccounted ones are UNRESOLVED_BOUNDARY, with a reason",
              all((x.get("unresolved_reason") or "") for x in unres), len(unres))
    # behavioural, not a grep for loop keywords: a failing or malformed batch must cost
    # exactly one provider call, so a retry could not hide anywhere.
    n_batches = len(CL._batches(sents))
    for label, p in (("a provider failure", StubProvider(fail_typing=True)),
                     ("a truncated reply", StubProvider(typing='{"sentences": [')),
                     ("prose instead of JSON", StubProvider(typing="no."))):
        CL.identify(p, sentences(20), sents)
        check("%s costs exactly one call per batch -- no retry" % label,
              p.typing_calls == n_batches, (p.typing_calls, n_batches))


# ── deadline plumbing survives the larger batch ─────────────────────────────
def test_the_deadline_still_reaches_identification():
    src = (HERE / "new_engine_v1" / "claims.py").read_text()
    tree = ast.parse(src)
    sites = [x for x in ast.walk(tree) if isinstance(x, ast.Call)
             and getattr(x.func, "attr", "") == "complete"]
    check("identification has exactly one provider call site", len(sites) == 1, len(sites))
    check("it is temperature-pinned and deadline-aware",
          all(any(k.arg == "temperature" for k in x.keywords)
              and any(k.arg == "deadline" for k in x.keywords) for x in sites))
    check("it passes the declared output cap, not a literal",
          any(any(k.arg == "max_tokens"
                  and getattr(k.value, "id", "") == "BATCH_MAX_TOKENS"
                  for k in x.keywords) for x in sites))
    gsrc = (HERE / "new_engine_v1" / "grounding_v2.py").read_text()
    body = gsrc.split("def run_shadow(")[1]
    check("the shadow still takes its clock before identification",
          body.index("deadline = started +") < body.index("CL.identify("))
    check("and still hands it to identification",
          "CL.identify(provider, article_text, sentences, deadline=deadline)" in body)

    class Recorder(StubProvider):
        def __init__(self):
            super().__init__()
            self.deadlines = []

        def complete(self, system, user, max_tokens=3000, timeout=180,
                     temperature=None, deadline=None):
            self.deadlines.append(deadline)
            return super().complete(system, user, max_tokens, timeout, temperature)

    import time
    p = Recorder()
    dl = time.monotonic() + 30
    CL.identify(p, sentences(20), CL.segment(sentences(20)), deadline=dl)
    check("every identification call received the shared deadline",
          p.deadlines and all(d == dl for d in p.deadlines), p.deadlines)


# ── the total call bound ────────────────────────────────────────────────────
def test_the_total_v2_call_bound_fell():
    check("identification ceiling 4", CL.MAX_BATCHES_PER_ARTICLE == 4)
    check("classification ceiling 10, unchanged from #59",
          GV2.MAX_CLASSIFY_BATCHES == 10)
    check("total 14, was 18",
          CL.MAX_BATCHES_PER_ARTICLE + GV2.MAX_CLASSIFY_BATCHES == 14)
    check("classification batch size untouched at 4", GV2.CLASSIFY_BATCH_SIZE == 4)
    check("the shadow deadline is untouched at 120s",
          GV2.GROUNDING_V2_TOTAL_SECONDS == 120 and GV2.MIN_CALL_SECONDS == 10)
    # behavioural: a 72-sentence article cannot exceed the bound
    p = StubProvider()
    out = GV2.run_shadow(p, article_text=sentences(72),
                         pack={"sources": [{"source_id": "S0", "role": "ANCHOR",
                                            "text": "Sentence 000 asserts x.",
                                            "url": "u", "publisher": "p",
                                            "accessed_at": "t", "fetch_status": "ok",
                                            "content_length": 0, "sha256": "",
                                            "excerpts": []}]})
    m = out["metrics"]
    check("an over-long article stays inside 14 calls",
          m["model_calls"] <= 14, m["model_calls"])
    check("  identification part inside 4",
          m["identification_calls"] <= 4, m["identification_calls"])
    check("  classification part inside 10",
          m["classification_calls"] <= 10, m["classification_calls"])


# ── nothing else moved ──────────────────────────────────────────────────────
def test_the_typing_prompt_model_and_contracts_are_untouched():
    src = (HERE / "new_engine_v1" / "claims.py").read_text()
    check("typing system prompt unchanged",
          "You label sentences from one article." in src)
    check("the reply schema is unchanged",
          '"atoms": [{"claim": "one proposition", "verbatim": true|false,' in src)
    check("temperature still pinned to 0", "temperature=0" in src)
    check("segmentation untouched",
          '"sentence_id": "S%03d" % n' in src and '"sha256": sha256_text(piece)' in src)
    check("backbone verification untouched", "def verify_backbone(" in src)
    check("UNRESOLVED semantics untouched",
          "UNRESOLVED_BOUNDARY" in src and "def _unresolved(" in src)
    gsrc = (HERE / "new_engine_v1" / "grounding_v2.py").read_text()
    check("classifier prompt untouched", "You classify ONE claim against" in gsrc)


# ── atomic splits stay tied to the sentence they came from ───────────────────
def test_atoms_stay_tied_to_their_parent_span():
    """A bigger batch puts more sentences in one reply, which is exactly the condition
    under which an atom could be attached to the wrong parent. Checked per atom against
    the segmentation backbone, not against the reply."""
    art = sentences(20)
    sents = CL.segment(art)
    by_id = {s["sentence_id"]: s for s in sents}
    # two atoms per sentence, so splits actually exist to mis-attach
    typing = {"sentences": [{"sentence_id": s["sentence_id"], "type": "EMPIRICAL",
                             "atoms": [{"claim": "first half", "verbatim": False,
                                        "claim_type": "EMPIRICAL"},
                                       {"claim": s["exact_span"], "verbatim": True,
                                        "claim_type": "EMPIRICAL"}]}
                            for s in sents]}
    out = CL.identify(StubProvider(typing=typing), art, sents)
    n_atoms = 0
    for r in out["records"]:
        sid = r["sentence_id"]
        if r["parent_exact_span"] != by_id[sid]["exact_span"]:
            check("%s parent span matches the backbone" % sid, False,
                  r["parent_exact_span"])
        for a in r["atoms"]:
            n_atoms += 1
            if a["parent_sentence_id"] != sid or not a["atomic_id"].startswith(sid + "-A"):
                check("atom %s is tied to %s" % (a["atomic_id"], sid), False, a)
    check("every atom carries its parent id and a parent-prefixed atomic_id",
          n_atoms == 40, n_atoms)
    check("atomic_ids are unique across the whole article",
          len({a["atomic_id"] for r in out["records"] for a in r["atoms"]}) == n_atoms)
    check("a verbatim atom is marked VERBATIM, a paraphrase DERIVED",
          all([a["derivation"] for a in r["atoms"]] == ["DERIVED", "VERBATIM"]
              for r in out["records"]))
    # and the parent span is always genuinely from the article
    check("every parent span is a real substring of the article",
          all(r["parent_exact_span"] in art for r in out["records"]))


# ── shadow OFF means the provider is never touched ──────────────────────────
def test_shadow_off_costs_zero_calls_and_reads_nothing():
    from new_engine_v1 import runner as RUN
    import os
    import tempfile

    class Counting(StubProvider):
        pass

    saved = os.environ.pop(GV2.SHADOW_ENV, None)
    try:
        check("unset means OFF", GV2.enabled() is False)
        for val in ("", "0", "false", "no", "off", "maybe", "TRUE-ish"):
            os.environ[GV2.SHADOW_ENV] = val
            if val.strip().lower() in ("1", "true", "on", "yes"):
                continue
            check("  %r is OFF" % val, GV2.enabled() is False, val)
        os.environ.pop(GV2.SHADOW_ENV, None)
        p = Counting()
        with tempfile.TemporaryDirectory() as d:
            RUN._shadow_grounding_v2(p, pathlib.Path(d), {"article_text": ARTICLE},
                                     ARTICLE, {"sources": []})
            check("shadow OFF makes zero provider calls",
                  p.typing_calls == 0 and p.classify_calls == 0,
                  (p.typing_calls, p.classify_calls))
            check("and writes no artifact at all",
                  list(pathlib.Path(d).iterdir()) == [],
                  [x.name for x in pathlib.Path(d).iterdir()])
        for on in ("1", "true", "on", "yes", "YES", " On "):
            os.environ[GV2.SHADOW_ENV] = on
            check("  %r is ON (explicit opt-in still works)" % on, GV2.enabled() is True)
    finally:
        os.environ.pop(GV2.SHADOW_ENV, None)
        if saved is not None:
            os.environ[GV2.SHADOW_ENV] = saved


# ── V2 output is structurally unable to reach a production decision ─────────
def test_v2_output_is_non_authoritative_by_structure():
    p = StubProvider()
    out = GV2.run_shadow(p, article_text=ARTICLE, pack={"sources": [
        {"source_id": "S0", "role": "ANCHOR", "text": "x", "url": "u",
         "publisher": "p", "accessed_at": "t", "fetch_status": "ok",
         "content_length": 0, "sha256": "", "excerpts": []}]})
    check("the payload declares itself a shadow", out.get("shadow") is True)
    check("and its authority is NONE",
          str(out.get("authority", "")).startswith("NONE"), out.get("authority"))
    # import-level, not prose: the deciding modules must not reference V2 at all.
    for mod in ("decision.py", "stages.py", "publication_safety_bridge.py"):
        f = HERE / "new_engine_v1" / mod
        f = f if f.exists() else HERE / mod
        if not f.exists():
            continue
        tree = ast.parse(f.read_text())
        names = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                names |= {a.name for a in n.names}
            elif isinstance(n, ast.ImportFrom):
                names.add(n.module or "")
                names |= {a.name for a in n.names}
            elif isinstance(n, ast.Attribute):
                names.add(n.attr)
            elif isinstance(n, ast.Name):
                names.add(n.id)
        check("%s never references grounding_v2" % mod,
              not any("grounding_v2" in x or x in ("GV2",) for x in names),
              sorted(x for x in names if "ground" in x.lower()))
    # the runner reaches it only after the decision is persisted
    rsrc = (HERE / "new_engine_v1" / "runner.py").read_text()
    check("the shadow is called after the decision is persisted",
          rsrc.index("_persist(A, run_root") < rsrc.index("_shadow_grounding_v2(provider"))


# ── deadline exhaustion stays a diagnostic ──────────────────────────────────
def test_deadline_exhaustion_is_a_diagnostic_not_a_verdict():
    p = StubProvider()
    pack = {"sources": [{"source_id": "S0", "role": "ANCHOR", "text": "x", "url": "u",
                         "publisher": "p", "accessed_at": "t", "fetch_status": "ok",
                         "content_length": 0, "sha256": "", "excerpts": []}]}
    # a budget already gone before the first classification call
    out = GV2.run_shadow(p, article_text=ARTICLE, pack=pack, total_seconds=0)
    m = out["metrics"]
    check("an exhausted budget is reported, not raised",
          m["deadline_exhausted"] is True, m["deadline_exhausted"])
    check("it is still only a shadow with no authority",
          out.get("shadow") is True and str(out.get("authority", "")).startswith("NONE"))
    check("no classification call is attempted once the budget is gone",
          m["classification_calls"] == 0, m["classification_calls"])
    check("no claim was silently dropped by exhaustion",
          len(out["findings"]) == m["claims_identified"],
          (len(out["findings"]), m["claims_identified"]))
    check("and not one of them carries a real verdict",
          not any(f["result"]["classification"] in GV2.ENUM
                  for f in out["findings"]),
          {f["result"]["classification"] for f in out["findings"]})
    check("the exhaustion label is not a member of the verdict enum",
          GV2.DEADLINE_EXHAUSTED not in GV2.ENUM
          and GV2.CLASSIFIER_ERROR not in GV2.ENUM)
    # a generous budget is not reported as exhausted
    ok = GV2.run_shadow(StubProvider(), article_text=ARTICLE, pack=pack)
    check("a healthy run reports no exhaustion",
          ok["metrics"]["deadline_exhausted"] is False)
    check("the declared bound is still 120s / 10s minimum leg",
          ok["metrics"]["total_seconds_bound"] == 120
          and GV2.MIN_CALL_SECONDS == 10, ok["metrics"]["total_seconds_bound"])
    # the clamp itself: every provider leg gets the shared deadline, never a fresh one
    seen = []

    class Recorder(StubProvider):
        def complete(self, system, user, max_tokens=3000, timeout=180,
                     temperature=None, deadline=None):
            seen.append(deadline)
            return super().complete(system, user, max_tokens, timeout, temperature)

    GV2.run_shadow(Recorder(), article_text=ARTICLE, pack=pack)
    check("every leg of both phases shares one deadline",
          seen and len(set(seen)) == 1 and seen[0] is not None, set(seen))


def main() -> None:
    for fn in (test_the_bounds_are_what_the_measurements_support,
               test_the_coverage_ceiling_is_unchanged,
               test_the_frozen_article_needs_three_batches,
               test_long_sentences_still_split_a_batch_early,
               test_batching_is_deterministic_and_order_preserving,
               test_no_sentence_can_disappear_however_the_reply_breaks,
               test_the_deadline_still_reaches_identification,
               test_the_total_v2_call_bound_fell,
               test_atoms_stay_tied_to_their_parent_span,
               test_shadow_off_costs_zero_calls_and_reads_nothing,
               test_v2_output_is_non_authoritative_by_structure,
               test_deadline_exhaustion_is_a_diagnostic_not_a_verdict,
               test_the_typing_prompt_model_and_contracts_are_untouched):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL IDENTIFICATION BATCHING TESTS PASSED")


if __name__ == "__main__":
    main()
