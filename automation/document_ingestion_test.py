#!/usr/bin/env python3
"""
document_ingestion_test.py -- bounded text-layer PDF ingestion for the Research Pack.

The loss these tests exist to stop was measured on 2026-09-03. Three manual production
trials found the right documents and could not open them: Trial 3's subject WAS a
technical report, and both OpenAI's incident postmortem and METR's report on the same
incident came back `unsupported_content_type:application/pdf`, so the article was
written from other people's summaries of a document one fetch away. Trial 2 lost two
MIT faculty-governance reports the same way.

The second failure these exist to stop is the tempting fix: replacing a PDF with its
first twelve thousand characters. Evidence lives on page 20 as readily as page 1, and a
prefix would have looked like it worked.

Every PDF here is built byte by byte with a real uncompressed text layer and a proper
xref. No network, and the only parse that runs is the real one.
"""
from __future__ import annotations

import hashlib
import io
import os
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import pdf_extract as PDFX                                            # noqa: E402
from new_engine_v1 import documents as DOC                            # noqa: E402
from new_engine_v1 import research as RS                              # noqa: E402
from new_engine_v1.contracts import sha256_text                       # noqa: E402

FAILURES: list = []


def check(label: str, ok: bool, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- %r" % (detail,)))
    if not ok:
        FAILURES.append(label)


# ── fixtures: real PDFs, built here ───────────────────────────────────────────
def make_pdf(pages_text, *, extra_catalog="", page_extra="") -> bytes:
    """A valid PDF with an uncompressed text layer. `|` separates lines on a page."""
    n = len(pages_text)
    font_obj = 2 + n * 2 + 1
    kids = " ".join("%d 0 R" % (3 + i * 2) for i in range(n))
    objs = ["<</Type/Catalog/Pages 2 0 R%s>>" % extra_catalog,
            "<</Type/Pages/Kids[%s]/Count %d>>" % (kids, n)]
    for i, txt in enumerate(pages_text):
        objs.append("<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]"
                    "/Contents %d 0 R/Resources<</Font<</F1 %d 0 R>>>>%s>>"
                    % (4 + i * 2, font_obj, page_extra))
        lines = "".join("BT /F1 12 Tf 72 %d Td (%s) Tj ET\n" % (720 - 14 * j, w)
                        for j, w in enumerate(txt.split("|")))
        objs.append("<</Length %d>>stream\n%s\nendstream" % (len(lines), lines))
    objs.append("<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>")
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += ("%d 0 obj" % i).encode() + body.encode("latin-1") + b"endobj\n"
    xref_at = len(out)
    out += ("xref\n0 %d\n" % (len(objs) + 1)).encode() + b"0000000000 65535 f \n"
    for off in offsets:
        out += ("%010d 00000 n \n" % off).encode()
    out += ("trailer<</Size %d/Root 1 0 R>>\nstartxref\n%d\n%%%%EOF\n"
            % (len(objs) + 1, xref_at)).encode()
    return bytes(out)


def scanned_pdf(n=3) -> bytes:
    """Pages with no text operators at all -- what a scan extracts to."""
    font_obj = 2 + n * 2 + 1
    kids = " ".join("%d 0 R" % (3 + i * 2) for i in range(n))
    objs = ["<</Type/Catalog/Pages 2 0 R>>",
            "<</Type/Pages/Kids[%s]/Count %d>>" % (kids, n)]
    for i in range(n):
        objs.append("<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]"
                    "/Contents %d 0 R/Resources<</Font<</F1 %d 0 R>>>>>>"
                    % (4 + i * 2, font_obj))
        blob = "0 0 612 792 re f\n"                      # a filled rectangle, no text
        objs.append("<</Length %d>>stream\n%s\nendstream" % (len(blob), blob))
    objs.append("<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>")
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += ("%d 0 obj" % i).encode() + body.encode("latin-1") + b"endobj\n"
    xref_at = len(out)
    out += ("xref\n0 %d\n" % (len(objs) + 1)).encode() + b"0000000000 65535 f \n"
    for off in offsets:
        out += ("%010d 00000 n \n" % off).encode()
    out += ("trailer<</Size %d/Root 1 0 R>>\nstartxref\n%d\n%%%%EOF\n"
            % (len(objs) + 1, xref_at)).encode()
    return bytes(out)


def encrypted_pdf() -> bytes:
    import pypdf
    w = pypdf.PdfWriter(clone_from=io.BytesIO(make_pdf(["secret grading policy text|"
                                                        "more of the same words here"])))
    w.encrypt("a-password-we-do-not-have")
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


SUBJECT_PAGE = ("the michigan covered grading policy transcript notation|"
                "first-year students receive covered pass no-credit transcripts|"
                "while professors assign internal letter grades for the record")
FILLER = "table of contents|appendix|acknowledgements|list of figures"
TERMS = DOC.selection_terms("michigan covered grading policy transcript notation",
                            ["covered grades first-year policy"])


# ── a fake acquisition response, so nothing here touches the network ─────────
class Resp:
    def __init__(self, body: bytes, ctype: str):
        self._b, self.headers = body, Headers(ctype)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self, n=None):
        return self._b[:n] if n else self._b


