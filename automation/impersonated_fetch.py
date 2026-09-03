#!/usr/bin/env python3
"""
impersonated_fetch.py -- one bounded browser-impersonating GET, shared.

WHY THIS EXISTS
Plain urllib is refused with HTTP 403 by some sites not because of its User-Agent
string but because its TLS ClientHello (JA3 fingerprint) is not a browser's. Confirmed
live on the production host, twice: stock curl got 403 on dezeen.com while curl_cffi
impersonating chrome124 got a clean 200 with the full article on the same URL, and on
2026-09-03 five lsa.umich.edu policy pages that the Research Pack had recorded as
http_403 returned 200 with 646-1,702 usable words each through the same impersonation.

WHY IT IS ITS OWN MODULE
There were nearly two implementations of this request. The orchestrator's anchor
acquisition has had one since 2026-08-10; the Research Pack needed the same thing, and
a second copy is how two networking paths drift apart. So the request lives here once.
The orchestrator keeps its own method name and its own timeout constant -- existing
tests monkeypatch the former and budget against the latter -- and delegates only the
request itself.

It must be importable from anywhere, including the engine package, which may not
import the orchestrator. So: stdlib plus curl_cffi, and no project imports.

NOT A RETRY MECHANISM
One request per call. Callers decide whether a second attempt is permitted at all, and
own the budget it spends. Nothing here loops.
"""
from __future__ import annotations

try:
    from curl_cffi import requests as _requests
except Exception:                                   # not installed, or import failed
    _requests = None

# chrome124/safari17_0/firefox133 all get through; chrome110's fingerprint stays
# blocked on the sites this exists for. Do not "upgrade" this to chrome110.
IMPERSONATE = "chrome124"
DEFAULT_CAP = 500_000


def available() -> bool:
    """False when curl_cffi is not installed. Callers must degrade, never assume."""
    return _requests is not None


def get(url: str, *, timeout: float, cap: int = DEFAULT_CAP) -> dict | None:
    """One impersonated GET.

    None when curl_cffi is unavailable -- distinct from a request that ran and failed.
    Otherwise {"status": int, "content_type": str (lowercased), "text": str}, capped.

    The status and content type are REPORTED rather than judged, because callers do not
    agree about them: the orchestrator wants HTML or nothing, while the Research Pack
    has to tell a PDF apart from a block so it can keep saying PDF_UNSUPPORTED.

    Exceptions propagate. Every caller already treats a raised fetch as a failed one,
    and swallowing here would hide a transport failure as an empty page.
    """
    if _requests is None:
        return None
    r = _requests.get(url, impersonate=IMPERSONATE, timeout=timeout)
    return {"status": r.status_code,
            "content_type": (r.headers.get("Content-Type") or "").lower(),
            "text": (r.text or "")[:cap]}


def html_or_none(url: str, *, timeout: float, cap: int = DEFAULT_CAP) -> str | None:
    """HTML on a 200, else None -- the orchestrator's long-standing semantics."""
    rec = get(url, timeout=timeout, cap=cap)
    if rec is None or rec["status"] != 200 or "text/html" not in rec["content_type"]:
        return None
    return rec["text"]
