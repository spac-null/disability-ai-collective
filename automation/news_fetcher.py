#!/usr/bin/env python3
"""
News fetcher — daily quality journalism RSS scraper for article grounding.

Fetches RSS from curated quality sources, scores items for thematic relevance,
stores in news_seeds table, extracts disability angles for top candidates via LLM.

Cron: 0 6 * * *  (runs before run_discovery.py at 07:00, generation at 09:00)
Usage: python3 automation/news_fetcher.py
"""
import sys, os, json, re, sqlite3, hashlib, time, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path
from email.utils import parsedate_to_datetime

# ── Env / paths ───────────────────────────────────────────────────────────────

REPO = Path(__file__).parent.parent
DB   = REPO / "disability_findings.db"
LOG  = REPO / "automation" / "news_fetcher.log"

# Load CLIPROXY_KEY from the same secrets file production_orchestrator.py uses
# (no export statements — parse manually, same pattern as that file).
_ENV_FILE = Path("/srv/secrets/openclaw.env")
if _ENV_FILE.exists():
    for _line in _ENV_FILE.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

# CLIProxy — same endpoint production_orchestrator.py uses for all editorial LLM
# calls. news_fetcher previously called Nous Portal directly via a Hermes-managed
# OAuth agent_key (/srv/data/hermes/auth.json); that key stopped being refreshed
# on 2026-05-16 when the rest of the pipeline migrated to OpenRouter/CLIProxy,
# leaving angle extraction silently 401ing for two months.
API_URL = "http://127.0.0.1:8317/v1/chat/completions"
API_KEY = os.environ.get("CLIPROXY_KEY", "")
MODEL   = "openrouter/claude-sonnet-4.6"

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
    # Hacker News re-added 2026-08-09 continuation, explicit request, despite the
    # original removal reasoning below (link aggregator, arbitrary/clickbait-prone
    # titles) -- kept for visibility, not endorsement; expect noisier candidates
    # out of this feed than the curated journalism sources around it.
    {"url": "https://news.ycombinator.com/rss",                         "name": "Hacker News",           "tier": 2},
    {"url": "https://www.techmeme.com/feed.xml",                        "name": "Techmeme",              "tier": 2},
    {"url": "https://restofworld.org/feed/latest/full",                 "name": "Rest of World",         "tier": 1},
    {"url": "https://www.wired.com/feed/rss",                           "name": "Wired",                 "tier": 2},
    # 404 Media re-added 2026-08-10 -- the "network-level block" from its prior
    # removal was actually DNS poisoning on trident's WiFi/default-route
    # resolver (192.168.1.1, router/ISP-side Whalebone filtering), not a real
    # block on the domain: confirmed via `dig @1.1.1.1`/`@8.8.8.8` returning
    # real Fastly IPs while trident's default resolver returned a single
    # sinkhole IP with a fake "Whalebone Sinkhole CA" cert. Fixed at the host
    # level (systemd-resolved + NetworkManager profile now point wlo1 at
    # 1.1.1.1/8.8.8.8), not with a third-party proxy service -- verified real
    # cert (Certainly CA), HTTP 200, valid RSS content post-fix.
    {"url": "https://www.404media.co/rss/",                             "name": "404 Media",             "tier": 1},
    {"url": "https://www.theverge.com/rss/index.xml",                   "name": "The Verge",             "tier": 2},

    # ── Art, design & architecture ────────────────────────────────────────────
    {"url": "https://hyperallergic.com/feed/",                          "name": "Hyperallergic",         "tier": 1},
    {"url": "https://www.dezeen.com/feed/",                             "name": "Dezeen",                "tier": 1},
    {"url": "https://www.theguardian.com/artanddesign/rss",             "name": "Guardian Art & Design", "tier": 1},
    {"url": "https://rss.nytimes.com/services/xml/rss/nyt/Arts.xml",    "name": "NYT Arts",              "tier": 2},
    {"url": "https://www.creativeboom.com/feed/",                       "name": "Creative Boom",         "tier": 1},
    {"url": "https://thecreativeindependent.com/feed.xml",              "name": "The Creative Independent","tier": 1},
    {"url": "https://www.lemonde.fr/en/arts/rss_full.xml",              "name": "Le Monde Arts",         "tier": 2},

    # ── Society, disability & cities ──────────────────────────────────────────
    {"url": "https://www.theguardian.com/society/rss",                  "name": "Guardian Society",      "tier": 1},
    {"url": "https://www.theguardian.com/cities/rss",                   "name": "Guardian Cities",       "tier": 1},
    {"url": "https://www.disabilitynewsservice.com/feed/",              "name": "Disability News Service","tier": 1},
    {"url": "https://jacobin.com/feed/",                                "name": "Jacobin",               "tier": 2},
    {"url": "https://disabilityarts.online/feed/",                      "name": "Disability Arts Online", "tier": 1},
    {"url": "https://cripnews.substack.com/feed",                       "name": "Crip News",             "tier": 1},
    {"url": "https://www.disabilitydebrief.org/feed",                   "name": "Disability Debrief",    "tier": 2},
    {"url": "https://rootedinrights.org/feed/",                         "name": "Rooted in Rights",      "tier": 2},
    # Two added 2026-08-09 continuation -- Deaf-specific and disability-culture-
    # specific respectively, filling a real gap: nothing above covers Deaf
    # community writing directly, and DVP is disability CULTURE/politics/media,
    # a different register than the policy/admin-heavy DNS/Guardian Society beat.
    {"url": "https://limpingchicken.com/feed/",                         "name": "The Limping Chicken",   "tier": 1},
    {"url": "https://disabilityvisibilityproject.com/feed/",            "name": "Disability Visibility Project","tier": 1},

    # ── Behavioural science, progress & historical reassessment ───────────────
    # Bregman-vein material: counterintuitive social science, archival reappraisal,
    # progress-studies-style argument grounded in data. None publish daily; several
    # will return zero items on most runs at the days=7 cutoff — expected, not a bug.
    # Paired with the behavioral_science/history_archive THEME_KEYWORDS buckets added
    # 2026-08-07 — without those, items from these feeds score 0.0 and are silently
    # discarded before angle-extraction ever sees them (verified live).
    {"url": "https://psyche.co/feed.rss",                               "name": "Psyche",                "tier": 1},
    {"url": "https://www.worksinprogress.news/feed",                    "name": "Works in Progress",     "tier": 1},
    {"url": "https://asteriskmag.com/feed",                             "name": "Asterisk",              "tier": 1},
    {"url": "https://behavioralscientist.org/feed/",                    "name": "Behavioral Scientist",  "tier": 1},
    {"url": "https://www.nature.com/nathumbehav.rss",                   "name": "Nature Human Behaviour","tier": 1},
    {"url": "https://daily.jstor.org/feed/",                            "name": "JSTOR Daily",           "tier": 1},
    {"url": "https://publicdomainreview.org/rss.xml",                   "name": "Public Domain Review",  "tier": 2},
    {"url": "https://www.vox.com/rss/future-perfect/index.xml",         "name": "Vox Future Perfect",    "tier": 2},
    {"url": "https://www.smithsonianmag.com/rss/latest_articles/",      "name": "Smithsonian Magazine",  "tier": 2},
    {"url": "https://www.atlasobscura.com/feeds/latest",                "name": "Atlas Obscura",         "tier": 2},
    # Very low cadence (roughly monthly) but genuinely active and right register —
    # narrative true-story pieces, not trivia lists. Real feed is on FeedBurner; the
    # site's own /feeds/ path returns the HTML homepage, not XML.
    {"url": "https://feeds.feedburner.com/damninteresting/all",         "name": "Damn Interesting",      "tier": 2},

    # ── Culture & longform ────────────────────────────────────────────────────
    {"url": "https://aeon.co/feed.rss",                                 "name": "Aeon",                  "tier": 1},
    {"url": "https://theconversation.com/articles.atom",                "name": "The Conversation",      "tier": 1},
    {"url": "https://www.theatlantic.com/feed/all/",                    "name": "The Atlantic",          "tier": 1},
    # New Statesman removed — 403 to both the crawler UA and a browser UA since
    # at least 2026-07-30, live-reconfirmed 2026-08-06.
    {"url": "https://www.economist.com/science-and-technology/rss.xml", "name": "Economist Sci-Tech",    "tier": 1},
    {"url": "https://www.economist.com/culture/rss.xml",                "name": "Economist Culture",     "tier": 1},
    {"url": "https://www.groene.nl/rss.xml",                            "name": "De Groene Amsterdammer","tier": 2},

    # ── International quality ─────────────────────────────────────────────────
    {"url": "https://www.nrc.nl/rss/",                                  "name": "NRC Handelsblad",       "tier": 1},
    {"url": "https://www.lemonde.fr/en/rss/une.xml",                    "name": "Le Monde English",      "tier": 1},
    {"url": "https://www.lemonde.fr/en/europe/rss_full.xml",            "name": "Le Monde Europe",       "tier": 2},
    {"url": "https://dutchnews.nl/feed/",                               "name": "DutchNews",             "tier": 2},
    {"url": "https://www.ansa.it/emiliaromagna/notizie/emiliaromagna_rss.xml", "name": "ANSA Emilia-Romagna", "tier": 2},
    {"url": "https://www.ansa.it/english/news/english_nr_rss.xml",      "name": "ANSA English",          "tier": 2},
    # El Pais English removed — feed is live (200) but frozen: live-verified
    # 2026-08-06, all 62 items dated January-April 2020, so every fetch always
    # falls outside the 7-day cutoff and silently yields zero.
    {"url": "https://www.theguardian.com/world/rss",                    "name": "Guardian World",        "tier": 2},

    # ── Space, economy, philosophy, ecology, anthropology ─────────────────────
    # Added 2026-08-09 per an explicit editorial-direction request: more weight
    # toward architecture/design/art/philosophy/history/technology/science/
    # biology/economy/prototypes/indigenous culture/language/cinema/sustainability/
    # mythology/space, less toward pure policy/politics/government/administration/
    # law/marketing coverage. Paired with the new philosophy/space_cosmos/
    # economy_finance/sustainability_ecology/indigenous_tribal THEME_KEYWORDS
    # buckets below — without matching keyword buckets, items from these feeds
    # would score against the wrong themes or 0.0 and be silently discarded
    # (same failure mode already documented above for the 2026-08-07 feed batch).
    {"url": "https://www.space.com/feeds/all",                          "name": "Space.com",             "tier": 2},
    {"url": "https://www.sapiens.org/feed/",                            "name": "SAPIENS (anthropology)","tier": 1},
    {"url": "https://www.economist.com/finance-and-economics/rss.xml",  "name": "Economist Finance",     "tier": 1},
    {"url": "https://dailynous.com/feed/",                              "name": "Daily Nous (philosophy)","tier": 2},
    {"url": "https://www.theguardian.com/environment/rss",              "name": "Guardian Environment",  "tier": 1},
]

