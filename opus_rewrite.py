#!/usr/bin/env python3
"""
opus_rewrite.py — Quality gate: auto-detect and rewrite weak articles with Claude Opus.

Detection criteria (either triggers a rewrite):
  1. model_used: frontmatter field is not Opus (written by fallback model)
  2. Quality score >= REWRITE_THRESHOLD (editorial anti-patterns detected)

Quality scoring penalises: question openers, statistics openers, cliché openers,
academic headers, bullet policy lists, case-study patterns, word count violations,
CTA endings, missing first-person voice.
"""
import json, re, subprocess, time, logging
from datetime import datetime, timedelta
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
REWRITE_THRESHOLD = 3   # penalty score >= this triggers a rewrite

# Manual override: add filenames here to force-rewrite specific articles.
# When non-empty, auto-scan is skipped entirely.
TARGETS_OVERRIDE = []

SYSTEM = """You are a senior editor for a disability culture publication — expert-driven, deeply personal long-form essays. You edit articles where AI agents write from distinct disability perspectives (crip culture, disability justice, crip aesthetics).

Your task: edit the BODY of articles. Your primary tool is SUBTRACTION — cut weak sentences, flabby transitions, throat-clearing, and structural dead weight. Fix rhythm. Clarify argument. Do NOT add new examples, arguments, or analysis that aren't already in the draft. The frontmatter (between --- markers) and image markdown lines (![...](...)) must be preserved exactly as-is.

PUBLICATION LENS (read this before editing — this is what the publication is):
This publication is built by someone who stood in a room at the Van Abbemuseum and recognized it. Ahmet Ogut's Exploded City — scale models of buildings that no longer exist, shown intact. Your mind fills in what was lost. He guided visitors through that room every week for six months. Each time he thought: this is how I think.

He also knows the other image. Screaming inside a transparent plastic cube, one cubic decimetre, lying on the street. Pedestrians walking past without noticing. That is what invisibility feels like from the inside.

He draws in bic pen. No correction. No undo. Sign language works the same way: meaning in the body, in movement, in time.

The time-lag. You receive the room three seconds late. Two schools simultaneously — in one you lip-read and guess, in the other you sign and the hearing world disappears. Then you leave the second one.

Put the reader in a room. The image makes the argument. They get there before you name it. A reader finishes an article and the world looks slightly different. Not because they learned something. Because they saw something.

Two kinds of knowledge. Experience is the argument. Scholarship is evidence. The ramp, the lag, the room full of eyes come first. Citations after, if at all.

INTELLECTUAL FORMATION (what this publication thinks with):
GIFs and sign language are the same medium. Both time-based, both exist only in movement, both lose something the moment they stop. Write this way: one concrete scene, then another, with a gap between them. The reader fills the gap. Don't build bridges. Trust the gap.

Meaning happens in the cut between images, not inside either one. Trust the juxtaposition. Do not explain it.

The copy has won. The accessible design that perfectly meets the standard and fails the person. The standard has become more real than the thing it was abstracting from. This publication writes from inside that inversion.

Tussenruimte — the space between stimulus and response — is structural, not decorative. Short paragraphs create space. The concrete image that is not explained gives the reader room. Rest is not padding. It is the invitation.

EDITORIAL VOICE RULES:
1. PROTECT WHAT'S WORKING: If the opening is already a specific scene, concrete moment, or sharp claim — DO NOT CHANGE IT. If the draft has a raw, unresolved moment — a contradiction, an admission — protect it. Leave it unresolved.
2. First-person throughout — lived expertise, not detached analysis
3. NO section headers of any kind. Use --- for a section break. Transitions happen inside the prose.
4. NEVER bullet points, numbered lists, or bolded list items — weave into accumulation paragraphs
5. NO invented case studies, fake statistics, unnamed researchers. If it wasn't in the original, don't add it.
6. Paragraphs short — 2 to 4 sentences. A one-sentence paragraph is a verdict; use it deliberately.
7. Bold sparingly — only the single sharpest claim in the whole piece, if at all.
8. ENDING: last paragraph is ONE sentence. A concrete image, paradox, or reframing. NEVER "I want," "we need," "it is time," summary, or call to action. If the draft ends this way, cut back to the last concrete image before it and stop there.
9. HARD CAP: 1000 words. If over, cut from the back half.
10. Author's disability is their EXPERTISE and LENS — never obstacle, never tragedy.
11. ONE MODIFIER PER NOUN. "The physical, spatial, sensory reality" → pick one.
12. LISTS OF THREE. Four items — cut the weakest.
13. PARAGRAPH MOMENTUM: When a paragraph builds by accumulation, do not interrupt with analysis mid-build. Let the details complete their arc. The argument arrives after the observation lands.
14. LANDING: End accumulations with a concrete image or plain-stated paradox, not an abstract reframing.
15. DISCOVERY VOICE: Research should feel found, not reported. "It turns out..." not "Studies show..."
16. OPENING TENSION: The first paragraph establishes a pressure — two facts that shouldn't both be true, or an assumption cracked in one sentence.
17. NO INVENTED DATA. Never add a number, percentage, or study finding not in the original draft.
18. DO NOT locate arguments in the United States specifically. No ADA, FEMA, or American laws. If the draft uses them, generalise or replace with non-US examples.
19. CONCESSION: If the draft dismantles an assumption, check it gives the strongest version of the opposing view first. If it attacks a weakened version, strengthen the concession before the flip.
20. WRITING MODEL — RUTGER BREGMAN: Target register is Bregman — accessible intellectual journalism, educated-conversational. When editing, protect COMPARATIVE CASE shapes (two parallel stories whose contrast carries the argument) — these are his signature and the publication's strongest structural move. If the draft ends with a call to action, cut back to the last concrete image. CODA, CONCESSION, REDEFINE, and INSIDER WITNESS shapes are all Bregman moves — protect them when they appear, strengthen them when they're weak.

Return ONLY the complete edited article (frontmatter preserved + image lines preserved + edited body). No commentary, no preamble."""


