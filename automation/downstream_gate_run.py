#!/usr/bin/env python3
"""Run Grounding → Reader against an existing article whose run stopped at Safety.

Designed for the Oct 24 Haneda article (production-20261024T070253Z-93923695)
and any future free_argumentative or story_architecture run that held only at
Safety and never reached Grounding.

Usage on Trident:

  python3 automation/downstream_gate_run.py \
      --run-dir /srv/data/cripminds-new-engine-v1/production-20261024T070253Z-93923695

Reads from the run directory:
  ARTICLE_FINAL.md          article text
  LEDGER.json               frozen ledger
  NEGATIVE_LINEAGE.json     negative lineage (may be {})
  RESEARCH_PACK.json        full research pack (for grounding source texts)
  SOURCE_SNAPSHOT.json      source_text + sha256  [preferred over deriving from pack]
  WRITER_PACKET.json        writer packet         [needed for grounding repair validator]

Writes DOWNSTREAM_GATE_RESULT.json into the run directory (or --out path).
Exits 0 on publication-ready, non-zero otherwise.
"""

import argparse
import hashlib
import json
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from new_engine_v1 import composition as CP  # noqa: E402
from claude_cli_provider import ClaudeCLIProvider  # noqa: E402


# ── helpers ───────────────────────────────────────────────────────────────────

