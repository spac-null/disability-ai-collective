#!/usr/bin/env python3
"""
opus_rewrite.py — Quality gate: auto-detect and rewrite weak articles with Claude Opus.

Detection criteria (either triggers a rewrite):
  1. model_used: frontmatter field is not Opus (written by fallback model)
  2. Quality score >= REWRITE_THRESHOLD (De Correspondent anti-patterns detected)

Quality scoring penalises: question openers, statistics openers, cliché openers,
academic headers, bullet policy lists, case-study patterns, word count violations,
CTA endings, missing first-person voice.
"""
import json, re, subprocess, time, logging
from pathlib import Path
import os

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

# Load secrets from env file (no export statements — must parse manually)
_ENV_FILE = Path("/srv/secrets/openclaw.env")
if _ENV_FILE.exists():
    for _line in _ENV_FILE.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

import urllib.request

API_KEY          = os.environ.get("ANTHROPIC_API_KEY", "")
API_URL          = "http://172.19.0.1:8317/v1/chat/completions"
MODEL            = "claude-opus-4-6"
POSTS            = Path("/srv/data/openclaw/workspaces/ops/disability-ai-collective/_posts")
GOLD_STANDARD    = POSTS / "2026-03-08-architects-are-designing-buildings-for-the-wrong-sense.md"
REWRITE_THRESHOLD = 2   # penalty score >= this triggers a rewrite

# Manual override: add filenames here to force-rewrite specific articles.
# When non-empty, auto-scan is skipped entirely.
TARGETS_OVERRIDE = []

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


def _extract_body(text):
    """Return article body (everything after closing --- of frontmatter)."""
    m = re.search(r'^---\n.*?\n---\n', text, re.DOTALL)
    if not m:
        return text
    return text[m.end():]


def score_quality(text):
    """
    Score De Correspondent anti-patterns in article text.
    Returns {"score": int, "flags": [str]}.
    Higher score = worse quality. Threshold: REWRITE_THRESHOLD.
    """
    body = _extract_body(text)
    # First non-empty, non-image body line
    first_line = ""
    for line in body.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("![") and not stripped.startswith("*"):
            first_line = stripped
            break

    flags = []
    score = 0

    # Opens with a question
    if first_line.endswith("?"):
        flags.append("opens-with-question")
        score += 3

    # Opens with statistics or attributed study
    if re.match(r'^(\d|According to|Studies show|Research shows|A recent|New research)', first_line):
        flags.append("opens-with-statistic")
        score += 2

    # Opens with cliché
    cliches = ("In today's world", "In recent years", "As we know", "It is well known",
                "Throughout history", "In the age of", "In a world where")
    if any(first_line.startswith(c) for c in cliches):
        flags.append("opens-with-cliche")
        score += 2

    # Academic section headers
    academic_headers = re.findall(
        r'^#{1,3}\s*(Research Question|Methodology|Key Findings?|Recommendations?|'
        r'Community Questions?|Introduction|Conclusion|Overview|Background)',
        body, re.MULTILINE | re.IGNORECASE
    )
    if academic_headers:
        flags.append(f"academic-headers:{','.join(academic_headers)}")
        score += 3 * len(academic_headers)

    # Bullet-point policy list (3+ consecutive bullet lines)
    bullet_runs = re.findall(r'(?:^- .+\n){3,}', body, re.MULTILINE)
    if bullet_runs:
        flags.append(f"bullet-list-runs:{len(bullet_runs)}")
        score += 2

    # "Case study:" pattern
    if re.search(r'Case study:', body, re.IGNORECASE):
        flags.append("case-study-pattern")
        score += 2

    # Word count
    word_count = len(body.split())
    if word_count < 600:
        flags.append(f"too-short:{word_count}w")
        score += 3
    elif word_count > 1200:
        flags.append(f"too-long:{word_count}w")
        score += 1

    # CTA or "what do you think" ending
    last_line = ""
    for line in reversed(body.splitlines()):
        if line.strip():
            last_line = line.strip()
            break
    if re.search(r'What do you think|Share your|Let us know|Join the conversation|'
                 r'Tell us|We want to hear', last_line, re.IGNORECASE):
        flags.append("cta-ending")
        score += 1

    # Missing first-person voice
    if not re.search(r'\bI\b', body):
        flags.append("no-first-person")
        score += 2

    return {"score": score, "flags": flags}


