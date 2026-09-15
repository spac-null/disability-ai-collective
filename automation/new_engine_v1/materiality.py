"""Materiality adjudication for unsupported factual surface.

SAFETY REMAINS AUTHORITATIVE ABOUT FACTUAL SUPPORT. Nothing here licenses a claim,
adds anything to the approved surface, or whitelists a token. The raw Safety finding
is preserved verbatim and travels into the audit trail unchanged: an article that
publishes through this module publishes with "unsupported" still recorded against it.

This module answers a different and narrower question -- CONSEQUENCE, not truth:

    If this unsupported element were corrected or removed, would the reader
    understand the story materially differently?

That is Crip Minds doctrine, already applied to Reader findings (see
publication_safety_bridge._check_reader_materiality_decision, which validates the same
MINOR/MATERIAL shape). MATERIALITY > PERFECTION: Safety investigates; materiality
decides whether the finding is serious enough to stop publication.

    raw_safety_decision = HOLD
    materiality          = MINOR
    effective_decision   = PASS_WITH_MINOR_FINDINGS

WHY THIS EXISTS. On 2026-09-14 and 2026-09-15 consecutive runs were lost at SAFETY to
one word. "A Mental Health Centre, CSM in Italian, is..." and "In the Italian region of
Lombardy..." each carry a word no approved material grants -- Safety was right both
times, and the word is real-world knowledge the source never supplied. But deleting it
changes no carrier, no chronology, no causality, no allegation, no argument and no
conclusion. The article means the same thing. Losing a day's work to that is perfection
overriding materiality.

THE MECHANICAL FLOOR COMES FIRST, AND THE MODEL CANNOT REACH BELOW IT. The hard
overrides are not requests to the adjudicator; they are decided here, before any call:

  * an unapproved NUMBER is never adjudicated -- a material number or statistic is on
    the hard list, and a figure the approved material never granted is exactly that;
  * unapproved SENSORY / SCENE / SPATIAL surface is never adjudicated -- that channel
    exists to catch invented events, testimony and scene, all hard-list categories;
  * an entity inside a QUOTATION is never adjudicated -- a central quotation is on the
    hard list, and a name inside quotation marks is part of what was quoted;
  * an entity appearing in the TITLE or DEK is never adjudicated -- that surface states
    the thesis, and a fact necessary to the thesis is on the hard list.

Only unapproved ENTITIES outside quotation, title and dek reach the model at all. So the
categories the doctrine refuses to let anyone downgrade cannot be downgraded even by a
model that tries: they never become a question.

ONE ADJUDICATION, AND NO GATE SHOPPING. One call, one verdict, for the whole set of
eligible findings at once. No retry until MINOR, no alternate model, no recomposition
loop, no automatic owner repair. If the verdict is MATERIAL the day ends.

FAIL CLOSED, ALWAYS. Uncertain, malformed, unavailable, contradictory, or unable to
explain itself all resolve to MATERIAL. There is no fallback guess, and silence is never
read as permission.
"""

import re

# The dimensions the adjudicator may name. "none" is the only one compatible with
# continuing: the doctrine's MINOR requires carrier, event, chronology, causality,
# argument, allegation, conclusion and the reader's substantive understanding to be
# unchanged, so naming any of them is naming a reason to stop.
AFFECTED_DIMENSIONS = ("carrier", "chronology", "causality", "allegation",
                       "argument", "conclusion", "none")

# Blocking findings whose unsupported tokens this module knows how to adjudicate.
# Anything else -- any unfamiliar category -- makes the whole attempt ineligible and the
# run stays exactly as terminal as it was. Fail-closed, like every other guard here.
ELIGIBLE_PREFIXES = ("NEW_UNSUPPORTED_FACTS", "PACKAGE_UNSUPPORTED_FACTS")

_BUCKET = re.compile(r"(numbers|entities|sensory|scene|spatial)=\[([^\]]*)\]")


def _tokens(bucket_text):
    return [v.strip().strip("'").strip('"') for v in bucket_text.split(",") if v.strip()]


def parse_blocking(blocking):
    """Every unsupported token in the blocking list, by channel.

    Returns (buckets, eligible) where `eligible` is False when any blocking entry is a
    category this module does not recognise -- in which case no adjudication may run.
    """
    buckets = {k: [] for k in ("numbers", "entities", "sensory", "scene", "spatial")}
    eligible = bool(blocking)
    for entry in blocking or []:
        text = str(entry)
        if not text.startswith(ELIGIBLE_PREFIXES):
            eligible = False
            continue
        for name, items in _BUCKET.findall(text):
            buckets[name].extend(_tokens(items))
    return buckets, eligible


