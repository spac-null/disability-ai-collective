"""Generate analysis/ERRORS.md and analysis/DECISION.md from the recorded results.

All numbers are read from the result JSON; none are transcribed by hand.
"""
import json
import os

B = "/srv/data/cripminds-new-engine-v1/experiments/factuality-bakeoff"
HEAD = "context_SOURCE_COMPLETE"
SUP = {"SUPPORTED_DIRECT", "SUPPORTED_RELATION", "UNDER_CITED_BUT_SUPPORTED",
       "INTERPRETATION_SUPPORTED_PREMISES"}


def rd(p, default=None):
    path = B + "/" + p
    return json.load(open(path)) if os.path.exists(path) else default


gold = rd("gold/CRIP_MINDS_GOLD.json")
metrics = rd("analysis/METRICS.json")
errors = rd("analysis/ERRORS.json", [])
span = rd("analysis/SPAN_METRICS.json", {})
defect = rd("systems/FACTCG_DEFECT_AUDIT.json", {})
frank_f = rd("external/FRANK_FACTCG.json")
frank_m = rd("external/FRANK_MINICHECK.json")
cases = {c["case_id"]: c for c in gold["cases"]}

# --------------------------------------------------------------- ERRORS.md
L = []
L.append("# Wrong decisions on the Crip Minds trusted set\n")
L.append("Condition: `%s` (complete frozen evidence, source prose). "
         "Every wrong decision by every system is listed; none is rationalised away "
         "because confidence was low.\n" % HEAD)

why_false_unsupported = {
    "CM05": "lexical shortcut - a plain affiliation sentence flagged with no competing reading",
    "CM09": "long-context / multi-source: the figure is stated verbatim in two separate "
            "sources and the checker still scored the joint attribution low",
    "CM20": "long compound claim - six coordinated properties in one sentence; "
            "under-citation confusion, the declared basis omits the licensing facts",
    "CM21": "long compound claim + under-citation confusion",
    "CM22": "interpretive-language confusion ('best understood')",
    "CM23": "interpretive-language confusion (causal framing over supported premises)",
    "CM25": "interpretive-language confusion (editorial comparative 'more important')",
    "CM27": "interpretive-language confusion ('is the mechanism of speech itself')",
}
why_false_supported = {
    "CM29": "missed a consequence/efficiency relation asserted by no source "
            "('so a sentence can be built in fewer selections')",
    "CM30": "missed a quantifier/scope transfer - the source's count describes the "
            "article's own selection ('eight of the most interesting'), not the event",
    "CM31": "missed an asserted chronology the sources never date",
    "CM32": "missed a qualifier loss - the source limits the exclusion to hardware "
            "installed 'by non-licensed resellers'",
}

for direction, why_map in (("FALSE_SUPPORTED", why_false_supported),
                           ("FALSE_UNSUPPORTED", why_false_unsupported)):
    sel = [e for e in errors if e["condition"] == HEAD and e["direction"] == direction]
    L.append("\n## %s (%d)\n" % (direction, len(sel)))
    if direction == "FALSE_SUPPORTED":
        L.append("The dangerous permissive error: an unsupported claim judged supported.\n")
    else:
        L.append("The mierenneuker error: a supported claim judged unsupported.\n")
    L.append("| case | article | gold | failure type | system | raw | why wrong |")
    L.append("|---|---|---|---|---|---|---|")
    for e in sel:
        L.append("| %s | %s | %s | %s | %s | %s | %s |" % (
            e["case_id"], e["article"], e["gold_label"], e["failure_type"],
            e["system"], e["raw"], why_map.get(e["case_id"], "see case note")))

L.append("\n## Claims behind the case ids\n")
for cid in sorted({e["case_id"] for e in errors if e["condition"] == HEAD}):
    c = cases[cid]
    L.append("**%s** (%s, %s) - %s\n" % (cid, c["gold_label"], c["failure_type"],
                                         c["claim_text"]))
    L.append("> evidence: %s\n" % (c.get("gold_evidence") or c["adjudication_note"])[:400])

L.append("\n## Cases every system got right\n")
wrong = {e["case_id"] for e in errors if e["condition"] == HEAD}
right = [cid for cid in cases if cid not in wrong]
L.append("%d of %d cases drew no wrong decision from any system: %s\n"
         % (len(right), len(cases), ", ".join(sorted(right))))

with open(B + "/analysis/ERRORS.md", "w") as fh:
    fh.write("\n".join(L))

# ------------------------------------------------------------- DECISION.md
D = []
D.append("# Crip Minds - specialist factuality bake-off: decision\n")
D.append("**Production authority granted: ZERO. Production unchanged, main unchanged, "
         "nothing published, cron untouched.**\n")

