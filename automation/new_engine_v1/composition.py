"""
composition.py -- the autonomous Story Architecture composition path.

WHY THIS EXISTS. PR #62 merged the Story Architecture's contracts, validators, packet
builder and rendering/continuity safety machinery, and proved on a held-out real subject
that the architecture can produce a strong article. What it did NOT merge was a pipeline
that RUNS those stages. The held-out proof was orchestrated by hand: a person built the
evidence freeze, performed the Worth gate, wrote the architecture, derived the CUT watch
terms, invoked the Writer and invoked Continuity. Every contract was real and every
validator was real; the caller was a human.

That is the production blocker this module removes. It automates exactly those six
missing stages and nothing else. It introduces no new architecture: every gate below is
a function merged in #62, called with the arguments its docstring already specifies.

WHAT IS DELIBERATELY NOT HERE
  No new validator, no Article Form Gate, no reader_now_wonders, no altitude model, no
  pivot-paragraph generation, no ending ontology. Where a stage's output is refused, the
  refusal is the merged validator's, quoted verbatim into the failure reason.

THE ONE RULE THE WHOLE MODULE SERVES
  The ledger is the only origin of factual permission (see ledger.py). Every stage after
  it SELECTS, ORDERS, CONNECTS, INTERPRETS and TIMES. None of them authors a fact. So the
  ledger is machine-checked against the frozen source bytes before anything downstream
  exists, and a fact whose support span is not in its own sources is REJECTED rather than
  passed to a later stage to be repaired.

REPAIR BUDGET, everywhere: at most ONE, and it may only narrow.
  A repair receives the exact validator failures and the same frozen evidence. It may
  drop, split or narrow. It may not broaden, and it may not touch a fact or field that
  already validated. If the second attempt still fails, the stage HOLDS. There is no
  retry loop anywhere in this file, and no stage regenerates a later stage's input to
  improve quality -- a HOLD is a real answer.

PROVIDER. Composition runs on the CLIProxy subscription path only; see
`composition_provider`. OpenRouter stays where it already is, behind the authoritative
external Fact Check.
"""
from __future__ import annotations

import json
import re
import time

from . import contracts as C
from . import continuity as CE
from . import ledger as LG
from . import stages as S
from . import story as ST
from .provider import Provider, ProviderError, parse_json_object

# ── stage names, in order ─────────────────────────────────────────────────────
LEDGER = "LEDGER"
WORTH = "WORTH"
ARCHITECTURE = "ARCHITECTURE"
CUT_TERMS = "CUT_TERMS"
WRITER = "WRITER"
CONTINUITY = "CONTINUITY"
SAFETY = "SAFETY"
GROUNDING = "GROUNDING"
FACT_CHECK = "FACT_CHECK"
READER = "READER"

STAGES = (LEDGER, WORTH, ARCHITECTURE, CUT_TERMS, WRITER, CONTINUITY, SAFETY,
          GROUNDING, FACT_CHECK, READER)

# ── the composition selector ──────────────────────────────────────────────────
# Deliberately NOT NEW_ENGINE_V1_MODE. That flag answers "may this engine run at all",
# and overloading it with "and which composition path" would make both meanings
# ambiguous -- a run could not then say what it had been asked to do. Two questions, two
# flags. Default stays legacy until a cutover is decided.
COMPOSITION_LEGACY = "legacy"
COMPOSITION_STORY_ARCHITECTURE = "story_architecture"
COMPOSITION_ENGINES = (COMPOSITION_LEGACY, COMPOSITION_STORY_ARCHITECTURE)
DEFAULT_COMPOSITION_ENGINE = COMPOSITION_LEGACY

COMPOSITION_ENGINE_ENV = "COMPOSITION_ENGINE"


class UnknownCompositionEngine(Exception):
    """An unrecognised value fails closed rather than falling back to a default: a run
    asked for an engine that does not exist has not been understood, and quietly writing
    the article with the other one is the worst available answer."""


def current_composition_engine(env: dict | None = None) -> str:
    import os
    raw = (env if env is not None else os.environ).get(COMPOSITION_ENGINE_ENV, "")
    val = (raw or "").strip().lower()
    if not val:
        return DEFAULT_COMPOSITION_ENGINE
    if val not in COMPOSITION_ENGINES:
        raise UnknownCompositionEngine(
            "%s=%r is not one of %s" % (COMPOSITION_ENGINE_ENV, raw,
                                        ", ".join(COMPOSITION_ENGINES)))
    return val


PASS = "PASS"
HOLD = "HOLD"
SKIPPED = "SKIPPED"
NOT_RUN = "NOT_RUN"

# Per-stage HOLD codes. One per stage, so a failure is answerable without reading prose.
LEDGER_HOLD = "LEDGER_HOLD"
WORTH_HOLD = "WORTH_HOLD"
ARCHITECTURE_HOLD = "ARCHITECTURE_HOLD"
CUT_TERMS_HOLD = "CUT_TERMS_HOLD"
WRITER_HOLD = "WRITER_HOLD"
CONTINUITY_HOLD = "CONTINUITY_HOLD"
SAFETY_HOLD = "SAFETY_HOLD"
GROUNDING_HOLD = "GROUNDING_HOLD"
FACT_CHECK_HOLD = "FACT_CHECK_HOLD"
READER_HOLD = "READER_HOLD"

# Text budget per source inside a composition prompt. The evidence freeze must see the
# source bytes it is quoting from, so this is far larger than stages.PACK_SOURCE_CHARS,
# which exists to keep a source from crowding out an anchor in a reading prompt.
#
# SET FROM A MEASURED FAILURE. The first Ground Truth canary to reach Worth was refused
# NO_PLAUSIBLE_LENS, and the cause was not judgement: the four facts carrying the lens
# sit at chars 12,438-13,163 of a 15,744-char anchor, and the pack handed the freeze the
# first 12,000. The stage cannot select what it was never shown, and a truncation that
# removes the last third of an essay removes exactly the part where a writer says what
# their measure cannot see.
FREEZE_SOURCE_CHARS = 24_000


# Below this there is not enough verified material to select a story from, and the
# honest failure is that rather than a complaint about one fact.
MIN_VERIFIED_FACTS = 4


class CompositionHold(Exception):
    """A stage refused. Carries the code and the validator's own reasons."""

    def __init__(self, stage: str, code: str, reasons: list, payload: dict | None = None):
        super().__init__("%s: %s" % (code, "; ".join(str(r) for r in reasons)[:400]))
        self.stage = stage
        self.code = code
        self.reasons = [str(r) for r in reasons]
        # What the stage had produced when it refused. A LEDGER_HOLD that discards the
        # ledger it built answers "it failed" and not "here is what it emitted", and the
        # second is the only one anybody can act on.
        self.payload = payload or {}


# ── PROVIDER: composition is a subscription-path workload ────────────────────
# ── PROVIDER: composition reuses the existing abstraction, unchanged ─────────
# THE CORRECTED PREMISE, recorded because the campaign brief carried the old one.
#
# The brief instructed composition to run on "the existing Claude / CLIProxy
# subscription path" and NOT on OpenRouter. That rested on CLIProxy fronting a Claude
# subscription. It does not -- not any more. Measured on the host, 2026-09-04:
#
#   every native claude-* route on CLIProxy   401 "OAuth access token has expired"
#   its refresh token                          401 "invalid_refresh_token"
#   OpenRouter, anthropic/claude-opus-4.8      200
#
# and the owner confirmed they no longer reach Claude through CLIProxy. So OpenRouter is
# not an alternative to the Claude path here; it IS the Claude path, which is exactly
# what provider.py's own docstring describes as production "silently falling back for
# days". Pinning composition to CLIProxy would not enforce a policy, it would just make
# composition the only stage that cannot reach a model.
#
# So: the existing Provider, unchanged, with its own CLIProxy-then-OpenRouter order --
# which is also what the brief asks for elsewhere, in as many words: reuse the existing
# provider abstraction, do not add a new provider framework. Every call still records
# `requested_model` and `actual_model` separately, so which leg actually served a stage
# stays visible in the run's provider identity rather than being assumed.
#
# COMPOSITION_MODEL overrides the model for composition only, and defaults to whatever
# the caller already chose, so this path introduces no second model policy.
COMPOSITION_MODEL_ENV = "COMPOSITION_MODEL"


def composition_model(default: str = "") -> str:
    import os
    return (os.environ.get(COMPOSITION_MODEL_ENV) or "").strip() or default


def composition_provider(provider):
    """The provider composition actually uses.

    Identical to the one handed in unless COMPOSITION_MODEL asks for a different model.
    A test double is passed through untouched.
    """
    want = composition_model(getattr(provider, "model", ""))
    if isinstance(provider, Provider) and want != provider.model:
        return Provider(model=want, cliproxy_url=provider.cliproxy_url)
    return provider


def _ask(provider, system: str, user: str, max_tokens: int, stage: str,
         code: str, temperature: float | None = None) -> tuple:
    """One model call returning one JSON object. Transport or shape failure is a HOLD.

    A malformed reply is retried ONCE and only mechanically -- same prompt, no feedback,
    no instruction to do better -- because an unparseable reply is a formatting accident
    and a second identical request is the cheapest way to find out. Anything that fails
    twice is a HOLD. Nothing here retries for quality.
    """
    last = None
    for attempt in (1, 2):
        try:
            comp = provider.complete(system=system, user=user, max_tokens=max_tokens,
                                     temperature=temperature)
        except ProviderError as e:
            raise CompositionHold(stage, code, ["provider unavailable: %s" % e])
        try:
            return parse_json_object(comp.text), _identity(comp, attempt)
        except ProviderError as e:
            last = e
    raise CompositionHold(stage, code,
                          ["reply was not one JSON object after two attempts: %s" % last])


def _identity(comp, attempts: int = 1) -> dict:
    ident = comp.identity() if hasattr(comp, "identity") else {}
    ident["attempts"] = attempts
    return ident


# ── SPAN VERIFICATION: the machine check the whole module rests on ───────────
# Normalization is narrow and already proven: whitespace, quote and dash shape, and the
# space markup leaves in front of punctuation. It can remove no word and reorder nothing,
# so a normalized match is still the source's own words in the source's own order.
_WS = re.compile(r"\s+")
_PUNCT_SPACE = re.compile(r"\s+([,.;:!?%])")
_ELLIPSIS = re.compile(r"\s*(?:\.\.\.|…)\s*")


