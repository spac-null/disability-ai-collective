"""
research.py -- bounded pre-writing research for NEW_ENGINE_V1.

WHY THIS STAGE EXISTS
Before it, the anchor snapshot was the entire corpus an article was built from. The
28 August 2026 production run made that visible: a 1,245-word Dezeen roundup whose
subject-relevant material was 118 words of the project's own promotional copy became a
637-word interpretive feature, because the only way to reach that length from one fact
is to read the fact five times. Downstream web fact-checking did not help -- it verifies
a finished article and is a separate responsibility that stays exactly where it is.

WHAT IT DOES
Scopes the anchor, searches for candidate material, FETCHES the candidates, verifies
that every excerpt it hands downstream is a verbatim span of something actually
fetched, collapses duplicates, and returns a frozen RESEARCH_PACK plus a sufficiency
verdict. Everything downstream (Discovery, Form, Writer, Grounding) reads the pack.

WHAT IT DELIBERATELY DOES NOT DO
  - It is not a crawler. Every phase has a hard cap; see BOUNDS.
  - A search result is not a source. A snippet, a model citation and a Sonar summary
    can only ever NAME a page; material enters the pack solely from bytes fetched from
    the source URL, hashed, and persisted.
  - It never imports orchestrator.fact_check. The verifier must not become a research
    dependency, so search here uses its own narrow client (same public transport, no
    shared code, no backwards edge).
  - It has no opinion about article quality. It reports what material exists; the
    sufficiency rule below is deterministic and model-free.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

from .contracts import sha256_text
from .provider import ProviderError, parse_json_object

# ── BOUNDS (an article pipeline, not a crawler) ────────────────────────────────
MAX_QUERIES = 4               # search calls per run
MAX_CANDIDATE_URLS = 12       # distinct URLs considered for fetching
MAX_FETCHED_SOURCES = 5       # successful fetches kept, excluding the anchor
PER_SOURCE_CHARS = 12_000     # text kept per fetched source
PACK_TEXT_BUDGET = 40_000     # total pack text across all sources
FETCH_TIMEOUT = 20            # seconds; one attempt per URL, no retry loop
SEARCH_MODEL = "perplexity/sonar"
OPENROUTER_URL = "https://openrouter.ai/api/v1"
UA = "Mozilla/5.0 (compatible; CripMinds/1.0; +editorial research)"

# Sufficiency floors. Subject-relevant material (SRM) is counted in words of
# VERIFIED verbatim excerpt -- not document length, which is what let a roundup
# look substantial while saying 118 words about its actual subject.
SRM_ARTICLE_WORDS = 400
SRM_SHORT_WORDS = 150
ANCHOR_RICH_WORDS = 600       # single-source exception, subject-relevant only
NEAR_DUPLICATE_JACCARD = 0.6

ARTICLE = "ARTICLE"
SHORT_ARTICLE = "SHORT_ARTICLE"
NARROW = "NARROW"
HOLD = "HOLD_INSUFFICIENT_RESEARCH"

ROLE_ANCHOR = "ANCHOR"
ROLE_PRIMARY = "PRIMARY"
ROLE_INDEPENDENT = "INDEPENDENT"
ROLE_TERTIARY = "TERTIARY"
ROLE_CONTEXT = "CONTEXT"
ROLE_COUNTERWEIGHT = "COUNTERWEIGHT"
ROLES = (ROLE_ANCHOR, ROLE_PRIMARY, ROLE_INDEPENDENT, ROLE_TERTIARY,
         ROLE_CONTEXT, ROLE_COUNTERWEIGHT)

# Roles that can establish independence. TERTIARY is excluded on purpose: an
# encyclopaedia entry, a database record or an aggregated profile summarises other
# people's reporting, so counting it as an independent account would let one underlying
# story appear twice. It may still carry real subject material -- and does -- which is
# why it contributes verified words while buying no independence and satisfying no
# requirement for a first-party source.
SUPPORTING_ROLES = (ROLE_PRIMARY, ROLE_INDEPENDENT, ROLE_COUNTERWEIGHT)
# Roles whose verified excerpts count as subject-relevant material.
MATERIAL_ROLES = SUPPORTING_ROLES + (ROLE_TERTIARY,)


class ResearchError(ProviderError):
    """Research could not be performed -- transport, key or search failure.

    A subclass of ProviderError on purpose: to the run record this is infrastructure,
    not editorial judgement, and it must read as PROVIDER_FAILURE so the scheduled
    wrapper alerts an operator. "We could not read enough" and "there was not enough
    to read" are different answers and must never collapse into one.
    """


# ── deterministic helpers ─────────────────────────────────────────────────────
def domain_of(url: str) -> str:
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def registrable(url_or_host: str) -> str:
    """Last two labels of the host. Deliberately crude: it over-merges a few
    public suffixes (foo.co.uk and bar.co.uk read as co.uk), which errs toward
    calling two sources the SAME publisher -- the safe direction for an
    independence test."""
    host = domain_of(url_or_host) if "//" in url_or_host else url_or_host.lower()
    parts = [p for p in host.split(".") if p]
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def _shingles(text: str, n: int = 5) -> set:
    w = re.findall(r"[a-z0-9]+", (text or "").lower())
    return {tuple(w[i:i + n]) for i in range(max(0, len(w) - n + 1))}


def near_duplicate(a: str, b: str, threshold: float = NEAR_DUPLICATE_JACCARD) -> bool:
    """Bounded near-duplicate test: 5-gram Jaccard over the first PER_SOURCE_CHARS.
    Catches syndication, mirrored press releases and reprints, which is the whole
    job -- three copies of one announcement are one source, not three."""
    sa, sb = _shingles(a[:PER_SOURCE_CHARS]), _shingles(b[:PER_SOURCE_CHARS])
    if not sa or not sb:
        return False
    inter = len(sa & sb)
    return inter / float(len(sa | sb)) >= threshold


def strip_html(html: str) -> str:
    t = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", html)
    t = re.sub(r"(?is)<br\s*/?>|</p>|</div>|</li>|</h[1-6]>", "\n", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    t = (t.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"')
          .replace("&#39;", "'").replace("&lt;", "<").replace("&gt;", ">"))
    t = re.sub(r"[ \t\r\f\v]+", " ", t)
    return re.sub(r"\n\s*\n\s*\n+", "\n\n", t).strip()


def _title_from_html(html: str) -> str:
    m = re.search(r"(?is)<title[^>]*>(.*?)</title>", html or "")
    return re.sub(r"\s+", " ", strip_html(m.group(1))).strip()[:200] if m else ""


def _canonical_from_html(html: str) -> str:
    m = re.search(r'(?is)<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', html or "")
    return m.group(1).strip() if m else ""


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


# ── network: search names pages, fetch supplies material ──────────────────────
def _post_json(url: str, key: str, payload: dict, timeout: int) -> dict:
    req = urllib.request.Request(
        url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer %s" % key},
        method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def search_urls(query: str, *, api_key: str = "", timeout: int = 60) -> list:
    """Return candidate URLs for one query. NAMES pages; supplies no material.

    Its own narrow client on purpose: research must not import the downstream
    verifier (orchestrator.fact_check), which uses the same public transport for a
    different responsibility. Nothing in this function's return value can reach an
    article -- only fetched bytes can.
    """
    key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        raise ResearchError("OPENROUTER_API_KEY not set -- cannot search")
    try:
        body = _post_json(OPENROUTER_URL, key, {
            "model": SEARCH_MODEL,
            "messages": [
                {"role": "system", "content":
                 "You find primary and independent sources. Reply with a plain list of "
                 "full URLs, one per line, no commentary. Prefer first-party pages "
                 "(project, institution, paper, report, archive) and independent "
                 "reporting or scholarship. No aggregators, no social posts."},
                {"role": "user", "content": query}],
            "max_tokens": 700,
        }, timeout)
    except Exception as e:                                   # transport of any kind
        raise ResearchError("search failed: %s: %s" % (type(e).__name__, e))
    text = ((body.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    urls = re.findall(r"https?://[^\s<>\"')\]]+", text)
    for c in (body.get("citations") or []):
        if isinstance(c, str) and c.startswith("http"):
            urls.append(c)
    out, seen = [], set()
    for u in urls:
        u = u.rstrip(".,;)")
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def fetch_source(url: str, *, timeout: int = FETCH_TIMEOUT) -> dict:
    """One attempt. Returns a record whose `status` decides whether it may contribute.

    Anything other than status 'ok' with non-empty text supplies NO material: a
    paywall, a 403, a timeout and an empty body are all the same answer here, which
    is that nothing was read.
    """
    rec = {"url": url, "status": "", "text": "", "title": "", "canonical_url": "",
           "content_length": 0, "sha256": ""}
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            ctype = (r.headers.get("Content-Type") or "").lower()
            raw = r.read(2_000_000)
        if "html" not in ctype and "text" not in ctype:
            rec["status"] = "unsupported_content_type:%s" % (ctype.split(";")[0] or "?")
            return rec
        html = raw.decode(r.headers.get_content_charset() or "utf-8", "replace")
        text = strip_html(html)[:PER_SOURCE_CHARS]
        if len(text.split()) < 60:
            rec["status"] = "empty_or_blocked"
            return rec
        rec.update(status="ok", text=text, title=_title_from_html(html),
                   canonical_url=_canonical_from_html(html),
                   content_length=len(text), sha256=sha256_text(text))
    except urllib.error.HTTPError as e:
        rec["status"] = "http_%s" % e.code
    except Exception as e:
        rec["status"] = "%s" % type(e).__name__
    return rec


# ── model-assisted stages (both bounded to one call each) ─────────────────────
SCOPE_SYSTEM = (
    "You scope research before an article exists. You do not decide what the article "
    "argues -- that happens later, from the evidence you help gather. Name what is "
    "concretely there and what would have to be read to understand it.\n"
    "Judge the anchor honestly: a roundup entry or a press blurb is thin no matter how "
    "interesting it sounds, and a paper, report, judgment, dataset or long interview is "
    "rich even when it is dull.\n"
    "If the anchor covers SEVERAL unrelated subjects -- a roundup, a school show, a list, "
    "a digest -- choose exactly ONE and scope everything to it. Every query you write "
    "must serve that one subject; a query about another item on the list is wasted, and "
    "the article will not be about it. Mark the chosen subject with `subject_span`: a "
    "span copied CHARACTER-FOR-CHARACTER from the anchor covering that subject and "
    "nothing else, from where it starts to where it ends. It is checked against the "
    "anchor programmatically, and the article that follows is confined to it."
)


def scope_prompt(anchor_text: str, sha: str) -> str:
    return (
        "ANCHOR SOURCE (sha256 %s):\n<<<SOURCE\n%s\nSOURCE>>>\n\n"
        "Reply with JSON only:\n"
        "{\n"
        '  "subject": "the concrete subject: the object, project, work, event, person '
        'or decision this would be about",\n'
        '  "named_entities": ["people, institutions, works, places, documents actually '
        'named in the anchor"],\n'
        '  "questions": ["concrete questions raised by the anchor that reading would '
        'answer -- factual, not thematic"],\n'
        '  "queries": ["at most %d search queries that would find primary or '
        'independent material. Name the entity; do not search for a thesis."],\n'
        '  "anchor_kind": "roundup_entry|press_release|news_report|feature|paper|report|'
        'judgment|dataset|interview|archive|other",\n'
        '  "anchor_subject_words": integer  // words in the anchor that are ABOUT the '
        'subject, not about neighbouring items,\n'
        '  "subject_span": "verbatim span of the anchor covering the chosen subject '
        'only -- REQUIRED when the anchor covers several unrelated subjects, empty '
        'string when the whole anchor is about one subject",\n'
        '  "narrower_subject": "" or a narrower subject the anchor actually supports\n'
        "}\n" % (sha[:16], anchor_text[:20_000], MAX_QUERIES))


def scope(provider, anchor_text: str, sha: str) -> dict:
    c = provider.complete(SCOPE_SYSTEM, scope_prompt(anchor_text, sha), max_tokens=1200)
    p = parse_json_object(c.text)
    # The span is only worth anything if it is really in the anchor. A paraphrased or
    # invented span is dropped rather than carried, exactly like an excerpt -- and a
    # dropped span means the scope invariant downstream simply does not bind, never
    # that a wrong region does.
    span = p.get("subject_span")
    if not (isinstance(span, str) and span.strip()
            and _norm(span) in _norm(anchor_text)):
        p["subject_span"] = ""
    p["queries"] = [q for q in (p.get("queries") or []) if isinstance(q, str)][:MAX_QUERIES]
    try:
        p["anchor_subject_words"] = int(p.get("anchor_subject_words") or 0)
    except (TypeError, ValueError):
        p["anchor_subject_words"] = 0
    p["_provider"] = c.identity()
    return p


ASSESS_SYSTEM = (
    "You label fetched sources for an editorial research pack. You do not write, "
    "summarise or interpret. For each source you state its role, its relation to the "
    "anchor, and the spans in it that are ABOUT the subject.\n"
    "Every excerpt must be copied CHARACTER-FOR-CHARACTER from the source text you were "
    "given. Excerpts are checked programmatically and silently dropped if they are not "
    "exact spans, so do not paraphrase, do not merge two places, do not tidy anything.\n"
    "Give at most 6 excerpts per source, each one to three sentences. The pack is a "
    "working corpus, not a transcript: quote the spans that carry facts, dates, names, "
    "numbers, mechanisms or a document's own wording, and stop.\n"
    "A source that is a copy, syndication or reprint of the anchor is not independent; "
    "say so in `relation`.\n"
    "Roles: PRIMARY is first-party -- the project, institution, author, paper, report, "
    "judgment or archive itself. INDEPENDENT is reporting, scholarship or criticism by "
    "someone else. TERTIARY is an encyclopaedia entry, database record, directory or "
    "aggregated profile: useful, often accurate, but a summary of other people's work "
    "rather than an account of its own. CONTEXT is background about a venue, school, "
    "publisher or field rather than about the subject. COUNTERWEIGHT complicates or "
    "bounds the reading.\n"
    "Only the subject named above is the subject. Material about the school, the venue, "
    "the publisher, the programme or another item in the same roundup is CONTEXT, "
    "however much vocabulary it shares with the subject."
)


def assess_prompt(subject: str, anchor_text: str, sources: list) -> str:
    blocks = []
    for s in sources:
        blocks.append("SOURCE %s  url=%s  publisher=%s\n<<<TEXT\n%s\nTEXT>>>"
                      % (s["source_id"], s["url"], s["publisher"], s["text"][:8000]))
    return (
        "SUBJECT: %s\n\nANCHOR (for comparison only):\n<<<ANCHOR\n%s\nANCHOR>>>\n\n%s\n\n"
        "Reply with JSON only:\n"
        '{"sources": [{"source_id": "...", "role": "PRIMARY|INDEPENDENT|CONTEXT|'
        'COUNTERWEIGHT", "relation": "corroborates|extends|complicates|contradicts|'
        'background|duplicate_of_anchor", "why_relevant": "one plain sentence", '
        '"excerpts": ["verbatim spans about the subject"]}]}\n'
        % (subject, anchor_text[:6000], "\n\n".join(blocks)))


def assess(provider, subject: str, anchor_text: str, sources: list) -> dict:
    if not sources:
        return {"sources": []}
    # Sized against the real bound: at most MAX_FETCHED_SOURCES sources x 6 excerpts.
    # A truncated reply is not valid JSON and correctly HOLDs the run as a provider
    # error -- which is what happened on the first live end-to-end at 3000 tokens.
    c = provider.complete(ASSESS_SYSTEM, assess_prompt(subject, anchor_text, sources),
                          max_tokens=6000)
    p = parse_json_object(c.text)
    p["_provider"] = c.identity()
    return p


# ── pack assembly ─────────────────────────────────────────────────────────────
def verified_excerpts(claimed, source_text: str) -> tuple:
    """Keep only spans that really are in the fetched bytes. Returns (kept, dropped)."""
    hay = _norm(source_text)
    kept, dropped = [], []
    for e in (claimed or []):
        if isinstance(e, str) and len(e.split()) >= 4 and _norm(e) in hay:
            kept.append(e.strip())
        elif isinstance(e, str) and e.strip():
            dropped.append(e.strip()[:120])
    return kept, dropped


def build_pack(*, anchor: dict, scoped: dict, fetched: list, assessment: dict,
               searched: dict) -> dict:
    """Assemble the frozen pack. Deterministic given its inputs -- replayable."""
    by_id = {s["source_id"]: s for s in fetched}
    labels = {a.get("source_id"): a for a in (assessment.get("sources") or [])}

    anchor_src = {
        "source_id": "S0", "role": ROLE_ANCHOR, "url": anchor["url"],
        "canonical_url": anchor.get("canonical_url", ""),
        "publisher": registrable(anchor["url"]), "title": anchor.get("title", ""),
        "accessed_at": anchor["accessed_at"], "fetch_status": "ok",
        "sha256": sha256_text(anchor["text"]), "content_length": len(anchor["text"]),
        "relation": "anchor", "duplicate_cluster": 0, "why_relevant": "anchor source",
        "text": anchor["text"], "excerpts": [], "excerpts_dropped": [],
    }

    sources, budget = [anchor_src], PACK_TEXT_BUDGET - len(anchor["text"])
    clusters = [[anchor_src]]
    budget_dropped = []
    MIN_USEFUL_CHARS = 1000
    for s in fetched:
        # A source the budget cannot carry is DROPPED, not carried empty. A pack entry
        # with no text is a citation, and a citation is not a source here -- it would
        # also be unverifiable, since every excerpt must be a span of carried text.
        if budget < MIN_USEFUL_CHARS:
            budget_dropped.append({"source_id": s["source_id"], "url": s["url"],
                                   "reason": "pack text budget exhausted"})
            continue
        lab = labels.get(s["source_id"], {})
        role = lab.get("role") if lab.get("role") in ROLES else ROLE_CONTEXT
        if role == ROLE_ANCHOR:
            role = ROLE_CONTEXT
        cluster = None
        for i, group in enumerate(clusters):
            if any(near_duplicate(s["text"], g["text"]) for g in group):
                cluster = i
                group.append(s)
                break
        if cluster is None:
            clusters.append([s])
            cluster = len(clusters) - 1
        text = s["text"][:max(0, budget)]
        budget -= len(text)
        # Excerpts are verified against the text the pack will actually CARRY, not the
        # text that was fetched. The two differ once the budget truncates a source, and
        # verifying against the longer one would ship a span nothing downstream can see
        # -- found by the contract check on the first live run, which is what it is for.
        kept, dropped = verified_excerpts(lab.get("excerpts"), text)
        sources.append({
            "source_id": s["source_id"], "role": role, "url": s["url"],
            "canonical_url": s.get("canonical_url", ""), "publisher": s["publisher"],
            "title": s.get("title", ""), "accessed_at": s["accessed_at"],
            "fetch_status": s["status"], "sha256": sha256_text(text),
            "content_length": len(text),
            "relation": lab.get("relation", "background"),
            "duplicate_cluster": cluster,
            "why_relevant": (lab.get("why_relevant") or "")[:300],
            "text": text, "excerpts": kept, "excerpts_dropped": dropped,
        })

    anchor_reg = registrable(anchor["url"])
    # CONTEXT is background and cannot, on its own, make an article possible. The live
    # 28 August regression is why this rule is explicit: research on a roundup entry
    # returned four university programme pages -- real, fetched, hashed, genuinely
    # independent of the publisher, and about the SCHOOL rather than the subject. Under
    # a role-blind count that boilerplate would have bought a short article about a
    # tactile booklet. Support means PRIMARY, INDEPENDENT or COUNTERWEIGHT material.
    def _usable(s, roles):
        return (s["role"] in roles and s["duplicate_cluster"] != 0
                and s["publisher"] != anchor_reg
                and s["relation"] != "duplicate_of_anchor" and s["excerpts"])

    supporting = [s for s in sources[1:] if _usable(s, SUPPORTING_ROLES)]
    material = [s for s in sources[1:] if _usable(s, MATERIAL_ROLES)]
    independent_clusters = sorted({s["duplicate_cluster"] for s in supporting})
    # Independence is counted per PUBLISHER, not per page. The live Minnie Evans
    # regression returned two Whitney pages and two High Museum pages: four distinct
    # documents, four duplicate clusters, and two institutions. Counting pages would
    # let one institution corroborate itself, which is the syndication failure wearing
    # a different hat.
    independent_publishers = sorted({s["publisher"] for s in supporting})
    srm_words = sum(len(" ".join(s["excerpts"]).split()) for s in material)
    tertiary_words = sum(len(" ".join(s["excerpts"]).split())
                         for s in material if s["role"] == ROLE_TERTIARY)
    context_words = sum(len(" ".join(s["excerpts"]).split())
                        for s in sources[1:] if s["role"] == ROLE_CONTEXT)

    pack = {
        "subject": scoped.get("subject", ""),
        "questions": scoped.get("questions", [])[:10],
        "queries": searched.get("queries", []),
        "candidates_considered": searched.get("candidates", []),
        "anchor_kind": scoped.get("anchor_kind", "other"),
        "anchor_subject_words": scoped.get("anchor_subject_words", 0),
        "subject_span": scoped.get("subject_span", "") or "",
        "narrower_subject": scoped.get("narrower_subject", "") or "",
        "sources": sources,
        "coverage": {
            "fetched_ok": len(sources) - 1,
            "budget_dropped": budget_dropped,
            "fetch_failures": searched.get("failures", []),
            "roles_present": sorted({s["role"] for s in sources}),
            "distinct_publishers": len({s["publisher"] for s in sources}),
            "duplicate_clusters": len(clusters),
            "independent_clusters": len(independent_clusters),
            "independent_publishers": len(independent_publishers),
            "subject_relevant_words": srm_words,
            "tertiary_words": tertiary_words,
            "context_only_words": context_words,
        },
    }
    pack["sufficiency"] = sufficiency(pack)
    pack["pack_sha256"] = sha256_text(json.dumps(
        {k: v for k, v in pack.items() if k != "pack_sha256"},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    return pack


def sufficiency(pack: dict) -> dict:
    """Model-free verdict over roles, independence and subject-relevant material.

    Roles and independence, never a URL count: three copies of one press release
    collapse into one cluster and cannot buy independence, and one genuinely rich
    primary anchor can carry a narrow piece with no support at all.
    """
    cov = pack["coverage"]
    # The binding number is whichever is smaller: distinct duplicate clusters (a
    # syndicated story is one source) and distinct publishers (one institution's two
    # pages are one source). Both failure modes have been seen live.
    ind = min(cov["independent_clusters"],
              cov.get("independent_publishers", cov["independent_clusters"]))
    srm = cov["subject_relevant_words"]
    roles = set(cov["roles_present"])
    # PRIMARY means first-party. No other role substitutes for it, and no publisher or
    # domain is named anywhere in this function: classification assigns the role,
    # sufficiency reads it.
    primary = ROLE_PRIMARY in roles
    counterweight = ROLE_COUNTERWEIGHT in roles
    anchor_rich = (pack.get("anchor_subject_words", 0) >= ANCHOR_RICH_WORDS
                   and pack.get("anchor_kind") in
                   ("paper", "report", "judgment", "dataset", "interview", "archive"))
    reasons = ["independent=%d (clusters=%d, publishers=%s)"
               % (ind, cov["independent_clusters"],
                  cov.get("independent_publishers", "?")), "subject_relevant_words=%d" % srm,
               "roles=%s" % ",".join(sorted(roles)),
               "anchor_kind=%s(%d subject words)" % (pack.get("anchor_kind"),
                                                     pack.get("anchor_subject_words", 0))]

    if ind >= 2 and srm >= SRM_ARTICLE_WORDS and (primary or ind >= 3):
        v, missing = ARTICLE, []
    elif ind >= 1 and srm >= SRM_SHORT_WORDS:
        v, missing = SHORT_ARTICLE, ["not enough independent material for a full feature"]
    elif anchor_rich:
        v, missing = SHORT_ARTICLE, ["single rich primary source; scope must stay narrow"]
    else:
        v = HOLD
        if not ind and cov.get("context_only_words"):
            missing = ["only background/context material was found (%d words); nothing "
                       "primary or independent about the subject itself"
                       % cov["context_only_words"]]
        elif not ind:
            missing = ["no primary or independent source with verified subject material"]
        else:
            missing = ["subject-relevant material below the floor (%d < %d words)"
                       % (srm, SRM_SHORT_WORDS)]

    if v in (SHORT_ARTICLE, ARTICLE) and pack.get("narrower_subject"):
        v = NARROW
        missing = ["material supports the narrower subject: %s" % pack["narrower_subject"]]
    if v == ARTICLE and not counterweight:
        reasons.append("no counterweight source; the argument must not rest on a broad "
                       "or contested comparison")
    return {"verdict": v, "reasons": reasons, "what_is_missing": missing}


# ── orchestration (one bounded pass) ──────────────────────────────────────────
def research(provider, *, anchor: dict, now_iso: str, api_key: str = "") -> dict:
    """Scope -> search -> fetch -> assess -> pack. Raises ResearchError on a
    provider/transport failure so the caller can fail closed; it never returns a
    pack it could not actually build."""
    scoped = scope(provider, anchor["text"], sha256_text(anchor["text"]))
    candidates, failures, seen = [], [], set()
    queries = scoped.get("queries", [])[:MAX_QUERIES]
    for q in queries:
        try:
            found = search_urls(q, api_key=api_key)
        except ResearchError as e:
            failures.append({"query": q, "error": str(e)[:200]})
            continue
        for u in found:
            if len(candidates) >= MAX_CANDIDATE_URLS:
                break
            if u in seen or u == anchor["url"]:
                continue
            seen.add(u)
            candidates.append(u)

    fetched = []
    for i, url in enumerate(candidates, 1):
        if len(fetched) >= MAX_FETCHED_SOURCES:
            break
        rec = fetch_source(url)
        if rec["status"] != "ok":
            failures.append({"url": url, "status": rec["status"]})
            continue
        rec.update(source_id="S%d" % (len(fetched) + 1), accessed_at=now_iso,
                   publisher=registrable(url))
        fetched.append(rec)

    assessment = assess(provider, scoped.get("subject", ""), anchor["text"], fetched)
    pack = build_pack(anchor=anchor, scoped=scoped, fetched=fetched,
                      assessment=assessment,
                      searched={"queries": queries, "candidates": candidates,
                                "failures": failures})
    pack["_provider"] = {"scope": scoped.get("_provider", {}),
                         "assess": assessment.get("_provider", {})}
    return pack
