#!/usr/bin/env python3
"""
News fetcher — daily quality journalism RSS scraper for article grounding.

Fetches RSS from curated quality sources, scores items for thematic relevance,
stores in news_seeds table, extracts disability angles for top candidates via LLM.

Cron: 0 6 * * *  (runs before run_discovery.py at 07:00, generation at 09:00)
Usage: python3 automation/news_fetcher.py
"""
import os, sys, json, re, sqlite3, hashlib, time, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path
from email.utils import parsedate_to_datetime

# ── Env / paths ───────────────────────────────────────────────────────────────

_ENV_FILE = Path("/srv/secrets/openclaw.env")
if _ENV_FILE.exists():
    for _line in _ENV_FILE.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

REPO = Path(__file__).parent.parent
DB   = REPO / "disability_findings.db"
LOG  = REPO / "automation" / "news_fetcher.log"

API_URL = "http://172.19.0.1:8317/v1/chat/completions"
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL   = "claude-sonnet-4-6"

# ── Feed list ─────────────────────────────────────────────────────────────────
# Tier 1 = quality longform journalism / science. Tier 2 = broad quality.
# Feeds already in feeds.json are included here too — news_fetcher fetches
# independently for persistence; no live-at-generation race condition.

QUALITY_FEEDS = [
    # ── Science & nature ──────────────────────────────────────────────────────
    {"url": "https://www.nature.com/nature.rss",                        "name": "Nature",                "tier": 1},
    {"url": "https://www.newscientist.com/feed/home/",                  "name": "New Scientist",         "tier": 1},
    {"url": "https://nautil.us/feed/",                                  "name": "Nautilus",              "tier": 1},
    {"url": "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml", "name": "NYT Science",           "tier": 1},

    # ── Technology & design ───────────────────────────────────────────────────
    {"url": "https://www.technologyreview.com/feed/",                   "name": "MIT Tech Review",       "tier": 1},
    {"url": "https://hnrss.org/frontpage",                              "name": "Hacker News",           "tier": 1},
    {"url": "https://www.wired.com/feed/rss",                           "name": "Wired",                 "tier": 2},
    {"url": "https://404media.co/feed/",                                "name": "404 Media",             "tier": 2},
    {"url": "https://www.theverge.com/rss/index.xml",                   "name": "The Verge",             "tier": 2},

    # ── Art, design & architecture ────────────────────────────────────────────
    {"url": "https://hyperallergic.com/feed/",                          "name": "Hyperallergic",         "tier": 1},
    {"url": "https://www.dezeen.com/feed/",                             "name": "Dezeen",                "tier": 1},
    {"url": "https://www.theguardian.com/artanddesign/rss",             "name": "Guardian Art & Design", "tier": 1},
    {"url": "https://rss.nytimes.com/services/xml/rss/nyt/Arts.xml",    "name": "NYT Arts",              "tier": 2},

    # ── Society, disability & cities ──────────────────────────────────────────
    {"url": "https://www.theguardian.com/society/rss",                  "name": "Guardian Society",      "tier": 1},
    {"url": "https://www.theguardian.com/cities/rss",                   "name": "Guardian Cities",       "tier": 1},
    {"url": "https://www.disabilitynewsservice.com/feed/",              "name": "Disability News Service","tier": 1},
    {"url": "https://jacobin.com/feed/",                                "name": "Jacobin",               "tier": 2},

    # ── Culture & longform ────────────────────────────────────────────────────
    {"url": "https://aeon.co/feed.rss",                                 "name": "Aeon",                  "tier": 1},
    {"url": "https://theconversation.com/articles.atom",                "name": "The Conversation",      "tier": 1},
    {"url": "https://www.theatlantic.com/feed/all/",                    "name": "The Atlantic",          "tier": 1},
    {"url": "https://www.newstatesman.com/feed",                        "name": "New Statesman",         "tier": 2},
    {"url": "https://www.economist.com/science-and-technology/rss.xml", "name": "Economist Sci-Tech",    "tier": 1},
    {"url": "https://www.economist.com/culture/rss.xml",                "name": "Economist Culture",     "tier": 1},
    {"url": "https://www.groene.nl/rss.xml",                            "name": "De Groene Amsterdammer","tier": 2},

    # ── International quality ─────────────────────────────────────────────────
    {"url": "https://www.nrc.nl/rss/",                                  "name": "NRC Handelsblad",       "tier": 1},
    {"url": "https://www.lemonde.fr/en/rss/une.xml",                    "name": "Le Monde English",      "tier": 1},
    {"url": "https://elpais.com/rss/elpais/inenglish.xml",              "name": "El Pais English",       "tier": 2},
    {"url": "https://www.theguardian.com/world/rss",                    "name": "Guardian World",        "tier": 2},
]