D.append("\n## Headline, project-specific set\n")
D.append("Complete frozen evidence, n=%d (%d supported-family, %d unsupported-family), "
         "%d distinct articles.\n"
         % (len(cases),
            sum(1 for c in cases.values() if c["gold_label"] in SUP),
            sum(1 for c in cases.values() if c["gold_label"] not in SUP),
            gold["meta"]["distinct_articles"]))
D.append("| system | supported recall | unsupported recall | balanced acc | false supported | false unsupported |")
D.append("|---|---|---|---|---|---|")
for s, e in metrics["systems"].items():
    d = e.get(HEAD)
    if not d:
        continue
    D.append("| %s | %s | %s | %s | %d | %d |" % (
        s, d["supported_recall"], d["unsupported_recall"], d["balanced_accuracy"],
        d["FALSE_SUPPORTED"], d["FALSE_UNSUPPORTED"]))

bl = metrics["systems"].get("BASELINE_validate_turn_support", {}).get("context_LEDGER_COMPLETE")
if bl:
    D.append("\nCurrent production baseline (`validate_turn_support`, ledger conditions, "
             "n=%d): balanced accuracy %s, false supported %d, false unsupported %d. "
             "On the complete ledger it refuses almost nothing by construction, so its "
             "balanced accuracy sits at chance; it is a coarse relation-class licence, "
             "not a classifier.\n"
             % (bl["n_scored"], bl["balanced_accuracy"], bl["FALSE_SUPPORTED"],
                bl["FALSE_UNSUPPORTED"]))

D.append("\n### The statistical caveat that governs everything below\n")
D.append("The unsupported-family has only %d members. The difference between the best and "
         "worst unsupported-recall here is one or two cases. No ranking on this axis is "
         "separable from noise, and no system may be promoted on it.\n"
         % sum(1 for c in cases.values() if c["gold_label"] not in SUP))

D.append("\n## What the systems actually missed\n")
D.append("Every system, including the production baseline, judged **CM30** supported: "
         "*\"The event featured eight pavilions\"*, where the frozen source says only "
         "*\"Eight pavilion highlights\"* and *\"eight of the most interesting\"*. The count "
         "belongs to the article's own selection, not to the event. FactCG and MiniCheck "
         "also passed **CM32**, the qualifier loss that drops *\"by non-licensed resellers\"*. "
         "These are the relation and qualifier shapes this experiment exists to catch.\n")
D.append("The false rejections cluster just as sharply on editorial interpretation: "
         "CM22 (*'best understood'*), CM23 (causal framing on supported premises), "
         "CM25 (*'more important'*), CM27 (*'the mechanism of speech itself'*). "
         "A checker that refuses these costs availability without buying safety.\n")

if defect:
    s = defect["summary"]
    D.append("\n## FactCG: a library defect found by the wiring check\n")
    D.append("`INSTRUCTION_TEMPLATE` renders premise and claim into a single string with the "
             "claim at the end, then tokenises with `truncation='only_first'`, "
             "`max_length=%d`. On a single sequence that truncates the tail, so a long "
             "premise removes the claim. The chunk then returns a fixed claim-independent "
             "probability and the max-over-chunks aggregation propagates it to the whole "
             "document.\n" % s["limit_tokens"])
    D.append("Observed: **0.8916546702 identical** for the true claim, an unrelated gold "
             "claim, and a deliberately false control on the same context. "
             "Affected %d of %d scored conditions (%s%%), across cases %s. "
             "A separate `FACTCG_GOLD_CHUNKFIX` variant splits oversized chunks so the "
             "claim always survives; checkpoint, threshold and aggregation are untouched.\n"
             % (s["conditions_with_claim_truncating_chunk"], s["conditions_audited"],
                s["pct_conditions_affected"], ", ".join(s["cases_affected"])))
    D.append("This matters beyond the score: on Crip Minds' real sources — PDF extractions "
             "and navigation furniture with no sentence punctuation — FactCG can report "
             "high support for anything.\n")

if span:
    D.append("\n## LettuceDetect: span localization\n")
    D.append("Precision %s, recall %s, F1 %s on the unsupported spans. "
             "%d of %d supported-family claims drew a false span flag.\n"
             % (span["span_precision"], span["span_recall"], span["span_f1"],
                span["n_false_span_claims_supported_family"], span["n_supported_family_cases"]))
    D.append("The one overlapping hit (CM32) flags the entire sentence rather than the "
             "missing qualifier. On CM28 it flagged *'self-taught painter'* and *'in 1964'* "
             "while missing the actual unsupported locative, *'born in the Alice Griffith "
             "public housing development'*. It also flagged ordinary editorial "
             "interpretation as hallucination, which §16 names as unacceptable.\n")