class Headers:
    def __init__(self, ctype):
        self._c = ctype

    def get(self, k, default=None):
        return self._c if k.lower() == "content-type" else default

    def get_content_charset(self):
        return "utf-8"


def fetch(body: bytes, ctype: str, terms=TERMS, env=None):
    """Drive the real fetch_source over a stubbed transport."""
    calls = {"parse": 0}
    real_urlopen, real_parse = RS.urllib.request.urlopen, DOC.parse
    prev = os.environ.get(DOC.DOCUMENTS_ENV)
    if env is None:
        os.environ.pop(DOC.DOCUMENTS_ENV, None)
    else:
        os.environ[DOC.DOCUMENTS_ENV] = env

    def counting_parse(data, **kw):
        calls["parse"] += 1
        return real_parse(data, **kw)

    RS.urllib.request.urlopen = lambda req, timeout=None: Resp(body, ctype)
    DOC.parse = counting_parse
    RS.DOC.parse = counting_parse
    try:
        return RS.fetch_source("https://example.org/doc.pdf", terms=terms), calls
    finally:
        RS.urllib.request.urlopen = real_urlopen
        DOC.parse = real_parse
        RS.DOC.parse = real_parse
        if prev is None:
            os.environ.pop(DOC.DOCUMENTS_ENV, None)
        else:
            os.environ[DOC.DOCUMENTS_ENV] = prev


# ── 1 ────────────────────────────────────────────────────────────────────────
def test_a_small_text_layer_pdf_is_read():
    rec, calls = fetch(make_pdf([SUBJECT_PAGE]), "application/pdf")
    check("status ok", rec["status"] == "ok", rec["status"])
    check("route is document", rec["route"] == "document", rec["route"])
    check("the text is carried", "covered grading policy" in rec["text"], rec["text"][:80])
    check("with a page marker", "[PDF PAGE 1]" in rec["text"])
    check("the parser ran once", calls["parse"] == 1, calls)


# ── 2 ────────────────────────────────────────────────────────────────────────
def test_evidence_on_a_later_page_is_found():
    """The whole point. A first-12k-characters implementation passes every other test
    in this file and fails this one."""
    pages = [FILLER] * 19 + [SUBJECT_PAGE] + [FILLER] * 5
    rec, _ = fetch(make_pdf(pages), "application/pdf")
    doc = rec["document"]
    check("page 20 is selected", doc["selection"]["pages_selected"] == [20],
          doc["selection"]["pages_selected"])
    check("its text is carried", "covered pass no-credit" in rec["text"])
    check("the marker names the real page", "[PDF PAGE 20]" in rec["text"])
    check("no page-1 filler was carried", "table of contents" not in rec["text"].lower())
    check("and the document's true length is recorded",
          doc["selection"]["pages_available"] == 25,
          doc["selection"]["pages_available"])


