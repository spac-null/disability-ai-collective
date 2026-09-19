"""Emit HARDWARE.json, LICENSES.json, MANIFEST.json and span-localization metrics."""
import json
import os
import subprocess
import sys

B = "/srv/data/cripminds-new-engine-v1/experiments/factuality-bakeoff"
REPO = "/srv/data/hermes/workspace/factuality-bakeoff"


def sh(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                              timeout=60).stdout.strip()
    except Exception as exc:
        return "ERR %s" % exc


# ---------------------------------------------------------------- hardware
hardware = {
    "host": sh("hostname"),
    "kernel": sh("uname -r"),
    "cpu_model": sh("lscpu | grep 'Model name' | head -1 | cut -d: -f2 | xargs"),
    "cpu_threads": sh("nproc"),
    "ram_total": sh("free -h | awk '/^Mem:/{print $2}'"),
    "gpu": sh("nvidia-smi --query-gpu=name --format=csv,noheader"),
    "gpu_vram": sh("nvidia-smi --query-gpu=memory.total --format=csv,noheader"),
    "nvidia_driver": sh("nvidia-smi --query-gpu=driver_version --format=csv,noheader"),
    "cuda_toolkit": sh("nvcc --version 2>/dev/null | tail -2 | head -1"),
    "disk_root": sh("df -h / | tail -1"),
    "note": "Single shared workstation that also runs Crip Minds production cron. Disk was "
            "the binding constraint during setup; model downloads were sequenced to keep "
            "headroom and no unrelated data was deleted.",
}
with open(B + "/HARDWARE.json", "w") as fh:
    json.dump(hardware, fh, indent=1)

# ---------------------------------------------------------------- licences
def model_licenses():
    out = {}
    try:
        os.environ.setdefault("HF_HOME", B + "/models/hf")
        from huggingface_hub import HfApi
        api = HfApi()
        for repo in ["yaxili96/FactCG-DeBERTa-v3-Large", "lytang/MiniCheck-Flan-T5-Large",
                     "KRLabsOrg/lettucedect-v2-mmbert-base",
                     "KRLabsOrg/lettucedect-v2-taxonomy-head",
                     "microsoft/deberta-v3-large", "google/flan-t5-large",
                     "jhu-clsp/mmBERT-base"]:
            try:
                i = api.model_info(repo)
                cd = i.card_data or {}
                out[repo] = {"license": cd.get("license"), "revision": i.sha}
            except Exception as exc:
                out[repo] = {"license": "LOOKUP_FAILED", "error": str(exc)[:120]}
    except Exception as exc:
        out["_error"] = str(exc)[:200]
    return out


licenses = {
    "principle": "Code licence and model licence are reported separately; a model licence "
                 "is never inferred from its repository licence.",
    "code": {
        "FactCG": {
            "repo": "https://github.com/derenlei/FactCG",
            "commit": "41f185413312ed9b3904ec03963fe899693498e0",
            "LICENSE_file": "MIT",
            "pyproject_classifier": "Apache Software License",
            "flag": "INCONSISTENT: the LICENSE file says MIT while pyproject.toml classifies "
                    "the project as Apache-2.0. Resolve with the authors before production use.",
        },
        "MiniCheck": {
            "repo": "https://github.com/Liyan06/MiniCheck",
            "commit": "b58b9fa69acbd1015ec970fa65dd752413a053d2",
            "LICENSE_file": "Apache-2.0",
        },
        "LettuceDetect": {
            "repo": "https://github.com/KRLabsOrg/LettuceDetect",
            "commit": "2096ed28f3b662a62b4406795da3d6fbc5490063",
            "release_installed": "0.2.3",
            "LICENSE_file": "MIT",
            "note": "Brief expected ~0.2.2; verified current stable is 0.2.3 (changelog dated "
                    "2026-08-14) and pinned to that.",
        },
    },
    "models": model_licenses(),
    "datasets": {
        "FRANK": {"repo": "https://github.com/artidoro/frank", "license": "MIT",
                  "commit": "80a88fb12cc0bfc17ff6ee2c5ebb0c4f4dd8a5f4", "used": True},
        "RAGTruth": {"license": "NOT_REVIEWED", "used": False,
                     "reason": "not run in this experiment"},
        "MAVEN-ERE": {"license": "NOT_REVIEWED", "used": False,
                      "reason": "not run in this experiment"},
    },
    "remote_code": {
        "trust_remote_code_used": False,
        "note": "No checkpoint required trust_remote_code. All three load through standard "
                "transformers classes.",
    },
    "credentials": {
        "tokens_used": False,
        "note": "All downloads were anonymous public reads. No token was set, printed or stored.",
    },
}
with open(B + "/LICENSES.json", "w") as fh:
    json.dump(licenses, fh, indent=1)

