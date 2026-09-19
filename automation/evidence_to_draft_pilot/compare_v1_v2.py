#!/usr/bin/env python3
"""
compare_v1_v2.py -- what changed when the reviewers were given the whole evidence.

v1 and v2 differ in ONE input: v1 delivered the first 5,000 characters of each source
(60.2% of the retained set); v2 delivered all of it. Same articles, same shuffle map,
same models and settings, same rubric plus an EVIDENCE_NOT_VISIBLE option.

v2 is DIAGNOSTIC RE-EVALUATION AFTER EXPOSURE, not a confirmatory rerun. v1's preference
result stands as the v1 record; v2 is reported beside it, never in place of it.
"""
from __future__ import annotations

import json
import pathlib
import sys

V1 = pathlib.Path("/srv/data/cripminds-new-engine-v1/experiments/"
                  "evidence-to-draft-pilot")
OUT = pathlib.Path("/srv/data/cripminds-new-engine-v1/experiments/"
                   "evidence-to-draft-pilot-audit-v2")


def located(review, arm):
    v = ((review or {}).get("by_arm") or {}).get(arm) or {}
    return v.get("located_count", 0)


def status_counts(review, arm):
    """v2 adds a status per objection: UNSUPPORTED / CONTRADICTED / EVIDENCE_NOT_VISIBLE."""
    v = ((review or {}).get("by_arm") or {}).get(arm) or {}
    out = {}
    for c in v.get("located_material_objections") or []:
        s = (c.get("status") or "UNSPECIFIED").upper()
        out[s] = out.get(s, 0) + 1
    return out


def main():
    man = json.loads((V1 / "EXPERIMENT_MANIFEST.json").read_text())
    runs = man["development_subjects"] + man["held_out_subjects"]
    rows = []
    tot = {"v1_A": 0, "v1_B": 0, "v2_A": 0, "v2_B": 0}
    pref = {"v1": {}, "v2": {}}
    conf = {"v1": {}, "v2": {}}
    statuses = {}

    print("%-10s %-6s | %-11s | %-11s | %-17s | %-17s"
          % ("subject", "split", "v1 objs A/B", "v2 objs A/B", "v1 pref c/x (conf)",
             "v2 pref c/x (conf)"))
    for run in runs:
        v1f = V1 / "reviews" / ("%s.json" % run)
        v2f = OUT / ("REVIEW_V2_%s.json" % run)
        if not (v1f.exists() and v2f.exists()):
            continue
        a = json.loads(v1f.read_text())
        b = json.loads(v2f.read_text())
        split = "dev" if run in man["development_subjects"] else "held"

        r = {"subject_id": run, "split": split, "v1": {}, "v2": {}}
        for tag, d in (("v1", a), ("v2", b)):
            for arm in ("A", "B"):
                r[tag]["%s_claude" % arm] = located(d["claude"], arm)
                r[tag]["%s_codex" % arm] = located(d["codex"], arm)
            for who in ("claude", "codex"):
                p = (d[who] or {}).get("preference_by_arm") or {}
                r[tag]["%s_pref" % who] = p.get("best")
                r[tag]["%s_conf" % who] = p.get("confidence")
                pref[tag][p.get("best")] = pref[tag].get(p.get("best"), 0) + 1
                c = (p.get("confidence") or "UNSTATED").upper()
                conf[tag][c] = conf[tag].get(c, 0) + 1
        for arm in ("A", "B"):
            tot["v1_%s" % arm] += r["v1"]["%s_claude" % arm] + r["v1"]["%s_codex" % arm]
            tot["v2_%s" % arm] += r["v2"]["%s_claude" % arm] + r["v2"]["%s_codex" % arm]
            for who in ("claude", "codex"):
                for k, n in status_counts(b[who], arm).items():
                    statuses[k] = statuses.get(k, 0) + n
        rows.append(r)
        print("%-10s %-6s | %5s/%-5s | %5s/%-5s | %6s/%-6s %-3s | %6s/%-6s %s"
              % (run[-8:], split,
                 r["v1"]["A_claude"] + r["v1"]["A_codex"],
                 r["v1"]["B_claude"] + r["v1"]["B_codex"],
                 r["v2"]["A_claude"] + r["v2"]["A_codex"],
                 r["v2"]["B_claude"] + r["v2"]["B_codex"],
                 r["v1"]["claude_pref"], r["v1"]["codex_pref"],
                 (r["v1"]["claude_conf"] or "")[:3],
                 r["v2"]["claude_pref"], r["v2"]["codex_pref"],
                 (r["v2"]["claude_conf"] or "")[:3]))

    print()
    print("TOTAL LOCATED MATERIAL OBJECTIONS")
    print("   v1:  A=%d  B=%d   (delivered 60.2%% of the evidence)"
          % (tot["v1_A"], tot["v1_B"]))
    print("   v2:  A=%d  B=%d   (delivered 100%%)" % (tot["v2_A"], tot["v2_B"]))
    print()
    print("PREFERENCE VOTES (12 per evaluation)")
    print("   v1:", json.dumps(pref["v1"]), " confidence:", json.dumps(conf["v1"]))
    print("   v2:", json.dumps(pref["v2"]), " confidence:", json.dumps(conf["v2"]))
    print()
    print("V2 OBJECTION STATUS (the option v1 could not express):")
    print("  ", json.dumps(statuses))

    payload = {"evaluation_version": 2,
               "v2_is": "diagnostic re-evaluation after exposure, not confirmatory",
               "only_input_difference": "complete frozen evidence instead of the first "
                                        "5000 characters of each source",
               "per_subject": rows,
               "totals": tot, "preferences": pref, "confidence": conf,
               "v2_objection_status_counts": statuses}
    (OUT / "AB_V1_VS_V2.json").write_text(json.dumps(payload, indent=1,
                                                     ensure_ascii=False))
    print("\nwrote %s" % (OUT / "AB_V1_VS_V2.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