def normalize_span(s: str) -> str:
    s = (s or "").replace("’", "'").replace("‘", "'") \
                 .replace("“", '"').replace("”", '"') \
                 .replace("—", "-").replace("–", "-") \
                 .replace(" ", " ")
    return _PUNCT_SPACE.sub(r"\1", _WS.sub(" ", s)).strip().lower()


def span_in(span: str, haystack: str) -> bool:
    """Is `span` verbatim in `haystack`, subject only to the normalization above?

    An explicit ellipsis segments the span: every segment must appear, IN ORDER, each one
    after the last. That is strictly stronger than searching for the segments anywhere,
    and it is the only way a quotation with an elision can be checked at all. An implicit
    elision -- words dropped with no ellipsis -- is not a quotation and does not match.
    """
    hay = normalize_span(haystack)
    parts = [p for p in _ELLIPSIS.split(span or "") if p.strip()]
    if not parts:
        return False
    at = 0
    for p in parts:
        i = hay.find(normalize_span(p), at)
        if i < 0:
            return False
        at = i + len(normalize_span(p))
    return True


def source_texts(pack: dict) -> dict:
    """source_id -> fetched text, from the frozen RESEARCH_PACK."""
    return {s["source_id"]: s.get("text") or "" for s in (pack.get("sources") or [])}


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 1 -- EVIDENCE FREEZE / LEDGER
# ══════════════════════════════════════════════════════════════════════════════
# The model SELECTS and ATOMIZES. It does not invent support. Everything it emits is
# checked against the frozen bytes of the source it names, and a fact whose span is not
# there is rejected -- never handed downstream for the Writer to "handle".
FREEZE_SYSTEM = (
    "You are freezing an evidence ledger. This is the only stage that may create a "
    "factual permission; every later stage may only select from what you emit here, so a "
    "fact you get wrong cannot be corrected later, and a fact you omit cannot be used.\n"
    "Read the sources and break what they establish into ATOMIC facts: one fact asserts "
    "one thing. If a sentence in a source carries a date AND a name AND a mechanism, that "
    "is three facts, not one.\n"
    "For each fact quote a support_span: a VERBATIM run of characters from ONE of the "
    "sources you cite. It is checked mechanically against the source bytes. Do not "
    "paraphrase it, do not tidy it, do not join two distant sentences into one span. If "
    "you must elide, write ... between the kept parts and both parts must be verbatim and "
    "in the source's own order.\n"
    "Your proposition may be worded in your own words, but it may not assert anything the "
    "span does not carry. Do not append a person, a date, an institution or a relation "
    "that the span itself does not state -- that is the single most common way this stage "
    "fails. If the span carries a mechanism but not the year, the proposition has no year "
    "in it.\n"
    "NEGATIVES ARE THE STAGE'S COMMONEST FAILURE, so read this twice. A claim that "
    "something does not exist, was never built, is not mentioned, is the only one, or is "
    "the first, is checked against the WORDS OF YOUR OWN SPAN: the span must itself say "
    "no, not, never, none, without, nothing, lacks, absent, or has yet to. Noticing that "
    "the sources never mention a thing is NOT evidence, and a span that merely fails to "
    "mention it will be rejected. Silence is not evidence of absence.\n"
    "  You have two honest options and one wrong one. If a source states the negative, "
    "quote that sentence and use scope WORLD. If you counted a bounded set yourself, use "
    "scope AUDITED_CORPUS, give corpus_size, and word the proposition as a claim about "
    "THAT SET -- \"none of the eight entries describes...\" -- not about the world. If "
    "neither is true, DO NOT EMIT THE FACT. Leaving it out costs the article a detail; "
    "asserting it costs the article its grounding.\n"
    "  NOW THE OTHER HALF OF THAT RULE, which matters just as much. When a source DOES "
    "state a negative in its own words -- \"it does not measure overcrowding, housing "
    "quality or eviction risk\", \"shows these as no reading rather than as zero\", "
    "\"people with no housing at all, absent by construction from a survey of "
    "households\" -- that is not something to avoid. It is evidence, it is quotable, and "
    "it is frequently the most valuable material in the whole source, because what a "
    "measure or a record CANNOT hold is usually the thing nobody else has written down. "
    "CAPTURE IT. Quote the source's own negative sentence as the span, give the fact its "
    "negative claim_type, and leave the scope WORLD -- the span's own words are what "
    "licenses it. Do not skip a passage of what something does not do, does not cover or "
    "cannot see because it looks like a negative claim: a stated negative is a fact, and "
    "only an UNstated one is a fabrication.\n"
    "Include the unglamorous facts and the ones that cut against the obvious story. "
    "Selection happens later and cannot select what you did not freeze."
)

FREEZE_SCHEMA = (
    "Reply with ONE JSON object:\n"
    '{"facts": [{\n'
    '  "fact_id": "F01",                       sequential, F01, F02, ... , no gaps\n'
    '  "proposition": "...",                   one assertion, plain words, no citation\n'
    '  "claim_type": "POSITIVE_FACT",          one of: %s\n'
    '  "claim_kind": "OCCURRENCE",             OCCURRENCE = a documented happening, or a\n'
    "                                          documented particular action, decision or\n"
    "                                          measurement. DISPOSITION = a rule, a\n"
    "                                          conditional, a property, or an attributed\n"
    "                                          statement. Every attribution is a\n"
    "                                          DISPOSITION: it licenses reporting that\n"
    "                                          someone said a thing, not asserting that\n"
    "                                          the thing happened.\n"
    '  "evidence_ids": ["S0"],                 the source ids the span is FROM\n'
    '  "support_span": "...",                  VERBATIM from one cited source\n'
    '  "entities": ["..."],                    named people, places, organisations\n'
    '  "scope": "WORLD"                        negatives only: WORLD needs explicit\n'
    "                                          negative evidence; AUDITED_CORPUS is a\n"
    "                                          claim about a set you enumerated, and then\n"
    '                                          also give "corpus_size": <int>\n'
    "}]}\n"
    "No prose outside the JSON." % ", ".join(LG.CLAIM_TYPES)
)


def truncated_sources(pack: dict, per_source_chars: int = FREEZE_SOURCE_CHARS) -> list:
    """Which sources the freeze will not see the whole of.

    Reported, never silent. A source cut short does not fail anything -- it just makes a
    class of fact invisible, and an invisible fact class looks exactly like a subject
    that had no such material in it. That is the failure this function exists to name.
    """
    out = []
    for s in (pack.get("sources") or []):
        n = len(s.get("text") or "")
        if n > per_source_chars:
            out.append({"source_id": s.get("source_id"), "chars": n,
                        "shown": per_source_chars, "lost": n - per_source_chars})
    return out


def freeze_prompt(pack: dict, subject: str, per_source_chars: int = FREEZE_SOURCE_CHARS) -> str:
    L = ["SUBJECT", "  " + (subject or "").strip(), "", "SOURCES"]
    for s in (pack.get("sources") or []):
        text = (s.get("text") or "")[:per_source_chars]
        L += ["", "%s  role=%s  url=%s" % (s["source_id"], s.get("role", ""),
                                           s.get("url", "")),
              "<<<%s" % s["source_id"], text, "%s>>>" % s["source_id"]]
    L += ["", FREEZE_SCHEMA]
    return "\n".join(L)


def _as_ledger(facts) -> dict:
    """The model emits a list; the ledger is keyed by fact_id. Shape errors are refused
    here rather than producing a ledger with a None key."""
    if not isinstance(facts, list) or not facts:
        raise CompositionHold(LEDGER, LEDGER_HOLD,
                              ["the reply carries no 'facts' list"])
    out = {}
    for i, f in enumerate(facts, 1):
        if not isinstance(f, dict):
            raise CompositionHold(LEDGER, LEDGER_HOLD,
                                  ["fact %d is %s, not an object" % (i, type(f).__name__)])
        fid = str(f.get("fact_id") or "").strip()
        if not fid:
            raise CompositionHold(LEDGER, LEDGER_HOLD, ["fact %d has no fact_id" % i])
        if fid in out:
            raise CompositionHold(LEDGER, LEDGER_HOLD, ["duplicate fact_id %r" % fid])
        f["fact_id"] = fid
        out[fid] = f
    return out


def check_ledger(ledger: dict, srcs: dict) -> dict:
    """Every check that can refuse a fact, in one place, per fact id.

    Returns {fact_id: [failures]} for the facts that are not usable. Three layers:
      1. the merged ledger contract (taxonomy, negative-scope rule, span present)
      2. SPAN BINDING -- the span must be in a source THIS FACT CITES, not merely
         somewhere in the corpus. A span quoted from S1 and attributed to S0 is a
         provenance error, and the merged validator's single-blob evidence_text cannot
         see it.
      3. the merged proposition/support-span audit. The F10 lesson: a proposition may not
         silently append a year or a titled person its span does not carry. Deterministic
         only -- this is not a general entailment gate.
    """
    failures: dict[str, list] = {}

    def add(fid, msg):
        failures.setdefault(fid, []).append(msg)

    # 1. the merged contract, against the whole authorised corpus
    corpus = "\n".join(srcs.values())
    for err in LG.validate_ledger(ledger, corpus):
        fid = str(err).split(":", 1)[0].strip()
        add(fid if fid in ledger else "<ledger>", err)

    for fid, f in sorted(ledger.items()):
        if not re.match(r"^F\d{2,}$", fid):
            add(fid, "%s: fact_id must look like F01" % fid)
        kind = f.get("claim_kind")
        if kind not in ST.CLAIM_KINDS:
            add(fid, "%s: claim_kind %r is not one of %s"
                % (fid, kind, ", ".join(ST.CLAIM_KINDS)))

        # 2. span binding to the cited sources
        if f.get("claim_type") == LG.INTERPRETATION:
            continue
        cited = [e for e in (f.get("evidence_ids") or [])]
        unknown = [e for e in cited if e not in srcs]
        if unknown:
            add(fid, "%s: cites source ids that are not in the pack: %s" % (fid, unknown))
        span = f.get("support_span") or ""
        known = [e for e in cited if e in srcs]
        if span and known and not any(span_in(span, srcs[e]) for e in known):
            found_in = [sid for sid, t in srcs.items() if span_in(span, t)]
            add(fid, "%s: support_span is not verbatim in any cited source (%s)%s"
                % (fid, ", ".join(known),
                   "; it is in %s, so the attribution is wrong" % ", ".join(found_in)
                   if found_in else ""))

    # 3. the proposition/span audit
    for finding in ST.proposition_span_audit(ledger)["findings"]:
        fid = finding["fact_id"]
        for ex in finding["exceeds"]:
            add(fid, "%s: the proposition asserts a %s (%r) that its own support_span "
                     "does not carry" % (fid, ex["kind"], ex["value"]))
    return failures


