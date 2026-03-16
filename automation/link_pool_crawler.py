#!/usr/bin/env python3
"""
Link pool crawler — weekly Monday 02:00
Fetches URLs from seed sitemaps, stores live links for article injection.
"""

import gzip
import hashlib
import json
import logging
import random
import re
import sqlite3
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

DB_PATH    = Path(__file__).parent / "disability_findings.db"
LOG_PATH   = Path("/srv/data/openclaw/workspaces/ops/disability-ai-collective/automation/link_pool_crawler.log")
UA         = "Mozilla/5.0 (compatible; CripMinds/1.0)"
TIMEOUT    = 10
MAX_BODY   = 60_000   # bytes read per GET
RECHECK_PCT = 0.10    # re-validate 10% of existing URLs per run

SEED_SITES = [
    {"domain": "scientias.nl",         "sitemap": "https://scientias.nl/sitemap.xml",              "max_urls": 2000},
    {"domain": "vpro.nl",              "sitemap": "https://www.vpro.nl/sitemap.xml",                "max_urls": 2000},
    {"domain": "jstor.org",            "sitemap": "https://www.jstor.org/sitemap.xml",              "max_urls": 500},
    {"domain": "puppetmastermagazine.net","sitemap":"https://www.puppetmastermagazine.net/sitemap.xml","max_urls":2000},
    # vanabbemuseum.nl: returns HTML at /sitemap.xml (bot-blocked), removed 2026-03-16
    {"domain": "mediamatic.net",       "sitemap": "https://www.mediamatic.net/sitemap.xml",         "max_urls": 2000},
    {"domain": "aeon.co",              "sitemap": "https://assets.aeon.co/sitemaps/aeon/main.xml",  "max_urls": 300, "gzip": True, "sleep": 4},
]

TOPIC_KEYWORDS = {
    "art":        ["art", "artist", "gallery", "exhibition", "museum", "painting", "sculpture", "installation"],
    "design":     ["design", "architecture", "building", "urban", "infrastructure", "spatial"],
    "science":    ["research", "study", "brain", "cognitive", "neuroscience", "data", "experiment"],
    "culture":    ["culture", "cultural", "film", "music", "book", "literature", "theatre", "performance"],
    "ecology":    ["ecology", "environment", "climate", "nature", "species", "planet"],
    "activism":   ["protest", "movement", "rights", "justice", "policy", "law", "disability", "access"],
    "theory":     ["theory", "philosophy", "critique", "analysis", "epistemology", "feminist"],
    "technology": ["technology", "digital", "software", "algorithm", "AI", "interface", "media"],
}

