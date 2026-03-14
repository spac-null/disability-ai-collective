#!/usr/bin/env python3
"""
Discovery runner — finds disability hidden gems in mainstream journalism.

Two sources:
  1. Existing RSSDisabilityCrawler — disability-specific sites
  2. Google News RSS — mainstream queries, LLM extracts hidden disability angle

Cron: 0 7 * * *
"""
import os, sys, json, re, sqlite3, hashlib, time, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).parent
DB   = REPO / "disability_findings.db"
LOG  = REPO / "discovery.log"

API_URL  = "http://172.19.0.1:8317/v1/chat/completions"
API_KEY  = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL    = "claude-sonnet-4-6"   # Sonnet fine for extraction — cheap+fast

# Mainstream queries for Google News — designed to surface hidden disability angles
# NOT "disability accessibility news" — that's too obvious
# Mainstream queries — designed to surface HIDDEN disability angles
# Covers: design/tech, culture/art, paradigms, stereotypes, microaggressions,
#         deaf gain, neurodivergent perspectives, diversity of thought
MAINSTREAM_QUERIES = [
    # Design & space
    "architecture acoustic design building",
    "urban transit navigation pedestrian city",
    "museum exhibition visitor experience sensory",
    "public space social interaction inclusion",

    # Culture & representation
    "film casting Hollywood representation authentic",
    "concert live music audience experience",
    "theater performance access audience",
    "art criticism curator perspective voice",

    # Paradigms & ways of thinking
    "neurodiversity workplace creativity innovation",
    "deaf culture sign language visual thinking",
    "blind perspective spatial reasoning navigation",
    "chronic illness invisible condition workplace",

    # Stereotypes & microaggressions
    "inspiration porn media representation disability",
    "supercrip narrative trope film media",
    "diversity inclusion token representation workplace",
    "ableism language everyday microaggression",

    # Deaf gain & cognitive diversity
    "deaf gain visual spatial cognition advantage",
    "autistic thinking pattern recognition advantage",
    "ADHD hyperfocus creativity divergent thinking",
    "sensory processing difference perception art",

    # Social & political
    "social model disability rights justice",
    "crip culture reclaiming identity politics",
    "care work dependency interdependence community",
    "access intimacy disability relationship",

    # Technology as secondary lens
    "AI interface design user experience",
    "wearable technology body autonomy",
    "captioning subtitles language access",

    # Unexpected mainstream — hidden disability angles
    "film score composer creative process interview",
    "museum gallery redesign visitor engagement",
    "voice interface smart home assistant design",
    "sports injury recovery athlete performance",
    "open office workplace design productivity",
    "fashion runway model casting industry",
    "video game controller design mechanics",
    "restaurant kitchen chef ergonomics design",
    "concert hall acoustics architect design",
    "emergency evacuation building safety design",

    # Cripping Collaboration paper angles (Dronkert 2023)
    "productivity hustle pace burnout workplace culture",
    "diversity inclusion program corporate initiative",
    "independent living self-sufficiency housing",
    "peer review academic publishing gatekeeping access",
    "care worker staffing shortage social services",
    "science fiction film alienation institutional rejection",
    "asking for help stigma autonomy self-reliance",
    "diversity advisory board consultation representation",
    "meeting culture async remote work schedule",
    "credential degree requirement job hiring screen",

    # Crip time & work (Kafer, Samuels, McRuer)
    "long COVID return work fatigue productivity chronic illness",
    "four day work week flexible schedule productivity",
    "career gap resume employment non-linear ageism",
    "gig economy platform workers algorithm rating speed",
    "workplace wellness program employee health individual responsibility",

    # Care, community, loneliness (Mingus, Piepzna-Samarasinha)
    "loneliness epidemic social connection community infrastructure",
    "caregiver burnout unpaid family care labor",
    "mutual aid community care neighborhood network organizing",
    "doctor patient relationship healthcare communication trust",

    # Technology & design (Hamraie, Fritsch, AI hiring bias)
    "AI hiring software video interview bias discrimination",
    "smart city sensor urban infrastructure technology inclusion",
    "exoskeleton neural interface paralysis cure technology",

    # Public space & law (Schweik ugly laws)
    "hostile architecture anti-homeless bench spikes city design",
    "quality of life policing mental illness public space",

    # Culture & aesthetics (Siebers, Chapman)
    "body image beauty standards AI generated images representation",
    "ADHD diagnosis adults medication productivity neurodiversity",
    "prenatal genetic screening embryo selection disability",

    # Policy & law — hidden disability angles in mainstream legal/policy news
    "Medicaid home community based services HCBS cuts waiver",
    "nursing home alternatives community care institutionalization",
    "police shooting mental health crisis response reform",
    "competency to stand trial backlog jail wait time",
    "school discipline suspension expulsion disparities",
    "restraint seclusion school students injury",
    "voter ID law accessibility polling place barrier",
    "ballot assistance restriction voting law",
    "organ transplant criteria exclusion quality of life",
    "AI algorithm Medicaid insurance denial benefits",
    "prior authorization artificial intelligence health insurance",
    "solitary confinement reform legislation lawsuit",
    "SSI asset limit savings reform disability benefits",
    "benefits cliff work requirement Medicaid disability",
    "guardianship reform supported decision making",
    "subminimum wage sheltered workshop disability employment",
    "heat wave mortality vulnerable chronic illness medication",
    "disaster evacuation accessible transportation barrier",
    "public charge immigration benefits disability",
    "zoning group home neighborhood opposition fair housing",

    # Cultural events — art, film, performance, discourse
    "film festival programming selection jury diversity",
    "art gallery exhibition curator selection representation",
    "theater casting open call audition diversity",
    "opera ballet dance company casting body",
    "talk show guest expert panel representation",
    "documentary film festival submission independent",
    "museum collection acquisition artist diversity",
    "art residency fellowship application process",
    "theater sensory relaxed performance audience",
    "academic conference keynote speaker lineup",
    "comedy stand-up performance body identity humor",
    "workshop creative writing facilitation participation",
]

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def fetch_google_news_rss(query, max_items=5):
    """Fetch Google News RSS for a query — returns list of {title, url, snippet}."""
    encoded = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            xml = r.read()
        root = ET.fromstring(xml)
        items = []
        for item in root.findall(".//item")[:max_items]:
            title   = item.findtext("title", "").strip()
            link    = item.findtext("link", "").strip()
            desc    = re.sub(r"<[^>]+>", "", item.findtext("description", "")).strip()[:400]
            if title and link:
                items.append({"title": title, "url": link, "snippet": desc})
        return items
    except Exception as e:
        log(f"  Google News fetch failed for '{query}': {e}")
        return []