# ── Relevance scoring ─────────────────────────────────────────────────────────

# Added 2026-08-09 continuation, explicit request: exclude the mental-health-
# news-cycle beat (NHS service cuts, psychiatric ward conditions, crisis-care
# policy) from discovery entirely. Scoped narrowly to multi-word news-genre
# phrases, not single words like "mental" or "psychiatric" -- this only stops
# an RSS item ABOUT the mental-health-policy beat from being picked as source
# material; it does not touch what a persona can write about from their own
# disability lens when it comes up naturally in an unrelated story (see
# .claude/audience-engagement-tasklist.md's persona-identity guardrail for why
# that distinction matters). Triggered by a real example: "Millions in England
# face longer waits for mental health care as NHS providers plan cuts"
# (Guardian Society) scored via the general health_systems bucket and became
# a full article before this exclusion existed.
MENTAL_HEALTH_NEWS_EXCLUDE = [
    "mental health service", "mental health services", "mental health crisis",
    "mental health trust", "mental health act", "mental health funding",
    "mental health policy", "mental health ward", "mental health care",
    "psychiatric ward", "psychiatric hospital", "psychiatric unit",
    "psychiatric bed", "crisis care", "crisis line", "suicide prevention",
    "sectioned under", "nhs mental health", "camhs", "inpatient psychiatric",
]

