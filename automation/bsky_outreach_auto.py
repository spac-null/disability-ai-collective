#!/usr/bin/env python3
"""
bsky_outreach_auto.py — Weekly Bluesky outreach to key community figures.

Logic:
  1. Pick next pending verified target from targets.json
  2. Find best matching recent article (last N days) by keyword overlap
  3. If match score < threshold → skip this week (no post)
  4. Generate post text via Opus (CLIProxyAPI) — tailored to person + article
  5. Validate length, post with proper facets
  6. Update targets.json → status: done

Run via cron (weekly, e.g. Saturday 10:00):
  0 10 * * 6 cd /srv/data/openclaw/workspaces/ops/disability-ai-collective && \
    source /srv/secrets/openclaw.env && \
    python3 automation/bsky_outreach_auto.py >> automation/bsky_outreach.log 2>&1
"""
import json, os, re, logging, urllib.request as ureq, urllib.parse
from pathlib import Path
from datetime import datetime, timezone, timedelta

REPO      = Path(__file__).parent.parent
TARGETS_F = Path(__file__).parent / "targets.json"
LOG_F     = Path(__file__).parent / "bsky_outreach.log"
POSTS_DIR = REPO / "_posts"
API       = "https://bsky.social/xrpc"
CLAUDE    = os.environ.get("CLAUDE_API_URL", "http://172.19.0.1:8317/v1")
CLAUDE_KEY= os.environ.get("CLAUDE_API_KEY", "sk-unused")

logging.basicConfig(
    filename=str(LOG_F), level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


# ── Article scanning ───────────────────────────────────────────────────────────

def _parse_frontmatter(text: str) -> dict:
    """Extract key: value pairs from YAML frontmatter."""
    meta = {}
    if not text.startswith("---"):
        return meta
    end = text.find("---", 3)
    if end == -1:
        return meta
    for line in text[3:end].splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip().strip('"\'')
    return meta


def find_best_article(focus_keywords: list, lookback_days: int, threshold: int) -> dict | None:
    """
    Scan _posts/ for recent articles. Score each against focus_keywords.
    Returns best match dict if score >= threshold, else None.
    """
    cutoff = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    best = None
    best_score = 0

    for post_file in sorted(POSTS_DIR.glob("*.md"), reverse=True):
        stem = post_file.stem
        if stem[:10] < cutoff:
            break
        try:
            raw = post_file.read_text(errors="ignore")
        except Exception:
            continue

        meta    = _parse_frontmatter(raw)
        title   = meta.get("title", stem)
        excerpt = meta.get("excerpt", "")
        keywords_fm = meta.get("keywords", "")
        category    = meta.get("category", "")

        # Combine all searchable text (lowercased)
        searchable = f"{title} {excerpt} {keywords_fm} {category}".lower()

        score = sum(1 for kw in focus_keywords if kw.lower() in searchable)
        if score > best_score:
            best_score = score
            best = {
                "slug":     stem,
                "title":    title,
                "excerpt":  excerpt,
                "date":     stem[:10],
                "author":   meta.get("author", ""),
                "score":    score,
            }

    if best and best["score"] >= threshold:
        return best
    log.info("No match above threshold %d (best score: %d)", threshold, best_score if best else 0)
    return None


# ── Text generation ────────────────────────────────────────────────────────────

def generate_post_text(target: dict, article: dict, max_chars: int) -> str | None:
    """Call Opus via CLIProxyAPI to write the outreach message body."""
    prompt = (
        "You are the editor of cripminds.com — a disability-led AI arts publication that writes about "
        "disability as culture, not tragedy. Architecture, design, economics, aesthetics. "
        "You are writing a short Bluesky message to {name}.\n\n"
        "About them: {bio}\n"
        "Their focus: {focus}\n\n"
        "Your recent article they might care about:\n"
        "  Title: {title}\n"
        "  Excerpt: {excerpt}\n\n"
        "Write a Bluesky message body. Rules:\n"
        "- MAX {max_chars} characters (this is strict — count carefully)\n"
        "- Start with the connection between their work and this article — no intro, no greeting\n"
        "- One precise observation or hook. Not a pitch. Not a summary.\n"
        "- Sound like one editor to a peer, not a brand to an influencer\n"
        "- Do NOT include their handle or any hashtags — those are added automatically\n"
        "- Do NOT start with 'Your work' or 'As someone who'\n"
        "- Return ONLY the message body text, nothing else"
    ).format(
        name=target["name"],
        bio=target["bio"],
        focus=", ".join(target["focus_keywords"]),
        title=article["title"],
        excerpt=article["excerpt"],
        max_chars=max_chars,
    )

    payload = {
        "model":      "claude-opus-4-6",
        "max_tokens": 300,
        "messages":   [{"role": "user", "content": prompt}],
    }
    try:
        req = ureq.Request(
            f"{CLAUDE}/chat/completions",
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type":  "application/json",
                "Authorization": f"Bearer {CLAUDE_KEY}",
            },
            method="POST",
        )
        with ureq.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
        text = data["choices"][0]["message"]["content"].strip()
        # Strip any quotes the model might wrap around the output
        text = text.strip('"\'')
        return text
    except Exception as e:
        log.error("LLM generation failed: %s", e)
        return None


