"""VERBATIM PORT of the frozen Phase-1 shadow_v0 module of the same name.

Source: .claude/experiments/production-migration-phase1-shadow-v0-2026-08-20/impl/shadow_v0/
on the research line (backup/research-main-2026-08-20). Copied rather than imported so this
production-candidate package has no dependency on an experiment directory, and copied
VERBATIM rather than adapted so NEW_ENGINE_V1 artifacts stay directly comparable with the
frozen shadow runs (same SCHEMA_VERSION, same hashes for the same payloads).

Do not "improve" this file. It is the frozen contract. If it must change, that is a
schema-version decision, not an edit.
"""
from __future__ import annotations

from . import contracts as C

ACCEPT = "ACCEPT"
HOLD = "HOLD"


def decide(artifacts: dict) -> tuple[str, list[str]]:
    """Returns (decision, reasons). Deterministic. Fail-closed: anything unproven HOLDs."""
    reasons = []

    # 1. Required artifact lineage complete.
    missing = [s for s in C.REQUIRED_STAGES if s != C.SHADOW_DECISION and s not in artifacts]
    if missing:
        return HOLD, ["lineage incomplete: missing %s" % ", ".join(missing)]

    # 2. Writer output exists and the provider did not fail.
    #    Provider failure HOLDs -- it does NOT fall back to a template article.
    wo = artifacts[C.WRITER_OUTPUT].payload
    if wo.get("provider_status") != "ok":
        return HOLD, ["writer provider failed (provider_status=%r); shadow policy is HOLD, "
                      "not legacy template fallback" % wo.get("provider_status")]
    if not wo.get("article_text", "").strip():
        return HOLD, ["writer output is empty"]
    reasons.append("writer output present, provider ok")

    # 3. Grounding status settled.
    gf = artifacts[C.GROUNDING_FINDINGS].payload
    if gf.get("status") != "settled":
        return HOLD, ["grounding status is %r, not settled" % gf.get("status")]
    reasons.append("grounding settled")

    # 4. No unresolved genuine unsupported finding.
    unsupported = [f for f in gf.get("findings", []) if f["classification"] == "TRUE_UNSUPPORTED"]
    repaired = set()
    if C.GROUNDING_REPAIR in artifacts:
        repaired = {p.get("finding_id") for p in artifacts[C.GROUNDING_REPAIR].payload.get("patches", [])}
    unresolved = [f for f in unsupported if f.get("id") not in repaired]
    if unresolved:
        return HOLD, ["%d unresolved TRUE_UNSUPPORTED finding(s): %s"
                      % (len(unresolved), ", ".join(f.get("id", "?") for f in unresolved))]
    if unsupported:
        reasons.append("%d TRUE_UNSUPPORTED finding(s), all repaired patch-only" % len(unsupported))
    else:
        reasons.append("no TRUE_UNSUPPORTED findings")

    # 5. TRUE_UNCERTAIN HOLDs for now. The preserved architecture does not establish
    #    that an uncertain finding is safe to accept, so V0 fails closed. Recorded as
    #    an open policy question in ACCEPT-HOLD.md.
    uncertain = [f for f in gf.get("findings", []) if f["classification"] == "TRUE_UNCERTAIN"]
    if uncertain and not gf.get("uncertain_adjudicated", False):
        return HOLD, ["%d TRUE_UNCERTAIN finding(s) not adjudicated; V0 policy is HOLD"
                      % len(uncertain)]
    if uncertain:
        reasons.append("%d TRUE_UNCERTAIN finding(s), explicitly adjudicated" % len(uncertain))

    # 6. Repair, if any, must have verified clean.
    if C.GROUNDING_REPAIR in artifacts:
        rp = artifacts[C.GROUNDING_REPAIR].payload
        v = rp.get("verification", {})
        # Every unsafe or unestablished repair state holds, including the two the old
        # arithmetic could not name. `reclassified` is a pre-existing claim the second
        # pass judged differently -- the repair did not cause it, and it blocks anyway,
        # because whether the claim is supported is a separate question from who wrote
        # it. `unresolved` is "we could not tell", which is never a pass.
        for key in ("repair_affected_unsupported", "reclassified_unsupported",
                    "unresolved_repair_identity", "unrelated_edits"):
            if v.get(key, 1) != 0:
                return HOLD, ["repair verification failed: %s=%r" % (key, v.get(key))]
        reasons.append("repair verified: 0 repair-affected, 0 reclassified, "
                       "0 unresolved, 0 unrelated edits")

    return ACCEPT, reasons
