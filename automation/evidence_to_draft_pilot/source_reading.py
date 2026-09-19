"""
source_reading.py -- the Claude vs Gemini source-extraction subtest (section 14).

A SEPARATE EXPERIMENT, ON PURPOSE. Its outputs are never fed into arms A, B or C. If a
better extractor helps, that has to be demonstrated on its own before it is allowed to
move an article comparison, or no improvement is attributable to anything.

WHAT IS IDENTICAL, AND WHAT THAT LIMITS. Both readers receive byte-identical input: the
SAME extracted `text` field from the SAME retained source record, truncated at the same
character count, with the same prompt and the same schema. This is therefore a fair
model-to-model comparison AND a text-only one. Section 14 asks that a document-image task
record whether the model actually receives page images: it does not. No page image exists
in the retained packs -- `include_images` is False in production research and the pack
stores extracted text and a sha256, never image bytes -- so no vision path is exercised
on either side and nothing here may be read as a claim about document-image reading.

WHY GEMINI IS THE ONLY PAID CALL IN THE PILOT. Section 5 puts Claude and Codex on
subscriptions and allows OpenRouter credits for a bounded source-reading trial only. The
model id and its price are verified against the live /models endpoint before any request
is issued, rather than hardcoded from a recommendation, and the aggregate spend is capped
by the shared Ledger.

THE FIELDS. Section 14's list, kept apart rather than merged, because the failures this
subtest exists to see are exactly the ones a flattened record hides: an attribution that
becomes a finding, a qualifier that is dropped, a date that is bound to the wrong event,
a translation presented as the original, and a relationship the passage does NOT
establish being silently supplied.

SCORING IS TWO-SIDED. Precision without coverage is not a win: an extractor that returns
three unimpeachable propositions from a document carrying thirty is worse, for this
publication, than one that returns twenty-five with two qualifier slips. Both numbers are
reported and neither is collapsed into a single score.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
AUTOMATION = HERE.parent
if str(AUTOMATION) not in sys.path:
    sys.path.insert(0, str(AUTOMATION))

from new_engine_v1 import composition as CP                        # noqa: E402

PROMPT_VERSION = "source-reading-v1"
OPENROUTER_URL = "https://openrouter.ai/api/v1"

# Verified live against /models before use; see `verify_model`. Not hardcoded from a
# recommendation -- `verify_model` refuses to proceed if the id is absent from the
# catalogue or if its price has moved above the ceiling below.
GEMINI_MODEL = "google/gemini-3.1-flash-lite"
GEMINI_PRICE_CEILING = {"prompt": 1e-6, "completion": 5e-6}

PER_SOURCE_CHARS = 12000

EXTRACTION_SYSTEM = """You are extracting factual propositions from ONE source document.

Extract what the document ESTABLISHES. Do not add anything from your own knowledge, and
do not resolve an ambiguity the document leaves open. Missing means missing: if a field
is not in the document, use null. An invented value is worse than an absent one.

Separate these, and never merge them:
  - what the document ASSERTS in its own voice
  - what the document ATTRIBUTES to a named speaker or source
  - what the document QUALIFIES (may, could, reportedly, an estimate, a disputed figure)

Reply with ONE JSON object:

{"propositions": [
  {"proposition": "the claim, in one sentence",
   "actor": "who does or undergoes it, or null",
   "event": "the event identity this belongs to, or null",
   "date_time": "as the document gives it, or null",
   "place": "as the document gives it, or null",
   "attribution": "the named speaker or source, or null if the document asserts it",
   "asserted_by_document": true,
   "qualifier": "the hedge, estimate or uncertainty as written, or null",
   "disjunction": "an either/or the document leaves open, or null",
   "support_span": "an EXACT quoted span from the document, copied character for character",
   "span_location": "a short locator, e.g. paragraph 4 or the heading it sits under",
   "original_language": "the language of the support_span",
   "translation": "an English translation IF the span is not English, else null",
   "not_established": "a relationship a reader might infer that this passage does NOT establish, or null"}
]}

The support_span must be copied from the document. Do not paraphrase it, do not tidy its
punctuation and do not translate it in place -- put any translation in `translation`.

