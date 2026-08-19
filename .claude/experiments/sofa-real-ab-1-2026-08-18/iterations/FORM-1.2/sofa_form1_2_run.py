#!/usr/bin/env python3
"""
sofa_form1_2_run.py — TEMP-WORKTREE-ONLY. Generates ONE Sofa FORM-1.2
article from the frozen Edinburgh commission.

Same writer model/params as all prior Edinburgh runs:
openrouter/claude-opus-4.8 via CLIProxy, max_tokens=5000, timeout=180,
no_think=False, no temperature override. No new Fable call, no Discovery
model call. Exactly one writer call. No retries, no candidates.

Two phases, so that the persisted prompt is provably the executed prompt:

  --preserve : verify frozen source by SHA-256, build the packet, render
               the writer prompt, write packet + prompt + metadata + all
               hashes to disk, fsync. NO MODEL CALL.
  --execute  : re-derive the packet and prompt, assert they hash-match the
               already-persisted artifacts, then make the single writer
               call and persist the raw response and article.
"""
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT_REAL = Path("/tmp/cripminds-sofa-real-test-1")
sys.path.insert(0, str(REPO_ROOT_REAL / "automation"))

CASE_DIR = REPO_ROOT_REAL / ".claude/experiments/sofa-real-ab-1-2026-08-18"
OUT_DIR = REPO_ROOT_REAL / ".claude/experiments/sofa-form1-2-2026-08-19"

WRITER_MODEL = "openrouter/claude-opus-4.8"
WRITER_MAX_TOKENS = 5000
WRITER_TIMEOUT = 180

# Frozen Guardian source, verified identical on the Mac preservation copy
# and in this worktree before FORM-1.2 was built.
EXPECTED_SOURCE_SHA256 = "fee0a03b8bb0c56b88b0806a9120576c87f0983764d8620c77c56b59531d4753"
EXPECTED_COMMISSION_SHA256 = "870d84ba931abf194db5fad8017185cbf2f034ec08e383d1d89fcb8b3fce3387"
EXPECTED_EVIDENCE_SHA256 = "8628b234e1fc335b391b26a2dddf7b048b626f073b09a0cf6706f4e2d5ce60a5"


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
    """Deterministically verify the frozen inputs BEFORE anything else.
    Guards against a contaminated capture being fed to the writer."""
    src_path = CASE_DIR / "source-snapshot.txt"
    cb_path = CASE_DIR / "commission-brief.json"
    ep_path = CASE_DIR / "evidence-packet.json"

    src_bytes = src_path.read_bytes()
    cb_bytes = cb_path.read_bytes()
    ep_bytes = ep_path.read_bytes()

    actual = {
        "source": sha256_bytes(src_bytes),
        "commission": sha256_bytes(cb_bytes),
        "evidence": sha256_bytes(ep_bytes),
    }
    expected = {
        "source": EXPECTED_SOURCE_SHA256,
        "commission": EXPECTED_COMMISSION_SHA256,
        "evidence": EXPECTED_EVIDENCE_SHA256,
    }
    for k in expected:
        if actual[k] != expected[k]:
            raise SystemExit(
                f"FROZEN INPUT MISMATCH for {k}: expected {expected[k]}, got {actual[k]}. "
                f"Refusing to run -- this is not the intended frozen Guardian material."
            )

    source_text = src_bytes.decode("utf-8")
    commission_brief = json.loads(cb_bytes)
    evidence_packet = json.loads(ep_bytes)
    evidence_packet["source_text"] = source_text
    return commission_brief, evidence_packet, source_text, actual


def derive(commission_brief, evidence_packet, source_text):
    from orchestrator.sofa_discovery_shadow_form1_2 import (
        build_form1_2_packet, build_form1_2_writer_prompt,
    )
    packet = build_form1_2_packet(commission_brief, evidence_packet)
    system, user = build_form1_2_writer_prompt(packet, source_text)
    packet_json = json.dumps(packet, indent=2, ensure_ascii=False)
    rendered = (
        "=== SYSTEM ===\n" + system + "\n\n=== USER ===\n" + user
    )
    return packet, packet_json, system, user, rendered