# ── 3 ────────────────────────────────────────────────────────────────────────
def test_a_scanned_pdf_yields_no_evidence():
    rec, calls = fetch(scanned_pdf(), "application/pdf")
    check("status is pdf_no_text_layer", rec["status"] == DOC.PDF_NO_TEXT_LAYER,
          rec["status"])
    check("no text was carried", rec["text"] == "" and rec["sha256"] == "")
    check("no document provenance was invented", "document" not in rec)
    check("and no OCR was attempted anywhere",
          "ocr" not in (HERE / "new_engine_v1" / "documents.py").read_text().lower()
          .replace("no ocr", "").replace("ocr is", "").replace("ocr, and", "")
          .replace("without ocr", "").replace("ocr fallback", ""))


# ── 4 ────────────────────────────────────────────────────────────────────────
def test_an_encrypted_pdf_yields_no_evidence():
    rec, _ = fetch(encrypted_pdf(), "application/pdf")
    check("status is pdf_encrypted", rec["status"] == DOC.PDF_ENCRYPTED, rec["status"])
    check("no text was carried", rec["text"] == "")


# ── 5 ────────────────────────────────────────────────────────────────────────
def test_a_malformed_pdf_yields_no_evidence():
    for label, body in (("truncated mid-object", b"%PDF-1.4\n1 0 obj<</Type/Cat"),
                        ("header then garbage",
                         b"%PDF-1.4\n" + bytes(range(256)) * 8),
                        ("header only", b"%PDF-")):
        rec, _ = fetch(body, "application/pdf")
        check("%s -> no evidence" % label,
              rec["status"] in (DOC.PDF_PARSE_ERROR, DOC.PDF_NO_TEXT_LAYER),
              rec["status"])
        check("   nothing was carried", rec["text"] == "" and "document" not in rec)


# ── 6 ────────────────────────────────────────────────────────────────────────
def test_an_oversize_pdf_is_never_parsed():
    big = b"%PDF-1.4\n" + b"0" * (DOC.DOC_MAX_BYTES + 64)
    rec, calls = fetch(big, "application/pdf")
    check("status is pdf_too_large", rec["status"] == DOC.PDF_TOO_LARGE, rec["status"])
    check("the parser was NOT invoked", calls["parse"] == 0, calls)
    check("and parse() refuses oversize bytes on its own too",
          DOC.parse(big)["status"] == DOC.PDF_TOO_LARGE)


# ── 7 ────────────────────────────────────────────────────────────────────────
def test_a_document_over_the_page_limit_is_rejected_whole():
    """The bound is a cliff, not a truncation: a document past it is refused entire,
    because parsing its first hundred pages and calling that the document would be a
    quieter kind of wrong than refusing it.

    The limit is 100 because the four documents the production trials lost are 16, 38,
    80 and 91 pages. At 40 the last two were refused for being long, and length is not
    what makes a report untrustworthy.
    """
    check("the page limit is explicit", DOC.DOC_MAX_PAGES == 100, DOC.DOC_MAX_PAGES)

    # exactly at the limit: read
    at_limit, calls = fetch(
        make_pdf([SUBJECT_PAGE] + [FILLER] * (DOC.DOC_MAX_PAGES - 1)), "application/pdf")
    check("a document of exactly %d pages is read" % DOC.DOC_MAX_PAGES,
          at_limit["status"] == "ok", at_limit["status"])
    check("   it reports its true length",
          at_limit["document"]["selection"]["pages_available"] == DOC.DOC_MAX_PAGES,
          at_limit["document"]["selection"]["pages_available"])
    check("   and its subject page is found", "covered pass no-credit" in at_limit["text"])
    check("   the parser ran", calls["parse"] == 1)

    # one page past it: refused whole
    over, _ = fetch(make_pdf([FILLER] * DOC.DOC_MAX_PAGES + [SUBJECT_PAGE]),
                    "application/pdf")
    check("a document of %d pages is pdf_page_limit" % (DOC.DOC_MAX_PAGES + 1),
          over["status"] == DOC.PDF_PAGE_LIMIT, over["status"])
    check("   NO partial evidence was trusted",
          over["text"] == "" and over["sha256"] == "" and "document" not in over)
    check("   and the other bounds did not move to pay for it",
          (DOC.DOC_MAX_BYTES, DOC.DOC_MAX_PAGES_CARRIED, DOC.DOC_MAX_CHARS_CARRIED,
           DOC.DOC_PARSE_TIMEOUT) == (8 * 1024 * 1024, 6, 18_000, 15),
          (DOC.DOC_MAX_BYTES, DOC.DOC_MAX_PAGES_CARRIED, DOC.DOC_MAX_CHARS_CARRIED,
           DOC.DOC_PARSE_TIMEOUT))