def scan_posts_needing_rewrite():
    """Scan _posts/ and return filenames of articles that need a rewrite."""
    targets = []
    for path in sorted(POSTS.glob("*.md")):
        text = path.read_text()

        # Skip gold standard — never rewrite the reference article
        if path == GOLD_STANDARD:
            continue

        # Signal 1: written by a non-Opus model
        m = re.search(r'^model_used:\s*(.+)$', text, re.MULTILINE)
        is_fallback = bool(m and "opus" not in m.group(1).lower()
                          and "rewrite" not in m.group(1).lower())

        # Signal 2: quality score
        q = score_quality(text)
        needs_rewrite = is_fallback or q["score"] >= REWRITE_THRESHOLD

        if needs_rewrite:
            model_info = m.group(1).strip() if m else "unknown"
            log.info("  needs rewrite: %s | model=%s | score=%d | flags=%s",
                     path.name, model_info, q["score"], q["flags"])
            targets.append(path.name)

    return targets


def get_targets():
    """Return list of filenames to rewrite. Manual override takes full precedence."""
    if TARGETS_OVERRIDE:
        log.info("Using manual TARGETS_OVERRIDE (%d files)", len(TARGETS_OVERRIDE))
        return TARGETS_OVERRIDE
    log.info("Auto-scanning posts for rewrite candidates...")
    return scan_posts_needing_rewrite()


def verify_frontmatter_preserved(original, rewritten):
    """Check that critical frontmatter fields and image lines are intact."""
    if not rewritten.strip().startswith("---"):
        log.warning("  verify: missing frontmatter block")
        return False

    for field in ("title:", "date:", "author:", "image:"):
        om = re.search(rf'^{field}(.+)$', original, re.MULTILINE)
        rm = re.search(rf'^{field}(.+)$', rewritten, re.MULTILINE)
        if om and (not rm or om.group(1).strip() != rm.group(1).strip()):
            log.warning("  verify: frontmatter field changed or missing: %s", field)
            return False

    orig_imgs = set(re.findall(r'^!\[.*?\]\(.*?\)', original, re.MULTILINE))
    rew_imgs  = set(re.findall(r'^!\[.*?\]\(.*?\)', rewritten, re.MULTILINE))
    if orig_imgs != rew_imgs:
        log.warning("  verify: image lines changed. orig=%s rew=%s", orig_imgs, rew_imgs)
        return False

    return True


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


def git_commit_rewrites(rewritten_filenames):
    """Commit and push rewritten posts to origin (GH Pages)."""
    files = [f"_posts/{f}" for f in rewritten_filenames]
    subprocess.run(["git", "add"] + files, cwd=POSTS.parent, check=True)
    msg = f"quality: opus rewrite — {len(rewritten_filenames)} article(s) upgraded"
    subprocess.run(["git", "commit", "-m", msg], cwd=POSTS.parent, check=True)
    subprocess.run(["git", "push", "origin", "main"], cwd=POSTS.parent, check=True)
    log.info("Committed and pushed: %s", msg)


def main():
    if not GOLD_STANDARD.exists():
        raise SystemExit(f"Gold standard article not found: {GOLD_STANDARD}")

    gold = GOLD_STANDARD.read_text()
    targets = get_targets()

    if not targets:
        log.info("No articles need rewriting. Done.")
        return

    log.info("%d article(s) queued for rewrite: %s", len(targets), targets)
    rewritten = []

    for filename in targets:
        path = POSTS / filename
        if not path.exists():
            log.warning("SKIP (not found): %s", filename)
            continue

        log.info("\n[Opus rewrite] %s", filename)
        original = path.read_text()

        # Detect original model for audit trail
        m = re.search(r'^model_used:\s*(.+)$', original, re.MULTILINE)
        original_model = m.group(1).strip() if m else "unknown"

        # Backup original
        path.with_suffix(".md.bak").write_text(original)

        try:
            rewritten_text = call_opus(original, gold, filename)
            rewritten_text = rewritten_text.lstrip("\n")

            if not verify_frontmatter_preserved(original, rewritten_text):
                log.warning("  Frontmatter verification failed — skipping write")
                continue

            # Update model_used to record the rewrite
            if "model_used:" in rewritten_text:
                rewritten_text = re.sub(
                    r'^model_used:.*$',
                    f'model_used: {MODEL} (rewrote {original_model})',
                    rewritten_text, flags=re.MULTILINE
                )
            else:
                rewritten_text = re.sub(
                    r'^(image:.*)$',
                    rf'\1\nmodel_used: {MODEL} (rewrote {original_model})',
                    rewritten_text, flags=re.MULTILINE
                )

            path.write_text(rewritten_text)
            q_after = score_quality(rewritten_text)
            log.info("  OK (%d chars) | quality score after: %d", len(rewritten_text), q_after["score"])
            rewritten.append(filename)
            time.sleep(4)

        except Exception as e:
            log.error("  ERR: %s — restoring original", e)
            path.write_text(original)

    if rewritten:
        git_commit_rewrites(rewritten)
        log.info("\nDone — %d article(s) rewritten and committed.", len(rewritten))
    else:
        log.warning("No articles successfully rewritten.")


if __name__ == "__main__":
    main()
