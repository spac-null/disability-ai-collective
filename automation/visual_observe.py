#!/usr/bin/env python3
"""
visual_observe.py -- bounded visual-observation utility. Non-claim-bearing, unwired.

WHY THIS EXISTS
`figure_harvest.py` retains the sentences a publisher wrote under a photograph. It cannot
see the photograph. A 2026-09-07 retrospective benchmark over two published subjects
(WildSumaco, Tollymore) established what the picture holds that the prose does not: on
WildSumaco the ground-to-deck steps, the doorway through the earthen wall and the stair
to the upper room are visible and appear in NO source in the pack, which says only that
the pavilion "lifts off the forest floor". That is a real research question the text
cannot ask.

The same benchmark established the failure mode, and it decided this module's shape. One
call carrying five mixed visuals read the photographs well and the drawings badly: it
reported "a key is provided" for Tollymore's floor plan without reading a single room
name, and it misread three of the seven printed level labels on WildSumaco's section into
plausible-looking wrong numbers (+3.75 for +3.70, +2.65 for +2.60, -0.60 for -0.80).

Both findings are load-bearing:
  - a drawing gets its own call at full useful resolution, never a slot in a batch;
  - a number that came out of a picture may not leave this module, ever.

WHAT THIS IS
A manual utility. Given local image paths, it makes one or more bounded model calls and
writes `VISUAL_OBSERVATIONS.json`. Nothing more.

WHAT THIS IS NOT, and none of these is a future extension of this module
  - No image acquisition. Paths are supplied by a person; this module never discovers,
    searches for, crawls or downloads an image.
  - No OCR subsystem. There is no tesseract, no layout parser, no glyph model. The vision
    model reads what it reads and the numeric guard below assumes it reads badly.
  - No stage consumes the output. Worth, Architecture, Writer, the freeze, the ledger and
    the fact check are all untouched and none of them imports this module.
  - No RESEARCH_PACK mutation and no `SCHEMA_VERSION` bump. This writes a sidecar beside
    a run, not into the frozen contract.
  - No path to an image generator. Neither Recraft nor `gen_images` is imported here, and
    no source image is copied, re-encoded to disk, or written under `assets/`. The bytes
    this module encodes exist only in the request it sends.
  - No retry for a better answer. A transport failure is recorded as a failure. There is
    no second attempt, no reroll, no "ask again with a nudge" -- a module that retries
    until it likes the reading is a module that manufactures its own evidence.

NON-CLAIM-BEARING, AND WHAT THAT MEANS CONCRETELY
`VISUAL_OBSERVATIONS.json` is DATA AVAILABLE, NOT EDITORIAL EVIDENCE CONSUMED, exactly as
`figures[]` is today. No fact may rest on a line in it. It is a model's reading of a
picture: unlike a harvested caption, it is NOT verbatim by construction and NOT a
substring of anything a publisher wrote. It cannot be verified against the source text,
so it cannot be treated like source text. If a later phase exposes this file to
ARCHITECTURE, that phase owes its own decision about what may stand on it; carrying it
into the ledger is not that decision and is not authorised here.

THE CAPTION IS A SEPARATE EVIDENCE OBJECT
A publisher caption is not a description of the image it sits above. Measured on the
benchmark: Dezeen's "The team sought to integrate the building into the surrounding
forest" sits over an interior photograph of a table and a whiteboard. So this module does
not send captions to the model and does not store them: fusing the two would invent a
sentence no publisher wrote about an image nobody described. A caption lives on the pack
source, in `figures[]`, and the two are joined -- if ever -- by a human reading both.
"""
from __future__ import annotations

import argparse
import base64
import datetime
import hashlib
import io
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

API_URL = "https://openrouter.ai/api/v1/chat/completions"

# A utility model on the OpenRouter utility path, deliberately NOT the editorial
# transport. Claude-family editorial calls run on the owner's subscription via
# `claude_cli_provider` (Phase 2B); this is a cheap bounded describe-a-picture job and
# has no business on that path. Measured on the benchmark: $0.0061 for two calls.
DEFAULT_MODEL = "google/gemini-2.5-flash"

SIDECAR_NAME = "VISUAL_OBSERVATIONS.json"
SIDECAR_VERSION = 1          # this sidecar's own shape. NOT the engine SCHEMA_VERSION.

