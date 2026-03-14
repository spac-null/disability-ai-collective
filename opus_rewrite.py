#!/usr/bin/env python3
"""
Rewrite weak articles to De Correspondent quality using Claude Opus.
Preserves frontmatter + image lines. Rewrites body prose only.
"""
import json, re, urllib.request, time
from pathlib import Path

import os

# Load secrets from env file (no export statements — must parse manually)
_ENV_FILE = Path("/srv/secrets/openclaw.env")
if _ENV_FILE.exists():
    for _line in _ENV_FILE.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

API_KEY  = os.environ.get("ANTHROPIC_API_KEY", "")
API_URL  = "http://172.19.0.1:8317/v1/chat/completions"
MODEL    = "claude-opus-4-6"
POSTS    = Path("/srv/data/openclaw/workspaces/ops/disability-ai-collective/_posts")

# Add filenames here to batch-rewrite articles with Opus.
# All existing articles already rewritten — list is intentionally empty.
TARGETS = [
]

SYSTEM = """You are a senior editor at De Correspondent — the Dutch long-form journalism platform known for expert-driven, deeply personal reported essays. You edit articles for the disability-ai-collective, an editorial arts platform where AI agents write from distinct disability perspectives (crip culture, disability justice, dis.art aesthetic).

Your task: rewrite the BODY of articles to match De Correspondent quality. The frontmatter (between --- markers) and image markdown lines (![...](...)) must be preserved exactly as-is.

DE CORRESPONDENT VOICE RULES:
1. Open with ONE specific concrete moment, scene, or sharp claim — never a question, statistics, or "In today's world"
2. First-person throughout — lived expertise, not detached analysis
3. NO academic headers: Research Question / Methodology / Key Findings / Recommendations / Community Questions
4. NO bullet-point policy lists — weave argument into prose
5. NO "Case study: Sarah, a graphic designer..." — use real narrative flow
6. Long paragraphs with rhythm — vary short punchy sentences with longer development
7. Bold sparingly — only sharpest claims, never structural markers
8. End on a resonant question or image, not a call-to-action
9. 700-1000 words body — substantial but not padded
10. Author's disability is their EXPERTISE and LENS, never tragedy or limitation
11. Crip culture references (Sins Invalid, crip time, disability justice) only when they fit naturally

Return ONLY the complete rewritten article (frontmatter preserved + image lines preserved + rewritten body). No commentary, no preamble."""

def call_opus(article_text, gold_text, filename):
    user_msg = f"""STYLE REFERENCE (De Correspondent quality — match this voice):
<gold_standard>
{gold_text}
</gold_standard>

ARTICLE TO REWRITE:
<article filename="{filename}">
{article_text}
</article>

Rewrite the article body to De Correspondent quality. Preserve frontmatter and all image markdown lines exactly."""

    payload = json.dumps({
        "model": MODEL,
        "max_tokens": 2500,
        "messages": [{"role": "user", "content": user_msg}],
        "system": SYSTEM,
    }).encode()

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        }
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        resp = json.loads(r.read())
    return resp["choices"][0]["message"]["content"]

def main():
    gold = (POSTS / "2026-03-08-architects-are-designing-buildings-for-the-wrong-sense.md").read_text()

    for filename in TARGETS:
        path = POSTS / filename
        if not path.exists():
            print(f"SKIP: {filename}")
            continue

        print(f"\n[Opus] {filename}")
        original = path.read_text()
        path.with_suffix(".md.bak").write_text(original)

        try:
            rewritten = call_opus(original, gold, filename)
            if "---" not in rewritten[:200]:
                print(f"  WARN: missing frontmatter in response, skipping")
                print(f"  Preview: {rewritten[:300]}")
                continue
            path.write_text(rewritten.lstrip("\n"))
            print(f"  OK ({len(rewritten)} chars)")
            time.sleep(4)
        except Exception as e:
            print(f"  ERR: {e}")
            path.write_text(original)

    print("\nDone.")

if __name__ == "__main__":
    main()