REPAIR_LEDGER_SYSTEM = (
    "You are repairing rejected facts in an evidence ledger. The validator's exact "
    "failures are given. The evidence is unchanged and is the same evidence you had.\n"
    "For each rejected fact you may do exactly one of:\n"
    "  DROP    -- omit it. Always available, and often correct.\n"
    "  SPLIT   -- replace it with two or more narrower facts, each with its own verbatim\n"
    "             span. Number them after the highest existing id.\n"
    "  NARROW  -- keep it but remove what its span does not carry, or requote the span\n"
    "             verbatim from the source it actually came from.\n"
    "A REJECTED NEGATIVE IS ALMOST ALWAYS A DROP. If the failure says a WORLD negative "
    "needs evidence that states the negative, then no rewording will save it: either "
    "quote a span that actually contains the negative, or re-scope it to AUDITED_CORPUS "
    "with a corpus_size and word it as a claim about that set, or DROP IT. Emitting the "
    "same claim again in different words will simply be rejected again.\n"
    "You may NOT broaden a fact, add a claim, or restate a rejected fact in wording that "
    "asserts the same unsupported thing. If the evidence does not carry it, DROP it: an "
    "omitted fact costs the article a detail, and a wrong one costs it its grounding.\n"
    "Return ONLY the replacement facts for the rejected ids. The facts that validated are "
    "already frozen and are not yours to edit."
)


def freeze_ledger(provider, pack: dict, subject: str) -> dict:
    """STAGE 1. Frozen research material in, machine-checked ledger out."""
    srcs = source_texts(pack)
    if not srcs:
        raise CompositionHold(LEDGER, LEDGER_HOLD, ["the research pack has no sources"])
    system, user = FREEZE_SYSTEM, freeze_prompt(pack, subject)
    obj, ident = _ask(provider, system, user, 12_000, LEDGER, LEDGER_HOLD)
    ledger = _as_ledger(obj.get("facts"))
    failures = check_ledger(ledger, srcs)
    calls, repairs = 1, 0

    if failures:
        # ONE repair, and it may only narrow. Facts that already validated are removed
        # from the model's reach entirely, so a repair cannot quietly rewrite them.
        rejected = sorted(failures)
        kept = {fid: f for fid, f in ledger.items() if fid not in failures}
        ru = ["THE EVIDENCE (unchanged)", freeze_prompt(pack, subject), "",
              "REJECTED FACTS AND THE EXACT VALIDATOR FAILURES"]
        for fid in rejected:
            if fid in ledger:
                ru.append("")
                ru.append("%s  proposition: %s" % (fid, ledger[fid].get("proposition")))
                ru.append("    span quoted: %r" % (ledger[fid].get("support_span") or "")[:300])
                ru.append("    cited: %s" % (ledger[fid].get("evidence_ids") or []))
            for msg in failures[fid]:
                ru.append("    FAILED: %s" % msg)
        ru += ["", "Highest existing fact id: %s" % (max(ledger) if ledger else "F00"),
               "", FREEZE_SCHEMA]
        obj2, ident2 = _ask(provider, REPAIR_LEDGER_SYSTEM, "\n".join(ru), 8_000,
                            LEDGER, LEDGER_HOLD)
        calls += 1
        repairs = 1
        ident = {"freeze": ident, "repair": ident2}
        replacements = _as_ledger(obj2.get("facts")) if obj2.get("facts") else {}
        touched = [fid for fid in replacements if fid in kept]
        if touched:
            raise CompositionHold(
                LEDGER, LEDGER_HOLD,
                ["the repair rewrote facts that had already validated: %s -- a repair "
                 "may only replace rejected facts" % sorted(touched)])
        ledger = dict(kept)
        ledger.update(replacements)
        failures = check_ledger(ledger, srcs)

    # A fact that is still unsupportable after its one repair is REJECTED. That is the
    # campaign's own rule for a fact whose support cannot be verified -- reject the FACT
    # -- and it is the safe direction: nothing invalid reaches any later stage either
    # way, and the alternative is that one stubborn fact out of sixty destroys an
    # article whose other fifty-nine are verified.
    #
    # This is not a relaxed gate. No rejected fact is available to the architect, so it
    # cannot be selected, cannot carry a beat and cannot license a turn. What changes is
    # only whether the RUN dies with it. The rejections are recorded on the result, and
    # the stage still HOLDS when too little verified material survives -- which is the
    # honest failure: "there is not enough here to write from", not "fact 61 was wrong".
    rejected = {}
    if failures:
        rejected = {fid: msgs for fid, msgs in failures.items() if fid in ledger}
        for fid in rejected:
            ledger.pop(fid, None)
        orphaned = sorted(failures.keys() - set(rejected))
        if orphaned:
            raise CompositionHold(
                LEDGER, LEDGER_HOLD,
                ["the ledger is invalid in a way no single fact owns: %s" % orphaned]
                + ["%s" % "; ".join(failures[o]) for o in orphaned][:4],
                {"ledger": ledger, "rejected": rejected})
        still = check_ledger(ledger, srcs)
        if still:
            raise CompositionHold(
                LEDGER, LEDGER_HOLD,
                ["rejecting the invalid facts did not leave a valid ledger"]
                + ["%s: %s" % (f, "; ".join(m)) for f, m in sorted(still.items())][:6],
                {"ledger": ledger, "rejected": rejected})

    if len(ledger) < MIN_VERIFIED_FACTS:
        raise CompositionHold(
            LEDGER, LEDGER_HOLD,
            ["only %d fact(s) survived the freeze; there is not enough verified material "
             "to select a story from" % len(ledger)]
            + (["rejected as unsupportable: %s" % sorted(rejected)] if rejected else []),
            {"ledger": ledger, "rejected": rejected})

    kinds = {}
    for f in ledger.values():
        kinds[f.get("claim_kind")] = kinds.get(f.get("claim_kind"), 0) + 1
    return {"status": PASS, "ledger": ledger, "provider": ident,
            "model_calls": calls, "repairs": repairs,
            "sources_truncated": truncated_sources(pack),
            "facts": len(ledger), "claim_kinds": kinds,
            "rejected": rejected,
            "rejected_count": len(rejected),
            "span_verified": True,
            "sources": sorted(srcs),
            "freeze_rule": "After this freeze no stage may mint a fact. No possibility "
                           "to fact, no association to causation, no description to "
                           "experience, no design intent to actual effect, no absence in "
                           "sources to absence in world."}


def ledger_block(ledger: dict, include_spans: bool = False) -> str:
    """The ledger as the later stages see it: ids and propositions.

    Spans are withheld by default. A selection stage's job is to choose among
    permissions, and handing it the source wording invites it to quote around the
    permission rather than from it.
    """
    L = []
    for fid, f in sorted(ledger.items()):
        L.append("%s  [%s / %s]  %s" % (fid, f.get("claim_type"), f.get("claim_kind"),
                                        f.get("proposition")))
        if include_spans:
            L.append("      span: %r" % (f.get("support_span") or "")[:200])
    return "\n".join(L)


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 2 -- WORTH GATE
# ══════════════════════════════════════════════════════════════════════════════
# Runs before the expensive stages, and a refusal is a first-class outcome. The gate
# answers one question: is there a reading that changes what this story MEANS, or is
# there only a vocabulary being attached to it? A HOLD here is cheap and correct.
WORTH_SYSTEM = (
    "You are deciding whether a story belongs in this publication, and separately whether "
    "there is a story at all. Two judgements, kept apart.\n"
    "\n"
    "1. THE LENS. Crip Minds reads the world through disability as a way of knowing, not "
    "as a subject to cover. A publishable lens NAMES A MECHANISM and changes what the "
    "story means -- after reading it, the reader understands the same facts differently. "
    "Verdicts:\n"
    "  STRONG_DIRECT_LENS       disability is materially in the story itself\n"
    "  STRONG_INTERPRETIVE_LENS a disability reading reveals a mechanism the story has\n"
    "                           but does not know it has\n"
    "\n"
    "READ THIS BEFORE YOU DECIDE, because the commonest error here is a category one. "
    "STRONG_INTERPRETIVE_LENS does NOT require the material to mention disability, "
    "impairment, access or bodies. If the material mentioned them the verdict would be "
    "STRONG_DIRECT_LENS. So refusing an interpretive reading BECAUSE the ledger never "
    "names disability is not applying the standard, it is deleting the verdict: the whole "
    "category exists for subjects that never say the word.\n"
    "  What an interpretive reading asks is what a system, record, measure, instrument, "
    "form, institution or piece of infrastructure can and cannot register about a body or "
    "a life -- what it has a field for, what it turns into a number, what it drops, and "
    "who it cannot see at all. Any material that classifies people, or that converts a "
    "classification into something a body then has to live with, is a candidate. So is "
    "material that states its own limits: a measure that says what it does not capture, a "
    "record that has no field for something, a survey whose subject is absent from it by "
    "construction. That is the publication's central mode, not an edge case.\n"
    "  The bar is still real, and it is a MECHANISM. The reading has to name how the "
    "thing works and change what the story means, and it has to be carried by facts in "
    "the ledger rather than by your own sympathy for the subject. A resemblance is not a "
    "mechanism, and neither is the observation that something is hard or unfair.\n"
    "  WEAK_ANALOGY             the connection is a resemblance, not a mechanism\n"
    "  NO_PLAUSIBLE_LENS        there is no such reading here\n"
    "  GREAT_GENERAL_STORY_WRONG_PUBLICATION  a real story, for somewhere else\n"
    "REFUSE RATHER THAN REACH. A forced lens is the failure this gate exists to catch, "
    "and the last three verdicts are correct answers that cost nothing. Do not write that "
    "something 'faces barriers', 'reminds us that', 'is a metaphor for' disability, or "
    "that 'we are all' anything -- those are vocabulary, not mechanism.\n"
    "\n"
    "2. THE STORY. A story has a concrete carrier a reader can hold onto -- a person, an "
    "object, an event, a place or a process -- something that HAPPENS or CHANGES, and a "
    "tension. An idea is not a story. Chronology is not causation: only mark a causal link "
    "SUPPORTED_CAUSAL when a fact actually asserts the mechanism, otherwise it is "
    "CHRONOLOGICAL_ADJACENCY or CONTESTED.\n"
    "\n"
    "Cite fact ids for everything. You may not use a fact id that is not in the ledger."
)