# ── 8 ────────────────────────────────────────────────────────────────────────
def test_the_parse_deadline_actually_kills_a_hang():
    """A between-pages check is not a bound. This hangs INSIDE the parse and must still
    return, on time, with no evidence."""
    real = PDFX.worker_source
    PDFX.worker_source = lambda max_pages: "import time\ntime.sleep(60)\n"
    try:
        t = time.monotonic()
        got = DOC.parse(make_pdf([SUBJECT_PAGE]), timeout=2)
        elapsed = time.monotonic() - t
    finally:
        PDFX.worker_source = real
    check("status is pdf_parse_timeout", got.get("status") == DOC.PDF_PARSE_TIMEOUT, got)
    check("it returned on time, not after 60s", elapsed < 10, elapsed)
    check("no pages came back", "pages" not in got)
    check("the timeout is an explicit constant", DOC.DOC_PARSE_TIMEOUT == 15)
    px = (HERE / "pdf_extract.py").read_text()
    check("and the bound is enforced by killing a worker, not by a between-page check",
          "subprocess.run(" in px and "timeout=timeout" in px
          and "TimeoutExpired" in px)
    # AST, not a text scan -- the project already learned that lesson once, when a
    # raw-text purity check failed on a safety docstring.
    import ast
    mods = set()
    for n in ast.walk(ast.parse((HERE / "new_engine_v1" / "documents.py").read_text())):
        if isinstance(n, ast.Import):
            mods.update(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom):
            mods.add(n.module or "")
    check("the engine package itself spawns nothing",
          not (mods & {"subprocess", "socket", "requests", "sqlite3"}), sorted(mods))


# ── 9 ────────────────────────────────────────────────────────────────────────
def test_a_pdf_served_as_octet_stream_is_still_a_pdf():
    for ctype in ("application/octet-stream", "", "application/x-download"):
        rec, calls = fetch(make_pdf([SUBJECT_PAGE]), ctype)
        check("%r + %%PDF- is accepted" % (ctype or "(missing)",),
              rec["status"] == "ok", rec["status"])
        check("   and parsed once", calls["parse"] == 1)


# ── 10 ───────────────────────────────────────────────────────────────────────
def test_html_falsely_labelled_pdf_is_never_parsed():
    html = b"<html><head><title>Not a PDF</title></head><body><p>words</p></body></html>"
    rec, calls = fetch(html, "application/pdf")
    check("status is type_mismatch", rec["status"] == DOC.TYPE_MISMATCH, rec["status"])
    check("the parser was NOT called", calls["parse"] == 0, calls)
    check("and it was not run through the HTML extractor either",
          rec["text"] == "" and "Not a PDF" not in rec.get("title", ""))
    # a non-PDF, non-texty type that never claimed to be a document keeps its old answer
    rec2, calls2 = fetch(b"\x00\x01\x02binary", "image/png")
    check("an unrelated binary type keeps unsupported_content_type",
          rec2["status"] == "unsupported_content_type:image/png", rec2["status"])
    check("   and is not parsed", calls2["parse"] == 0)


