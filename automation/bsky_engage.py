#!/usr/bin/env python3
"""
bsky_engage.py — Bluesky reply engagement for cripminds.com

Polls notifications twice daily (cron). For each substantive reply/mention
on a cripminds post, generates a short in-persona reply from the article's author.

State: automation/bsky_engage_seen.json  (processed notification CIDs)
Log:   automation/bsky_engage.log
"""
import json, os, re, logging, urllib.request as ureq, urllib.error
from pathlib import Path
from datetime import datetime, timezone

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO     = Path(__file__).parent.parent
SOCIAL   = REPO / "_social"
STATE_F  = Path(__file__).parent / "bsky_engage_seen.json"
LOG_F    = Path(__file__).parent / "bsky_engage.log"
API      = "https://bsky.social/xrpc"
CLAUDE   = "http://172.19.0.1:8317/v1"

logging.basicConfig(
    filename=str(LOG_F), level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

# ── Per-persona reply voices ───────────────────────────────────────────────────
REPLY_PROMPTS = {
    "Siri Sage": (
        "You are Siri Sage — blind acoustic designer, dry wit, thinks in sound. "
        "Someone replied to your essay on Bluesky. Write a short reply (max 220 chars). "
        "Sound like a person, not a brand. If they disagreed, engage the argument. "
        "If they shared a personal story, acknowledge the specific detail they mentioned. "
        "No hashtags. No 'great point!'. No emojis unless one fits exactly right."
    ),
    "Pixel Nova": (
        "You are Pixel Nova — Deaf visual designer, thinks in maps and wayfinding, precise observations. "
        "Someone replied to your essay on Bluesky. Write a short reply (max 220 chars). "
        "Sound like a person having a real conversation. Engage what they actually said. "
        "If they pushed back, push back or concede — pick one. No 'thanks for sharing'. No hashtags."
    ),
    "Maya Flux": (
        "You are Maya Flux — wheelchair user, urban mobility researcher, politically direct. "
        "Someone replied to your essay on Bluesky. Write a short reply (max 220 chars). "
        "Be direct and human. If they disagreed, say whether they're right or wrong and why. "
        "If they shared something from their own life, connect it to the larger point. No hashtags."
    ),
    "Zen Circuit": (
        "You are Zen Circuit — autistic interface designer, pattern-recognition brain, dry and exact. "
        "Someone replied to your essay on Bluesky. Write a short reply (max 220 chars). "
        "Engage the actual content. If they found a pattern you missed, acknowledge it. "
        "If they misread the argument, correct it precisely. No warmth-performance. No hashtags."
    ),
}

GENERIC_PROMPT = (
    "You write for cripminds.com — a disability-led AI arts publication. "
    "Someone mentioned your publication on Bluesky. Write a short reply (max 220 chars). "
    "Sound like an editor, not a brand account. Engage what they said. No hashtags."
)

# ── Bluesky helpers ────────────────────────────────────────────────────────────
def bsky_post(path, payload, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = ureq.Request(f"{API}/{path}",
                       data=json.dumps(payload).encode(),
                       headers=headers, method="POST")
    with ureq.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def bsky_get(path, params=None, token=None):
    url = f"{API}/{path}"
    if params:
        url += "?" + "&".join(f"{k}={ureq.quote(str(v))}" for k, v in params.items())
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = ureq.Request(url, headers=headers)
    with ureq.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def auth():
    handle   = os.environ["BSKY_HANDLE"]
    password = os.environ["BSKY_APP_PASSWORD"]
    sess = bsky_post("com.atproto.server.createSession",
                     {"identifier": handle, "password": password})
    return sess["accessJwt"], sess["did"]

# ── State ──────────────────────────────────────────────────────────────────────
def load_seen():
    if STATE_F.exists():
        return set(json.loads(STATE_F.read_text()))
    return set()

def save_seen(seen):
    STATE_F.write_text(json.dumps(sorted(seen)))

# ── URI → agent map ────────────────────────────────────────────────────────────
def build_uri_map():
    """Map Bluesky post URI → agent name.
    Reads from _social/*.json; falls back to matching _posts/ front matter."""
    m = {}
    if not SOCIAL.exists():
        return m
    posts = list(REPO.glob("_posts/*.md"))
    for f in SOCIAL.glob("*.json"):
        try:
            d = json.loads(f.read_text())
            uri   = d.get("bsky_uri") or d.get("uri", "")
            agent = d.get("agent", "")
            if not agent:
                slug = f.stem
                for post in posts:
                    if slug in post.name:
                        txt = post.read_text()
                        ma  = re.search(r'^author:\s*["\']?([^"\'\n]+)["\']?', txt, re.M)
                        if ma:
                            agent = ma.group(1).strip()
                        break
            if uri and agent:
                m[uri] = agent
        except Exception:
            pass
    return m

# ── Claude call ────────────────────────────────────────────────────────────────
def generate_reply(system, prompt):
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    payload = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 100,
        "system": system,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = ureq.Request(
        f"{CLAUDE}/chat/completions",
        data=json.dumps({
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 100,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        }).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with ureq.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    text = data["choices"][0]["message"]["content"].strip().strip('"').strip("'")
    # Hard cap 220 chars, break at word boundary
    if len(text) > 220:
        cut = text[:220].rfind(" ")
        text = text[:cut] if cut > 150 else text[:220]
    return text

# ── Substantive filter ─────────────────────────────────────────────────────────
def is_substantive(text):
    """Ignore pure reactions: 'love this!', 'so true', single emoji, etc."""
    if not text:
        return False
    clean = re.sub(r"[\U00010000-\U0010ffff]", "", text).strip()  # strip emoji
    clean = re.sub(r"[@#]\S+", "", clean).strip()                  # strip handles/tags
    words = [w for w in clean.split() if len(w) > 2]
    return len(words) >= 5  # at least 5 real words

# ── Main ───────────────────────────────────────────────────────────────────────
def run():
    log.info("bsky_engage start")
    seen    = load_seen()
    uri_map = build_uri_map()
    log.info("URI map: %d known posts", len(uri_map))

    try:
        token, did = auth()
    except Exception as e:
        log.error("Auth failed: %s", e)
        return

    # Fetch unread notifications
    try:
        data  = bsky_get("app.bsky.notification.listNotifications",
                         {"limit": 50}, token=token)
        notifs = data.get("notifications", [])
    except Exception as e:
        log.error("listNotifications failed: %s", e)
        return

    log.info("Fetched %d notifications", len(notifs))
    replied = 0

    for n in notifs:
        cid    = n.get("cid", "")
        reason = n.get("reason", "")  # reply | mention | like | repost | follow | quote

        if cid in seen:
            continue
        seen.add(cid)

        if reason not in ("reply", "mention", "quote"):
            continue

        # Get the text of what they wrote
        record  = n.get("record", {})
        text    = record.get("text", "")
        author  = n.get("author", {}).get("handle", "someone")

        if not is_substantive(text):
            log.info("Skipped non-substantive from @%s: %r", author, text[:60])
            continue

        # Find which persona to reply as
        # Check if they replied to one of our posts
        reply_ref = record.get("reply", {})
        parent_uri = reply_ref.get("parent", {}).get("uri", "")
        agent = uri_map.get(parent_uri, "")

        system_prompt = REPLY_PROMPTS.get(agent, GENERIC_PROMPT)

        # Build context for Claude
        user_prompt = (
            f"@{author} wrote:\n\"{text}\"\n\n"
            f"Reply in character. Max 220 chars. No preamble, just the reply text."
        )

        try:
            reply_text = generate_reply(system_prompt, user_prompt)
        except Exception as e:
            log.warning("Generate failed for @%s: %s", author, e)
            continue

        if not reply_text:
            continue

        # Post reply
        try:
            root_ref = reply_ref.get("root", reply_ref.get("parent", {}))
            record_payload = {
                "$type": "app.bsky.feed.post",
                "text": reply_text,
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "reply": {
                    "root":   {"uri": root_ref.get("uri", parent_uri),
                               "cid": root_ref.get("cid", n.get("cid", ""))},
                    "parent": {"uri": n.get("uri", ""),
                               "cid": n.get("cid", "")},
                },
            }
            result = bsky_post("com.atproto.repo.createRecord",
                               {"repo": did, "collection": "app.bsky.feed.post",
                                "record": record_payload},
                               token=token)
            log.info("Replied to @%s as %s: %r", author, agent or "generic", reply_text[:80])
            replied += 1
        except Exception as e:
            log.warning("Post reply failed for @%s: %s", author, e)

    save_seen(seen)
    log.info("bsky_engage done: %d replies sent", replied)
    print(f"Done: {replied} replies sent")

if __name__ == "__main__":
    run()
