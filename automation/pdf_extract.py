#!/usr/bin/env python3
"""
pdf_extract.py -- run a PDF text-layer extraction that cannot outlive its deadline.

Companion to bounded_http (which bounds a network read) and impersonated_fetch (which
owns one browser-impersonating request): the project keeps its I/O primitives at this
level so both the orchestrator and the engine package can use them, and so the engine
package can stay free of sqlite3, requests, socket and subprocess.

WHY A PROCESS
A deadline checked between pages is not a bound. Opening a malformed object, resolving
a cyclic cross-reference table or decompressing a crafted stream all happen inside a
single call, and a check that only runs between pages never gets the chance to run. The
narrowest mechanism that actually bounds the work is a process that can be killed, and
it buys a second property for free: a parser crash on a hostile file cannot take the
production run down with it.

Same interpreter, no external binary. The worker imports nothing from this project,
opens no file of its own, and has no network module available to it.

WHAT IT IS NOT
No OCR. No embedded attachments, no JavaScript, no forms or actions, no following a
link found inside a document. Bytes in, page text out.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

# Reads PDF bytes on stdin, writes one JSON object on stdout.
_WORKER = r'''
import io, json, sys
def out(o):
    sys.stdout.write(json.dumps(o))
    sys.stdout.flush()
    raise SystemExit(0)
try:
    import pypdf
except Exception as e:
    out({"error": "unavailable", "detail": type(e).__name__})
data = sys.stdin.buffer.read()
try:
    r = pypdf.PdfReader(io.BytesIO(data), strict=False)
    if getattr(r, "is_encrypted", False):
        # An empty user password is a real and common case; anything else needs a
        # credential we do not have and will not guess at.
        try:
            if r.decrypt("") == 0:
                out({"error": "encrypted"})
        except Exception:
            out({"error": "encrypted"})
    n = len(r.pages)
    if n > MAX_PAGES:
        out({"error": "page_limit", "pages_available": n})
    pages = []
    for i, page in enumerate(r.pages, 1):
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        pages.append({"page_no": i, "text": t})
    out({"pages": pages, "pages_available": n})
except SystemExit:
    raise
except Exception as e:
    out({"error": "parse", "detail": "%s: %s" % (type(e).__name__, str(e)[:200])})
'''


def worker_source(max_pages: int) -> str:
    return "MAX_PAGES = %d\n%s" % (max_pages, _WORKER)


def parse_bounded(data: bytes, *, timeout: float, max_pages: int) -> dict:
    """One bounded attempt. Never raises for an ordinary failure.

    Returns the worker's own result -- {"pages": [...], "pages_available": n} or
    {"error": "unavailable"|"encrypted"|"page_limit"|"parse"} -- plus
    {"error": "timeout"} when the deadline killed it. Naming those outcomes is the
    caller's job; this only makes sure one of them arrives.
    """
    try:
        proc = subprocess.run(
            [sys.executable, "-c", worker_source(max_pages)],
            input=data, capture_output=True, timeout=timeout,
            # No shell, and nothing inherited that the interpreter does not need.
            env={"PATH": os.environ.get("PATH", ""), "PYTHONPATH": "",
                 "PYTHONHOME": os.environ.get("PYTHONHOME", "")},
        )
    except subprocess.TimeoutExpired:
        # subprocess.run kills the child on timeout: the bound is real, not advisory.
        return {"error": "timeout"}
    except Exception as e:
        return {"error": "parse", "detail": type(e).__name__}
    if proc.returncode != 0 and not proc.stdout.strip():
        return {"error": "parse", "detail": "worker exit %s" % proc.returncode}
    try:
        return json.loads(proc.stdout.decode("utf-8", "replace") or "{}") or {
            "error": "parse", "detail": "empty result"}
    except Exception:
        return {"error": "parse", "detail": "unreadable result"}
