#!/usr/bin/env python3
"""
documents.py -- bounded text-layer extraction from PDFs, for the Research Pack.

WHY THIS EXISTS
On 2026-09-03 three manual production trials showed the engine losing the most
authoritative document about an article's own subject because it could not open a PDF.
Trial 3's subject WAS a technical report: OpenAI's incident postmortem and METR's
report on the same incident both came back `unsupported_content_type:application/pdf`,
so the article was written from other people's summaries of a document sitting one
fetch away. Trial 2 lost two MIT faculty-governance reports the same way.

WHAT THIS IS NOT
No OCR. No external binary. No browser, no JavaScript, no embedded attachments, no
forms or actions, no following a link found inside a document. The only output is
bounded plain text plus provenance. Text extracted from a PDF is untrusted source
content exactly like fetched HTML, and nothing here treats it as instruction.

WHERE THE PARSE ACTUALLY RUNS
Not here. pdf_extract, outside this package, spawns a short-lived worker and enforces
the deadline by killing it -- because a between-pages deadline check is not a bound:
opening a malformed object, resolving a cyclic xref or decompressing a crafted stream
all happen inside one call, and a check that only runs between pages never gets to run.
This package may not import subprocess (or sqlite3, requests, socket), a purity rule
that predates documents and that a parser is not a good enough reason to breach. So
this module owns the POLICY -- the bounds, the name of each failure, which pages are
carried, what provenance is recorded -- and none of the machinery.
"""
from __future__ import annotations

import hashlib
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
import pdf_extract as PDFX                                            # noqa: E402

# ── hard bounds ───────────────────────────────────────────────────────────────
# DOC_MAX_PAGES was 40 in the first draft and refused half the evidence this module was
# written for. The four documents the production trials actually lost are 16, 38, 80 and
# 91 pages, all with real text layers -- so a 40-page bound fixed two of four failures
# and called the other two untrustworthy for being long, which is not what length means.
# 100 is set from those measurements and nothing else.
#
# Length is the weakest of the five bounds anyway. Bytes cap what is read, the worker
# deadline caps how long any of it may take, and the carry bounds cap what reaches the
# pack -- and none of those moved. A long document costs parse time, and parse time is
# already bounded by something that kills it.
DOC_MAX_BYTES = 8 * 1024 * 1024      # 8 MiB; never read or parse beyond this
DOC_MAX_PAGES = 100                  # never TRUST a document longer than this;
                                     # raised from 40 on the evidence below
DOC_MAX_PAGES_CARRIED = 6            # pages that may enter the pack
DOC_MAX_CHARS_CARRIED = 18_000       # characters of document text in the pack
DOC_PARSE_TIMEOUT = 15               # seconds, wall clock, enforced by killing

PDF_MAGIC = b"%PDF-"
EXTRACTOR_NAME = "pypdf"

# ── statuses ──────────────────────────────────────────────────────────────────
# Every one of these means NO evidence. They are distinct because "we could not read
# it" and "there was nothing to read" are different facts about a source, and a run
# that loses evidence should say which happened.
PDF_TOO_LARGE = "pdf_too_large"
PDF_PAGE_LIMIT = "pdf_page_limit"
PDF_ENCRYPTED = "pdf_encrypted"
PDF_PARSE_ERROR = "pdf_parse_error"
PDF_PARSE_TIMEOUT = "pdf_parse_timeout"
PDF_NO_TEXT_LAYER = "pdf_no_text_layer"
PDF_UNAVAILABLE = "pdf_extractor_unavailable"
TYPE_MISMATCH = "type_mismatch"

# Below this many words in the WHOLE document there is no text layer to read.
#
# The line is low on purpose. It separates "nothing came out" from "something did",
# which is the only question here -- a scan yields zero words, or a handful of stray
# glyphs from a signature block. It is NOT a judgement about whether a document is
# worth reading: a one-page policy memo is a legitimate research source, and an earlier
# draft of this file set the floor at 40 and silently discarded exactly that. How good
# the material is gets decided later, by the assessor, from the text.
MIN_DOC_WORDS = 15

DOCUMENTS_ENV = "CRIPMINDS_RESEARCH_DOCUMENTS"
_OFF = ("0", "false", "no", "off")


