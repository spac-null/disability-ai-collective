#!/usr/bin/env python3
"""
jurisdiction.py -- no default national framework.

THE INCIDENT, and it is the whole specification.
The WildSumaco article's argument rested on a directory field: an American field-station
directory records ADA accessibility for WildSumaco Biological Station as No. The building
the article was about is a 2025 teaching pavilion in Napo Province, Ecuador. Three
separate things were wrong at once and each is a different error:

  the ENTITY    the record is the STATION's, not the pavilion's, and nothing in the
                ledger tied the two
  the FRAMEWORK the ADA is United States law; Ecuador is not in the United States
  the PLACEMENT two accurate sentences, set side by side so a reader draws a third
                conclusion neither source supports

Grounding objected on five of seven runs, latterly to the adjacency rather than to any
wording, and the claim was removed from the live article on 2026-09-06 (032cf7f).

THE DOCTRINE
A legal or accessibility standard is evidence about THE RECORD THAT STATES IT. It becomes
evidence about the article's subject only when the evidence establishes that relation.
English-language research imports US frameworks into non-US stories constantly, because
US material is what is written down in English; being the only standard anybody wrote
down does not make a standard local.

ONE SEMANTIC OWNER, AND IT IS THE LEDGER
Not Research, not Worth, not the Writer, and not the same rule copied into five stages.
The ledger is already the sole origin of factual permission, and it already enforces the
rule this is a special case of: "Do not append a person, a date, an institution or a
relation that the span itself does not state." Jurisdiction is that rule applied to
standards -- the span says a directory records a value, so the permission is to report
what the directory records, and nothing more. Every later stage inherits the restriction
without knowing this module exists.

WHAT IT DOES, DETERMINISTICALLY
No model call. No network. No geocoding. No legal reasoning. Two tables and some regex.

  1. `subject_country` is READ OFF FROZEN EVIDENCE or left None. A country counts only
     if the pack's own source texts name it, and only if one country clearly dominates.
     Nothing is inferred from a top-level domain, a publisher's address or a model's
     knowledge of where a place is. Unknown is a permitted, expected answer, and when it
     is the answer this module restricts nothing.
  2. A fact whose proposition names a jurisdiction-BOUND standard is classified. Where
     the standard's jurisdiction and the subject's country are both known and differ,
     the fact is RESTRICTED, not deleted: its claim_type becomes ATTRIBUTION -- a
     permission to report that a named record says a thing -- and it is stamped with what
     it actually is.

WHAT IT DELIBERATELY IS NOT
  - Not a global legal ontology. BOUND_STANDARDS is a short list of standards that are
    unambiguously the law of one country and that this publication's material actually
    keeps hitting. It is meant to stay short.
  - Not a ban on the ADA. A US subject with US evidence is untouched, and there is a test
    that says so. The failure being prevented is a foreign framework silently becoming
    the local one, not the ADA existing.
  - Not a rule about the word "accessibility". Ordinary access facts, in any country, are
    ordinary facts and this module never sees them.
"""
from __future__ import annotations

import re

# ── what a standard IS, once you stop assuming ────────────────────────────────
LOCAL_LAW = "LOCAL_LAW"                          # the law where the subject is
LOCAL_CODE = "LOCAL_CODE"                        # a building/accessibility code, ditto
FOREIGN_LEGAL_STANDARD = "FOREIGN_LEGAL_STANDARD"  # law, but of somewhere else
INSTITUTIONAL_RULE = "INSTITUTIONAL_RULE"        # one organisation's own rule
DIRECTORY_CLASSIFICATION = "DIRECTORY_CLASSIFICATION"  # a database's own field value
INTERNATIONAL_INSTRUMENT = "INTERNATIONAL_INSTRUMENT"  # binds nobody in particular
STANDARD_ROLES = (LOCAL_LAW, LOCAL_CODE, FOREIGN_LEGAL_STANDARD, INSTITUTIONAL_RULE,
                  DIRECTORY_CLASSIFICATION, INTERNATIONAL_INSTRUMENT)

# ── the bound standards ───────────────────────────────────────────────────────
# Each entry: pattern -> (name, ISO-2 country, role when it IS local).
# Kept deliberately small. Add a standard when this publication's material actually hits
# it and it is genuinely the law of exactly one country -- not to be comprehensive.
BOUND_STANDARDS = (
    (r"\bADAAG\b", "ADAAG", "US", LOCAL_CODE),
    (r"\bADA\b|\bAmericans with Disabilities Act\b", "ADA", "US", LOCAL_LAW),
    (r"\bSection 508\b", "Section 508", "US", LOCAL_LAW),
    (r"\bFair Housing Act\b", "Fair Housing Act", "US", LOCAL_LAW),
    (r"\bInternational Building Code\b|\bIBC\b", "International Building Code", "US",
     LOCAL_CODE),
    (r"\bEquality Act 2010\b", "Equality Act 2010", "GB", LOCAL_LAW),
    (r"\bDisability Discrimination Act\b|\bDDA\b", "Disability Discrimination Act", "GB",
     LOCAL_LAW),
    (r"\bPart M\b", "Part M", "GB", LOCAL_CODE),
    (r"\bSection 117\b", "Section 117", "GB", LOCAL_LAW),
    (r"\bAODA\b|\bAccessibility for Ontarians with Disabilities Act\b", "AODA", "CA",
     LOCAL_LAW),
)