WORTH_SCHEMA = (
    "Reply with ONE JSON object:\n"
    '{"worth_gate": {"verdict": "...", "lens_claim": "one or two sentences naming the\n'
    '                 mechanism", "changes_meaning_how": "what a reader understands\n'
    '                 differently", "evidence_ids": ["F.."]},\n'
    ' "story_candidate": {"story_id": "kebab-slug", "carrier_type": "object",\n'
    '                 "opening_possibility": "the concrete thing to open on",\n'
    '                 "real_event_or_change": "what happens or changes",\n'
    '                 "tension": "...", "reader_first_sees": "...",\n'
    '                 "reader_later_discovers": "...",\n'
    '                 "causal_chain": [{"kind": "SUPPORTED_CAUSAL", "link": "...",\n'
    '                                  "evidence_ids": ["F.."]}],\n'
    '                 "evidence_ids": ["F.."]}}\n'
    "carrier_type is one of: %s\n"
    "If the verdict is WEAK_ANALOGY, NO_PLAUSIBLE_LENS or "
    "GREAT_GENERAL_STORY_WRONG_PUBLICATION, give the verdict and a one-sentence "
    "lens_claim saying what you considered and why it does not hold, and omit "
    "story_candidate. A refusal needs no further proof.\n"
    "No prose outside the JSON." % ", ".join(ST.CARRIERS)
)


def worth_gate(provider, ledger: dict, subject: str) -> dict:
    """STAGE 2. A HOLD here stops the article before any expensive composition."""
    user = "\n".join(["SUBJECT", "  " + (subject or "").strip(), "",
                      "THE FROZEN LEDGER -- the only facts that exist",
                      ledger_block(ledger), "", WORTH_SCHEMA])
    obj, ident = _ask(provider, WORTH_SYSTEM, user, 4_000, WORTH, WORTH_HOLD)
    lens = obj.get("worth_gate") or {}
    verdict = lens.get("verdict")

    errs = ST.validate_lens(lens)
    if errs:
        raise CompositionHold(WORTH, WORTH_HOLD,
                              ["the worth gate's own output is invalid"] + errs)
    if verdict not in ST.LENS_PUBLISHABLE:
        # Not an engine failure. The gate did its job and the answer is no.
        raise CompositionHold(
            WORTH, WORTH_HOLD,
            ["verdict %s -- this subject is not publishable here" % verdict,
             (lens.get("lens_claim") or "")[:300]])

    cand = obj.get("story_candidate") or {}
    errs = ST.validate_candidate(cand)
    unknown = sorted(set(cand.get("evidence_ids") or []) - set(ledger))
    if unknown:
        errs.append("story_candidate cites fact ids not in the ledger: %s" % unknown)
    unknown_lens = sorted(set(lens.get("evidence_ids") or []) - set(ledger))
    if unknown_lens:
        errs.append("the lens cites fact ids not in the ledger: %s" % unknown_lens)
    if errs:
        raise CompositionHold(WORTH, WORTH_HOLD,
                              ["there is a lens but not a story"] + errs)

    yld = ST.narrative_yield(cand)
    return {"status": PASS, "worth_gate": lens, "story_candidate": cand,
            "narrative_yield": yld, "verdict": verdict,
            "provider": ident, "model_calls": 1, "repairs": 0}


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 3 -- STORY ARCHITECT
# ══════════════════════════════════════════════════════════════════════════════
# The architect SELECTS from the ledger and decides the order in which the reader
# discovers it. It may not mint a proposition, and its own prose fields are audited for
# exactly that -- the "pink" incident got a colour into the packet through the architect's
# `turn` field, and the packet is built FROM the architecture, so the post-writer audit
# then certified the fabrication as approved.
ARCHITECT_SYSTEM = (
    "You are building the reader's path through a story whose facts are already frozen. "
    "You SELECT, ORDER, CONNECT and TIME. You never author a fact.\n"
    "\n"
    "SELECT. Decide which facts are USED and which are CUT, and give every cut a reason "
    "from the declared set. Selection that discards nothing is not selection: a real "
    "architecture cuts the redundant second proof, the background nobody needs, the "
    "second example making the same point. Every fact is either used or cut, never both.\n"
    "\n"
    "ORDER. Beats, in reading order. Each beat carries ONE concrete carrier -- a NOUN "
    "PHRASE naming the thing the reader holds onto, with no verb clause in it. A carrier "
    "that contains a clause is asserting that something HAPPENED, and that needs a fact "
    "whose claim_kind is OCCURRENCE behind it. Where the ledger holds only a rule (a "
    "DISPOSITION -- what the thing does under a condition), you may say what the thing "
    "does; you may not narrate an instance of it happening.\n"
    "\n"
    "TIME. Each beat says what the reader must NOT be told yet, and why they will want the "
    "next one.\n"
    "\n"
    "THE TURN. The crip turn re-reads something the reader has ALREADY BEEN SHOWN and "
    "names which beat it re-reads. Every relation it asserts -- a cause, an equivalence, a "
    "comparison, a superlative, a generalisation, an absence -- must be a relation a "
    "licensing fact already asserts. Two true facts do not license a relation between "
    "them. An unpublished figure is not a small one, and an absent reading is not a low "
    "one.\n"
    "\n"
    "WRITE MEANING, NOT PERFORMANCE. Your prose fields are read by the Writer as "
    "instructions and get copied. So state what is true and what it means; do not write "
    "the rhetoric. No 'Go back to the sand.', no 'Read that list again.', no sentence "
    "whose job is to tell the reader what the article is doing. The Writer places the "
    "paragraphs and finds the sentences.\n"
    "\n"
    "PROHIBITIONS are instructions to the Writer and must be phrased as imperatives -- "
    "'Do not ...', 'Never ...'. Never phrase one as a description of what the evidence "
    "lacks: 'the source does not establish X' is the exact sentence shape the Writer turns "
    "into a caveat, which is the defect this whole architecture exists to remove. Write "
    "one prohibition for every way this particular story could be embellished: an invented "
    "witness or visitor, a feeling attributed to someone unreported, a motive beyond a "
    "stated aim, a claim that something was never done, a colour or size nobody recorded."
)

ARCHITECT_SCHEMA = (
    "Reply with ONE JSON object:\n"
    '{"article_type": "NARRATIVE_ARTICLE",       one of: %(types)s\n'
    ' "story_spine": "ONE sentence: what happens",\n'
    ' "opening_object_or_event": "the concrete thing the article opens on",\n'
    ' "reader_initial_state": "the only thing the reader should understand first",\n'
    ' "lens_realization": "IMPLICIT",            IMPLICIT, EXPLICIT or EITHER\n'
    ' "crip_turn_rereads": "B5",                 the beat_id the turn re-reads\n'
    ' "turn": "",                                the story turn, if distinct; may be ""\n'
    ' "crip_turn": "what the reader should understand differently by the end",\n'
    ' "ending_move": "what the last movement lands on",\n'
    ' "beats": [{"beat_id": "B1", "happens": "...",\n'
    '            "concrete_carrier": "a noun phrase, no verb clause",\n'
    '            "facts_allowed": ["F.."], "concept_introduced": "",\n'
    '            "why_reader_wants_next": "...", "must_not_say_yet": "..."}],\n'
    ' "use_facts": ["F.."],                      every fact used in any beat\n'
    ' "use_quotes": [],\n'
    ' "definitions": {"term": "plain-words gloss, explained at first use"},\n'
    ' "cut_evidence": [{"evidence_id": "F..", "reason": "REDUNDANT_PROOF"}],\n'
    "                                            reasons: %(cuts)s\n"
    ' "prohibitions": ["Do not ..."],\n'
    ' "final_lens": {"lens_claim": "...", "evidence_basis": ["F.."],\n'
    '                "what_changes_for_the_reader": "what the reader now UNDERSTANDS,\n'
    "                 READS, MEANS or SEES differently -- use one of those words\",\n"
    '                "story_beat_before": "B4",   the beat the turn re-reads\n'
    '                "crip_turn": "the turn itself, naming something from that beat",\n'
    '                "story_beat_after": "B6",    a LATER beat than story_beat_before\n'
    '                "before_reading": "what the reader thought the story was",\n'
    '                "after_reading": "what it is",\n'
    '                "crip_turn_carrier": "the concrete thing the turn lands on -- a\n'
    "                 noun phrase that appears in the story_beat_before beat\"}}\n"
    "No prose outside the JSON."
    % {"types": ", ".join(ST.ARTICLE_TYPES), "cuts": ", ".join(ST.CUT_REASONS)}
)


def _sentence_initial(word: str, arch: dict) -> bool:
    """Does `word` only ever appear as the first word of a sentence in the architecture?

    `_entities` skips sentence-initial capitals when it reads an article, because a
    capital there carries no information. It cannot do that across the architecture's
    separate short fields, which is why the manual baseline's crip turn -- "Near the
    complexes..." -- reports "Near" as an unapproved entity. Checked, not assumed: a name
    that also appears mid-sentence is still reported.
    """
    fields = [str(arch.get(k) or "") for k in
              ("story_spine", "opening_object_or_event", "reader_initial_state",
               "turn", "crip_turn", "ending_move")]
    for b in (arch.get("beats") or []):
        fields += [str(b.get(k) or "") for k in
                   ("happens", "concrete_carrier", "concept_introduced")]
    for f in fields:
        for sent in re.split(r"(?<=[.!?])\s+", f.strip()):
            sent = sent.strip()
            if not sent:
                continue
            body = re.split(r"\s+", sent, maxsplit=1)
            if len(body) > 1 and re.search(r"\b%s\b" % re.escape(word), body[1]):
                return False
    return True