# ── 11 ───────────────────────────────────────────────────────────────────────
def test_ordinary_html_is_untouched_by_any_of_this():
    body = ("<html><head><title>Ordinary</title>"
            "<link rel='canonical' href='https://example.org/c'></head><body><p>" +
            ("the committee recorded that the audible signal had been inoperative for "
             "eleven weeks before the inspection and the operator replaced the unit "
             "the following March " * 3) + "</p></body></html>").encode()
    rec, calls = fetch(body, "text/html; charset=utf-8")
    check("status ok", rec["status"] == "ok", rec["status"])
    check("route is the ordinary one", rec["route"] == "ordinary", rec["route"])
    check("the PDF parser was NOT called", calls["parse"] == 0, calls)
    check("no document provenance was attached", "document" not in rec)
    check("title and canonical still extracted",
          rec["title"] == "Ordinary" and rec["canonical_url"] == "https://example.org/c")
    check("sha is over the carried text", rec["sha256"] == sha256_text(rec["text"]))
    check("the HTML read cap is unchanged",
          "raw = r.read(2_000_000)" in (HERE / "new_engine_v1" / "research.py").read_text())
    check("and the 60-word floor is unchanged",
          "if len(text.split()) < 60:" in
          (HERE / "new_engine_v1" / "research.py").read_text())


# ── 12 ───────────────────────────────────────────────────────────────────────
def test_the_off_switch_restores_the_old_behaviour():
    rec, calls = fetch(make_pdf([SUBJECT_PAGE]), "application/pdf", env="0")
    check("a valid PDF is unsupported again",
          rec["status"] == "unsupported_content_type:application/pdf", rec["status"])
    check("the parser was NOT called", calls["parse"] == 0, calls)
    check("no document provenance", "document" not in rec)
    for off in ("0", "false", "no", "off", "FALSE"):
        os.environ[DOC.DOCUMENTS_ENV] = off
        check("   %r switches documents off" % off, not DOC.enabled())
    os.environ.pop(DOC.DOCUMENTS_ENV, None)
    check("unset means ENABLED", DOC.enabled())
    os.environ[DOC.DOCUMENTS_ENV] = "1"
    check("and an explicit 1 is enabled", DOC.enabled())
    os.environ.pop(DOC.DOCUMENTS_ENV, None)


# ── 13 ───────────────────────────────────────────────────────────────────────
def test_pdf_provenance_is_complete_and_checkable():
    data = make_pdf([FILLER] * 19 + [SUBJECT_PAGE])
    rec, _ = fetch(data, "application/pdf")
    d = rec["document"]
    check("media_type", d["media_type"] == "application/pdf", d.get("media_type"))
    check("file_sha256 is the hash of the FETCHED BYTES",
          d["file_sha256"] == hashlib.sha256(data).hexdigest(), d["file_sha256"])
    check("extractor is named and versioned",
          d["extractor"]["name"] == "pypdf" and d["extractor"]["version"],
          d["extractor"])
    check("pages_available is the real count", d["selection"]["pages_available"] == 20)
    check("pages_selected is what was carried",
          d["selection"]["pages_selected"] == [20], d["selection"])
    check("truncated is recorded", d["selection"]["truncated"] is False,
          d["selection"])
    check("text sha256 is the hash of the CARRIED TEXT",
          rec["sha256"] == sha256_text(rec["text"]))
    check("file hash and text hash are different things",
          d["file_sha256"] != rec["sha256"])
    check("locators are pages", all(l["kind"] == "page" for l in d["locators"]))
    for l in d["locators"]:
        seg = rec["text"][l["char_start"]:l["char_end"]]
        check("locator for page %d maps to real carried text" % l["page_no"],
              bool(seg.strip()) and "covered pass no-credit" in seg, seg[:60])
    check("no pack_id was added", "pack_id" not in d and "pack_id" not in rec)
    check("no subject_source_id was added", "subject_source_id" not in d)


