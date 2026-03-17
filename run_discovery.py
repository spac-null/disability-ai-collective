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

# Load secrets from env file (no export statements — must parse manually)
_ENV_FILE = Path("/srv/secrets/openclaw.env")
if _ENV_FILE.exists():
    for _line in _ENV_FILE.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())


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

    # Europe — policy, culture, design
    "NHS social care funding reform UK community",
    "EU Accessibility Act digital services compliance 2025",
    "UK Personal Independence Payment PIP assessment reform",
    "European mental health deinstitutionalization social care",
    "UK zero hours contract gig work insecurity",
    "Cannes Berlin Venice film festival programming selection",
    "Edinburgh Fringe festival performance casting diversity",
    "European city urban mobility pedestrian cycling design",
    "Scandinavia welfare model work life balance reform",
    "West End theater casting body representation",

    # Latin America — policy, culture, design
    "Brazil social assistance benefit reform inclusion",
    "Latin America care economy community informal network",
    "Colombia Chile Argentina mental health policy reform",
    "Brazil urban favela city planning infrastructure access",
    "Latin America film festival documentary social justice",
    "São Paulo Mexico City urban design transit equity",

    # Asia & Pacific — policy, culture, design
    "Japan overwork karoshi workplace culture burnout reform",
    "South Korea workplace mental health burnout productivity",
    "Australia NDIS disability insurance funding reform",
    "Japan aging population care workforce shortage",
    "India urban infrastructure accessible city design",
    "Busan Tokyo film festival selection programming",
    "China tech company hiring algorithm screening",
    "South Korea Japan neurodiversity workplace stigma",

    # Global / non-US international
    "global south climate disaster vulnerable population evacuation",
    "universal design international building standard",
    "WHO mental health global policy community care",
    "international aid development disability inclusion",
    "global aging population care workforce crisis",

    # Historical & comparative — Bregman register
    # Stories that bridge past and present, reframe current debates through
    # unexpected historical parallels. What disability culture knew before
    # mainstream discourse caught up.
    "shipwreck survival isolation community cooperation history",
    "archaeological evidence ancient disability care survival burial",
    "indigenous community care elder disabled traditional knowledge",
    "wartime rehabilitation disability injury prosthetics history adaptation",
    "asylum mental hospital deinstitutionalization history reform community",
    "forgotten inventor engineer accessible design history technology",
    "oral history disability rights movement archive testimony",
    "natural disaster community mutual aid unexpected solidarity response",
    "historical accident industrial design failure lesson safety",
    "medieval historical disability care monastery community record",
    "nineteenth century freak show exhibition disability history reclaim",
    "deaf school history residential community sign language suppression",
    "blind school history reading braille tactile innovation",
    "polio iron lung survivor history disability rights movement connection",
    "disability history movement 504 sit-in occupation protest archive",
    "thalidomide disability rights history pharmaceutical accountability",
    "island community isolated adaptive improvised culture anthropology",
    "ancient Rome Greece disability evidence archaeological historical",
    "historical eugenics disability forced sterilization reckoning",
    "science overturned assumption rethink paradigm disability perception",
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


# ── Step 9a: PubMed academic abstract discovery ───────────────────────────────

PUBMED_TERMS = [
    "disability AND (design OR architecture OR art)",
    "disability AND (technology OR interface OR digital)",
    "neurodivergent AND (culture OR identity OR epistemology)",
    "deaf AND (culture OR language OR visual)",
    "chronic illness AND (culture OR representation OR narrative)",
    "crip theory OR disability justice",
]