# ── Bluesky helpers ────────────────────────────────────────────────────────────

def bsky_req(path, payload=None, token=None, method="POST"):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = ureq.Request(
        f"{API}/{path}",
        data=json.dumps(payload).encode() if payload else None,
        headers=headers, method=method,
    )
    with ureq.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def resolve_did(handle: str) -> str:
    url = f"{API}/com.atproto.identity.resolveHandle?handle={urllib.parse.quote(handle)}"
    with ureq.urlopen(ureq.Request(url, method="GET"), timeout=10) as r:
        return json.loads(r.read())["did"]


def byte_range(full_text: str, substring: str) -> tuple[int, int]:
    b, sb = full_text.encode("utf-8"), substring.encode("utf-8")
    i = b.find(sb)
    return i, i + len(sb)


def build_post(handle: str, did: str, text_body: str) -> tuple[str, list]:
    """Assemble full post text + facets from body text and target handle."""
    tags      = "#accessibility #DisabilitySky #CripMinds"
    mention   = f"@{handle}"
    full_text = f"{mention} {text_body}\n\n{tags}"

    # Check grapheme length (Bluesky limit = 300)
    if len(full_text) > 300:
        # Trim body to fit
        overhead   = len(mention) + 1 + 2 + len(tags)
        max_body   = 300 - overhead
        text_body  = text_body[:max_body].rsplit(" ", 1)[0]
        full_text  = f"{mention} {text_body}\n\n{tags}"

    facets = []

    # Mention facet
    ms, me = byte_range(full_text, mention)
    if ms >= 0:
        facets.append({
            "index":    {"byteStart": ms, "byteEnd": me},
            "features": [{"$type": "app.bsky.richtext.facet#mention", "did": did}],
        })

    # Hashtag facets
    for tag in ["#accessibility", "#DisabilitySky", "#CripMinds"]:
        ts, te = byte_range(full_text, tag)
        if ts >= 0:
            facets.append({
                "index":    {"byteStart": ts, "byteEnd": te},
                "features": [{"$type": "app.bsky.richtext.facet#tag", "tag": tag[1:]}],
            })

    return full_text, facets


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    bsky_handle   = os.environ.get("BSKY_HANDLE", "")
    bsky_password = os.environ.get("BSKY_APP_PASSWORD", "")
    if not bsky_handle or not bsky_password:
        log.error("BSKY_HANDLE and BSKY_APP_PASSWORD must be set — aborting")
        return

    # Load targets
    data = json.loads(TARGETS_F.read_text())
    cfg  = data.get("config", {})
    threshold    = cfg.get("match_threshold", 2)
    lookback     = cfg.get("lookback_days", 21)
    max_body     = cfg.get("max_generated_text_chars", 210)

    # Find next eligible target
    target = next(
        (t for t in data["targets"]
         if t.get("status") == "pending" and t.get("handle_verified", False)),
        None
    )
    if not target:
        log.info("No pending verified targets — nothing to do")
        return

    log.info("Next target: %s (%s)", target["name"], target["handle"])

    # Find best matching article
    article = find_best_article(target["focus_keywords"], lookback, threshold)
    if not article:
        log.info(
            "No article match for %s (threshold %d, lookback %d days) — skipping this week",
            target["name"], threshold, lookback
        )
        return

    log.info(
        "Matched article '%s' (score %d) for %s",
        article["title"], article["score"], target["name"]
    )

    # Generate post body — up to 3 attempts
    body = None
    for attempt in range(3):
        body = generate_post_text(target, article, max_body)
        if body and len(body) <= max_body:
            break
        if body:
            log.warning("Generated text too long (%d chars), retrying", len(body))
            body = None
    if not body:
        log.error("Failed to generate valid post text after 3 attempts — aborting")
        return

    # Auth
    try:
        session = bsky_req("com.atproto.server.createSession",
                           {"identifier": bsky_handle, "password": bsky_password})
        token = session["accessJwt"]
        did   = session["did"]
    except Exception as e:
        log.error("Bluesky auth failed: %s", e)
        return

    # Resolve target DID
    try:
        target_did = resolve_did(target["handle"])
    except Exception as e:
        log.error("Could not resolve DID for %s: %s", target["handle"], e)
        return

    # Build and post
    full_text, facets = build_post(target["handle"], target_did, body)
    log.info("Posting (%d graphemes): %s", len(full_text), full_text[:80])

    record = {
        "repo":       did,
        "collection": "app.bsky.feed.post",
        "record": {
            "$type":     "app.bsky.feed.post",
            "text":      full_text,
            "facets":    facets,
            "createdAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    }
    try:
        result = bsky_req("com.atproto.repo.createRecord", record, token=token)
        uri = result.get("uri", "")
    except Exception as e:
        log.error("Post failed: %s", e)
        return

    log.info("Posted to %s: %s", target["name"], uri)

    # Mark done in targets.json
    for t in data["targets"]:
        if t["handle"] == target["handle"]:
            t["status"]         = "done"
            t["posted_date"]    = datetime.now().strftime("%Y-%m-%d")
            t["post_uri"]       = uri
            t["matched_article"] = article["slug"]
            break
    TARGETS_F.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    log.info("targets.json updated")


if __name__ == "__main__":
    main()