def _quoted_spans(text):
    out = []
    for m in re.finditer(r'"[^"]{0,400}"|“[^”]{0,400}”', text or ""):
        out.append(m.group(0))
    return out


def _title_and_dek(article_text, package):
    surface = []
    for line in (article_text or "").splitlines():
        if line.startswith("# "):
            surface.append(line[2:])
            break
    for key in ("title", "dek", "meta_description", "social_hook", "excerpt"):
        v = (package or {}).get(key)
        if isinstance(v, str):
            surface.append(v)
    return " ".join(surface)


def hard_material(buckets, article_text, package):
    """The findings the model never gets to see, with the reason each is withheld.

    This is the doctrine's hard-override list expressed mechanically. It runs BEFORE any
    model call, and nothing below it can reverse it.
    """
    reasons = []
    for tok in buckets.get("numbers") or []:
        reasons.append((tok, "unapproved number or statistic"))
    for channel in ("sensory", "scene", "spatial"):
        for tok in buckets.get(channel) or []:
            reasons.append((tok, "unapproved %s surface (invented event/scene/testimony)"
                            % channel))
    quoted = " ".join(_quoted_spans(article_text))
    thesis = _title_and_dek(article_text, package)
    for tok in buckets.get("entities") or []:
        if tok and re.search(r"\b%s\b" % re.escape(tok), quoted):
            reasons.append((tok, "appears inside a quotation"))
        elif tok and re.search(r"\b%s\b" % re.escape(tok), thesis):
            reasons.append((tok, "appears in the title or dek (thesis surface)"))
    return reasons


def adjudicable(buckets, article_text, package):
    """Entities outside quotation, title and dek -- the only findings a model may judge."""
    withheld = {tok for tok, _ in hard_material(buckets, article_text, package)}
    return [t for t in (buckets.get("entities") or []) if t and t not in withheld]


# ── locating a finding so the adjudicator can see its consequence ───────────────────

def locate(article_text, token):
    """(sentence, paragraph) containing `token`. Context, never permission."""
    body = article_text or ""
    para = ""
    for block in body.split("\n\n"):
        if re.search(r"\b%s\b" % re.escape(token), block):
            para = block.strip()
            break
    sentence = ""
    for s in re.split(r"(?<=[.!?])\s+", para or body):
        if re.search(r"\b%s\b" % re.escape(token), s):
            sentence = s.strip()
            break
    return sentence, para


MATERIALITY_SYSTEM = (
    "You adjudicate CONSEQUENCE, not truth.\n\n"
    "An editorial safety check has found factual surface in a finished article that the "
    "approved research material never granted. The finding stands: the element IS "
    "unsupported, it stays recorded as unsupported, and you are not being asked whether "
    "it is correct, plausible, or probably true. Do not reason about whether it is true. "
    "Do not research it. Do not defend it.\n\n"
    "Your only question, for each finding:\n\n"
    "    If this unsupported element were CORRECTED OR REMOVED, would the reader "
    "understand the story materially differently?\n\n"
    "Answer MINOR only when removing or correcting it leaves ALL of these unchanged: the "
    "carrier, the event, the chronology, the causality, the argument, any allegation, the "
    "conclusion, and the reader's substantive understanding. If removing it would weaken, "
    "shift or complicate any of those, it is MATERIAL.\n\n"
    "Answer MATERIAL whenever the element bears on: the identity of a central person or "
    "entity, the identity of the primary carrier, a central quotation, an allegation "
    "presented as fact, chronology the story needs, causality the argument needs, a "
    "material number or statistic, a diagnosis, a legal or status claim, core "
    "institutional responsibility, any fact the thesis or conclusion depends on, anything "
    "contradicting the source record, or an invented event, testimony or motive.\n\n"
    "If you are uncertain, or cannot explain the consequence concretely, answer MATERIAL. "
    "Uncertainty is not a reason to let something through."
)

MATERIALITY_SCHEMA = (
    "Reply with ONE JSON object:\n"
    '{"findings": [{"finding": "the exact unsupported span, verbatim",\n'
    '               "classification": "MINOR|MATERIAL",\n'
    '               "counterfactual": "what changes in the article if it is removed or\n'
    '                                  corrected -- concrete, not a restatement",\n'
    '               "changes_reader_understanding": "YES|NO",\n'
    '               "affected_dimensions": ["carrier|chronology|causality|allegation|\n'
    '                                        argument|conclusion|none"],\n'
    '               "reason": "one or two sentences"}]}\n'
    "Use \"none\" alone when no dimension is affected. Never pair \"none\" with another "
    "dimension. Classify every finding you are given, exactly once."
)