THEME_KEYWORDS = {
    # "building"/"museum"/"gallery" removed 2026-08-10 (Opus review, Interaction
    # A) -- confirmed real collateral: "Three men dead after west London
    # building fire" cleared the selection gate purely on "building" at this
    # bucket's x1.5 weight; museum/gallery duplicated art_culture, giving any
    # ordinary gallery review an effective x2.5 (both buckets' weight summed).
    # A weighted bucket needs higher-precision terms than an unweighted one did.
    "architecture":   ["architecture","design","urban","housing","planning",
                       "infrastructure","public space","construction","zoning","facade",
                       "interior","spatial","acoustics","pavilion"],
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
    "business_labor": ["work","employment","labor","gig","hiring",
                       "productivity","burnout","workplace",
                       "job","career","wage"],
    "health_systems": ["hospital","diagnosis","treatment",
                       "patient","clinic","medicine",
                       "pharmaceutical","drug","surgery","chronic"],
    "education":      ["school","university","student","curriculum","learning","classroom",
                       "exam","teaching","pedagogy","literacy","degree","college"],
    # Added 2026-08-07 alongside the Bregman-vein feed additions (Psyche, Works in
    # Progress, Asterisk, Behavioral Scientist, Nature Human Behaviour, JSTOR Daily,
    # Undark, Noema) — without these two buckets, real items from those feeds scored
    # 0.0 and were silently discarded before angle-extraction ever saw them (verified
    # live: "The myth of medieval childhood" from Works in Progress, "Mother Teresa
    # was virtuous, but she was wrong about virtue" from Psyche, "The Many Lives of
    # Libraries" from JSTOR Daily all scored 0.0 against the prior 8 buckets).
    "behavioral_science": ["experiment","psychology","psychological","behaviour","behavior",
                       "cognitive bias","cooperation","altruism","trust","incentive","norm",
                       "replication","survey","game theory","decision-making","habit",
                       "persuasion","nudge","bias","virtue","empathy"],
    "history_archive": ["historian","archive","century","medieval","archaeology","ancient",
                       "empire","revolution","colonial","primary source","manuscript",
                       "excavation","antiquity","dynasty","folklore","myth","legacy",
                       "mythology","ritual","relic","artifact","legend","ancestral"],
    # Five buckets added 2026-08-09 for the editorial-direction shift described above
    # the space/anthropology/economy/philosophy/environment feed additions.
    "philosophy":     ["philosophy","philosopher","ethics","metaphysics","phenomenology",
                       "existential","epistemology","moral philosophy","logic",
                       "consciousness","free will","ontology"],
    # bare "space" removed 2026-08-10 (Opus review, Interaction A) -- matched
    # 14 items with no astronomy context at all ("Co-Working Meets Art at
    # Brooklyn's Newest Experimental Space", a heatwave-alert story) and
    # inflated their score at this bucket's x1.5 weight. The remaining terms
    # are specific enough that this bucket doesn't need the generic word.
    "space_cosmos":   ["galaxy","astronomy","NASA","telescope","planet","cosmos",
                       "universe","astrophysics","satellite","Mars","exoplanet","orbit",
                       "spacecraft"],
    "economy_finance": ["economy","economic","stocks","stock market","investment",
                       "startup","prototype","venture","trade","currency","GDP",
                       "market","finance"],
    "sustainability_ecology": ["sustainability","sustainable","climate","renewable",
                       "biodiversity","conservation","ecosystem","carbon","rewilding",
                       "deforestation","jungle","rainforest"],
    # "ancestral" removed 2026-08-10 (Opus review, Interaction A) -- duplicated
    # history_archive, giving any item hitting both an effective x3.0 (both
    # buckets' x1.5 weight summed). This bucket's remaining terms are specific
    # enough on their own.
    "indigenous_tribal": ["indigenous","tribe","tribal","anthropology",
                       "oral tradition","elder","ceremony","first nations","aboriginal",
                       "ethnography"],
}

# Items mentioning these get a +0.3 boost — explicit disability lens
# Added 2026-08-09 continuation, per an Opus review of this pipeline's weakest
# link: the +0.3 boost below, on the original bare-word list, was empirically
# a "welfare-administration journalism" detector, not a disability-lens
# detector -- 74% of boosted items cleared get_news_seed's 0.4 gate vs 18% of
# unboosted ones, and 48% of boosted items came from just 2 feeds (Disability
# News Service + Guardian Society, the UK social-policy beat). This directly
# contradicted the pipeline's own stated rule ("disability as lens, not
# topic" -- _fable_editorial_brief, _fable_editorial_review) by rewarding
# exactly the topic-not-lens framing the writer layer exists to avoid, and
# starved Bregman-register material: all 4 canonical anchor pieces in
# .claude/bregman-anchor-corpus.md Section 1 score 0.0 under this scorer,
# below a Wired affiliate promo-code item at 0.675. Removed the four bare
# single words responsible ("disability","disabled","barrier","accommodation"
# -- the last two also false-positive on generic housing/negotiation stories
# unrelated to disability); kept only multi-word/specific terms, consistent
# with the whole-word-vs-substring lesson already documented on
# _keyword_matches. Boost also halved (0.3 -> 0.15) so a genuine lens-match no
# longer single-handedly clears the 0.4 selection gate on its own.
DISABILITY_BOOSTERS = [
    "accessible","accessibility","wheelchair","deaf","blind",
    "autistic","neurodivergent","chronic illness","inclusive design","universal design",
    "assistive","impairment","sign language","braille",
    "screen reader","caption","crip","spinal","mobility","invisible disability",
]

# Theme -> preferred persona for agent selection is live in
# DiscoveryMixin._news_seed_to_agent (automation/orchestrator/discovery.py).
# A dead, stale copy of this map used to live here -- removed 2026-08-10
# rather than synced: nothing in this file ever read it, and a documented-
# but-stale duplicate of live config is worse than no duplicate, since it
# can eventually get read as authoritative by someone who doesn't check.


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
    # disability_angle IS NULL means both "not yet attempted" and "attempted, model
    # said none exists" — a seed the model correctly rejects stays NULL forever and
    # gets re-selected by extract_top_angles' ORDER BY relevance_score DESC every
    # single day until prune_old drops it at 14 days, permanently occupying top-10
    # slots and starving fresh seeds below it (~150 wasted extraction calls/month).
    # angle_checked marks "an attempt happened" independent of the outcome, so a
    # real rejection is remembered without ever writing a sentinel into
    # disability_angle itself — production_orchestrator.get_news_seed selects on
    # `disability_angle IS NOT NULL`, so a sentinel there would get fed straight
    # into the article-generation prompt as if it were a real angle.
    try:
        conn.execute("ALTER TABLE news_seeds ADD COLUMN angle_checked TEXT")
    except sqlite3.OperationalError:
        pass
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