def check_architecture(arch: dict, ledger: dict) -> list:
    """Every merged pre-Writer gate, called in one place.

    This runs BEFORE the packet is built, which is the whole point: a Writer handed an
    unlicensed turn writes it, and a packet built from a minting architecture launders the
    invention into "approved" material.
    """
    errs = []
    errs += ["MINTED_FACT: " + e for e in LG.architect_may_not_mint(arch, ledger)]
    # Shape, USE/CUT honesty, carrier-occurrence support and turn-relation support.
    errs += ST.validate_architecture(arch, set(ledger), ledger)
    fl = arch.get("final_lens") or {}
    errs += ["FINAL_LENS: " + e for e in ST.validate_final_lens(fl, arch, ledger)]
    errs += ["LENS_EMBODIMENT: " + e for e in ST.validate_lens_embodiment(arch, fl)]
    errs += ["LENS_REALIZATION: " + e for e in ST.validate_lens_realization(arch, fl)]
    # The architect must be semantic, not rhetorical: its fields are transcribed.
    errs += ["ARCHITECT_RHETORIC: " + e for e in CE.validate_architect_is_semantic(arch)]
    # NUMBERS and NAMED ENTITIES the architect's own prose fields assert and no approved
    # proposition carries. This is the "pink" channel: the packet is built FROM the
    # architecture, so an attribute invented here is legitimised before the post-writer
    # audit ever compares prose to packet.
    #
    # Only two of the audit's five channels are read as failures, and that is a measured
    # decision rather than a softening. Run against the manual baseline architecture --
    # the one that produced the article this campaign is reproducing -- the audit returns
    # hard_ok False on `unapproved_entities: ['Near']`, a sentence-initial word, and
    # `unapproved_spatial: ['lower']`, which is the ledger's own wording for F14/F15. Both
    # are false positives on architect fields, and blocking on them would refuse the
    # proven architecture and spend the single repair getting back to it. The three noisy
    # channels are carried as telemetry, where the module's own docstring already puts
    # them: candidates for review, not verdicts.
    audit = ST.architect_prose_audit(arch, LG.propositions(ledger))
    for channel in ("unapproved_numbers", "unapproved_entities"):
        vals = [v for v in (audit.get(channel) or [])
                if not _sentence_initial(v, arch)]
        if vals:
            errs.append("ARCHITECT_PROSE: the architecture's own prose asserts %s no "
                        "approved fact carries: %s" % (channel[11:], vals[:6]))
    # Optional semantic-ownership representation. The held-out baseline did not carry it,
    # so it is validated where present and never required -- requiring it would be a new
    # architecture feature, which this campaign is explicitly not adding.
    props = arch.get("propositions")
    if isinstance(props, list) and props:
        errs += ["PROPOSITIONS: " + e for e in ST.validate_propositions(props)]
        errs += ["ENDING_RESTATES: " + e
                 for e in ST.validate_ending_does_not_restate(arch, props)]
    return errs


REPAIR_ARCH_SYSTEM = (
    "You are repairing a story architecture that failed validation. The exact failures "
    "are given, and the ledger is unchanged.\n"
    "You may NARROW, REORDER or REMOVE. You may not add a fact, and you may not reach for "
    "a fact id that is not in the ledger.\n"
    "Most of these failures are one of three things, and the fix is the same each time: "
    "something asserted more than the evidence carries. A carrier that narrates an event "
    "becomes a plain noun phrase. A turn that fuses two true facts into a relation loses "
    "the relation and keeps the facts. A lens that reaches past its evidence gets smaller "
    "and truer. Narrower and true beats wider and refused.\n"
    "\n"
    "CARRIER_INSTANCE_NOT_SUPPORTED is the commonest one, and the check for it is "
    "GRAMMATICAL, not a judgement about meaning. It reads the carrier for a verb. So a "
    "carrier must be a bare noun phrase containing NO VERB OF ANY KIND: no finite verb, "
    "no relative clause, no participle. Adjectives, prepositions and possessives are "
    "fine.\n"
    "  Not this  : the block group where no figure is published\n"
    "  Not this  : the state that shows no reading\n"
    "  Not this  : the servo pulling the brake arm\n"
    "  This      : the block group with no published figure\n"
    "  This      : the blank cell on the score card\n"
    "  This      : the brake arm\n"
    "Cut the clause and keep the THING. Whatever the clause was saying either belongs in "
    "the beat's `happens` field, where a disposition may be described, or it was an event "
    "the ledger does not hold and must go entirely. Do not try to rescue the clause by "
    "rewording it -- rewording keeps the verb, and the check will refuse it again.\n"
    "Return the COMPLETE corrected architecture object, same schema."
)


def architect(provider, ledger: dict, worth: dict, subject: str) -> dict:
    """STAGE 3. Ledger plus an approved lens in; a validated architecture out."""
    cand = worth.get("story_candidate") or {}
    lens = worth.get("worth_gate") or {}
    # The lens VERDICT and its claim reach the architect because the architecture must
    # carry a final lens. The gate's reasoning about publication suitability does not:
    # Worth decides whether to publish, it does not write the article.
    user = "\n".join([
        "SUBJECT", "  " + (subject or "").strip(), "",
        "THE STORY THAT WAS APPROVED",
        "  spine        : %s" % cand.get("real_event_or_change", ""),
        "  open on      : %s" % cand.get("opening_possibility", ""),
        "  tension      : %s" % cand.get("tension", ""),
        "  first sees   : %s" % cand.get("reader_first_sees", ""),
        "  later learns : %s" % cand.get("reader_later_discovers", ""),
        "",
        "THE APPROVED LENS (%s)" % lens.get("verdict", ""),
        "  " + (lens.get("lens_claim") or ""),
        "",
        "THE FROZEN LEDGER -- the only facts that exist. You may use no other.",
        ledger_block(ledger),
        "", ARCHITECT_SCHEMA])

    obj, ident = _ask(provider, ARCHITECT_SYSTEM, user, 8_000, ARCHITECTURE,
                      ARCHITECTURE_HOLD)
    errs = check_architecture(obj, ledger)
    calls, repairs = 1, 0
    if errs and not (obj.get("beats") or []):
        # Nothing to repair toward: a reply with no beats is a shape failure, not an
        # architecture that reached too far.
        raise CompositionHold(
            ARCHITECTURE, ARCHITECTURE_HOLD,
            ["the reply is not an architecture"] + errs[:6],
            {"architecture": obj, "failures": errs, "provider": ident,
             "model_calls": calls, "repairs": repairs})

    if errs:
        ru = "\n".join([
            "THE ARCHITECTURE YOU PRODUCED",
            json.dumps(obj, indent=1),
            "",
            "THE EXACT VALIDATION FAILURES",
            "\n".join("  - %s" % e for e in errs),
            "",
            "THE FROZEN LEDGER -- unchanged",
            ledger_block(ledger),
            "", ARCHITECT_SCHEMA])
        obj2, ident2 = _ask(provider, REPAIR_ARCH_SYSTEM, ru, 8_000, ARCHITECTURE,
                            ARCHITECTURE_HOLD)
        calls += 1
        repairs = 1
        ident = {"architect": ident, "repair": ident2}
        errs2 = check_architecture(obj2, ledger)
        if errs2:
            raise CompositionHold(
                ARCHITECTURE, ARCHITECTURE_HOLD,
                ["still invalid after one repair (%d failure(s))" % len(errs2)] + errs2[:10],
                {"architecture": obj2, "architecture_before_repair": obj,
                 "failures": errs2, "failures_before_repair": errs,
                 "provider": ident, "model_calls": calls, "repairs": repairs})
        obj = obj2

    return {"status": PASS, "architecture": obj, "provider": ident,
            "model_calls": calls, "repairs": repairs,
            "beats": len(obj.get("beats") or []),
            "used": len(obj.get("use_facts") or []),
            "cut": len(obj.get("cut_evidence") or [])}


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 4 -- CUT WATCH TERMS, derived deterministically
# ══════════════════════════════════════════════════════════════════════════════
# In the held-out run this was prepared by hand, and one incorrect caller passed the
# wrong shape and made the CUT audit vacuous -- it reported clean prose because it was
# watching nothing. So: derived from the ledger, no model call, contract-checked, and
# coverage reported rather than assumed.
#
# THE LICENSING RULE. A CUT fact's words are only a betrayal if no USED fact already
# licenses them. "3D-printed" leaked from a cut fact in the held-out article, but many
# cut facts share ordinary vocabulary with used ones, and watching those words would
# report a violation every time the article says something it is allowed to say. So a
# candidate term is dropped when a USED proposition carries it -- compared on stems, the
# same narrow morphology cut_adherence itself uses.
_TERM_STOP = set("""
about above after against along among around because before being below between both
during each either from into more most much neither only other over same some such than
that their them then there these they this those through under until very what when
where which while with within without would could should have has had was were been
will they're it's its also just like make made makes making take takes taken thing
things very well were what whether while
""".split()) | ST._FUNCTION_WORDS

CUT_TERMS_PER_FACT = 6
CUT_TERM_MIN = ST.CUT_SENTINEL_MIN


def _candidate_terms(fact: dict) -> list:
    """Concrete words a cut fact would betray itself by: its numbers, its named
    entities, and its distinctive content words. Ordered most to least specific."""
    text = "%s %s" % (fact.get("proposition") or "", fact.get("support_span") or "")
    out, seen = [], set()

    def push(t):
        t = (t or "").strip()
        key = t.lower()
        if t and key not in seen and len(key) >= CUT_TERM_MIN:
            seen.add(key)
            out.append(t)

    for n in sorted(ST._numbers(text), key=len, reverse=True):
        push(n)
    for e in sorted(ST._entities(text, skip_sentence_initial=False)):
        push(e)
    for w in (fact.get("entities") or []):
        push(str(w))
    for w in re.findall(r"[A-Za-z][A-Za-z-]{3,}", text):
        if w.lower() not in _TERM_STOP:
            push(w)
    return out