# ── Relevance scoring ─────────────────────────────────────────────────────────

THEME_KEYWORDS = {
    "architecture":   ["architecture","building","design","urban","housing","planning",
                       "infrastructure","public space","construction","zoning","facade",
                       "interior","spatial","acoustics","museum","gallery","pavilion"],
    "technology":     ["AI","algorithm","interface","software","digital","automation",
                       "robot","sensor","wearable","assistive","app","machine learning",
                       "neural","hardware","platform","code","computing","data"],
    "art_culture":    ["art","artist","gallery","exhibition","museum","film","theatre",
                       "music","performance","festival","curator","cinema","dance",
                       "craft","fiction","novel","poetry","photography","sculpture"],
    "science_nature": ["research","study","brain","cognition","biology","evolution",
                       "ecology","species","perception","sensory","neuroscience",
                       "genetics","climate","physics","chemistry","medicine"],
    "language":       ["language","translation","sign","communication","literacy",
                       "notation","reading","writing","grammar","linguistic","dialect",
                       "caption","subtitle","text","speech","voice"],
    "business_labor": ["work","employment","labor","gig","salary","hiring","economy",
                       "productivity","care work","burnout","workplace","union",
                       "remote","office","job","career","wage","contract"],
    "health_systems": ["hospital","NHS","healthcare","insurance","diagnosis","treatment",
                       "mental health","therapy","care","patient","clinic","medicine",
                       "pharmaceutical","drug","surgery","chronic"],
    "education":      ["school","university","student","curriculum","learning","classroom",
                       "exam","teaching","pedagogy","literacy","degree","college"],
}

# Items mentioning these get a +0.3 boost — explicit disability lens
DISABILITY_BOOSTERS = [
    "disability","disabled","accessible","accessibility","wheelchair","deaf","blind",
    "autistic","neurodivergent","chronic illness","inclusive design","universal design",
    "assistive","impairment","barrier","accommodation","sign language","braille",
    "screen reader","caption","crip","spinal","mobility","invisible disability",
]

# Theme → preferred persona for agent selection
THEME_TO_PERSONA = {
    "architecture":   "Pixel Nova",
    "art_culture":    "Pixel Nova",
    "technology":     "Zen Circuit",
    "science_nature": "Zen Circuit",
    "language":       "Siri Sage",
    "health_systems": "Maya Flux",
    "business_labor": "Maya Flux",
    "education":      "Siri Sage",
}


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


# ── DB ────────────────────────────────────────────────────────────────────────

