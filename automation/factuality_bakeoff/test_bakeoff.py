"""Deterministic offline tests for the factuality bake-off harness (§29).

No network, no model, no GPU: these check the measurement layer, which is the thing that
was wrong twice before. Run with:

    python3 -m unittest automation.factuality_bakeoff.test_bakeoff -v
"""
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import cm_evidence as E  # noqa: E402

B = "/srv/data/cripminds-new-engine-v1/experiments/factuality-bakeoff"
GOLD_PATH = B + "/gold/CRIP_MINDS_GOLD.json"
REPO_ROOT = "/srv/data/hermes/workspace/factuality-bakeoff"


def load_gold():
    with open(GOLD_PATH) as fh:
        return json.load(fh)


class TestNormalization(unittest.TestCase):
    """Representation normalization must not become semantic forgiveness (§12)."""

    def test_html_entities_decoded(self):
        raw = "Scott&#8217;s work &amp; the museum&nbsp;show"
        norm, log = E.normalize(raw)
        self.assertNotIn("&#8217;", norm)
        self.assertNotIn("&amp;", norm)
        self.assertIn("html_unescape", log)
        self.assertIn("Scott's work & the museum show", norm)

    def test_unicode_and_quote_folding_logged(self):
        norm, log = E.normalize("“quoted” – dash")
        self.assertEqual(norm, '"quoted" - dash')
        self.assertIn("quote_fold", log)
        self.assertIn("dash_fold", log)

    def test_negation_is_preserved(self):
        for raw in ["the walls are not parallel",
                    "no published estimate exists",
                    "without an interpreter",
                    "cannot be verified"]:
            sig_before = E.content_signature(raw)
            norm, _ = E.normalize(raw)
            sig_after = E.content_signature(norm)
            self.assertEqual(sig_before["negations"], sig_after["negations"])
            self.assertTrue(sig_after["negations"], "negation token lost for %r" % raw)

    def test_numbers_are_preserved_and_not_merged(self):
        a = E.content_signature("more than 80 works")
        b = E.content_signature("over 100 works")
        self.assertEqual(a["numbers"], ["80"])
        self.assertEqual(b["numbers"], ["100"])
        self.assertNotEqual(a["numbers"], b["numbers"])

    def test_qualifiers_are_preserved(self):
        raw = "non-approved hardware, by non-licensed resellers"
        norm, _ = E.normalize(raw)
        self.assertIn("non-licensed resellers", norm)

    def test_no_word_removal_or_reordering(self):
        raw = "  The   museum  said it  would not  comment.  "
        norm, _ = E.normalize(raw)
        self.assertEqual(norm, "The museum said it would not comment.")
        self.assertEqual(E.content_signature(raw)["word_count"],
                         E.content_signature(norm)["word_count"])

    def test_normalization_is_idempotent(self):
        raw = "&amp;“x” – 1980’s"
        once, _ = E.normalize(raw)
        twice, _ = E.normalize(once)
        self.assertEqual(once, twice)


class TestEvidenceDelivery(unittest.TestCase):
    """The previous audit's headline defect was silent source truncation."""

    def test_complete_evidence_is_not_truncated(self):
        gold = load_gold()
        case = gold["cases"][0]
        run = E.load_run("/srv/data/cripminds-new-engine-v1/" + case["evidence_run_id"])
        ctx, ids = E.source_text_for(run, None, complete=True)
        for sid in ids:
            full = run["sources"][sid]["norm_text"]
            self.assertIn(full, ctx, "source %s was truncated in the delivered context" % sid)

    def test_every_case_context_contains_whole_sources(self):
        gold = load_gold()
        for case in gold["cases"]:
            run = E.load_run("/srv/data/cripminds-new-engine-v1/" + case["evidence_run_id"])
            ctx = case["context_SOURCE_COMPLETE"]
            for sid in case["complete_source_ids"]:
                self.assertIn(run["sources"][sid]["norm_text"], ctx,
                              "%s: source %s not delivered in full" % (case["case_id"], sid))

    def test_no_silent_prefix_cap(self):
        """No context is a round-number prefix of its source set."""
        gold = load_gold()
        for case in gold["cases"]:
            n = len(case["context_SOURCE_COMPLETE"])
            for cap in (1000, 2000, 4000, 8000, 12000, 16000, 24000, 32000):
                self.assertNotEqual(n, cap, "%s context length equals a suspicious cap" % case["case_id"])