def do_preserve():
    commission_brief, evidence_packet, source_text, input_hashes = load_frozen()
    packet, packet_json, system, user, rendered = derive(
        commission_brief, evidence_packet, source_text)

    # Deterministic proof that the source handed to the writer is the
    # frozen source, byte for byte, not a terminal re-capture.
    if source_text not in user:
        raise SystemExit("Rendered prompt does not embed the frozen source verbatim.")
    embedded_sha = sha256_text(source_text)
    if embedded_sha != EXPECTED_SOURCE_SHA256:
        raise SystemExit("Embedded source hash mismatch.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_fsync(OUT_DIR / "form1-2-packet.json", packet_json)
    write_fsync(OUT_DIR / "form1-2-writer-prompt.txt", rendered)
    write_fsync(OUT_DIR / "form1-2-source-snapshot.txt", source_text)

    meta = {
        "iteration": "FORM-1.2",
        "phase": "PRESERVED_PRE_EXECUTION",
        "model_requested": WRITER_MODEL,
        "parameters": {
            "max_tokens": WRITER_MAX_TOKENS,
            "timeout": WRITER_TIMEOUT,
            "no_think": False,
            "temperature_override": None,
        },
        "writer_calls_planned": 1,
        "retries": 0,
        "candidates": 1,
        "frozen_input_sha256": input_hashes,
        "expected_frozen_input_sha256": {
            "source": EXPECTED_SOURCE_SHA256,
            "commission": EXPECTED_COMMISSION_SHA256,
            "evidence": EXPECTED_EVIDENCE_SHA256,
        },
        "frozen_inputs_verified": True,
        "packet_sha256": sha256_text(packet_json),
        "prompt_sha256": sha256_text(rendered),
        "system_prompt_sha256": sha256_text(system),
        "user_prompt_sha256": sha256_text(user),
        "source_embedded_in_prompt_verbatim": True,
        "module_sha256": sha256_bytes(
            (REPO_ROOT_REAL / "automation/orchestrator/sofa_discovery_shadow_form1_2.py").read_bytes()
        ),
        "runner_sha256": sha256_bytes(Path(__file__).read_bytes()),
    }
    write_fsync(OUT_DIR / "form1-2-run-metadata.json",
                json.dumps(meta, indent=2, ensure_ascii=False))
    print(json.dumps({
        "ok": True, "phase": "preserved",
        "packet_sha256": meta["packet_sha256"],
        "prompt_sha256": meta["prompt_sha256"],
        "source_sha256": input_hashes["source"],
        "prompt_chars": len(rendered),
    }, indent=2))
    return 0


def do_execute():
    commission_brief, evidence_packet, source_text, input_hashes = load_frozen()
    packet, packet_json, system, user, rendered = derive(
        commission_brief, evidence_packet, source_text)

    meta_path = OUT_DIR / "form1-2-run-metadata.json"
    if not meta_path.exists():
        raise SystemExit("No pre-execution preservation found. Run --preserve first.")
    meta = json.loads(meta_path.read_text())

    # The persisted prompt MUST be the executed prompt.
    if sha256_text(rendered) != meta["prompt_sha256"]:
        raise SystemExit(
            f"Prompt drift: re-derived {sha256_text(rendered)} != preserved {meta['prompt_sha256']}"
        )
    if sha256_text(packet_json) != meta["packet_sha256"]:
        raise SystemExit("Packet drift vs preserved packet.")
    on_disk = (OUT_DIR / "form1-2-writer-prompt.txt").read_text()
    if sha256_text(on_disk) != meta["prompt_sha256"]:
        raise SystemExit("Preserved prompt file does not match its recorded hash.")
    if (OUT_DIR / "form1-2-article.md").exists():
        raise SystemExit("An article already exists. Refusing to re-run (one writer call only).")

    from production_orchestrator import ProductionOrchestrator
    from orchestrator.config import CLIPROXY_URL, CLIPROXY_KEY

    with tempfile.TemporaryDirectory() as tmp:
        orch = ProductionOrchestrator()
        orch.repo_root = Path(tmp)
        orch.posts_dir = orch.repo_root / "_posts"
        orch.drafts_dir = orch.repo_root / "_drafts"
        orch.assets_dir = orch.repo_root / "assets"
        orch.discovery_db = orch.repo_root / "disability_findings.db"
        orch.posts_dir.mkdir(parents=True, exist_ok=True)
        orch.drafts_dir.mkdir(parents=True, exist_ok=True)
        orch.assets_dir.mkdir(parents=True, exist_ok=True)

        text, actual_model = orch._call_openai_compat_api(
            CLIPROXY_URL, CLIPROXY_KEY, system, user,
            model=WRITER_MODEL, max_tokens=WRITER_MAX_TOKENS, timeout=WRITER_TIMEOUT,
            no_think=False, return_model=True,
        )

    if not text or not text.strip():
        raise SystemExit("Writer returned no usable text. Not retrying (one call only).")

    raw = text
    article = text.strip()
    write_fsync(OUT_DIR / "form1-2-raw-response.txt", raw)
    write_fsync(OUT_DIR / "form1-2-article.md", article)

    meta.update({
        "phase": "EXECUTED",
        "model_actual": actual_model,
        "writer_calls_made": 1,
        "raw_response_sha256": sha256_text(raw),
        "article_sha256": sha256_text(article),
        "article_word_count": len(article.split()),
    })
    write_fsync(meta_path, json.dumps(meta, indent=2, ensure_ascii=False))
    print(json.dumps({
        "ok": True, "phase": "executed",
        "model_requested": WRITER_MODEL, "model_actual": actual_model,
        "word_count": meta["article_word_count"],
        "article_sha256": meta["article_sha256"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        if mode == "--preserve":
            sys.exit(do_preserve())
        elif mode == "--execute":
            sys.exit(do_execute())
        else:
            raise SystemExit("usage: sofa_form1_2_run.py --preserve | --execute")
    except SystemExit:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(json.dumps({"ok": False, "reason": f"{type(e).__name__}: {e}"}))
        sys.exit(1)