def _local(el, name, default=""):
    """Get a namespace-qualified child's text by local tag name, ignoring whichever
    namespace it's actually in. Needed for RSS 1.0/RDF feeds (e.g. Nature), whose
    <item>/<title>/<link>/<description> are all namespace-qualified and use dc:date
    instead of pubDate — root.findall(".//item") and item.findtext("title") both
    silently return nothing against them (no exception, so no log line either)."""
    for c in el:
        if c.tag.split("}")[-1] == name and c.text:
            return c.text
    return default


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
        # .strip(): some feeds (Dezeen) serve leading whitespace before the XML
        # declaration, which ET rejects outright ("XML or text declaration not at
        # start of entity") — 127/127 fetch attempts failed silently into the
        # except-and-log branch below since the log began (2026-04-06).
        root = ET.fromstring(raw.strip())

        # RSS 2.0 — also handles RSS 1.0/RDF (e.g. Nature), where <item> and its
        # children are namespace-qualified and dates are dc:date not pubDate.
        # root.findall(".//item") only matches the unqualified tag, so an RDF feed
        # silently yielded 0 items here with no exception and no log line.
        for item in (e for e in root.iter() if e.tag.split("}")[-1] == "item"):
            title   = _strip_html(_local(item, "title"))[:200]
            link    = (_local(item, "link")).strip()
            summary = _strip_html(_local(item, "description"))[:500]
            dt      = _parse_dt(_local(item, "pubDate") or _local(item, "date"))
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
            if not link:
                # Some Atom feeds (Jacobin) carry no <link> at all, only <id> — all
                # three fallbacks above return None and the entry used to be
                # dropped by the `title and link` check below. <id> is a URI in
                # practice for these feeds even though the spec doesn't guarantee it.
                _eid = (entry.findtext("a:id", "", ns) or entry.findtext("id", "")).strip()
                if _eid.startswith("http"):
                    link = _eid
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
    # Substring matching on single words &gt;=4 chars false-positived constantly:
    # "deaf" in "a deafening silence", "blind" in "SelectBlinds promo", "crip" in
    # "full description"/subscription/prescription/transcript, "care" in "career",
    # "work" in "network", "sign" in "design", "text" in "context"/"texture" — all
    # matched and fired the relevance boost / theme tag on unrelated stories, which
    # is why the daily top-10 LLM queue was full of promo codes and Xbox news.
    # Multi-word keys ("sign language", "chronic illness") keep substring matching
    # since word-set membership can't match a phrase; single words become
    # whole-word with simple plural tolerance instead.
    kw = keyword.lower()
    if " " in kw:
        return kw in text
    return kw in words or f"{kw}s" in words or f"{kw}es" in words


# Added 2026-08-09 continuation, Tier A from the same Opus review: narrow,
# high-precision welfare/policy-process program names, not the bare word
# "policy" (a Tier B version using bare government/minister/policy/legislation/
# reform words was tested and rejected -- 15% of the pool zeroed, including a
# Hyperallergic thesis exhibition and a Guardian art review; false-positive
# rate too high). This Tier A list zeroed 12/755 real seeds in testing, 100%
# precision (every hit was genuinely the UK/AU welfare-administration beat),
# but blocked 4/54 real published articles -- accepted tradeoff, explicit
# owner decision: this is effectively the entire beat Disability News Service
# covers, so it heavily suppresses that feed, not just individual stories.
POLICY_PROCESS_EXCLUDE = [
    "white paper", "green paper", "policy paper", "consultation period",
    "public consultation", "spending review", "select committee",
    "parliamentary inquiry", "regulatory reform", "autumn statement",
    "budget statement", "royal commission", "department for work and pensions",
    "dwp", "benefit claimant", "welfare reform", "universal credit",
    "benefit cuts", "disability benefits review", "work capability",
    "pip assessment", "personal independence payment", "ndis review",
]

# Added 2026-08-09 continuation, same review: base scoring summed keyword hits
# across all 15 THEME_KEYWORDS buckets with equal weight, so the stated
# editorial preference (toward architecture/space/mythology, away from
# policy/admin -- commit 508cc86) existed only in feed/persona-routing
# decisions and never once in the ranking function itself. A multi-domain
# welfare story (touching health_systems + business_labor + education +
# science_nature at once) could out-score a single-domain architecture or
# mythology piece purely on vocabulary breadth. These multipliers apply
# per-bucket, before the sum -- default 1.0 for any bucket not listed.
THEME_WEIGHTS = {
    "architecture": 1.5, "history_archive": 1.5, "space_cosmos": 1.5,
    "indigenous_tribal": 1.5, "philosophy": 1.5,
    "health_systems": 0.7, "business_labor": 0.7,
}


# Added 2026-08-10, Opus review finding (the most severe of that review):
# MENTAL_HEALTH_NEWS_EXCLUDE/POLICY_PROCESS_EXCLUDE ran globally on
# title+summary, before theme scoring -- zeroing real, on-brief disability-
# arts/history content that happened to mention an excluded phrase in
# passing. Two confirmed real casualties from the live DB, both actually
# published under the old rules: a Guardian Art & Design piece on a
# disability-arts exhibition ("near death experiences, 'crip memes' and the
# tyranny of the DWP") zeroed on "dwp"; a Leonora Carrington surrealist-art
# piece zeroed on "psychiatric hospital" matching incidentally in the
# summary. This directly falsified this file's own prior claim that no
# published article would be blocked by either list. Exclusions now only
# apply when the item's DOMINANT theme isn't one of these -- a genuine
# welfare-beat story won't dominant-match art/architecture/history, so the
# original mental-health/policy detection is unaffected.
_EXCLUSION_PROTECTED_THEMES = {"art_culture", "architecture", "history_archive"}


