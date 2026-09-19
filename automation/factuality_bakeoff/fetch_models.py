"""Download and pin the three specialist checkpoints, recording revision hashes.

Aborts before any download that would take free disk below FLOOR_GB.
"""
import json
import os
import shutil
import sys

FLOOR_GB = 2.2
B = "/srv/data/cripminds-new-engine-v1/experiments/factuality-bakeoff"
os.environ.setdefault("HF_HOME", B + "/models/hf")

from huggingface_hub import snapshot_download  # noqa: E402
from huggingface_hub import HfApi  # noqa: E402

TARGETS = {
    "factcg": ["yaxili96/FactCG-DeBERTa-v3-Large"],
    "minicheck": ["lytang/MiniCheck-Flan-T5-Large"],
    "lettuce": ["KRLabsOrg/lettucedect-v2-mmbert-base", "KRLabsOrg/lettucedect-v2-taxonomy-head"],
}

which = sys.argv[1]
out = {}
api = HfApi()
for repo in TARGETS[which]:
    free = shutil.disk_usage("/").free / 1e9
    print("free GB before %s: %.1f" % (repo, free), flush=True)
    if free < FLOOR_GB:
        print("ABORT: disk floor reached, refusing to download", repo)
        break
    info = api.model_info(repo)
    rev = info.sha
    path = snapshot_download(repo, revision=rev)
    size = sum(
        os.path.getsize(os.path.join(dp, f))
        for dp, _, fs in os.walk(path) for f in fs
        if not os.path.islink(os.path.join(dp, f))
    )
    out[repo] = {
        "revision": rev,
        "path": path,
        "bytes": size,
        "gb": round(size / 1e9, 3),
        "license": (info.card_data or {}).get("license") if info.card_data else None,
        "tags": (info.tags or [])[:20],
    }
    print(json.dumps({repo: out[repo]}, indent=1), flush=True)
    print("free GB after: %.1f" % (shutil.disk_usage("/").free / 1e9), flush=True)

dest = B + "/systems/MODELS_%s.json" % which
prev = {}
if os.path.exists(dest):
    prev = json.load(open(dest))
prev.update(out)
with open(dest, "w") as fh:
    json.dump(prev, fh, indent=1)
print("wrote", dest)
