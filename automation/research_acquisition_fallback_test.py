#!/usr/bin/env python3
"""
research_acquisition_fallback_test.py -- the Research Pack's one permitted refetch.

The failure these hold the line on is dated and was measured, not imagined. Three
manual production trials on 2026-09-03 died or were degraded at ACQUISITION rather than
at search: the queries found the right documents and the transport could not read them.
Trial 2 held with subject_relevant_words=0 while four first-party University of Michigan
policy pages sat behind a TLS fingerprint check, and a probe of those exact URLs
afterwards returned 200 with 646-1,702 usable words each through impersonation.

So the fallback has to work, and -- more importantly -- it has to stay bounded and stay
honest. No network here: both legs are injected.
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import research as RS                            # noqa: E402

FAILURES: list = []


def check(label: str, ok: bool, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- %r" % (detail,)))
    if not ok:
        FAILURES.append(label)


# ── fixtures ──────────────────────────────────────────────────────────────────
def _article_html(marker="ordinary"):
    """Enough real words to clear the 60-word floor the extractor applies."""
    body = (("The committee recorded that the audible signal had been inoperative for "
             "eleven weeks before the inspection, and that the operator replaced the "
             "unit the following March. Members asked why the fault had not appeared in "
             "the previous return. The clerk said the return covered a different "
             "quarter. ") * 3)
    return ("<html><head><title>Policy %s</title>"
            "<link rel='canonical' href='https://example.org/canonical'>"
            "</head><body><p>%s</p></body></html>" % (marker, body))


class _Resp:
    """Minimal urlopen response: context manager, headers, capped read."""

    def __init__(self, body: str, ctype="text/html; charset=utf-8"):
        self._body = body.encode()
        self.headers = _Headers(ctype)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self, n=None):
        return self._body[:n] if n else self._body


class _Headers:
    def __init__(self, ctype):
        self._ctype = ctype

    def get(self, k, default=None):
        return self._ctype if k.lower() == "content-type" else default

    def get_content_charset(self):
        return "utf-8"


class Wire:
    """Records every network attempt of both kinds, so a third one cannot hide."""

    def __init__(self, *, ordinary, impersonated, available=True):
        self.ordinary_spec, self.impersonated_spec = ordinary, impersonated
        self.available = available
        self.ordinary_calls, self.impersonated_calls = [], []

    # the ordinary leg, standing in for urllib.request.urlopen
    def urlopen(self, req, timeout=None):
        self.ordinary_calls.append(getattr(req, "full_url", req))
        spec = self.ordinary_spec
        if isinstance(spec, Exception):
            raise spec
        return _Resp(spec[0], spec[1])

    # the fallback leg, standing in for impersonated_fetch.get
    def get(self, url, *, timeout, cap):
        self.impersonated_calls.append((url, timeout, cap))
        spec = self.impersonated_spec
        if isinstance(spec, Exception):
            raise spec
        return spec

    def attempts(self):
        return len(self.ordinary_calls) + len(self.impersonated_calls)


def run_fetch(wire, url="https://example.org/doc", budget=None):
    real_urlopen, real_get, real_avail = (
        RS.urllib.request.urlopen, RS.IMP.get, RS.IMP.available)
    RS.urllib.request.urlopen = wire.urlopen
    RS.IMP.get = wire.get
    RS.IMP.available = lambda: wire.available
    try:
        return RS.fetch_source(url, fallback_budget=budget)
    finally:
        RS.urllib.request.urlopen = real_urlopen
        RS.IMP.get = real_get
        RS.IMP.available = real_avail


import urllib.error                                                  # noqa: E402


def _http_error(code):
    return urllib.error.HTTPError("https://example.org/doc", code, "blocked", {}, None)


def _html_200(marker="fallback"):
    return {"status": 200, "content_type": "text/html; charset=utf-8",
            "text": _article_html(marker)}


# ── A ─────────────────────────────────────────────────────────────────────────
def test_an_ordinary_page_is_fetched_once():
    wire = Wire(ordinary=(_article_html("ordinary"), "text/html"),
                impersonated=AssertionError("the fallback must not run"))
    rec = run_fetch(wire)
    check("the ordinary attempt succeeds", rec["status"] == "ok", rec["status"])
    check("it carries the text", len(rec["text"].split()) > 60, len(rec["text"].split()))
    check("the fallback was NOT called", wire.impersonated_calls == [])
    check("exactly one network attempt", wire.attempts() == 1, wire.attempts())
    check("and the record says so", rec["attempts"] == 1 and rec["route"] == "ordinary",
          (rec["attempts"], rec["route"]))


# ── B ─────────────────────────────────────────────────────────────────────────
def test_a_403_is_recovered_by_one_impersonated_attempt():
    """Trial 2's exact shape: the ordinary leg is refused, the page is readable."""
    wire = Wire(ordinary=_http_error(403), impersonated=_html_200())
    rec = run_fetch(wire)
    check("the source becomes usable", rec["status"] == "ok", rec["status"])
    check("the recovered text is what entered the record",
          "eleven weeks" in rec["text"])
    check("the fallback ran once", len(wire.impersonated_calls) == 1,
          wire.impersonated_calls)
    check("the record records the route", rec["route"] == "impersonated", rec["route"])
    check("bounded by FALLBACK_TIMEOUT", wire.impersonated_calls[0][1] == RS.FALLBACK_TIMEOUT,
          wire.impersonated_calls[0])
    check("and capped", wire.impersonated_calls[0][2] == RS.FALLBACK_CAP)