def derive_cut_watch_terms(arch: dict, ledger: dict) -> dict:
    """STAGE 4. {cut_fact_id: [watch terms]} plus a coverage report.

    Deterministic and model-free. Every declared CUT fact gets an entry, so
    `cut_adherence` can never silently watch nothing, and any cut fact for which no term
    survives licensing is REPORTED rather than dropped.
    """
    used_text = " ".join((ledger.get(f) or {}).get("proposition") or ""
                         for f in (arch.get("use_facts") or []))
    licensed = {ST._stem(w) for w in re.findall(r"[a-z0-9]+", used_text.lower())}

    terms: dict[str, list] = {}
    unlicensed_only, missing = [], []
    for c in (arch.get("cut_evidence") or []):
        cid = c.get("evidence_id")
        fact = ledger.get(cid)
        if cid is None:
            continue
        terms[cid] = []
        if not fact:
            missing.append(cid)
            continue
        cands = _candidate_terms(fact)
        kept = []
        for t in cands:
            # A term whose stem a USED fact already carries cannot betray the cut: the
            # article is entitled to that word.
            stems = {ST._stem(w) for w in re.findall(r"[a-z0-9]+", t.lower())}
            if stems and stems <= licensed:
                continue
            kept.append(t)
            if len(kept) >= CUT_TERMS_PER_FACT:
                break
        terms[cid] = kept
        if not kept:
            unlicensed_only.append(cid)

    report = {
        "terms": terms,
        "cut_declared": len(arch.get("cut_evidence") or []),
        "cut_with_terms": sum(1 for v in terms.values() if v),
        "cut_fully_licensed_by_used_facts": sorted(unlicensed_only),
        "cut_ids_not_in_ledger": sorted(missing),
        "terms_total": sum(len(v) for v in terms.values()),
        "derivation": "deterministic; no model call",
    }
    errs = validate_cut_terms(terms, arch)
    if missing:
        errs.append("cut_evidence names ids that are not in the ledger: %s" % sorted(missing))
    if errs:
        raise CompositionHold(CUT_TERMS, CUT_TERMS_HOLD, errs)
    report["status"] = PASS
    return report


def validate_cut_terms(terms, arch: dict) -> list:
    """The shape contract. This is the check whose absence made the CUT audit vacuous.

    `cut_adherence` does `cut_terms.get(cid) or []` and then iterates, so a str value
    iterates per CHARACTER and every term is silently dropped as too short, while a dict
    value iterates over its KEYS. Both report clean prose. Neither can happen unnoticed
    again.
    """
    errs = []
    if not isinstance(terms, dict):
        return ["cut watch terms must be a dict of {fact_id: [terms]}, got %s"
                % type(terms).__name__]
    declared = [c.get("evidence_id") for c in (arch.get("cut_evidence") or [])]
    for cid in declared:
        if cid not in terms:
            errs.append("cut fact %s has no watch-term entry, so nothing would watch it"
                        % cid)
    for cid, v in sorted(terms.items()):
        if not isinstance(v, list):
            errs.append("%s: watch terms must be a list of strings, got %s -- a %s here "
                        "iterates wrongly and silently watches nothing"
                        % (cid, type(v).__name__, type(v).__name__))
            continue
        for t in v:
            if not isinstance(t, str):
                errs.append("%s: watch term %r is %s, not a string"
                            % (cid, t, type(t).__name__))
            elif len(t.strip()) < CUT_TERM_MIN:
                errs.append("%s: watch term %r is shorter than the %d-character floor "
                            "cut_adherence enforces, so it would be reported skipped "
                            "rather than checked" % (cid, t, CUT_TERM_MIN))
    extra = sorted(set(terms) - set(declared))
    if extra:
        errs.append("watch terms for facts that were not cut: %s" % extra)
    return errs


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 5 -- WRITER
# ══════════════════════════════════════════════════════════════════════════════
# The Writer receives the minimal packet and the craft doctrine. Nothing else: no
# research pack, no source bodies, no provenance, no evidence gaps, no grounding
# boundaries, no validation reasoning, no Worth reasoning. `render()` builds the packet
# text and is the only thing that does.
#
# CRAFT DOCTRINE. `stages.PROSE_DOCTRINE` already carries almost all of it, and is
# reused verbatim rather than restated: difficult ideas and easy reading, plain
# vocabulary, one claim to a sentence, concrete before abstract, keep naming the thing,
# explain what the reader needs at once in ordinary words, no thesis announcement, no
# summary ending, write shorter if the material will not carry the length. Three things
# the campaign's craft research established are genuinely absent from it, so only those
# three are added.
WRITER_CRAFT_DELTA = (
    "  Keep a technical term when it is the precise one, and explain it in ordinary "
    "words at first use. Simplify the SYNTAX around a difficult idea rather than "
    "replacing the idea's own name with a vaguer word.\n"
    "  Do not let a sentence announce its own structural job. Sentences like \"The answer "
    "was mostly things you cannot look at\", \"So go back to the beginning\", \"Read that "
    "list again and notice what it is\" tell the reader what the article is doing instead "
    "of telling them about the world. This is the single measured difference between "
    "published prose and this pipeline's drafts, so it matters more than it looks: write "
    "the thing, not a note about the thing. One-sentence paragraphs are fine and normal.\n"
    "  Write in your own plain register. Do not imitate a named writer or reach for a "
    "recognisable style."
)

WRITER_SYSTEM = (
    "You are writing one finished article from an approved packet.\n\n"
    + S.PROSE_DOCTRINE + "\n" + WRITER_CRAFT_DELTA + "\n\n" + S._NO_FABRICATION
    + "\n\nOutput the article as markdown: a single `# ` title line, then the prose. No "
      "front matter, no notes to the editor, no headings inside the body, no commentary "
      "about what you did."
)


# Not a length policy. A reply below this is not an article at all, and BRIEF is a real
# article_type whose length this gate must not second-guess.
WRITER_MIN_WORDS = 50


def writer_packet(arch: dict, ledger: dict) -> tuple:
    """The packet and its rendered prompt. Refused if it carries the auditing frame."""
    packet = ST.build_packet(arch, arch.get("final_lens") or {},
                             LG.propositions(ledger))
    errs = ST.validate_packet(packet)
    if errs:
        raise CompositionHold(WRITER, WRITER_HOLD,
                              ["the writer packet is not clean"] + errs)
    return packet, ST.render(packet)


def _clean_article(text: str) -> str:
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.split("```")[1] if "```" in t[3:] else t[3:]
        if t.lower().startswith("markdown"):
            t = t[8:]
    return t.strip()


def write_article(provider, arch: dict, ledger: dict) -> dict:
    """STAGE 5. ONE Writer call. A retry only when the output is mechanically unusable."""
    packet, prompt = writer_packet(arch, ledger)
    last = ""
    for attempt in (1, 2):
        try:
            comp = provider.complete(system=WRITER_SYSTEM, user=prompt,
                                     max_tokens=6_000)
        except ProviderError as e:
            raise CompositionHold(WRITER, WRITER_HOLD, ["provider unavailable: %s" % e])
        article = _clean_article(comp.text)
        # Mechanically unusable, not "not good enough": empty, missing its title line, or
        # too short to be prose at all. The floor is deliberately very low, because BRIEF
        # is a legitimate article_type and a length judgement is not this gate's business
        # -- it exists to catch a reply that is not an article, not a reply that is a
        # short one. There is no quality-regeneration loop here.
        if len(article.split()) >= WRITER_MIN_WORDS and article.lstrip().startswith("#"):
            return {"status": PASS, "article_text": article, "packet": packet,
                    "prompt": prompt, "prompt_sha256": C.sha256_text(prompt),
                    "provider": _identity(comp, attempt),
                    "model_calls": attempt, "repairs": 0,
                    "words": len(article.split())}
        last = ("empty reply" if not article else
                "%d words, title line %s" % (len(article.split()),
                                             "present" if article.lstrip().startswith("#")
                                             else "missing"))
    raise CompositionHold(WRITER, WRITER_HOLD,
                          ["the Writer produced nothing usable after one mechanical "
                           "retry (%s)" % last])


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 6 -- CONTINUITY
# ══════════════════════════════════════════════════════════════════════════════
# LINGUISTIC FREEDOM, ZERO FACTUAL FREEDOM. Exactly one pass.
CONTINUITY_SYSTEM = (
    "You are the continuity editor. The article's facts and structure are already "
    "correct and are not yours to change. Your job is to make it read as continuous "
    "prose.\n"
    "\n"
    "YOU MAY: rephrase, merge two sentences, split one into two, delete a sentence whose "
    "only job was signposting, re-paragraph freely, and remove repetition. Leaving a good "
    "sentence exactly as it is (NO_CHANGE) is a valid and common answer.\n"
    "\n"
    "YOU MAY NOT add anything: no fact, no event, no relation, no causality, no negative "
    "claim, no person, no experience, no number, no name, no colour, no place. This is "
    "checked mechanically both ways -- by lineage and by a semantic delta -- so an "
    "addition will be caught even when it introduces no new noun. In particular do not "
    "add a because, a therefore, a so, an only, a never or a first that the sentence you "
    "are editing did not already carry: those are the additions that look like style and "
    "are not.\n"
    "\n"
    "WHAT TO FIX FIRST. Sentences that announce their own structural job -- telling the "
    "reader what the article is doing rather than telling them about the world. Delete or "
    "rewrite them. Then scaffolding language, then repetition, then any sentence a reader "
    "would have to read twice.\n"
    "\n"
    "Every output sentence must declare the input sentence ids it came from. A sentence "
    "with no parent is an invention."
)

CONTINUITY_SCHEMA = (
    "Reply with ONE JSON object:\n"
    '{"edits": [{"id": "E001", "operation": "REPHRASE", "parents": ["D001"],\n'
    '            "text": "the output sentence",\n'
    '            "paragraph_break": false}]}\n'
    "operation is one of: %s\n"
    "  NO_CHANGE       keep the parent sentence as it is (still give its text)\n"
    "  REPHRASE        one parent, reworded\n"
    "  MERGE_REPHRASE  TWO OR MORE parents combined into one sentence\n"
    "  SPLIT_REPHRASE  one parent becoming this and the next output sentence\n"
    "  DELETE          the parent is removed; give NO text\n"
    'Set "paragraph_break": true on the LAST sentence of each paragraph. Paragraphing is\n'
    "yours to decide.\n"
    "Emit edits in READING ORDER, covering the whole article.\n"
    "No prose outside the JSON." % ", ".join(CE.OPERATIONS)
)


