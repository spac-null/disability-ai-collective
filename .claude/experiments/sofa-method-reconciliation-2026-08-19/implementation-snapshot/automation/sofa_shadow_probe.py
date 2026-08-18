#!/usr/bin/env python3
"""
sofa_shadow_probe.py — Sofa Architecture V1 Shadow Slice 1 / 1.1 / Real
Article Test 1 runner.

SHADOW ONLY. Not called by production_orchestrator.py, not on any cron
path, not wired to publish.py/social.py/gate.py. Reads and writes only
under a caller-specified output directory (created if absent).

WHAT THIS SCRIPT DOES:
  1. Loads a "case" — an existing, already-commissioned Fable Layer 1
     brief (source_decision == "commission") plus its source text.
  2. Runs the real orchestrator.sofa_discovery_shadow.run_shadow_discovery
     against it, producing a validated Discovery Packet.
  3. Projects that packet to a writer context (now including the full
     REFERENCE SOURCE — Real Article Test 1 correction 0C) and runs
     run_shadow_writer, producing a shadow article.
  4. Runs run_shadow_grounding_audit against the ARTICLE TEXT itself — a
     valid packet does not guarantee a grounded article — and computes
     discovery_packet_eligible_for_comparison (now returning the tri-state
     GROUNDED / REVIEWABLE_WITH_UNCERTAINTY / FAIL status) from both
     results.
  5. Writes the packet, writer context, article, grounding audit, and
     eligibility verdict to disk for manual inspection.

REAL ARTICLE TEST 1 CORRECTION (0D) — NO HARDCODED ONE-MODEL PROBE:
Slice 1/1.1's `_live_llm_call` hardcoded a single model
("openrouter/anthropic/claude-opus-4.8") for all three roles (Discovery,
Writer, Grounding Audit). This script now resolves THREE INDEPENDENT,
role-specific callers — `discovery_llm_call`, `writer_llm_call`,
`audit_llm_call` — each configured separately and never silently
substituted for another role. Live mode requires an explicit
--model-config JSON file (see `_DEFAULT_MODEL_CONFIG_DOC` below for the
exact shape) naming the URL/model/key-env for each of the three roles;
there is no built-in default model name in this script's own code,
because "the current production model" is a fact to look up in the real
production config at run time, never a guess baked into this file. The
resolved model identifiers actually used are always printed and returned
in the result dict so a caller can record them verbatim.

LLM WIRING — READ BEFORE RUNNING:

  --offline PATH        Loads a JSON fixture of {"discovery": <raw model
                         text>, "writer": <raw model text>, "audit": <raw
                         model text>} and uses those three strings AS IF
                         they were the three model responses (Discovery,
                         Writer, Grounding Audit, in that order). Used when
                         no live model credentials are configured — always
                         disclosed as agent-authored in the fixture's own
                         `_disclosure` field, never presented as real model
                         output.

  --model-config PATH   Required for a live run. A JSON file:
                         {"discovery": {"url":..., "key_env":...,
                         "model":...}, "writer": {...}, "audit": {...}}.
                         Each role calls its own configured endpoint/model.
                         Fails closed (raises) if a required role config
                         is missing, or if the named key_env is unset in
                         the environment — never silently falls back to a
                         different model or a stub.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from orchestrator.grounding import build_evidence_packet  # noqa: E402
from orchestrator.sofa_discovery_shadow import (  # noqa: E402
    SofaShadowError,
    run_shadow_discovery,
    run_shadow_writer,
    run_shadow_grounding_audit,
    grounding_audit_status,
    discovery_packet_eligible_for_comparison,
    to_writer_context,
    validate_discovery_packet,
)

_DEFAULT_MODEL_CONFIG_DOC = """
Expected --model-config JSON shape (no defaults are hardcoded in this script):
{
  "discovery": {"url": "http://127.0.0.1:8317/v1", "key_env": "CLIPROXY_KEY", "model": "openrouter/claude-fable-5"},
  "writer":    {"url": "http://127.0.0.1:8317/v1", "key_env": "CLIPROXY_KEY", "model": "openrouter/claude-opus-4.8"},
  "audit":     {"url": "http://127.0.0.1:8317/v1", "key_env": "CLIPROXY_KEY", "model": "openrouter/claude-fable-5"}
}
Resolve the exact model/url values from the REAL production config/code
(automation/orchestrator/config.py's CLIPROXY_URL, and the PROVIDERS list
inside call_llm_via_openclaw_session / the model names inside
_call_editorial_model, in automation/orchestrator/llm.py) — never guess.
"""


def _make_live_llm_call(role_name: str, role_config: dict, max_tokens: int = 4000, timeout: int = 180):
    """Builds one role-specific live caller. Fails closed immediately (at
    call time, not lazily hidden) if the role's key_env is unset — this
    function never falls back to a different model or a stub."""
    url = role_config.get("url")
    model = role_config.get("model")
    key_env = role_config.get("key_env")
    if not (url and model and key_env):
        raise SofaShadowError(
            f"--model-config entry for role {role_name!r} is incomplete "
            f"(needs url, model, key_env): {role_config!r}"
        )
    api_key = os.environ.get(key_env, "")
    if not api_key:
        raise SofaShadowError(
            f"role {role_name!r} is configured to use model {model!r} via env var {key_env!r}, "
            "but that environment variable is unset — refusing to make a live call for this role. "
            "Use --offline <fixture.json> instead, or export the required key."
        )

    def _call(system_prompt: str, user_prompt: str) -> str:
        import urllib.request
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens,
            "stream": False,
        }
        req = urllib.request.Request(
            url.rstrip("/") + "/chat/completions",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode())
        return payload["choices"][0]["message"]["content"]

    return _call, model


def _offline_llm_calls(fixture_path: Path):
    """Returns (discovery_call, writer_call, audit_call, resolved_models)
    from a single disclosed fixture file — each role gets its own fixed
    string, so this is NOT the same as Slice 1/1.1's positional
    call-counter (that approach breaks once each role can be called a
    different number of times, e.g. under a retry)."""
    fixture = json.loads(fixture_path.read_text())
    resolved = {
        "discovery": "OFFLINE_FIXTURE (agent-authored, not a live model)",
        "writer": "OFFLINE_FIXTURE (agent-authored, not a live model)",
        "audit": "OFFLINE_FIXTURE (agent-authored, not a live model)",
    }
    return (
        lambda system, user: fixture["discovery"],
        lambda system, user: fixture["writer"],
        lambda system, user: fixture["audit"],
        resolved,
    )


def run(case_path: Path, out_dir: Path, discovery_llm_call, writer_llm_call, audit_llm_call,
        resolved_models: dict) -> dict:
    case = json.loads(case_path.read_text())
    commission_brief = case["commission_brief"]
    source_text = case["source_text"]
    evidence_packet = build_evidence_packet(
        source_text,
        source_origin=case.get("source_origin", "fixture"),
    )

    packet = run_shadow_discovery(commission_brief, evidence_packet, discovery_llm_call,
                                   discovery_lens=case.get("discovery_lens"))
    ok, errors = validate_discovery_packet(packet)
    if not ok:
        raise SofaShadowError("generated packet failed validation: " + "; ".join(errors))

    writer_context = to_writer_context(packet, source_text)
    article_text = run_shadow_writer(writer_context, writer_llm_call)

    # A grounded packet does not guarantee a grounded article — audit the
    # ARTICLE TEXT itself before this case can be treated as eligible for
    # any Sofa quality comparison.
    audit = run_shadow_grounding_audit(source_text, packet, article_text, audit_llm_call)
    audit_status, audit_reasons = grounding_audit_status(audit)
    eligible, eligibility_status, eligibility_reasons = discovery_packet_eligible_for_comparison(packet, audit)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "discovery_packet.json").write_text(json.dumps(packet, indent=2))
    (out_dir / "writer_context.json").write_text(json.dumps(writer_context, indent=2))
    (out_dir / "shadow_article.md").write_text(article_text)
    (out_dir / "grounding_audit.json").write_text(json.dumps(audit, indent=2))
    (out_dir / "eligibility.json").write_text(json.dumps({
        "packet_valid": ok,
        "grounding_status": audit_status,
        "grounding_reasons": audit_reasons,
        "eligible_for_comparison": eligible,
        "eligibility_status": eligibility_status,
        "eligibility_reasons": eligibility_reasons,
        "resolved_models": resolved_models,
    }, indent=2))

    return {
        "packet_path": str(out_dir / "discovery_packet.json"),
        "writer_context_path": str(out_dir / "writer_context.json"),
        "article_path": str(out_dir / "shadow_article.md"),
        "audit_path": str(out_dir / "grounding_audit.json"),
        "eligibility_path": str(out_dir / "eligibility.json"),
        "grounding_status": audit_status,
        "eligible_for_comparison": eligible,
        "resolved_models": resolved_models,
    }


def main():
    parser = argparse.ArgumentParser(description="Sofa Architecture V1 Shadow runner (shadow only).")
    parser.add_argument("--case", required=True, type=Path)
    parser.add_argument("--offline", type=Path, default=None,
                         help="Path to a {discovery, writer, audit} JSON fixture; skips any live model call.")
    parser.add_argument("--model-config", type=Path, default=None,
                         help="Required for a live run. " + _DEFAULT_MODEL_CONFIG_DOC)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    if args.offline:
        discovery_call, writer_call, audit_call, resolved = _offline_llm_calls(args.offline)
    else:
        if not args.model_config:
            raise SofaShadowError(
                "Live mode requires --model-config (no hardcoded default model). " + _DEFAULT_MODEL_CONFIG_DOC
            )
        cfg = json.loads(args.model_config.read_text())
        for role in ("discovery", "writer", "audit"):
            if role not in cfg:
                raise SofaShadowError(f"--model-config is missing the {role!r} role. " + _DEFAULT_MODEL_CONFIG_DOC)
        discovery_call, discovery_model = _make_live_llm_call("discovery", cfg["discovery"])
        writer_call, writer_model = _make_live_llm_call("writer", cfg["writer"])
        audit_call, audit_model = _make_live_llm_call("audit", cfg["audit"])
        resolved = {"discovery": discovery_model, "writer": writer_model, "audit": audit_model}

    result = run(args.case, args.out, discovery_call, writer_call, audit_call, resolved)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
