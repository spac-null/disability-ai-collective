#!/usr/bin/env python3
"""
validate_bundle.py -- deterministic capture validation for one production bundle.

Runs ONLY the checks the Phase-2 protocol allows at this stage. It does NOT run the
shadow architecture, does not call a model, and does not inspect article quality.

USAGE:
    python3 validate_bundle.py <bundle-dir> [--index P2-01]

Exit 0 = VALID (eligible, assign the next chronological index).
Exit 1 = CAPTURE_INVALID (record the reason, take the next chronological run).
"""
import argparse
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from compare import CaptureBundle, BundleError  # noqa: E402

CHECKS = [
    ("bundle complete", lambda b, r: not r["problems"]),
    ("atomic-completion marker present", lambda b, r: r["sealed"]),
    ("raw source persisted", lambda b, r: (b.root / "source/raw_cached_source.txt").exists()),
    ("normalized source persisted", lambda b, r: (b.root / "source/packet_source.txt").exists()),
    ("evidence packet persisted", lambda b, r: (b.root / "source/evidence_packet.json").exists()),
    ("writer-visible evidence persisted", lambda b, r: (b.root / "legacy/writer_prompt.txt").exists()),
    ("raw writer output persisted", lambda b, r: (b.root / "legacy/writer_output_raw.md").exists()),
    ("rewrite output available", lambda b, r: (b.root / "legacy/post_rewrite.md").exists()),
    ("disposition available", lambda b, r: (b.root / "legacy/disposition.json").exists()),
    ("hashes verify", lambda b, r: not any("hash mismatch" in p for p in r["problems"])),
    ("secrets scan clean", lambda b, r: not r["warnings"]),
]


def _sha_file(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def bundle_hash(root: pathlib.Path) -> str:
    """Stable hash over the whole bundle: every file path + content, sorted."""
    h = hashlib.sha256()
    for f in sorted(p for p in root.rglob("*") if p.is_file()):
        h.update(f.relative_to(root).as_posix().encode())
        h.update(f.read_bytes())
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bundle")
    ap.add_argument("--index", default=None, help="chronological sample index, e.g. P2-01")
    a = ap.parse_args()
    root = pathlib.Path(a.bundle)
    try:
        b = CaptureBundle(root)
    except BundleError as e:
        print(json.dumps({"bundle": str(root), "validity": "CAPTURE_INVALID",
                          "reason": str(e)}, indent=2))
        sys.exit(1)

    rep = b.validate()
    results = []
    for name, fn in CHECKS:
        try:
            ok = bool(fn(b, rep))
        except Exception as e:
            ok = False
            name = "%s (error: %s)" % (name, e)
        results.append({"check": name, "pass": ok})
        print("  %s  %s" % ("PASS" if ok else "FAIL", name))

    valid = all(r["pass"] for r in results)
    pkt, disp, prov = b.packet(), b.disposition(), b.provenance()
    row = {
        "sample_index": a.index,
        "bundle": str(root),
        "run_id": root.name,
        "validity": "VALID" if valid else "CAPTURE_INVALID",
        "failed_checks": [r["check"] for r in results if not r["pass"]],
        "problems": rep["problems"],
        "warnings": rep["warnings"],
        "source_url": prov.get("source_url"),
        "source_origin": pkt.get("source_origin"),
        "source_sha256": _sha_file(root / "source/packet_source.txt"),
        "declared_source_hash": pkt.get("source_hash"),
        "evidence_packet_hash": pkt.get("evidence_packet_hash"),
        "source_truncated": pkt.get("source_truncated"),
        "raw_writer_output_sha256": _sha_file(root / "legacy/writer_output_raw.md"),
        "rewrite_output_sha256": _sha_file(root / "legacy/post_rewrite.md"),
        "gate_fixed": disp.get("gate_fixed"),
        "degraded_stages": disp.get("degraded_stages"),
        "should_block": disp.get("should_block"),
        "review_clean": disp.get("review_clean"),
        "fact_check_status": disp.get("fact_check_status"),
        "legacy_disposition": disp.get("disposition"),
        "slug": disp.get("slug"),
        "capture_bundle_sha256": bundle_hash(root),
    }
    print()
    print(json.dumps(row, indent=2, sort_keys=True))
    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