# ── bounds ────────────────────────────────────────────────────────────────────
PHOTO_BATCH_MAX = 5          # photographs per call
DRAWING_BATCH = 1            # a drawing is never batched. This is not configurable.
PHOTO_MAX_PX = 1100
DRAWING_MAX_PX = 2200        # full useful resolution; Dezeen serves drawings at 2364
MAX_VISUALS_PER_JOB = 12
MAX_TOKENS = 6000
TIMEOUT_SECONDS = 240

DRAWING_TYPES = ("PLAN", "SECTION", "DIAGRAM", "MAP")
PHOTO_TYPES = ("PHOTO", "OTHER", "")

FIELDS = ("observable_facts", "spatial_relationships", "not_established",
          "questions_raised")

# ── the prompt ────────────────────────────────────────────────────────────────
SYSTEM = (
    "You are a bounded visual-observation utility for an editorial research pipeline. "
    "You describe only what is visibly present in the image supplied.\n\n"
    "Return, for EVERY visual, exactly these fields and nothing else:\n"
    "VISUAL_ID\nTYPE:\nOBSERVABLE_FACTS:\nSPATIAL_RELATIONSHIPS:\nNOT_ESTABLISHED:\n"
    "QUESTIONS_RAISED:\n\n"
    "OBSERVABLE_FACTS: only what can actually be seen. Allowed shape: \"A stair rises "
    "beside the central wall.\" / \"The occupied floor is elevated above visible "
    "ground.\" / \"Two building volumes are separated by an uncovered gap.\"\n"
    "SPATIAL_RELATIONSHIPS: how the visible parts stand to one another.\n"
    "NOT_ESTABLISHED: name the important unknowns explicitly -- whether another entrance "
    "exists, whether a lift or ramp exists outside the frame, whether this is the only "
    "route, whether the drawing shows every level.\n"
    "QUESTIONS_RAISED: questions a journalist could put to a source. Not conclusions.\n\n"
    "FORBIDDEN, anywhere in your output:\n"
    "- any statement that something is accessible or inaccessible, or any reference to "
    "accessibility standards or legal compliance;\n"
    "- any conclusion about what a wheelchair user can or cannot do;\n"
    "- that a route is the only one, or that no alternative exists;\n"
    "- what an architect intended, ignored or wanted;\n"
    "- ANY NUMBER. No dimension, no height, no level, no scale value, no count read off "
    "a drawing's labels or key. This holds even when the number is printed in the image: "
    "a printed level or scale bar is exactly what this utility is measured to misread, so "
    "do not quote one. Where a drawing prints a WORD label for a room or a space, quote "
    "that word verbatim and say it is a printed label -- \"A space is labelled "
    "OBSERVATORIO DE AVES.\" is correct; \"+2.60\" is not, and \"eleven rooms are "
    "numbered\" is not.\n\n"
    "Where the image is a drawing, read its printed word labels and its key, and say what "
    "they say. Say which spaces the labels let you identify and which they do not."
)

USER_PREAMBLE = (
    "%d visual(s) follow. Each is preceded by its VISUAL_ID. No publisher caption is "
    "supplied and none should be inferred: describe the image in front of you. Return the "
    "six-field block for each visual, in order."
)

# ── guards ────────────────────────────────────────────────────────────────────
# Fail-closed by design: a guard hit DROPS the whole observation rather than editing it.
# Half a sentence with its number cut out is a sentence nobody wrote and nobody can check.

# Any digit at all. The benchmark's misreads were all digit strings, and a plausible wrong
# number is worse than no number because nothing downstream can tell it from a right one.
_DIGIT_RE = re.compile(r"\d")

# Spelled-out magnitudes. A small spelled count ("Two building volumes are separated by an
# uncovered gap.") is an ALLOWED observation and must survive, so a bare number word is not
# a hit -- only a number word bound to a unit or a measured quantity.
_NUMBER_WORD = (r"(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
                r"dozen|half|quarter)")
_UNIT = (r"(?:m|mm|cm|km|metres?|meters?|ft|feet|foot|inch(?:es)?|yards?|"
         r"square\s+(?:metres?|meters?|feet)|m2|sq\s?m|storeys?|stories)")