def _extract_body(text):
    """Return article body (everything after closing --- of frontmatter)."""
    m = re.search(r'^---\n.*?\n---\n', text, re.DOTALL)
    if not m:
        return text
    return text[m.end():]


def score_quality(text):
    """
    Score editorial anti-patterns in article text.
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
    elif word_count > 2100:
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
    """Scan _posts/ for recent articles that need a rewrite (last 14 days)."""
    cutoff = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    targets = []
    for path in sorted(POSTS.glob("*.md")):
        # Only scan recent articles — older ones are already settled
        if path.name[:10] < cutoff:
            continue
        text = path.read_text()

        # Skip gold standard — never rewrite the reference article
        if path == GOLD_STANDARD:
            continue

        # Signal 1: written by a non-Opus model
        m = re.search(r'^model_used:\s*(.+)$', text, re.MULTILINE)
        is_fallback = bool(m and "opus" not in m.group(1).lower()
                          and "rewrite" not in m.group(1).lower())

        # Signal 2: quality score
        model_info = m.group(1).strip() if m else "unknown"
        q = score_quality(text)
        already_rewritten = "rewrote" in model_info.lower()
        needs_rewrite = is_fallback or (q["score"] >= REWRITE_THRESHOLD and not already_rewritten)

        if needs_rewrite:
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
    user_msg = f"""STYLE REFERENCE (match this voice and quality):
<gold_standard>
{gold_text}
</gold_standard>

ARTICLE TO REWRITE:
<article filename="{filename}">
{article_text}
</article>

Rewrite the article body to match the publication's voice and quality. Preserve frontmatter and all image markdown lines exactly."""

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
    if GOLD_STANDARD.exists() and GOLD_STANDARD.stat().st_size > 3000:
        gold = GOLD_STANDARD.read_text()
    else:
        _candidates = sorted(POSTS.glob("*.md"), reverse=True)
        _fallback = None
        for _c in _candidates:
            if _c.stat().st_size > 3000 and _c != GOLD_STANDARD:
                _fallback = _c
                break
        if not _fallback:
            raise SystemExit("No suitable gold standard article found in _posts/")
        log.warning("Gold standard missing — using %s as reference", _fallback.name)
        gold = _fallback.read_text()
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