def continuity_pass(provider, article_text: str, arch: dict) -> dict:
    """STAGE 6. Exactly one pass. A failure holds; it does not re-run the Writer."""
    draft = CE.label_draft(article_text)
    if not draft:
        raise CompositionHold(CONTINUITY, CONTINUITY_HOLD,
                              ["the draft has no sentences to edit"])
    title = ""
    for line in article_text.splitlines():
        if line.strip().startswith("#"):
            title = line.strip().lstrip("#").strip()
            break

    user = "\n".join(
        ["THE DRAFT, ONE SENTENCE PER LINE"]
        + ["  %s  %s" % (k, v) for k, v in sorted(draft.items())]
        + ["", CONTINUITY_SCHEMA])
    obj, ident = _ask(provider, CONTINUITY_SYSTEM, user, 8_000, CONTINUITY,
                      CONTINUITY_HOLD)
    edits = obj.get("edits")
    if not isinstance(edits, list) or not edits:
        raise CompositionHold(CONTINUITY, CONTINUITY_HOLD,
                              ["the reply carries no 'edits' list"])

    errs = CE.validate_lineage(edits, draft)
    if errs:
        raise CompositionHold(CONTINUITY, CONTINUITY_HOLD,
                              ["continuity lineage is invalid -- an output sentence with "
                               "no parent is an invention"] + errs[:10])
    body = CE.apply_edits(edits)
    if not body.strip():
        raise CompositionHold(CONTINUITY, CONTINUITY_HOLD,
                              ["every sentence was deleted"])
    final = ("# %s\n\n%s" % (title, body)) if title else body

    # The semantic gate. Lineage is necessary and not sufficient: an editor can invent a
    # claim while truthfully naming a parent.
    delta_errs = CE.validate_semantic_delta(article_text, final)
    form = arch.get("article_type")
    return {"status": PASS, "article_text": final, "edits": edits,
            "draft_sentences": len(draft),
            "output_sentences": sum(1 for e in edits
                                    if e.get("operation") != CE.DELETE),
            "deletes": sum(1 for e in edits if e.get("operation") == CE.DELETE),
            "semantic_delta": CE.semantic_delta(article_text, final),
            "semantic_delta_errors": delta_errs,
            "writtenness": CE.writtenness(final, form),
            "provider": ident, "model_calls": 1, "repairs": 0,
            "words": len(body.split())}


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 7 -- POST-CONTINUITY SAFETY
# ══════════════════════════════════════════════════════════════════════════════
# Every merged screen, on the finished candidate. A failure HOLDS. It does not regenerate
# the Writer: an article that invented something is evidence about the run, and rerolling
# it destroys that evidence and buys a second draft with an unknown defect.
def safety_audit(draft_text: str, final_text: str, packet: dict, arch: dict,
                 ledger: dict, cut_terms: dict) -> dict:
    """The merged post-writer stack, on both the draft and the final."""
    def screens(text):
        surface = ST.factual_surface_audit(text, packet)
        neg = ST.negative_admission_audit(text, ledger)
        return {
            "words": len(text.split()),
            "paragraphs": len(CE.paragraphs(text)),
            "factual_surface": surface,
            "hard_factual_ok": surface["hard_ok"],
            "negative_admission": neg,
            "negative_admission_ok": neg["ok"],
            "intent_causal": ST.intent_causal_scan(text),
            "prose_leaks": ST.prose_leaks(text),
            "scaffold": ST.scaffold_adherence(text),
            "cut_adherence": ST.cut_adherence(text, arch, cut_terms),
        }

    a = {"writer_draft": screens(draft_text), "continuity_final": screens(final_text)}
    f = a["continuity_final"]
    delta_errs = CE.validate_semantic_delta(draft_text, final_text)

    blocking = []
    if not f["hard_factual_ok"]:
        s = f["factual_surface"]
        blocking.append(
            "NEW_UNSUPPORTED_FACTS: the final prose carries factual surface the packet "
            "never granted -- numbers=%s entities=%s sensory=%s scene=%s spatial=%s"
            % (s["unapproved_numbers"], s["unapproved_entities"], s["unapproved_sensory"],
               s["unapproved_scene"], s["unapproved_spatial"]))
    if not f["negative_admission_ok"]:
        blocking.append(
            "UNSUPPORTED_NEGATIVES: %d negative-shaped sentence(s) with no negative fact "
            "behind them: %s"
            % (len(f["negative_admission"]["unmatched"]),
               [h["sentence"][:90] for h in f["negative_admission"]["unmatched"]][:4]))
    if f["cut_adherence"]["violations"]:
        blocking.append(
            "CUT_LEAKAGE: %s"
            % [(v["evidence_id"], v["term"], v["match"])
               for v in f["cut_adherence"]["violations"]][:6])
    if not f["prose_leaks"]["ok"] or not f["scaffold"]["ok"]:
        blocking.append("MACHINE_LANGUAGE: provenance frames %s, scaffold names %s"
                        % (f["prose_leaks"]["frames"], f["scaffold"]["leaked"]))
    # intent_causal_scan is TELEMETRY, and deliberately so. Unlike
    # negative_admission_audit it pairs nothing against the ledger -- it is a pure text
    # scan -- so it fires on intent the ledger explicitly grants: an ATTRIBUTION fact
    # reading "fitted with fragrances INTENDED to engage all the senses" licenses the
    # article to say exactly that, and the scan flags it anyway. Blocking on it would
    # refuse approved material, and giving it a ledger-pairing pass would be a new
    # validator, which this campaign is not adding. It is also absent from the required
    # zeroes the campaign specifies. So it is counted and surfaced to the human gate,
    # where an unsupported motive is a thing a reader can actually settle.
    if delta_errs:
        blocking.append("CONTINUITY_ADDED_MATERIAL: %s" % delta_errs[:6])
    # The CUT audit reporting its own blind spots is a failure of the derivation, which is
    # deterministic and therefore a bug rather than a judgement.
    ca = f["cut_adherence"]
    if ca["cut_without_watch_terms"] or ca["skipped_too_short"]:
        blocking.append(
            "CUT_AUDIT_BLIND: cut facts with no watch term %s; terms below the length "
            "floor %s -- the audit would report clean prose without having looked"
            % (ca["cut_without_watch_terms"], ca["skipped_too_short"]))

    return {"status": HOLD if blocking else PASS,
            "blocking": blocking,
            "audits": a,
            "semantic_delta": CE.semantic_delta(draft_text, final_text),
            "semantic_delta_errors": delta_errs,
            "lens_serialized": ST.lens_is_serialized(final_text,
                                                     arch.get("final_lens") or {}),
            "lens_realization": ST.validate_lens_realization(
                arch, arch.get("final_lens") or {}, final_text),
            "architect_prose_telemetry": ST.architect_prose_audit(
                arch, LG.propositions(ledger))}


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 8/9 -- THE FACTUAL BRIDGE
# ══════════════════════════════════════════════════════════════════════════════
# The smallest clean interface to the two authoritative implementations. Neither is
# reimplemented and neither's semantics are touched. `heldout_factual_bridge.py` was the
# reference; it is not imported, because it carries the held-out article's own paths,
# hardcoded source ids and a hand-written F10 fallback.
def ground_candidate(provider, article_text: str, source_text: str, source_sha: str,
                     pack: dict) -> dict:
    """STAGE 8. The authoritative Grounder, called unmodified.

    `stages.ground` is the same function the legacy path runs, with the same arguments:
    the article, the anchor source and the pack. It never sees the architecture or the
    ledger -- grounding asks whether the PROSE is carried by the SOURCES, and handing it
    the machine's own approval record is how a grounder starts agreeing with the engine.
    """
    try:
        gf = S.ground(provider, article_text, source_text, source_sha, pack)
    except ProviderError as e:
        raise CompositionHold(GROUNDING, GROUNDING_HOLD,
                              ["grounder provider unavailable: %s" % e])
    findings = gf.get("findings") or []
    # The classifications are the Grounder's own, and the policy applied to them is the
    # frozen one from decision.py: TRUE_UNSUPPORTED blocks, and TRUE_UNCERTAIN blocks
    # unless it was explicitly adjudicated, because the architecture does not establish
    # that an uncertain finding is safe to accept. Restated here rather than imported
    # because `decide` also requires a legacy artifact lineage this path does not have;
    # the POLICY is unchanged, and no classification is reinterpreted.
    unsupported = [f for f in findings if f.get("classification") == "TRUE_UNSUPPORTED"]
    uncertain = [f for f in findings if f.get("classification") == "TRUE_UNCERTAIN"]
    blocking = list(unsupported)
    if uncertain and not gf.get("uncertain_adjudicated", False):
        blocking += uncertain
    settled = gf.get("status") == "settled"
    return {"status": PASS if (settled and not blocking) else HOLD,
            "grounding": {k: v for k, v in gf.items() if k != "_provider"},
            "findings": findings,
            "unsupported": unsupported,
            "uncertain": uncertain,
            "blocking": blocking,
            "grounding_status": gf.get("status"),
            "provider": gf.get("_provider", {}),
            "model_calls": 1}


# STAGE 9 lives OUTSIDE this package, in `composition_factual_bridge.py`, and is
# injected. That is a purity constraint, not a preference: the authoritative Fact Check
# is `orchestrator.fact_check.FactCheckMixin`, and `new_engine_v1` is asserted by test to
# import no part of the legacy orchestrator -- an AST scan that sees a function-local
# import exactly as it sees a top-level one. So the bridge is the caller's to supply,
# the same way `runner.run` already takes an injected `research_fn`.
#
# A missing callable is reported NOT_RUN and never stubbed: a publication gate that
# answers a question nobody asked it is worse than an absent one, so the run carries the
# absence to the human gate rather than passing on it.
def fact_check_unavailable(article_text: str) -> dict:
    return {"status": NOT_RUN,
            "missing": ["no fact-check callable was injected; the authoritative "
                        "implementation lives outside this package by design"],
            "runtime_seconds": 0.0}


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 10 -- READER GATE
# ══════════════════════════════════════════════════════════════════════════════
# Runs LAST, after factual safety, because a reader verdict on an article that turns out
# to be ungrounded is wasted and misleading. It returns exact passages on a HOLD and
# nothing rewrites in response: a reader HOLD is a report to a person.
READER_DIMENSIONS = ("OPENING", "READABILITY", "ACCESSIBLE_READING", "MOMENTUM",
                     "BREATHING", "RESEARCH_LOAD", "ENGINE_LANGUAGE_LEAK",
                     "CRIP_MINDS_FIT", "ENDING")

