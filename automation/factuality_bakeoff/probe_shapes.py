import json
import os
import sys

BASE = "/srv/data/cripminds-new-engine-v1/"


def sk(o, dep=0, maxdep=3):
    pad = "  " * dep
    if isinstance(o, dict):
        for k, v in list(o.items())[:16]:
            n = len(v) if isinstance(v, (list, dict, str)) else v
            print(pad, k, "::", type(v).__name__, str(n)[:60])
            if isinstance(v, (dict, list)) and dep < maxdep:
                sk(v, dep + 1, maxdep)
    elif isinstance(o, list) and o:
        print(pad, "[0]::", type(o[0]).__name__)
        if dep < maxdep:
            sk(o[0], dep + 1, maxdep)


for run, files in [
    ("fast-lane-v1-fresh-asl-whitehouse-20260912", ["RESEARCH_PACK.json", "ARTICLE_PACKET.json", "FACT_STATUS.json"]),
    ("fast-lane-v1-replay-td-snap-20260912", ["ARTICLE_PACKET.json", "ARCH.json"]),
    ("replay-ab-20260910T082513Z-30f2477", ["FINAL_EVIDENCE_MANIFEST.json", "WRITER_PACKET.json"]),
]:
    for f in files:
        p = BASE + run + "/" + f
        if not os.path.exists(p):
            print("MISSING", run, f)
            continue
        print("\n#####", run, f)
        try:
            sk(json.load(open(p)))
        except Exception as exc:
            print("  err", exc)
