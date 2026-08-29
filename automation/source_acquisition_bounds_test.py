#!/usr/bin/env python3
"""
source_acquisition_bounds_test.py -- the two acquisition bugs the Selector V2
enablement study measured, tested against local servers only.

1. A HANG. urlopen(timeout=10) bounds one socket operation, not the transfer. A server
   that answers 200 and then dribbles bytes just fast enough keeps every individual
   recv alive, so the fetch never times out and never raises -- there is nothing for
   exception handling upstream to catch. The slow-drip server below reproduces exactly
   that, and the test asserts a real wall-clock ceiling rather than "it eventually
   stopped".

2. A FALLBACK THAT NEVER FIRED. curl_cffi impersonation existed for sites that reject
   our TLS fingerprint, but it only ran when the transport FAILED -- and those sites
   answer 200 with a JavaScript shell, which is a successful transport. Verified live
   on lemonde.fr. The fixtures below reproduce the shape: primary returns 200 and no
   article, impersonation returns the article.

No network, no external site. Both servers bind 127.0.0.1 on an ephemeral port.
"""
from __future__ import annotations

import http.server
import pathlib
import socket
import socketserver
import sys
import threading
import time

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import bounded_http as BH                                     # noqa: E402
from orchestrator import discovery as D                       # noqa: E402

FAILURES: list = []