def run_pubmed_discovery():
    """Fetch recent PubMed abstracts on disability + culture/design/tech."""
    log("Running PubMed discovery...")
    import urllib.parse
    new = 0
    for term in PUBMED_TERMS:
        try:
            # Search for PMIDs
            params = urllib.parse.urlencode({
                "db": "pubmed", "term": term,
                "retmax": 5, "retmode": "json", "sort": "date"
            })
            url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{params}"
            req = urllib.request.Request(url, headers={"User-Agent": "CripMinds/1.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            pmids = data.get("esearchresult", {}).get("idlist", [])
            if not pmids:
                continue

            # Fetch abstracts
            fetch_url = (
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?"
                f"db=pubmed&id={','.join(pmids)}&retmode=xml&rettype=abstract"
            )
            req2 = urllib.request.Request(fetch_url, headers={"User-Agent": "CripMinds/1.0"})
            with urllib.request.urlopen(req2, timeout=15) as r:
                xml_text = r.read().decode("utf-8", errors="replace")

            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_text)
            for article in root.iter("PubmedArticle"):
                try:
                    title_el    = article.find(".//ArticleTitle")
                    abstract_el = article.find(".//AbstractText")
                    pmid_el     = article.find(".//PMID")
                    if title_el is None or abstract_el is None or pmid_el is None:
                        continue
                    title    = (title_el.text or "").strip()
                    abstract = (abstract_el.text or "").strip()[:500]
                    pmid     = pmid_el.text.strip()
                    url_art  = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                    angle    = extract_disability_angle(title, abstract, url_art)
                    if angle:
                        saved = save_finding(url_art, title, angle, "pubmed.ncbi.nlm.nih.gov",
                                             abstract, source_type="academic")
                        if saved:
                            new += 1
                            log(f"  + PubMed: {title[:60]}")
                except Exception as e:
                    log(f"  PubMed article parse error: {e}")
            time.sleep(1)  # rate limit
        except Exception as e:
            log(f"  PubMed term '{term[:40]}' failed: {e}")
    log(f"PubMed discovery done: {new} new findings")


# ── Step 9b: Art institution RSS feeds ───────────────────────────────────────

ART_FEEDS = [
    {"url": "https://vanabbemuseum.nl/en/feed/",             "domain": "vanabbemuseum.nl"},
    {"url": "https://www.mediamatic.net/en/rss/",            "domain": "mediamatic.net"},
    {"url": "https://internationaleonline.org/feed/",        "domain": "internationaleonline.org"},
    {"url": "https://www.puppetmastermagazine.net/feed/",    "domain": "puppetmastermagazine.net"},
]

def _parse_rss_feed(xml_bytes: bytes) -> list[dict]:
    """Parse RSS/Atom feed, return list of {title, url, snippet}."""
    try:
        root = ET.fromstring(xml_bytes)
    except Exception:
        return []
    items = []
    # RSS 2.0
    for item in root.iter("item"):
        title_el = item.find("title")
        link_el  = item.find("link")
        desc_el  = item.find("description")
        if title_el is None or link_el is None:
            continue
        title   = re.sub(r'<[^>]+>', '', title_el.text or "").strip()
        url_i   = (link_el.text or "").strip()
        snippet = re.sub(r'<[^>]+>', '', desc_el.text or "")[:300].strip() if desc_el is not None else ""
        if title and url_i:
            items.append({"title": title, "url": url_i, "snippet": snippet})
    # Atom fallback
    if not items:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", ns):
            title_el = entry.find("atom:title", ns)
            link_el  = entry.find("atom:link", ns)
            summ_el  = entry.find("atom:summary", ns)
            if title_el is None or link_el is None:
                continue
            items.append({
                "title":   (title_el.text or "").strip(),
                "url":     link_el.get("href", "").strip(),
                "snippet": re.sub(r'<[^>]+>', '', summ_el.text or "")[:300].strip() if summ_el is not None else "",
            })
    return items


def run_art_feeds_discovery():
    """Fetch art institution RSS feeds and extract disability angles."""
    log("Running art feeds discovery...")
    new = 0
    for feed in ART_FEEDS:
        try:
            req = urllib.request.Request(
                feed["url"],
                headers={"User-Agent": "CripMinds/1.0", "Accept": "application/rss+xml, text/xml"}
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                xml_bytes = r.read()
            items = _parse_rss_feed(xml_bytes)
            log(f"  {feed['domain']}: {len(items)} items")
            for item in items[:10]:
                angle = extract_disability_angle(item["title"], item["snippet"], item["url"])
                if angle:
                    saved = save_finding(item["url"], item["title"], angle,
                                         feed["domain"], item["snippet"], source_type="art")
                    if saved:
                        new += 1
                        log(f"  + art: {item['title'][:60]}")
            time.sleep(1)
        except Exception as e:
            log(f"  Art feed {feed['domain']} failed: {e}")
    log(f"Art feeds discovery done: {new} new findings")


def main():
    log("=== Discovery run start ===")

    # 1. Disability-specific RSS sources
    run_rss_crawler()

    # 2. Mainstream Google News + LLM angle extraction
    if API_KEY:
        run_google_news_discovery()
    else:
        log("WARN: ANTHROPIC_API_KEY not set — skipping Google News LLM extraction")

    # 3. PubMed academic abstracts
    if API_KEY:
        run_pubmed_discovery()

    # 4. Art institution RSS feeds
    if API_KEY:
        run_art_feeds_discovery()

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