_MEASURE_RES = (
    re.compile(r"\b%s[-\s]+%s\b" % (_NUMBER_WORD, _UNIT), re.I),
    re.compile(r"\b(?:scale|scale\s+bar|ratio)\b", re.I),
    re.compile(r"\b(?:level|floor|datum)\s+(?:height|heights|label|labels|marker|markers)\b", re.I),
    re.compile(r"\b(?:dimension|dimensions|measurement|measurements|elevation\s+value)\b", re.I),
)

# Conclusions this utility may not reach, whatever the picture shows.
_PROHIBITED_RES = (
    (re.compile(r"\b(?:in)?accessib\w*", re.I), "accessibility_conclusion"),
    (re.compile(r"\bADA\b|\bequality\s+act\b|\bbuilding\s+regulations?\b", re.I), "legal_framework"),
    (re.compile(r"\bcomplian\w*|\bconforms?\s+to\b|\bmeets?\s+the\s+standard\b", re.I), "compliance_conclusion"),
    (re.compile(r"\bwheelchair\w*|\bmobility\s+(?:aid|impair\w*)|\bstep[-\s]free\b", re.I), "wheelchair_conclusion"),
    (re.compile(r"\bonly\s+(?:route|way|entrance|access|means)\b|\bsole\s+(?:route|entrance)\b", re.I), "route_exclusivity"),
    (re.compile(r"\bno\s+(?:other|alternative)\s+(?:route|way|entrance|access)\b", re.I), "route_exclusivity"),
    (re.compile(r"\bcannot\s+(?:be\s+)?(?:reach|reached|enter|entered|access|accessed|use|used)\w*", re.I), "reachability_conclusion"),
    (re.compile(r"\bunreachable\b|\bimpassable\b", re.I), "reachability_conclusion"),
    (re.compile(r"\bdangerous\b|\bunsafe\b|\bhazard\w*", re.I), "safety_verdict"),
    (re.compile(r"\bintended\s+(?:for|to)\b|\bintention\w*|\bthe\s+architect\s+(?:ignored|wanted|chose|failed)", re.I), "intent_claim"),
)


# A count of the numbered items in a key ("Eleven rooms are numbered.") is a count
# inferred from labels, which is prohibited, and it carries no digit -- so the digit rule
# misses it. A count of VISIBLE THINGS ("Two building volumes are separated by an
# uncovered gap.") is an allowed observation. The difference is what is being counted, so
# the rule binds the number word to label vocabulary, not to any number word at all.
_LABEL_COUNT_RES = (
    re.compile(r"\b%s\b[^.]{0,40}\b(?:numbered|labelled|labeled|labels|legend|key)\b"
               % _NUMBER_WORD, re.I),
    re.compile(r"\b(?:key|legend)\b[^.]{0,40}\b%s\b\s+(?:entries|items|rooms|spaces)\b"
               % _NUMBER_WORD, re.I),
)


def _numeric_hit(text: str) -> str:
    if _DIGIT_RE.search(text):
        return "vision_read_number"
    for r in _LABEL_COUNT_RES:
        if r.search(text):
            return "label_count"
    for r in _MEASURE_RES:
        if r.search(text):
            return "measurement_language"
    return ""


# NOT_ESTABLISHED exists to say "whether this is the only route is not established" --
# the exact string the prohibited list would otherwise catch. So in that field a
# prohibited shape is permitted ONLY in the interrogative/unknown frame below, and an
# affirmative one ("The building is inaccessible.") is still dropped. Found by the
# module's own test on the first run: the naive guard deleted the disclaimer and kept the
# observation it qualified, which is worse than either alone.
_UNKNOWN_FRAME_RE = re.compile(
    r"\b(?:whether|if)\b.*\b(?:not\s+(?:established|shown|visible|determinable)|"
    r"unknown|unclear|cannot\s+be\s+determined|is\s+not\s+established)\b|"
    r"^\s*whether\b", re.I | re.S)


def _prohibited_hit(text: str, *, allow_unknown_frame: bool = False) -> str:
    for r, reason in _PROHIBITED_RES:
        if r.search(text):
            if allow_unknown_frame and _UNKNOWN_FRAME_RE.search(text):
                return ""
            return reason
    return ""