# ── 14 ───────────────────────────────────────────────────────────────────────
def test_selection_is_deterministic():
    data = make_pdf([FILLER] * 9 + [SUBJECT_PAGE] + [FILLER] * 5)
    a, _ = fetch(data, "application/pdf")
    b, _ = fetch(data, "application/pdf")
    check("same bytes and terms give the same pages",
          a["document"]["selection"]["pages_selected"]
          == b["document"]["selection"]["pages_selected"])
    check("the same text", a["text"] == b["text"])
    check("and the same hash", a["sha256"] == b["sha256"])
    check("scoring itself is stable",
          DOC.score_page(SUBJECT_PAGE, TERMS) == DOC.score_page(SUBJECT_PAGE, TERMS))
    check("ties break by page number, low first",
          DOC.select_pages([{"page_no": i, "text": FILLER} for i in (3, 1, 2)],
                           [])["pages_selected"] == [1, 2, 3])


# ── 15 ───────────────────────────────────────────────────────────────────────
def test_the_pack_budget_still_binds_and_locators_follow_it():
    """The pack's own budget can truncate a document AFTER extraction. A locator that
    survived that pointing past the end would be provenance that grounds nothing."""
    long_page = " ".join("michigan covered grading policy transcript word%d" % i
                         for i in range(1200))
    rec, _ = fetch(make_pdf([long_page]), "application/pdf")
    rec.update(source_id="S1", accessed_at="2026-09-03T00:00:00+00:00",
               publisher="example.org")
    anchor_text = "anchor " * 100
    pack = RS.build_pack(
        anchor={"url": "https://anchor.example/a", "text": anchor_text,
                "accessed_at": "2026-09-03T00:00:00+00:00", "sha256": "0" * 64,
                "publisher": "anchor.example", "title": "A"},
        scoped={"subject": "the michigan covered grading policy", "questions": [],
                "queries": ["q"], "anchor_kind": "report",
                "anchor_subject_words": 300, "named_entities": []},
        fetched=[rec],
        assessment={"sources": [{"source_id": "S1", "role": "PRIMARY",
                                 "relation": "extends", "why_relevant": "first-party",
                                 "excerpts": []}]},
        searched={"queries": ["q"], "candidates": ["https://example.org/doc.pdf"],
                  "failures": []})
    s = [x for x in pack["sources"] if x["source_id"] == "S1"][0]
    check("the document is in the pack", s["fetch_status"] == "ok")
    check("its text respects the pack budget",
          len(anchor_text) + len(s["text"]) <= RS.PACK_TEXT_BUDGET,
          (len(anchor_text), len(s["text"]), RS.PACK_TEXT_BUDGET))
    check("the pack budget was NOT raised", RS.PACK_TEXT_BUDGET == 40_000)
    check("sha is over the text the pack carries", s["sha256"] == sha256_text(s["text"]))
    for l in s["document"]["locators"]:
        check("locator stays inside the carried text",
              l["char_end"] <= len(s["text"]), (l, len(s["text"])))
    check("and document text never exceeds its own bound",
          len(rec["text"]) <= DOC.DOC_MAX_CHARS_CARRIED, len(rec["text"]))
    check("HTML sources in the same pack grew no document fields",
          all("document" not in x for x in pack["sources"]
              if x["source_id"] != "S1"), [x["source_id"] for x in pack["sources"]])


