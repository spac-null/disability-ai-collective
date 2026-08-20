#!/usr/bin/env python3
"""
compare.py -- deterministic live-vs-shadow comparison harness.

Ingests ONE captured production bundle (written by automation/shadow_capture.py) and
compares the LEGACY PRODUCTION lineage against a PHASE-1 CLEAN SHADOW lineage built from
the SAME frozen evidence.

No model call. No LLM judge. No prose-quality scoring. This harness reports what differs
and what can be attributed; it does not decide which article is better.

The shadow side is optional: with no shadow lineage supplied the harness still validates
the bundle and reports the legacy outcome, so it can be run the moment capture lands and
before any shadow execution exists.
"""
from __future__ import annotations

import hashlib
import json
import pathlib

SCHEMA = "compare-v1"


class BundleError(Exception):
    """Raised when a capture bundle cannot support a sound comparison."""


def _sha(t):
    if t is None:
        return None
    return hashlib.sha256(t.encode("utf-8") if isinstance(t, str) else t).hexdigest()


def _read(p):
    return p.read_text(encoding="utf-8") if p.exists() else None


class CaptureBundle:
    """One production run, as captured. Fail-closed on incompleteness."""

    REQUIRED = ["source/packet_source.txt", "source/evidence_packet.json",
                "legacy/writer_output_raw.md"]

    def __init__(self, root: pathlib.Path):
        self.root = pathlib.Path(root)
        if not self.root.is_dir():
            raise BundleError("bundle root does not exist: %s" % self.root)
        self.manifest = self._load_manifest()
        self.sealed = (self.root / "COMPLETE").exists()

    def _load_manifest(self):
        p = self.root / "manifest.jsonl"
        if not p.exists():
            raise BundleError("no manifest.jsonl -- not a capture bundle")
        out = []
        for i, line in enumerate(p.read_text().splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise BundleError("manifest line %d is not valid JSON: %s" % (i, e))
        return out

    def validate(self) -> dict:
        """Structural + integrity validation. Returns a report; raises on fatal problems."""
        problems, warnings = [], []
        if not self.sealed:
            problems.append("bundle is not sealed (no COMPLETE marker) -> CAPTURE_INVALID")
        for rel in self.REQUIRED:
            if not (self.root / rel).exists():
                problems.append("missing required artifact: %s" % rel)
        # every hash the manifest recorded must still match the file on disk
        mismatches = []
        for ev in self.manifest:
            for rel, rec in (ev.get("entries") or {}).items():
                if not isinstance(rec, dict) or "sha256" not in rec:
                    continue
                actual = _sha(_read(self.root / rel))
                if actual is None:
                    problems.append("manifest references a missing file: %s" % rel)
                elif actual != rec["sha256"]:
                    mismatches.append(rel)
        if mismatches:
            problems.append("hash mismatch on: %s" % ", ".join(sorted(set(mismatches))))
        refused = [rel for ev in self.manifest for rel, rec in (ev.get("entries") or {}).items()
                   if isinstance(rec, dict) and rec.get("status") == "REFUSED_POSSIBLE_SECRET"]
        if refused:
            warnings.append("capture refused %d artifact(s) as possibly secret-bearing: %s"
                            % (len(refused), ", ".join(refused)))
        status = "CAPTURE_INVALID" if problems else "VALID"
        return {"status": status, "problems": problems, "warnings": warnings,
                "sealed": self.sealed, "events": [e["event"] for e in self.manifest]}

    # ---- accessors
    def packet(self):
        raw = _read(self.root / "source/evidence_packet.json")
        return json.loads(raw) if raw else {}

    def provenance(self):
        raw = _read(self.root / "source/provenance.json")
        return json.loads(raw) if raw else {}

    def disposition(self):
        raw = _read(self.root / "legacy/disposition.json")
        return json.loads(raw) if raw else {}

    def brief(self):
        raw = _read(self.root / "legacy/fable_brief.json")
        return json.loads(raw) if raw else {}

    def raw_source(self):
        return _read(self.root / "source/raw_cached_source.txt")

    def packet_source(self):
        return _read(self.root / "source/packet_source.txt")

    def writer_prompt(self):
        return _read(self.root / "legacy/writer_prompt.txt")

    def writer_raw(self):
        return _read(self.root / "legacy/writer_output_raw.md")

    def post_rewrite(self):
        return _read(self.root / "legacy/post_rewrite.md")


# ------------------------------------------------------------------ dimensions
def source_equivalence(bundle: CaptureBundle, shadow_source_text=None) -> dict:
    """Hash proof that legacy and shadow consumed the same evidence."""
    pkt = bundle.packet()
    legacy_text = bundle.packet_source()
    d = {
        "legacy_packet_source_sha256": _sha(legacy_text),
        "legacy_packet_declared_source_hash": pkt.get("source_hash"),
        "legacy_evidence_packet_hash": pkt.get("evidence_packet_hash"),
        "legacy_source_origin": pkt.get("source_origin"),
        "legacy_source_truncated": pkt.get("source_truncated"),
        "legacy_source_length_chars": pkt.get("source_length_chars"),
        "raw_cached_vs_packet_source_identical": bundle.raw_source() == legacy_text,
    }
    if shadow_source_text is None:
        d["verdict"] = "NO_SHADOW_SOURCE_SUPPLIED"
        return d
    d["shadow_source_sha256"] = _sha(shadow_source_text)
    d["verdict"] = "EQUIVALENT" if _sha(shadow_source_text) == _sha(legacy_text) else "SOURCE_MISMATCH"
    return d


def legacy_outcome(bundle: CaptureBundle) -> dict:
    raw, post = bundle.writer_raw(), bundle.post_rewrite()
    disp = bundle.disposition()
    out = {
        "writer_raw_sha256": _sha(raw),
        "writer_raw_words": len(raw.split()) if raw else None,
        "post_rewrite_sha256": _sha(post),
        "post_rewrite_words": len(post.split()) if post else None,
        "rewrite_ran": post is not None,
        "rewrite_changed_content": (raw is not None and post is not None and raw not in post and raw != post),
        "gate_fixed": disp.get("gate_fixed"),
        "degraded_stages": disp.get("degraded_stages"),
        "should_block": disp.get("should_block"),
        "review_clean": disp.get("review_clean"),
        "fact_check_status": disp.get("fact_check_status"),
        "disposition": disp.get("disposition"),
        "slug": disp.get("slug"),
    }
    if raw and post:
        out["word_delta_rewrite"] = out["post_rewrite_words"] - out["writer_raw_words"]
    return out


def shadow_outcome(shadow_manifest: dict | None) -> dict:
    """Reads a Phase-1 shadow run MANIFEST.json. None until a shadow run exists."""
    if not shadow_manifest:
        return {"verdict": "NO_SHADOW_RUN_SUPPLIED"}
    return {
        "stage_hashes": shadow_manifest.get("stage_hashes"),
        "decision": shadow_manifest.get("decision"),
        "source_sha256": shadow_manifest.get("source_sha256"),
        "schema_version": shadow_manifest.get("schema_version"),
    }


def grounding_comparison(bundle: CaptureBundle, shadow_findings=None) -> dict:
    """Legacy has no source-relative grounding audit; it has fact_check (world-relative)
    plus the grounding_* fields on the persisted brief. Those are DIFFERENT measurements
    and are reported separately rather than merged."""
    b = bundle.brief()
    d = {
        "legacy_measurable": bool(b),
        "legacy_grounding_status": b.get("grounding_status"),
        "legacy_grounding_violations": b.get("grounding_violations"),
        "legacy_fact_check_status": bundle.disposition().get("fact_check_status"),
        "note": "legacy grounding_status is BRIEF-field validation (planner evidence "
                "candidates); fact_check is world-relative. Neither is a source-relative "
                "audit of the finished article, which is what shadow Writer Grounding does. "
                "These are not the same measurement and are not merged.",
    }
    if shadow_findings is None:
        d["shadow"] = "NO_SHADOW_FINDINGS_SUPPLIED"
    else:
        d["shadow_findings_by_class"] = {
            c: sum(1 for f in shadow_findings if f.get("classification") == c)
            for c in ("TRUE_UNSUPPORTED", "TRUE_UNCERTAIN", "LEGITIMATE_INTERPRETATION")}
    return d


def structure_comparison(bundle: CaptureBundle, shadow_article=None) -> dict:
    """Structural only. Deliberately NOT prose similarity and NOT a quality judgement."""
    def prof(text):
        if not text:
            return None
        paras = [p for p in text.split("\n\n") if p.strip()]
        return {"words": len(text.split()), "paragraphs": len(paras),
                "section_breaks": text.count("\n---\n"),
                "mean_para_words": round(sum(len(p.split()) for p in paras) / len(paras), 1) if paras else 0}
    return {"legacy_writer_raw": prof(bundle.writer_raw()),
            "legacy_post_rewrite": prof(bundle.post_rewrite()),
            "shadow_article": prof(shadow_article) if shadow_article else "NO_SHADOW_ARTICLE_SUPPLIED"}


def legacy_rule_effects(bundle: CaptureBundle) -> dict:
    """Material changes attributable to legacy stages, ONLY where the evidence supports
    attribution. Attribution is by construction: raw writer output vs post-rewrite output
    isolates the rewrite stage exactly, because nothing else runs between them."""
    raw, post = bundle.writer_raw(), bundle.post_rewrite()
    prompt = bundle.writer_prompt()
    eff = {"rewrite_attributable": None, "persona_injection_present": None,
           "rule_judge_effects": "NOT_ATTRIBUTABLE_FROM_THIS_BUNDLE"}
    if raw is not None and post is not None:
        eff["rewrite_attributable"] = {
            "changed": raw != post,
            "raw_words": len(raw.split()), "post_words": len(post.split()),
            "basis": "raw writer output vs post-rewrite output; nothing else executes between "
                     "these two captures, so any difference is the rewrite stage",
        }
    if prompt:
        markers = ["YOU ARE ", "WRITE LIKE THIS PERSON", "YOUR WOUND",
                   "AUTHORIZED PERSONAL HISTORY", "YOUR CANON"]
        eff["persona_injection_present"] = {m: (m in prompt) for m in markers}
        eff["writer_prompt_chars"] = len(prompt)
    eff["note"] = ("gate/review rule-judge effects are not attributable here: the gate can "
                   "rewrite content in place and the capture records only its result, not a "
                   "pre/post pair. Recorded as a known limitation, not inferred.")
    return eff


def compare(bundle_root, shadow_run_root=None) -> dict:
    b = CaptureBundle(pathlib.Path(bundle_root))
    validation = b.validate()
    report = {"schema": SCHEMA, "bundle": str(bundle_root), "validation": validation}
    if validation["status"] == "CAPTURE_INVALID":
        report["verdict"] = "CAPTURE_INVALID"
        report["next_action"] = "take the next chronological complete run"
        return report

    shadow_manifest = shadow_source = shadow_article = shadow_findings = None
    if shadow_run_root:
        sr = pathlib.Path(shadow_run_root)
        mp = sr / "MANIFEST.json"
        if mp.exists():
            shadow_manifest = json.loads(mp.read_text())
        shadow_source = _read(sr / "source-snapshot.txt")
        wo = sr / "WRITER_OUTPUT.json"
        if wo.exists():
            shadow_article = json.loads(wo.read_text())["payload"].get("article_text")
        gf = sr / "GROUNDING_FINDINGS.json"
        if gf.exists():
            shadow_findings = json.loads(gf.read_text())["payload"].get("findings")

    report["source_equivalence"] = source_equivalence(b, shadow_source)
    report["legacy_outcome"] = legacy_outcome(b)
    report["shadow_outcome"] = shadow_outcome(shadow_manifest)
    report["grounding"] = grounding_comparison(b, shadow_findings)
    report["structure"] = structure_comparison(b, shadow_article)
    report["legacy_rule_effects"] = legacy_rule_effects(b)

    se = report["source_equivalence"]["verdict"]
    if se == "SOURCE_MISMATCH":
        report["verdict"] = "REJECTED_SOURCE_MISMATCH"
        report["reason"] = ("legacy and shadow did not consume identical evidence; no "
                            "comparison of outcomes is sound")
    elif se == "NO_SHADOW_SOURCE_SUPPLIED":
        report["verdict"] = "LEGACY_ONLY"
        report["reason"] = "bundle valid; awaiting a shadow lineage on the same frozen evidence"
    else:
        report["verdict"] = "COMPARABLE"
        legacy_blocked = bool(report["legacy_outcome"].get("should_block"))
        report["outcome_pair"] = {
            "legacy": "BLOCKED" if legacy_blocked else "DRAFT",
            "shadow": report["shadow_outcome"].get("decision"),
            "note": "a blocked legacy run is valid comparison data; neither system is assumed "
                    "correct merely because it blocked. The pairing is observed, not scored.",
        }
    return report


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("bundle")
    ap.add_argument("--shadow-run", default=None)
    a = ap.parse_args()
    print(json.dumps(compare(a.bundle, a.shadow_run), indent=2, sort_keys=True))
