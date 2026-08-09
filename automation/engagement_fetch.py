#!/usr/bin/env python3
"""
engagement_fetch.py — pulls real reader-engagement data from every channel
this pipeline publishes to, into one queryable table.

WHY THIS EXISTS: see .claude/audience-engagement-tasklist.md, item 1. The
pipeline publishes into a void — nothing anywhere reads back whether an
article actually landed with readers. This is pure data collection, step
one of closing that loop. It deliberately does NOT feed anything back into
generation yet (no weight changes, no persona tuning) — same observation-
before-action discipline as the shadow checks in automation/orchestrator/
review.py. Behavior changes are a separate, later decision once enough data
exists to trust a correlation.

FIVE SOURCES, confirmed working directly against real data on trident before
this script was written (2026-08-09):
  - GoatCounter: self-hosted, storing everything in a plain SQLite file at
    /srv/data/goatcounter/goatcounter.db (not behind an API) — read directly,
    zero auth. Gives pageviews + scroll-depth event counts per path.
  - Google Search Console: uses the existing google-calendar.json service
    account (already used for calendar integration) via an RS256-signed JWT
    bearer token — no new credential. Needs PyJWT + cryptography, both
    already installed on trident (checked: no new pip install required).
    Gives clicks/impressions/ctr/position per URL. Site property is the
    DOMAIN property `sc-domain:cripminds.com`, NOT a URL-prefix property —
    confirmed via a real /sites list call; using the wrong format 403s.
  - Bluesky: app.bsky.feed.getPosts on the PUBLIC, unauthenticated endpoint
    (public.api.bsky.app) — no session/login needed at all for reading
    engagement on public posts.
  - Mastodon: GET /api/v1/statuses/<id> is also public, no token needed.
  - Tumblr: GET /v2/blog/<blog>/posts with just the consumer API key as a
    query param returns note_count — no full OAuth1 signing needed for
    reading (posting does need it — see _tumblr_oauth_header in
    orchestrator/social.py).

SCHEMA: one flat table, source+metric as free text rather than one column
per metric, because the five sources have genuinely different metric sets
and a wide table would be mostly NULL. Multiple snapshots per article over
time are expected and fine (metrics keep changing for days/weeks after
publish) — that's why fetched_at is part of the uniqueness constraint, not
a column to overwrite.

USAGE:
    python3 automation/engagement_fetch.py            # fetch for last 60 days
    python3 automation/engagement_fetch.py --days 14   # shorter window
    python3 automation/engagement_fetch.py --dry-run   # print, don't write
"""
import argparse
import json
import os
import re
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
POSTS_DIR = REPO_ROOT / "_posts"
SOCIAL_DIR = REPO_ROOT / "_social"
DB_PATH = REPO_ROOT / "automation" / "engagement.db"
GOATCOUNTER_DB = Path("/srv/data/goatcounter/goatcounter.db")
GOOGLE_SA_FILE = Path("/srv/secrets/google-calendar.json")
GSC_SITE = "sc-domain:cripminds.com"

# Same manual .env parsing pattern used throughout this codebase (see
# orchestrator/config.py) — no export statements in these files.
for _env_file in [Path("/srv/secrets/openclaw.env"), Path("/srv/secrets/tumblr.env")]:
    if _env_file.exists():
        for _line in _env_file.read_text().splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                os.environ.setdefault(_k.strip(), _v.strip())


