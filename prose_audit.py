#!/usr/bin/env python3
"""
prose_audit.py — One-off Opus audit of all non-article prose files.

Checks voice consistency with publication DNA and Bregman register.
Markdown files: outputs improved version in place.
HTML / other: outputs a text report of what to fix, no file changes.

Usage:
  ./run python3 prose_audit.py
  ./run python3 prose_audit.py --dry-run   (report only, no writes)
"""
import json, re, os, argparse, logging
from pathlib import Path
import urllib.request

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

_ENV_FILE = Path("/srv/secrets/openclaw.env")
if _ENV_FILE.exists():
    for _line in _ENV_FILE.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
API_URL = "http://172.19.0.1:8317/v1/chat/completions"
MODEL   = "claude-opus-4-6"
BASE    = Path("/srv/data/openclaw/workspaces/ops/disability-ai-collective")

SYSTEM = """You are a senior editor reviewing non-article prose files for a disability culture publication. You check them for voice consistency with the publication's DNA and Bregman register.

PUBLICATION DNA:
This publication is built by someone who stood in a room at the Van Abbemuseum and recognized it. Ahmet Ogut's Exploded City — scale models of buildings that no longer exist, shown intact. Your mind fills in what was lost. He guided visitors through that room every week for six months. Each time he thought: this is how I think.

He also knows the other image. Screaming inside a transparent plastic cube, one cubic decimetre, lying on the street. Pedestrians walking past without noticing. That is what invisibility feels like from the inside.

He draws in bic pen. No correction. No undo. Sign language works the same way: meaning in the body, in movement, in time.

GIFs and sign language are the same medium. Both time-based, both exist only in movement, both lose something the moment they stop. Write this way: one concrete scene, then another, with a gap between them. The reader fills the gap. Trust the gap.

Two kinds of knowledge. Experience is the argument. Scholarship is evidence. The ramp, the lag, the room full of eyes come first. Citations after, if at all.

The copy has won. The accessible design that perfectly meets the standard and fails the person. The standard has become more real than the thing it was abstracting from.

WRITING MODEL — RUTGER BREGMAN: Accessible intellectual journalism that reads like a smart person explaining something to a friend. Plain vocabulary. Sentence economy. One modifier per noun. Never announce the thesis — the example makes the argument.

VOICE RULES:
- Plain English. "Use" not "utilise."
- Short declarative lands the idea. Longer sentence develops it. Short again.
- No academic headers in prose sections. No bullet-point policy lists.
- Disability as culture and identity — never tragedy, never inspiration porn.
- No startup language ("building," "platform," "space," "community," "voices," "centering").
- No hedging: "aims to," "seeks to," "strives to."
- Named and specific — who, where, when, what happened."""


PROSE_TARGETS = [
    # (path_relative_to_BASE, mode: 'rewrite'|'report')
    ("MANIFESTO.md",            "rewrite"),
    ("editorial-lens.md",       "report"),
    ("about.html",              "report"),
    ("press/index.html",        "report"),
    ("jascha.html",             "report"),
    ("docs/analytics.md",       "report"),
    ("docs/DISCOVERY.md",       "report"),
]


def call_opus(content, path, mode):
    if mode == "rewrite":
        instruction = (
            "Rewrite this file to better embody the publication DNA and Bregman register. "
            "Preserve all structure (markdown headers, front matter if any). "
            "Return ONLY the improved file content — no commentary, no preamble."
        )
    else:
        instruction = (
            "Review this file for voice consistency with the publication DNA and Bregman register. "
            "Output a brief report (5-10 bullet points max) noting: what works, what drifts, "
            "specific lines or phrases that should change and what they should become. "
            "Be concrete — quote the problem text, give the fix."
        )

    user_msg = f"FILE: {path}\n\n{instruction}\n\n<file>\n{content}\n</file>"

    payload = json.dumps({
        "model": MODEL,
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": user_msg}],
        "system": SYSTEM,
    }).encode()
    req = urllib.request.Request(
        API_URL, data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        resp = json.loads(r.read())
    return resp["choices"][0]["message"]["content"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Report only, no file writes")
    args = parser.parse_args()

    results = {}

    for rel_path, mode in PROSE_TARGETS:
        path = BASE / rel_path
        if not path.exists():
            log.warning("SKIP (not found): %s", rel_path)
            continue

        log.info("\n[Opus audit] %s (%s)", rel_path, mode)
        content = path.read_text()

        try:
            result = call_opus(content, rel_path, mode)
            results[rel_path] = result

            if mode == "rewrite" and not args.dry_run:
                path.with_suffix(path.suffix + ".bak").write_text(content)
                path.write_text(result)
                log.info("  Rewritten: %s", rel_path)
            else:
                log.info("  Report:\n%s", result)

        except Exception as e:
            log.warning("  FAILED: %s — %s", rel_path, e)

    # Write report file
    report_path = BASE / "prose_audit_report.md"
    lines = ["# Prose Audit Report\n"]
    for rel_path, result in results.items():
        lines.append(f"## {rel_path}\n\n{result}\n\n---\n")
    report_path.write_text("\n".join(lines))
    log.info("\nReport written: %s", report_path)


if __name__ == "__main__":
    main()