def score_item(item: dict) -> tuple[float, list[str]]:
    """Return (relevance_score 0-1, matched_themes list)."""
    text = f"{item['title']} {item.get('summary', '')}".lower()
    words = set(re.findall(r"\b\w+\b", text))

    theme_hits: dict[str, int] = {}
    for theme, keywords in THEME_KEYWORDS.items():
        hits = sum(1 for kw in keywords if _keyword_matches(text, words, kw))
        if hits:
            theme_hits[theme] = hits

    dominant = max(theme_hits, key=theme_hits.get) if theme_hits else None
    if dominant not in _EXCLUSION_PROTECTED_THEMES:
        # health_systems exclusion added 2026-08-10, explicit request: no
        # healthcare content at all, including disability-health angles.
        # First tried ungated (any health_systems hit zeroes outright) --
        # confirmed live that this re-broke the exact art/disability pieces
        # fixed earlier tonight (both mention "hospital" in passing: the
        # disability-arts exhibition, the Carrington piece). Reverted to the
        # same protected-theme gate as the other two exclusions below.
        if "health_systems" in theme_hits:
            return 0.0, []
        if any(kw in text for kw in MENTAL_HEALTH_NEWS_EXCLUDE):
            return 0.0, []
        if any(kw in text for kw in POLICY_PROCESS_EXCLUDE):
            return 0.0, []

    weighted_sum = sum(hits * THEME_WEIGHTS.get(theme, 1.0) for theme, hits in theme_hits.items())
    base = min(weighted_sum / 8.0, 0.7) if theme_hits else 0.0
    boost = 0.15 if any(_keyword_matches(text, words, kw) for kw in DISABILITY_BOOSTERS) else 0.0
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
    """Ask Sonnet to find the hidden disability angle. Returns angle, or None
    if the model genuinely found none.

    Raises on network/API failure (added 2026-08-10, Opus review) instead of
    swallowing it into the same None as a genuine "no angle" verdict. Before
    this fix, a transient CLIProxy outage got recorded identically to "the
    model said NONE" -- the caller then set angle_checked and never retried
    that seed. ~10 seeds/day were being permanently lost this way to
    ordinary transient failures. Callers must catch and retry, not treat an
    exception as a verdict."""
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
    req = urllib.request.Request(
        API_URL, data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        resp = json.loads(r.read())
    angle = resp["choices"][0]["message"]["content"].strip()
    angle = re.sub(r"<think>.*?</think>", "", angle, flags=re.DOTALL).strip()
    angle = re.sub(r"\*\*Pitch:\*\*\s*", "", angle).strip()
    angle = re.sub(r"^\*\*", "", angle).strip()
    if angle.upper().startswith("NONE") or len(angle) < 15:
        return None
    return angle


# ── Category-jump judge (SHADOW MODE, added 2026-08-10) ────────────────────────
#
# Item 4 (discovery-time premise/angle scoring) was blocked all session on real
# calibration input. Got it: two consultations with an external model that has
# real history on the owner's taste, calibrated against real examples --
# positive gold-standard: Sara Hendren's "All Technology Is Assistive" (WIRED)
# and Jane Jacobs's "The Uses of Sidewalks: Safety" (Death and Life of Great
# American Cities); negative, same-genre controls (competent journalism that
# still fails the test): a Guardian first-person wheelchair-accessibility
# piece and a web-accessibility piece with a real named source -- both kept
# BECAUSE they show "named person + concrete detail + disability" is NOT
# sufficient on its own. Ta-Nehisi Coates's "The Case for Reparations" was
# offered first, then explicitly downgraded on a second pass as too broad a
# taste prediction -- kept out of the prompt below for that reason.
#
# The core test, sharper than "correction moment + resisting example" alone
# (Stage B's fields, on the generation side of this pipeline): a disability
# lens must reveal what a system/object IS or DOES, not just who it excludes.
# "Public transport is hard for wheelchair users" names harm; "a feature meant
# to speed passenger flow strands one kind of passenger" reveals the system's
# actual optimization target. Concretely, a real category jump: medical splint
# -> modernist furniture; busy sidewalk -> security infrastructure.
#
# SHADOW MODE, same discipline as every other shadow check in this project:
# logs its YES/NO/reasoning to category_jump_shadow, and NEVER conditions
# selection or generation on it. Real (item, verdict) pairs need to
# accumulate and get checked against real judgment before this becomes
# anything but observation.
#
# Runs on its OWN sampled candidate pool (see sample_shadow_candidates),
# deliberately decoupled from extract_angle/extract_top_angles's pool as of
# 2026-08-10 -- per calibration feedback, judging only the keyword scorer's
# top-N would re-import the exact problem Stage 1 exists to escape.
# extract_angle's pool (which DOES drive real selection via disability_angle
# gating get_news_seed) is untouched by this change.
_JUDGE_PROMPT_VERSION = "v2-evidentiary-bridge"

_CATEGORY_JUMP_SYSTEM_PROMPT = """You are the CRIPMINDS SOURCE ANGLE JUDGE.

You receive one RSS item consisting of a TITLE and SUMMARY.

Your job is NOT to decide whether the topic concerns disability, accessibility, AI, art, design, politics, culture, or any other preferred subject.

Your job is to decide whether the item contains concrete material from which a CripMinds writer could reveal a HIDDEN MECHANISM of the thing itself.

A strong item starts in one apparent category and contains a concrete person, object, event, behaviour, failure, contradiction, or detail that could make the argument end in a meaningfully different category.

Examples of the pattern:

* medical leg splint -> modernist furniture
* busy sidewalk -> security infrastructure
* assistive device -> theory of technology
* ordinary house purchase -> extraction mechanism

The disability lens must do more than show that disabled people are affected by something.

BAD:
"Public transport is difficult for wheelchair users."
This tells us who is harmed. It does not change what public transport means.

POTENTIALLY GOOD:
"A design feature intended to speed passenger flow repeatedly strands one kind of passenger."
This may reveal that the transport system is not simply transporting people; it is optimizing for a hidden definition of the acceptable passenger.

Do not reward:

* disability keyword density
* worthy social issues
* policy relevance
* explicit calls for inclusion
* statistics about inequality
* a named disabled person by itself
* an article merely illustrating a thesis it states from the beginning
* generic conclusions such as "society is ableist," "accessibility matters," "technology can exclude," or "design should be inclusive"

Do not invent missing facts.

A possible hidden mechanism must be grounded in something actually present in the TITLE or SUMMARY.

Run these tests:

1. OSTENSIBLE CATEGORY
   What does this item appear to be about before interpretation?

2. RESISTING DETAIL
   Is there one concrete person, object, event, behaviour, failure, contradiction, or observed detail that does not sit neatly inside the obvious explanation?

3. HIDDEN MECHANISM
   Could that detail reveal what the object/system is actually doing, optimizing, assuming, measuring, rewarding, hiding, or making possible?

4. CATEGORY JUMP
   Is that hidden mechanism meaningfully different from the item's ostensible category?

The vocabulary of the starting subject and the ending insight should normally belong to different conceptual domains.

5. CORRECTION
   Could a writer truthfully make a movement approximately like:

"I thought this was a story about X. The concrete case suggests it is actually a story about Y."

X and Y must not merely be:
"disability problem" -> "bigger disability problem"
or
"access barrier" -> "evidence that accessibility matters."

6. EVIDENTIARY BRIDGE (the most important test -- apply it hardest)
   Quote or closely paraphrase the EXACT fact in the TITLE or SUMMARY that
   supports the jump from X to Y. Not the general topic -- the specific
   fact doing the work.

   You are allowed to discover an implication already present in the
   source. You are NOT allowed to invent the causal bridge yourself.

   Bad bridge, reject the jump even if the destination sounds good:
   "Google is a private company, therefore this creates private demand
   generation" -- this is YOUR inference, not a fact stated or implied by
   the source.

   Good bridge, keep the jump:
   "the summary states the drug showed a measurable biomarker change but
   the review calls the patient-level effect trivial" -- this fact is
   actually present and directly supports the mechanism.

   If you cannot point to a specific sentence or fact doing this work,
   the bridge field must be null, and the decision must be NO regardless
   of how good the proposed destination sounds.

DECISION RULE:

Return YES only when:

* there is concrete evidence in the supplied item;
* that evidence supports a plausible hidden mechanism;
* the mechanism changes our understanding of the thing/system itself;
* the resulting category jump does not depend on invented facts;
* AND the evidentiary bridge (test 6) points to a specific, quotable
  fact -- not a plausible-sounding inference you supplied yourself.

Return NO when:

* the thesis is already completely stated by the topic;
* examples merely demonstrate the stated thesis;
* disability only identifies who benefits or suffers;
* the apparent and hidden categories are basically the same;
* reaching the proposed hidden mechanism requires speculation beyond the supplied item;
* OR the evidentiary bridge is empty, vague, or is your own inference
  rather than something stated or clearly implied by the source. This
  overrides an otherwise attractive destination -- a great-sounding jump
  with a hand-wavy bridge is still a NO.

A YES does NOT mean the eventual essay angle has been proven.
It means the source contains enough grounded friction to justify further investigation.

Return only this JSON:

{
"decision": "YES" | "NO",
"ostensible_category": "What the item appears to be about",
"resisting_detail": "The exact concrete detail creating friction, or null",
"hidden_mechanism": "What the detail may reveal about what the thing/system actually does, or null",
"category_jump": "X -> Y, or null",
"evidentiary_bridge": "The exact fact from the source supporting the jump -- quote or close paraphrase, or null if none exists",
"correction": "I thought X; this case suggests Y, or null",
"reason": "Maximum 3 sentences. Explain why it passes or fails the mechanism-reveal test, and if NO specifically because of the bridge, say so."
}"""


def category_jump_judge(title: str, summary: str) -> tuple[dict | None, str]:
    """SHADOW MODE -- see the module comment above this function for the
    full design rationale and calibration sources. Never raises.

    Returns (judgment_or_None, status). Added 2026-08-10, per calibration
    feedback: a judge FAILURE and a genuine NO must never be
    indistinguishable in the shadow data -- the exact bug that silently
    lost the strongest positive example from the first real batch (a
    truncated-but-real response looked identical to "no judgment" until
    diagnosed by hand). status is one of:
      "ok"            -- valid judgment returned
      "no_api_key"    -- API_KEY not set
      "timeout"       -- request timed out
      "model_error"   -- network/API error other than timeout
      "empty_response" -- API returned no usable content
      "invalid_json"  -- content didn't parse as the expected JSON shape
    """
    if not API_KEY:
        return None, "no_api_key"
    user = f"TITLE:\n{title}\n\nSUMMARY:\n{summary}"
    payload = json.dumps({
        "model": MODEL,
        # 500 wasn't enough -- confirmed via a real failure 2026-08-10 on the
        # Alzheimer's-drug seed: a verbose-but-valid response (7 populated
        # fields including a full "reason" paragraph) came within a few
        # dozen tokens of this cap on a successful run, and a less lucky
        # generation hit it mid-string, producing invalid JSON that silently
        # returned None -- losing exactly the strongest positive calibration
        # example from the first real batch. Same failure class already
        # diagnosed and fixed elsewhere in this pipeline for the same reason
        # (see _plan_follow_read's max_tokens history on the generation side).
        "max_tokens": 900,
        "messages": [
            {"role": "system", "content": _CATEGORY_JUMP_SYSTEM_PROMPT},
            {"role": "user", "content": user},
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
    except Exception as e:
        status = "timeout" if "timed out" in str(e).lower() else "model_error"
        log(f"  category-jump judge {status}: {e}")
        return None, status

    try:
        raw = resp["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, AttributeError):
        log("  category-jump judge: empty/malformed API response")
        return None, "empty_response"
    if not raw:
        return None, "empty_response"

    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
    try:
        judgment = json.loads(raw)
    except json.JSONDecodeError as e:
        log(f"  category-jump judge invalid JSON: {e}")
        return None, "invalid_json"
    if "decision" not in judgment:
        return None, "invalid_json"
    return judgment, "ok"


SAMPLER_VERSION = "v2-stratified"


def sample_shadow_candidates(conn, n: int = 10, days: int = 3):
    """Stratified sampler for Stage 1 shadow judging ONLY -- added
    2026-08-10 per calibration feedback. Judging only the keyword scorer's
    top-N would re-import the exact problem Stage 1 exists to escape:
    density-ranking is likely to suppress the low-keyword-density material
    Stage 1 is supposed to catch. Deliberately separate from
    extract_top_angles's pool, which drives real selection (disability_angle
    gates get_news_seed) and is completely untouched by this function --
    this samples for observation only, writes nothing back to news_seeds.

    "Sample before any semantic ranking whatsoever" -- the WHERE clause
    below only excludes things that are legitimately unusable regardless of
    taste (already used, already touched by extract_angle/angle_checked,
    outside the age window); nothing here asks whether content is relevant
    or interesting. Three lanes, each genuinely distinct (not "not in the
    other lanes"), fixed proportions -- NOT tuned by early YES rates, which
    would make later comparisons uninterpretable:
      - ~30% keyword_top: the old scorer's actual top candidates (does the
        old system happen to concentrate good anomalies?)
      - ~30% keyword_low: the old scorer's genuinely LOWEST-scoring
        candidates (ORDER BY relevance_score ASC, not merely "outside the
        top 10" -- is the old scorer actively suppressing the material
        Stage 1 values?)
      - ~40% broad_random: ORDER BY RANDOM() over the full eligible pool,
        capped per-source so one prolific feed can't dominate (how common
        are good anomalies in RSS generally?)

    Returns a list of (seed_id, url, title, summary, candidate_origin)."""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    lane_low = max(round(n * 0.3), 0)
    lane_top = max(round(n * 0.3), 0)
    lane_broad = max(n - lane_low - lane_top, 0)

    base_where = (
        "WHERE disability_angle IS NULL AND angle_checked IS NULL AND used = 0 "
        "AND pub_date >= ?"
    )

    top_rows = conn.execute(f"""
        SELECT id, url, title, summary, source_name FROM news_seeds
        {base_where}
        ORDER BY relevance_score DESC
        LIMIT ?
    """, (cutoff, lane_top)).fetchall()

    low_rows_raw = conn.execute(f"""
        SELECT id, url, title, summary, source_name FROM news_seeds
        {base_where}
        ORDER BY relevance_score ASC
        LIMIT ?
    """, (cutoff, lane_low + len(top_rows))).fetchall()  # pad for overlap trim
    top_ids = {r[0] for r in top_rows}
    low_rows = [r for r in low_rows_raw if r[0] not in top_ids][:lane_low]

    seen_ids = top_ids | {r[0] for r in low_rows}
    placeholders = ",".join("?" * len(seen_ids)) if seen_ids else "''"
    broad_pool = conn.execute(f"""
        SELECT id, url, title, summary, source_name FROM news_seeds
        {base_where} AND id NOT IN ({placeholders})
        ORDER BY RANDOM()
    """, (cutoff, *seen_ids)).fetchall()

    broad_rows = []
    per_source_count: dict[str, int] = {}
    max_per_source = max(2, lane_broad // 3 or 1)
    for row in broad_pool:
        src = row[4]
        if per_source_count.get(src, 0) >= max_per_source:
            continue
        broad_rows.append(row)
        per_source_count[src] = per_source_count.get(src, 0) + 1
        if len(broad_rows) >= lane_broad:
            break

    return (
        [(r[0], r[1], r[2], r[3], "keyword_top") for r in top_rows]
        + [(r[0], r[1], r[2], r[3], "keyword_low") for r in low_rows]
        + [(r[0], r[1], r[2], r[3], "broad_random") for r in broad_rows]
    )


def run_category_jump_shadow(conn, n: int = 10):
    """Drives Stage 1 shadow judging on its own independent candidate pool
    -- see sample_shadow_candidates's docstring. Never affects real
    selection/generation; writes only to category_jump_shadow."""
    if not API_KEY:
        log("CLIProxy API key not set — skipping category-jump shadow judging")
        return
    candidates = sample_shadow_candidates(conn, n=n)
    judged = failed = 0
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for seed_id, url, title, summary, origin in candidates:
        judgment, status = category_jump_judge(title, summary or "")
        _persist_category_jump_shadow(conn, seed_id, now, judgment or {}, status, origin)
        if judgment:
            judged += 1
        else:
            failed += 1
        time.sleep(0.5)
    log(
        f"Category-jump shadow judging done: {judged} judged, {failed} failed "
        f"({SAMPLER_VERSION}, {len(candidates)} sampled)"
    )


def _persist_category_jump_shadow(conn, seed_id: str, judged_at: str, judgment: dict,
                                   status: str = "ok", candidate_origin: str = None):
    """Never raises -- pure shadow logging, must never affect the real run.

    status added 2026-08-10: "ok" or an error type (see category_jump_judge's
    docstring) -- decision coverage and taste calibration are two different
    questions and must never be conflated by treating a failure identically
    to a real NO, the exact bug that silently lost a real calibration
    example earlier tonight."""
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS category_jump_shadow (
                id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                seed_id              TEXT NOT NULL,
                judged_at            TEXT NOT NULL,
                decision             TEXT,
                ostensible_category  TEXT,
                resisting_detail     TEXT,
                hidden_mechanism     TEXT,
                category_jump        TEXT,
                correction           TEXT,
                reason               TEXT,
                UNIQUE(seed_id, judged_at)
            )
        """)
        # Migration-safe additions -- ALTER TABLE ADD COLUMN has no
        # "IF NOT EXISTS" in SQLite, and this table already had real rows
        # in production before each of these fields existed.
        for col in (
            "evidentiary_bridge TEXT", "attempt_status TEXT", "error_type TEXT",
            "candidate_origin TEXT", "sampler_version TEXT",
            "judge_prompt_version TEXT", "model_version TEXT",
        ):
            try:
                conn.execute(f"ALTER TABLE category_jump_shadow ADD COLUMN {col}")
            except sqlite3.OperationalError:
                pass  # column already exists
        attempt_status = "success" if status == "ok" else "error"
        error_type = None if status == "ok" else status
        conn.execute(
            "INSERT OR REPLACE INTO category_jump_shadow "
            "(seed_id, judged_at, decision, ostensible_category, resisting_detail, "
            "hidden_mechanism, category_jump, evidentiary_bridge, correction, reason, "
            "attempt_status, error_type, candidate_origin, sampler_version, "
            "judge_prompt_version, model_version) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                seed_id, judged_at, judgment.get("decision"),
                judgment.get("ostensible_category"), judgment.get("resisting_detail"),
                judgment.get("hidden_mechanism"), judgment.get("category_jump"),
                judgment.get("evidentiary_bridge"),
                judgment.get("correction"), judgment.get("reason"),
                attempt_status, error_type, candidate_origin, SAMPLER_VERSION,
                _JUDGE_PROMPT_VERSION, MODEL,
            ),
        )
        conn.commit()
    except Exception as e:
        log(f"  category-jump shadow persistence failed: {e}")


# See extract_top_angles's docstring/comment for why this exists -- a cheap,
# uncalibrated mitigation for score_item()'s structural blind spot, not a
# substitute for the real fix (an LLM-judged angle-interest score).
EXPLORATION_SLOTS = 2


def extract_top_angles(conn, n: int = 10):
    """Fetch top-N unprocessed seeds by score and extract disability angles."""
    if not API_KEY:
        log("CLIProxy API key not set — skipping angle extraction")
        return
    # Match get_news_seed's own 3-day pub_date window (production_orchestrator.py) —
    # this used to select purely by relevance_score with no age filter, so it could
    # (and did) spend a paid Sonnet call extracting an angle for a seed that would
    # already be outside get_news_seed's selection window by the time anything looked
    # for it. Measured live: 31 unused angled seeds in the DB, only 3 actually
    # reachable by get_news_seed's cutoff.
    cutoff = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    top_n = max(n - EXPLORATION_SLOTS, 0)
    top_rows = conn.execute("""
        SELECT id, url, title, summary FROM news_seeds
        WHERE disability_angle IS NULL AND angle_checked IS NULL AND used = 0
              AND pub_date >= ?
        ORDER BY relevance_score DESC
        LIMIT ?
    """, (cutoff, top_n)).fetchall()

    # Exploration slots, added 2026-08-10 -- mitigation for the discovery
    # scorer's structural blind spot, not a fix for it (the real fix is an
    # LLM-judged angle-interest score, still gated on real calibration
    # examples). score_item() measures topic-keyword density, which is a
    # DIFFERENT axis from narrative craft -- confirmed via the 4 canonical
    # Bregman anchor pieces in .claude/bregman-anchor-corpus.md all scoring
    # 0.0 (real material is low-keyword-density by construction: one
    # concrete dated thing, plain vocabulary, no named framework). That
    # means genuinely strong, sparse material can be filtered out before
    # extract_angle -- the one point that actually reads full content
    # instead of counting keywords -- ever sees it. A few random slots from
    # outside the score-ranked top N give that material a chance at the
    # real judgment, without needing any calibration data to do it.
    top_ids = [r[0] for r in top_rows]
    explore_rows = []
    if EXPLORATION_SLOTS > 0:
        placeholders = ",".join("?" * len(top_ids)) if top_ids else "''"
        explore_rows = conn.execute(f"""
            SELECT id, url, title, summary FROM news_seeds
            WHERE disability_angle IS NULL AND angle_checked IS NULL AND used = 0
                  AND pub_date >= ? AND id NOT IN ({placeholders})
            ORDER BY RANDOM()
            LIMIT ?
        """, (cutoff, *top_ids, EXPLORATION_SLOTS)).fetchall()

    rows = top_rows + explore_rows
    extracted = 0
    today = datetime.now().strftime("%Y-%m-%d")
    for seed_id, url, title, summary in rows:
        try:
            angle = extract_angle(title, summary or "", url)
        except Exception as e:
            # Added 2026-08-10 (Opus review): do NOT set angle_checked here --
            # a transient API failure is not a verdict. Leaving it NULL means
            # this seed is retried on the next run instead of being
            # permanently skipped, which is what happened before this fix.
            log(f"  LLM extraction failed for {title[:50]}: {e} — will retry next run")
            continue
        if angle:
            conn.execute(
                "UPDATE news_seeds SET disability_angle = ?, angle_checked = ? WHERE id = ?",
                (angle, today, seed_id),
            )
            log(f"  + angle: {title[:50]} → {angle[:70]}")
            extracted += 1
        else:
            conn.execute(
                "UPDATE news_seeds SET angle_checked = ? WHERE id = ?",
                (today, seed_id),
            )
        conn.commit()
        time.sleep(0.5)
    log(f"Angle extraction done: {extracted}/{len(rows)} got angles ({len(explore_rows)} exploration slots)")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log("=== news_fetcher start ===")
    conn = sqlite3.connect(str(DB))
    init_db(conn)

    # 1. Fetch all feeds
    raw_items = fetch_all_feeds(days=7)

    # 2. Score, deduplicate, store items above threshold
    stored = skipped_score = skipped_dupe = skipped_blocked = 0
    MIN_SCORE = 0.15
    MAX_PER_SOURCE = 8  # cap per source per run — prevents one feed dominating

    # Title patterns that produce useless grounding material
    BLOCKED_TITLE_PATTERNS = re.compile(
        r'\b(obituary|obituaries|in memoriam|necrology|'
        r'corrections?|erratum|errata)\b'
        r'|dies? at \d+'          # implicit obituaries: "Dies at 86"
        r'|\|\s*(brief\s+)?letters?\b'   # Guardian "| Letters" / "| Brief letters"
        r'|letters? to the editor'
        r'|\bshow hn:|\bask hn:|\btell hn:'   # Hacker News submissions
        # Affiliate/commerce churn. _keyword_matches' comment above already noted
        # "the daily top-10 LLM queue was full of promo codes" — whole-word matching
        # fixed the false-positive keywords but not the items themselves, which score
        # legitimately: "Barkbox Promo Codes and Discounts: Up to 50% Off" scores
        # 0.675 and "Noom Promo Codes", "Peacock Promo Codes", "HBO Max Promo Code",
        # "iRobot Promo Code", "Paramount+ Coupon Codes" all clear get_news_seed's
        # 0.4 gate. 17 such items in a 755-seed sample, all from Wired, all eligible
        # both for selection and for a paid Sonnet angle-extraction call.
        r'|\bpromo code|\bcoupon code|\bdiscount code|\bpromo codes'
        r'|\bbest deals\b|\bdeal of the day\b|\bbuying guide\b'
        r'|\d+%\s*off\b|\$\d+\s*off\b',
        re.IGNORECASE,
    )

    # Score everything first, then sort by score before applying MAX_PER_SOURCE
    # -- added 2026-08-10 (Opus review). The old order applied the per-source
    # cap during iteration in feed order (i.e. recency), before any score
    # comparison, so a high-volume feed's 8 slots went to whatever was newest
    # regardless of score -- silently undoing tonight's weight/exclusion
    # retuning for exactly the feeds that publish enough to hit the cap.
    scored_items = []
    for item in raw_items:
        title = item.get("title", "")
        if BLOCKED_TITLE_PATTERNS.search(title):
            skipped_blocked += 1
            continue
        score, themes = score_item(item)
        if score < MIN_SCORE:
            skipped_score += 1
            continue
        item["relevance_score"] = score
        item["themes"] = themes
        scored_items.append(item)

    scored_items.sort(key=lambda it: it["relevance_score"], reverse=True)

    source_counts: dict[str, int] = {}
    for item in scored_items:
        src = item["source_name"]
        if source_counts.get(src, 0) >= MAX_PER_SOURCE:
            skipped_score += 1
            continue
        if title_already_seen(conn, item["title"]):
            skipped_dupe += 1
            continue
        if store_seed(conn, item):
            stored += 1
            source_counts[src] = source_counts.get(src, 0) + 1

    log(f"Stored {stored} new seeds | skipped {skipped_score} low-score | {skipped_dupe} near-dupe | {skipped_blocked} blocked")

    # 3. LLM angle extraction for top candidates
    if API_KEY:
        extract_top_angles(conn, n=10)
    else:
        log("CLIProxy API key not set — skipping angle extraction")

    # 3b. Category-jump judge, SHADOW MODE ONLY -- independent candidate
    # pool, writes only to category_jump_shadow, never touches news_seeds.
    # See run_category_jump_shadow/sample_shadow_candidates docstrings.
    run_category_jump_shadow(conn, n=10)

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