def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS engagement_metrics (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            slug       TEXT NOT NULL,
            source     TEXT NOT NULL,
            metric     TEXT NOT NULL,
            value      REAL NOT NULL,
            fetched_at TEXT NOT NULL,
            UNIQUE(slug, source, metric, fetched_at)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_engagement_slug ON engagement_metrics(slug)")
    conn.commit()


def upsert(conn, slug, source, metric, value, fetched_at):
    conn.execute(
        "INSERT OR REPLACE INTO engagement_metrics (slug, source, metric, value, fetched_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (slug, source, metric, value, fetched_at),
    )


def list_recent_articles(days):
    """Returns list of dicts: slug, site_path (e.g. /2026/08/07/one-in-twelve-.../),
    social_json (Path or None). Derived from the post filename via the site's
    own permalink pattern (/:year/:month/:day/:title/, confirmed in _config.yml),
    not guessed."""
    cutoff = datetime.now() - timedelta(days=days)
    out = []
    for f in sorted(POSTS_DIR.glob("*.md")):
        m = re.match(r"^(\d{4})-(\d{2})-(\d{2})-(.+)\.md$", f.name)
        if not m:
            continue
        y, mo, d, slug = m.groups()
        try:
            post_date = datetime(int(y), int(mo), int(d))
        except ValueError:
            continue
        if post_date < cutoff:
            continue
        social_json = SOCIAL_DIR / f"{slug}.json"
        out.append({
            "slug": slug,
            "site_path": f"/{y}/{mo}/{d}/{slug}/",
            "social_json": social_json if social_json.exists() else None,
        })
    return out


def fetch_goatcounter(conn, articles, fetched_at, dry_run):
    if not GOATCOUNTER_DB.exists():
        print(f"GoatCounter DB not found at {GOATCOUNTER_DB} — skipping (expected if not running on trident)")
        return
    gc = sqlite3.connect(f"file:{GOATCOUNTER_DB}?mode=ro", uri=True)
    try:
        for art in articles:
            row = gc.execute(
                "SELECT count(*) FROM hits h JOIN paths p ON h.path_id = p.path_id "
                "WHERE p.event = 0 AND p.path = ?",
                (art["site_path"].rstrip("/"),),
            ).fetchone()
            pageviews = row[0] if row else 0
            if pageviews and not dry_run:
                upsert(conn, art["slug"], "goatcounter", "pageviews", pageviews, fetched_at)
            for depth in (25, 50, 75, 100):
                # NOT .rstrip("/") -- confirmed 2026-08-09 continuation by reading
                # GoatCounter's raw paths table directly: automatic pageview hits
                # (event=0, queried above) are stored WITHOUT a trailing slash, but
                # custom events (event=1, this site's own scroll-depth tracker in
                # _layouts/default.html) are stored with whatever location.pathname
                # gave it -- which always has the trailing slash for this site's
                # /:year/:month/:day/:title/ permalinks. Stripping it here made
                # every scroll-depth lookup silently match zero rows since this
                # script's first commit (3c1e478) -- confirmed via a live query,
                # zero scroll_* rows ever existed in engagement.db despite pageviews
                # working the whole time. Also added depth 100, tracked by the site's
                # JS (`marks = {25,50,75,100}`) but never queried here before.
                row = gc.execute(
                    "SELECT count(*) FROM hits h JOIN paths p ON h.path_id = p.path_id "
                    "WHERE p.event = 1 AND p.path = ?",
                    (f"scroll-{depth}:{art['site_path']}",),
                ).fetchone()
                n = row[0] if row else 0
                if n and not dry_run:
                    upsert(conn, art["slug"], "goatcounter", f"scroll_{depth}", n, fetched_at)
            if dry_run and pageviews:
                print(f"  [goatcounter] {art['slug']}: pageviews={pageviews}")
    finally:
        gc.close()


def _gsc_access_token():
    import jwt  # PyJWT — confirmed already installed on trident, no new dependency
    sa = json.loads(GOOGLE_SA_FILE.read_text())
    now = int(time.time())
    claim = {
        "iss": sa["client_email"],
        "scope": "https://www.googleapis.com/auth/webmasters.readonly",
        "aud": "https://oauth2.googleapis.com/token",
        "iat": now,
        "exp": now + 3600,
    }
    assertion = jwt.encode(claim, sa["private_key"], algorithm="RS256")
    data = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": assertion,
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp)["access_token"]