def enabled() -> bool:
    """On unless explicitly switched off. The rollback is one environment value on the
    cron line -- CRIPMINDS_RESEARCH_DOCUMENTS=0 restores the pre-2026-09-03 behaviour,
    in which a PDF is reported unsupported and never opened."""
    return (os.environ.get(DOCUMENTS_ENV, "") or "").strip().lower() not in _OFF


def looks_like_pdf(head: bytes) -> bool:
    """The first five bytes, and nothing else. A Content-Type is a claim by the server;
    this is the file. HTML served as application/pdf fails here, which is the point."""
    return bool(head) and head[:len(PDF_MAGIC)] == PDF_MAGIC


def extractor_version() -> str:
    try:
        import importlib.metadata as md
        return md.version("pypdf")
    except Exception:
        return "unknown"


def available() -> bool:
    try:
        import pypdf                                                  # noqa: F401
        return True
    except Exception:
        return False


# ── the bounded parse ─────────────────────────────────────────────────────────
def parse(data: bytes, *, timeout: float = DOC_PARSE_TIMEOUT) -> dict:
    """Bounded parse. Returns {"pages": [{page_no, text}], "pages_available": n}
    or {"status": <one of the PDF_* statuses>}.

    One attempt. No retry, no OCR, no second parser.

    The work itself happens in pdf_extract, outside this package: it spawns a worker
    process to make the deadline real, and this package stays free of sqlite3,
    requests, socket and subprocess -- a purity boundary that predates documents and
    that a parser is not a good enough reason to breach. What lives here is the policy:
    the bounds, what each failure is called, which pages are carried, what provenance
    is recorded.
    """
    if len(data) > DOC_MAX_BYTES:
        # Checked before a worker exists: an oversize file must not be parsed at all.
        return {"status": PDF_TOO_LARGE}
    got = PDFX.parse_bounded(data, timeout=timeout, max_pages=DOC_MAX_PAGES)
    err = got.get("error")
    if err == "unavailable":
        return {"status": PDF_UNAVAILABLE}
    if err == "timeout":
        return {"status": PDF_PARSE_TIMEOUT}
    if err == "encrypted":
        return {"status": PDF_ENCRYPTED}
    if err == "page_limit":
        # Explicitly NOT "parse the first forty pages and call it the document".
        return {"status": PDF_PAGE_LIMIT, "pages_available": got.get("pages_available")}
    if err:
        return {"status": PDF_PARSE_ERROR}
    pages = got.get("pages") or []
    if not pages:
        return {"status": PDF_PARSE_ERROR}
    if sum(len(p.get("text", "").split()) for p in pages) < MIN_DOC_WORDS:
        # A scan. There is nothing here to read without OCR, and OCR is not in this
        # pipeline.
        return {"status": PDF_NO_TEXT_LAYER, "pages_available": got.get("pages_available")}
    return {"pages": pages, "pages_available": got.get("pages_available", len(pages))}


# ── deterministic page selection ──────────────────────────────────────────────
_WORD = None


def _tokens(text: str) -> list:
    global _WORD
    if _WORD is None:
        import re
        _WORD = re.compile(r"[a-z0-9]+")
    return _WORD.findall((text or "").lower())


# Terms this common carry no signal about which page matters.
_STOP = frozenset(
    "the a an and or but if of to in on for with by from at as is are was were be been "
    "this that these those it its his her their our your not no than then so such "
    "which who whom what when where how why all any both each few more most other some "
    "only own same too very can will just should now about into over under between".split())


def selection_terms(*parts) -> list:
    """The terms pages are scored against, taken from the research context that already
    exists at fetch time -- the subject and the queries. No model call: targeted
    research does not exist yet, and inventing a call here would be a second one."""
    seen, terms = set(), []
    for p in parts:
        for t in _tokens(p if isinstance(p, str) else " ".join(map(str, p or []))):
            if len(t) > 2 and t not in _STOP and t not in seen:
                seen.add(t)
                terms.append(t)
    return terms


