"""
shadow_capture.py -- passive, OFF-by-default observational capture of one production
article run, for Phase-2 live-vs-shadow comparison.

WHY THIS EXISTS
Production does not persist the exact generation-time source material. `article_plans`
stores `source_hash` and `evidence_packet_hash` but never the bytes; `news_seeds` stores
only the RSS summary. That makes it impossible to prove later that a shadow run consumed
the same evidence a legacy run consumed, and re-fetching a URL is not proof (pages change,
and some sites block fetching outright). This module closes that gap ONCE.

It also captures the RAW WRITER OUTPUT, which is otherwise ephemeral: `raw_content` is
overwritten by the whole-document rewrite a few lines later. The target architecture removes
that rewrite stage, so distinguishing what the legacy WRITER produced from what the legacy
REWRITER changed is the single most important comparison signal, and it exists nowhere on
disk today.

CONTRACT -- this module is NON-AUTHORITATIVE
  * OFF by default. `SHADOW_CAPTURE` unset -> every entry point returns immediately.
  * Never raises into the pipeline. Every public function is wrapped; on any failure it
    logs and returns. A capture failure MUST NOT change what production does, and in
    particular must never cause an article to be held. This module observes the legacy
    baseline; it is not part of the target ACCEPT/HOLD architecture.
    The guards catch `Exception`, NOT `BaseException`: observability must not swallow
    process-level signals such as SystemExit or KeyboardInterrupt, which have to
    propagate so the orchestrator can shut down cleanly.
  * Append-only. It writes new files under its own root and never rewrites one.
  * No SQLite. No network. No subprocess. No LLM call. Nothing under _posts/ or _drafts/.
  * No mutation of any object handed to it -- payloads are serialised, never modified.

USAGE (call sites in generate.py are one line each, all inside try/except by construction):
    from shadow_capture import capture
    capture("evidence", run_id=..., source_text=..., evidence_packet=...)
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import tempfile
import uuid
from datetime import datetime, timezone

SCHEMA_VERSION = "shadow-capture-v1"
ENV_FLAG = "SHADOW_CAPTURE"
ENV_ROOT = "SHADOW_CAPTURE_ROOT"
DEFAULT_ROOT = "/srv/data/cripminds-shadow-capture"

# Substrings that must never be written into a capture bundle. If an upstream bug ever
# lets a credential into a source packet we stop capturing that field rather than persist
# it -- see _scan_for_secrets.
_SECRET_MARKERS = (
    "api_key", "apikey", "api-key", "secret", "password", "passwd", "authorization",
    "bearer ", "sk-", "ghp_", "xoxb-", "access_token", "refresh_token", "private_key",
    "BEGIN RSA", "BEGIN OPENSSH", "BEGIN PRIVATE KEY",
)


def enabled() -> bool:
    return os.environ.get(ENV_FLAG, "").strip().upper() in ("1", "ON", "TRUE", "YES")


def _root() -> pathlib.Path:
    return pathlib.Path(os.environ.get(ENV_ROOT, DEFAULT_ROOT))


def new_run_id() -> str:
    """Chronologically sortable, collision-free. Safe to call when disabled."""
    return "%s-%s" % (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"), uuid.uuid4().hex[:8])


def _sha256(data) -> str:
    if data is None:
        return ""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _scan_for_secrets(text) -> list:
    if not isinstance(text, str):
        return []
    low = text.lower()
    return [m for m in _SECRET_MARKERS if m.lower() in low]


def _atomic_write(path: pathlib.Path, text: str) -> None:
    """Write via a temp file + rename so a partially written bundle is never observed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=".part")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _write(run_id: str, relpath: str, text: str, logger=None) -> dict:
    """Persist one artifact. Refuses to write anything that looks like a credential."""
    hits = _scan_for_secrets(text)
    if hits:
        msg = ("shadow_capture: REFUSED to persist %s -- possible secret markers %s. "
               "Capture skipped for this field; production unaffected." % (relpath, hits[:3]))
        if logger:
            logger.error(msg)
        return {"path": relpath, "status": "REFUSED_POSSIBLE_SECRET", "markers": hits[:3]}
    p = _root() / run_id / relpath
    _atomic_write(p, text)
    return {"path": relpath, "sha256": _sha256(text), "bytes": len(text.encode("utf-8"))}


def _append_manifest(run_id: str, event: str, entries: dict, logger=None) -> None:
    """Append-only event log. Never rewrites an existing line."""
    line = json.dumps({
        "schema_version": SCHEMA_VERSION,
        "event": event,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "entries": entries,
    }, sort_keys=True, ensure_ascii=False)
    p = _root() / run_id / "manifest.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def _j(obj) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False, default=str)