# NOT bound to any one country, and therefore never restricted by this module. Listed
# explicitly rather than left out, because "not in the table" and "deliberately not
# national" are different facts and a future reader will want to know which this is.
INTERNATIONAL_STANDARDS = (
    (r"\bWCAG\b|\bWeb Content Accessibility Guidelines\b", "WCAG"),
    (r"\bCRPD\b|\bConvention on the Rights of Persons with Disabilities\b", "CRPD"),
    (r"\bEN 301 ?549\b", "EN 301 549"),
    (r"\bISO \d{3,5}\b", "ISO standard"),
)

_BOUND_RES = tuple((re.compile(p, re.I), n, c, r) for p, n, c, r in BOUND_STANDARDS)
_INTL_RES = tuple((re.compile(p, re.I), n) for p, n in INTERNATIONAL_STANDARDS)

# ── country lexicon ───────────────────────────────────────────────────────────
# A LEXICON, not a gazetteer: it maps a name a source actually printed to an ISO-2 code.
# It answers "which country did this text NAME", never "where is this place". Only
# countries this publication's material realistically involves; unknown is fine.
COUNTRY_NAMES = {
    "US": (r"\bUnited States\b", r"\bU\.S\.A?\b", r"\bUSA\b", r"\bAmerican?\b"),
    "GB": (r"\bUnited Kingdom\b", r"\bBritain\b", r"\bBritish\b", r"\bEngland\b",
           r"\bScotland\b", r"\bWales\b", r"\bNorthern Ireland\b"),
    "IE": (r"\bIreland\b", r"\bIrish\b"),
    "EC": (r"\bEcuador\b", r"\bEcuadorian\b"),
    "NL": (r"\bNetherlands\b", r"\bDutch\b"),
    "DE": (r"\bGermany\b", r"\bGerman\b"),
    "FR": (r"\bFrance\b", r"\bFrench\b"),
    "ES": (r"\bSpain\b", r"\bSpanish\b"),
    "IT": (r"\bItaly\b", r"\bItalian\b"),
    "CA": (r"\bCanada\b", r"\bCanadian\b"),
    "AU": (r"\bAustralia\b", r"\bAustralian\b"),
    "JP": (r"\bJapan\b", r"\bJapanese\b"),
    "BR": (r"\bBrazil\b", r"\bBrazilian\b"),
    "PE": (r"\bPeru\b", r"\bPeruvian\b"),
    "CO": (r"\bColombia\b", r"\bColombian\b"),
    "MX": (r"\bMexico\b", r"\bMexican\b"),
    "IN": (r"\bIndia\b", r"\bIndian\b"),
    "CN": (r"\bChina\b", r"\bChinese\b"),
    "ZA": (r"\bSouth Africa\b", r"\bSouth African\b"),
    "NO": (r"\bNorway\b", r"\bNorwegian\b"),
    "SE": (r"\bSweden\b", r"\bSwedish\b"),
    "DK": (r"\bDenmark\b", r"\bDanish\b"),
    "CH": (r"\bSwitzerland\b", r"\bSwiss\b"),
    "AT": (r"\bAustria\b", r"\bAustrian\b"),
    "BE": (r"\bBelgium\b", r"\bBelgian\b"),
    "PT": (r"\bPortugal\b", r"\bPortuguese\b"),
    "NZ": (r"\bNew Zealand\b",),
    "KE": (r"\bKenya\b", r"\bKenyan\b"),
    "NG": (r"\bNigeria\b", r"\bNigerian\b"),
}
_COUNTRY_RES = {c: tuple(re.compile(p, re.I) for p in pats)
                for c, pats in COUNTRY_NAMES.items()}

# A country must be named more often than every other, by this margin, before it is
# called the subject's. Set to 2 because a foreign-source pack legitimately mentions the
# publisher's own country in passing -- measured on the live WildSumaco pack, where
# Ecuador leads 26 to 3 across six sources and every single source leads with it. A tie,
# or a one-mention lead, is honestly unknown.
COUNTRY_MARGIN = 2
MIN_COUNTRY_MENTIONS = 2


def country_mentions(text: str) -> dict:
    """{ISO-2: count} for every country NAMED in this text. Deterministic."""
    out = {}
    for code, pats in _COUNTRY_RES.items():
        n = sum(len(p.findall(text or "")) for p in pats)
        if n:
            out[code] = n
    return out


