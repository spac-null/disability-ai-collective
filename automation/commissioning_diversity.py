#!/usr/bin/env python3
"""Small, fail-safe diversity memory for commissioning.

This is a prior, not a quota.  It only counts metadata that an artifact or candidate
explicitly carries; unknown values contribute nothing.  The module is deliberately
pure so selector and knowledge-first can use one contract and tests need no database.
"""
from __future__ import annotations

import collections
import pathlib
import re
import unicodedata

FIELDS = ("subject_country", "subject_world_region", "source_country",
          "source_language", "source_script")
OPTIONAL_FIELDS = FIELDS + ("translation_used", "cross_border_scope")
WINDOW = 20


def source_script(text: str) -> str | None:
    """Return the dominant named Unicode script family, or None when unknowable."""
    counts = collections.Counter()
    for ch in str(text or ""):
        if not ch.isalpha():
            continue
        name = unicodedata.name(ch, "")
        for script in ("LATIN", "CYRILLIC", "GREEK", "ARABIC", "HEBREW",
                       "DEVANAGARI", "BENGALI", "THAI", "HANGUL", "HIRAGANA",
                       "KATAKANA", "CJK", "YI", "GEORGIAN", "ARMENIAN"):
            if script in name:
                counts[script] += 1
                break
    if not counts:
        return None
    return counts.most_common(1)[0][0]


def normalize_metadata(item: dict | None) -> dict:
    item = item or {}
    out = {}
    aliases = {"subject_country": ("subject_country", "country"),
               "subject_world_region": ("subject_world_region", "world_region"),
               "source_country": ("source_country", "origin_source_country"),
               "source_language": ("source_language", "language"),
               "source_script": ("source_script", "script"),
               "translation_used": ("translation_used",),
               "cross_border_scope": ("cross_border_scope",)}
    for key, names in aliases.items():
        for name in names:
            value = item.get(name)
            if value is not None and str(value).strip() != "":
                out[key] = value
                break
    return out


def profile(records: list[dict], limit: int = WINDOW) -> dict:
    """Count explicit metadata in newest-first published records."""
    counts = {f: collections.Counter() for f in FIELDS}
    used = 0
    for record in records[:limit]:
        meta = normalize_metadata(record)
        if not meta:
            continue
        used += 1
        for field in FIELDS:
            value = meta.get(field)
            if value is not None and str(value).strip():
                counts[field][str(value).strip()] += 1
    return {"window": min(len(records), limit), "records_with_metadata": used,
            "counts": {f: dict(counts[f]) for f in FIELDS}}


def prior(metadata: dict | None, history: dict | None) -> tuple[float, dict]:
    """Moderate additive prior: rare/absent values gain, repeated values lose.

    Unknown metadata is neutral.  The selector's existing quality ordering remains
    lexicographically ahead of this value, so a clearly stronger story still wins.
    """
    meta = normalize_metadata(metadata)
    counts = (history or {}).get("counts") or {}
    effects = {}
    total = 0.0
    for field in FIELDS:
        value = meta.get(field)
        if value is None or str(value).strip() == "":
            effects[field] = 0.0
            continue
        n = int((counts.get(field) or {}).get(str(value).strip(), 0))
        effect = 0.18 if n == 0 else (0.08 if n == 1 else (-0.10 if n >= 3 else 0.0))
        effects[field] = effect
        total += effect
    return round(total, 3), effects


def rank_candidates(candidates: list[dict], history: dict | None) -> list[dict]:
    """Annotate and stable-sort proposed candidates by prior only within their quality order."""
    out = []
    for index, candidate in enumerate(candidates):
        c = dict(candidate)
        value, effects = prior(c, history)
        c["commissioning_metadata"] = normalize_metadata(c)
        c["diversity_prior"] = value
        c["diversity_prior_effects"] = effects
        c["_commission_order"] = index
        out.append(c)
    return sorted(out, key=lambda c: (-c["diversity_prior"], c["_commission_order"]))


def read_frontmatter_posts(posts_dir: pathlib.Path, limit: int = WINDOW) -> list[dict]:
    """Read only explicit public frontmatter; no inference from prose or URLs."""
    paths = sorted(pathlib.Path(posts_dir).glob("*.md"), reverse=True)
    records = []
    for path in paths[:limit]:
        text = path.read_text(encoding="utf-8", errors="replace")
        if not text.startswith("---"):
            continue
        block = text.split("---", 2)[1]
        record = {}
        for line in block.splitlines():
            m = re.match(r"^([A-Za-z_][\w-]*):\s*[\"']?([^\"']*?)[\"']?\s*$", line)
            if m:
                record[m.group(1)] = m.group(2).strip()
        records.append(record)
    return records


def published_history(posts_dir: pathlib.Path, limit: int = WINDOW) -> dict:
    return profile(read_frontmatter_posts(posts_dir, limit), limit)


def current_history(limit: int = WINDOW) -> dict:
    """Canonical published window; an operator may point tests at a fixture directory."""
    posts = pathlib.Path(__file__).resolve().parents[1] / "_posts"
    return published_history(posts, limit)