class TestGoldIntegrity(unittest.TestCase):

    def test_per_article_cap_respected(self):
        gold = load_gold()
        counts = {}
        for c in gold["cases"]:
            counts[c["article_key"]] = counts.get(c["article_key"], 0) + 1
        for art, n in counts.items():
            self.assertLessEqual(n, 2, "article %s contributes %d cases (cap is 2)" % (art, n))

    def test_minimum_size_and_diversity(self):
        gold = load_gold()
        self.assertGreaterEqual(len(gold["cases"]), 30)
        self.assertGreaterEqual(len({c["article_key"] for c in gold["cases"]}), 15)

    def test_not_dominated_by_one_failure_type(self):
        gold = load_gold()
        types = {}
        for c in gold["cases"]:
            types[c["failure_type"]] = types.get(c["failure_type"], 0) + 1
        worst = max(types.values())
        self.assertLess(worst / len(gold["cases"]), 0.5,
                        "one failure type dominates the set: %r" % types)

    def test_label_authority_is_trusted_only(self):
        allowed = {"DIRECT_SOURCE", "POSTMORTEM_CONFIRMED", "OWNER_CONFIRMED"}
        for c in load_gold()["cases"]:
            parts = set(c["authority"].split("+"))
            self.assertTrue(parts <= allowed,
                            "%s uses non-trusted authority %r" % (c["case_id"], c["authority"]))

    def test_no_unresolved_label_in_scored_gold(self):
        for c in load_gold()["cases"]:
            self.assertNotIn(c["gold_label"], {"UNRESOLVED", "", None})

    def test_claim_is_not_empty_and_is_normalized(self):
        for c in load_gold()["cases"]:
            self.assertTrue(c["claim_text"].strip())
            self.assertEqual(c["claim_text"], E.normalize(c["claim_text"])[0])

    def test_claim_evidence_identity(self):
        """Each case's evidence must come from the run it names."""
        for c in load_gold()["cases"]:
            run = E.load_run("/srv/data/cripminds-new-engine-v1/" + c["evidence_run_id"])
            self.assertTrue(run["sources"], "%s has no frozen sources" % c["case_id"])
            self.assertEqual(sorted(run["sources"]), sorted(c["complete_source_ids"]))


class TestNoLeakage(unittest.TestCase):
    """Labels, notes and adjudication must never reach a system's input (§29)."""

    LABEL_WORDS = ["SUPPORTED_DIRECT", "UNSUPPORTED_RELATION", "PERIPHERAL_UNSUPPORTED",
                   "INTERPRETATION_SUPPORTED_PREMISES", "UNDER_CITED_BUT_SUPPORTED",
                   "DIRECT_SOURCE", "OWNER_CONFIRMED", "POSTMORTEM_CONFIRMED"]

    def test_contexts_carry_no_label_vocabulary(self):
        for c in load_gold()["cases"]:
            for key in ("context_SOURCE_CITED_BASIS", "context_SOURCE_COMPLETE",
                        "context_LEDGER_CITED_BASIS", "context_LEDGER_COMPLETE"):
                ctx = c.get(key) or ""
                for w in self.LABEL_WORDS:
                    self.assertNotIn(w, ctx, "%s/%s leaks %s" % (c["case_id"], key, w))

    def test_contexts_carry_no_adjudication_note(self):
        for c in load_gold()["cases"]:
            note = c["adjudication_note"][:60]
            self.assertNotIn(note, c["context_SOURCE_COMPLETE"])

    def test_claim_not_verbatim_in_ledger_context(self):
        """A ledger context must never simply restate the claim."""
        for c in load_gold()["cases"]:
            for key in ("context_LEDGER_CITED_BASIS", "context_LEDGER_COMPLETE"):
                ctx = c.get(key)
                if not ctx:
                    continue
                for line in ctx.split("\n"):
                    prop = re.sub(r"^\[[^\]]+\]\s*", "", line)
                    self.assertNotEqual(prop.strip(), c["claim_text"].strip(),
                                        "%s: claim appears verbatim as a ledger fact" % c["case_id"])