def _load_json(p: pathlib.Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _source_text_from_pack(pack: dict) -> tuple[str, str]:
    """Derive source_text + sha256 from RESEARCH_PACK when SOURCE_SNAPSHOT absent."""
    parts = []
    for s in (pack.get("sources") or []):
        sid = s.get("source_id", "")
        text = (s.get("text") or "")[:CP.FREEZE_SOURCE_CHARS]
        parts.append("<<<%s\n%s\n%s>>>" % (sid, text, sid))
    src = "\n\n".join(parts)
    return src, _sha256(src)


def _load_writer_packet(run_dir: pathlib.Path) -> dict:
    candidates = ["WRITER_PACKET.json", "attempt-A/WRITER_PACKET.json"]
    for name in candidates:
        p = run_dir / name
        if p.exists():
            return _load_json(p)
    return {}


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Run Grounding + Reader on a held article's existing ARTICLE_FINAL")
    ap.add_argument("--run-dir", required=True,
                    help="Evidence root directory for the held run")
    ap.add_argument("--out", default=None,
                    help="Path to write the JSON result (default: DOWNSTREAM_GATE_RESULT.json "
                         "inside --run-dir)")
    ap.add_argument("--skip-grounding-repair", action="store_true",
                    help="Report grounding blockers and stop; do not attempt completion loop")
    args = ap.parse_args()

    run_dir = pathlib.Path(args.run_dir)
    if not run_dir.is_dir():
        print("ERROR: run-dir not found:", run_dir, file=sys.stderr)
        return 1

    # ── load ──────────────────────────────────────────────────────────────────
    article_text = (run_dir / "ARTICLE_FINAL.md").read_text(encoding="utf-8")
    ledger = _load_json(run_dir / "LEDGER.json")
    negative_lineage = (_load_json(run_dir / "NEGATIVE_LINEAGE.json")
                        if (run_dir / "NEGATIVE_LINEAGE.json").exists() else {})

    pack = _load_json(run_dir / "RESEARCH_PACK.json")
    writer_packet = _load_writer_packet(run_dir)

    if (run_dir / "SOURCE_SNAPSHOT.json").exists():
        snap = _load_json(run_dir / "SOURCE_SNAPSHOT.json")
        # Artifact schema wraps payload; fall back to flat shape for older files
        snap_data = snap.get("payload") or snap
        source_text = snap_data["source_text"]
        source_sha = snap_data.get("source_sha256") or _sha256(source_text)
    else:
        print("SOURCE_SNAPSHOT.json absent — deriving source text from RESEARCH_PACK")
        source_text, source_sha = _source_text_from_pack(pack)

    print("Article : %d words" % len(article_text.split()))
    print("Ledger  : %d facts" % len(ledger))
    print("Pack    : %d sources" % len(pack.get("sources") or []))
    print("Source  : %d chars  sha=%s…" % (len(source_text), source_sha[:12]))
    if writer_packet:
        print("Packet  : loaded (%d beats)" % len(
            writer_packet.get("beats") or []))
    else:
        print("Packet  : absent (grounding repair validator will be looser)")
    print()

    provider = ClaudeCLIProvider()

    # Build the same audit closure the free path uses: whole-ledger licensing,
    # actual safety_audit call.  Used inside grounding_completion_loop to guard
    # that no repair introduces a new Safety finding.
    srcs = CP.source_texts(pack)
    licensing = CP.check_ledger(ledger, srcs)

    def audit_fn(text, pkg_=None, **kw):
        r = CP.safety_audit(text, text, licensing, {}, ledger, {}, None,
                            negative_lineage, package=pkg_, **kw)
        r["audited_text_sha256"] = _sha256(text or "")
        return r

    # ── GROUNDING ─────────────────────────────────────────────────────────────
    print("=== GROUNDING ===")
    try:
        g = CP.ground_candidate(provider, article_text, source_text, source_sha, pack)
    except CP.CompositionHold as e:
        print("HOLD (provider error):", e)
        return 2

    print("Status   :", g.get("status"))
    blockers = g.get("blocking") or []
    fatal = g.get("fatal") or []
    print("Findings :", len(g.get("findings") or []))
    print("Blocking :", len(blockers), " fatal:", len(fatal))
    for f in fatal[:5]:
        print("  [%s] %s" % (f.get("classification"), (f.get("quote") or "")[:120]))

    grounding_passed = g.get("status") == CP.PASS
    final_article = article_text

    if not grounding_passed and not args.skip_grounding_repair and blockers:
        print()
        print("=== GROUNDING COMPLETION LOOP ===")
        try:
            loop = CP.grounding_completion_loop(
                provider,
                article_text=article_text,
                package=None,
                initial=g,
                ledger=ledger,
                packet=writer_packet,
                arch=None,
                pack=pack,
                source_text=source_text,
                source_sha=source_sha,
                audit_fn=audit_fn,
            )
        except CP.CompositionHold as e:
            print("HOLD (loop error):", e)
            loop = {"status": CP.HOLD, "article_text": article_text}

        print("Loop status  :", loop.get("status"))
        print("Iterations   :", loop.get("iterations"))
        print("Accepted     :", loop.get("accepted"))
        print("Rejected     :", loop.get("rejected"))
        grounding_passed = loop.get("status") == CP.PASS
        final_article = loop.get("article_text") or article_text
        g["completion_loop"] = loop
    print()

    # ── READER ────────────────────────────────────────────────────────────────
    if not grounding_passed:
        print("GROUNDING HOLD — not proceeding to Reader.")
        result = {
            "run_dir": str(run_dir),
            "grounding_status": CP.HOLD,
            "reader_status": CP.NOT_RUN,
            "publication_ready": False,
            "grounding": g,
        }
    else:
        print("=== READER ===")
        try:
            r = CP.reader_gate(provider, final_article)
        except CP.CompositionHold as e:
            print("HOLD (provider error):", e)
            return 3

        print("Status   :", r.get("status"))
        print("One line :", r.get("one_line"))
        held_dims = r.get("held") or {}
        if held_dims:
            for dim, v in held_dims.items():
                print("  HOLD [%s]" % dim)
                for passage in ((v or {}).get("passages") or [])[:2]:
                    print("    %r" % passage[:100])

        publication_ready = r.get("status") == CP.PASS
        result = {
            "run_dir": str(run_dir),
            "grounding_status": g.get("status"),
            "reader_status": r.get("status"),
            "reader_one_line": r.get("one_line"),
            "reader_held_dimensions": list(held_dims.keys()),
            "publication_ready": publication_ready,
            "final_article_words": len(final_article.split()),
            "grounding": g,
            "reader": r,
        }

    # ── write result ──────────────────────────────────────────────────────────
    out_path = pathlib.Path(args.out or run_dir / "DOWNSTREAM_GATE_RESULT.json")
    out_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8")

    print()
    print("Result → %s" % out_path)
    print("Publication ready:", result["publication_ready"])
    return 0 if result["publication_ready"] else 4


if __name__ == "__main__":
    sys.exit(main())