Extract thoroughly. A document carrying thirty propositions should not return five."""


def extraction_prompt(text: str) -> str:
    return ("THE DOCUMENT\n\n%s\n\nReply with one JSON object."
            % text[:PER_SOURCE_CHARS])


def parse_extraction(reply: str) -> tuple:
    txt = (reply or "").strip()
    if txt.startswith("```"):
        txt = re.sub(r"^```[a-zA-Z]*\n?", "", txt)
        txt = re.sub(r"\n?```\s*$", "", txt)
    i, j = txt.find("{"), txt.rfind("}")
    if i < 0 or j <= i:
        return [], ["reply carries no JSON object"]
    try:
        obj = json.loads(txt[i:j + 1])
    except Exception as exc:                                       # noqa: BLE001
        return [], ["reply is not valid JSON: %s" % exc]
    props = obj.get("propositions")
    if not isinstance(props, list):
        return [], ["reply carries no 'propositions' list"]
    return [p for p in props if isinstance(p, dict)], []


def score_extraction(props: list, document: str) -> dict:
    """Deterministic scoring. No model judges this.

    SPAN PRESENCE IS NOT ENTAILMENT, and the field name says so: `spans_present` counts
    spans that really occur in the document after the production normalisation
    (`composition.span_in`, whitespace/quote/dash shape only -- it can remove no word and
    reorder nothing). A present span proves the words are there; it does not prove the
    proposition follows from them. That judgement is left to the blind reviewers.
    """
    total = len(props)
    present = sum(1 for p in props
                  if p.get("support_span")
                  and CP.span_in(p["support_span"], document))
    absent = [p.get("support_span") for p in props
              if p.get("support_span")
              and not CP.span_in(p["support_span"], document)]
    return {
        "propositions": total,
        "spans_present_in_document": present,
        "spans_not_found": len(absent),
        "spans_not_found_examples": [str(s)[:120] for s in absent[:5]],
        "with_attribution": sum(1 for p in props if p.get("attribution")),
        "with_qualifier": sum(1 for p in props if p.get("qualifier")),
        "with_disjunction": sum(1 for p in props if p.get("disjunction")),
        "with_date": sum(1 for p in props if p.get("date_time")),
        "with_event_binding": sum(1 for p in props if p.get("event")),
        "with_place": sum(1 for p in props if p.get("place")),
        "non_english_spans": sum(1 for p in props
                                 if (p.get("original_language") or "en").lower()
                                 not in ("en", "english")),
        "translations_kept_separate": sum(1 for p in props if p.get("translation")),
        "declares_not_established": sum(1 for p in props if p.get("not_established")),
        "span_presence_is_not_entailment": True,
    }


# ── the paid half ────────────────────────────────────────────────────────────
def _api_key() -> str:
    """Read from the ops secrets file, never printed and never logged."""
    p = pathlib.Path("/srv/secrets/openclaw.env")
    for line in p.read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("no OPENROUTER_API_KEY in %s" % p)


def verify_model(model: str = GEMINI_MODEL) -> dict:
    """Confirm the id exists and price it, BEFORE any paid request (section 14)."""
    with urllib.request.urlopen("%s/models" % OPENROUTER_URL, timeout=60) as fh:
        cat = json.load(fh)
    row = next((m for m in cat["data"] if m["id"] == model), None)
    if row is None:
        raise RuntimeError("model %r is not in the OpenRouter catalogue" % model)
    pricing = row.get("pricing") or {}
    p_in = float(pricing.get("prompt") or 0)
    p_out = float(pricing.get("completion") or 0)
    if p_in > GEMINI_PRICE_CEILING["prompt"] or p_out > GEMINI_PRICE_CEILING["completion"]:
        raise RuntimeError("model %r prices (%s/%s) exceed the pilot ceiling"
                           % (model, p_in, p_out))
    return {
        "model": model,
        "verified_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "price_per_input_token_usd": p_in,
        "price_per_output_token_usd": p_out,
        "context_length": row.get("context_length"),
        "input_modalities": (row.get("architecture") or {}).get("input_modalities"),
        "receives_page_images_in_this_test": False,
        "input_actually_sent": "extracted text only, from the retained research pack",
    }


def call_gemini(system: str, user: str, model: str = GEMINI_MODEL,
                timeout: int = 180) -> dict:
    """One bounded OpenRouter request. No tools, no search, no fallback provider."""
    body = {
        "model": model,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        # Pinned as far as the API supports it: no silent reroute to another provider,
        # and no automatic paid tool or web search.
        "provider": {"allow_fallbacks": False},
        "tools": [],
        "temperature": 0,
        "max_tokens": 8000,
        "usage": {"include": True},
    }
    req = urllib.request.Request(
        "%s/chat/completions" % OPENROUTER_URL,
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer %s" % _api_key(),
                 "Content-Type": "application/json",
                 "X-Title": "cripminds-evidence-to-draft-pilot"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as fh:
        d = json.load(fh)
    usage = d.get("usage") or {}
    return {
        "text": (d["choices"][0]["message"].get("content") or ""),
        "resolved_model": d.get("model") or model,
        "requested_model": model,
        "provider_name": d.get("provider"),
        "usage": usage,
        "cash_cost_usd": float(usage.get("cost") or 0.0),
        "duration_ms": int((time.time() - t0) * 1000),
    }