# ── printed key entries ───────────────────────────────────────────────────────
# A plan key reads "05 GUEST BEDROOM". The digit there is an INDEX, not a quantity, and
# the words beside it are the printed room vocabulary this utility exists to recover --
# the one thing the batched benchmark call failed to read at all. The blanket digit rule
# above deleted all 22 such observations on the Tollymore proof, which is the guard
# working exactly as written and destroying the only material worth having.
#
# So a key entry is harvested into `printed_labels` as an IDENTIFIER STRING and its prose
# sentence is still dropped. No numeral survives in any prose field, nothing here is a
# measurement, and a label is never a count: "eleven rooms are numbered" carries no
# uppercase label and is dropped whole, as it must be.
_KEY_ENTRY_RE = re.compile(r"\b(\d{1,2})\s+([A-Z][A-Z][A-Z /&'\u2019-]{1,38})(?=[,;.]|\s{2}|$)")


def harvest_printed_labels(text: str) -> list:
    """Printed key entries in one observation. [] when the line is about magnitude."""
    for r in _MEASURE_RES:                       # a scale bar is never a room label
        if r.search(text):
            return []
    out = []
    for idx, label in _KEY_ENTRY_RE.findall(text):
        clean = label.strip(" ,;.-")
        if len(clean) >= 3:
            out.append({"index": idx, "label": clean, "kind": "printed_key_entry"})
    return out


def guard(field: str, text: str) -> str:
    """'' when the observation may stand, else the reason it may not."""
    return _numeric_hit(text) or _prohibited_hit(text)


def apply_guards(record: dict) -> tuple:
    """Split one parsed visual into (kept_record, rejected_entries).

    NOT_ESTABLISHED is guarded for the prohibited list but NOT for numbers or route
    language: "whether this is the only route is not established" is the guard's own
    output shape, and dropping it would delete the disclaimer while keeping the
    observation it qualifies. That asymmetry is deliberate -- read the field names.
    """
    kept, rejected, labels = dict(record), [], []
    for field in FIELDS:
        survivors = []
        for line in record.get(field) or []:
            reason = (_prohibited_hit(line, allow_unknown_frame=True)
                      if field == "not_established" else guard(field, line))
            if reason:
                if reason == "vision_read_number":
                    labels.extend(harvest_printed_labels(line))
                rejected.append({"visual_id": record.get("visual_id"), "field": field,
                                 "reason": reason, "text": line})
            else:
                survivors.append(line)
        kept[field] = survivors
    seen, uniq = set(), []
    for l in labels:
        k = (l["index"], l["label"])
        if k not in seen:
            seen.add(k)
            uniq.append(l)
    kept["printed_labels"] = uniq
    kept["guard_dropped"] = len(rejected)
    return kept, rejected


# ── image encoding ────────────────────────────────────────────────────────────
def _encode(path: pathlib.Path, max_px: int) -> tuple:
    """(data-uri, sha256 of the ORIGINAL file, original size). Pillow only resizes."""
    from PIL import Image                                   # local: not every caller has it
    raw = path.read_bytes()
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    original = im.size
    im.thumbnail((max_px, max_px))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=88)
    return ("data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode(),
            hashlib.sha256(raw).hexdigest(), original)


def is_drawing(type_hint: str) -> bool:
    return (type_hint or "").upper() in DRAWING_TYPES


def plan_calls(items: list) -> list:
    """Group visuals into calls. A drawing is alone in its call, always."""
    calls, batch = [], []
    for it in items:
        if is_drawing(it.get("type_hint")):
            if batch:
                calls.append(batch)
                batch = []
            calls.append([it])
            continue
        batch.append(it)
        if len(batch) >= PHOTO_BATCH_MAX:
            calls.append(batch)
            batch = []
    if batch:
        calls.append(batch)
    return calls


# ── response parsing ──────────────────────────────────────────────────────────
_FIELD_LABELS = {
    "TYPE": "type",
    "OBSERVABLE_FACTS": "observable_facts",
    "SPATIAL_RELATIONSHIPS": "spatial_relationships",
    "NOT_ESTABLISHED": "not_established",
    "QUESTIONS_RAISED": "questions_raised",
}
_VID_RE = re.compile(r"^\s*VISUAL_ID\s*:?\s*(\S+)", re.I)
_LABEL_RE = re.compile(r"^\s*(%s)\s*:\s*(.*)$" % "|".join(_FIELD_LABELS), re.I)