# ── 16 ───────────────────────────────────────────────────────────────────────
def test_nothing_active_inside_a_document_is_followed_or_executed():
    src = (HERE / "new_engine_v1" / "documents.py").read_text() + \
        (HERE / "pdf_extract.py").read_text()
    worker = PDFX.worker_source(DOC.DOC_MAX_PAGES)
    for banned in ("urllib", "requests", "socket", "http.client", "webbrowser",
                   "eval(", "exec(", "os.system", "subprocess", "open(",
                   "urlopen", "Popen"):
        check("the worker cannot %s" % banned.rstrip("(."), banned not in worker, banned)
    for banned in ("get_attachments", "embedded_file", "EmbeddedFile", "/JavaScript",
                   "add_js", "extract_attachment", "pytesseract", "tesseract"):
        check("documents.py has no %s" % banned, banned not in src)
    # a PDF carrying an OpenAction/JS and an embedded-file name yields text and nothing else
    hostile = make_pdf([SUBJECT_PAGE + "|https://evil.example/callback"],
                       extra_catalog="/OpenAction<</S/JavaScript/JS(app.alert\\(1\\))>>"
                                     "/Names<</EmbeddedFiles<</Names[(x)5 0 R]>>>>")
    rec, _ = fetch(hostile, "application/pdf")
    check("the document still reads as plain text", rec["status"] == "ok", rec["status"])
    check("its output is text only, with no action taken",
          "app.alert" not in rec["text"], rec["text"][:120])
    check("a URL printed inside the page is carried as TEXT, not fetched",
          "evil.example" in rec["text"])
    check("and the record holds no attachment or action field",
          not any(k in rec.get("document", {}) for k in
                  ("attachments", "actions", "javascript", "embedded_files")))
    res = (HERE / "new_engine_v1" / "research.py").read_text()
    fn = res.split("def _as_document")[1].split("\ndef ")[0]
    code = "\n".join(l for l in fn.splitlines()
                     if not l.strip().startswith("#") and '"""' not in l
                     and "suffix" not in l and "claim by" not in l)
    check("routing is by magic bytes", "looks_like_pdf" in code, code[:200])
    check("and never by a .pdf suffix", ".pdf" not in code and "endswith" not in code)


# ── #53's contract is preserved ───────────────────────────────────────────────
def test_the_two_attempt_contract_from_pr_53_is_unchanged():
    res = (HERE / "new_engine_v1" / "research.py").read_text()
    check("still two attempts maximum", RS.MAX_ATTEMPTS_PER_SOURCE == 2)
    check("still one fallback call site", res.count("IMP.get(") == 1)
    body = res.split("def fetch_source(")[1].split("# ── model-assisted")[0]
    check("still no loop in fetch_source",
          "\n    for " not in body and "\n    while " not in body)
    check("the fallback budget is unchanged",
          RS.FALLBACK_TOTAL_SECONDS == 60 and RS.FALLBACK_TIMEOUT == 15)
    check("the fallback triggers are unchanged",
          RS.FALLBACK_STATUSES == ("http_403", "empty_or_blocked"))
    check("a PDF is not a fallback trigger, so no extra fetch happens for one",
          "application/pdf" not in str(RS.FALLBACK_STATUSES))
    check("research thresholds are unchanged",
          (RS.MAX_QUERIES, RS.MAX_CANDIDATE_URLS, RS.MAX_FETCHED_SOURCES,
           RS.PER_SOURCE_CHARS, RS.PACK_TEXT_BUDGET) == (4, 12, 5, 12_000, 40_000))


def main() -> None:
    for fn in (test_a_small_text_layer_pdf_is_read,
               test_evidence_on_a_later_page_is_found,
               test_a_scanned_pdf_yields_no_evidence,
               test_an_encrypted_pdf_yields_no_evidence,
               test_a_malformed_pdf_yields_no_evidence,
               test_an_oversize_pdf_is_never_parsed,
               test_a_document_over_the_page_limit_is_rejected_whole,
               test_the_parse_deadline_actually_kills_a_hang,
               test_a_pdf_served_as_octet_stream_is_still_a_pdf,
               test_html_falsely_labelled_pdf_is_never_parsed,
               test_ordinary_html_is_untouched_by_any_of_this,
               test_the_off_switch_restores_the_old_behaviour,
               test_pdf_provenance_is_complete_and_checkable,
               test_selection_is_deterministic,
               test_the_pack_budget_still_binds_and_locators_follow_it,
               test_nothing_active_inside_a_document_is_followed_or_executed,
               test_the_two_attempt_contract_from_pr_53_is_unchanged):
        print("\n" + fn.__name__)
        fn()
    os.environ.pop(DOC.DOCUMENTS_ENV, None)
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL DOCUMENT INGESTION TESTS PASSED")


if __name__ == "__main__":
    main()