class TestConditionSeparation(unittest.TestCase):
    """CITED_BASIS and COMPLETE_FROZEN_EVIDENCE must stay separate (§14)."""

    def test_conditions_are_stored_separately(self):
        for c in load_gold()["cases"]:
            self.assertIn("context_SOURCE_CITED_BASIS", c)
            self.assertIn("context_SOURCE_COMPLETE", c)

    def test_cited_ids_are_subset_of_complete(self):
        for c in load_gold()["cases"]:
            self.assertTrue(set(c["cited_source_ids"]) <= set(c["complete_source_ids"]))

    def test_results_keep_conditions_apart(self):
        for name in ("FACTCG_GOLD.json", "MINICHECK_GOLD.json"):
            path = B + "/systems/" + name
            if not os.path.exists(path):
                continue
            obj = json.load(open(path))
            for r in obj["results"]:
                keys = set(r["scores"])
                self.assertTrue(keys <= {"context_SOURCE_CITED_BASIS", "context_SOURCE_COMPLETE",
                                         "context_LEDGER_CITED_BASIS", "context_LEDGER_COMPLETE"})
                self.assertNotIn("combined", keys)


class TestThresholdDiscipline(unittest.TestCase):

    def test_gold_threshold_is_the_published_default(self):
        for name in ("FACTCG_GOLD.json", "MINICHECK_GOLD.json"):
            path = B + "/systems/" + name
            if not os.path.exists(path):
                continue
            obj = json.load(open(path))
            self.assertIn("0.5", obj["threshold_policy"])
            self.assertIn("no tuning", obj["threshold_policy"].lower())

    def test_frank_threshold_chosen_on_validation_only(self):
        for name in ("FRANK_FACTCG.json", "FRANK_MINICHECK.json"):
            path = B + "/external/" + name
            if not os.path.exists(path):
                continue
            obj = json.load(open(path))
            self.assertIn("valid", obj["splits"])
            self.assertIn("threshold_search", obj["splits"]["valid"])
            self.assertNotIn("threshold_search", obj["splits"].get("test", {}),
                             "a threshold was searched on the FRANK test split")

    def test_frank_split_membership_respected(self):
        """Published split files must agree with the split field used for scoring."""
        data = B + "/repos/frank/data"
        if not os.path.exists(data + "/validation_split.txt"):
            self.skipTest("FRANK not cloned")
        val = set(open(data + "/validation_split.txt").read().split())
        tst = set(open(data + "/test_split.txt").read().split())
        self.assertFalse(val & tst, "FRANK validation and test splits overlap")
        anns = json.load(open(data + "/human_annotations.json"))
        for a in anns:
            if a.get("split") == "valid":
                self.assertIn(a["hash"], val)
            elif a.get("split") == "test":
                self.assertIn(a["hash"], tst)


class TestExternalDatasetHonesty(unittest.TestCase):
    """Datasets that were NOT run must be recorded as not run, never implied (§22, §28)."""

    def test_manifest_declares_ragtruth_and_maven_status(self):
        path = B + "/MANIFEST.json"
        if not os.path.exists(path):
            self.skipTest("manifest not written yet")
        man = json.load(open(path))
        ext = man.get("external_datasets", {})
        for name in ("RAGTruth", "MAVEN-ERE"):
            self.assertIn(name, ext)
            self.assertIn("status", ext[name])
            self.assertIn(ext[name]["status"], {"RUN", "NOT_RUN"})
            if ext[name]["status"] == "NOT_RUN":
                self.assertTrue(ext[name].get("reason"))

    def test_no_ragtruth_result_file_claims_implicit_true_collapse(self):
        path = B + "/external/RAGTRUTH_RESULTS.json"
        if not os.path.exists(path):
            self.skipTest("RAGTruth not run")
        obj = json.load(open(path))
        self.assertIn("implicit_true", json.dumps(obj),
                      "RAGTruth results must keep implicit_true separate")

    def test_maven_absent_relation_not_scored_as_negative(self):
        path = B + "/external/MAVEN_PROBES.json"
        if not os.path.exists(path):
            self.skipTest("MAVEN not run")
        obj = json.load(open(path))
        self.assertNotIn("absent_as_negative", json.dumps(obj))