def _plain(line: str) -> str:
    """Strip markdown emphasis and a leading bullet. The model is asked for six bare
    labels and mostly complies; when it bolds them, that is not a parse failure."""
    return re.sub(r"^\s*[-*\u2022]\s+", "", (line or "").replace("**", "").replace("__", ""))


def _sentences(blob: str) -> list:
    """One field's text -> discrete observations. Bullets if present, else sentences."""
    lines = [re.sub(r"^\s*[-*•]\s*", "", l).strip()
             for l in blob.splitlines() if l.strip()]
    if len(lines) > 1:
        return [l for l in lines if l]
    text = " ".join(lines).strip()
    if not text:
        return []
    return [s.strip() for s in re.split(r"(?<=[.?])\s+(?=[A-Z\"'(])", text) if s.strip()]


def parse_blocks(text: str) -> list:
    """Model text -> [{visual_id, type, <four list fields>}]. Tolerant of markdown."""
    out, cur, field = [], None, None
    for raw in (text or "").splitlines():
        line = _plain(raw)
        m = _VID_RE.match(line)
        if m:
            if cur:
                out.append(cur)
            cur = {"visual_id": m.group(1).strip().strip(":"), "type": "",
                   **{f: [] for f in FIELDS}}
            field = None
            continue
        if cur is None:
            continue
        m = _LABEL_RE.match(line)
        if m:
            key = _FIELD_LABELS[m.group(1).upper()]
            rest = m.group(2).strip()
            if key == "type":
                cur["type"], field = rest, None
            else:
                field = key
                cur[field] = ([rest] if rest else [])
            continue
        if field:
            cur[field].append(line.strip())
    if cur:
        out.append(cur)
    for rec in out:
        for f in FIELDS:
            rec[f] = _sentences("\n".join(rec[f]))
    return out


# ── the call ──────────────────────────────────────────────────────────────────
def _api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if key:
        return key
    env = pathlib.Path("/srv/secrets/openclaw.env")
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("OPENROUTER_API_KEY="):
                return line.split("=", 1)[1].strip()
    return ""


