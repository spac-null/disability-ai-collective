"""
testimony_l2.py — L2 active human-testimony retrieval scaffold (A-M
reconciliation item L, 2026-08-14).

The reconciliation confirmed L1 (use testimony already present in the one
fetched primary source) exists but L2 (actively seek a companion first-
person source when the primary lacks one) does not: discovery.py's
fetch_source_article/get_source_text fetch exactly the one already-
identified URL, and nothing anywhere searches for a companion source or
weights human testimony over other text.

Same discipline as cj2_shadow.py, which this module deliberately mirrors:
OFF-by-default, additive-only, mode read from an environment variable,
never raises, a shadow-path failure must never be indistinguishable from
or cause a real production failure.

Mode is read from the L2_TESTIMONY_MODE environment variable:
  OFF    (default, unset) — this mixin's entry point still gets called by
         generate.py (see the call site's own comment for why that's safe),
         but no-ops immediately: zero heuristic evaluation, zero fixture
         read, zero mutation of evidence_packet, zero persistence.
  SHADOW — evaluates the deterministic testimony-needed heuristic against
         evidence_packet's own source_text (zero network calls — the
         heuristic is pure text analysis), then, ONLY if testimony is
         judged needed, attempts to load a pre-supplied companion-source
         CANDIDATE from a fixture file (L2_COMPANION_FIXTURE env var) —
         exactly the same "fixture only, no live orchestration exists yet"
         discipline cj2_shadow.py uses for its own winner input. Runs
         deterministic eligibility checks on the candidate and, if
         eligible, attaches it to evidence_packet under a SEPARATE
         "companion_source" key with its own provenance — NEVER touches
         source_text, source_hash, or evidence_packet_hash, which remain
         the primary factual authority, unchanged, exactly as built by
         grounding.build_evidence_packet. Persists the outcome to
         automation/engagement.db's new l2_testimony_runs table, same file
         every other shadow/plan signal already writes to.

NOT IMPLEMENTED IN THIS MODULE, BY DESIGN (see .claude/l2-testimony-design-
2026-08-14.md for the full preregistered design of the missing piece):
live companion-source SEARCH. Finding a real candidate today requires
either a new search integration (none exists in this codebase — the
closest is fact_check.py's _web_verify_quote/_web_verify_claim, which are
narrow verification queries against a claim already in hand, not open-
ended "find me a first-person account of X" search) or reusing an
existing production call in a new, currently-unvalidated way. Standing up
either is a genuine semantic/source-ranking design question — which
search mechanism, how to rank/score real candidates, how to bound cost
and latency — not a mechanical wiring task, so it is written up as a
design document and left unimplemented rather than guessed at here. This
module's SHADOW mode is real, tested, and runs today against fixture
candidates; only the live-search step is deferred.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime

_MODE_OFF = "OFF"
_MODE_SHADOW = "SHADOW"

REASON_TESTIMONY_ALREADY_PRESENT = "TESTIMONY_ALREADY_PRESENT"
REASON_NO_SOURCE_TEXT = "NO_SOURCE_TEXT"
REASON_NO_COMPANION_FIXTURE = "NO_COMPANION_FIXTURE"
REASON_FIXTURE_UNREADABLE = "FIXTURE_UNREADABLE"
REASON_DUPLICATE_OF_PRIMARY = "DUPLICATE_OF_PRIMARY"
REASON_UNVERIFIABLE_ATTRIBUTION = "UNVERIFIABLE_ATTRIBUTION"
REASON_TOO_SHORT = "TOO_SHORT"
REASON_MISSING_FIELDS = "MISSING_FIELDS"
REASON_ATTACHED = "ATTACHED"
REASON_L2_UNAVAILABLE = "L2_UNAVAILABLE"

# Minimum length for a companion candidate's text to be considered
# substantive enough to evaluate at all -- an "unverifiable/low-quality"
# candidate per instruction 9's own test list is exactly a too-short or
# attribution-less fragment, not a judgment call worth an LLM.
_MIN_COMPANION_TEXT_CHARS = 40

# Same pragmatic first-person-testimony signal used nowhere else in this
# codebase yet -- a quoted span of substantive length sitting near an
# attribution verb. Not a general "is this good testimony" judgment (that
# needs a human or a future semantic pass); only "does the primary source
# already contain SOME first-person quoted material," which is the one
# question L1 vs L2 actually turns on.
_ATTRIBUTION_VERBS = (
    "said", "says", "told", "tells", "recalls", "recalled", "explains",
    "explained", "describes", "described", "according to", "recounts",
    "recounted", "remembers", "remembered", "wrote", "writes",
)
_FIRST_PERSON_RE = re.compile(r"\b(I|I'm|I've|I'd|my|me|we|our)\b")


def _current_l2_mode() -> str:
    return os.environ.get("L2_TESTIMONY_MODE", _MODE_OFF).strip().upper()


def _testimony_needed_heuristic(source_text):
    """Deterministic, zero-network check: does the primary source already
    contain first-person testimony (L1's territory), or is it lacking one
    (L2's territory)? Returns (needed: bool, reason_code: str).

    A quote counts as testimony already present when it is (a) long enough
    to be substantive (>=20 chars, filters short interjections/sentence
    fragments quoted for style), (b) sits within ~80 characters of a
    recognized attribution verb (a quote with no visible speaker doesn't
    establish whose lived experience it is), and (c) either the quote
    itself or its attribution window contains a first-person marker --
    third-person-only quotes ('the report found conditions were poor') are
    not first-person testimony even when clearly attributed.

    This is intentionally narrow and will have real false negatives (missing
    testimony phrased without a classic attribution verb) and false
    positives (a quote that happens to contain 'I' without being genuine
    lived-experience testimony) -- exactly why this stays SHADOW, feeding a
    future calibration pass rather than gating anything today."""
    if not source_text:
        return True, REASON_NO_SOURCE_TEXT

    for m in re.finditer(r'"([^"]{20,400})"', source_text):
        quote = m.group(1)
        window_start = max(0, m.start() - 80)
        window_end = min(len(source_text), m.end() + 80)
        window = source_text[window_start:window_end]
        has_attribution = any(v in window.lower() for v in _ATTRIBUTION_VERBS)
        has_first_person = bool(_FIRST_PERSON_RE.search(quote)) or bool(_FIRST_PERSON_RE.search(window))
        if has_attribution and has_first_person:
            return False, REASON_TESTIMONY_ALREADY_PRESENT

    return True, "NO_FIRST_PERSON_TESTIMONY_DETECTED"


def _source_text_hash(text):
    if not text:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _check_companion_eligibility(candidate, evidence_packet):
    """Deterministic eligibility checks on a companion-source candidate
    dict (expected shape: {"url": str, "text": str, "person": str,
    "quote": str (optional, the specific testimony span)}).

    Returns (eligible: bool, reason_code: str). Never raises -- a
    malformed candidate is just ineligible, not a crash.

    Distinguishes PRIMARY FACTUAL SOURCE from COMPANION HUMAN SOURCE by
    construction: this function only ever judges the candidate against
    itself and the primary's hash/text for duplication -- it never
    upgrades a companion candidate's authority, and a companion candidate
    can never cause the primary source_text/source_hash to change (those
    are computed once, in grounding.build_evidence_packet, before this
    function ever runs, and are never written to here)."""
    if not isinstance(candidate, dict):
        return False, REASON_MISSING_FIELDS
    url = (candidate.get("url") or "").strip()
    text = (candidate.get("text") or "").strip()
    person = (candidate.get("person") or "").strip()
    if not url or not text:
        return False, REASON_MISSING_FIELDS
    if not person:
        return False, REASON_UNVERIFIABLE_ATTRIBUTION
    if len(text) < _MIN_COMPANION_TEXT_CHARS:
        return False, REASON_TOO_SHORT

    primary_text = evidence_packet.get("source_text") or ""
    primary_hash = evidence_packet.get("source_hash")
    if primary_hash and _source_text_hash(text) == primary_hash:
        return False, REASON_DUPLICATE_OF_PRIMARY
    if primary_text and (text in primary_text or primary_text in text):
        return False, REASON_DUPLICATE_OF_PRIMARY

    return True, REASON_ATTACHED


class TestimonyL2Mixin:
    def _l2_testimony_attempt(self, evidence_packet, slug=None):
        """Called unconditionally by generate.py right after evidence_packet
        is built (mirrors cj2_shadow.py's own call-site discipline: the
        mode check lives inside this method, not at the call site, so OFF
        is one code path away from ON rather than a separate call graph).
        Mutates evidence_packet IN PLACE (adds a "companion_source" key)
        rather than returning a new dict -- generate.py's own evidence-
        lineage discipline requires exactly one evidence_packet object
        threaded by reference through every stage (see the Pixel-
        validation mixed-brief incident this guards against); returning a
        new object here would silently violate that invariant. Never
        raises."""
        try:
            mode = _current_l2_mode()
            if mode == _MODE_OFF:
                return

            if mode != _MODE_SHADOW:
                self._persist_l2_testimony_run({
                    "slug": slug, "testimony_needed": None, "needed_reason": None,
                    "companion_attached": False, "outcome_reason": REASON_L2_UNAVAILABLE,
                    "companion_url": None, "companion_person": None,
                })
                return

            source_text = evidence_packet.get("source_text")
            needed, needed_reason = _testimony_needed_heuristic(source_text)

            if not needed:
                evidence_packet["companion_source"] = None
                self._persist_l2_testimony_run({
                    "slug": slug, "testimony_needed": False, "needed_reason": needed_reason,
                    "companion_attached": False, "outcome_reason": needed_reason,
                    "companion_url": None, "companion_person": None,
                })
                return

            fixture_path = os.environ.get("L2_COMPANION_FIXTURE", "")
            if not fixture_path or not os.path.isfile(fixture_path):
                evidence_packet["companion_source"] = None
                self._persist_l2_testimony_run({
                    "slug": slug, "testimony_needed": True, "needed_reason": needed_reason,
                    "companion_attached": False, "outcome_reason": REASON_NO_COMPANION_FIXTURE,
                    "companion_url": None, "companion_person": None,
                })
                return

            try:
                with open(fixture_path, "r", encoding="utf-8") as f:
                    candidate = json.load(f)
            except Exception as e:
                evidence_packet["companion_source"] = None
                self._persist_l2_testimony_run({
                    "slug": slug, "testimony_needed": True, "needed_reason": needed_reason,
                    "companion_attached": False, "outcome_reason": REASON_FIXTURE_UNREADABLE,
                    "companion_url": None, "companion_person": None,
                    "detail": str(e),
                })
                return

            eligible, outcome_reason = _check_companion_eligibility(candidate, evidence_packet)
            if not eligible:
                evidence_packet["companion_source"] = None
                self._persist_l2_testimony_run({
                    "slug": slug, "testimony_needed": True, "needed_reason": needed_reason,
                    "companion_attached": False, "outcome_reason": outcome_reason,
                    "companion_url": (candidate.get("url") if isinstance(candidate, dict) else None),
                    "companion_person": (candidate.get("person") if isinstance(candidate, dict) else None),
                })
                return

            evidence_packet["companion_source"] = {
                "role": "companion_testimony",
                "url": candidate["url"],
                "text": candidate["text"],
                "person": candidate["person"],
                "quote": candidate.get("quote"),
            }
            self._persist_l2_testimony_run({
                "slug": slug, "testimony_needed": True, "needed_reason": needed_reason,
                "companion_attached": True, "outcome_reason": REASON_ATTACHED,
                "companion_url": candidate["url"], "companion_person": candidate["person"],
            })
        except Exception as e:
            self.logger.warning("L2 testimony attempt failed (non-fatal, production unaffected): %s", e)

    def _persist_l2_testimony_run(self, record: dict) -> None:
        """Same automation/engagement.db file every other shadow/plan signal
        already writes to. Never raises."""
        try:
            db_dir = self.repo_root / "automation"
            db_dir.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(db_dir / "engagement.db")
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS l2_testimony_runs (
                        id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                        recorded_at        TEXT NOT NULL,
                        slug               TEXT,
                        mode               TEXT NOT NULL,
                        testimony_needed   INTEGER,
                        needed_reason      TEXT,
                        companion_attached INTEGER NOT NULL,
                        outcome_reason     TEXT,
                        companion_url      TEXT,
                        companion_person   TEXT,
                        detail             TEXT
                    )
                """)
                conn.execute(
                    "INSERT INTO l2_testimony_runs "
                    "(recorded_at, slug, mode, testimony_needed, needed_reason, "
                    " companion_attached, outcome_reason, companion_url, companion_person, detail) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        record.get("slug"), _current_l2_mode(),
                        (None if record.get("testimony_needed") is None
                         else (1 if record["testimony_needed"] else 0)),
                        record.get("needed_reason"),
                        1 if record.get("companion_attached") else 0,
                        record.get("outcome_reason"),
                        record.get("companion_url"), record.get("companion_person"),
                        record.get("detail"),
                    ),
                )
                conn.commit()
            finally:
                conn.close()
        except Exception as e:
            self.logger.warning("L2 testimony run persistence failed (non-fatal): %s", e)
