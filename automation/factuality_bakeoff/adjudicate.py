"""Adjudication aid: anchor a candidate claim into a run's complete frozen evidence.

Prints, for each content term of the claim, whether it occurs anywhere in the frozen
sources, plus context windows around the best-matching sentences. Absence is reported
per term so that an UNSUPPORTED judgement rests on a checked absence over the complete
source set, never on a truncated view.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cm_evidence as E

BASE = "/srv/data/cripminds-new-engine-v1/"
STOP = set("""a an the of to in on at for from by with and or but as is are was were be been
being this that these those it its his her their our your my he she they we you i not no
than then so such which who whom whose what when where how why if into over under about
after before during between through can could may might must shall should will would have
has had do does did done more most less least very also only just own same other others
one two them there here also per via""".split())


def terms(text):
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-\.]*", E.normalize(text)[0])
    out, seen = [], set()
    for w in words:
        lw = w.lower().strip(".'-")
        if not lw or lw in STOP or len(lw) < 3 and not lw.isdigit():
            continue
        if lw in seen:
            continue
        seen.add(lw)
        out.append(w)
    return out


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?;])\s+", text) if s.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--claim", required=True)
    ap.add_argument("--sources", default="", help="comma list to restrict (default all)")
    ap.add_argument("--top", type=int, default=6)
    ap.add_argument("--grep", default="", help="extra comma-separated phrases to locate")
    args = ap.parse_args()

    run = E.load_run(BASE + args.run)
    if not run["sources"]:
        print("!! NO FULL FROZEN SOURCE TEXT for", args.run)
        print("   fact support_spans available:", len(run["facts"]))
        return

    want = [s for s in args.sources.split(",") if s] or sorted(run["sources"])
    claim_terms = terms(args.claim)
    print("RUN:", run["run_id"])
    print("SUBJECT:", (run["subject"] or "?")[:180])
    print("SOURCES:", {k: (run["sources"][k]["publisher"], run["sources"][k]["raw_chars"]) for k in want})
    print("\nCLAIM:", args.claim)
    print("\n== TERM PRESENCE over complete frozen evidence ==")
    joined = " \n".join(run["sources"][k]["norm_text"] for k in want).lower()
    missing = []
    for t in claim_terms:
        hit = t.lower() in joined
        if not hit:
            missing.append(t)
        print("   %-28s %s" % (t, "present" if hit else "ABSENT"))
    print("\nABSENT TERMS:", missing or "(none)")

    for phrase in [p for p in args.grep.split(",") if p.strip()]:
        pn = E.normalize(phrase)[0].lower()
        print("\n== GREP %r ==" % phrase)
        found = False
        for k in want:
            tx = run["sources"][k]["norm_text"]
            low = tx.lower()
            start = 0
            while True:
                i = low.find(pn, start)
                if i < 0:
                    break
                found = True
                print("   [%s] ...%s..." % (k, tx[max(0, i - 180):i + len(pn) + 180]))
                start = i + len(pn)
        if not found:
            print("   NOT FOUND in", want)

    print("\n== BEST-MATCHING SOURCE SENTENCES ==")
    scored = []
    low_terms = [t.lower() for t in claim_terms]
    for k in want:
        for s in sentences(run["sources"][k]["norm_text"]):
            sl = s.lower()
            sc = sum(1 for t in low_terms if t in sl)
            if sc:
                scored.append((sc, k, s))
    scored.sort(key=lambda x: -x[0])
    for sc, k, s in scored[:args.top]:
        print("\n   (%d terms) [%s] %s" % (sc, k, s[:700]))


if __name__ == "__main__":
    main()