def _post(body: dict, key: str) -> dict:
    req = urllib.request.Request(
        API_URL, data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json",
                 "HTTP-Referer": "https://cripminds.com",
                 "X-Title": "cripminds visual observation utility"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as r:
        return json.loads(r.read())


def observe(items: list, *, out_dir=None, model: str = DEFAULT_MODEL,
            api_key: str = "", dry_run: bool = False) -> dict:
    """Observe manually supplied visuals. Writes the sidecar when out_dir is given.

    items: [{"path": str, "visual_id"?: str, "source_id"?: str, "type_hint"?: str}]

    ONE ATTEMPT PER CALL. A transport failure lands in `errors` and the job continues; it
    is never retried, because a retry policy on a describe-a-picture job is a policy for
    getting the reading you wanted.
    """
    if len(items) > MAX_VISUALS_PER_JOB:
        raise ValueError("%d visuals exceeds MAX_VISUALS_PER_JOB=%d"
                         % (len(items), MAX_VISUALS_PER_JOB))
    norm = []
    for i, it in enumerate(items):
        p = pathlib.Path(it["path"]).expanduser()
        if not p.exists():
            raise FileNotFoundError(str(p))
        norm.append({"path": p,
                     "visual_id": it.get("visual_id") or "V-%d" % (i + 1),
                     "source_id": it.get("source_id") or "",
                     "type_hint": (it.get("type_hint") or "").upper()})

    key = api_key or _api_key()
    if not key and not dry_run:
        raise RuntimeError("no OPENROUTER_API_KEY available")

    calls = plan_calls(norm)
    observations, rejected, errors, usage = [], [], [], []
    for group in calls:
        max_px = DRAWING_MAX_PX if is_drawing(group[0].get("type_hint")) else PHOTO_MAX_PX
        content = [{"type": "text", "text": USER_PREAMBLE % len(group)}]
        meta = []
        for it in group:
            uri, sha, size = _encode(it["path"], max_px)
            meta.append({"visual_id": it["visual_id"], "source_id": it["source_id"],
                         "type_hint": it["type_hint"], "file": it["path"].name,
                         "file_sha256": sha, "original_px": list(size),
                         "sent_max_px": max_px})
            content.append({"type": "text", "text": "VISUAL_ID: " + it["visual_id"]})
            content.append({"type": "image_url", "image_url": {"url": uri}})
        if dry_run:
            usage.append({"visuals": [m["visual_id"] for m in meta], "dry_run": True})
            continue
        body = {"model": model, "temperature": 0, "max_tokens": MAX_TOKENS,
                "messages": [{"role": "system", "content": SYSTEM},
                             {"role": "user", "content": content}]}
        try:
            resp = _post(body, key)
        except (urllib.error.HTTPError, urllib.error.URLError, OSError) as e:
            detail = ""
            if isinstance(e, urllib.error.HTTPError):
                detail = e.read()[:400].decode("utf-8", "replace")
            errors.append({"visuals": [m["visual_id"] for m in meta],
                           "error": "%s: %s" % (type(e).__name__, detail or e)})
            continue
        text = (resp.get("choices") or [{}])[0].get("message", {}).get("content", "")
        usage.append({"visuals": [m["visual_id"] for m in meta],
                      "requested_model": model, "actual_model": resp.get("model"),
                      "usage": resp.get("usage")})
        by_id = {m["visual_id"]: m for m in meta}
        for rec in parse_blocks(text):
            m = by_id.get(rec["visual_id"])
            if m is None:
                errors.append({"visuals": [rec["visual_id"]],
                               "error": "response names a visual that was not sent"})
                continue
            kept, rej = apply_guards(rec)
            kept.update({k: m[k] for k in ("source_id", "type_hint", "file",
                                           "file_sha256", "original_px", "sent_max_px")})
            observations.append(kept)
            rejected.extend(rej)
        missing = set(by_id) - {o["visual_id"] for o in observations}
        for vid in sorted(missing):
            errors.append({"visuals": [vid], "error": "no block returned for this visual"})

    sidecar = {
        "sidecar_version": SIDECAR_VERSION,
        "created_at": datetime.datetime.now(datetime.timezone.utc)
                              .isoformat(timespec="seconds"),
        "status": "NON_CLAIM_BEARING",
        "notice": ("A model's reading of a picture. NOT verbatim, NOT a substring of any "
                   "publisher text, NOT verifiable against the source. No stage reads "
                   "this file; no fact may rest on a line in it. Publisher captions are "
                   "a SEPARATE evidence object and are deliberately absent here."),
        "guards": {"numeric": "any digit, or measurement language, drops the observation",
                   "prohibited": sorted({r for _, r in _PROHIBITED_RES}),
                   "not_established_exemption": "prohibited list only, numbers allowed "
                                                "to name an unknown",
                   "printed_labels": "printed key entries kept as IDENTIFIER strings; "
                                     "never a measurement, never a count, and the prose "
                                     "sentence that carried them is still dropped"},
        "requested_model": model,
        "calls": len(calls),
        "call_policy": {"photo_batch_max": PHOTO_BATCH_MAX,
                        "drawing_batch": DRAWING_BATCH,
                        "photo_max_px": PHOTO_MAX_PX,
                        "drawing_max_px": DRAWING_MAX_PX,
                        "temperature": 0, "retries": 0},
        "observations": observations,
        "rejected": rejected,          # guard audit material. NOT evidence, NOT for reuse.
        "errors": errors,
        "usage": usage,
    }
    if out_dir:
        d = pathlib.Path(out_dir)
        d.mkdir(parents=True, exist_ok=True)
        (d / SIDECAR_NAME).write_text(json.dumps(sidecar, indent=1, ensure_ascii=False))
    return sidecar


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Observe manually supplied source visuals.")
    ap.add_argument("images", nargs="+",
                    help="local image path, optionally PATH:VISUAL_ID:TYPE_HINT")
    ap.add_argument("--out-dir", help="directory to write %s into" % SIDECAR_NAME)
    ap.add_argument("--source-id", default="", help="pack source id these visuals came from")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--dry-run", action="store_true", help="plan calls, send nothing")
    a = ap.parse_args(argv)
    items = []
    for spec in a.images:
        parts = spec.split(":")
        items.append({"path": parts[0],
                      "visual_id": parts[1] if len(parts) > 1 else "",
                      "type_hint": parts[2] if len(parts) > 2 else "",
                      "source_id": a.source_id})
    out = observe(items, out_dir=a.out_dir, model=a.model, dry_run=a.dry_run)
    print(json.dumps(out, indent=1, ensure_ascii=False))
    return 0 if not out["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
