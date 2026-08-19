#!/usr/bin/env python3
"""
sofa_form1_3_run.py — FORM-1.3, LOCAL_CLAUDE_SUBSCRIPTION execution.

This is a MANUAL ARCHITECTURE-DEVELOPMENT RUN, not a production-path
replay. The writer is the local Claude subscription, not the frozen
Edinburgh path (openrouter/claude-opus-4.8 via CLIProxy). No OpenRouter,
no Trident, no Fable.

Because the writer is invoked through the local agent harness rather than
an HTTP API, the run is split so the executed prompt is still provably the
persisted prompt:

  --preserve            verify frozen inputs by SHA-256, build the packet,
                        render the writer prompt, persist packet + prompt +
                        metadata + hashes, fsync. NO GENERATION.
  --record <file> <model>
                        hash-check that the packet and prompt on disk still
                        match, then ingest exactly one generated article,
                        persist it and its hash, and stamp the model
                        identity actually used. Refuses if an article
                        already exists (one generation only).
"""
import hashlib
import json
import os
import sys
from pathlib import Path

REPO = Path("/Users/stargatesgx/code/disability-collective-ai")
CASE_DIR = REPO / ".claude/experiments/sofa-real-ab-1-2026-08-18/case"
OUT_DIR = REPO / ".claude/experiments/sofa-real-ab-1-2026-08-18/iterations/FORM-1.3"
sys.path.insert(0, str(OUT_DIR))

EXPECTED_SOURCE_SHA256 = "fee0a03b8bb0c56b88b0806a9120576c87f0983764d8620c77c56b59531d4753"
EXPECTED_COMMISSION_SHA256 = "870d84ba931abf194db5fad8017185cbf2f034ec08e383d1d89fcb8b3fce3387"
EXPECTED_EVIDENCE_SHA256 = "8628b234e1fc335b391b26a2dddf7b048b626f073b09a0cf6706f4e2d5ce60a5"

EXECUTION_MODE = "LOCAL_CLAUDE_SUBSCRIPTION"


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_text(s):
    return sha256_bytes(s.encode("utf-8"))


def write_fsync(path: Path, data: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())


def load_frozen():
    src = (CASE_DIR / "source-snapshot.txt").read_bytes()
    cb = (CASE_DIR / "commission-brief.json").read_bytes()
    ep = (CASE_DIR / "evidence-packet.json").read_bytes()
    actual = {"source": sha256_bytes(src), "commission": sha256_bytes(cb),
              "evidence": sha256_bytes(ep)}
    expected = {"source": EXPECTED_SOURCE_SHA256, "commission": EXPECTED_COMMISSION_SHA256,
                "evidence": EXPECTED_EVIDENCE_SHA256}
    for k in expected:
        if actual[k] != expected[k]:
            raise SystemExit(f"FROZEN INPUT MISMATCH for {k}: expected {expected[k]}, "
                             f"got {actual[k]}. Refusing to run.")
    source_text = src.decode("utf-8")
    evidence_packet = json.loads(ep)
    evidence_packet["source_text"] = source_text
    return json.loads(cb), evidence_packet, source_text, actual


def derive(cb, ep, source_text):
    from sofa_discovery_shadow_form1_3 import build_form1_3_packet, build_form1_3_writer_prompt
    packet = build_form1_3_packet(cb, ep)
    system, user = build_form1_3_writer_prompt(packet, source_text)
    packet_json = json.dumps(packet, indent=2, ensure_ascii=False)
    rendered = "=== SYSTEM ===\n" + system + "\n\n=== USER ===\n" + user
    return packet, packet_json, system, user, rendered


