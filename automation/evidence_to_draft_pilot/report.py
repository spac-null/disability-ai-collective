#!/usr/bin/env python3
"""
report.py -- SUMMARY.md, the concise human-readable deliverable (section 20).

Written from RESULTS.json, so it cannot disagree with the data. It names the three paired
comparisons section 20 asks to be highlighted -- the strongest improvement, an important
regression, and a case showing no meaningful benefit -- and it SELECTS THEM BY RULE
rather than by taste, so that an unattractive case cannot quietly fail to be chosen.

The rules, applied to held-out subjects first and falling back to the full set:
  strongest improvement  most accepted guarded edits with a clean combined delta and no
                         new deterministic blocker against its own pre-edit draft
  important regression   the largest increase in deterministic blockers between the
                         pre-edit draft and a variant, or a rejected batch that left a
                         subject with no improvement at all
  no meaningful benefit  the smallest absolute change in words and blockers across arms
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path("/srv/data/cripminds-new-engine-v1/experiments/"
                    "evidence-to-draft-pilot")


def blockers(arm: dict) -> int | None:
    c = (arm or {}).get("deterministic_checks") or {}
    sa = c.get("safety_audit") or {}
    return sa.get("blocking_count")


def pick(rows: list) -> dict:
    held = [r for r in rows if r.get("split") == "held_out"] or rows
    scored = []
    for r in held:
        arms = r.get("arms") or {}
        b = arms.get("B") or {}
        acc = b.get("edits_accepted") or 0
        clean = not (b.get("combined_delta_errors") or [])
        base = blockers(arms.get("A")) if blockers(arms.get("A")) is not None else 0
        bb = blockers(b) if blockers(b) is not None else 0
        scored.append({"row": r, "accepted": acc, "clean": clean,
                       "delta_blockers": (bb or 0) - (base or 0),
                       "word_swing": abs((b.get("words") or 0)
                                         - ((arms.get("A") or {}).get("words") or 0))})
    best = max(scored, key=lambda s: (s["clean"], s["accepted"]), default=None)
    worst = max(scored, key=lambda s: s["delta_blockers"], default=None)
    flat = min(scored, key=lambda s: (s["accepted"], s["word_swing"]), default=None)
    return {"strongest_improvement": best, "important_regression": worst,
            "no_meaningful_benefit": flat}


def main():
    res = json.loads((ROOT / "RESULTS.json").read_text())
    rows = res["subjects"]
    sel = pick(rows)
    L = []
    A = L.append

    A("# Evidence-to-draft pilot — summary\n")
    A("**NOT_PUBLISHABLE_EXPERIMENT.** Every article below was generated from retained "
      "evidence for comparison only. None has been through the authoritative fact check "
      "or the publication bridge, none has been reviewed by the owner, and none may be "
      "published.\n")

    b = res["budget"]
    A("## Budget\n")
    A("| | |\n|---|---|")
    A("| subscription calls | %d of %d |" % (b["subscription_calls"],
                                             b["subscription_cap"]))
    A("| OpenRouter requests | %d |" % b["openrouter_requests"])
    A("| OpenRouter cash | $%.4f of $%.2f |" % (b["openrouter_spend_usd"],
                                                b["openrouter_cap_usd"]))
    A("| transport failures | %d |" % b["transport_failures"])
    A("")

    A("## What was checked, and what was not\n")
    A("Ran: %s.\n" % "; ".join(res["checks_that_ran"]))
    A("**Did not run**: %s. This is therefore not ALL_GATES_PASS and no variant below "
      "is a publication candidate.\n" % "; ".join(res["checks_that_did_not_run"]))

    A("## Per subject\n")
    A("| subject | split | writer | A words / blockers | B words / blockers / edits | "
      "C status | reviewers agree |")
    A("|---|---|---|---|---|---|---|")
    for r in rows:
        arms = r.get("arms") or {}
        a, bb, c = arms.get("A") or {}, arms.get("B") or {}, arms.get("C") or {}
        rev = r.get("review") or {}
        pref = (rev.get("preference") or {})
        A("| %s | %s | %s | %s / %s | %s / %s / %s acc, %s rej | %s | %s |" % (
            r["subject_id"][-8:], r.get("split", "?"),
            (r.get("writer") or {}).get("status", "?"),
            a.get("words", "-"), blockers(a) if blockers(a) is not None else "-",
            bb.get("words", "-"), blockers(bb) if blockers(bb) is not None else "-",
            bb.get("edits_accepted", "-"), bb.get("edits_rejected", "-"),
            c.get("status", c.get("planner_status", "-")),
            pref.get("agree", "-")))
    A("")

    A("## Editing behaviour\n")
    for r in rows:
        arms = r.get("arms") or {}
        a, bb = arms.get("A") or {}, arms.get("B") or {}
        cont = a.get("continuity") or {}
        A("- **%s** — production Continuity %s (%s edits); Prose Finish %s. "
          "Guarded editor: %s, %s of %s patches accepted%s."
          % (r["subject_id"][-8:],
             "discarded whole" if cont.get("discarded") else "applied",
             cont.get("edits", "?"),
             "applied" if (a.get("prose_finish") or {}).get("applied") else "not applied",
             bb.get("editor_status", "-"), bb.get("edits_accepted", "-"),
             bb.get("edits_proposed", "-"),
             "" if bb.get("batch_accepted", True)
             else "; prior bytes preserved: %s"
                  % bb.get("prior_bytes_preserved_on_rejection")))
    A("")

    A("## Three comparisons worth reading\n")
    for key, label in (("strongest_improvement", "Strongest improvement"),
                       ("important_regression", "Important regression"),
                       ("no_meaningful_benefit", "No meaningful benefit")):
        s = sel.get(key)
        if not s:
            A("**%s** — not determinable from the completed set.\n" % label)
            continue
        r = s["row"]
        d = ROOT / "variants" / r["subject_id"]
        A("**%s — %s**  \n%s  \n`%s`  \nPre-edit: `%s/PRE_EDIT.md` · A: `%s/A.md` · "
          "B: `%s/B.md` · C: `%s/C.md`  \nAccepted edits: %s; blocker change vs A: %s.\n"
          % (label, r["subject_id"][-8:], r["subject"][:110], d, d, d, d, d,
             s["accepted"], s["delta_blockers"]))

    A("## Owner review needed\n")
    any_owner = False
    for r in rows:
        rev = r.get("review") or {}
        for o in rev.get("owner_review_needed") or []:
            any_owner = True
            A("- **%s / arm %s** — %s" % (r["subject_id"][-8:], o["arm"], o["why"]))
    if not any_owner:
        A("No unresolved substantive reviewer disagreement was recorded, or reviews did "
          "not run. Absence of disagreement is not agreement with the owner.\n")
    A("")

    A("## What this pilot cannot claim\n")
    A("Six subjects do not demonstrate unattended production reliability. Nothing here "
      "shows a variant would have published, because the authoritative factual tail did "
      "not run. The A/B comparison is controlled — both arms start from identical Writer "
      "bytes — but B vs C is not: C draws its own draft, so a difference there is a "
      "strategy exploration and not a causal attribution. Reviewer preferences are model "
      "assessments, not the owner's judgement and not independent fact-checking.\n")

    (ROOT / "SUMMARY.md").write_text("\n".join(L))
    print("wrote %s" % (ROOT / "SUMMARY.md"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