def fetch_gsc(conn, articles, fetched_at, dry_run):
    if not GOOGLE_SA_FILE.exists():
        print(f"GSC service account not found at {GOOGLE_SA_FILE} — skipping")
        return
    try:
        token = _gsc_access_token()
    except Exception as e:
        print(f"GSC auth failed: {e}")
        return
    site = urllib.parse.quote(GSC_SITE, safe="")
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    req = urllib.request.Request(
        f"https://www.googleapis.com/webmasters/v3/sites/{site}/searchAnalytics/query",
        data=json.dumps({
            "startDate": start, "endDate": end, "dimensions": ["page"], "rowLimit": 5000,
        }).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.load(resp)
    except Exception as e:
        print(f"GSC query failed: {e}")
        return
    by_path = {}
    for row in result.get("rows", []):
        url = row["keys"][0]
        path = urllib.parse.urlparse(url).path
        by_path[path] = row
    for art in articles:
        row = by_path.get(art["site_path"])
        if not row:
            continue
        if dry_run:
            print(f"  [gsc] {art['slug']}: clicks={row['clicks']} impressions={row['impressions']} ctr={row['ctr']:.3f}")
            continue
        upsert(conn, art["slug"], "gsc", "clicks", row["clicks"], fetched_at)
        upsert(conn, art["slug"], "gsc", "impressions", row["impressions"], fetched_at)
        upsert(conn, art["slug"], "gsc", "ctr", row["ctr"], fetched_at)
        upsert(conn, art["slug"], "gsc", "position", row["position"], fetched_at)


def fetch_bluesky(conn, articles, fetched_at, dry_run):
    uris = []
    for art in articles:
        if not art["social_json"]:
            continue
        try:
            data = json.loads(art["social_json"].read_text())
        except Exception:
            continue
        uri = data.get("bsky_uri")
        if uri:
            uris.append((art["slug"], uri))
    if not uris:
        return
    # getPosts takes up to 25 URIs per call
    for i in range(0, len(uris), 25):
        batch = uris[i:i + 25]
        params = "&".join(f"uris={urllib.parse.quote(u, safe='')}" for _, u in batch)
        req = urllib.request.Request(
            f"https://public.api.bsky.app/xrpc/app.bsky.feed.getPosts?{params}"
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.load(resp)
        except Exception as e:
            print(f"Bluesky fetch failed for batch: {e}")
            continue
        by_uri = {p["uri"]: p for p in result.get("posts", [])}
        for slug, uri in batch:
            post = by_uri.get(uri)
            if not post:
                continue
            if dry_run:
                print(f"  [bluesky] {slug}: likes={post.get('likeCount', 0)} reposts={post.get('repostCount', 0)}")
                continue
            for metric, key in (("likes", "likeCount"), ("reposts", "repostCount"),
                                 ("replies", "replyCount"), ("quotes", "quoteCount")):
                upsert(conn, slug, "bluesky", metric, post.get(key, 0), fetched_at)


def fetch_mastodon(conn, articles, fetched_at, dry_run):
    for art in articles:
        if not art["social_json"]:
            continue
        try:
            data = json.loads(art["social_json"].read_text())
        except Exception:
            continue
        url = data.get("mastodon_url")
        if not url:
            continue
        m = re.search(r"/(\d+)$", url)
        if not m:
            continue
        status_id = m.group(1)
        instance = urllib.parse.urlparse(url).netloc
        req = urllib.request.Request(f"https://{instance}/api/v1/statuses/{status_id}")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                post = json.load(resp)
        except Exception as e:
            print(f"Mastodon fetch failed for {art['slug']}: {e}")
            continue
        if dry_run:
            print(f"  [mastodon] {art['slug']}: favourites={post.get('favourites_count', 0)} reblogs={post.get('reblogs_count', 0)}")
            continue
        for metric, key in (("favourites", "favourites_count"), ("reblogs", "reblogs_count"),
                             ("replies", "replies_count")):
            upsert(conn, art["slug"], "mastodon", metric, post.get(key, 0), fetched_at)


def fetch_tumblr(conn, articles, fetched_at, dry_run):
    api_key = os.environ.get("TUMBLR_CONSUMER_KEY", "")
    blog = os.environ.get("TUMBLR_BLOG", "").strip().rstrip(".tumblr.com")
    if not api_key or not blog:
        print("Tumblr: no credentials loaded — skipping")
        return
    by_url = {}
    for art in articles:
        if not art["social_json"]:
            continue
        try:
            data = json.loads(art["social_json"].read_text())
        except Exception:
            continue
        url = data.get("tumblr_url")
        if url:
            by_url[url] = art["slug"]
    if not by_url:
        return
    # Fetch recent posts once (paginated) rather than one call per post — Tumblr's
    # posts endpoint doesn't support lookup by URL directly.
    offset = 0
    remaining = dict(by_url)
    while remaining and offset < 200:
        req = urllib.request.Request(
            f"https://api.tumblr.com/v2/blog/{blog}/posts?api_key={api_key}&limit=20&offset={offset}"
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                posts = json.load(resp).get("response", {}).get("posts", [])
        except Exception as e:
            print(f"Tumblr fetch failed: {e}")
            break
        if not posts:
            break
        for post in posts:
            url = post.get("post_url")
            slug = remaining.pop(url, None)
            if slug:
                if dry_run:
                    print(f"  [tumblr] {slug}: notes={post.get('note_count', 0)}")
                else:
                    upsert(conn, slug, "tumblr", "notes", post.get("note_count", 0), fetched_at)
        offset += 20


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=60, help="how many days back to check articles for")
    parser.add_argument("--dry-run", action="store_true", help="print what would be recorded, write nothing")
    args = parser.parse_args()

    articles = list_recent_articles(args.days)
    print(f"Checking engagement for {len(articles)} article(s) from the last {args.days} days")

    conn = None if args.dry_run else sqlite3.connect(DB_PATH)
    if conn:
        init_db(conn)
    fetched_at = datetime.now().strftime("%Y-%m-%d")

    fetch_goatcounter(conn, articles, fetched_at, args.dry_run)
    fetch_gsc(conn, articles, fetched_at, args.dry_run)
    fetch_bluesky(conn, articles, fetched_at, args.dry_run)
    fetch_mastodon(conn, articles, fetched_at, args.dry_run)
    fetch_tumblr(conn, articles, fetched_at, args.dry_run)

    if conn:
        conn.commit()
        n = conn.execute("SELECT count(*) FROM engagement_metrics WHERE fetched_at = ?", (fetched_at,)).fetchone()[0]
        print(f"Wrote {n} metric row(s) for {fetched_at} to {DB_PATH}")
        conn.close()


if __name__ == "__main__":
    main()