class TestSafetyAndSideEffects(unittest.TestCase):

    def test_live_results_live_outside_the_git_repo(self):
        self.assertFalse(B.startswith(REPO_ROOT))
        for sub in ("gold", "systems", "analysis", "external", "models"):
            self.assertFalse(os.path.join(B, sub).startswith(REPO_ROOT))

    def test_no_model_weights_or_corpora_inside_repo(self):
        bad = []
        for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
            if ".git" in dirpath:
                continue
            for f in filenames:
                if f.endswith((".safetensors", ".bin", ".ckpt", ".pt", ".onnx")):
                    bad.append(os.path.join(dirpath, f))
        self.assertEqual(bad, [], "model weights committed into the repo: %r" % bad[:3])

    def test_baseline_module_is_offline_and_readonly(self):
        """The production baseline must not open network or write anything."""
        src = open(os.path.join(HERE, "cm_baseline.py")).read()
        for bad in ("requests", "urllib", "http", "openai", "anthropic",
                    "open(", "write", "subprocess"):
            self.assertNotIn(bad, src, "baseline module references %r" % bad)

    def test_harness_has_no_paid_api_fallback(self):
        for name in os.listdir(HERE):
            # this file names the forbidden endpoints in order to assert their absence
            if not name.endswith(".py") or name == os.path.basename(__file__):
                continue
            src = open(os.path.join(HERE, name)).read()
            for bad in ("api.openai.com", "api.anthropic.com", "openrouter",
                        "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
                self.assertNotIn(bad, src, "%s references paid API %r" % (name, bad))

    def test_no_publishing_side_effects_in_harness(self):
        for name in os.listdir(HERE):
            # this file names the forbidden operations in order to assert their absence
            if not name.endswith(".py") or name == os.path.basename(__file__):
                continue
            src = open(os.path.join(HERE, name)).read()
            for bad in ("git push", "git commit", "publish(", "deploy(", "crontab"):
                self.assertNotIn(bad, src, "%s has a publishing side effect %r" % (name, bad))


class TestBaselineSemantics(unittest.TestCase):
    """The baseline must keep answering its own question, unchanged."""

    def test_relation_class_licence_behaviour(self):
        import cm_baseline as BL
        facts = {"F1": {"proposition": "The ramp provides resistance when dancers move up."}}
        # a CAUSE trigger with no licensing fact -> refusal
        res = BL.check("The ramp matters because it resists movement.", ["F1"], facts)
        self.assertEqual(res["decision"], "UNSUPPORTED")
        self.assertIn("CAUSE", [e["relation"] for e in res["errors"]])
        # no relation asserted -> nothing to license
        res2 = BL.check("The ramp has a steep peak.", ["F1"], facts)
        self.assertEqual(res2["decision"], "SUPPORTED")

    def test_documented_question_is_recorded(self):
        import cm_baseline as BL
        self.assertIn("class", BL.QUESTION.lower())

    def test_conditions_reported_separately(self):
        import cm_baseline as BL
        # the complete ledger licenses CAUSE (F1) and CONSEQUENCE (F3); the cited
        # basis (F2 alone) licenses neither, so the two conditions must disagree.
        facts = {"F1": {"proposition": "A happened because B happened."},
                 "F2": {"proposition": "C happened."},
                 "F3": {"proposition": "B happened, so C followed."}}
        both = BL.both_conditions("A happened because B happened, so C followed.", ["F2"], facts)
        self.assertIn("CITED_BASIS", both)
        self.assertIn("COMPLETE_FROZEN_EVIDENCE", both)
        self.assertNotEqual(both["CITED_BASIS"]["decision"],
                            both["COMPLETE_FROZEN_EVIDENCE"]["decision"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