def extract_disability_angle(title, snippet, url):
    """Ask LLM to find the hidden disability angle in a mainstream article.
    Returns angle string or None if no meaningful angle found."""
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
        f"Article: {title}\n"
        f"Source: {url}\n"
        f"Snippet: {snippet}\n\n"
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
        return None if angle.upper().startswith("NONE") or len(angle) < 15 else angle
    except Exception as e:
        log(f"  LLM extraction failed: {e}")
        return None

def save_finding(url, title, angle, domain, snippet, source_type="google_news"):
    """Save a finding to the DB. Returns True if new, False if duplicate."""
    finding_id = hashlib.md5(url.encode()).hexdigest()
    conn = sqlite3.connect(DB)
    try:
        conn.execute("""
            INSERT INTO findings
              (id, url, title, angle, confidence, domain, source_type,
               source_details, disability_concepts, content_snippet,
               discovered_date, status, used_for_article)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            finding_id, url, title, angle,
            0.75,   # default confidence for LLM-extracted angles
            domain, source_type,
            f"Google News: {source_type}", json.dumps(["hidden_angle"]),
            snippet[:300], datetime.now().isoformat(), "pending", 0,
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False   # already exists
    finally:
        conn.close()

TEMPLATE_PATTERNS = [
    r"^The \w+ Perspective on '",
    r"^Disability Insight: How '",
    r"^What '.+' Misses About",
    r"^Inclusive Analysis:",
    r"^Accessibility Critique:",
    r"^The \w+ Story Behind '",
    r": The \w+ Story Behind '",
    r": The \w+ Dimension of '",
]

def _is_template_angle(angle):
    if not angle:
        return True
    if angle.strip().upper().startswith("NONE"):
        return True
    import re as _re
    for p in TEMPLATE_PATTERNS:
        if _re.match(p, angle):
            return True
    return False

def run_rss_crawler():
    """Run the existing disability RSS crawler, then LLM-verify its angles."""
    log("Running RSS disability crawler...")
    try:
        sys.path.insert(0, str(REPO))
        from rss_disability_crawler import RSSDisabilityCrawler
        crawler = RSSDisabilityCrawler()
        crawler.db_path = str(DB)
        crawler.run_rss_crawl()
        log("RSS crawler done")
    except Exception as e:
        log(f"RSS crawler error: {e}")
        return

    # LLM verification pass — remove template angles, replace with real ones or delete
    log("Verifying RSS angles via LLM...")
    conn = sqlite3.connect(DB)
    rows = conn.execute(
        "SELECT id, title, angle, url, content_snippet FROM findings WHERE source_type='rss'"
    ).fetchall()
    kept = deleted = 0
    for finding_id, title, angle, url, snippet in rows:
        if not _is_template_angle(angle):
            kept += 1
            continue
        real_angle = extract_disability_angle(title, snippet, url)
        if real_angle:
            conn.execute(
                "UPDATE findings SET angle=?, confidence=0.75 WHERE id=?",
                (real_angle, finding_id)
            )
            conn.commit()
            log(f"  + verified: {title[:50]}")
            kept += 1
        else:
            conn.execute("DELETE FROM findings WHERE id=?", (finding_id,))
            conn.commit()
            log(f"  - removed (no disability angle): {title[:50]}")
            deleted += 1
        time.sleep(0.5)
    conn.close()
    log(f"RSS verification done: {kept} kept, {deleted} removed")

def run_google_news_discovery():
    """Fetch Google News for mainstream queries, extract disability angles via LLM."""
    log(f"Running Google News discovery ({len(MAINSTREAM_QUERIES)} queries)...")
    new_total = 0

    for query in MAINSTREAM_QUERIES:
        log(f"  Query: {query}")
        items = fetch_google_news_rss(query, max_items=4)

        for item in items:
            domain = re.sub(r"https?://(?:www\.)?([^/]+).*", r"\1", item["url"])
            angle = extract_disability_angle(item["title"], item["snippet"], item["url"])

            if angle:
                saved = save_finding(
                    url=item["url"],
                    title=item["title"],
                    angle=angle,
                    domain=domain,
                    snippet=item["snippet"],
                    source_type="google_news",
                )
                if saved:
                    log(f"    + [{domain}] {angle[:80]}")
                    new_total += 1
            time.sleep(0.5)   # gentle rate limit on LLM calls

        time.sleep(1)

    log(f"Google News discovery done — {new_total} new findings")
    return new_total

def main():
    log("=== Discovery run start ===")

    # 1. Disability-specific RSS sources
    run_rss_crawler()

    # 2. Mainstream Google News + LLM angle extraction
    if API_KEY:
        run_google_news_discovery()
    else:
        log("WARN: ANTHROPIC_API_KEY not set — skipping Google News LLM extraction")

    # Summary
    conn = sqlite3.connect(DB)
    total, unused = conn.execute(
        "SELECT COUNT(*), SUM(CASE WHEN used_for_article=0 THEN 1 ELSE 0 END) FROM findings"
    ).fetchone()
    conn.close()
    log(f"DB: {total} total findings, {unused} unused")
    log("=== Discovery run done ===")

if __name__ == "__main__":
    main()