def build_user(findings_context, packet_summary, safety_finding):
    parts = ["THE SAFETY FINDING (authoritative; the element is unsupported):",
             str(safety_finding)[:800], ""]
    if packet_summary:
        parts += ["WHAT THE ARTICLE IS DOING (from the frozen editorial packet):",
                  str(packet_summary)[:1500], ""]
    parts.append("FINDINGS TO ADJUDICATE:")
    for i, f in enumerate(findings_context, 1):
        parts += ["", "%d. UNSUPPORTED SPAN: %s" % (i, f["token"]),
                  "   SENTENCE: %s" % f["sentence"][:600],
                  "   PARAGRAPH: %s" % f["paragraph"][:1200]]
        if f.get("ledger_facts"):
            parts.append("   RELATED LEDGER FACTS: %s" % f["ledger_facts"][:600])
    return "\n".join(parts)


def packet_summary(packet, arch):
    """Carrier, thesis and argument, as the frozen packet already states them."""
    out = []
    for src, keys in ((arch or {}, ("carrier", "thesis", "crip_turn", "spine")),
                      (packet or {}, ("carrier", "thesis", "subject"))):
        for k in keys:
            v = src.get(k)
            if isinstance(v, str) and v.strip():
                out.append("%s: %s" % (k, v.strip()[:300]))
            elif isinstance(v, dict):
                lab = v.get("label") or v.get("name") or v.get("text")
                if isinstance(lab, str) and lab.strip():
                    out.append("%s: %s" % (k, lab.strip()[:300]))
    seen, uniq = set(), []
    for line in out:
        if line not in seen:
            seen.add(line)
            uniq.append(line)
    return "\n".join(uniq)


# ── verdict ─────────────────────────────────────────────────────────────────────────

def _clean_dims(value):
    if not isinstance(value, list):
        return None
    dims = [str(d).strip().lower() for d in value if str(d).strip()]
    if not dims or any(d not in AFFECTED_DIMENSIONS for d in dims):
        return None
    if "none" in dims and len(dims) > 1:
        return None                     # "none" plus a dimension is contradictory
    return dims


def verdict(reply, expected_tokens):
    """Fold one model reply into a decision. Anything short of a complete, coherent,
    unanimous MINOR is MATERIAL."""
    result = {"classification": "MATERIAL", "findings": [], "may_continue": False,
              "reason": ""}
    rows = (reply or {}).get("findings")
    if not isinstance(rows, list) or not rows:
        result["reason"] = "adjudicator returned no findings"
        return result

    got = {}
    for row in rows:
        if not isinstance(row, dict):
            result["reason"] = "malformed finding row"
            return result
        tok = str(row.get("finding") or "").strip().strip("'\"")
        cls = str(row.get("classification") or "").strip().upper()
        chg = str(row.get("changes_reader_understanding") or "").strip().upper()
        dims = _clean_dims(row.get("affected_dimensions"))
        cf = str(row.get("counterfactual") or "").strip()
        why = str(row.get("reason") or "").strip()
        entry = {"finding": tok, "classification": cls,
                 "changes_reader_understanding": chg, "affected_dimensions": dims or [],
                 "counterfactual": cf, "reason": why}
        result["findings"].append(entry)
        if cls not in ("MINOR", "MATERIAL") or chg not in ("YES", "NO") or dims is None:
            result["reason"] = "incomplete or invalid adjudication for %r" % tok
            return result
        if not cf or not why:
            result["reason"] = "adjudicator did not explain %r" % tok
            return result
        got[tok] = entry

    missing = [t for t in expected_tokens if t not in got]
    if missing:
        result["reason"] = "findings not adjudicated: %s" % missing
        return result
    extra = [t for t in got if t not in expected_tokens]
    if extra:
        result["reason"] = "adjudicated findings that were not asked about: %s" % extra
        return result

    for tok in expected_tokens:
        e = got[tok]
        if not (e["classification"] == "MINOR"
                and e["changes_reader_understanding"] == "NO"
                and e["affected_dimensions"] == ["none"]):
            result["reason"] = "%r is MATERIAL under the rule" % tok
            return result

    result["classification"] = "MINOR"
    result["may_continue"] = True
    result["reason"] = "every unsupported element is peripheral: removing it changes no "\
                       "carrier, chronology, causality, allegation, argument or conclusion"
    return result
