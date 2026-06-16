#!/usr/bin/env python3
"""
Retroactively fix broken keywords on existing _posts/*.md articles.

Bad keywords look like: title-fragment pairs ("arithmetic nobody", "flood hears")
or pure generic filler ("neurodivergent workplace, autism diagnosis, neurodiversity").

Skips articles whose keywords already look specific (proper nouns, named theories, etc.)
"""
import re, sys, os, time
from pathlib import Path
import urllib.request, urllib.error, json

POSTS_DIR = Path(__file__).parent.parent / "_posts"
CLIPROXY_URL = os.environ.get("CLIPROXY_URL", "http://127.0.0.1:8317/v1")
CLIPROXY_KEY = os.environ.get("CLIPROXY_KEY", "local")

# Keywords that indicate a bad/generic auto-generated set
GENERIC_SIGNALS = [
    "neurodivergent workplace", "autism diagnosis", "neurodiversity",
    "wheelchair accessibility", "disability infrastructure", "urban design",
    "blind navigation", "acoustic accessibility", "spatial design",
    "deaf accessibility", "visual information design", "visual design",
]

# Minimum specificity signals that indicate keywords are already good
SPECIFICITY_SIGNALS = [
    # proper nouns, named theories, legislation, events
    "baron-cohen", "ndis", "swan care", "jennifer kanary", "mirthe berentsen",
    "christine sun kim", "stelarc", "liz carr", "jim sinclair", "warren neidich",
    "labyrinth", "autonomous exhibition", "niet normaal", "ine gevers",
    "health and care visa", "employment tribunal", "camouflaging", "masking",
    "extreme male brain", "systemizing quotient",
]


def is_bad_keywords(kw_line: str) -> bool:
    """Return True if keywords look auto-generated / generic."""
    kw_lower = kw_line.lower()
    # Check for title-fragment pattern: two short words that look like they came from a title
    # e.g. "arithmetic nobody", "flood hears", "room sings"
    fragment_pattern = re.findall(r'\b([a-z]{3,12}) ([a-z]{3,12})\b', kw_lower)
    # If first keyword is a 2-word phrase that doesn't contain any specific signal, suspect
    has_specific = any(sig in kw_lower for sig in SPECIFICITY_SIGNALS)
    if has_specific:
        return False
    has_generic = sum(1 for sig in GENERIC_SIGNALS if sig in kw_lower)
    if has_generic >= 2:
        return True
    # Title-fragment detection: keyword starts with two lowercase common words
    if fragment_pattern and len(fragment_pattern[0][0]) <= 8 and len(fragment_pattern[0][1]) <= 8:
        # Looks like a title fragment if none of the keywords are longer phrases
        long_kws = [k for k in re.findall(r'[^\[\],]+', kw_lower) if len(k.strip()) > 15]
        if not long_kws:
            return True
    return False


def call_llm(title: str, content: str, author: str) -> list:
    body_preview = content[:1500]
    payload = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 120,
        "messages": [{"role": "user", "content": (
            f"Title: {title}\nAuthor: {author}\n\nArticle excerpt:\n{body_preview}\n\n"
            "Return 5-7 comma-separated SEO keywords. Specific > generic. "
            "Include proper nouns, named theories, named people, legislation, events. "
            "Think: what would someone type into Google the day they read this article in a newspaper? "
            "No explanation, no numbering, no quotes. Just the comma-separated list."
        )}],
        "system": (
            "You generate SEO keywords for Crip Minds, a disability culture publication. "
            "Return 5-7 keywords as a comma-separated list. No explanation, no numbering, no quotes. "
            "Include specific proper nouns (people, institutions, named theories, artworks, legislation); "
            "include exact phrases people would type into Google; "
            "do NOT use generic filler like 'disability culture', 'neurodiversity', 'urban design' "
            "unless the article is specifically about that concept."
        ),
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{CLIPROXY_URL}/chat/completions",
        data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {CLIPROXY_KEY}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            raw = result["choices"][0]["message"]["content"].strip()
            kws = [k.strip().strip('"').strip("'") for k in raw.split(",") if k.strip()]
            return kws[:7]
    except Exception as e:
        print(f"  LLM error: {e}")
        return []


def fix_post(path: Path, dry_run: bool = False) -> bool:
    text = path.read_text()
    # Find keywords line
    kw_match = re.search(r'^keywords: \[(.+)\]', text, re.MULTILINE)
    if not kw_match:
        return False
    kw_line = kw_match.group(1)
    if not is_bad_keywords(kw_line):
        return False

    # Extract front matter fields
    title_m = re.search(r'^title: "(.+)"', text, re.MULTILINE)
    author_m = re.search(r'^author: "(.+)"', text, re.MULTILINE)
    title = title_m.group(1) if title_m else path.stem
    author = author_m.group(1) if author_m else ""

    # Extract body (after second ---)
    parts = text.split("---", 2)
    content = parts[2].strip() if len(parts) >= 3 else text

    print(f"  Fixing: {title[:60]}")
    print(f"  Old: [{kw_line[:80]}]")

    if dry_run:
        print("  [dry-run, skipping LLM call]")
        return True

    new_kws = call_llm(title, content, author)
    if not new_kws:
        print("  LLM returned nothing, skipping")
        return False

    new_kw_str = ", ".join(new_kws)
    print(f"  New: [{new_kw_str[:80]}]")
    new_text = re.sub(
        r'^keywords: \[.+\]',
        f"keywords: [{new_kw_str}]",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    path.write_text(new_text)
    return True


def main():
    dry_run = "--dry-run" in sys.argv
    posts = sorted(POSTS_DIR.glob("*.md"))
    fixed = 0
    skipped = 0
    for path in posts:
        result = fix_post(path, dry_run=dry_run)
        if result:
            fixed += 1
            time.sleep(0.5)  # rate limit
        else:
            skipped += 1
    print(f"\nDone. Fixed: {fixed}, Already OK / skipped: {skipped}")


if __name__ == "__main__":
    main()
