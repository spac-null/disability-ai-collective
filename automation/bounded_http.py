"""
bounded_http.py -- HTTP reads that cannot outlive a wall-clock deadline.

Stdlib only, no project imports, so both the source-acquisition path and the model
provider can share one definition instead of growing two that drift.

WHY THIS EXISTS
urlopen(timeout=N) bounds one socket OPERATION, not the transfer, and every byte that
arrives resets it. A server returning one byte every N-1 seconds keeps a request alive
indefinitely and never raises, so there is nothing for exception handling upstream to
catch. Measured twice while building this: a body drip ran unbounded, and after that
was fixed a HEADER drip ran past a 25-second body deadline, because http.client blocks
reading headers before a caller ever holds a response object to bound.

So the deadline lives on the socket. Every read is budgeted -- connect, request,
headers, redirects, body -- and there is no phase left that reads unbudgeted. Reads
still pass through io.BufferedReader, whose read(n) loops until it has n bytes, but
each underlying read now goes through _budget() and cannot outlive what is left.

No global socket state is mutated. No thread or process exists to be left behind: the
deadline is checked by the very call that would otherwise block.
"""
from __future__ import annotations

import http.client
import io
import socket
import time
import urllib.request


class DeadlineExceeded(Exception):
    """A request outlived its wall-clock budget. An ordinary transport failure as far
    as callers are concerned -- they already treat any exception as a failed fetch."""


class DeadlineSocket:
    """Delegates to a real socket, refusing any operation once the deadline has passed
    and never letting one block beyond it."""

    def __init__(self, sock, deadline: float, op_timeout: float):
        self._sock = sock
        self._deadline = deadline
        self._op_timeout = op_timeout

    def _budget(self):
        remaining = self._deadline - time.monotonic()
        if remaining <= 0:
            raise DeadlineExceeded("deadline reached")
        self._sock.settimeout(min(remaining, self._op_timeout))

    def recv(self, *a, **kw):
        self._budget()
        return self._sock.recv(*a, **kw)

    def recv_into(self, *a, **kw):
        self._budget()
        return self._sock.recv_into(*a, **kw)

    def send(self, *a, **kw):
        self._budget()
        return self._sock.send(*a, **kw)

    def sendall(self, *a, **kw):
        self._budget()
        return self._sock.sendall(*a, **kw)

    def makefile(self, mode="rb", buffering=None, **kw):
        # SocketIO reads through THIS object, so http.client's header and body reads
        # are budgeted too. That is the whole point of the wrapper.
        #
        # The _io_refs line is socket.makefile's own bookkeeping, reproduced because
        # this stands in for it: urllib closes the connection socket as soon as it has
        # a response and relies on that count to keep the descriptor alive for whoever
        # still holds the file object. Without it the first body read fails with
        # "Bad file descriptor" -- which it did, before this line existed.
        self._sock._io_refs += 1
        raw = socket.SocketIO(self, "rb")
        return raw if buffering == 0 else io.BufferedReader(raw)

    def __getattr__(self, name):
        return getattr(self._sock, name)


def bounded_opener(deadline: float, *, op_timeout: float, max_redirects: int):
    """An opener whose every connection reads under `deadline` (a time.monotonic
    value). Built per call, so nothing global is mutated and two concurrent requests
    cannot inherit each other's deadline."""

    class _Redirects(urllib.request.HTTPRedirectHandler):
        max_redirections = max_redirects

    def _wrap(conn):
        conn.sock = DeadlineSocket(conn.sock, deadline, op_timeout)

    class _Conn(http.client.HTTPConnection):
        def connect(self):
            super().connect()
            _wrap(self)

    class _SConn(http.client.HTTPSConnection):
        def connect(self):
            super().connect()
            _wrap(self)

    class _H(urllib.request.HTTPHandler):
        def http_open(self, req):
            return self.do_open(_Conn, req)

    class _SH(urllib.request.HTTPSHandler):
        def https_open(self, req):
            return self.do_open(_SConn, req)

    return urllib.request.build_opener(_Redirects(), _H(), _SH())


def read_capped(resp, *, cap: int, chunk: int) -> bytes:
    """Read at most `cap` bytes. read1, not read: read(n) is a BufferedReader loop that
    keeps calling recv until it has n bytes. Both are budgeted by DeadlineSocket, but
    read1 returns control here, so the cap is honoured chunk by chunk instead of in one
    enormous request."""
    parts, size = [], 0
    while size < cap:
        try:
            piece = resp.read1(min(chunk, cap - size))
        except (TimeoutError, socket.timeout) as e:
            raise DeadlineExceeded("read stalled after %d bytes: %s" % (size, e)) from e
        if not piece:
            break
        parts.append(piece)
        size += len(piece)
    return b"".join(parts)