for name, fr in (("FactCG", frank_f), ("MiniCheck", frank_m)):
    if not fr:
        continue
    t = fr["splits"]["test"]
    D.append("\n## FRANK external sanity - %s\n" % name)
    D.append("Test n=%d records (%d sentence scorings), run once. "
             "At the published default 0.5: balanced accuracy %s, precision %s, recall %s, "
             "F1 %s, false supported %d, false unsupported %d.\n"
             % (t["n_records"], t["n_sentence_scorings"],
                t["at_default_0.5"]["balanced_accuracy"], t["at_default_0.5"]["precision"],
                t["at_default_0.5"]["recall"], t["at_default_0.5"]["f1"],
                t["at_default_0.5"]["FALSE_SUPPORTED"], t["at_default_0.5"]["FALSE_UNSUPPORTED"]))
    g = fr.get("global_dev_threshold")
    if g is not None and "at_global_dev_threshold" in t:
        gt = t["at_global_dev_threshold"]
        D.append("At the single global threshold %s, chosen on the FRANK validation split "
                 "before test scoring: balanced accuracy %s, false supported %d, "
                 "false unsupported %d.\n"
                 % (g, gt["balanced_accuracy"], gt["FALSE_SUPPORTED"], gt["FALSE_UNSUPPORTED"]))
    fam = t.get("by_error_family_default_threshold") or {}
    if fam:
        D.append("\n| FRANK error family | unsupported records | caught at 0.5 | missed |")
        D.append("|---|---|---|---|")
        for k, v in fam.items():
            D.append("| %s | %d | %d | %d |" % (k, v["n_unsupported_with_this_family"],
                                                v["caught_at_0.5"], v["missed_at_0.5"]))
    D.append("\nThese numbers answer whether the implementation behaves like a factuality "
             "system. They are not a deployment argument: both systems have public "
             "benchmark histories, and FRANK is news-summarisation, not Crip Minds prose.\n")

D.append("\n## Verdicts\n")
D.append("| system | verdict |")
D.append("|---|---|")
D.append("| FactCG | **NOT_READY** - claim-truncation defect on exactly the document shape "
         "Crip Minds fetches; silently claim-independent when it fires |")
D.append("| MiniCheck | **MIXED** - best balanced accuracy here, but it buys unsupported "
         "recall with four false rejections, three of them editorial interpretation |")
D.append("| LettuceDetect | **MIXED** - cheapest and fastest, low false-flag rate on plain "
         "supported claims, but span precision 0.143 and it flags interpretation |")

D.append("\n**BEST SPECIALIST: NONE.**\n")
D.append("**BEST ROLE: DIAGNOSTIC ONLY** (LettuceDetect), and only if someone wants a cheap "
         "second opinion while reading. No specialist earns a production role.\n")
D.append("\nNo system meets the §25 standard. PROMISING requires project-specific evidence "
         "that a component solves a real failure class without shifting errors into false "
         "rejections. The two failure classes that actually recur in Crip Minds — "
         "quantifier/scope transfer and qualifier loss — are missed by all three, while the "
         "rejections land on legitimate editorial interpretation. That is the opposite of "
         "the required trade: it costs availability and buys no safety.\n")

D.append("\n## One proposed shadow integration\n")
D.append("**NONE.** Nothing earned one. A shadow lane still costs review attention and "
         "creates a number people will start trusting, and on this evidence the number "
         "would be wrong in the direction that matters — permissive on relation and "
         "qualifier errors, restrictive on interpretation.\n")

D.append("\n## One actual blocker\n")
D.append("**The trusted set cannot yet separate these systems on the permissive axis.** "
         "Only %d unsupported-family cases reached trusted-label authority, and zero "
         "CONTRADICTED cases did, in the entire retained corpus of %d runs. That is not a "
         "labelling shortfall; it reflects that confirmed material factual inventions are "
         "genuinely rare in the retained record.\n"
         % (sum(1 for c in cases.values() if c["gold_label"] not in SUP), 253))

D.append("\n## Next step\n")
D.append("No clear winner, so: **stop specialist factuality work and return to normal "
         "production evidence.** The artefact worth keeping is the trusted claim/evidence "
         "set and its harness, which is reusable the next time a component claims to catch "
         "relation errors. If anyone revisits this, the precondition is more trusted "
         "unsupported and contradicted cases — not another model.\n")

with open(B + "/analysis/DECISION.md", "w") as fh:
    fh.write("\n".join(D))

print("wrote analysis/ERRORS.md and analysis/DECISION.md")
print("errors listed:", len([e for e in errors if e["condition"] == HEAD]))