def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS news_seeds (
            id               TEXT PRIMARY KEY,
            url              TEXT NOT NULL UNIQUE,
            title            TEXT NOT NULL,
            summary          TEXT,
            source_name      TEXT NOT NULL,
            source_tier      INTEGER DEFAULT 2,
            pub_date         TEXT,
            fetched_date     TEXT NOT NULL,
            relevance_score  REAL DEFAULT 0.0,
            themes           TEXT,
            disability_angle TEXT,
            used             INTEGER DEFAULT 0,
            used_date        TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ns_score   ON news_seeds(relevance_score)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ns_used    ON news_seeds(used)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ns_pub     ON news_seeds(pub_date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ns_fetched ON news_seeds(fetched_date)")
    conn.commit()


def url_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def store_seed(conn, item: dict) -> bool:
    """Store a scored item. Returns True if new, False if duplicate."""
    try:
        conn.execute("""
            INSERT INTO news_seeds
              (id, url, title, summary, source_name, source_tier, pub_date,
               fetched_date, relevance_score, themes, disability_angle, used)
            VALUES (?,?,?,?,?,?,?,?,?,?,NULL,0)
        """, (
            url_id(item["url"]),
            item["url"],
            item["title"],
            item.get("summary", ""),
            item["source_name"],
            item["source_tier"],
            item.get("pub_date"),
            datetime.now().strftime("%Y-%m-%d"),
            item["relevance_score"],
            json.dumps(item.get("themes", [])),
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def prune_old(conn, days: int = 14):
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    cur = conn.execute(
        "DELETE FROM news_seeds WHERE fetched_date < ? AND used = 0", (cutoff,)
    )
    conn.commit()
    if cur.rowcount:
        log(f"Pruned {cur.rowcount} old unused seeds (>{days}d)")


# ── RSS fetch ─────────────────────────────────────────────────────────────────

def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text or "").strip()


def _parse_dt(s: str) -> datetime:
    if not s:
        return datetime.now(timezone.utc)
    for fn in (
        lambda x: parsedate_to_datetime(x),
        lambda x: datetime.fromisoformat(x.rstrip("Z")).replace(tzinfo=timezone.utc),
        lambda x: datetime.strptime(x[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc),
    ):
        try:
            dt = fn(s)
            return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
        except Exception:
            pass
    return datetime.now(timezone.utc)


def fetch_feed(feed: dict, days: int = 7) -> list[dict]:
    """Fetch one RSS/Atom feed, return items newer than `days`."""
    url = feed["url"]
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    ATOM_NS = "http://www.w3.org/2005/Atom"
    items = []
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "CripMinds/2.0 (+https://cripminds.com)"},
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            raw = r.read()
        root = ET.fromstring(raw)

        # RSS 2.0
        for item in root.findall(".//item"):
            title   = _strip_html(item.findtext("title", ""))[:200]
            link    = (item.findtext("link") or "").strip()
            summary = _strip_html(item.findtext("description", ""))[:500]
            dt      = _parse_dt(item.findtext("pubDate", ""))
            if dt >= cutoff and title and link:
                items.append({
                    "title": title, "url": link, "summary": summary,
                    "pub_date": dt.strftime("%Y-%m-%d"),
                    "source_name": feed["name"], "source_tier": feed["tier"],
                })

        # Atom
        ns = {"a": ATOM_NS}
        for entry in root.findall("a:entry", ns):
            title = _strip_html(
                entry.findtext("a:title", "", ns) or entry.findtext("title", "")
            )[:200]
            link_el = entry.find("a:link[@rel='alternate']", ns)
            if link_el is None:
                link_el = entry.find("a:link", ns)
            if link_el is None:
                link_el = entry.find("link")
            link    = (link_el.get("href", "") if link_el is not None else "").strip()
            summary = _strip_html(
                entry.findtext("a:summary", "", ns)
                or entry.findtext("a:content", "", ns)
                or entry.findtext("summary", "")
            )[:500]
            dt = _parse_dt(
                entry.findtext("a:updated", "", ns)
                or entry.findtext("a:published", "", ns)
                or entry.findtext("updated", "")
            )
            if dt >= cutoff and title and link:
                items.append({
                    "title": title, "url": link, "summary": summary,
                    "pub_date": dt.strftime("%Y-%m-%d"),
                    "source_name": feed["name"], "source_tier": feed["tier"],
                })

    except Exception as e:
        log(f"  Feed skipped ({feed['name']}): {e}")

    return items


def fetch_all_feeds(days: int = 7) -> list[dict]:
    """Fetch all QUALITY_FEEDS, deduplicate by URL, return flat list."""
    seen_urls = set()
    all_items = []
    for feed in QUALITY_FEEDS:
        items = fetch_feed(feed, days=days)
        for item in items:
            if item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                all_items.append(item)
    log(f"Fetched {len(all_items)} unique items from {len(QUALITY_FEEDS)} feeds")
    return all_items


# ── Relevance scoring ─────────────────────────────────────────────────────────

def _keyword_matches(text: str, words: set[str], keyword: str) -> bool:
    kw = keyword.lower()
    if len(kw) < 4:
        return kw in words
    return kw in text


def score_item(item: dict) -> tuple[float, list[str]]:
    """Return (relevance_score 0-1, matched_themes list)."""
    text = f"{item['title']} {item.get('summary', '')}".lower()
    words = set(re.findall(r"\b\w+\b", text))

    theme_hits: dict[str, int] = {}
    for theme, keywords in THEME_KEYWORDS.items():
        hits = sum(1 for kw in keywords if _keyword_matches(text, words, kw))
        if hits:
            theme_hits[theme] = hits

    base = min(sum(theme_hits.values()) / 8.0, 0.7) if theme_hits else 0.0
    boost = 0.3 if any(_keyword_matches(text, words, kw) for kw in DISABILITY_BOOSTERS) else 0.0
    matched = sorted(theme_hits, key=theme_hits.get, reverse=True)
    return round(min(base + boost, 1.0), 3), matched


def title_already_seen(conn, title: str, days: int = 7) -> bool:
    """Jaccard similarity check — reject near-duplicate titles."""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    rows = conn.execute(
        "SELECT title FROM news_seeds WHERE fetched_date >= ?", (cutoff,)
    ).fetchall()
    if not rows:
        return False
    words_new = set(re.findall(r"\b\w{4,}\b", title.lower()))
    if not words_new:
        return False
    for (existing,) in rows:
        words_ex = set(re.findall(r"\b\w{4,}\b", existing.lower()))
        union = words_new | words_ex
        if not union:
            continue
        jaccard = len(words_new & words_ex) / len(union)
        if jaccard > 0.7:
            return True
    return False


# ── LLM angle extraction ──────────────────────────────────────────────────────

def extract_angle(title: str, summary: str, url: str) -> str | None:
    """Ask Sonnet to find the hidden disability angle. Returns angle or None."""
    if not API_KEY:
        return None

    system = (
        "You find hidden disability angles in mainstream journalism. "
        "Your job: read a mainstream article and identify what a disabled person "
        "— a blind architect, a deaf designer, a wheelchair user, an autistic pattern analyst — "
        "would notice that non-disabled readers miss.\n\n"
        "Look for:\n"
        "- Design decisions that exclude without realising it\n"
        "- Paradigms or assumptions that privilege non-disabled ways of knowing\n"
        "- Stereotypes or microaggressions embedded in language or framing\n"
        "- Deaf gain, autistic cognition, or crip wisdom the article unknowingly illustrates\n"
        "- Moments where disability expertise would reframe the entire argument\n"
        "- Invisible labour, care work, or interdependence the mainstream lens erases\n\n"
        "This is NOT about what the article says about disability. "
        "It is about what disability culture and theory would see inside it.\n\n"
        "Reply with ONE sharp sentence describing the angle, written as an essay pitch. "
        "If the article has no meaningful hidden angle, reply exactly: NONE"
    )
    user = (
        f"Article: {title}\nSource: {url}\nSummary: {summary}\n\n"
        "What is the hidden disability angle in this mainstream article?"
    )
    payload = json.dumps({
        "model": MODEL,
        "max_tokens": 120,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        "stream": False,
    }).encode()
    try:
        req = urllib.request.Request(
            API_URL, data=payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.loads(r.read())
        angle = resp["choices"][0]["message"]["content"].strip()
        angle = re.sub(r"<think>.*?</think>", "", angle, flags=re.DOTALL).strip()
        if angle.upper().startswith("NONE") or len(angle) < 15:
            return None
        return angle
    except Exception as e:
        log(f"  LLM extraction failed: {e}")
        return None


def extract_top_angles(conn, n: int = 10):
    """Fetch top-N unprocessed seeds by score and extract disability angles."""
    if not API_KEY:
        log("ANTHROPIC_API_KEY not set — skipping angle extraction")
        return
    rows = conn.execute("""
        SELECT id, url, title, summary FROM news_seeds
        WHERE disability_angle IS NULL AND used = 0
        ORDER BY relevance_score DESC
        LIMIT ?
    """, (n,)).fetchall()
    extracted = 0
    for seed_id, url, title, summary in rows:
        angle = extract_angle(title, summary or "", url)
        if angle:
            conn.execute(
                "UPDATE news_seeds SET disability_angle = ? WHERE id = ?",
                (angle, seed_id),
            )
            conn.commit()
            log(f"  + angle: {title[:50]} → {angle[:70]}")
            extracted += 1
        time.sleep(0.5)
    log(f"Angle extraction done: {extracted}/{len(rows)} got angles")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log("=== news_fetcher start ===")
    conn = sqlite3.connect(str(DB))
    init_db(conn)

    # 1. Fetch all feeds
    raw_items = fetch_all_feeds(days=7)

    # 2. Score, deduplicate, store items above threshold
    stored = skipped_score = skipped_dupe = 0
    MIN_SCORE = 0.15
    for item in raw_items:
        score, themes = score_item(item)
        if score < MIN_SCORE:
            skipped_score += 1
            continue
        item["relevance_score"] = score
        item["themes"] = themes
        if title_already_seen(conn, item["title"]):
            skipped_dupe += 1
            continue
        if store_seed(conn, item):
            stored += 1

    log(f"Stored {stored} new seeds | skipped {skipped_score} low-score | {skipped_dupe} near-dupe")

    # 3. LLM angle extraction for top candidates
    if API_KEY:
        extract_top_angles(conn, n=10)
    else:
        log("ANTHROPIC_API_KEY not set — skipping angle extraction")

    # 4. Prune old unused seeds
    prune_old(conn, days=14)

    # Summary
    total, unused, with_angle = conn.execute(
        "SELECT COUNT(*), SUM(CASE WHEN used=0 THEN 1 ELSE 0 END), "
        "SUM(CASE WHEN disability_angle IS NOT NULL AND used=0 THEN 1 ELSE 0 END) "
        "FROM news_seeds"
    ).fetchone()
    conn.close()
    log(f"DB: {total} total seeds | {unused} unused | {with_angle} with angle")
    log("=== news_fetcher done ===")


if __name__ == "__main__":
    main()