def score_page(text: str, terms) -> float:
    """Normalised distinct-term overlap. Deterministic, and independent of page length
    so a long page of boilerplate cannot outscore a short page that is on subject."""
    if not terms:
        return 0.0
    toks = set(_tokens(text))
    if not toks:
        return 0.0
    return sum(1 for t in set(terms) if t in toks) / float(len(set(terms)))


def select_pages(pages: list, terms, *, max_pages: int = DOC_MAX_PAGES_CARRIED,
                 max_chars: int = DOC_MAX_CHARS_CARRIED) -> dict:
    """Pick at most `max_pages`, carry them in page order, and say what was left out.

    The rule that matters: a document is never replaced by its first N characters.
    Evidence lives on page 20 as readily as page 1, so pages are chosen by relevance
    and only then put back in reading order.

    When the chosen pages exceed the character bound, WHOLE pages are dropped -- the
    least relevant first, and on a tie the later page -- rather than pages being cut
    into fragments. Only a single page that alone exceeds the bound is cut, and that is
    recorded too. Nothing is omitted silently.
    """
    scored = [(score_page(p.get("text", ""), terms), -p["page_no"], p) for p in pages]
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    # Once ANY page is on subject, pages that match nothing are not carried: a
    # document's front matter would otherwise spend the character bound that the page
    # the evidence is actually on has to fit inside. When no page matches -- no terms,
    # or a document about something else -- the first pages stand, in order.
    if scored and scored[0][0] > 0:
        scored = [x for x in scored if x[0] > 0]
    top = scored[:max_pages]
    rank = {s[2]["page_no"]: i for i, s in enumerate(top)}     # 0 = most relevant
    kept = sorted((s[2] for s in top), key=lambda p: p["page_no"])

    def rendered(ps):
        return sum(len(page_marker(p["page_no"])) + 1
                   + len((p.get("text") or "").strip()) + 2 for p in ps)

    # Drop WHOLE pages, least relevant first and on a tie the later page, rather than
    # cutting pages into fragments.
    omitted = []
    while len(kept) > 1 and rendered(kept) > max_chars:
        worst = max(kept, key=lambda p: rank[p["page_no"]])
        kept.remove(worst)
        omitted.append(worst["page_no"])

    text_parts, locators, cursor, truncated = [], [], 0, False
    for p in kept:
        body = (p.get("text") or "").strip()
        marker = page_marker(p["page_no"])
        room = max_chars - cursor - len(marker) - 1
        if room <= 0:
            omitted.append(p["page_no"])
            truncated = True
            continue
        if len(body) > room:
            # The only cut this makes: one page alone larger than the whole bound.
            body = body[:room]
            truncated = True
        block = marker + "\n" + body
        start = cursor + len(marker) + 1
        text_parts.append(block)
        locators.append({"kind": "page", "page_no": p["page_no"],
                         "char_start": start, "char_end": start + len(body)})
        cursor += len(block) + 2                              # the "\n\n" join
    if omitted:
        truncated = True
    text = "\n\n".join(text_parts)
    return {"text": text,
            "pages_available": len(pages),
            # What actually reached the text, in reading order -- read off the
            # locators rather than recomputed, so the two cannot disagree.
            "pages_selected": [l["page_no"] for l in locators],
            "pages_omitted_for_budget": sorted(set(omitted)),
            "truncated": truncated,
            "locators": locators}


def page_marker(page_no: int) -> str:
    """The boundary carried in the pack text. Plain and greppable: downstream stages
    read this as evidence text with provenance, and none of them learn a PDF mode."""
    return "[PDF PAGE %d]" % page_no


def file_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def clip_locators(locators: list, carried_len: int) -> tuple:
    """Locators must describe the text the pack ACTUALLY carries.

    The pack's total text budget can truncate any source after this module is done
    with it, and a locator pointing past the end would look like provenance while
    grounding nothing -- the same failure the excerpt verifier was written for. So
    locators are clipped to the carried text and anything wholly beyond it is dropped.
    """
    out, lost = [], False
    for loc in locators:
        if loc["char_start"] >= carried_len:
            lost = True
            continue
        if loc["char_end"] > carried_len:
            loc = dict(loc, char_end=carried_len)
            lost = True
        out.append(loc)
    return out, lost