# ── C ─────────────────────────────────────────────────────────────────────────
def test_a_403_whose_fallback_also_fails_stays_failed():
    for label, spec in (("the fallback is refused too", {"status": 403,
                                                         "content_type": "text/html",
                                                         "text": ""}),
                        ("the fallback raises", RuntimeError("tls handshake failed")),
                        ("the fallback returns a shell", {"status": 200,
                                                          "content_type": "text/html",
                                                          "text": "<html><body>js"
                                                                  "</body></html>"})):
        wire = Wire(ordinary=_http_error(403), impersonated=spec)
        rec = run_fetch(wire)
        check("%s -> source stays failed" % label, rec["status"] == "http_403",
              rec["status"])
        check("   no text was invented", rec["text"] == "" and rec["sha256"] == "")


# ── D ─────────────────────────────────────────────────────────────────────────
def test_an_unusable_representation_is_refetched():
    """A 200 carrying a JS shell is a successful request with no article in it. The
    ordinary leg cannot tell that from a thin page, so the extractor's own 60-word
    floor is the rule -- the confident one already in this module."""
    wire = Wire(ordinary=("<html><body><p>Enable JavaScript to continue.</p></body>"
                          "</html>", "text/html"),
                impersonated=_html_200())
    rec = run_fetch(wire)
    check("the shell is recovered into an article", rec["status"] == "ok", rec["status"])
    check("via the fallback", rec["route"] == "impersonated")
    check("one fallback attempt only", len(wire.impersonated_calls) == 1)


# ── E ─────────────────────────────────────────────────────────────────────────
def test_a_pdf_reached_by_fallback_is_still_unsupported():
    """Trial 3 lost OpenAI's and METR's technical reports this way. Document ingestion
    is separate work; this only has to report the content type truthfully."""
    wire = Wire(ordinary=_http_error(403),
                impersonated={"status": 200, "content_type": "application/pdf",
                              "text": "%PDF-1.7 ..."})
    rec = run_fetch(wire)
    check("status is PDF_UNSUPPORTED",
          rec["status"] == "unsupported_content_type:application/pdf", rec["status"])
    check("no PDF text entered the record", rec["text"] == "")
    check("nothing tried to parse it", rec["sha256"] == "")

    # and an ordinary PDF never triggers a refetch at all: it is a successful
    # representation, so asking again cannot change the answer
    wire2 = Wire(ordinary=("%PDF-1.7", "application/pdf"),
                 impersonated=AssertionError("a PDF must not be refetched"))
    rec2 = run_fetch(wire2)
    check("an ordinary PDF is not refetched", wire2.impersonated_calls == [])
    check("and reports PDF_UNSUPPORTED",
          rec2["status"] == "unsupported_content_type:application/pdf", rec2["status"])


# ── F ─────────────────────────────────────────────────────────────────────────
def test_two_network_attempts_is_the_hard_maximum():
    check("the contract is a stated constant", RS.MAX_ATTEMPTS_PER_SOURCE == 2,
          RS.MAX_ATTEMPTS_PER_SOURCE)
    for spec in ({"status": 403, "content_type": "text/html", "text": ""},
                 {"status": 200, "content_type": "text/html", "text": "<html>x</html>"},
                 RuntimeError("boom")):
        wire = Wire(ordinary=_http_error(403), impersonated=spec)
        rec = run_fetch(wire)
        check("never more than 2 attempts (%s)" % type(spec).__name__,
              wire.attempts() == 2, wire.attempts())
        check("   and the record never claims more",
              rec["attempts"] <= RS.MAX_ATTEMPTS_PER_SOURCE, rec["attempts"])
    src = (HERE / "new_engine_v1" / "research.py").read_text()
    body = src.split("def fetch_source(")[1].split("# \u2500\u2500 model-assisted")[0]
    check("fetch_source contains no loop",
          "\n    for " not in body and "\n    while " not in body)
    check("and calls the fallback exactly once", body.count("IMP.get(") == 1)