# --------------------------------------------------------------------------- events
def _ev_evidence(run_id, logger=None, *, raw_cached_source=None, returned_source=None,
                 packet_source=None, evidence_packet=None, provenance=None):
    """The four distinct source representations. 'Source text' is NOT one object:
      raw_cached_source  -- discovery.py's _source_text_cache[url], the full extraction
      returned_source    -- get_source_text()'s returned slice (cached[:max_chars])
      packet_source      -- the post-fallback-downgrade value handed to build_evidence_packet
                            (None when origin == fallback_summary)
      evidence_packet    -- the packet dict actually passed to planner/reviewer/executor
    """
    e = {}
    for name, val in (("source/raw_cached_source.txt", raw_cached_source),
                      ("source/returned_source.txt", returned_source),
                      ("source/packet_source.txt", packet_source)):
        if val is not None:
            e[name] = _write(run_id, name, val, logger)
    if evidence_packet is not None:
        e["source/evidence_packet.json"] = _write(run_id, "source/evidence_packet.json",
                                                  _j(evidence_packet), logger)
    if provenance is not None:
        e["source/provenance.json"] = _write(run_id, "source/provenance.json", _j(provenance), logger)
    return e


def _ev_commission(run_id, logger=None, *, fable_brief=None, commission_input=None):
    e = {}
    if commission_input is not None:
        e["legacy/commission_input.json"] = _write(run_id, "legacy/commission_input.json",
                                                   _j(commission_input), logger)
    if fable_brief is not None:
        e["legacy/fable_brief.json"] = _write(run_id, "legacy/fable_brief.json", _j(fable_brief), logger)
    return e


def _ev_writer(run_id, logger=None, *, writer_prompt=None, raw_writer_output=None,
               provider=None, model=None):
    """RAW writer output, BEFORE the whole-document rewrite. Ephemeral otherwise."""
    e = {}
    if writer_prompt is not None:
        e["legacy/writer_prompt.txt"] = _write(run_id, "legacy/writer_prompt.txt", writer_prompt, logger)
    if raw_writer_output is not None:
        e["legacy/writer_output_raw.md"] = _write(run_id, "legacy/writer_output_raw.md",
                                                  raw_writer_output, logger)
    e["legacy/writer_meta.json"] = _write(run_id, "legacy/writer_meta.json",
                                          _j({"provider": provider, "model": model}), logger)
    return e


def _ev_rewrite(run_id, logger=None, *, pre_rewrite=None, post_rewrite=None):
    e = {}
    for name, val in (("legacy/pre_rewrite.md", pre_rewrite), ("legacy/post_rewrite.md", post_rewrite)):
        if val is not None:
            e[name] = _write(run_id, name, val, logger)
    if pre_rewrite is not None and post_rewrite is not None:
        e["rewrite_changed_content"] = (pre_rewrite != post_rewrite)
    return e


def _ev_disposition(run_id, logger=None, *, gate_fixed=None, degraded_stages=None,
                    should_block=None, review_clean=None, fact_check_status=None,
                    disposition=None, slug=None, article_file=None):
    payload = {
        "slug": slug, "article_file": str(article_file) if article_file else None,
        "gate_fixed": gate_fixed, "degraded_stages": list(degraded_stages or []),
        "should_block": should_block, "review_clean": review_clean,
        "fact_check_status": fact_check_status, "disposition": disposition,
    }
    return {"legacy/disposition.json": _write(run_id, "legacy/disposition.json", _j(payload), logger)}


_EVENTS = {
    "evidence": _ev_evidence,
    "commission": _ev_commission,
    "writer": _ev_writer,
    "rewrite": _ev_rewrite,
    "disposition": _ev_disposition,
}


def capture(event: str, run_id: str = None, logger=None, **kwargs) -> None:
    """The ONLY public entry point. Never raises. Returns None always.

    A failure here is logged and swallowed on purpose: observability must not be able to
    alter, block, or fail a production article run.
    """
    try:
        if not enabled() or not run_id:
            return
        handler = _EVENTS.get(event)
        if handler is None:
            return
        entries = handler(run_id, logger, **kwargs)
        _append_manifest(run_id, event, entries, logger)
    except Exception as exc:                # broad, but NOT BaseException: SystemExit
                                            # and KeyboardInterrupt must propagate
        try:
            if logger:
                logger.error("shadow_capture: capture(%r) failed, continuing unaffected: %s", event, exc)
        except Exception:
            pass
        return


def seal(run_id: str, logger=None) -> None:
    """Write COMPLETE marker. A bundle without it is incomplete -> CAPTURE_INVALID."""
    try:
        if not enabled() or not run_id:
            return
        _atomic_write(_root() / run_id / "COMPLETE",
                      json.dumps({"schema_version": SCHEMA_VERSION,
                                  "sealed_at": datetime.now(timezone.utc).isoformat()}) + "\n")
    except Exception as exc:
        try:
            if logger:
                logger.error("shadow_capture: seal failed, continuing unaffected: %s", exc)
        except Exception:
            pass