# ---------------------------------------------------- span localization (§16)
span = None
p = B + "/systems/LETTUCEDETECT_GOLD.json"
if os.path.exists(p):
    L = json.load(open(p))
    SUP = {"SUPPORTED_DIRECT", "SUPPORTED_RELATION", "UNDER_CITED_BUT_SUPPORTED",
           "INTERPRETATION_SUPPORTED_PREMISES"}
    cond = "context_SOURCE_COMPLETE"
    tp = fp = fn = 0
    false_span_supported = []
    false_span_interpretation = []
    exact_hits = []
    missed = []
    for r in L["results"]:
        c = r["conditions"].get(cond)
        if not c:
            continue
        gold_unsup = r["gold_label"] not in SUP
        if gold_unsup:
            if c["span_overlaps_gold"]:
                tp += 1
                exact_hits.append({"case_id": r["case_id"],
                                   "gold_span": r["gold_unsupported_span"],
                                   "flagged": [s["text"] for s in c["spans"]],
                                   "overlap_chars": c["best_overlap_chars"]})
            else:
                fn += 1
                missed.append({"case_id": r["case_id"], "failure_type": r["failure_type"],
                               "gold_span": r["gold_unsupported_span"],
                               "flagged": [s["text"] for s in c["spans"]],
                               "n_spans": c["n_spans"]})
                if c["n_spans"]:
                    fp += 1  # flagged, but the wrong words
        else:
            if c["example_flagged"]:
                fp += 1
                rec = {"case_id": r["case_id"], "gold_label": r["gold_label"],
                       "flagged": [s["text"] for s in c["spans"]],
                       "categories": [s.get("category") for s in c["spans"]]}
                false_span_supported.append(rec)
                if r["gold_label"] == "INTERPRETATION_SUPPORTED_PREMISES":
                    false_span_interpretation.append(rec)
    prec = tp / (tp + fp) if (tp + fp) else None
    rec_ = tp / (tp + fn) if (tp + fn) else None
    span = {
        "condition": cond,
        "span_precision": round(prec, 3) if prec is not None else None,
        "span_recall": round(rec_, 3) if rec_ is not None else None,
        "span_f1": round(2 * prec * rec_ / (prec + rec_), 3) if (prec and rec_) else None,
        "useful_exact_localizations": exact_hits,
        "missed_unsupported_spans": missed,
        "false_spans_on_supported_claims": false_span_supported,
        "false_spans_on_editorial_interpretation": false_span_interpretation,
        "n_false_span_claims_supported_family": len(false_span_supported),
        "n_supported_family_cases": sum(1 for r in L["results"] if r["gold_label"] in SUP),
    }
    with open(B + "/analysis/SPAN_METRICS.json", "w") as fh:
        json.dump(span, fh, indent=1)

# ---------------------------------------------------------------- manifest
manifest = {
    "experiment": "Crip Minds specialist factuality / relation checker bake-off",
    "date_utc": __import__("datetime").datetime.now(
        __import__("datetime").timezone.utc).isoformat(),
    "host": hardware["host"],
    "starting_main": "aaf491a468fe73a9e88e85e4011035732722618f",
    "experiment_branch": "pilot/factuality-bakeoff-2026-09-19",
    "worktree": REPO,
    "live_results_root": B,
    "production_authority": "ZERO",
    "production_changed": False,
    "main_changed": False,
    "published": False,
    "cron_changed": False,
    "systems": {
        "FactCG": {"status": "RUN", "checkpoint": "yaxili96/FactCG-DeBERTa-v3-Large",
                   "revision": "0430e3509dbd28d2dff7a117c0eae25359ff3e80"},
        "MiniCheck": {"status": "RUN", "checkpoint": "lytang/MiniCheck-Flan-T5-Large",
                      "revision": "96eafd01cee2d16cf81aaa2fb226b14f422a37b3",
                      "model_choice_frozen_before_scoring": True},
        "LettuceDetect": {"status": "RUN", "checkpoint": "KRLabsOrg/lettucedect-v2-mmbert-base",
                          "revision": "8831ce063dff760b01efe4519b4188f5ee2456f2",
                          "taxonomy_head": "KRLabsOrg/lettucedect-v2-taxonomy-head"},
    },
    "external_datasets": {
        "FRANK": {"status": "RUN",
                  "note": "published valid/test split respected; threshold chosen on "
                          "validation only; test scored once"},
        "RAGTruth": {"status": "NOT_RUN",
                     "reason": "Experiment time was spent on the project-specific set, which "
                               "§8 makes the deciding surface, and on diagnosing a FactCG "
                               "defect. RAGTruth would also be a compatibility check only for "
                               "LettuceDetect, which documents training on it."},
        "MAVEN-ERE": {"status": "NOT_RUN",
                      "reason": "No defensible support/contradiction probe was constructed "
                                "within this experiment; per the brief an invalid probe is "
                                "worse than none, and absence of an annotation is not proof "
                                "of absence."},
    },
    "contamination": {
        "LettuceDetect": "Model card documents training on RAGTruth and PsiloQA. RAGTruth "
                         "results would be a compatibility metric, not independent evidence.",
        "MiniCheck": "Public LLM-AggreFact benchmark history, which includes RAGTruth "
                     "converted into its format. FRANK is not part of LLM-AggreFact.",
        "FactCG": "Public LLM-AggreFact benchmark history; the paper reports FRANK-adjacent "
                  "summarization benchmarks. Treat external numbers as sanity only.",
        "CripMinds_gold": "Freshly built from retained runs; no system has seen it.",
    },
    "stop_conditions_checked": {
        "at_least_30_trusted_examples": True,
        "all_specialists_infeasible": False,
        "licensing_blocks_use": False,
        "measurement_confuses_support_with_materiality": False,
        "set_dominated_by_one_article_or_failure_type": False,
    },
}
with open(B + "/MANIFEST.json", "w") as fh:
    json.dump(manifest, fh, indent=1)

print(json.dumps(hardware, indent=1))
print("\nspan metrics:", json.dumps(span, indent=1)[:900] if span else "n/a")
print("\nwrote HARDWARE.json LICENSES.json MANIFEST.json SPAN_METRICS.json")