# ── G ─────────────────────────────────────────────────────────────────────────
def test_the_fallback_cannot_escape_the_run_budget():
    # a budget with nothing left must suppress the attempt outright
    spent = RS.FallbackBudget(total=RS.FALLBACK_TIMEOUT)
    spent.spend(RS.FALLBACK_TIMEOUT)
    wire = Wire(ordinary=_http_error(403), impersonated=_html_200())
    rec = run_fetch(wire, budget=spent)
    check("an exhausted budget suppresses the fallback", wire.impersonated_calls == [])
    check("and leaves the ordinary answer intact", rec["status"] == "http_403",
          rec["status"])

    # a budget that can still pay for one permits exactly one
    fresh = RS.FallbackBudget(total=RS.FALLBACK_TIMEOUT)
    wire2 = Wire(ordinary=_http_error(403), impersonated=_html_200())
    check("a funded budget permits the attempt",
          run_fetch(wire2, budget=fresh)["status"] == "ok")
    check("and the attempt is charged to it", fresh.attempts == 1, fresh.attempts)
    check("partially spent budgets refuse an attempt they cannot afford",
          not RS.FallbackBudget(total=RS.FALLBACK_TIMEOUT - 1).can_afford(
              RS.FALLBACK_TIMEOUT))
    check("the total is explicit", RS.FALLBACK_TOTAL_SECONDS == 60)
    check("the per-attempt bound is explicit", RS.FALLBACK_TIMEOUT == 15)
    check("worst case added per run is the total, not per-candidate",
          RS.FALLBACK_TOTAL_SECONDS < RS.MAX_CANDIDATE_URLS * RS.FALLBACK_TIMEOUT)
    src = (HERE / "new_engine_v1" / "research.py").read_text()
    check("the run builds one shared budget", "fallback_budget = FallbackBudget()" in src)
    check("and passes it into every fetch",
          "fetch_source(url, fallback_budget=fallback_budget)" in src)


# ── H ─────────────────────────────────────────────────────────────────────────
def test_fallback_acquired_text_has_ordinary_provenance():
    wire = Wire(ordinary=_http_error(403), impersonated=_html_200())
    rec = run_fetch(wire)
    from new_engine_v1.contracts import sha256_text
    check("url is the requested url", rec["url"] == "https://example.org/doc")
    check("canonical_url was extracted",
          rec["canonical_url"] == "https://example.org/canonical", rec["canonical_url"])
    check("title was extracted", rec["title"].startswith("Policy"), rec["title"])
    check("fetch_status is the ordinary 'ok', not a special one", rec["status"] == "ok")
    check("sha256 is over the text the record carries",
          rec["sha256"] == sha256_text(rec["text"]))
    check("content_length matches", rec["content_length"] == len(rec["text"]))
    ordinary = run_fetch(Wire(ordinary=(_article_html("fallback"), "text/html"),
                              impersonated=AssertionError("no")))
    check("an impersonated page hashes identically to the same page fetched ordinarily",
          rec["sha256"] == ordinary["sha256"], (rec["sha256"], ordinary["sha256"]))


# ── I ─────────────────────────────────────────────────────────────────────────
def test_no_behavioural_change_for_pages_that_already_worked():
    """Every non-fallback status must behave exactly as before: one attempt, same
    string. A 404 in particular is out of scope and must not be retried."""
    cases = [(_http_error(404), "http_404"), (_http_error(500), "http_500"),
             (_http_error(401), "http_401"), (_http_error(429), "http_429"),
             (TimeoutError("slow"), "TimeoutError"),
             (("%PDF", "application/pdf"), "unsupported_content_type:application/pdf")]
    for spec, expected in cases:
        wire = Wire(ordinary=spec,
                    impersonated=AssertionError("must not refetch %s" % expected))
        rec = run_fetch(wire)
        check("%s is unchanged and not refetched" % expected,
              rec["status"] == expected and wire.impersonated_calls == [], rec["status"])
    check("only two statuses may ever trigger a refetch",
          RS.FALLBACK_STATUSES == ("http_403", "empty_or_blocked"), RS.FALLBACK_STATUSES)
    wire = Wire(ordinary=_http_error(403), impersonated=_html_200(), available=False)
    check("and without curl_cffi installed nothing is attempted",
          run_fetch(wire)["status"] == "http_403" and wire.impersonated_calls == [])