def subject_country(pack: dict) -> tuple:
    """(iso2 | None, evidence) read off the pack's frozen source texts.

    NEVER geocoded, never inferred from a domain, never asked of a model. A country is
    the subject's only if the sources NAME it and one name clearly dominates; anything
    else returns None, which is a real answer and switches this module off for the run.
    """
    counts = {}
    for s in (pack.get("sources") or []):
        for code, n in country_mentions(s.get("text") or "").items():
            counts[code] = counts.get(code, 0) + n
    if not counts:
        return None, {"counts": {}, "reason": "no country is named in the frozen sources"}
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    top, top_n = ranked[0]
    runner_n = ranked[1][1] if len(ranked) > 1 else 0
    if top_n < MIN_COUNTRY_MENTIONS or top_n - runner_n < COUNTRY_MARGIN:
        return None, {"counts": counts,
                      "reason": "no country is named clearly enough to be the subject's"}
    return top, {"counts": counts, "reason": "named in the frozen sources", "mentions": top_n}


def standards_in(text: str) -> list:
    """Every jurisdiction-bound or international standard NAMED in this text."""
    hits, seen = [], set()
    for rx, name, code, local_role in _BOUND_RES:
        if rx.search(text or "") and name not in seen:
            seen.add(name)
            hits.append({"standard": name, "jurisdiction": code,
                         "local_role": local_role, "bound": True})
    for rx, name in _INTL_RES:
        if rx.search(text or "") and name not in seen:
            seen.add(name)
            hits.append({"standard": name, "jurisdiction": None,
                         "local_role": INTERNATIONAL_INSTRUMENT, "bound": False})
    return hits


# Wording that shows the fact is ALREADY about a record rather than about the world.
# A proposition built this way needs no restriction: it already says whose claim it is.
_RECORD_VOICE = re.compile(
    r"(?i)\b(records?|recorded|entry|directory|listing|database|register|registry|"
    r"lists?|states?|says?|reports?|classif\w+|according to|profile|field)\b")


def classify_fact(fact: dict, country: str | None) -> dict | None:
    """What this fact's standard actually is, here. None when no standard is named.

    Returns {standard, standard_jurisdiction, standard_role, restrict, reason}.
    `restrict` is True only when a BOUND standard's country is known, the subject's
    country is known, and they differ.
    """
    text = "%s %s" % (fact.get("proposition") or "", fact.get("support_span") or "")
    hits = standards_in(text)
    if not hits:
        return None
    # A bound standard governs the verdict; an international one never restricts.
    hit = next((h for h in hits if h["bound"]), hits[0])
    if not hit["bound"]:
        return {"standard": hit["standard"], "standard_jurisdiction": None,
                "standard_role": INTERNATIONAL_INSTRUMENT, "restrict": False,
                "reason": "an international instrument is not one country's law"}
    if country is None:
        return {"standard": hit["standard"],
                "standard_jurisdiction": hit["jurisdiction"],
                "standard_role": hit["local_role"], "restrict": False,
                "reason": "the subject's country is not established in the frozen "
                          "evidence, so no relation between subject and standard can be "
                          "asserted either way"}
    if country == hit["jurisdiction"]:
        return {"standard": hit["standard"],
                "standard_jurisdiction": hit["jurisdiction"],
                "standard_role": hit["local_role"], "restrict": False,
                "reason": "the standard is the law where the subject is"}
    return {"standard": hit["standard"],
            "standard_jurisdiction": hit["jurisdiction"],
            "standard_role": FOREIGN_LEGAL_STANDARD, "restrict": True,
            "reason": "%s is %s law and the subject is in %s; this fact is evidence "
                      "about the record that states it, not about the subject"
                      % (hit["standard"], hit["jurisdiction"], country)}


def apply(ledger: dict, pack: dict) -> tuple:
    """Stamp and, where required, restrict. Returns (ledger, report).

    THE LEDGER IS NOT SHORTENED. A restricted fact keeps its id, its proposition, its
    span and its evidence; what changes is what it PERMITS. claim_type becomes
    ATTRIBUTION, which in this taxonomy licenses reporting that someone said a thing
    rather than asserting the thing -- exactly the permission a foreign directory's
    field actually carries. Deleting it would lose real evidence and, worse, would hide
    the restriction from every later stage and from the run record.
    """
    country, evidence = subject_country(pack)
    restricted, noted = [], []
    for fid, fact in sorted(ledger.items()):
        v = classify_fact(fact, country)
        if v is None:
            continue
        fact["standard"] = v["standard"]
        fact["standard_jurisdiction"] = v["standard_jurisdiction"]
        fact["standard_role"] = v["standard_role"]
        fact["jurisdiction_note"] = v["reason"]
        if v["restrict"]:
            fact["claim_type_before_jurisdiction"] = fact.get("claim_type")
            fact["claim_type"] = "ATTRIBUTION"
            restricted.append(fid)
        else:
            noted.append(fid)
    return ledger, {
        "subject_country": country,
        "country_evidence": evidence,
        "restricted": restricted,
        "noted": noted,
        "rule": "NO DEFAULT NATIONAL FRAMEWORK. A standard is evidence about the record "
                "that states it; it applies to the subject only where the evidence "
                "establishes that relation.",
    }


def subject_place(pack: dict) -> str:
    """A free-text place for the run record, taken verbatim from the pack's own subject
    line. Deliberately dumb: it is a label for a human reading the record, never an
    input to a decision. `subject_country` above is the only thing anything acts on."""
    return (pack.get("subject") or "").strip()[:200]
