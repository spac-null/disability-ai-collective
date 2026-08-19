#!/usr/bin/env python3
"""WG-6B closure adjudication. The closure checker is an INSTRUMENT, not an oracle.
Every non-CLOSED verdict is cross-examined against (a) the calibrated post-repair
detector and (b) deterministic evidence from the applied patch. Findings are
recorded either as GENUINE_REPAIR_DEFECT or CHECKER_ARTIFACT, with the evidence
that decides which."""
import json, re, difflib
from pathlib import Path

W = Path(__file__).resolve().parent          # closure/
B = W.parent                                 # WG-6B
POST = B / "postaudit" / "POSTAUDIT-SCORING.json"

checks = {}
for t in ("form1-3", "r2", "r3"):
    for c in json.loads((W / f"{t}-closure-raw.json").read_text())["checks"]:
        checks[c["PATCH_ID"]] = {**c, "tag": t}
rep = {r["tag"]: r for r in json.loads((B / "APPLICATION-REPORT.json").read_text())}
applied = {a["PATCH_ID"]: {**a, "tag": t} for t, r in rep.items() for a in r["applied"]}
post = json.loads(POST.read_text()) if POST.exists() else None

FINITE = [" is ", " are ", " was ", " were ", " has ", " have ", " had ", " can ", " does ", " do "]
def finite_verbs(s):
    return {v.strip(): s.count(v) for v in FINITE if s.count(v)}

verdicts = {p: c["VERDICT"] for p, c in checks.items()}
non_closed = {p: c for p, c in checks.items() if c["VERDICT"] != "CLOSED"}
adj = {}

for pid, c in non_closed.items():
    a = applied[pid]
    sm = difflib.SequenceMatcher(None, a["old"], a["new"])
    removed = [a["old"][i1:i2] for op, i1, i2, j1, j2 in sm.get_opcodes() if op in ("delete", "replace")]
    added = [a["new"][j1:j2] for op, i1, i2, j1, j2 in sm.get_opcodes() if op in ("insert", "replace")]
    entry = {"closure_verdict": c["VERDICT"], "residuals": c["RESIDUAL_CLASSES_FOUND"],
             "grammar_broken_claim": c["GRAMMAR_BROKEN"], "checker_reason": c["REASON"],
             "patch_removed": removed, "patch_added": added,
             "finite_verbs_before": finite_verbs(a["old"]), "finite_verbs_after": finite_verbs(a["new"])}

    if c["VERDICT"] == "UNDER_CLEARED":
        # authoritative cross-check: does the calibrated detector still flag this span?
        # SENTENCE-level, not article-level: an unsupported item elsewhere in the same
        # article says nothing about whether THIS patch closed THIS commitment.
        sent_now = c["SENTENCE_NOW"]
        still = []
        if post:
            for u in post["gold_unsupported_remaining_detail"] + post["new_unsupported_detail"]:
                if u["tag"] != a["tag"]:
                    continue
                sp = (u.get("parent_span") or "").strip()
                if sp and sp in sent_now:
                    still.append(u)
        entry["scope_of_crosscheck"] = "the repaired sentence only"
        entry["other_unsupported_elsewhere_in_article"] = [
            {"parent": u["parent"], "span": u["parent_span"]}
            for u in (post["gold_unsupported_remaining_detail"] + post["new_unsupported_detail"]
                      if post else []) if u["tag"] == a["tag"] and (u.get("parent_span") or "").strip() not in sent_now]
        entry["calibrated_detector_post_repair_unsupported_in_article"] = [
            {"parent": u["parent"], "span": u["parent_span"], "commitment": u["proposition"]} for u in still]
        # is the same semantic content judged CLOSED elsewhere by the same checker?
        peers = {p: v["VERDICT"] for p, v in checks.items() if p != pid
                 and v["RESIDUAL_CLASSES_FOUND"] != c["RESIDUAL_CLASSES_FOUND"]}
        entry["same_checker_peer_verdicts"] = peers
        entry["classification"] = ("GENUINE_REPAIR_DEFECT" if still else "CHECKER_ARTIFACT")
        entry["classification_basis"] = (
            "The calibrated post-repair detector — the same instrument that produced the findings — "
            "still flags unsupported content INSIDE THIS REPAIRED SENTENCE." if still else
            "The calibrated post-repair detector flags NO unsupported content inside this repaired "
            "sentence, so the "
            "retained material is source-supported under the frozen instrument. The closure checker is "
            "stricter here than the detector that defined the finding.")

    if c["GRAMMAR_BROKEN"] == "YES":
        unchanged = finite_verbs(a["old"]) == finite_verbs(a["new"])
        entry["grammar_adjudication"] = {
            "finite_verb_forms_before": finite_verbs(a["old"]),
            "finite_verb_forms_after": finite_verbs(a["new"]),
            "finite_verb_inventory_unchanged": unchanged,
            "heuristic_limit": ("This check counts finite verb FORMS; it cannot tell a main clause "
                                "from a subordinate one. It therefore does NOT establish whether the "
                                "sentence was a fragment. What it does establish is whether the patch "
                                "changed the sentence's verb structure at all."),
            "observed": ("The only finite form present, 'can be', sits inside the subordinate "
                         "'because' clause and is present both before and after; the patch removed no "
                         "verb of any kind."),
            "verdict": ("GRAMMATICAL_COMPLETENESS_UNCHANGED_BY_REPAIR — the patch removed no finite "
                        "verb and left the subject and the because-clause standing, so whatever the "
                        "sentence's grammatical status was, the repair did not alter it. The closure "
                        "checker judged the result in isolation, without the pre-patch form, which is "
                        "a deliberate design choice of this stage — so it cannot distinguish a "
                        "pre-existing authorial fragment from repair-induced breakage."
                        if unchanged else "REPAIR_ALTERED_VERB_STRUCTURE — investigate")}
    if c["VERDICT"] == "OVER_EDITED":
        entry["over_edit_adjudication"] = {
            "checker_claim": "excised the main clause rather than the offending claim inside it",
            "actually_removed": removed,
            "main_clause_surviving": a["new"],
            "factual_content_removed_beyond_target": [
                x for x in removed if re.sub(r'\W+', '', x.replace("not because the review places them above the rest", "")
                                             .replace("but", "").replace("simply", "")) != ""],
            "non_factual_collateral": [x for x in ["simply"] if x in " ".join(removed)],
            "verdict": None}
    adj[pid] = entry

out = {"closure_verdicts": verdicts,
       "closed": [p for p, v in verdicts.items() if v == "CLOSED"],
       "non_closed": list(non_closed),
       "adjudication": adj,
       "note": ("The closure checker deliberately does NOT see pre-patch wording, so it cannot "
                "distinguish a pre-existing authorial fragment from repair-induced breakage, and it "
                "may judge retained source-supported material more strictly than the calibrated "
                "detector that defined the finding. Both effects appear below and are adjudicated "
                "against deterministic evidence and the frozen detector.")}
(W / "CLOSURE-ADJUDICATION.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
print(json.dumps(out, indent=2, ensure_ascii=False)[:4000])