def check(label, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- " + str(detail)[:240]))
    if not ok:
        FAILURES.append(label)


ARTICLE = ("<html><body>" + "".join(
    "<p>%s</p>" % (("The council report records that the crossing at Fen Lane relies on "
                    "users observing or hearing an approaching vehicle, and the audible "
                    "warning sounded on four of the nine occasions logged in %d. " % (2020 + i))
                   * 3) for i in range(12)) + "</body></html>")

JS_SHELL = ("<html><body><noscript>Please enable JavaScript to continue.</noscript>"
            "<div id=root></div></body></html>")


class _Orch(D.DiscoveryMixin):
    """The real acquisition mixin, nothing stubbed but the logger."""

    def __init__(self):
        import logging
        self.logger = logging.getLogger("source_acquisition_bounds_test")
        self.logger.addHandler(logging.NullHandler())
        self.logger.propagate = False


# ── 1. slow drip ──────────────────────────────────────────────────────────────
class _SlowDripHandler(http.server.BaseHTTPRequestHandler):
    """200, a Content-Length far larger than it will ever send, then one byte at a
    time with a gap comfortably inside the socket timeout. Every individual recv
    succeeds; only a total deadline can stop this."""
    GAP = 0.4

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", "500000")
        self.end_headers()
        try:
            while True:
                self.wfile.write(b"x")
                self.wfile.flush()
                time.sleep(self.GAP)
        except Exception:
            pass

    def log_message(self, *a):
        pass


class _Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def _serve(handler):
    srv = _Server(("127.0.0.1", 0), handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv, "http://127.0.0.1:%d/x" % srv.server_address[1]


def test_a_slow_drip_response_cannot_run_past_the_deadline():
    srv, url = _serve(_SlowDripHandler)
    try:
        o = _Orch()
        t0 = time.monotonic()
        try:
            o._fetch_url_html(url)
            elapsed = time.monotonic() - t0
            check("the drip was stopped by a timeout, not by completing", False,
                  "returned after %.1fs" % elapsed)
        except BH.DeadlineExceeded as e:
            elapsed = time.monotonic() - t0
            check("a slow drip raises SourceAcquisitionTimeout", True)
            check("it says how far it got", "bytes" in str(e), str(e))
        except Exception as e:
            elapsed = time.monotonic() - t0
            check("a slow drip raises SourceAcquisitionTimeout", False,
                  "%s: %s" % (type(e).__name__, e))
        # the bound is the point: the socket timeout alone would never have fired,
        # because the gap between bytes is well inside it.
        check("the gap between bytes is inside the socket timeout, so only a total "
              "deadline can end this",
              _SlowDripHandler.GAP < D._SOURCE_SOCKET_TIMEOUT)
        check("bounded by the deadline plus scheduling slack (%.1fs <= %ds + 3s)"
              % (elapsed, D._SOURCE_LEG_DEADLINE),
              elapsed <= D._SOURCE_LEG_DEADLINE + 3, elapsed)
        check("and it really did wait for the deadline, not fail early",
              elapsed >= D._SOURCE_LEG_DEADLINE - 1, elapsed)
    finally:
        srv.shutdown()
        srv.server_close()


class _HeaderDripHandler(socketserver.BaseRequestHandler):
    """A status line, then response HEADERS one byte at a time. getresponse() blocks
    reading them, so the caller never receives a response object at all -- a deadline
    that only guards the body loop is still running when this test's clock runs out.
    Measured before the fix: past 120s against a 25s body deadline."""
    GAP = 0.3

    def handle(self):
        self.request.recv(4096)
        self.request.sendall(b"HTTP/1.0 200 OK\r\n")
        try:
            for b in (b"X-Pad: " + b"y" * 100000):
                self.request.sendall(bytes([b]))
                time.sleep(self.GAP)
        except Exception:
            pass


def test_a_header_drip_cannot_run_past_the_deadline_either():
    srv, url = _serve(_HeaderDripHandler)
    try:
        o = _Orch()
        t0 = time.monotonic()
        try:
            o._fetch_url_html(url)
            check("a header drip is stopped", False, "it returned")
        except Exception:
            check("a header drip is stopped by the deadline", True)
        elapsed = time.monotonic() - t0
        check("the header gap is inside the socket timeout, so only a total deadline "
              "can end this", _HeaderDripHandler.GAP < D._SOURCE_SOCKET_TIMEOUT)
        check("bounded by the deadline plus scheduling slack (%.1fs <= %ds + 3s)"
              % (elapsed, D._SOURCE_LEG_DEADLINE),
              elapsed <= D._SOURCE_LEG_DEADLINE + 3, elapsed)
        check("every phase is budgeted, not just the body",
              elapsed >= D._SOURCE_LEG_DEADLINE - 1, elapsed)
    finally:
        srv.shutdown()
        srv.server_close()


def test_the_bound_is_a_total_not_a_per_read_timeout():
    """A read-by-read timeout is not what is being tested; a server sending NOTHING
    would trip the old socket timeout too. The drip server sends continuously, so
    passing the test above is only possible with a real total deadline."""
    src = (HERE / "orchestrator" / "discovery.py").read_text()
    shared = (HERE / "bounded_http.py").read_text()
    fn = src.split("def _fetch_url_html(self")[1].split("\n    def ")[0]
    check("the deadline is taken before the request", "deadline = time.monotonic()" in fn)
    check("the connection reads through a deadline-budgeted socket",
          "_bounded_opener(deadline)" in fn)
    check("the body is read with read1, so one underlying read returns control",
          "resp.read1(" in shared)
    check("and not with read(), whose internal loop would reset the socket timeout "
          "on every byte that arrives",
          "resp.read(" not in shared and "resp.read(" not in fn)
    check("the cap is honoured by the shared reader",
          "read_capped(" in fn and "cap=500000" in fn)
    wrapper = shared.split("class DeadlineSocket:")[1].split("\ndef bounded_opener")[0]
    check("every read is budgeted before it can block",
          all(("self._budget()" in wrapper.split("def %s" % m)[1][:120])
              for m in ("recv(", "recv_into(", "send(", "sendall(")), wrapper[:0])
    check("the budget shrinks the timeout to what is left",
          "settimeout(min(remaining, self._op_timeout))" in wrapper)
    check("and refuses outright once the deadline has passed",
          "raise DeadlineExceeded" in wrapper)
    check("makefile reads through the wrapper, so headers are budgeted too",
          "socket.SocketIO(self" in wrapper)
    check("no global socket state is mutated",
          "setdefaulttimeout" not in src and "setdefaulttimeout" not in shared)
    check("no thread or process is spawned to do the bounding",
          "Thread(" not in shared and "subprocess" not in shared and "Thread(" not in fn)
    check("the deadline is carried per opener, never in module state",
          "def bounded_opener(deadline" in shared)
    check("one definition of the bound, shared with the model provider",
          "import bounded_http" in (HERE / "new_engine_v1" / "provider.py").read_text())
    check("redirects are bounded below urllib's default of 10",
          D._SOURCE_MAX_REDIRECTS == 3)
    check("the redirect bound is per-opener, not a global class mutation",
          "max_redirections = max_redirects" in shared
          and "urllib.request.HTTPRedirectHandler.max_redirections =" not in shared
          and "urllib.request.HTTPRedirectHandler.max_redirections =" not in src)
    check("the 500K response cap survives", "500000" in fn)
    check("the content-type check survives", 'text/html" not in content_type' in fn)


def test_no_socket_is_left_open_by_a_timeout():
    srv, url = _serve(_SlowDripHandler)
    try:
        o = _Orch()
        try:
            o._fetch_url_html(url)
        except Exception:
            pass
        check("the response context manager closed the connection",
              threading.active_count() < 50, threading.active_count())
    finally:
        srv.shutdown()
        srv.server_close()


# ── 2. representation-aware fallback ─────────────────────────────────────────
def _fixture(primary_html, primary_raises=False, impersonated=None,
             impersonated_raises=False):
    """An orchestrator whose two legs are scripted, so a test can state exactly what
    each representation was without going near a network."""
    o = _Orch()
    calls = {"primary": 0, "impersonated": 0}

    def primary(url):
        calls["primary"] += 1
        if primary_raises:
            raise D.SourceAcquisitionTimeout("scripted transport failure")
        return primary_html

    def imp(url):
        calls["impersonated"] += 1
        if impersonated_raises:
            raise RuntimeError("scripted impersonation failure")
        return impersonated
    o._fetch_url_html = primary
    o._fetch_url_html_impersonated = imp
    return o, calls


def test_A_a_usable_primary_is_never_refetched():
    o, calls = _fixture(ARTICLE, impersonated=ARTICLE)
    text = o.fetch_source_article("https://example.org/a")
    check("the article was acquired", text and len(text) > 600, len(text or ""))
    check("origin is a real fetch", o._last_fetch_origin == "fetched_article")
    check("the impersonated leg was NOT called", calls["impersonated"] == 0, calls)


def test_A2_a_short_or_promotional_article_is_still_usable_and_not_refetched():
    """Fallback is about representation, never about editorial quality. A thin but
    real article must not trigger a second fetch."""
    thin = ("<html><body>" + "".join(
        "<p>%s</p>" % ("The Nasher Museum exhibition opens on 19 August and runs "
                       "until December, admission free, curated by the museum's own "
                       "staff from the permanent collection. " * 3) for _ in range(4))
        + "</body></html>")
    o, calls = _fixture(thin, impersonated=ARTICLE)
    text = o.fetch_source_article("https://example.org/thin")
    check("the thin article was accepted as acquired",
          o._last_fetch_origin == "fetched_article", o._last_fetch_origin)
    check("no second fetch was made for a merely thin article",
          calls["impersonated"] == 0, calls)


def test_B_a_200_with_a_js_shell_falls_through_and_recovers():
    o, calls = _fixture(JS_SHELL, impersonated=ARTICLE)
    text = o.fetch_source_article("https://example.org/lemonde")
    check("the primary representation was unusable but the transport succeeded",
          calls["primary"] == 1)
    check("the impersonated leg was called", calls["impersonated"] == 1, calls)
    check("acquisition succeeded on the recovered representation",
          text and len(text) > 600, len(text or ""))
    check("origin is a real fetch", o._last_fetch_origin == "fetched_article")
    status, reason = o.classify_source_acquisition(
        text, o._last_fetch_origin, o._last_fetch_paragraph_count)
    check("and it classifies USABLE", status == "USABLE", (status, reason))


def test_C_both_representations_unusable_is_an_acquisition_failure_not_weak_material():
    o, calls = _fixture(JS_SHELL, impersonated=JS_SHELL)
    text = o.fetch_source_article("https://example.org/walled",
                                  fallback_text="a short RSS blurb")
    check("both legs were tried", calls["primary"] == 1 and calls["impersonated"] == 1,
          calls)
    check("origin is NOT a real fetch", o._last_fetch_origin != "fetched_article",
          o._last_fetch_origin)
    status, reason = o.classify_source_acquisition(
        text or "", o._last_fetch_origin, o._last_fetch_paragraph_count)
    check("it classifies as an acquisition failure",
          status == "SOURCE_ACQUISITION_FAILED", (status, reason))
    check("the reason is about acquisition, not about the material",
          "weak" not in reason.lower() and "thin" not in reason.lower()
          and "candidate" not in reason.lower(), reason)


def test_D_a_transport_failure_still_reaches_the_impersonated_leg():
    o, calls = _fixture(None, primary_raises=True, impersonated=ARTICLE)
    text = o.fetch_source_article("https://example.org/dezeen")
    check("the impersonated leg ran on a transport failure", calls["impersonated"] == 1)
    check("the article was recovered", text and len(text) > 600, len(text or ""))
    check("origin is a real fetch", o._last_fetch_origin == "fetched_article")


def test_D2_a_transport_failure_is_not_refetched_twice():
    """The old path already tried impersonation on transport failure. The new
    representation check must not make that a second, duplicate attempt."""
    o, calls = _fixture(None, primary_raises=True, impersonated=JS_SHELL)
    o.fetch_source_article("https://example.org/dead", fallback_text="blurb")
    check("exactly one impersonated attempt, not two", calls["impersonated"] == 1, calls)


def test_E_the_existing_failure_semantics_are_untouched():
    o, calls = _fixture(None, primary_raises=True, impersonated=None)
    text = o.fetch_source_article("https://example.org/gone", fallback_text="an RSS blurb")
    check("falls back to the RSS summary as before", text == "an RSS blurb", text)
    check("and says so through origin", o._last_fetch_origin == "fallback_summary")
    o2, _ = _fixture(None, primary_raises=True, impersonated=None)
    check("with no summary it returns None",
          o2.fetch_source_article("https://example.org/gone") is None)
    check("and origin is none", o2._last_fetch_origin == "none")
    src = (HERE / "orchestrator" / "discovery.py").read_text()
    check("there is still only one definition of a usable article",
          src.count("def classify_source_acquisition") == 1)
    check("the fallback decision defers to that definition",
          "self.classify_source_acquisition(text, \"fetched_article\", paras)" in src)


def main():
    for fn in (test_a_slow_drip_response_cannot_run_past_the_deadline,
               test_a_header_drip_cannot_run_past_the_deadline_either,
               test_the_bound_is_a_total_not_a_per_read_timeout,
               test_no_socket_is_left_open_by_a_timeout,
               test_A_a_usable_primary_is_never_refetched,
               test_A2_a_short_or_promotional_article_is_still_usable_and_not_refetched,
               test_B_a_200_with_a_js_shell_falls_through_and_recovers,
               test_C_both_representations_unusable_is_an_acquisition_failure_not_weak_material,
               test_D_a_transport_failure_still_reaches_the_impersonated_leg,
               test_D2_a_transport_failure_is_not_refetched_twice,
               test_E_the_existing_failure_semantics_are_untouched):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL SOURCE-ACQUISITION BOUNDS TESTS PASSED")


if __name__ == "__main__":
    main()