def do_preserve():
    cb, ep, source_text, input_hashes = load_frozen()
    packet, packet_json, system, user, rendered = derive(cb, ep, source_text)

    if source_text not in user:
        raise SystemExit("Rendered prompt does not embed the frozen source verbatim.")
    if sha256_text(source_text) != EXPECTED_SOURCE_SHA256:
        raise SystemExit("Embedded source hash mismatch.")
    # CHANGE 2 assertion: no global list-order authority may survive.
    for banned in ["in the order given", "in the order below", "in this order"]:
        if banned in system.lower():
            raise SystemExit(f"FORM-1.3 prompt still contains list-order authority: {banned!r}")

    write_fsync(OUT_DIR / "form1-3-packet.json", packet_json)
    write_fsync(OUT_DIR / "form1-3-writer-prompt.txt", rendered)
    write_fsync(OUT_DIR / "form1-3-source-snapshot.txt", source_text)
    write_fsync(OUT_DIR / "form1-3-writer-system.txt", system)
    write_fsync(OUT_DIR / "form1-3-writer-user.txt", user)

    meta = {
        "iteration": "FORM-1.3",
        "phase": "PRESERVED_PRE_GENERATION",
        "execution_mode": EXECUTION_MODE,
        "is_production_path_replay": False,
        "note": ("Manual architecture-development run. Writer identity does NOT match the "
                 "frozen Edinburgh lineage (openrouter/claude-opus-4.8 via CLIProxy); this "
                 "limits direct comparison with FORM-1/1.1/1.2."),
        "writer_generations_planned": 1,
        "retries": 0,
        "candidates": 1,
        "frozen_input_sha256": input_hashes,
        "packet_sha256": sha256_text(packet_json),
        "prompt_sha256": sha256_text(rendered),
        "system_prompt_sha256": sha256_text(system),
        "user_prompt_sha256": sha256_text(user),
        "source_embedded_in_prompt_verbatim": True,
        "module_sha256": sha256_bytes(
            (OUT_DIR / "sofa_discovery_shadow_form1_3.py").read_bytes()),
        "runner_sha256": sha256_bytes(Path(__file__).read_bytes()),
    }
    write_fsync(OUT_DIR / "form1-3-run-metadata.json",
                json.dumps(meta, indent=2, ensure_ascii=False))
    print(json.dumps({"ok": True, "phase": "preserved",
                      "packet_sha256": meta["packet_sha256"],
                      "prompt_sha256": meta["prompt_sha256"],
                      "source_sha256": input_hashes["source"],
                      "prompt_chars": len(rendered)}, indent=2))
    return 0


def do_record(article_path, model_identity):
    cb, ep, source_text, _ = load_frozen()
    packet, packet_json, system, user, rendered = derive(cb, ep, source_text)

    meta_path = OUT_DIR / "form1-3-run-metadata.json"
    if not meta_path.exists():
        raise SystemExit("No pre-generation preservation found. Run --preserve first.")
    meta = json.loads(meta_path.read_text())
    if sha256_text(rendered) != meta["prompt_sha256"]:
        raise SystemExit("Prompt drift vs preserved prompt.")
    if sha256_text(packet_json) != meta["packet_sha256"]:
        raise SystemExit("Packet drift vs preserved packet.")
    if sha256_text((OUT_DIR / "form1-3-writer-prompt.txt").read_text()) != meta["prompt_sha256"]:
        raise SystemExit("Preserved prompt file does not match its recorded hash.")
    if (OUT_DIR / "form1-3-article.md").exists():
        raise SystemExit("An article already exists. Refusing to re-record (one generation only).")

    raw = Path(article_path).read_text(encoding="utf-8")
    article = raw.strip()
    if not article:
        raise SystemExit("Empty generation.")

    write_fsync(OUT_DIR / "form1-3-raw-response.txt", raw)
    write_fsync(OUT_DIR / "form1-3-article.md", article)
    meta.update({
        "phase": "GENERATED",
        "model_identity_local": model_identity,
        "writer_generations_made": 1,
        "raw_response_sha256": sha256_text(raw),
        "article_sha256": sha256_text(article),
        "article_word_count": len(article.split()),
    })
    write_fsync(meta_path, json.dumps(meta, indent=2, ensure_ascii=False))
    print(json.dumps({"ok": True, "phase": "generated",
                      "execution_mode": EXECUTION_MODE,
                      "model_identity_local": model_identity,
                      "word_count": meta["article_word_count"],
                      "article_sha256": meta["article_sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "--preserve":
        sys.exit(do_preserve())
    elif mode == "--record":
        sys.exit(do_record(sys.argv[2], sys.argv[3]))
    raise SystemExit("usage: sofa_form1_3_run.py --preserve | --record <file> <model>")