# ── J ─────────────────────────────────────────────────────────────────────────
def test_sufficiency_sees_fallback_material_as_ordinary_material():
    """Trial 2 held at independent=0 / subject_relevant_words=0 because acquisition
    returned nothing about the subject. A recovered source has to count normally, or
    the fallback fixes the fetch and not the hold."""
    wire = Wire(ordinary=_http_error(403), impersonated=_html_200())
    rec = run_fetch(wire)
    rec.update(source_id="S1", accessed_at="2026-09-03T00:00:00+00:00",
               publisher="example.org")
    pack = RS.build_pack(
        anchor={"url": "https://anchor.example/a", "text": "anchor " * 80,
                "accessed_at": "2026-09-03T00:00:00+00:00", "sha256": "0" * 64,
                "publisher": "anchor.example", "title": "A"},
        scoped={"subject": "the committee's audible-signal fault", "questions": [],
                "queries": ["q"], "anchor_kind": "news_report",
                "anchor_subject_words": 300, "named_entities": []},
        fetched=[rec],
        assessment={"sources": [{"source_id": "S1", "role": "PRIMARY",
                                 "relation": "extends", "why_relevant": "first-party",
                                 "excerpts": ["the operator replaced the unit the "
                                              "following March"]}]},
        searched={"queries": ["q"], "candidates": ["https://example.org/doc"],
                  "failures": []})
    src = [s for s in pack["sources"] if s["source_id"] == "S1"]
    check("the recovered source is in the pack", len(src) == 1, pack["sources"])
    if src:
        s = src[0]
        check("with fetch_status ok", s["fetch_status"] == "ok", s["fetch_status"])
        check("with its role honoured", s["role"] == "PRIMARY", s["role"])
        check("and its excerpt verified against the carried text",
              s["excerpts"] and s["excerpts"][0] in s["text"], s["excerpts"])
        check("carrying its text", len(s["text"].split()) > 60)
        check("and a hash over the carried text",
              s["sha256"] and s["content_length"] == len(s["text"]))
    check("it counts toward coverage",
          pack["coverage"]["fetched_ok"] >= 1, pack["coverage"])
    check("and is not recorded as a failure", pack["coverage"]["fetch_failures"] == [],
          pack["coverage"]["fetch_failures"])


# ── one implementation, not two ───────────────────────────────────────────────
def test_there_is_one_impersonation_implementation():
    disc = (HERE / "orchestrator" / "discovery.py").read_text()
    res = (HERE / "new_engine_v1" / "research.py").read_text()
    shared = (HERE / "impersonated_fetch.py").read_text()
    disc_code = "\n".join(l for l in disc.splitlines()
                          if not l.strip().startswith("#"))
    check("the orchestrator no longer imports curl_cffi",
          "from curl_cffi import" not in disc_code and "import curl_cffi" not in disc_code)
    check("and holds no curl_cffi handle of its own",
          "_curl_cffi_requests" not in disc_code)
    check("it delegates to the shared module",
          "_impersonated_fetch.html_or_none(" in disc)
    check("research does not call curl_cffi itself", "curl_cffi" not in res)
    check("research uses the shared module", "IMP.get(" in res)
    check("only the shared module imports curl_cffi",
          "from curl_cffi import" in shared)
    import ast
    mods = set()
    for node in ast.walk(ast.parse(shared)):
        if isinstance(node, ast.Import):
            mods.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            mods.add(node.module or "")
    check("the shared module imports nothing from this project",
          not any(m.startswith(("orchestrator", "new_engine_v1")) for m in mods),
          sorted(mods))
    check("it depends only on the stdlib future import and curl_cffi",
          mods <= {"__future__", "curl_cffi"}, sorted(mods))
    rimports = [l for l in res.splitlines() if l.startswith(("import ", "from "))]
    check("research still imports no orchestrator module",
          not any("orchestrator" in l for l in rimports), rimports)
    check("the impersonation target is pinned in one place",
          shared.count('IMPERSONATE = "chrome124"') == 1
          and '"chrome124"' not in disc_code)


def main() -> None:
    for fn in (test_an_ordinary_page_is_fetched_once,
               test_a_403_is_recovered_by_one_impersonated_attempt,
               test_a_403_whose_fallback_also_fails_stays_failed,
               test_an_unusable_representation_is_refetched,
               test_a_pdf_reached_by_fallback_is_still_unsupported,
               test_two_network_attempts_is_the_hard_maximum,
               test_the_fallback_cannot_escape_the_run_budget,
               test_fallback_acquired_text_has_ordinary_provenance,
               test_no_behavioural_change_for_pages_that_already_worked,
               test_sufficiency_sees_fallback_material_as_ordinary_material,
               test_there_is_one_impersonation_implementation):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL RESEARCH ACQUISITION FALLBACK TESTS PASSED")


if __name__ == "__main__":
    main()