logging.basicConfig(
    filename=str(LOG_PATH),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("link_pool")


def url_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS link_pool (
            id              TEXT PRIMARY KEY,
            url             TEXT NOT NULL UNIQUE,
            title           TEXT,
            domain          TEXT NOT NULL,
            tags            TEXT,
            topic           TEXT,
            is_alive        INTEGER DEFAULT 1,
            last_checked    TEXT,
            discovered_date TEXT,
            source_sitemap  TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_lp_alive  ON link_pool(is_alive)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_lp_domain ON link_pool(domain)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_lp_topic  ON link_pool(topic)")
    conn.commit()


def fetch_bytes(url: str, decompress: bool = False) -> bytes | None:
    try:
        # No Accept-Encoding header — let servers return plain text so we control decompression
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            raw = r.read()
        if decompress or url.endswith(".gz"):
            try:
                raw = gzip.decompress(raw)
            except Exception:
                pass
        return raw
    except Exception as e:
        log.debug("fetch_bytes failed %s: %s", url, e)
        return None


def extract_sitemap_urls(sitemap_url: str, max_urls: int = 2000, is_gzip: bool = False) -> list[str]:
    """Parse sitemap XML (or sitemap index) and return a list of page URLs."""
    raw = fetch_bytes(sitemap_url, decompress=is_gzip)
    if not raw:
        return []

    # Some servers send gzip even without Accept-Encoding — try decompression before parse
    try:
        raw = gzip.decompress(raw)
    except Exception:
        pass  # Not gzip, use raw as-is

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        log.warning("XML parse error for %s: %s", sitemap_url, e)
        return []

    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    tag = root.tag.lower()

    # Sitemap index — recurse into each child sitemap
    if "sitemapindex" in tag:
        child_urls = []
        for sitemap_el in root.findall("sm:sitemap", ns):
            loc = sitemap_el.find("sm:loc", ns)
            if loc is not None and loc.text:
                child_urls.extend(extract_sitemap_urls(loc.text.strip(), max_urls))
                if len(child_urls) >= max_urls:
                    break
        return child_urls[:max_urls]

    # Regular urlset
    locs = []
    for url_el in root.findall("sm:url", ns):
        loc = url_el.find("sm:loc", ns)
        if loc is not None and loc.text:
            locs.append(loc.text.strip())

    # JSTOR is huge — sample randomly
    if len(locs) > max_urls:
        locs = random.sample(locs, max_urls)
    return locs[:max_urls]


def extract_title_and_snippet(html: bytes) -> tuple[str, str]:
    """Extract <title> and first substantive paragraph text from HTML bytes."""
    text = html.decode("utf-8", errors="replace")
    # Title
    m = re.search(r'<title[^>]*>(.*?)</title>', text, re.IGNORECASE | re.DOTALL)
    title = re.sub(r'<[^>]+>', '', m.group(1)).strip() if m else ""
    title = re.sub(r'\s+', ' ', title)[:200]
    # First good paragraph
    paras = re.findall(r'<p[^>]*>(.*?)</p>', text, re.DOTALL | re.IGNORECASE)
    snippet = ""
    for p in paras:
        clean = re.sub(r'<[^>]+>', '', p).strip()
        clean = re.sub(r'\s+', ' ', clean)
        if len(clean) > 80:
            snippet = clean[:200]
            break
    return title, snippet


def tag_url(title: str, snippet: str) -> tuple[list[str], str]:
    text = f"{title} {snippet}".lower()
    scores = {topic: sum(1 for kw in kws if kw in text) for topic, kws in TOPIC_KEYWORDS.items()}
    tags   = [t for t, s in scores.items() if s > 0]
    primary = max(scores, key=scores.get) if any(scores.values()) else "general"
    return tags, primary


def crawl_site(conn, site: dict) -> tuple[int, int]:
    """Crawl one seed site. Returns (new_urls, updated_urls)."""
    domain       = site["domain"]
    sitemap_url  = site["sitemap"]
    max_urls     = site.get("max_urls", 2000)
    is_gzip      = site.get("gzip", False)

    log.info("Crawling %s (%s)", domain, sitemap_url)
    urls = extract_sitemap_urls(sitemap_url, max_urls, is_gzip)
    if not urls:
        log.warning("No URLs extracted from %s", sitemap_url)
        return 0, 0

    log.info("%s: %d URLs from sitemap", domain, len(urls))
    new_count = updated_count = 0
    sleep_secs = site.get("sleep", 1)
    now = datetime.now(timezone.utc).isoformat()

    for url in urls:
        uid = url_id(url)
        existing = conn.execute("SELECT id FROM link_pool WHERE id = ?", (uid,)).fetchone()
        if existing:
            continue  # already in pool

        try:
            time.sleep(sleep_secs)
            raw = fetch_bytes(url)
            if not raw:
                log.debug("Empty response: %s", url)
                continue

            title, snippet = extract_title_and_snippet(raw[:MAX_BODY])
            tags, topic = tag_url(title, snippet)

            conn.execute("""
                INSERT OR IGNORE INTO link_pool
                    (id, url, title, domain, tags, topic, is_alive, last_checked, discovered_date, source_sitemap)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
            """, (uid, url, title, domain, json.dumps(tags), topic, now, now, sitemap_url))
            conn.commit()
            new_count += 1

        except Exception as e:
            log.warning("Error processing %s: %s", url, e)

    return new_count, updated_count


def revalidate_sample(conn) -> int:
    """HEAD-check a random 10% of existing alive URLs. Mark dead ones."""
    rows = conn.execute("SELECT id, url FROM link_pool WHERE is_alive = 1").fetchall()
    sample = random.sample(rows, max(1, int(len(rows) * RECHECK_PCT))) if rows else []
    dead = 0
    now  = datetime.now(timezone.utc).isoformat()
    for uid, url in sample:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA}, method="HEAD")
            with urllib.request.urlopen(req, timeout=8) as r:
                alive = r.status == 200
        except Exception:
            alive = False
        if not alive:
            conn.execute("UPDATE link_pool SET is_alive = 0, last_checked = ? WHERE id = ?", (now, uid))
            dead += 1
    conn.commit()
    log.info("Revalidation: %d checked, %d marked dead", len(sample), dead)
    return dead


def main():
    log.info("=== link_pool_crawler start ===")
    conn = sqlite3.connect(str(DB_PATH))
    init_db(conn)

    total_new = 0
    for site in SEED_SITES:
        try:
            new, _ = crawl_site(conn, site)
            total_new += new
            log.info("%s: +%d new URLs", site["domain"], new)
        except Exception as e:
            log.error("Site %s failed: %s", site["domain"], e)

    dead = revalidate_sample(conn)
    total = conn.execute("SELECT COUNT(*) FROM link_pool WHERE is_alive = 1").fetchone()[0]
    conn.close()

    log.info("=== done: +%d new, %d dead, %d total alive ===", total_new, dead, total)
    print(f"Done: +{total_new} new URLs, {dead} marked dead, {total} total alive")


if __name__ == "__main__":
    main()