READER_SYSTEM = (
    "You are reading a finished article as an ordinary intelligent reader who has not yet "
    "decided to keep reading. You are not the writer and you do not fix anything. Judge "
    "what is on the page.\n"
    "\n"
    "Report PASS or HOLD on each dimension, and on a HOLD quote the exact passage:\n"
    "  OPENING              Do the first two to four sentences name the concrete subject,\n"
    "                       say what is particular about it, and make clear why the piece\n"
    "                       exists? A framing device in front of the subject is a HOLD.\n"
    "  READABILITY          Does any sentence need rereading before its main claim is\n"
    "                       clear?\n"
    "  ACCESSIBLE_READING   Are difficult ideas carried in easy syntax and ordinary\n"
    "                       words? Is every technical term explained at first use, in a\n"
    "                       sentence, in plain words?\n"
    "  MOMENTUM             Does each paragraph earn the next? A paragraph that restates\n"
    "                       an earlier one in different abstract vocabulary is a HOLD.\n"
    "  BREATHING            Is concrete material given room, or is every sentence\n"
    "                       carrying fact plus interpretation plus atmosphere plus\n"
    "                       conclusion at once?\n"
    "  RESEARCH_LOAD        Does the piece read as written selectively from wide\n"
    "                       research, or as everything the writer found? One fact read\n"
    "                       three ways is one fact.\n"
    "  ENGINE_LANGUAGE_LEAK Any machine or process language: the source, the evidence,\n"
    "                       the record, what is unknown or unestablished, scaffold names,\n"
    "                       or a sentence announcing its own structural job.\n"
    "  CRIP_MINDS_FIT       Is the disability reading earned by the material, or asserted\n"
    "                       in one abstract late paragraph? Fit is earned, not asserted.\n"
    "  ENDING               Does it stop when the point lands, or add a closing paragraph\n"
    "                       because articles are expected to have one? Restating the\n"
    "                       arrival in other words is a HOLD.\n"
    "\n"
    "Be a hard reader. Do not award a PASS for the absence of an obvious defect, and do "
    "not soften a real one. If the piece is good, say so plainly."
)

READER_SCHEMA = (
    "Reply with ONE JSON object:\n"
    '{"dimensions": {"OPENING": {"verdict": "PASS", "note": "...",\n'
    '                            "passages": ["exact quote on a HOLD"]}, ...},\n'
    ' "overall": "PASS",            PASS only if every dimension passes\n'
    ' "one_line": "what a reader would say about this piece"}\n'
    "Every dimension must appear: %s\n"
    "No prose outside the JSON." % ", ".join(READER_DIMENSIONS)
)


def reader_gate(provider, article_text: str) -> dict:
    """STAGE 10. Nine dimensions. Exact passages on a HOLD. No auto-rewrite."""
    obj, ident = _ask(provider, READER_SYSTEM,
                      "THE ARTICLE\n\n" + article_text + "\n\n" + READER_SCHEMA,
                      4_000, READER, READER_HOLD)
    dims = obj.get("dimensions") or {}
    missing = [d for d in READER_DIMENSIONS if d not in dims]
    if missing:
        raise CompositionHold(READER, READER_HOLD,
                              ["the reader gate did not report on %s" % missing])
    held = {d: dims[d] for d in READER_DIMENSIONS
            if str((dims[d] or {}).get("verdict", "")).upper() != PASS}
    return {"status": HOLD if held else PASS,
            "dimensions": dims,
            "held": held,
            "passages": {d: (v or {}).get("passages") or [] for d, v in held.items()},
            "one_line": obj.get("one_line", ""),
            "provider": ident, "model_calls": 1}


# ══════════════════════════════════════════════════════════════════════════════
# THE ENTRYPOINT
# ══════════════════════════════════════════════════════════════════════════════
def run_story_architecture_composition(
        provider, *, pack: dict, source_text: str, source_sha: str,
        subject: str = "", fact_check: bool = True, reader: bool = True,
        fact_check_fn=None, out_dir=None) -> dict:
    """Approved research material in; a final article candidate out, or a HOLD.

    Ten stages, each one either PASS or the stage that stopped the run. There is no
    stage that reruns an earlier stage, and no stage that regenerates prose to get a
    better verdict: the first HOLD is the answer, and it names itself.

    `fact_check_fn` is injected the same way `runner.run` injects research: the
    authoritative Fact Check lives outside this package (see `fact_check_unavailable`),
    and a test can exercise the orchestration without two live credentials.
    """
    P = composition_provider(provider)
    subject = subject or pack.get("subject") or ""
    st = {s: {"status": NOT_RUN} for s in STAGES}
    calls: dict[str, int] = {}
    repairs: dict[str, int] = {}
    t0 = time.time()

    def record(stage, payload):
        st[stage] = payload
        calls[stage] = payload.get("model_calls", 0)
        repairs[stage] = payload.get("repairs", 0)
        return payload

    def out(failure_stage=None, failure_reason=None, code=None, article=None):
        """Build the result AND persist it. Persisting here rather than at each return
        is the point: a HOLD at safety, grounding, fact check or the reader gate is
        exactly the run whose intermediate artifacts someone needs to read, and four
        separate returns is four chances to forget one."""
        result = {
            "engine": COMPOSITION_STORY_ARCHITECTURE,
            "status": PASS if failure_stage is None else HOLD,
            "stages": {s: st[s].get("status", NOT_RUN) for s in STAGES},
            "detail": st,
            "failure_stage": failure_stage,
            "failure_reason": failure_reason,
            "reason_code": code,
            "article_text": article,
            "words": len((article or "").split()),
            "model_calls_by_stage": dict(calls),
            "model_calls_total": sum(calls.values()),
            "repairs_by_stage": {k: v for k, v in repairs.items() if v},
            "runtime_seconds": round(time.time() - t0, 1),
            "subject": subject,
        }
        if out_dir is not None:
            persist(out_dir, result)
        return result

    try:
        led = record(LEDGER, freeze_ledger(P, pack, subject))
        ledger = led["ledger"]

        w = record(WORTH, worth_gate(P, ledger, subject))

        a = record(ARCHITECTURE, architect(P, ledger, w, subject))
        arch = a["architecture"]

        cut = record(CUT_TERMS, derive_cut_watch_terms(arch, ledger))

        wr = record(WRITER, write_article(P, arch, ledger))
        draft = wr["article_text"]

        cont = record(CONTINUITY, continuity_pass(P, draft, arch))
        final = cont["article_text"]

        sa = record(SAFETY, safety_audit(draft, final, wr["packet"], arch, ledger,
                                         cut["terms"]))
        if sa["status"] != PASS:
            return out(SAFETY, "; ".join(sa["blocking"])[:600], SAFETY_HOLD, final)

        g = record(GROUNDING, ground_candidate(P, final, source_text, source_sha, pack))
        if g["status"] != PASS:
            return out(GROUNDING,
                       "grounding status %r; %d blocking finding(s): %s"
                       % (g["grounding_status"], len(g["blocking"]),
                          [("%s %s" % (f.get("classification"),
                                       str(f.get("quote") or f.get("claim") or "")[:70]))
                           for f in g["blocking"]][:4]),
                       GROUNDING_HOLD, final)

        if fact_check:
            fc = record(FACT_CHECK, (fact_check_fn or fact_check_unavailable)(final))
            if fc.get("status") == HOLD:
                return out(FACT_CHECK,
                           "blocking contradiction(s): %s"
                           % (fc.get("blocking_contradictions") or [])[:4],
                           FACT_CHECK_HOLD, final)
        else:
            st[FACT_CHECK] = {"status": SKIPPED}

        if reader:
            rg = record(READER, reader_gate(P, final))
            if rg["status"] != PASS:
                return out(READER,
                           "reader HOLD on %s" % ", ".join(sorted(rg["held"])),
                           READER_HOLD, final)
        else:
            st[READER] = {"status": SKIPPED}

        return out(article=final)

    except CompositionHold as e:
        st[e.stage] = dict(e.payload, status=HOLD, code=e.code, reasons=e.reasons)
        return out(e.stage, "; ".join(e.reasons)[:600], e.code,
                   st.get(CONTINUITY, {}).get("article_text")
                   or st.get(WRITER, {}).get("article_text"))


def persist(out_dir, result: dict) -> None:
    """Write the run's artifacts. A HOLD persists everything it reached, so "what did the
    engine actually do" is answerable afterwards -- the same reason a HOLDing research
    pack is persisted in `runner.run`."""
    import pathlib
    d = pathlib.Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    det = result.get("detail") or {}

    def dump(name, obj):
        (d / name).write_text(json.dumps(obj, indent=1, sort_keys=True, default=str))

    dump("COMPOSITION_RESULT.json",
         {k: v for k, v in result.items() if k != "detail"})
    if det.get(LEDGER, {}).get("ledger"):
        dump("FINAL_EVIDENCE_MANIFEST.json",
             {"subject": result.get("subject"),
              "facts": det[LEDGER]["ledger"],
              "fact_count": det[LEDGER].get("facts"),
              "sources": det[LEDGER].get("sources"),
              "freeze_rule": det[LEDGER].get("freeze_rule")})
    if det.get(WORTH, {}).get("worth_gate"):
        dump("WORTH_AND_CANDIDATE.json",
             {k: det[WORTH].get(k)
              for k in ("worth_gate", "story_candidate", "narrative_yield")})
    if det.get(ARCHITECTURE, {}).get("architecture"):
        dump("ARCHITECTURE.json", det[ARCHITECTURE]["architecture"])
    if det.get(CUT_TERMS, {}).get("terms") is not None:
        dump("CUT_WATCH_TERMS.json", det[CUT_TERMS]["terms"])
    if det.get(WRITER, {}).get("prompt"):
        (d / "WRITER_PACKET.txt").write_text(det[WRITER]["prompt"])
    if det.get(WRITER, {}).get("article_text"):
        (d / "WRITER_DRAFT.md").write_text(det[WRITER]["article_text"])
    if det.get(CONTINUITY, {}).get("article_text"):
        (d / "CONTINUITY_FINAL.md").write_text(det[CONTINUITY]["article_text"])
    if det.get(SAFETY, {}).get("audits"):
        dump("SAFETY_AUDIT.json", {k: v for k, v in det[SAFETY].items()
                                   if k != "status"})
    if det.get(GROUNDING, {}).get("grounding"):
        dump("GROUNDING_FINDINGS.json", det[GROUNDING]["grounding"])
    if det.get(FACT_CHECK, {}).get("status") not in (None, NOT_RUN, SKIPPED):
        dump("FACT_CHECK.json", det[FACT_CHECK])
    if det.get(READER, {}).get("dimensions"):
        dump("READER_AUDIT.json", {k: det[READER].get(k)
                                   for k in ("dimensions", "held", "one_line", "status")})
