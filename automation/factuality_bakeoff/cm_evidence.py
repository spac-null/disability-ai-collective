"""Frozen-evidence loading and representation normalization for the factuality bake-off.

Normalization is representation-only. It never removes words, negation, numbers or
qualifiers, and never reorders tokens. Every transform that changes a string is logged.
"""
from __future__ import annotations

import html
import json
import os
import re
import unicodedata

QUOTE_MAP = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"', "‟": '"',
    "′": "'", "″": '"', "«": '"', "»": '"',
}
DASH_MAP = {
    "‐": "-", "‑": "-", "‒": "-", "–": "-",
    "—": "-", "―": "-", "−": "-",
}
SPACE_RE = re.compile(r"[\s   ​﻿]+")


def normalize(text):
    """Return (normalized_text, transform_log). Purely representational."""
    if text is None:
        return "", ["none:input_was_none"]
    log = []
    cur = text

    prev = cur
    for _ in range(3):
        nxt = html.unescape(cur)
        if nxt == cur:
            break
        cur = nxt
    if cur != prev:
        log.append("html_unescape")

    prev = cur
    cur = unicodedata.normalize("NFC", cur)
    if cur != prev:
        log.append("unicode_nfc")

    prev = cur
    cur = "".join(QUOTE_MAP.get(ch, ch) for ch in cur)
    if cur != prev:
        log.append("quote_fold")

    prev = cur
    cur = "".join(DASH_MAP.get(ch, ch) for ch in cur)
    if cur != prev:
        log.append("dash_fold")

    prev = cur
    cur = SPACE_RE.sub(" ", cur).strip()
    if cur != prev:
        log.append("whitespace_collapse")

    return cur, log


WORD_RE = re.compile(r"[a-z0-9]+")
NEG_TOKENS = {
    "not", "no", "never", "without", "nor", "none", "cannot",
    "neither", "rarely", "unlike", "nothing", "isnt", "dont",
}


def content_signature(text):
    """Signature used by tests to prove normalization preserved meaning-bearing tokens."""
    low = normalize(text)[0].lower()
    words = WORD_RE.findall(low)
    return {
        "numbers": sorted(w for w in words if any(c.isdigit() for c in w)),
        "negations": sorted(w for w in words if w in NEG_TOKENS),
        "word_count": len(words),
    }


def _rd(run_dir, name):
    path = os.path.join(run_dir, name)
    if not os.path.exists(path):
        return None
    try:
        with open(path) as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None


def load_run(run_dir):
    """Load one retained run: frozen sources, frozen facts, claim map, article text."""
    pack = _rd(run_dir, "RESEARCH_PACK.json") or {}
    # Two schemas in the retained corpus: engine runs wrap the pack in "payload";
    # fast-lane runs store {subject, sources} flat. Accept both.
    payload = pack.get("payload") if isinstance(pack.get("payload"), dict) else pack
    if not isinstance(payload, dict):
        payload = {}

    sources = {}
    for s in payload.get("sources") or []:
        sid = s.get("source_id")
        if not sid:
            continue
        raw = s.get("text") or ""
        norm, log = normalize(raw)
        sources[sid] = {
            "source_id": sid,
            "publisher": s.get("publisher") or s.get("outlet"),
            "url": s.get("url"),
            "role": s.get("role"),
            "sha256": s.get("sha256"),
            "raw_text": raw,
            "norm_text": norm,
            "norm_log": log,
            "raw_chars": len(raw),
        }

    snap = _rd(run_dir, "SOURCE_SNAPSHOT.json") or {}
    snap_text = ((snap.get("payload") or {}).get("source_text")) or ""
    if snap_text and not any(s["raw_text"] == snap_text for s in sources.values()):
        norm, log = normalize(snap_text)
        sources.setdefault("SNAP", {
            "source_id": "SNAP", "publisher": None, "role": "snapshot", "sha256": None,
            "raw_text": snap_text, "norm_text": norm, "norm_log": log,
            "raw_chars": len(snap_text),
        })

    fem = _rd(run_dir, "FINAL_EVIDENCE_MANIFEST.json") or {}

    claim_map = None
    for name in ("CLAIM_MAP_OWNER_REPAIRED_F2.json", "CLAIM_MAP_OWNER_REPAIRED.json",
                 "CLAIM_MAP_REPAIRED.json", "CLAIM_MAP.json"):
        cm = _rd(run_dir, name)
        if cm:
            claim_map = {"file": name, "entries": cm.get("claim_map") or []}
            break

    article = None
    for name in ("ARTICLE_COMPLETED.md", "ARTICLE_REPAIRED.md", "ARTICLE_FINAL.md",
                 "article.md", "WRITER_DRAFT.md"):
        path = os.path.join(run_dir, name)
        if os.path.exists(path):
            with open(path) as fh:
                article = {"file": name, "text": fh.read()}
            break

    return {
        "run_id": os.path.basename(run_dir.rstrip("/")),
        "run_dir": run_dir,
        "subject": fem.get("subject"),
        "sources": sources,
        "facts": fem.get("facts") or {},
        "manifest_sources": fem.get("sources") or [],
        "claim_map": claim_map,
        "article": article,
    }


def source_text_for(run, evidence_ids, complete=False):
    """Return (context_text, source_ids_used).

    complete=False -> CITED_BASIS: only the named evidence sources.
    complete=True  -> COMPLETE_FROZEN_EVIDENCE: every frozen source for the run.
    No silent truncation: the full text of each selected source is returned.
    """
    if complete:
        ids = sorted(run["sources"])
    else:
        ids = [i for i in (evidence_ids or []) if i in run["sources"]]
    parts = ["[" + i + "] " + run["sources"][i]["norm_text"] for i in ids]
    return "\n\n".join(parts), ids
