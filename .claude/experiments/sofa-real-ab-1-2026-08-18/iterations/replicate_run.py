#!/usr/bin/env python3
"""
replicate_run.py — frozen FORM-1.3 variance replicates (R2, R3).

These are NOT new Form versions. They repeat the EXACT frozen FORM-1.3
writer condition: same source, same packet, same rendered writer prompt,
byte for byte, same LOCAL_CLAUDE_SUBSCRIPTION execution mode, one
generation each, no retries, no candidate selection.

The packet and prompt are NOT rebuilt -- they are copied from the original
FORM-1.3 evidence and hash-matched against it, so no byte can drift.

  --init <R>              copy + hash-verify the frozen condition into the
                          replicate dir, write pre-generation metadata.
  --record <R> <file> <model>
                          ingest exactly one generated article, hash it,
                          stamp model identity. Refuses if one exists.
"""
import hashlib, json, os, shutil, sys
from pathlib import Path

REPO = Path("/Users/stargatesgx/code/disability-collective-ai")
ITER = REPO / ".claude/experiments/sofa-real-ab-1-2026-08-18/iterations"
SRC = ITER / "FORM-1.3"

FROZEN = {
    "source":  ("form1-3-source-snapshot.txt", "fee0a03b8bb0c56b88b0806a9120576c87f0983764d8620c77c56b59531d4753"),
    "packet":  ("form1-3-packet.json",         "a620d0ce700a501de1695cc63253b518da283397388dba4dfb1f570af8f8e8ab"),
    "prompt":  ("form1-3-writer-prompt.txt",   "12e520e449752ed89522963c77a48fc2b86636a31a20d8f3ca47ac4ec276cdfd"),
}
CARRY = ["form1-3-writer-system.txt", "form1-3-writer-user.txt"]
EXECUTION_MODE = "LOCAL_CLAUDE_SUBSCRIPTION"
EXPECTED_MODEL = "claude-opus-5[1m]"


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def sha_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def write_fsync(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(data); fh.flush(); os.fsync(fh.fileno())


def do_init(rep):
    out = ITER / rep
    out.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for key, (fn, expected) in FROZEN.items():
        actual = sha_file(SRC / fn)
        if actual != expected:
            raise SystemExit(f"FROZEN {key} MISMATCH in FORM-1.3: expected {expected}, got {actual}")
        shutil.copy2(SRC / fn, out / fn)
        if sha_file(out / fn) != expected:
            raise SystemExit(f"copy of {key} does not hash-match after copy")
        hashes[key] = actual
    for fn in CARRY:
        shutil.copy2(SRC / fn, out / fn)

    meta = {
        "iteration": rep,
        "is_new_form_version": False,
        "repeats_condition": "FORM-1.3 (frozen, byte-identical)",
        "phase": "PRESERVED_PRE_GENERATION",
        "execution_mode": EXECUTION_MODE,
        "is_production_path_replay": False,
        "expected_model_identity": EXPECTED_MODEL,
        "frozen_condition_sha256": hashes,
        "writer_generations_planned": 1,
        "retries": 0,
        "candidates": 1,
        "note": ("Variance replicate. Nothing in the Form, packet, prompt, source or "
                 "commission differs from the original FORM-1.3 run. The fixed FORM-1.3 "
                 "prompt is itself the experimental object."),
    }
    write_fsync(out / f"{rep.lower()}-run-metadata.json", json.dumps(meta, indent=2, ensure_ascii=False))
    print(json.dumps({"ok": True, "replicate": rep, "phase": "initialised",
                      "frozen_condition_sha256": hashes}, indent=2))


def do_record(rep, article_path, model_identity):
    out = ITER / rep
    meta_path = out / f"{rep.lower()}-run-metadata.json"
    meta = json.loads(meta_path.read_text())
    for key, (fn, expected) in FROZEN.items():
        if sha_file(out / fn) != expected:
            raise SystemExit(f"{key} drifted in {rep}")
    if (out / f"{rep.lower()}-article.md").exists():
        raise SystemExit(f"{rep} already has an article. Refusing to re-record (one generation only).")
    if model_identity != EXPECTED_MODEL:
        raise SystemExit(f"MODEL CONFOUND: expected {EXPECTED_MODEL}, got {model_identity}. "
                         f"Refusing to record -- report instead of silently introducing a confound.")

    raw = Path(article_path).read_text(encoding="utf-8")
    article = raw.strip()
    if not article:
        raise SystemExit("Empty generation.")
    write_fsync(out / f"{rep.lower()}-raw-response.txt", raw)
    write_fsync(out / f"{rep.lower()}-article.md", article)
    meta.update({"phase": "GENERATED", "model_identity_local": model_identity,
                 "writer_generations_made": 1,
                 "raw_response_sha256": sha_text(raw),
                 "article_sha256": sha_text(article),
                 "article_word_count": len(article.split())})
    write_fsync(meta_path, json.dumps(meta, indent=2, ensure_ascii=False))
    print(json.dumps({"ok": True, "replicate": rep, "phase": "generated",
                      "model_identity_local": model_identity,
                      "word_count": meta["article_word_count"],
                      "article_sha256": meta["article_sha256"]}, indent=2))


if __name__ == "__main__":
    m = sys.argv[1] if len(sys.argv) > 1 else ""
    if m == "--init":
        do_init(sys.argv[2])
    elif m == "--record":
        do_record(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        raise SystemExit("usage: replicate_run.py --init <R> | --record <R> <file> <model>")
