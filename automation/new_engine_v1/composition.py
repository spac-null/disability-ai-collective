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

import ast
import difflib
import json
import re
import time

from . import contracts as C
from . import continuity as CE
from . import jurisdiction as JU
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
PROSE_FINISH = "PROSE_FINISH"
SAFETY = "SAFETY"
GROUNDING = "GROUNDING"
FACT_CHECK = "FACT_CHECK"
READER = "READER"
PACKAGE = "PACKAGE"

STAGES = (LEDGER, WORTH, ARCHITECTURE, CUT_TERMS, WRITER, CONTINUITY,
          PROSE_FINISH, PACKAGE, SAFETY,
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
# A stage supplied from a previous run's frozen artifacts rather than executed. Marked
# distinctly on purpose: a replay is a cheap way to test a later stage, and it must be
# impossible to mistake one for an autonomous run. `replay` is set on the result too.
REPLAYED = "REPLAYED"

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
# NOT a HOLD code. The package stage cannot stop an article; this names the transport or
# validation failure that made it skip, so a run can still say why it published without one.
PACKAGE_SKIPPED = "PACKAGE_SKIPPED"
# The package's own outcome, kept apart from the run's editorial verdict. A package that
# could not be PRODUCED is a fault in the machinery; a package that was produced and
# refused is a fault in the writing. Neither is a reason to call the article bad, and
# neither publishes: the candidate goes to the owner instead.
PACKAGE_OK = "OK"
PACKAGE_REFUSED = "REFUSED"
PACKAGE_TECHNICAL_FAILURE = "TECHNICAL_FAILURE"

# WHICH SURFACE PUBLISHED. Recorded because the two are different articles: the package,
# the hashes and every gate verdict belong to one of them and never to a mixture.
SURFACE_PROSE_FINISH = "PROSE_FINISH"
PRE_POLISH_FALLBACK = "PRE_POLISH_FALLBACK"

# The provider said the subscription cannot serve this call. A first-class outcome, not a
# retry and not a reason to start spending money elsewhere: an automatic fallback to a paid
# provider is exactly the surprise this code exists to avoid, so the run stops and says so.
# Raised by the injected provider (see claude_cli_provider.SubscriptionLimit) and recognised
# here by duck type, because this package may not import the CLI adapter.
CLAUDE_SUBSCRIPTION_LIMIT = "CLAUDE_SUBSCRIPTION_LIMIT"


def _is_subscription_limit(exc: BaseException) -> bool:
    return type(exc).__name__ == "SubscriptionLimit"

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
        return Provider(model=want, url=provider.url)
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
        except Exception as e:
            # A limit is not a transport failure and must not be retried: the second
            # attempt cannot succeed and the only thing it can do is look like one.
            if _is_subscription_limit(e):
                raise CompositionHold(stage, CLAUDE_SUBSCRIPTION_LIMIT,
                                      ["the Claude subscription cannot serve this call: "
                                       "%s" % str(e)[:300],
                                       "stopping; no paid fallback was attempted"])
            if not isinstance(e, ProviderError) and type(e).__name__ != "ClaudeCLIError":
                raise
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
    "NO DEFAULT NATIONAL FRAMEWORK. When a source names a legal standard, a code or an "
    "accessibility classification -- the ADA, Section 508, the Equality Act, a building "
    "code, a directory's own access field -- what you have evidence of is THAT RECORD "
    "SAYING THAT THING. You do not have evidence that the standard applies to your "
    "subject, and you may not word the proposition as though it does. Write it as what "
    "it is: 'the directory entry for X records ADA accessibility as No', not 'X is not "
    "ADA accessible', and never 'X is not accessible'. This is the single most common "
    "way a foreign framework gets imported into a story it has no business in: English-"
    "language research turns up American standards for subjects anywhere on earth, "
    "because American material is what is written down in English. Being the only "
    "standard anybody wrote down does not make a standard local. A later check will "
    "restrict such a fact to attribution automatically -- write it correctly and there "
    "is nothing to restrict.\n"
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


def highest_fact_number(ledger: dict) -> int:
    """The largest N among F<N> ids, compared as integers.

    Exists because the obvious `max(ledger)` is a lexicographic comparison, and every
    ledger over 99 facts makes it wrong in the one direction that causes a collision.
    """
    nums = [int(m.group(1)) for m in
            (re.match(r"^F(\d+)", str(k)) for k in (ledger or {})) if m]
    return max(nums) if nums else 0


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
        # NUMERICALLY, not lexicographically. `max()` over strings returns "F99" for a
        # ledger containing F100..F103, because "F9" sorts above "F1". The repair was
        # then told to number its splits from F99, minted F100-F102 on top of three
        # facts that had already validated, and the anti-rewrite guard refused the whole
        # ledger. Measured on the Ground Truth canary at 103 facts.
        ru += ["", "Highest existing fact id: F%d -- number any new fact from F%d upward, "
                   "and never reuse an id that is not in the rejected list above."
                   % (highest_fact_number(ledger), highest_fact_number(ledger) + 1),
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

    # NO DEFAULT NATIONAL FRAMEWORK (2026-09-06). Deterministic, no model call, and it
    # runs LAST -- on the ledger that already passed span verification -- because it
    # changes what a fact PERMITS, never whether the fact is supported. See
    # jurisdiction.py: a standard that is not the law where the subject is becomes an
    # ATTRIBUTION about the record that states it, and nothing is deleted.
    ledger, jurisdiction_report = JU.apply(ledger, pack)

    kinds = {}
    for f in ledger.values():
        kinds[f.get("claim_kind")] = kinds.get(f.get("claim_kind"), 0) + 1
    return {"status": PASS, "ledger": ledger, "provider": ident,
            "model_calls": calls, "repairs": repairs,
            "jurisdiction": jurisdiction_report,
            "subject_place": JU.subject_place(pack),
            "subject_country": jurisdiction_report["subject_country"],
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
    "3. PARTICULARS, NOT DEFINITIONS. A lens has to rest on at least one fact that is "
    "ABOUT THIS SUBJECT -- a specific record, measure, field, number, decision, person or "
    "event belonging to the thing you are reading. A fact that states something general "
    "about a category cannot carry an article, however true it is and however much it "
    "mentions disability.\n"
    "  Three real examples, all from ledgers this gate passed. One is a particular. The "
    "other two are the two different ways a fact can look like one and not be:\n"
    "    PARTICULAR  'McGonigle says the house's flexibility means the clients can close "
    "down three of the six blocks.' That is this house's own design decision, in its "
    "architect's own account of it. An article can stand on it, because it says something "
    "no other house's account says, and the reading stays inside it. Note what makes it "
    "work: not that a house involves levels and courtyards -- every house does -- but the "
    "tension between the building's own claim to adaptability and what that adaptability "
    "actually changes versus leaves fixed.\n"
    "    GENERAL     'Cochlear implants restore hearing in people with profound hearing "
    "loss and are a form of neuroprosthesis.' True, and a textbook definition. It would "
    "appear in any article about neurotechnology, so it can only ever be a passing clause "
    "and the piece will read as legitimation rather than argument.\n"
    "    NOT THIS SUBJECT  'The field station directory entry for WildSumaco Biological "
    "Station records ADA accessibility as No.' Specific, sourced, about a named place -- "
    "and still not a particular about the 2025 pavilion the article was about. It is a US "
    "directory's classification of the STATION, under the legal framework of a country the "
    "building is not in, and nothing in that ledger tied the record to the pavilion. A "
    "record about a neighbouring, parent or broader entity is not automatically a "
    "particular about your subject, and a foreign legal framework does not become the "
    "local one by being the only standard anybody wrote down. Placing such a record beside "
    "a claim about the subject is worse than useless: both sentences can be accurate and "
    "the adjacency still invites a third conclusion no source supports.\n"
    "  The second example was passed as STRONG_DIRECT_LENS on the strength of two such "
    "definitions. A whole article was written and correctly rejected as wrong for this "
    "publication. The third carried a published article's argument until the claim had to "
    "be withdrawn from the live piece. Those are the two errors this field exists to "
    "stop, and the third is the more dangerous because it looks specific.\n"
    "  A PARTICULAR IS NOT A BUILDING. Buildings are only the easiest place to see one, "
    "because they hand you objects and routes. The same shape lives anywhere a system "
    "commits to what a person is. Two more, in other domains:\n"
    "    PARTICULAR (a classification)  a streaming service's password-sharing policy has "
    "to decide what counts as one household. The particular is that boundary: it is an "
    "unappealable category that decides what a household is, so an interdependent or "
    "care-arranged household is not an edge case the rule handles badly -- it is one the "
    "rule cannot see, and there is no appeal from a category you were never shown.\n"
    "    PARTICULAR (a biological assumption)  a soundscape or acoustic survey is defined "
    "over a hearing range. The particular is the range: what counts as the audible world "
    "here depends on which hearing defines it, so the survey's own boundary is a claim "
    "about whose perception the world is being described for.\n"
    "  Those are shapes, not a library. A strong Crip Minds particular can live in a "
    "building, an experiment, a measurement, a classification, an interface, a biological "
    "assumption or an institutional rule. Do not treat the architectural one as the model "
    "and the rest as exceptions.\n"
    "  Then answer whether that evidence can CARRY the article. One particular is enough "
    "only if the story can be built on it. Name it in `lens_carrier`: the concrete "
    "subject-specific fact or tension the Crip Minds reading actually stands on, in a "
    "clause. Then say in `can_carry_article` whether it can hold more than one incidental "
    "sentence -- whether a reader would still be inside that reading in the middle of the "
    "piece, or whether it appears once and the article goes on to be about something "
    "else. A particular that gets mentioned and dropped is the same failure as a "
    "definition, arriving later.\n"
    "  AN ACCESSIBILITY FACT IS NOT AUTOMATICALLY AN INSIGHT. A subject-specific "
    "particular is EVIDENCE. Being about access does not make it the reading. A ramp, a "
    "stair, a lift, an acoustic condition, an accessibility field, an access page or a "
    "code requirement can carry an article only when it reveals a LESS OBVIOUS "
    "assumption, contradiction, mechanism, classification, dependency, timing model, "
    "sensory model, or model of the body, participant or user. Reporting that there is no "
    "ramp, that the building has stairs, that the accessibility field says No, or that "
    "the acoustics are difficult is not enough on its own, however specific and however "
    "well sourced -- WildSumaco's directory record was both and was still not the "
    "article's real insight. The bar here is INTELLECTUAL, not lexical: access evidence "
    "stays fully usable, and it has to earn the article the same way every other fact "
    "does.\n"
    "  So list in `lens_particulars` the fact ids from your evidence_ids that are "
    "particulars about this subject. Definitions, category statements and background "
    "framing do not belong in that list even when they are the reason you saw the lens. "
    "If NONE of your evidence is a particular, the honest verdict is not a publishable "
    "one -- say WEAK_ANALOGY or GREAT_GENERAL_STORY_WRONG_PUBLICATION and cost nothing.\n"
    "\n"
    "Cite fact ids for everything. You may not use a fact id that is not in the ledger."
)

WORTH_SCHEMA = (
    "Reply with ONE JSON object:\n"
    '{"worth_gate": {"verdict": "...", "lens_claim": "one or two sentences naming the\n'
    '                 mechanism", "changes_meaning_how": "what a reader understands\n'
    '                 differently", "evidence_ids": ["F.."],\n'
    '                 "lens_particulars": ["F.."],   the subset of evidence_ids that\n'
    '                                     are particulars about THIS subject, not\n'
    '                                     definitions or category statements\n'
    '                 "lens_carrier": "the concrete subject-specific fact or tension\n'
    '                                  the reading stands on",\n'
    '                 "can_carry_article": "YES|NO"   can it hold more than one\n'
    '                                     incidental sentence\n'
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
    # THE LENS MUST REST ON A PARTICULAR. Measured on two real ledgers that this gate
    # passed identically: WildSumaco cited ONE disability-bearing fact and published;
    # Meta/neurotech cited TWO and was correctly rejected by the Reader as wrong for the
    # publication. Neither density nor citation count separates them -- 3 facts of 85
    # against 2 of 84, and both verdicts were STRONG_DIRECT_LENS.
    #
    # This gate originally read that pair as particular-vs-definition and taught
    # WildSumaco's ADA record as the model PARTICULAR. That reading was wrong, and the
    # correction (2026-09-06) came from the published article rather than from this file:
    # the record is a US directory's classification of the STATION, the building is in
    # Ecuador, and nothing in the ledger tied the two. Grounding objected on five of seven
    # runs, latterly to the ADJACENCY rather than to any wording -- two accurate sentences
    # placed so a reader draws a third conclusion the sources cannot support. The claim was
    # removed from the live piece. So the prompt above now carries THREE examples, and the
    # third failure mode -- a specific, sourced record about a neighbouring or broader
    # entity, under a framework foreign to the subject -- is named as its own error rather
    # than held up as the standard.
    #
    # The particular requirement itself is UNCHANGED and deliberately not relaxed: a lens
    # still needs >= 1 subject-specific fact it can stand on. What changed is only which
    # facts qualify as subject-specific.
    #
    # The cost of getting this wrong is the whole article: Meta ran nine model calls
    # through Writer, Continuity, Safety, Grounding and Fact Check before anything noticed.
    # Refusing here costs two.
    particulars = [f for f in (lens.get("lens_particulars") or []) if f in ledger]
    stray = sorted(set(lens.get("lens_particulars") or [])
                   - set(lens.get("evidence_ids") or []))
    if stray:
        errs.append("lens_particulars cites facts the lens does not rest on: %s" % stray)
    carrier = str(lens.get("lens_carrier") or "").strip()
    can_carry = str(lens.get("can_carry_article") or "").strip().upper() == "YES"
    # >= 1 PARTICULAR IS NECESSARY AND NOT SUFFICIENT. A particular that gets named once
    # and dropped fails the same way a definition does, only later and after the article
    # has been written. So the gate also asks what the reading STANDS ON and whether that
    # can hold more than an incidental sentence.
    if particulars and not can_carry:
        raise CompositionHold(
            WORTH, WORTH_HOLD,
            ["the lens has subject-specific evidence but it cannot carry the article -- "
             "it would appear as one incidental sentence and the piece would be about "
             "something else",
             ("carrier: " + carrier)[:200] if carrier else "no carrier named",
             (lens.get("lens_claim") or "")[:200]],
            {"lens_particulars": particulars, "lens_carrier": carrier,
             "can_carry_article": lens.get("can_carry_article")})
    if particulars and not carrier:
        raise CompositionHold(
            WORTH, WORTH_HOLD,
            ["the lens names no carrier -- there is no concrete subject-specific fact or "
             "tension the reading stands on",
             (lens.get("lens_claim") or "")[:300]],
            {"lens_particulars": particulars})
    if not particulars:
        raise CompositionHold(
            WORTH, WORTH_HOLD,
            ["the lens rests on no particular about this subject -- every fact it cites "
             "is a definition or a general statement about a category, which can carry a "
             "clause but not an article",
             (lens.get("lens_claim") or "")[:300]],
            {"evidence_ids": lens.get("evidence_ids"),
             "lens_particulars": lens.get("lens_particulars")})

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
    # THE PACKET GATE BELONGS HERE, not after the architecture has been accepted.
    #
    # validate_packet refuses a packet carrying a provenance frame or a scaffold name,
    # and it was only ever run inside writer_packet -- i.e. AFTER check_architecture had
    # passed and the repair budget was spent. So a packet-level defect was terminal, with
    # no path to the repair that could have fixed it in one line. The first fresh-subject
    # run died exactly there: beat B4's `must_not_say_yet` read "Do not yet give the
    # evidence about existing local requirements", the frame fired on "the evidence", and
    # a run that had passed Ledger, Worth, Architecture and CUT could not continue.
    #
    # The gate is unchanged and its acceptance is unchanged. It is the same function on
    # the same packet; it now runs where a repair can still answer it. writer_packet
    # keeps its own call as a final assertion, so nothing can reach the Writer unchecked.
    try:
        errs += ["PACKET: " + e for e in ST.validate_packet(
            ST.build_packet(arch, arch.get("final_lens") or {},
                            LG.propositions(ledger)))]
    except Exception as e:                                        # noqa: BLE001
        errs.append("PACKET: could not be built from this architecture: %s" % e)

    # Optional semantic-ownership representation. The held-out baseline did not carry it,
    # so it is validated where present and never required -- requiring it would be a new
    # architecture feature, which this campaign is explicitly not adding.
    props = arch.get("propositions")
    if isinstance(props, list) and props:
        errs += ["PROPOSITIONS: " + e for e in ST.validate_propositions(props)]
        errs += ["ENDING_RESTATES: " + e
                 for e in ST.validate_ending_does_not_restate(arch, props)]
    return errs


# Two, and the reason is measured rather than chosen. The architecture stage held in
# three of five subscription canary runs, and two of those were legitimate mints its
# single repair could not clear -- a carrier asserting an occurrence, then a turn minting
# a relation. The manual baseline that produced the held-out article needed exactly those
# two repairs, in that order (REPAIR_1 carrier, REPAIR_2 turn). One repair cannot
# reproduce the article this canary exists to reproduce.
#
# THIS IS NOT A VALIDATOR RELAXATION. Acceptance is unchanged: the full architecture
# validator set runs after every repair and nothing reaches the Writer until it passes
# clean. What changes is only how many chances the architect gets to narrow its own
# output, and every chance is judged by the same gate as the first.
MAX_ARCHITECTURE_REPAIRS = 2

REPAIR_ARCH_SYSTEM = (
    "You are repairing a story architecture that failed validation. The exact failures "
    "are given, and the ledger is unchanged.\n"
    "You may NARROW, REORDER or REMOVE, and you may REPLACE an unsupported relation or "
    "carrier with a supported one that is ALREADY AVAILABLE IN THE LEDGER. You may not "
    "add a fact, mint an occurrence or a relation, broaden a proposition, or reach for a "
    "fact id that is not in the ledger. The ledger is frozen and the approved lens does "
    "not change.\n"
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


# ══════════════════════════════════════════════════════════════════════════════
# NON-CLAIM-BEARING VISUAL CONTEXT (Phase 2B)
# ══════════════════════════════════════════════════════════════════════════════
# `visual_observe.py` (Phase 2A) writes VISUAL_OBSERVATIONS.json beside a run when a
# person manually observes source visuals. Until now nothing read it. This is the one
# place that may: the architect chooses the story's ORDER and its CONCRETE OBJECTS, which
# is exactly the work a picture can inform without any fact resting on it.
#
# WHAT REACHES THE ARCHITECT, and nothing else:
#   printed word labels, numeral-free object/material vocabulary, broad spatial
#   relationships, questions_raised, not_established.
#
# WHY THE GUARD IS REAPPLIED HERE, having already run in the utility. The sidecar is a
# FILE ON DISK. It was written by a module with a guard; it can be edited by anything at
# all afterwards, and a consuming stage that trusts an on-disk artifact because the
# producer promised to be careful is trusting a promise, not a check. So every line is
# re-tested at this boundary and a failing line is DROPPED, not repaired. Duplication of
# the rule is the point.
#
# THIS PACKAGE MAY NOT IMPORT `visual_observe`: it carries a system prompt and a
# urllib-based transport, and the architecture stage must not acquire either. The regexes
# below are therefore local and deliberately re-stated.
#
# A PRINTED LABEL IS NOT A POSITION. The key entry "05 GUEST BEDROOM" tells the architect
# that a space is called a guest bedroom. It does not say where that space sits, what
# adjoins it, or how many there are -- so the index is dropped here and only the words
# survive. The Tollymore proof measured why: the model read all eighteen key entries
# correctly and misplaced a courtyard in the same breath.
VISUAL_CONTEXT_OPEN = "<VISUAL_CONTEXT_NON_CLAIM_BEARING>"
VISUAL_CONTEXT_CLOSE = "</VISUAL_CONTEXT_NON_CLAIM_BEARING>"
VISUAL_SIDECAR_NAME = "VISUAL_OBSERVATIONS.json"

MAX_VISUAL_LABELS = 24
MAX_VISUAL_LINES = 8               # per field, across all visuals
MAX_VISUAL_LINE_CHARS = 200
MAX_VISUAL_BLOCK_CHARS = 3_000

_VISUAL_DIGIT_RE = re.compile(r"\d")
_VISUAL_MEASURE_RE = re.compile(
    r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|dozen|half)"
    r"[-\s]+(?:m|mm|cm|km|metres?|meters?|ft|feet|foot|inch(?:es)?|storeys?|stories)\b"
    r"|\bscale\b|\bdimension|\bmeasurement|\blevel\s+heights?\b", re.I)
_VISUAL_REFUSED_RE = re.compile(
    r"\b(?:in)?accessib\w*|\bADA\b|\bcomplian\w*|\bwheelchair\w*|\bstep[-\s]free\b"
    r"|\bonly\s+(?:route|way|entrance|access)\b|\bno\s+(?:other|alternative)\s+"
    r"(?:route|way|entrance|access)\b|\bcannot\s+be\s+(?:reached|entered|accessed)\b"
    r"|\bunreachable\b|\bdangerous\b|\bunsafe\b|\bintended\s+for\b", re.I)
_VISUAL_UNKNOWN_FRAME_RE = re.compile(r"\b(?:whether|if)\b|\bnot\s+established\b", re.I)

# The permission text. It is the whole reason this may be shown at all, so it travels
# INSIDE the delimiters with the material it governs -- a reader of the prompt cannot
# encounter the observations without it.
VISUAL_CONTEXT_PREAMBLE = (
    "THIS IS NON-CLAIM-BEARING VISUAL CONTEXT. A person looked at published source\n"
    "pictures and a utility wrote down what was visible. It is NOT in the ledger, it is\n"
    "NOT evidence, and it is NOT verifiable against the source text.\n"
    "\n"
    "YOU MAY use it to notice a concrete object, to understand a possible spatial\n"
    "sequence, to choose a better order for the story, and to see a question the text\n"
    "evidence ought to answer.\n"
    "\n"
    "YOU MAY NOT make a fact of any of it. Not a fact id, not a carrier's warrant, not a\n"
    "lens particular, not a resolution of anything the ledger leaves open. Every beat\n"
    "still stands on a ledger fact and on nothing else. Do not assert accessibility, that\n"
    "a route is the only one, or any measurement, count or level. If a line here would\n"
    "improve the story only by being true, the story does not get it.\n"
    "\n"
    "PRINTED LABELS say what a space or object is CALLED. They do not say where it sits,\n"
    "what is next to it, or how many there are."
)


def _visual_line_ok(line: str, *, allow_unknown_frame: bool = False) -> bool:
    """True when one observation may be shown to the architect."""
    t = (line or "").strip()
    if not t or len(t) > MAX_VISUAL_LINE_CHARS:
        return False
    if _VISUAL_REFUSED_RE.search(t):
        # An unknown may be NAMED in the shapes the refusal list otherwise catches:
        # "whether this is the only route is not established" is the disclaimer, not the
        # claim, and dropping it would delete the caution while keeping what it qualifies.
        if not (allow_unknown_frame and _VISUAL_UNKNOWN_FRAME_RE.search(t)):
            return False
    if allow_unknown_frame:
        return True
    return not _VISUAL_DIGIT_RE.search(t) and not _VISUAL_MEASURE_RE.search(t)


def _visual_take(observations: list, field: str, *, unknowns: bool = False) -> list:
    out, seen = [], set()
    for o in observations or []:
        for line in (o.get(field) or []):
            t = " ".join(str(line).split())
            if t.lower() in seen or not _visual_line_ok(t, allow_unknown_frame=unknowns):
                continue
            seen.add(t.lower())
            out.append(t)
            if len(out) >= MAX_VISUAL_LINES:
                return out
    return out


def visual_context_block(sidecar: dict) -> str:
    """A sidecar -> the compact delimited block, or "" when nothing survives.

    Deterministic and offline. No model call, no network, no file write.
    """
    if not isinstance(sidecar, dict):
        return ""
    obs = sidecar.get("observations") or []
    labels, seen = [], set()
    for o in obs:
        for l in (o.get("printed_labels") or []):
            # The words only. The index is a position-flavoured identifier and this stage
            # gets no positions.
            w = " ".join(str(l.get("label") or "").split())
            if w and w.lower() not in seen and _visual_line_ok(w):
                seen.add(w.lower())
                labels.append(w)
            if len(labels) >= MAX_VISUAL_LABELS:
                break
    facts = _visual_take(obs, "observable_facts")
    rels = _visual_take(obs, "spatial_relationships")
    qs = _visual_take(obs, "questions_raised")
    unk = _visual_take(obs, "not_established", unknowns=True)
    if not (labels or facts or rels or qs or unk):
        return ""
    L = [VISUAL_CONTEXT_OPEN, VISUAL_CONTEXT_PREAMBLE, ""]
    if labels:
        L += ["PRINTED LABELS (what things are called, not where they are)",
              "  " + " | ".join(labels), ""]
    for title, lines in (("VISIBLE OBJECTS AND MATERIALS", facts),
                         ("BROAD SPATIAL RELATIONSHIPS", rels),
                         ("QUESTIONS THE TEXT EVIDENCE SHOULD ANSWER", qs),
                         ("EXPLICITLY NOT ESTABLISHED", unk)):
        if lines:
            L.append(title)
            L += ["  - " + x for x in lines]
            L.append("")
    L.append(VISUAL_CONTEXT_CLOSE)
    block = "\n".join(L).rstrip()
    if len(block) > MAX_VISUAL_BLOCK_CHARS:
        block = block[:MAX_VISUAL_BLOCK_CHARS].rstrip() + "\n" + VISUAL_CONTEXT_CLOSE
    return block


def load_visual_context(out_dir) -> str:
    """The block for this run, or "" -- which is the ordinary case.

    A missing sidecar, an unreadable one and a malformed one are the same answer: no
    visual context. This may never raise into a run, and it may never be the reason a
    composition holds. Nothing here fetches or observes anything; the file either exists
    because a person made it, or it does not.
    """
    if not out_dir:
        return ""
    import pathlib
    p = pathlib.Path(out_dir) / VISUAL_SIDECAR_NAME
    try:
        if not p.exists():
            return ""
        data = json.loads(p.read_text())
    except Exception:                                                 # noqa: BLE001
        return ""
    if not isinstance(data, dict):
        # Valid JSON is not a valid sidecar. Found by this boundary's own test: a file
        # containing a bare string parsed cleanly and then raised AttributeError into the
        # middle of a composition run, which is the one thing this function may not do.
        return ""
    if data.get("status") != "NON_CLAIM_BEARING":
        # The producer stamps this. An artifact that does not declare itself
        # non-claim-bearing is not the artifact this boundary agreed to read.
        return ""
    return visual_context_block(data)


def architect(provider, ledger: dict, worth: dict, subject: str,
              visual_context: str = "") -> dict:
    """STAGE 3. Ledger plus an approved lens in; a validated architecture out.

    `visual_context` is the optional non-claim-bearing block from
    `load_visual_context`. When it is "" -- the ordinary case, and every case before
    Phase 2B -- the prompt this stage sends is byte-identical to what it sent before the
    parameter existed. There is no other difference: no extra call, no schema change, and
    no reader of this block anywhere else in the pipeline.
    """
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
    if visual_context:
        # Appended, never interleaved: the ledger keeps its position as the last word on
        # what exists, and an empty block leaves `user` exactly as it was.
        user = user + "\n\n" + visual_context

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
             "model_calls": calls, "repairs": repairs,
             "visual_context_chars": len(visual_context)})

    # Each repair sees the CURRENT invalid architecture and the failures it actually has
    # now -- not the original ones -- so repair 2 answers repair 1's output rather than
    # re-answering a question that has already been partly fixed.
    idents = {"architect": ident}
    history = []
    first_errs = list(errs)
    while errs and repairs < MAX_ARCHITECTURE_REPAIRS:
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
        # `ru` deliberately carries NO visual context. A repair exists to narrow an
        # architecture back onto the ledger; handing it fresh non-evidential material at
        # exactly that moment is how a repair becomes a second draft.
        nxt, ident_r = _ask(provider, REPAIR_ARCH_SYSTEM, ru, 8_000, ARCHITECTURE,
                            ARCHITECTURE_HOLD)
        calls += 1
        repairs += 1
        idents["repair_%d" % repairs] = ident_r
        history.append({"attempt": repairs, "failure_count": len(errs),
                        "failures_answered": errs[:10]})
        obj = nxt
        # The full validator set, again, after every repair. Acceptance never moves.
        errs = check_architecture(obj, ledger)

    if errs:
        raise CompositionHold(
            ARCHITECTURE, ARCHITECTURE_HOLD,
            ["still invalid after %d repair(s) of a maximum %d (%d failure(s))"
             % (repairs, MAX_ARCHITECTURE_REPAIRS, len(errs))] + errs[:10],
            {"architecture": obj, "failures": errs,
             "failures_at_first_attempt": first_errs, "repair_history": history,
             "provider": idents, "model_calls": calls, "repairs": repairs,
             "repair_budget": MAX_ARCHITECTURE_REPAIRS})

    return {"status": PASS, "architecture": obj, "provider": idents,
            "model_calls": calls, "repairs": repairs,
            "repair_budget": MAX_ARCHITECTURE_REPAIRS,
            "repair_history": history,
            "failures_at_first_attempt": first_errs,
            # Observability, on the stage payload only: ARCHITECTURE.json is still the
            # architecture object and nothing else, so no artifact shape moves.
            "visual_context_chars": len(visual_context),
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
# THE LICENSING RULE, and the specificity rule beside it.
#
# A CUT fact's words are only a betrayal if (a) nothing the Writer was handed already
# licenses them, and (b) they actually identify that fact. The first canary to reach the
# safety stage failed on (b): the derivation emitted `change`, `moves`, `form`, `tell`,
# `There`, `Another`, `visual`, `real`, `unit`, `figure` as sentinels, and reported 26 CUT
# violations on prose that had leaked nothing. Ordinary English cannot betray a fact. The
# manual baseline's hand-picked terms were `photogrammetry`, `quantile`, `Lyft`, `12.15`,
# `Idle Hands` -- words that belong to one fact and nothing else.
#
# So specificity is measured, not guessed at from a stop list, and measured against the
# ledger itself: a term appearing in many propositions identifies none of them. Document
# frequency needs no vocabulary of English and cannot go stale.
CUT_TERMS_PER_FACT = 6
CUT_TERM_MIN = ST.CUT_SENTINEL_MIN

# A term in more than this many ledger propositions is not a sentinel for any of them.
CUT_TERM_MAX_DF = 2
# Below this length, a lowercase single word is almost always ordinary English. Proper
# nouns and numbers are exempt: "Lyft" is four characters and identifies one fact.
CUT_TERM_DISTINCTIVE_LEN = 7
# A prefix match counts as a morphological relation only if the two forms differ by at
# most this many characters -- the length of an inflectional suffix. Chosen against the
# cases, not guessed:
#     bike / bikes                  1   accept
#     override / overrides          1   accept
#     continuous / continuously     2   accept
#     corresponding/correspondingly 2   accept
#     down / download               4   REJECT -- a spelling coincidence, not morphology
#     specific / specifications     6   REJECT
# An earlier attempt used a floor on the SHORTER form instead. It rejected down/download
# correctly and then also rejected bike/bikes, because "bike" is four characters. The
# difference is the signal; the absolute length is not.
LICENSE_MORPH_DIFF = 3

# Ordinary English, which cannot betray a fact whatever its frequency in this corpus.
#
# A word list is used here after measuring the two alternatives and finding both unable to
# do the job. Document frequency over the ledger gives `reached` df=0 -- it came from a
# span, not a proposition -- and cannot separate `without` (df 1) from `inflate` (df 1),
# which the manual baseline wanted. Term frequency over the source corpus is worse: on
# 3,633 words it scores `tell` 1, `change` 2 and `real` 1 while scoring the WANTED
# `download` 18 and `project` 12. The knowledge that separates them is simply which words
# are ordinary English, so that is what is written down. It is used alongside the
# frequency rules, not instead of them.
_COMMON_ENGLISH = {ST._stem(w) for w in """
about above across after again against almost along already also although always among
amount another answer anyone appear applied apply approach area around arrive arrived
available based become becomes began begin behind being believe below best better between
beyond both bring brought build built called cannot capacity carried carry case cause
caused certain change changed changes clear close collect come coming common complete
consider contain continue could country course create created current currently decide
decided describe described design detail determine determined develop developed
difference different difficult direct directly during each early effect either enough
entering entire especially even event every example except exist expect experience
explain fact factor fall family feature figure final finally find first follow following
force form forms found four full further future general generally give given going great
greater group grow half hand happen hard have having help high higher hold holds however
important include included includes including increase increased increases indeed inside
instead into issue itself just keep kept kind know known large larger last late later
lead least leave left less level light like likely limit line little live local long
longer look lower made main major make makes making many matter mean means measure might
model more most move moves moving much must name near need needed never next none normal
note nothing notice number numerous occur offer often only open option options order
other others outside over part particular pass past people perhaps period person place
plan point possible present press pressure probably problem process produce program
programs provide provided public push question quite range rate rather reach reached real
really reason receive received recent record reduce refer regard relate remain report
require required result return right rise room rule same second section seem seen sense
series serve service set several shall short should show shown side simple simply since
single site situation size small some sort space special specific stand start state still
stop study subject such support suppose sure system systems take taken talk tell term
than that their them then there these they thing think this those though three through
time today together took total toward turn type under understand unit units unless until
upon used useful using usual usually value various very view visual want water well were
what when where whether which while whole will with within without work would year
because project correspond corresponding correspondingly across
continuous continuously contiguous
channel channels surface surfaces edge edges layer layers band bands frame frames
field fields ground grounds body bodies scale scales weight weights measure measures
reading readings signal signals pattern patterns picture pictures window windows
account accounts figure figures margin margins register registers record records
release releases pressure pressures distance distances position positions angle angles
range ranges gradient gradients threshold thresholds standard standards
condition conditions quality qualities property properties feature features
element elements object objects material materials structure structures
version versions method methods practice practices sector sectors
resistance instrument instruments device devices display displays
""".split()} | {ST._stem(w) for w in ST._FUNCTION_WORDS}

_WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9.,'-]*")
_NUMBERISH = re.compile(r"\d")
# A term that IS a number, as opposed to one that merely contains a digit. "ESP32S3" is a
# part name and belongs on the word path: sent down the number path it could never match,
# because ST._numbers does not read it as a number either.
_PURE_NUMBER = re.compile(r"^[$\u00a3\u20ac]?\d[\d,.:/-]*%?$")
_PROPER = re.compile(r"\b[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]+)*\b")


def _stems(text: str) -> set:
    return {ST._stem(w) for w in re.findall(r"[a-z0-9]+", (text or "").lower())}


def _words(text: str) -> set:
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def _licensed_by(term: str, words: set, numbers: set | None = None) -> bool:
    """Is `term` a morphological variant of a word the packet already carries?

    STEM EQUALITY CANNOT ANSWER THIS, and three canary runs died proving it. story.py's
    `_stem` is a suffix stripper, not a canonicaliser, so two variants of one word can
    stem differently:

        packet "overrides"      -> "overrid"        candidate "override"      -> "override"
        packet "correspondingly"-> "correspondingly" candidate "corresponding" -> "correspond"
        packet "continuously"   -> "continuously"   candidate "continuous"    -> "continuou"

    Every one of those pairs is the same word and every one failed an equality test, so
    the CUT audit watched vocabulary the Writer had been handed and reported leaks on
    prose that leaked nothing.

    Prefix containment answers it in both directions: a candidate is licensed if a packet
    word extends its root, or if the candidate extends a packet word's root. `_stem` is
    still used to find the roots -- the merged inflection logic is unchanged -- it is
    only the COMPARISON that stops being equality.

    This trades a little sensitivity for correctness, and knowingly: an unrelated packet
    word sharing a four-character root would license a term it should not, costing a
    sentinel. That direction loses a watch rather than inventing a violation, which is
    the right way round for a screen whose false positives block real articles.
    """
    # A NUMBER HAS NO MORPHOLOGY. It is licensed by its exact appearance and by nothing
    # else: prefix logic would make "2020" unlicensable under a length floor while also
    # letting "20" license "2024".
    #
    # AND IT MUST BE EXTRACTED THE SAME WAY ON BOTH SIDES. Candidates come from
    # ST._numbers, which reads "$12.15" as one token; `words` came from a [a-z0-9]+ scan,
    # which splits it into "12" and "15". So a decimal could never match, and the CUT
    # audit reported "$12.15" as leaked from cut F100 while USED fact F15 -- "A 45-minute
    # e-bike ride could cost a Citi Bike member $12.15" -- was sitting in the Writer's
    # own packet granting it. Same extractor on both sides, or the comparison is between
    # two different things.
    if _PURE_NUMBER.match(term.strip()):
        return term.strip().lower() in (numbers or set())
    roots = {r for r in ({term.lower()} | _stems(term)) if len(r) >= CUT_TERM_MIN}
    for w in words:
        for r in roots:
            if abs(len(w) - len(r)) > LICENSE_MORPH_DIFF:
                continue
            if w.startswith(r) or r.startswith(w):
                return True
    return False


def _document_frequency(ledger: dict) -> dict:
    """stem -> how many ledger propositions contain it."""
    df: dict[str, int] = {}
    for f in (ledger or {}).values():
        for s in _stems(f.get("proposition") or ""):
            df[s] = df.get(s, 0) + 1
    return df


def _is_distinctive(term: str, df: dict) -> bool:
    t = term.strip()
    if _PURE_NUMBER.match(t):
        return True                                  # a figure belongs to its fact
    if _ALNUM_ID.match(t):
        return True                                  # a part name belongs to its fact,
                                                     # and "ESP32" is five characters
    # ORDINARY ENGLISH FIRST, before the proper-noun shortcut. A capitalised word at the
    # start of a sentence looks exactly like a name to a regex: the canary watched
    # "Across" as a sentinel for F71 and duly reported a violation on the word "Across".
    # A single ordinary word is never a name, however it is capitalised.
    if " " not in t and _stems(t) & _COMMON_ENGLISH:
        return False
    if _PROPER.fullmatch(t):
        return True                                  # a name belongs to its fact
    if " " not in t and len(t) < CUT_TERM_DISTINCTIVE_LEN:
        return False                                 # short and lowercase: ordinary
    return max((df.get(s, 0) for s in _stems(t)), default=0) <= CUT_TERM_MAX_DF


# ── CUT CONFIDENCE TIERS ─────────────────────────────────────────────────────
# Single-token lexical CUT detection has a precision ceiling, established over five
# downstream replays on one frozen architecture. Each produced a different collision
# between a cut fact's word and an unrelated sense of the same word in the prose:
#
#   channel     cut: "a curved rear channel" (a groove)
#               art: "the usual channels" (media)
#   assembled   cut: "the assembled device"
#               art: "torque assembled out of what a survey published" (metaphor)
#
# No frequency measure separates these -- both senses are equally rare in the corpus --
# and a hand-maintained allowlist cannot be closed by enumeration.
#
# So a term is tiered by its SHAPE, which is decidable, rather than by a judgement about
# its senses, which is not. HIGH-confidence shapes are fact-bearing and cannot plausibly
# be sense collisions: a figure, an alphanumeric part name, a proper noun, a multi-word
# phrase. A bare everyday token cannot HOLD an article by itself.
#
# WHAT STILL CATCHES AN ACTUAL EXCLUDED FACT: the factual-surface audit on numbers and
# entities, the negative-admission gate, the occurrence and relation validators, the
# authoritative Grounder and the authoritative Fact Check. CUT was never the only
# control, and it is the weakest of them on ambiguous vocabulary.
CUT_HIGH = "HIGH"
CUT_LOW = "LOW"

# Advisory kinds. A low-confidence lexical hit is surfaced, never silently discarded, and
# travels to the Reader and the human review that can read a sense rather than a string.
CUT_ADVISORY = "CUT_ADVISORY"
SPATIAL_ADVISORY = "SPATIAL_ADVISORY"
SCENE_ADVISORY = "SCENE_ADVISORY"

_WHY_ADVISORY = ("the only evidence is the token itself, and a single lexical match "
                 "cannot decide a physical sense from an abstract one; structural "
                 "safety still holds this sentence if it violates a hard contract")


def _sentence_containing(text: str, token: str) -> str:
    """The article sentence a token appears in, so an advisory is readable."""
    low = token.lower()
    for s in CE.sentences(text):
        if low in s.lower():
            return s.strip()
    return ""

_ALNUM_ID = re.compile(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z0-9][A-Za-z0-9.\-/]*$")
# The same shape, found inside running text.
_IDENTIFIER = re.compile(
    r"\b(?=[A-Za-z0-9\-]*[A-Za-z])(?=[A-Za-z0-9\-]*\d)[A-Za-z][A-Za-z0-9\-]{2,}\b")


def cut_term_confidence(term: str) -> str:
    """HIGH if the term's shape is fact-bearing; LOW if it is a bare everyday token."""
    s = (term or "").strip()
    if not s:
        return CUT_LOW
    if " " in s:
        return CUT_HIGH                      # a distinctive multi-word phrase
    if _PURE_NUMBER.match(s):
        return CUT_HIGH                      # a figure, price or date
    if _ALNUM_ID.match(s):
        return CUT_HIGH                      # an identifier or part name
    if _PROPER.fullmatch(s) and not (_stems(s) & _COMMON_ENGLISH):
        return CUT_HIGH                      # a named entity, product or tool
    return CUT_LOW


def _candidate_terms(fact: dict) -> list:
    """Concrete words a cut fact would betray itself by: its numbers, its named entities,
    then its longest content words. Ordered most to least specific."""
    text = "%s %s" % (fact.get("proposition") or "", fact.get("support_span") or "")
    out, seen = [], set()

    def push(t):
        t = (t or "").strip(" .,;:'\"")
        key = t.lower()
        if t and key not in seen and len(key) >= CUT_TERM_MIN:
            seen.add(key)
            out.append(t)

    for n in sorted(ST._numbers(text), key=len, reverse=True):
        push(n)
    # ALPHANUMERIC IDENTIFIERS AND PART NAMES. Extracted explicitly because nothing else
    # here reaches them: ST._numbers wants digits only, _PROPER wants an initial capital
    # followed by lower-case, and the content-word scan excludes digits. So "ESP32S3" was
    # never a candidate at all, and a part name is exactly the high-confidence shape a
    # CUT sentinel is for.
    for m in sorted(set(_IDENTIFIER.findall(text)), key=len, reverse=True):
        push(m)
    for m in sorted(set(_PROPER.findall(text)), key=len, reverse=True):
        push(m)                                      # multi-word names first
    for w in (fact.get("entities") or []):
        push(str(w))
    for w in sorted(set(re.findall(r"[A-Za-z][A-Za-z-]{4,}", text)), key=len, reverse=True):
        push(w)
    return out


def derive_cut_watch_terms(arch: dict, ledger: dict) -> dict:
    """STAGE 4. {cut_fact_id: [watch terms]} plus a coverage report.

    Deterministic and model-free. Every declared CUT fact gets an entry, so
    `cut_adherence` can never silently watch nothing, and any cut fact for which no term
    survives licensing is REPORTED rather than dropped.
    """
    # Licensed by everything the WRITER WAS ACTUALLY HANDED, not merely by the used
    # propositions: the packet also carries beat text, carriers, definitions and
    # prohibitions, and a word in any of them is language the Writer was given. Rendering
    # it here is deterministic and free.
    try:
        packet_text = ST.render(ST.build_packet(
            arch, arch.get("final_lens") or {}, LG.propositions(ledger)))
    except Exception:                                             # noqa: BLE001
        packet_text = " ".join((ledger.get(f) or {}).get("proposition") or ""
                               for f in (arch.get("use_facts") or []))
    licensed_words = _words(packet_text)
    licensed_numbers = {n.strip().lower() for n in ST._numbers(packet_text)}
    packet_norm = normalize_span(packet_text)
    df = _document_frequency(ledger)

    terms: dict[str, list] = {}
    unlicensed_only, missing, dropped = [], [], {}
    for c in (arch.get("cut_evidence") or []):
        cid = c.get("evidence_id")
        fact = ledger.get(cid)
        if cid is None:
            continue
        terms[cid] = []
        if not fact:
            missing.append(cid)
            continue
        kept, rejected = [], []
        for cand in _candidate_terms(fact):
            # A MULTI-WORD TERM IS LICENSED ONLY AS A PHRASE. Checking its words
            # separately licensed "Idle Hands" because the packet happened to contain
            # both words elsewhere -- and a name is exactly the thing a phrase, not its
            # parts, identifies.
            if (normalize_span(cand) in packet_norm if " " in cand.strip()
                    else _licensed_by(cand, licensed_words, licensed_numbers)):
                rejected.append((cand, "licensed by the packet"))
                continue
            if not _is_distinctive(cand, df):
                rejected.append((cand, "not specific to this fact"))
                continue
            kept.append(cand)
            if len(kept) >= CUT_TERMS_PER_FACT:
                break
        terms[cid] = kept
        if rejected:
            dropped[cid] = rejected[:8]
        if not kept:
            unlicensed_only.append(cid)

    high = {cid: [x for x in v if cut_term_confidence(x) == CUT_HIGH]
            for cid, v in terms.items()}
    report = {
        "terms": terms,
        "high_confidence_terms": {k: v for k, v in high.items() if v},
        "confidence": {x: cut_term_confidence(x)
                       for v in terms.values() for x in v},
        "prohibitions": compile_cut_prohibitions(arch, ledger, terms),
        "cut_declared": len(arch.get("cut_evidence") or []),
        "cut_with_terms": sum(1 for v in terms.values() if v),
        "cut_without_distinctive_terms": sorted(unlicensed_only),
        "candidates_dropped": dropped,
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


# ── CUT COMPILED INTO PROHIBITIONS ───────────────────────────────────────────
# The packet already carries the architect's own prohibitions and a CUT list, and the
# Writer still named a circuit board, Reality Capture and an override -- all from facts
# the architecture had CUT. The CUT decision was in the packet as a count, not as
# something the Writer could act on.
#
# So the cut material is compiled into explicit prohibitions. Deterministically, with no
# model call, and with no article-specific sentence written by hand: the CATEGORY WORDING
# below is generic and fixed, while WHICH categories appear comes only from the cut facts
# themselves.
#
# The licensing rule is preserved exactly as the CUT audit applies it: a category is
# emitted only for a cut fact that still has at least one surviving watch term, and a
# term survives only if the packet does not license it. So a cut fact whose whole
# vocabulary the Writer was legitimately handed produces no prohibition, and cannot.
#
# Categories are matched on the cut fact's own proposition and span. This is a classifier
# over cut material, not a vocabulary ban on the article: nothing here forbids a word the
# packet grants.
# The wording is RELATIVE, not absolute, and that is the whole design.
#
# An absolute "Do not name electronic components" contradicted the packet: the run-D
# architecture USED a components fact, so the Writer was handed the ESP32S3, the PCB and
# the GPS module and told not to name them. A prohibition that argues with the approved
# material suppresses licensed detail and teaches the Writer to discount the rules.
#
# Suppressing such a category instead was tried and is worse: the markers are broad
# enough that a rich packet touches every one, and it silenced all six prohibitions on
# run D -- including the two that demonstrably stopped "circuit" and "Reality Capture".
#
# So each line forbids EXPANSION BEYOND the approved facts. USED material stays fully
# available, the boundary is stated without naming what lies past it, and exact
# enforcement stays with the deterministic post-Writer audit. No cut number, name,
# quotation or proposition appears here, so the Writer is never handed a forbidden value
# merely to be told not to repeat it.
CUT_CATEGORIES = [
    (("microcontroller", "servo", "circuit", "board", "module", "sensor", "gps", "oled",
      "sd card", "wiring", "enclosure", "solder", "3d print", "printer", "firmware",
      "battery", "motor", "chassis"),
     "Do not add electronic components, hardware or assembly detail beyond what the "
     "article facts above explicitly approve."),
    (("software", "app ", "package", "library", "toolkit", "photogrammetry", "scan",
      "capture", "render", "model file", "mesh", "geometry", "specification",
      "download", "repository", "code"),
     "Do not name software, tools, file formats or technical specifications beyond those "
     "the article facts above explicitly approve, and do not add detail about how the "
     "work was produced."),
    (("award", "grant", "funded", "funding", "prize", "fellowship", "residency",
      "commission", "sponsor", "donation"),
     "Do not add funders, awards, prizes or sums of money beyond what the article facts "
     "above explicitly approve."),
    (("price", "prices", "fee", "membership", "subscription", "cost", "revenue",
      "owned", "operated", "acquisition", "shareholder", "company", "corporation"),
     "Do not add prices, fees, membership costs, ownership or commercial arrangements "
     "beyond what the article facts above explicitly approve."),
    (("quantile", "margin of error", "sample", "weighting", "estimate period",
      "correction", "inflate", "standard error", "confidence", "methodology"),
     "Do not add detail about statistical method, sampling, weighting or margins of "
     "error beyond what the article facts above explicitly approve."),
    (("hopes", "plans", "intends", "other cities", "replicate", "roll out", "expand",
      "future", "next version"),
     "Do not add plans, future intentions or replication elsewhere beyond what the "
     "article facts above explicitly approve."),
    (("interview", "told", "spokesperson", "statement", "press", "newsroom",
      "publication", "reporter", "podcast", "broadcast"),
     "Do not add reporting, interviews, outlets or attributions of who said something "
     "to whom beyond what the article facts above explicitly approve."),
]


def compile_cut_prohibitions(arch: dict, ledger: dict, terms: dict) -> list:
    """Generic prohibitions whose CONTENT comes only from the cut facts.

    One line per category actually present in the cut material, deduplicated and in a
    fixed order so the packet is stable across runs. Nothing article-specific is written
    here and no model is asked anything.
    """
    out = []
    for markers, sentence in CUT_CATEGORIES:
        for c in (arch.get("cut_evidence") or []):
            cid = c.get("evidence_id")
            # Only a cut fact that still HAS a sentinel: if every candidate term was
            # licensed by the packet, the Writer was handed that vocabulary legitimately
            # and there is nothing to forbid.
            if not (terms or {}).get(cid):
                continue
            f = (ledger or {}).get(cid) or {}
            hay = ("%s %s" % (f.get("proposition") or "",
                              f.get("support_span") or "")).lower()
            if any(m in hay for m in markers):
                out.append(sentence)
                break
    return out


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


# ── NEGATIVE PROVENANCE ───────────────────────────────────────────────────────
# WHY THIS EXISTS. `negative_admission_audit` pairs a negative-shaped sentence with an
# approved negative fact by WORD OVERLAP, and its threshold scales with the FACT's
# length: it needs max(2, len(key)//3) of the fact's content words. So a faithful but
# NARROWER sentence can never match enough. Measured on the Ground Truth canary:
#
#   fact F59  NEGATIVE_EXISTENCE  "The rent burden measure says nothing about
#                                  homeowners, and nothing about people with no housing
#                                  at all, who are by construction absent from a survey
#                                  of households."   -> 9 key words, needs 3
#   prose                         "It says nothing about homeowners."
#                                                    -> supplies 1
#
# The prose is a correct rendering of the fact's first clause and the audit cannot see
# it. That is a defect of lexical matching, not of the article.
#
# The fix is PROVENANCE, not semantics. The Writer -- the only stage that turns a
# permission into a sentence -- declares which negative fact each negative sentence
# rests on, and the machine then verifies every constraint mechanically. A declaration
# is a claim about ORIGIN. It never makes unsupported content valid.
#
# PROVENANCE FLOWS FORWARD ONLY. A Continuity edit may inherit its parent's verified
# declaration; it may never mint one, and a declaration can never be inferred backwards
# from a later model edit onto the prose that preceded it. If Continuity output is
# discarded, its inheritance is discarded with it and only the Writer's own verified
# lineage applies. Nothing here reads a fact id from Continuity at all -- the strongest
# available form of that guarantee.
def label_sentences(article_text: str) -> dict:
    """S001.. over the article. Deterministic, and the ids the Writer must refer to."""
    return {"S%03d" % (i + 1): s
            for i, s in enumerate(CE.sentences(article_text))}


def attributed_negative_is_explicit(f: dict | None) -> bool:
    """Does this fact's FROZEN proposition AND its VERBATIM support span both state the
    negative?

    WHY THIS EXISTS (owner-directed, 2026-09-10). `claim_type` describes the FORM of a
    claim; whether its content is negative is a different dimension. An attributed
    negative -- "<source> states that there is no X" -- is typed ATTRIBUTION, so the
    permission compiler excluded it while the Architecture was simultaneously REQUIRING
    the Writer to state it.

    Retained production proof, production-20260910T073435Z-703b7b90 (pediatric mTBI):
    Architecture beat B2 instructs "Add the field's own stated position ... there is no
    objective clinical biomarker ..."; F39's frozen proposition and frozen support span
    both say exactly that; F39 is in `use_facts`; F39 is typed ATTRIBUTION; the rendered
    permission block lists only F13 and says "Nothing else." The run died on
    UNSUPPORTED_NEGATIVES. Two instructions that cannot both be satisfied, and no repair
    or recomposition can reconcile them because both come from frozen upstream.

    THIS ADMITS NO NEW EVIDENCE. The fact must already be SELECTED by the architecture,
    its frozen proposition must state the negative, and its verbatim source span must
    state it INDEPENDENTLY -- a proposition that resolves an ambiguous source into a
    negative the span does not carry stays refused. The shape test is
    story.negative_shape_of(), the SAME single owner the UNSUPPORTED_NEGATIVES audit uses
    to decide a sentence is negative, so a permission and the audit enforcing it cannot
    disagree about what a negative is. Writer lineage, entity, number and relation checks
    are all untouched.
    """
    prop = str((f or {}).get("proposition") or "")
    span = str((f or {}).get("support_span") or "")
    if not prop.strip() or not span.strip():
        return False
    return bool(ST.negative_shape_of(prop)[0]) and bool(ST.negative_shape_of(span)[0])


def negative_permissions(arch: dict, ledger: dict) -> dict:
    """The negative facts the architecture actually USES, by id.

    Only these ids are admissible in a declaration, and every one of their propositions
    is already in the packet as a used fact, so naming them exposes no new evidence.

    Admitted on either of two grounds: the fact's own claim_type is a recognised negative
    type, or it is an ATTRIBUTED negative whose frozen proposition and frozen support span
    both explicitly state it -- see attributed_negative_is_explicit().
    """
    use = set(arch.get("use_facts") or [])
    return {fid: f.get("proposition", "")
            for fid, f in (ledger or {}).items()
            if fid in use and (f.get("claim_type") in LG.NEGATIVE_TYPES
                               or attributed_negative_is_explicit(f))}


def verify_negative_lineage(article_text: str, declared, ledger: dict, packet: dict,
                            allowed_ids: set) -> tuple:
    """Which declarations survive machine verification, and why the others do not.

    Returns ({sentence_id: [fact_ids]}, [rejections]). Every check is deterministic and
    reuses a merged validator; none of them asks a model anything.
    """
    sentences = label_sentences(article_text)
    approved = ST.render(packet)
    a_words = ST._content_words(approved, fold=True)
    a_nums, a_ents = ST._numbers(approved), ST._entities(approved,
                                                         skip_sentence_initial=False)
    verified, rejected = {}, []

    for d in (declared or []):
        if not isinstance(d, dict):
            rejected.append({"declaration": str(d)[:80], "why": "not an object"})
            continue
        sid = str(d.get("sentence_id") or "").strip()
        fids = [str(f).strip() for f in (d.get("fact_ids") or [])]
        text = sentences.get(sid)
        if not text:
            rejected.append({"sentence_id": sid, "why": "no such sentence in the article"})
            continue
        bad = []
        for fid in fids:
            if fid not in ledger:
                bad.append("%s is not in the ledger" % fid)
            elif fid not in allowed_ids:
                # Either not a negative claim type, or not a fact the architecture used.
                ct = (ledger[fid] or {}).get("claim_type")
                bad.append("%s is %s, not an approved negative the architecture uses"
                           % (fid, ct))
        if not fids:
            bad.append("no fact_ids declared")
        if bad:
            rejected.append({"sentence_id": sid, "sentence": text[:120], "why": bad})
            continue

        # The negative RELATION comes from the fact. Every other relation the sentence
        # asserts must also be one the licensing facts assert -- the merged check.
        rel = ST.validate_turn_support(text, fids, ledger)
        # The rest of the sentence must stay packet-licensed: no new number, no new
        # entity, no unapproved sensory, scene or spatial assertion.
        nums = sorted(ST._numbers(text) - a_nums)
        ents = sorted(ST._entities(text) - a_ents)
        terms = ST._content_words(text) - a_words
        hard = sorted(x for x in terms
                      if x in ST.SENSORY_RISK or x in ST.SCENE_RISK
                      or x in ST.SPATIAL_RISK)
        if rel or nums or ents or hard:
            rejected.append({
                "sentence_id": sid, "sentence": text[:120], "fact_ids": fids,
                "why": (["relation the licensing facts do not assert: %s"
                         % [e["relation"] for e in rel]] if rel else [])
                       + (["new number(s) %s" % nums] if nums else [])
                       + (["new entit(y/ies) %s" % ents] if ents else [])
                       + (["unapproved concrete material %s" % hard] if hard else [])})
            continue
        verified[sid] = fids
    return verified, rejected


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
    + "\n\nOUTPUT. Reply with ONE JSON object:\n"
      '{"article": "the finished article as markdown: a single # title line, then the\n'
      "            prose. No front matter, no notes to the editor, no headings inside\n"
      '            the body, no commentary about what you did.",\n'
      ' "negative_lineage": [{"sentence_id": "S007", "fact_ids": ["F59"]}]}\n'
      "\n"
      "ABOUT negative_lineage. If you write a sentence that says something does NOT "
      "happen, does not exist, is not measured, is absent, is the only one or is the "
      "first -- name the approved permission it rests on. The permissions are listed "
      "below with their ids; only those ids are admissible, and only for a sentence that "
      "genuinely makes that negative claim.\n"
      "  Number your own sentences S001, S002, ... in reading order, counting every "
      "sentence of the article body from the start, and give the id of the sentence "
      "making the claim.\n"
      "  This is a statement about where a sentence came from. It licenses nothing else: "
      "the rest of the sentence must still contain no number, name or concrete detail "
      "that is not already above, and no relation the permission does not carry. If you "
      "have no negative sentences, return an empty list.\n"
      "  Do not write a negative claim you cannot point at a permission for. There is no "
      "permission for silence."
)


# Not a length policy. A reply below this is not an article at all, and BRIEF is a real
# article_type whose length this gate must not second-guess.
WRITER_MIN_WORDS = 50


# ══════════════════════════════════════════════════════════════════════════════
# SAFE RECOMPOSE -- the second and last composition (owner-directed, 2026-09-10)
# ══════════════════════════════════════════════════════════════════════════════
# WHY. Worth-PASS stories were dying on their own prose: one causal escalation, one
# status label the ledger never granted, one "separate experiment" that invented a second
# experiment -- and the whole composition was terminal. The remedy is NOT a longer chain
# of local repairs on that prose. A night batch spent five repair proposals on one draft,
# accepted one, and still held; the retained evidence could not even say whether the
# repairs were bad or the gate simply read differently the second time. Local repair had
# reached its useful end, and the only remaining lever was the owner arbitrating wording
# by hand, which is exactly what must never be required.
#
# So: throw the draft away and write the article ONCE more, from the SAME frozen
# authority, with a conservative factual hand. Two compositions per Worth-PASS story, no
# third.
#
# THIS LOWERS NO STANDARD. It is a WRITING contract, not a gate. Every downstream gate
# runs on B exactly as it ran on A, and B has the identical Ledger authority A had -- it
# may not create a fact, retrieve evidence, or widen a permission. House style is
# untouched: PROSE_DOCTRINE and WRITER_CRAFT_DELTA are both still in force, because a
# safe article is still a Crip Minds article and not a fact sheet.
COMPOSE_NORMAL = "NORMAL"
COMPOSE_SAFE_RECOMPOSE = "SAFE_RECOMPOSE"

SAFE_RECOMPOSE_DELTA = (
    "\n\nCONSERVATIVE FACTUAL HAND. This is the second and final composition of a story "
    "whose first draft was refused by the factual gates. You are not repairing that "
    "draft: you have not been shown it, and you are not meant to be. Write the article "
    "again from the packet above.\n"
    "  Everything above about HOW to write still holds, without exception. Difficult "
    "ideas, very easy reading. Find the story carrying the idea. Concrete people, events "
    "and objects carry the abstraction. One hard concept at a time. Calm, natural, "
    "book-like prose. Do NOT write notes, a fact sheet, an abstract, an academic summary "
    "or deliberately flattened prose -- a cautious article is not a dull one, and "
    "caution is not an excuse for bad writing.\n"
    "  What changes is the factual hand. Every assertion must be one the packet already "
    "carries. Where the packet is thinner than the sentence you would like to write, "
    "write the thinner sentence. Plain factual description beats interpretive flourish, "
    "every time.\n"
    "  Do not add factual strength for prose energy. Specifically, do not write any of "
    "the following unless the packet states it outright:\n"
    "    - a cause, or a stronger cause than the packet gives\n"
    "    - proved, showed that, demonstrated, confirmed, established\n"
    "    - first, only, leading, major, separate, unprecedented\n"
    "    - an expertise, seniority or status label for a person\n"
    "    - an institutional relationship, affiliation or group membership\n"
    "    - an order of events, or one event happening because of another\n"
    "    - a motive, an intention or a belief\n"
    "    - a named classification or category the packet does not name\n"
    "    - a comparison between two studies, measurements or cases\n"
    "    - a universal claim (all, every, always, none, never)\n"
    "    - a negative claim without its listed permission\n"
    "  Three worked refusals, so the shape is unmistakable. \"researchers argued X\" does "
    "not become \"researchers working on X argued\" -- that invents a research programme. "
    "\"a bodily response\" does not become \"proof that it worked\" -- that invents a "
    "conclusion. \"one experiment\" does not become \"a separate experiment\" -- that "
    "invents a second experiment.\n"
    "  If the packet cannot support a sentence, omit it or narrow it. An article that says "
    "less and is true is finished. An article that says more than its evidence carries is "
    "not an article yet."
)

# The same contract as the normal Writer, plus the conservative hand. Built by
# concatenation rather than rewritten, so the two can never drift apart.
WRITER_SYSTEM_SAFE_RECOMPOSE = WRITER_SYSTEM + SAFE_RECOMPOSE_DELTA

COMPOSE_SYSTEMS = {COMPOSE_NORMAL: WRITER_SYSTEM,
                   COMPOSE_SAFE_RECOMPOSE: WRITER_SYSTEM_SAFE_RECOMPOSE}


def negative_permissions_block(perms: dict) -> str:
    """The only place a fact id is shown to the Writer, and only for negatives.

    The packet itself still carries no ids -- ids are machine identity and prose has no
    use for them. These exist so a negative sentence can NAME its permission, and every
    proposition here is already in the packet as a used fact.
    """
    if not perms:
        return ("\n\nNEGATIVE PERMISSIONS\n  None. Do not write any sentence saying "
                "that something does not happen, does not exist or is absent.\n")
    L = ["", "", "NEGATIVE PERMISSIONS -- the only negatives you may write, by id"]
    for fid, prop in sorted(perms.items()):
        L.append("  %s  %s" % (fid, prop))
    L.append("  Nothing else. A negative claim with no id here has no permission.")
    return "\n".join(L) + "\n"


def writer_packet(arch: dict, ledger: dict, cut_prohibitions=None) -> tuple:
    """The packet and its rendered prompt. Refused if it carries the auditing frame.

    `cut_prohibitions` are the compiled CUT lines, added to the architect's own so that
    `render()` turns them into imperatives alongside everything else. They are appended
    rather than merged into the architecture: the architecture is a record of what the
    architect decided, and this is a deterministic consequence of its CUT list.
    """
    if cut_prohibitions:
        arch = dict(arch, prohibitions=list(arch.get("prohibitions") or [])
                    + [p for p in cut_prohibitions
                       if p not in (arch.get("prohibitions") or [])])
    packet = ST.build_packet(arch, arch.get("final_lens") or {},
                             LG.propositions(ledger))
    errs = ST.validate_packet(packet)
    if errs:
        raise CompositionHold(WRITER, WRITER_HOLD,
                              ["the writer packet is not clean"] + errs)
    perms = negative_permissions(arch, ledger)
    return packet, ST.render(packet) + negative_permissions_block(perms)


def _clean_article(text: str) -> str:
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.split("```")[1] if "```" in t[3:] else t[3:]
        if t.lower().startswith("markdown"):
            t = t[8:]
    return t.strip()


def write_article(provider, arch: dict, ledger: dict, cut_prohibitions=None,
                  compose_mode: str = COMPOSE_NORMAL) -> dict:
    """STAGE 5. ONE Writer call. A retry only when the output is mechanically unusable.

    `compose_mode` selects the writing contract and NOTHING else: the packet, the
    permissions, the validators and every downstream gate are identical in both modes.
    An unknown mode is refused rather than silently written normally -- fail-closed, the
    same as every other guard here.
    """
    if compose_mode not in COMPOSE_SYSTEMS:
        raise CompositionHold(WRITER, WRITER_HOLD,
                              ["unknown compose_mode %r" % compose_mode])
    system = COMPOSE_SYSTEMS[compose_mode]
    packet, prompt = writer_packet(arch, ledger, cut_prohibitions)
    perms = negative_permissions(arch, ledger)
    last = ""
    for attempt in (1, 2):
        try:
            comp = provider.complete(system=system, user=prompt,
                                     max_tokens=8_000)
        except Exception as e:
            if _is_subscription_limit(e):
                raise CompositionHold(WRITER, CLAUDE_SUBSCRIPTION_LIMIT,
                                      ["the Claude subscription cannot serve this call: "
                                       "%s" % str(e)[:300],
                                       "stopping; no paid fallback was attempted"])
            if not isinstance(e, ProviderError) and type(e).__name__ != "ClaudeCLIError":
                raise
            raise CompositionHold(WRITER, WRITER_HOLD, ["provider unavailable: %s" % e])
        try:
            obj = parse_json_object(comp.text)
            article = _clean_article(obj.get("article") or "")
            declared = obj.get("negative_lineage")
        except ProviderError as e:
            article, declared, obj = "", None, {}
            last = "reply was not one JSON object (%s)" % e
        # Mechanically unusable, not "not good enough": empty, missing its title line, or
        # too short to be prose at all. The floor is deliberately very low, because BRIEF
        # is a legitimate article_type and a length judgement is not this gate's business
        # -- it exists to catch a reply that is not an article, not a reply that is a
        # short one. There is no quality-regeneration loop here.
        if len(article.split()) >= WRITER_MIN_WORDS and article.lstrip().startswith("#"):
            verified, rejected = verify_negative_lineage(
                article, declared, ledger, packet, set(perms))
            return {"status": PASS, "article_text": article, "packet": packet,
                    "compose_mode": compose_mode,
                    "prompt": prompt, "prompt_sha256": C.sha256_text(prompt),
                    "provider": _identity(comp, attempt),
                    "model_calls": attempt, "repairs": 0,
                    "words": len(article.split()),
                    "negative_permissions": sorted(perms),
                    "negative_lineage_declared": declared or [],
                    "negative_lineage_verified": verified,
                    "negative_lineage_rejected": rejected}
        if not last:
            last = ("empty reply" if not article else
                    "%d words, title line %s"
                    % (len(article.split()),
                       "present" if article.lstrip().startswith("#") else "missing"))
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


def carry_negative_lineage(edits: list, draft_text: str, final_text: str,
                           writer_verified: dict) -> dict:
    """Inherit the Writer's verified declarations onto the edited descendants.

    FORWARD ONLY. An output sentence inherits its PARENTS' verified provenance and
    nothing else. Continuity cannot mint a declaration -- no fact id is ever read from
    its reply, which is the strongest form of that guarantee -- and nothing flows
    backwards onto the draft.

    The caller applies this only when the edit passed the zero-factual-freedom delta
    checks; a discarded edit inherits nothing, because it does not exist.
    """
    draft_ids = label_sentences(draft_text)          # D-order == S-order, both from
    final_ids = label_sentences(final_text)          # CE.sentences over the body
    # Writer ids are over the draft; Continuity parents are CE.label_draft ids, which
    # enumerate the same sentences in the same order. Map one to the other by position.
    draft_labels = CE.label_draft(draft_text)
    pos_of = {did: i for i, did in enumerate(sorted(draft_labels))}
    writer_by_pos = {}
    for sid, fids in (writer_verified or {}).items():
        try:
            writer_by_pos[int(sid[1:]) - 1] = fids
        except ValueError:
            continue

    out, seen = {}, 0
    for e in edits:
        if e.get("operation") == CE.DELETE:
            continue
        seen += 1
        inherited = []
        for parent in (e.get("parents") or []):
            i = pos_of.get(parent)
            if i is not None:
                inherited += writer_by_pos.get(i, [])
        if inherited:
            # The nth surviving edit is the nth sentence of the rendered output only when
            # each edit contributes exactly one sentence, which is the contract; where it
            # does not, the id simply fails to resolve and the sentence keeps no
            # provenance. Failing closed is correct: an unresolved inheritance must not
            # license anything.
            sid = "S%03d" % seen
            if sid in final_ids:
                out[sid] = sorted(set(inherited))
    return out


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
# ── THE PUBLICATION BUNDLE ───────────────────────────────────────────────────
# The package is not metadata. A title, a dek and a homepage card are the first prose a
# reader meets, they are quoted onward by search engines and social clients, and they can
# be wrong in exactly the way an article can be wrong -- not by using a word that is not
# in the evidence, but by putting two words the evidence does grant into a relation it
# never asserted. A station-level accessibility record becomes a claim about a building; an
# adjacency becomes a contradiction; a hedge becomes a finding.
#
# So the unit that is checked is the whole thing a reader will see:
#
#     PUBLICATION_BUNDLE = article + title + dek + excerpt + meta description + hook
#
# and it is checked by the gates that already exist, on one delimited text, rather than by
# a second factual pipeline built for metadata. What the surfaces below buy is diagnosis: a
# finding says DEK or TITLE instead of "the article", so the failure is actionable.
ARTICLE_SURFACE = "ARTICLE"
PACKAGE_SURFACE_LABELS = (("title", "TITLE"), ("dek", "DEK"),
                          ("homepage_excerpt", "EXCERPT"),
                          ("meta_description", "META_DESCRIPTION"),
                          ("social_hook", "SOCIAL_HOOK"))
PACKAGE_SURFACES = tuple(label for _, label in PACKAGE_SURFACE_LABELS)

BUNDLE_HEADER = (
    "THE PUBLICATION FURNITURE -- the title, standfirst and cards this article is "
    "published behind. This is public editorial prose, read before the article and often "
    "instead of it, and it is checked exactly like the article: every claim in it has to "
    "be carried by the same evidence.")


# ── TITLE CASE IS TYPOGRAPHY, NOT ENTITY EVIDENCE ────────────────────────────────────
# `ST._entities` reads a capital as a name, which is fair in running prose and worthless
# in a title, where convention capitalises every content word. On 2026-09-07 the title
# "One Room, Two Acoustics, Convertible in a Day" held a finished article by reporting
# "Acoustics" and "Convertible" as unapproved ENTITIES. Both are ordinary vocabulary and
# both claims were supported (F11, F14, F15).
#
# The demotion below is narrow on purpose. It does not license anything: a token it
# demotes is still reported as an unapproved TERM, which the audit's own note calls "a
# candidate for review, not a violation". What it removes is the token's standing in the
# HARD entity channel, and only when three things all hold -- every package field the
# token appears in is title-cased, the token carries no shape signal of its own, and it
# is a single word.
#
# WHAT STILL BLOCKS. A shaped name in a title ("A24", "MoMA", "U.S.", an all-caps
# acronym) has evidence beyond its capital and keeps it. Any name in the dek, excerpt,
# meta description or hook is in sentence case, where a mid-sentence capital IS evidence,
# and is untouched by this. Multi-word names keep the phrase test.
#
# WHAT THIS KNOWINGLY GIVES UP: a bare alphabetic invented name appearing ONLY in the
# title, and nowhere in the packet, article or ledger, is no longer caught by this
# lexical channel. Typography cannot separate that case from "Convertible" -- a rule that
# forgives one forgives the other -- so it is left to the Grounder and the Fact Check,
# which read the package inside the bundle. Recorded rather than hidden.
_TITLE_MINOR = frozenset("""a an the and but or nor for so yet at by in of on to up via
with from into onto over per as is it its this that than then when if not no""".split())
_SHAPE_SIGNAL = re.compile(r"\d|[a-z][A-Z]|\.")


def _is_title_cased(line: str) -> bool:
    """Is this line written in title case? Judged on content words only, so that the
    lowercase minor words a real title carries ("in a Day") do not defeat the test."""
    toks = re.findall(r"[A-Za-z][A-Za-z'\u2019]*", line or "")
    content = [t for t in toks if t.lower() not in _TITLE_MINOR]
    if len(content) < 3:
        return False
    caps = sum(1 for t in content if t[0].isupper())
    return caps >= max(2, round(0.8 * len(content)))


def _has_shape_signal(tok: str) -> bool:
    """Evidence of a name that does NOT come from being capitalised: a digit, an internal
    capital, an embedded period, or an all-caps acronym."""
    t = (tok or "").strip()
    return bool(_SHAPE_SIGNAL.search(t)) or (len(t) >= 2 and t.isupper())


def _title_case_only_token(tok: str, package: dict | None) -> bool:
    """True when every package field carrying `tok` is title-cased and the token itself
    offers no evidence of being a name beyond that capital."""
    t = (tok or "").strip()
    if not t or " " in t or _has_shape_signal(t):
        return False
    fields = [str((package or {}).get(f) or "") for f, _ in PACKAGE_SURFACE_LABELS]
    carrying = [v for v in fields
                if re.search(r"(?<![A-Za-z0-9])%s(?![A-Za-z0-9])" % re.escape(t), v)]
    return bool(carrying) and all(_is_title_cased(v) for v in carrying)


def package_prose(package: dict | None) -> str:
    """The package's five lines as one plain text, or "" when there is no package."""
    if not package:
        return ""
    lines = []
    for field, label in PACKAGE_SURFACE_LABELS:
        v = str((package or {}).get(field) or "").strip()
        if v:
            lines.append(v)
    return "\n\n".join(lines)


def bundle_text(article_text: str, package: dict | None) -> str:
    """The exact public surface, in one text, delimited so a grounder reads the furniture
    as sentences to check rather than as part of the article's argument."""
    if not package:
        return article_text or ""
    block = "\n".join("%s: %s" % (label, str(package.get(field) or "").strip())
                      for field, label in PACKAGE_SURFACE_LABELS
                      if str(package.get(field) or "").strip())
    return "%s\n\n---\n\n%s\n\n%s\n" % ((article_text or "").rstrip(),
                                        BUNDLE_HEADER, block)


def surface_of(text: str, package: dict | None) -> str:
    """Which surface does this quote come from? ARTICLE unless a package line carries it."""
    q = normalize_span(text or "")
    if not q or not package:
        return ARTICLE_SURFACE
    for field, label in PACKAGE_SURFACE_LABELS:
        v = normalize_span(str(package.get(field) or ""))
        # Long enough to be a quotation rather than a coincidence, in either direction: a
        # grounder may quote a whole dek or a clause of one.
        if len(v) >= 12 and len(q) >= 12 and (q in v or v in q):
            return label
    return ARTICLE_SURFACE


def surfaces_carrying(package: dict | None, tokens) -> list:
    """The surfaces that contain any of these tokens, for a diagnostic line."""
    out = []
    for field, label in PACKAGE_SURFACE_LABELS:
        v = normalize_span(str((package or {}).get(field) or "")).lower()
        if v and any(re.search(r"\b%s\b" % re.escape(normalize_span(str(t)).lower()), v)
                     for t in tokens if len(str(t).strip()) > 1):
            out.append(label)
    return out or ["PACKAGE"]


def split_by_surface(findings, package: dict | None) -> tuple:
    """(article findings, package findings), each stamped with its surface."""
    art, pkg = [], []
    for f in findings or []:
        if not isinstance(f, dict):
            art.append(f)
            continue
        where = surface_of(f.get("quote") or f.get("claim") or f.get("claim_text") or "",
                           package)
        f = dict(f, surface=where)
        (art if where == ARTICLE_SURFACE else pkg).append(f)
    return art, pkg


# ══════════════════════════════════════════════════════════════════════════════
# Every merged screen, on the finished candidate. A failure HOLDS. It does not regenerate
# the Writer: an article that invented something is evidence about the run, and rerolling
# it destroys that evidence and buys a second draft with an unknown defect.
def safety_audit(draft_text: str, final_text: str, packet: dict, arch: dict,
                 ledger: dict, cut_terms: dict, cut_report: dict | None = None,
                 negative_lineage: dict | None = None,
                 repair: dict | None = None, package: dict | None = None) -> dict:
    """The merged post-writer stack, on both the draft and the final."""
    # AFTER A FACTUAL REPAIR THE BASELINES MOVE, and getting that wrong made the repair
    # unpassable. The repair's authority comes from the LEDGER FACTS IT CITED and from the
    # grounder finding that authorised it -- not from the packet, and not from the
    # pre-repair prose. Audited against the old baselines, an authorised correction reads
    # twice as an invention: once as unapproved surface, once as the editor adding
    # material the editor never touched.
    #
    # So the approved surface gains what the accepted edits cited, and the relation
    # classes those edits introduced are passed to validate_semantic_delta's own
    # allow_relation_growth -- the parameter that exists for exactly this. Every one of
    # them was already checked per edit, against its cited facts, by the repair guard.
    # Nothing else moves: the CUT audit, the negative gate and the machine-language
    # screen are unchanged, and a repair that touched nothing changes no baseline at all.
    repair_text, allow_rel = "", ()
    if repair:
        cited = {f for e in (repair.get("edits") or []) for f in (e.get("fact_ids") or [])}
        repair_text = " ".join(
            "%s %s" % ((ledger.get(f) or {}).get("proposition", ""),
                       (ledger.get(f) or {}).get("support_span", "")) for f in cited)
        allow_rel = tuple({k for e in (repair.get("edits") or [])
                           for k in CE.relations(e.get("repaired") or "")})

    approved_render = ST.render(packet) + " " + repair_text
    approved_entities = ST._entities(approved_render, skip_sentence_initial=False)

    def _possessive_of_approved(e: str) -> bool:
        """"Survey's" is not a new entity when the packet grants "Survey".

        The merged audit compares capitalised tokens, so a possessive reads as an
        addition. It adds no factual surface -- the noun is approved and the apostrophe
        is grammar -- and the first canary to reach this stage was held by exactly this,
        on a packet containing "Survey" six times. Only the possessive is forgiven;
        every other unapproved entity still blocks.
        """
        base = re.sub(r"['\u2019]s$", "", e)
        return base != e and base in approved_entities

    def screens(text):
        surface = ST.factual_surface_audit(text, packet)
        if repair_text:
            lic_n, lic_e = _numbers_of(repair_text), ST._entities(
                repair_text, skip_sentence_initial=False)
            lic_w = ST._content_words(repair_text, fold=True)
            surface = dict(
                surface,
                unapproved_numbers=[x for x in surface["unapproved_numbers"]
                                    if x not in lic_n],
                unapproved_entities=[x for x in surface["unapproved_entities"]
                                     if x not in lic_e],
                unapproved_sensory=[x for x in surface["unapproved_sensory"]
                                    if x not in lic_w])
        ents = [e for e in surface["unapproved_entities"]
                if not _possessive_of_approved(e)]
        # SCENE AND SPATIAL TOKENS ARE ADVISORY. A bare word cannot decide its own sense:
        # "upper limit" is a range, not a storey, and the canary was held by exactly that
        # while the packet licensed the idea. Numbers, named entities and SENSORY
        # assertions stay HARD -- a colour the evidence never mentions is the "pink"
        # incident, and there is no abstract reading of it.
        surface = dict(surface,
                       unapproved_entities=ents,
                       possessives_forgiven=[e for e in surface["unapproved_entities"]
                                             if _possessive_of_approved(e)],
                       advisory_scene=list(surface["unapproved_scene"]),
                       advisory_spatial=list(surface["unapproved_spatial"]),
                       hard_ok=not (surface["unapproved_numbers"] or ents
                                    or surface["unapproved_sensory"]))
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
    # THE PACKAGE IS PUBLIC PROSE and is screened by the same functions, on its own text.
    # It is a third surface, not part of the article: the semantic delta below compares the
    # draft with the final and a title has no draft to differ from. What it does share is
    # every screen that asks whether prose carries factual surface the evidence never
    # granted -- which is the only question a title can get wrong.
    pkg_text = package_prose(package)
    if pkg_text:
        ps = screens(pkg_text)
        # WHAT THE PACKAGE IS ALLOWED TO USE is the packet AND the article, because the
        # article has already passed this same screen -- a word the prose was cleared to
        # print cannot be an invention when a dek repeats it. Case is ignored here and
        # only here: a title is title-cased and a packet is not, so "The Upper Room" would
        # otherwise report three unapproved entities on every article ever published.
        #
        # What survives this filter is the thing that matters: a NAME OR NUMBER THAT IS
        # NOWHERE, which is the one addition a five-line package can make lexically. The
        # additions it makes by RELATION -- adjacency sold as cause, a station's record
        # sold as a building's -- are invisible to any word-level screen and are caught by
        # the Grounder and the Fact Check, which read the package inside the bundle.
        # TITLE CASE IS TYPOGRAPHY, NOT ENTITY EVIDENCE (2026-09-07).
        #
        # `_entities` reads a capital as a name. In running prose that is a fair
        # heuristic; in a TITLE, where every content word is capitalised by convention,
        # it is no evidence at all. On 2026-09-07 the title
        #
        #     "One Room, Two Acoustics, Convertible in a Day"
        #
        # held a finished article by reporting two unapproved ENTITIES, "Acoustics" and
        # "Convertible" -- an ordinary noun and an ordinary adjective, and both claims
        # supported (F11, F14, F15).
        #
        # The instinct is to make the detector title-aware, and typography cannot do it:
        # a rule that forgives a bare capitalised word in a title forgives an invented
        # "Rockefeller Foundation" in exactly the same breath. What separates the two is
        # not how they are printed but whether the run's own evidence carries them. So
        # the licence, and only the licence, is widened along two axes it should always
        # have had:
        #
        #   MORPHOLOGY. `_licensed_by` already exists for this and its docstring is about
        #   this exact failure -- stem equality cannot see that "acoustic" and
        #   "Acoustics" are one word. Exact substring matching could not either.
        #
        #   THE LEDGER. The packet is a curated subset of the ledger, and a title is
        #   written from the settled article and the run's facts. "conversion" is an
        #   approved fact in this very run (F11, F15); "Convertible" being absent from
        #   the writer's subset of it does not make the word an invention.
        #
        # A NAME THAT IS NOWHERE IS STILL A NAME THAT IS NOWHERE. Nothing here forgives a
        # token the packet, the article and the ledger all lack, which is the one
        # addition a five-line package can lexically make. Multi-word names keep their
        # phrase check below. The relation-level additions -- adjacency sold as cause, a
        # station's record sold as a building's -- remain invisible to any word-level
        # screen and remain the Grounder's and the Fact Check's, which read the package
        # inside the bundle.
        ledger_text = " ".join(
            "%s %s" % (str((v or {}).get("proposition", "")),
                       str((v or {}).get("support_span", "")))
            for v in (ledger or {}).values() if isinstance(v, dict))
        licensed = (approved_render + " " + final_text + " " + ledger_text).lower()
        licensed_pkg_words = _words(licensed)
        licensed_pkg_numbers = {n.strip().lower() for n in ST._numbers(licensed)}

        def _pkg_licensed(tok) -> bool:
            base = re.sub(r"['\u2019]s$", "", str(tok)).strip()
            if not base:
                return True
            if base.lower() in licensed:
                return True
            if " " in base:                 # a name is identified by the phrase, not its
                return False                # parts -- unchanged from the exact test
            return _licensed_by(base, licensed_pkg_words, licensed_pkg_numbers)

        sf = ps["factual_surface"]
        ents = [e for e in sf["unapproved_entities"]
                if not _pkg_licensed(e) and not _title_case_only_token(e, package)]
        nums = [n for n in sf["unapproved_numbers"] if n not in _numbers_of(final_text)]
        sens = [t for t in sf["unapproved_sensory"] if not _pkg_licensed(t)]
        ps["factual_surface"] = dict(sf, unapproved_entities=ents,
                                     unapproved_numbers=nums, unapproved_sensory=sens)
        ps["hard_factual_ok"] = not (ents or nums or sens)
        # A negative the ARTICLE already carries is not a new negative when the dek
        # repeats it; one the article does not carry has to be licensed by the ledger like
        # any other, and nothing declared provenance for a title.
        art_norm = normalize_span(final_text)
        ps["negative_admission"] = dict(
            ps["negative_admission"],
            unmatched=[h for h in ps["negative_admission"]["unmatched"]
                       if normalize_span(h["sentence"]) not in art_norm])
        a["publication_package"] = ps
    f = a["continuity_final"]
    delta_errs = CE.validate_semantic_delta(draft_text, final_text,
                                            allow_relation_growth=allow_rel)
    if repair_text:
        # Surface the repair introduced from its cited facts is not the editor adding
        # material; it is the correction the grounder asked for.
        lic_n = _numbers_of(repair_text)
        lic_e = ST._entities(repair_text, skip_sentence_initial=False)
        delta_errs = [e for e in delta_errs
                      if not (("added numbers" in e and all(
                                  x.strip("[]' ") in lic_n
                                  for x in e.split(":")[-1].strip(" []").split(",")))
                              or ("added entities" in e and all(
                                  x.strip("[]' ") in lic_e
                                  for x in e.split(":")[-1].strip(" []").split(","))))]

    blocking = []
    if not f["hard_factual_ok"]:
        s = f["factual_surface"]
        blocking.append(
            "NEW_UNSUPPORTED_FACTS: the final prose carries factual surface the packet "
            "never granted -- numbers=%s entities=%s sensory=%s"
            % (s["unapproved_numbers"], s["unapproved_entities"],
               s["unapproved_sensory"]))
    # THE LEXICAL AUDIT IS THE FAST PATH. Anything it already licenses passes without
    # provenance being consulted at all. Only what it CANNOT see -- a faithful sentence
    # narrower than the fact it renders -- may be admitted by a verified Writer
    # declaration, and that declaration has already had every constraint checked
    # mechanically. See verify_negative_lineage.
    admitted, unadmitted = [], []
    by_id = label_sentences(final_text)
    lineage = negative_lineage or {}
    for h in f["negative_admission"]["unmatched"]:
        sent = " ".join(h["sentence"].split())
        sid = next((k for k, v in by_id.items()
                    if " ".join(v.split()) == sent), None)
        fids = lineage.get(sid) if sid else None
        if fids:
            admitted.append({"sentence_id": sid, "sentence": h["sentence"][:120],
                             "fact_ids": fids})
        else:
            unadmitted.append(h)
    if unadmitted:
        blocking.append(
            "UNSUPPORTED_NEGATIVES: %d negative-shaped sentence(s) with no negative fact "
            "behind them: %s"
            % (len(unadmitted), [h["sentence"][:90] for h in unadmitted][:4]))
    # Only a HIGH-confidence shape blocks. A bare everyday token that happens to occur
    # in a cut fact is recorded as telemetry and settled by the controls that can read a
    # claim rather than a string.
    viol = f["cut_adherence"]["violations"]
    hard = [v for v in viol if cut_term_confidence(v["term"]) == CUT_HIGH]
    soft = [v for v in viol if cut_term_confidence(v["term"]) != CUT_HIGH]
    if hard:
        blocking.append(
            "CUT_LEAKAGE: %s"
            % [(v["evidence_id"], v["term"], v["match"]) for v in hard][:6])
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
    # The CUT audit reporting a blind spot is a derivation bug, EXCEPT where the
    # derivation already explains it. A cut fact whose every candidate term was either
    # licensed by the packet or ordinary English has nothing that could betray it: the
    # article is entitled to those words whether the fact was cut or not, and watching
    # them is what produced 26 false positives on prose that had leaked nothing. So an
    # EXPLAINED empty entry is telemetry; an unexplained missing entry still blocks,
    # because that is the state in which the audit reports clean prose without looking.
    ca = f["cut_adherence"]
    explained = set((cut_report or {}).get("cut_without_distinctive_terms") or [])
    unexplained = [c for c in ca["cut_without_watch_terms"] if c not in explained]
    if unexplained or ca["skipped_too_short"]:
        blocking.append(
            "CUT_AUDIT_BLIND: cut facts with no watch term and no reason given %s; "
            "terms below the length floor %s -- the audit would report clean prose "
            "without having looked" % (unexplained, ca["skipped_too_short"]))

    # THE PACKAGE'S OWN FAILURES, named by the surface they are on, so a hold reads
    # "DEK" rather than "the article" and the owner knows which line to look at. The
    # negative gate is applied without lineage: nothing declared provenance for a title,
    # so a negative-shaped dek must be licensed by a negative fact in the ledger or not
    # written at all.
    if pkg_text:
        ps = a["publication_package"]
        if not ps["hard_factual_ok"]:
            sf = ps["factual_surface"]
            blocking.append(
                "PACKAGE_UNSUPPORTED_FACTS on %s: numbers=%s entities=%s sensory=%s"
                % (surfaces_carrying(package, sf["unapproved_numbers"]
                                     + sf["unapproved_entities"]
                                     + list(sf["unapproved_sensory"])),
                   sf["unapproved_numbers"], sf["unapproved_entities"],
                   sf["unapproved_sensory"]))
        un = ps["negative_admission"]["unmatched"]
        if un:
            blocking.append(
                "PACKAGE_UNSUPPORTED_NEGATIVES on %s: %s"
                % (surfaces_carrying(package, [h["sentence"] for h in un]),
                   [h["sentence"][:90] for h in un][:3]))
        phard = [v for v in ps["cut_adherence"]["violations"]
                 if cut_term_confidence(v["term"]) == CUT_HIGH]
        if phard:
            blocking.append(
                "PACKAGE_CUT_LEAKAGE on %s: %s"
                % (surfaces_carrying(package, [v["term"] for v in phard]),
                   [(v["evidence_id"], v["term"]) for v in phard][:4]))
        if not ps["prose_leaks"]["ok"] or not ps["scaffold"]["ok"]:
            blocking.append("PACKAGE_MACHINE_LANGUAGE: frames %s, scaffold %s"
                            % (ps["prose_leaks"]["frames"], ps["scaffold"]["leaked"]))

    # ── ADVISORIES, surfaced and never discarded ─────────────────────────────
    advisories = []
    for v in soft:
        advisories.append({
            "kind": CUT_ADVISORY, "token": v["term"],
            "sentence": _sentence_containing(final_text, v["term"]),
            "rule": "cut fact %s (%s), matched %s"
                    % (v["evidence_id"], v.get("reason"), v.get("match")),
            "why_not_hard": _WHY_ADVISORY})
    for tok in f["factual_surface"].get("advisory_spatial") or []:
        advisories.append({
            "kind": SPATIAL_ADVISORY, "token": tok,
            "sentence": _sentence_containing(final_text, tok),
            "rule": "story.SPATIAL_RISK",
            "why_not_hard": _WHY_ADVISORY})
    for tok in f["factual_surface"].get("advisory_scene") or []:
        advisories.append({
            "kind": SCENE_ADVISORY, "token": tok,
            "sentence": _sentence_containing(final_text, tok),
            "rule": "story.SCENE_RISK",
            "why_not_hard": _WHY_ADVISORY})

    return {"status": HOLD if blocking else PASS,
            "blocking": blocking,
            "audits": a,
            "cut_terms_without_a_sentinel": sorted(explained),
            "advisories": advisories,
            "negatives_admitted_by_provenance": admitted,
            "negatives_licensed_lexically":
                f["negative_admission"]["negative_sentences"]
                - len(f["negative_admission"]["unmatched"]),
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
                     pack: dict, arch: dict | None = None,
                     packet: dict | None = None) -> dict:
    """STAGE 8. The authoritative Grounder, called unmodified.

    `stages.ground` is the same function the legacy path runs, with the same arguments:
    the article, the anchor source and the pack. It never sees the architecture or the
    ledger -- grounding asks whether the PROSE is carried by the SOURCES, and handing it
    the machine's own approval record is how a grounder starts agreeing with the engine.
    """
    try:
        # The grounder is shown the same amount of each source the LEDGER was frozen
        # from. Anything less and it reports the shortfall as unsupported prose -- which
        # it did, and said so, on the first canary run to reach this stage.
        gf = S.ground(provider, article_text, source_text, source_sha, pack,
                      per_source_chars=FREEZE_SOURCE_CHARS)
    except Exception as e:
        if _is_subscription_limit(e):
            raise CompositionHold(GROUNDING, CLAUDE_SUBSCRIPTION_LIMIT,
                                  ["the Claude subscription cannot serve this call: %s"
                                   % str(e)[:300],
                                   "stopping; no paid fallback was attempted"])
        if not isinstance(e, ProviderError) and type(e).__name__ != "ClaudeCLIError":
            raise
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

    # ADJUDICATING A DEFINITIONAL GLOSS, deterministically, through the escape hatch
    # decision.py already provides for exactly this ("TRUE_UNCERTAIN ... not
    # adjudicated; V0 policy is HOLD").
    #
    # The architecture may declare `definitions`, and `render()` instructs the Writer to
    # EXPLAIN AT FIRST USE. The Grounder does not see the architecture -- by design -- so
    # it meets a sentence like "A servo is a small motor that turns to a commanded angle
    # and holds there." and correctly reports that the sources do not establish it. They
    # do not: it is a general-knowledge gloss the packet asked for, not a claim about
    # this subject. Left unadjudicated it blocks every run whose architecture uses a
    # definition, which is a packet feature the architect is expected to use.
    #
    # THE BOUNDS ARE TIGHT. Only TRUE_UNCERTAIN is eligible -- never TRUE_UNSUPPORTED.
    # The flagged sentence must name a term the architecture actually declared, and it
    # must add no factual surface the packet does not already carry, which is the same
    # test factual_surface_audit applies. Anything else still blocks.
    defs = {k.lower() for k in ((arch or {}).get("definitions") or {})}
    approved_words = ST._content_words(ST.render(packet), fold=True) if packet else set()
    adjudicated = []
    if defs and approved_words:
        for f in uncertain:
            q = str(f.get("quote") or "")
            if not q.strip():
                continue
            names_a_defined_term = any(
                term in " ".join(q.lower().split()) for term in defs)
            adds_surface = bool(ST._content_words(q) - approved_words) \
                or bool(ST._numbers(q) - ST._numbers(ST.render(packet))) \
                or bool(ST._entities(q) - ST._entities(ST.render(packet),
                                                       skip_sentence_initial=False))
            if names_a_defined_term and not adds_surface:
                adjudicated.append({"id": f.get("id"), "quote": q[:160],
                                    "why": "a gloss on a term the architecture declared "
                                           "in `definitions`, adding no factual surface "
                                           "the packet does not carry"})

    adjudicated_ids = {a["id"] for a in adjudicated}
    blocking = list(unsupported)
    if not gf.get("uncertain_adjudicated", False):
        blocking += [f for f in uncertain if f.get("id") not in adjudicated_ids]
    settled = gf.get("status") == "settled"
    return {"status": PASS if (settled and not blocking) else HOLD,
            "grounding": {k: v for k, v in gf.items() if k != "_provider"},
            "findings": findings,
            "unsupported": unsupported,
            "uncertain": uncertain,
            "uncertain_adjudicated_as_definitions": adjudicated,
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
# STAGE 8b -- ONE GROUNDED FACTUAL REPAIR
# ══════════════════════════════════════════════════════════════════════════════
# WHY. Two independent fresh subjects reproduced the same failure class: every
# deterministic screen passed and the Grounder still found genuine over-reach.
#
#   "Where M4(3) does appear in the final framework, it is in Policy HO9"
#       -- an exclusivity the same source refutes
#   "Yellow is the single label under which a tool a student needs can be allowed"
#       -- green permits it too
#   a minister's draft-consultation quote placed in the present tense beside final policy
#   "confident mistakes called hallucinations" where the source says only "can make mistakes"
#
# The deterministic screens cover added SURFACE -- a number, a name, a colour. They do not
# cover added SCOPE, and "X is the single Y" is an exclusivity assertion in positive shape,
# so negative_claim_scan never sees it. The Grounder does. So the Grounder is the semantic
# authority for this repair; nothing new is built to detect the class.
#
# THE REPAIR SUBTRACTS. It may delete unsupported scope, narrow a claim, remove an
# exclusivity, correct a tense or an ambiguous date, restore attribution, replace an
# unsupported characterisation with the supported wording, or delete the sentence. It may
# not add a fact, source, entity, occurrence or relation, broaden scope, strengthen
# certainty, or improve style anywhere else.
#
# AND IT REQUIRES THE REPAIR TO BE COMPLETE (2026-09-07, second finding). The repair is
# a single pass with no retry, so a flagged claim the model fixes in one place and leaves
# standing in another is simply not repaired. That is not a hypothetical:
# production-20260907T173433Z-ab65bb22 made the Grade I "exceptional interest" gloss
# twice, in different words; the repair cut the quoted sentence and left the other, and
# Grounding held the article on the claim it had just corrected. The same run edited the
# sentence holding a second flagged phrase -- removing a different phrase from it -- and
# left the flagged one in place.
#
# Nothing mechanical needed changing for this. `apply_grounding_repair` already accepts
# several edits carrying the same finding_id, applies each in order, and computes
# findings_left_unanswered as a set difference, so duplicates neither break it nor
# double-count. `repair_prompt` already hands the model the entire article. The model was
# simply never told the claim might appear twice, and the schema example showed one edit
# per finding.
#
# THE PROMPT NOW NAMES EVERY RELATION THE CHECK MEASURES (2026-09-07). Production run
# production-20260907T154937Z-8556915b was lost at exactly this seam: the article reached
# Grounding, the repair was attempted, and the validator refused it because
#
#     edit 1 ADDS relations=['EQUIVALENCE']    (cited facts F27, F25 carry neither)
#     edit 2 ADDS relations=['GENERALIZATION'] (cited facts F18, F54 carry neither)
#
# The check reads nine relation classes out of story.TURN_RELATION_SHAPES. The prompt
# warned about four of them. EQUIVALENCE was one of the four and the model did it anyway;
# GENERALIZATION was not warned about at all, and neither were NEGATION, ABSENCE or the
# superlative. An instruction that lists a subset of what the machine refuses is teaching
# the model a different contract from the one it is graded on, so the list below is now
# the same nine classes with the same trigger words, and generalisation -- retreating from
# one unsupported specific to a safe-sounding general case -- gets its own paragraph
# because it is the one that reads as caution while being an enlargement.
#
# Nothing about the validator, the permissions or the one-repair budget changes here.
# This is the instruction catching up with the check.
REPAIR_GROUNDING_SYSTEM = (
    "You are removing specific factual over-reach from a finished article. A grounder has "
    "named the exact passages and said what the evidence does and does not carry. The "
    "evidence is frozen and is the same evidence the article was written from.\n"
    "\n"
    "YOU ARE AN EXCISING EDITOR, NOT A WRITER. You take words OUT of a sentence that is "
    "already there. You do not compose a better sentence and put it back. This is the "
    "whole contract, and every rule below follows from it.\n"
    "\n"
    "PREFER DELETION OVER REPLACEMENT. In order: cut the offending words and leave the "
    "rest of the sentence untouched; if that will not do, cut the clause; if that will "
    "not do, delete the sentence. Re-writing the sentence around the problem is the one "
    "move that is never available.\n"
    "\n"
    "COPY `original` VERBATIM. Character for character from the article, including "
    "punctuation and capitalisation. Do not summarise the passage, do not tidy it, do not "
    "quote the grounder's description of it. An `original` that is not found in the "
    "article word for word is refused and the finding goes unanswered.\n"
    "\n"
    "THE REPAIRED SENTENCE MUST BE WEAKER THAN THE ORIGINAL, NEVER STRONGER. It may not "
    "become more causal, more exclusive, more comparative, more temporally specific, more "
    "interpretive or more certain. If your repaired wording says anything the original did "
    "not, it is an addition however true it is.\n"
    "\n"
    "RELATIONS ARE FACTUAL CLAIMS, AND CONNECTIVES CREATE THEM. This is the rule that is "
    "most often broken, because the words look like grammar rather than assertion. When "
    "you re-join the surviving halves of a cut sentence you will reach for a connective, "
    "and that connective is a new claim. These are the NINE classes the machine check "
    "measures, with the words that trigger each one:\n"
    "  CAUSE          because, since, causes, caused, led to, produces, makes it, due to\n"
    "  CONSEQUENCE    so, therefore, thus, as a result, hence, consequently, which is "
    "why, which meant, means that, so that, leading to, forcing, allowing\n"
    "  EQUIVALENCE    the same as, the same, amounts to, equivalent, identical, no "
    "different, is really, both are, are both, one and the same, re-read as\n"
    "  COMPARISON     more, less, fewer, greater, than, unlike, whereas, compared\n"
    "  SUPERLATIVE    most, least, best, worst, and any -est word\n"
    "  GENERALIZATION always, every, all, any, in general, wherever, whenever, never\n"
    "  NEGATION       no, not, nothing, none, without, cannot, can only, fails to\n"
    "  ABSENCE        absence, missing, unpublished, unreadable, uncounted, no estimate, "
    "not published, not counted\n"
    "  TEMPORAL       before, after, then, until, once, by the time\n"
    "None of these may appear in your repaired wording unless it is already in the "
    "original sentence, or a fact you cite carries it. Join the halves with a full stop "
    "instead of a connective, or delete one of them.\n"
    "\n"
    "GENERALISING IS THE QUIETEST WAY TO BREAK THIS, and it is what cost a real run. "
    "Cutting an unsupported specific and reaching for the general case in its place -- "
    "one study becoming 'such studies', one device becoming 'these systems', one "
    "occasion becoming 'whenever' -- feels like retreating to safer ground. It is the "
    "opposite: the narrow claim was about one thing, the general one is about a class, "
    "and a class is bigger. Cut the specific and stop. Say less about fewer things, "
    "never a little about more of them.\n"
    "\n"
    "EXCLUSIVITY, likewise, is a relation and not a hedge: only, single, alone, the "
    "first, the last, nothing else.\n"
    "\n"
    "TIME IS LICENSED ONLY BY THE TIME OPERATIONS. A repair may change what a sentence "
    "says about when something happened ONLY when its operation is CORRECT_TIME or "
    "CORRECT_DATE. Under any other operation, added temporal content is refused. So if a "
    "passage is wrong about time, say so with the operation -- do not slip a tense or a "
    "date fix into a NARROW.\n"
    "\n"
    "DO NOT INTRODUCE A NAME. No new person, work, place, institution or title, including "
    "one you are confident about and one that appears in the article elsewhere. Naming the "
    "thing a pronoun referred to is an addition unless a cited fact carries that name. If "
    "a reference is unclear, cut the reference.\n"
    "\n"
    "THE OPERATIONS, and what each one is for:\n"
    "  DELETE                  drop the whole sentence. Always available, often the right "
    "answer, never a failure.\n"
    "  NARROW                  cut scope, certainty, causal or comparative language.\n"
    "  REMOVE_EXCLUSIVITY      cut 'the only', 'the single', 'the first'.\n"
    "  NARROW_CHARACTERISATION cut an unsupported description down to the supported part. "
    "Cut it down -- do not swap in a different description.\n"
    "  RESTORE_ATTRIBUTION     put back 'according to X' that the sentence dropped, where "
    "a cited fact carries X.\n"
    "  CORRECT_TIME            fix a tense or time placement, so a draft-stage quote is "
    "not written as though it were said of the finished thing.\n"
    "  CORRECT_DATE            fix an ambiguous date reference so it points where the "
    "cited facts point.\n"
    "\n"
    "CITE EVERY FACT YOUR REPAIRED WORDING RESTS ON, not only the one the passage was "
    "already about. If you keep a date, a name or an attribution, the fact that carries it "
    "must be in your fact_ids -- otherwise the wording reads as an addition and is "
    "refused.\n"
    "\n"
    "THE GROUNDER'S EXPLANATION IS NOT EVIDENCE. It may name a date or a fact to help you "
    "see the problem; you may only use what the LISTED FACTS carry. If a reference is "
    "ambiguous and no listed fact resolves it, remove the reference rather than resolve "
    "it from the explanation.\n"
    "\n"
    "ONE REPAIR, EVERY OCCURRENCE. A flagged claim is often made more than once, and the "
    "grounder quotes only one place it appears. You have the WHOLE ARTICLE above. Before "
    "you write an edit, search it for the claim itself -- not the quoted wording, the "
    "CLAIM -- and repair every place it is made. Emit one edit per occurrence, all citing "
    "the same finding_id. Two edits for one finding is normal and correct.\n"
    "\n"
    "THIS IS THE COMMONEST WAY A REPAIR FAILS, and it cost a real run. The grounder "
    "flagged that a Grade I listing had been glossed as marking a building 'of "
    "exceptional interest'. The article said it twice, in different words, three "
    "paragraphs apart. The repair fixed the sentence that was quoted, the other survived "
    "untouched, and the article was held on the identical claim it had just been "
    "corrected for. In the same run a second flagged phrase sat inside a sentence the "
    "repair was editing for a different reason -- and was left in place while that other "
    "phrase was cut. There is no second repair, so an occurrence you do not reach now is "
    "an occurrence nobody reaches.\n"
    "\n"
    "You may not touch a sentence that was not flagged FOR SOME FINDING, and you may not "
    "improve the style of anything. Every edit must be traceable to a finding -- but one "
    "finding may legitimately require several edits.\n"
    "\n"
    "IF A FLAGGED PASSAGE CANNOT BE FIXED BY REMOVING WORDS, DELETE IT. A deleted "
    "sentence costs the article a sentence. An invented one costs it the run: the machine "
    "check refuses the edit, and there is no second repair."
)

REPAIR_GROUNDING_SCHEMA = (
    "Reply with ONE JSON object:\n"
    '{"edits": [{"finding_id": "F1",\n'
    '            "original": "the flagged sentence, verbatim from the article",\n'
    '            "repaired": "the corrected sentence, or \"\" to delete it",\n'
    '            "operation": "NARROW",   NARROW | REMOVE_EXCLUSIVITY | CORRECT_TIME |\n'
    "                                     CORRECT_DATE | RESTORE_ATTRIBUTION |\n"
    "                                     NARROW_CHARACTERISATION | DELETE\n"
    '            "fact_ids": ["F.."],     the ledger facts the repaired wording rests on\n'
    '            "what_was_removed": "the scope, exclusivity or certainty taken out"}]}\n'
    "One finding may have SEVERAL edits, one per place the claim is made. Repeat the "
    "same finding_id on each; they are applied in order and all of them count.\n"
    "No prose outside the JSON."
)

REPAIR_OPS = ("NARROW", "REMOVE_EXCLUSIVITY", "CORRECT_TIME", "CORRECT_DATE",
              "RESTORE_ATTRIBUTION", "NARROW_CHARACTERISATION", "DELETE")


def repairable_findings(findings: list) -> list:
    """The findings a subtractive repair can answer: a claim the article makes and the
    evidence does not carry. LEGITIMATE_INTERPRETATION is not one."""
    return [f for f in (findings or [])
            if f.get("classification") in ("TRUE_UNSUPPORTED", "TRUE_UNCERTAIN")
            and str(f.get("quote") or "").strip()]


# "27th" and "27" are the same day. ST._numbers reads the second and not the first, so a
# fact saying "published on 27th August 2026" licenses "2026" and not "27" -- and a
# repair restoring that date reads as an addition. Same class as the decimal split:
# the two sides must extract the same way or the comparison is between different things.
_ORDINAL = re.compile(r"(\d)(?:st|nd|rd|th)\b", re.I)


def _numbers_of(text: str) -> set:
    return ST._numbers(_ORDINAL.sub(r"\1", text or ""))


_DATEISH = re.compile(r"\b(?:\d{1,2}(?:st|nd|rd|th)?\s+)?(?:January|February|March|April"
                      r"|May|June|July|August|September|October|November|December)\b"
                      r"|\b(?:19|20)\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b", re.I)


def _relevant_facts(quote: str, ledger: dict, why: str = "", limit: int = 14) -> list:
    """The evidence for the passages this repair must fix, and nothing else.

    Overlap by wording, PLUS every date-bearing fact when the finding concerns a date.
    That second half is not a convenience: a date-bearing fact shares no vocabulary with
    the sentence whose date is wrong. The Ground Truth of this stage was a repair asked
    to fix "had not responded by noon that day" while F35 -- "The DNS article was written
    by Hannah Sharland and published on 27th August 2026" -- scored zero on overlap and
    was never shown to it. The repair then reached for the date in the grounder's own
    explanation, which is not evidence, and was refused. Correctly, and uselessly.

    Still no research, no pack, no source bodies.
    """
    key = {w for w in re.findall(r"[a-z]{5,}", (quote or "").lower())
           if w not in ST._FUNCTION_WORDS}
    scored, picked = [], set()
    for fid, f in (ledger or {}).items():
        prop = (f.get("proposition") or "").lower()
        hits = sum(1 for w in key if w in prop)
        if hits:
            scored.append((hits, fid, f))
    scored.sort(key=lambda x: -x[0])
    out = []
    for _, fid, f in scored[:limit]:
        out.append((fid, f)); picked.add(fid)
    if _DATEISH.search("%s %s" % (quote or "", why or "")):
        for fid, f in sorted((ledger or {}).items()):
            if fid in picked:
                continue
            if _DATEISH.search("%s %s" % (f.get("proposition", ""),
                                          f.get("support_span", ""))):
                out.append((fid, f)); picked.add(fid)
                if len(out) >= limit + 8:
                    break
    return out


def repair_prompt(article_text: str, findings: list, ledger: dict) -> str:
    L = ["THE ARTICLE", article_text, "", "WHAT THE GROUNDER FOUND"]
    for f in findings:
        L += ["", "FINDING %s  [%s]" % (f.get("id"), f.get("classification")),
              "  passage : %s" % str(f.get("quote"))[:400],
              "  why     : %s" % str(f.get("why"))[:600]]
        if f.get("suggested_patch"):
            L.append("  a narrower wording the grounder believes is supported: %s"
                     % str(f["suggested_patch"])[:300])
        rel = _relevant_facts(str(f.get("quote") or ""), ledger,
                              str(f.get("why") or ""))
        if rel:
            L.append("  THE FROZEN EVIDENCE FOR THIS PASSAGE:")
            for fid, fact in rel:
                L.append("    %s  %s" % (fid, fact.get("proposition", "")[:220]))
                if fact.get("support_span"):
                    L.append("        span: %r" % fact["support_span"][:200])
    L += ["", REPAIR_GROUNDING_SCHEMA]
    return "\n".join(L)


def apply_grounding_repair(article_text: str, edits: list, findings: list,
                           ledger: dict, packet: dict) -> tuple:
    """Apply the subtractive edits and verify each one. Returns (text, provenance, errs).

    Every edit is checked mechanically: it must answer a real finding, its original must
    be in the article, and its repaired wording may introduce no number, entity or
    relation the original and the licensing facts did not already carry. A repair that
    adds is refused, not applied.
    """
    ids = {str(f.get("id")) for f in findings}
    approved = ST.render(packet)
    a_nums, a_ents = _numbers_of(approved), ST._entities(approved,
                                                         skip_sentence_initial=False)
    out, prov, errs = article_text, [], []
    for i, e in enumerate(edits or [], 1):
        if not isinstance(e, dict):
            errs.append("edit %d is not an object" % i)
            continue
        fid = str(e.get("finding_id") or "")
        orig = (e.get("original") or "").strip()
        rep = (e.get("repaired") or "").strip()
        op = e.get("operation")
        if fid not in ids:
            errs.append("edit %d cites finding %r, which the grounder did not report"
                        % (i, fid))
            continue
        if op not in REPAIR_OPS:
            errs.append("edit %d has operation %r, not one of %s"
                        % (i, op, ", ".join(REPAIR_OPS)))
            continue
        if not orig or normalize_span(orig) not in normalize_span(out):
            errs.append("edit %d: the original is not in the article: %r"
                        % (i, orig[:80]))
            continue
        # THE REPAIR MAY ONLY SUBTRACT -- but a correction is measured against the
        # EVIDENCE IT CITES, not against the packet alone.
        #
        # The first real repair was refused for adding the number "27" and a TEMPORAL
        # relation, on edits doing exactly what CORRECT_DATE and CORRECT_TIME are for:
        # restoring a date the article had left ambiguous, and putting a draft
        # consultation quote back in its own tense. A guard that refuses those refuses
        # the permission it was written to enforce. So new surface is allowed only when a
        # CITED LEDGER FACT carries it, in its proposition or its support span, and
        # nowhere else.
        lic = [f for f in (e.get("fact_ids") or []) if f in ledger]
        lic_text = " ".join(
            "%s %s" % ((ledger[f] or {}).get("proposition", ""),
                       (ledger[f] or {}).get("support_span", "")) for f in lic)
        allowed_nums = a_nums | _numbers_of(lic_text)
        allowed_ents = a_ents | ST._entities(lic_text, skip_sentence_initial=False)
        new_nums = sorted(_numbers_of(rep) - _numbers_of(orig) - allowed_nums)
        new_ents = sorted(ST._entities(rep) - ST._entities(orig) - allowed_ents)
        # A time correction necessarily changes temporal content; that is the operation.
        # Every other relation class is still refused.
        new_rel = [x for x in (ST.validate_turn_support(rep, lic, ledger)
                               if rep and lic else [])
                   if not (x["relation"] == ST.TEMPORAL
                           and op in ("CORRECT_TIME", "CORRECT_DATE"))]
        if new_nums or new_ents or new_rel:
            errs.append("edit %d ADDS rather than subtracts -- numbers=%s entities=%s "
                        "relations=%s (allowed only what the cited facts %s carry)"
                        % (i, new_nums, new_ents,
                           [x["relation"] for x in new_rel], lic))
            continue
        unknown = sorted(set(e.get("fact_ids") or []) - set(ledger))
        if unknown:
            errs.append("edit %d cites fact ids not in the ledger: %s" % (i, unknown))
            continue
        idx = normalize_span(out).find(normalize_span(orig))
        # Replace on the raw text by locating the sentence it belongs to.
        target = next((s for s in CE.sentences(out)
                       if normalize_span(orig) in normalize_span(s)
                       or normalize_span(s) in normalize_span(orig)), None)
        if target is None:
            errs.append("edit %d: could not locate the sentence to replace" % i)
            continue
        out = out.replace(target, rep, 1) if rep else out.replace(target, "", 1)
        out = re.sub(r"[ \t]{2,}", " ", out)
        prov.append({"finding_id": fid, "operation": op,
                     "original": target.strip(), "repaired": rep,
                     "what_was_removed": e.get("what_was_removed", ""),
                     "fact_ids": lic,
                     "support_spans": [ (ledger.get(f) or {}).get("support_span", "")
                                        for f in lic ][:4],
                     "authorising_finding": next(
                         (str(x.get("why"))[:300] for x in findings
                          if str(x.get("id")) == fid), "")})
    return out.strip(), prov, errs


def apply_local_grounding_repair(article_text: str, edits: list, findings: list,
                                 ledger: dict, packet: dict) -> tuple:
    """Grounding's OWN repair (Stage 8b's first repair and Stage 8c's completion pass),
    claim-locally -- unlike apply_grounding_repair() just above, which Safety's article
    repair (Stage 9b) and the package-only repair keep using UNCHANGED.

    Real production evidence (retained Poetry, live continuation, 2026-09-09):
    apply_grounding_repair()'s number/entity permission is `a_nums | cited_facts` --
    the WHOLE packet, unioned with what the edit's own fact_ids cite -- so an edit
    correcting one unsupported proposition could still introduce an entity or number
    that happened to appear ANYWHERE else in the packet, unrelated to the proposition
    being fixed. One such edit introduced the entity "Something", caught by the
    mandatory post-repair Safety recheck -- correctly, but wastefully: the one repair
    opportunity was spent turning an unsupported claim into a DIFFERENT unsupported
    claim rather than fixing the one that was found.

    Everything here is identical to apply_grounding_repair() -- same fields, same
    REPAIR_OPS, same sentence-level application, same ST.validate_turn_support()
    relation check (which was already claim-local: it only ever checks against `lic`,
    the edit's own cited facts, never the whole packet) -- with two changes:

    1. `orig` must additionally be found inside a SINGLE paragraph, never spanning two.
       Not new to what this file's other local repairs already require; new only to
       Grounding, which previously located by sentence only.
    2. Number/entity permission drops the packet-wide term entirely. What a rewrite may
       carry is exactly what its own local span already had, plus what its OWN cited
       fact_ids explicitly license -- never merely because something appears somewhere
       else in the packet or the ledger.

    `packet` is accepted only for call-site parity with apply_grounding_repair() --
    this claim-local variant never reads it, which is the point of change 2 above.
    """
    ids = {str(f.get("id")) for f in findings}
    paras = CE.paragraphs(article_text)
    out, prov, errs = article_text, [], []
    for i, e in enumerate(edits or [], 1):
        if not isinstance(e, dict):
            errs.append("edit %d is not an object" % i)
            continue
        fid = str(e.get("finding_id") or "")
        orig = (e.get("original") or "").strip()
        rep = (e.get("repaired") or "").strip()
        op = e.get("operation")
        if fid not in ids:
            errs.append("edit %d cites finding %r, which the grounder did not report"
                        % (i, fid))
            continue
        if op not in REPAIR_OPS:
            errs.append("edit %d has operation %r, not one of %s"
                        % (i, op, ", ".join(REPAIR_OPS)))
            continue
        if not orig or normalize_span(orig) not in normalize_span(out):
            errs.append("edit %d: the original is not in the article: %r"
                        % (i, orig[:80]))
            continue
        host_idx = next((j for j, p in enumerate(paras)
                        if normalize_span(orig) in normalize_span(p)), None)
        if host_idx is None:
            errs.append("edit %d spans more than one paragraph -- not a local edit: %r"
                        % (i, orig[:80]))
            continue
        # THE REPAIR MAY ONLY SUBTRACT, licensed by exactly what its own local span
        # already had and what its OWN CITED facts explicitly carry -- never the whole
        # packet, which is the one change from apply_grounding_repair() above.
        lic = [f for f in (e.get("fact_ids") or []) if f in ledger]
        lic_text = " ".join(
            "%s %s" % ((ledger[f] or {}).get("proposition", ""),
                       (ledger[f] or {}).get("support_span", "")) for f in lic)
        allowed_nums = _numbers_of(lic_text)
        allowed_ents = ST._entities(lic_text, skip_sentence_initial=False)
        new_nums = sorted(_numbers_of(rep) - _numbers_of(orig) - allowed_nums)
        new_ents = sorted(ST._entities(rep) - ST._entities(orig) - allowed_ents)
        # A time correction necessarily changes temporal content; that is the operation.
        # Every other relation class is still refused. Unchanged from
        # apply_grounding_repair() -- this check was already claim-local.
        new_rel = [x for x in (ST.validate_turn_support(rep, lic, ledger)
                               if rep and lic else [])
                   if not (x["relation"] == ST.TEMPORAL
                           and op in ("CORRECT_TIME", "CORRECT_DATE"))]
        if new_nums or new_ents or new_rel:
            errs.append("edit %d ADDS rather than subtracts -- numbers=%s entities=%s "
                        "relations=%s (licensed only by this local span and the cited "
                        "facts %s, not the whole packet)"
                        % (i, new_nums, new_ents,
                           [x["relation"] for x in new_rel], lic))
            continue
        unknown = sorted(set(e.get("fact_ids") or []) - set(ledger))
        if unknown:
            errs.append("edit %d cites fact ids not in the ledger: %s" % (i, unknown))
            continue
        if orig not in out:
            errs.append("edit %d: quoted text does not match the article exactly "
                        "(whitespace or punctuation drift) -- refused rather than "
                        "guessed at" % i)
            continue
        target = next((s for s in CE.sentences(out)
                       if normalize_span(orig) in normalize_span(s)
                       or normalize_span(s) in normalize_span(orig)), None)
        if target is None:
            errs.append("edit %d: could not locate the sentence to replace" % i)
            continue
        out = out.replace(target, rep, 1) if rep else out.replace(target, "", 1)
        out = re.sub(r"[ \t]{2,}", " ", out)
        prov.append({"finding_id": fid, "operation": op,
                     "original": target.strip(), "repaired": rep,
                     "what_was_removed": e.get("what_was_removed", ""),
                     "fact_ids": lic,
                     "support_spans": [ (ledger.get(f) or {}).get("support_span", "")
                                        for f in lic ][:4],
                     "authorising_finding": next(
                         (str(x.get("why"))[:300] for x in findings
                          if str(x.get("id")) == fid), "")})
    return out.strip(), prov, errs


def grounding_repair(provider, article_text: str, findings: list, ledger: dict,
                     packet: dict) -> dict:
    """STAGE 8b. Exactly one call. Subtractive, audited, and never repeated. Verified
    by apply_local_grounding_repair() -- claim-local, not apply_grounding_repair()'s
    packet-wide permission (see that function's own docstring for why)."""
    target = repairable_findings(findings)
    if not target:
        return {"status": SKIPPED, "reason": "no repairable finding", "model_calls": 0}
    obj, ident = _ask(provider, REPAIR_GROUNDING_SYSTEM,
                      repair_prompt(article_text, target, ledger),
                      6_000, GROUNDING, GROUNDING_HOLD)
    edits = obj.get("edits")
    if not isinstance(edits, list) or not edits:
        raise CompositionHold(GROUNDING, GROUNDING_HOLD,
                              ["the factual repair returned no edits"])
    text, prov, errs = apply_local_grounding_repair(article_text, edits, target, ledger,
                                                    packet)
    # PARTIAL ACCEPTANCE. apply_local_grounding_repair already validates each edit on its own and
    # skips the ones that fail, so the accepted set is exactly the set that passed the
    # guard -- nothing here relaxes it, and no rejected edit is applied.
    #
    # What changed on 2026-09-05 is only what happens NEXT. A single bad edit used to
    # discard the whole repair: measured across four independent subjects, six edits were
    # refused and every valid edit beside them was thrown away with them, ending the run.
    # Now the valid edits stand and the run continues to Safety and the second Grounder,
    # which is authoritative and will still HOLD on anything the repair failed to answer.
    #
    # This is NOT a second repair. It is still one repair call, one set of edits, and one
    # authoritative Grounder after it. If every edit was refused, nothing was repaired and
    # re-running the Grounder would only rediscover the same findings, so that stays a HOLD.
    if errs and not prov:
        raise CompositionHold(
            GROUNDING, GROUNDING_HOLD,
            ["the factual repair did not stay within its permissions"] + errs[:6],
            {"attempted_edits": edits, "failures": errs})
    if not text.strip():
        raise CompositionHold(GROUNDING, GROUNDING_HOLD,
                              ["the factual repair deleted the whole article"])
    return {"status": PASS, "article_text": text, "edits": prov,
            "findings_answered": [f.get("id") for f in target],
            "rejected_edits": errs,
            "findings_left_unanswered": sorted(
                {str(f.get("id")) for f in target}
                - {str(e.get("finding_id")) for e in prov}),
            "provider": ident, "model_calls": 1, "repairs": 1}


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 8b/8c REPLACED -- PROGRESS-BOUNDED GROUNDING COMPLETION (owner-directed,
# 2026-09-09)
# ══════════════════════════════════════════════════════════════════════════════
# WHY. grounding_repair() above is committed the moment apply_local_grounding_repair()
# approves an edit's OWN added surface -- it never asks whether the resulting ARTICLE is
# actually better. The retained "Poetry as climate communication" continuation showed
# exactly the gap that leaves open: the one repair narrowed a claim by cutting
# "...to show that recited poetry could produce a range of responses from chills to
# goosebumps" from the flagged sentence, correctly by the edit's own local-permission
# check (the edit added no number, entity or relation). But the very next, UNEDITED
# sentence opened with "Something similar is at work..." -- a reference to the reaction
# the cut just removed. The result was a genuine article-body defect (Safety correctly
# raised NEW_UNSUPPORTED_FACTS / CONTINUITY_ADDED_MATERIAL on it), and by the time Safety
# caught it the one grounding-repair budget was already spent, so the whole article HELD
# on a defect ITS OWN repair had just introduced.
#
# THE FIX IS NOT A "SOMETHING" DETECTOR. No local-permission check, however good, can
# know what an untouched neighboring sentence depends on -- that is a property of the
# WHOLE resulting article, and the only thing that can answer it is running the real
# Safety and Grounding checks against the candidate BEFORE it becomes the accepted
# article. So repair here is TRANSACTIONAL: a proposal is applied to a temporary copy,
# validated in full, and only committed if it demonstrably leaves the article in a
# strictly better state. A proposal that fails validation is discarded whole -- the
# accepted article is exactly what it was before the proposal was tried -- and the
# reason is handed to the next proposal so the model does not repeat it blind.
#
# PROGRESS IS DEFINED NARROWLY, ON PURPOSE. Different wording, a model's own claim of
# improvement, or the same finding count with different findings are NOT progress --
# only a Grounding blocking set that is STRICTLY SMALLER counts, and only alongside a
# Safety recheck that introduces no NEW blocker. "1 blocker -> 1 different blocker" and
# "Grounding improvement + a new Safety problem" are both rejected, not accepted with a
# caveat.
#
# THE CEILING IS A FUSE, NOT A BUDGET. MAX_GROUNDING_COMPLETION_ITERATIONS bounds
# pathological execution; the loop is expected to stop earlier, on a PASS, on a
# proposal that cannot be turned into a candidate, on a repeated ineffective proposal, or
# on one iteration of no progress that the next iteration's rejection feedback also fails
# to fix within the fuse.
#
# FACTUAL AUTHORITY IS UNCHANGED. Every proposal still goes through
# apply_local_grounding_repair() -- the SAME claim-local guard grounding_repair() already
# uses: a repair may use only what its own local span already carried and what its own
# cited Ledger facts explicitly license, never the whole packet, never new research,
# never a new Ledger fact.
#
# SCOPE. Grounding only. Reader's editorial repair and the article-Safety repair (Stage
# 9b) are untouched -- this policy is proven here, on real production evidence, before it
# is considered anywhere else. If an accepted repair needs its package re-validated under
# existing pipeline semantics (it does not, currently: a Grounding factual repair changes
# only the article, never the package -- package regeneration after a factual repair is
# not part of today's semantics and this loop does not add it), the caller reaches for
# the SAME package_only_safety_completion() every other regenerated-package call site
# already uses; nothing here duplicates that logic.
GROUNDING_COMPLETION_MAX_ITERATIONS = 5


def _sentence_containing_quote(article_text: str, quote: str) -> int | None:
    """Index into CE.sentences(article_text) of the sentence carrying `quote`, or None."""
    sents = CE.sentences(article_text)
    return next((i for i, s in enumerate(sents)
                if normalize_span(quote) in normalize_span(s)
                or normalize_span(s) in normalize_span(quote)), None)


def neighbor_context_for(article_text: str, quote: str) -> tuple[str, str]:
    """(previous_sentence, next_sentence) around the sentence carrying `quote` -- READ-ONLY
    context so a repair proposal can see, without being permitted to touch, what an
    untouched neighboring sentence depends on before it removes anything. ("", "") if the
    quote cannot be located, exactly like every other locate-or-refuse guard in this
    file."""
    sents = CE.sentences(article_text)
    idx = _sentence_containing_quote(article_text, quote)
    if idx is None:
        return "", ""
    return (sents[idx - 1] if idx > 0 else "",
            sents[idx + 1] if idx + 1 < len(sents) else "")


GROUNDING_COMPLETION_LOOP_SYSTEM = REPAIR_GROUNDING_SYSTEM + "\n\n" + (
    "ONE MORE RULE, ABOVE ALL THE OTHERS ABOVE: DO NOT REMOVE INFORMATION THAT AN "
    "UNEDITED NEIGHBORING SENTENCE DEPENDS ON. Each finding below is shown with the "
    "sentence immediately before and after it, as READ-ONLY CONTEXT -- not for you to "
    "edit, but for you to check before you cut. If the next sentence refers back to "
    "something in the passage you are about to narrow or delete ('similar', 'that "
    "reaction', 'the same effect', 'this', 'it'), and your edit would remove the thing "
    "it refers to, your edit breaks a sentence you are not allowed to touch. In that "
    "case: choose a different narrowing that keeps the referent, or delete only within "
    "the sentence the finding actually names. Never solve this by rewriting the "
    "neighboring sentence itself -- it was not flagged, and editing it is not "
    "available to you here.\n"
    "\n"
    "YOUR PROPOSAL IS PROVISIONAL, NOT A COMMIT. It is applied to a copy, checked "
    "against Safety and against the Grounder again, and kept only if the resulting "
    "article is genuinely better -- fewer Grounding blockers, and no new Safety "
    "blocker. If it fails either check, the article you were shown is exactly what "
    "proceeds to your next attempt, unchanged; nothing you propose here is ever lost "
    "silently. If you are told a previous proposal was rejected and why, do not repeat "
    "it -- propose something that answers the stated reason."
)


def grounding_completion_prompt(article_text: str, findings: list, ledger: dict,
                                rejection: dict | None = None) -> str:
    """Same shape as repair_prompt(), plus READ-ONLY neighboring-sentence context per
    finding and, on a retry, the previous proposal's rejection reason -- concise and
    structured, never the previous transcript."""
    L = ["THE ARTICLE", article_text, "", "WHAT THE GROUNDER FOUND"]
    for f in findings:
        L += ["", "FINDING %s  [%s]" % (f.get("id"), f.get("classification")),
              "  passage : %s" % str(f.get("quote"))[:400],
              "  why     : %s" % str(f.get("why"))[:600]]
        if f.get("suggested_patch"):
            L.append("  a narrower wording the grounder believes is supported: %s"
                     % str(f["suggested_patch"])[:300])
        prev_s, next_s = neighbor_context_for(article_text, str(f.get("quote") or ""))
        if prev_s:
            L.append("  PREVIOUS SENTENCE (read-only, do not edit): %s" % prev_s[:300])
        if next_s:
            L.append("  NEXT SENTENCE (read-only, do not edit -- check it does not "
                     "depend on what you are about to remove): %s" % next_s[:300])
        rel = _relevant_facts(str(f.get("quote") or ""), ledger,
                              str(f.get("why") or ""))
        if rel:
            L.append("  THE FROZEN EVIDENCE FOR THIS PASSAGE:")
            for fid, fact in rel:
                L.append("    %s  %s" % (fid, fact.get("proposition", "")[:220]))
                if fact.get("support_span"):
                    L.append("        span: %r" % fact["support_span"][:200])
    if rejection:
        L += ["", "YOUR PREVIOUS PROPOSAL WAS REJECTED BECAUSE: %s"
             % str(rejection.get("reason", ""))[:300]]
        if rejection.get("detail"):
            L.append("  detail: %s" % str(rejection["detail"])[:400])
        L.append("Do not repeat that proposal. Propose something that answers this "
                "reason instead.")
    L += ["", REPAIR_GROUNDING_SCHEMA]
    return "\n".join(L)


# ══════════════════════════════════════════════════════════════════════════════
# DELETE_UNSUPPORTED_SURFACE -- deterministic, model-free subtraction (owner-directed,
# 2026-09-09)
# ══════════════════════════════════════════════════════════════════════════════
# WHY. The retained Poetry continuation's persistent blocker was as small as a Grounding
# repair gets -- one unlicensed modifier, "separate", in "a separate experiment with 27
# German-speaking participants" (the licensed fact says only "one experiment involved 27
# German-speaking participants"). The Grounder's own suggested_patch already names the
# fix. Both of the model's repair proposals still reached for a bigger rewrite -- one
# truncated the whole sentence and orphaned the next one's "Something similar..."
# reference, caught correctly (and only) by this same run's transactional Safety check.
# A trivial overclaim should not depend on a model choosing the small edit over the
# creative one on any given call.
#
# WHAT IT DOES. For each finding, compares the finding's QUOTE against the LOCALLY
# RELEVANT Ledger evidence -- the SAME _relevant_facts() lexical-overlap lookup
# repair_prompt() already uses -- and asks only: which of the quote's own content words
# do not appear anywhere in that evidence? If there are one or two such words (never
# more -- a bigger gap is not "a trivial modifier", it is exactly the shape this operator
# refuses to force), they are deleted, verbatim, from the article's own sentence. Nothing
# is invented, nothing is reworded, nothing is imported from a Ledger fact other than the
# words already there: this is length-reducing subtraction, not disguised generation.
#
# WHY THIS IS NOT suggested_patch. The Grounder's own narrower wording is a genuine
# rewrite -- "a separate experiment with" became "one experiment involving" here, a
# preposition and article changed, not merely a word removed. This operator will not
# emit that, because what it deletes is decided against the Ledger rather than taken
# from a model's phrasing.
#
# suggested_patch is now tried too, as a SEPARATE candidate source (see
# suggested_patch_candidate below, added 2026-09-09 after the retained Poetry
# continuation spent all five iterations rediscovering a correction the Grounder had
# already written down). That does not make it authority and does not weaken this
# operator: it is one more candidate, accepted only by the same transactional Safety
# check and Grounding recheck everything else here goes through.
#
# ELIGIBILITY IS NARROW AND FALLS THROUGH CLEANLY. No POS tagger, no synonym table, no
# per-word allowlist: if the deletion cannot be constructed (the quote cannot be located
# in a single sentence, the flagged word cannot be found there verbatim, or the residue
# is empty or unchanged), this returns None and the caller reaches for
# grounding_repair_proposal() exactly as it always has. And REGARDLESS of how this
# operator constructs a candidate, it is a candidate like any other: the SAME
# transactional Safety check and Grounding recheck grounding_completion_loop already
# runs on every proposal decide whether it is kept. A deletion that leaves the sentence
# broken, or that fails to resolve the finding, is rejected there -- this operator does
# not need to get grammar or resolution right on its own, only to never invent.
DETERMINISTIC_SUBTRACTION_MAX_WORDS = 2


def _local_licensed_words(quote: str, ledger: dict) -> set:
    """Content words from the Ledger facts _relevant_facts() finds relevant to `quote`
    -- the SAME lexical-overlap evidence lookup repair_prompt()/completion_prompt()
    already show a repair model, read here as the vocabulary a deletion may treat as
    already-licensed."""
    rel = _relevant_facts(quote, ledger)
    text = " ".join("%s %s" % (f.get("proposition", ""), f.get("support_span", ""))
                    for _fid, f in rel)
    return ST._content_words(text, fold=True)


def deterministic_subtractive_edit(article_text: str, finding: dict,
                                   ledger: dict) -> dict | None:
    """A DELETE_UNSUPPORTED_SURFACE candidate for ONE finding, or None if no minimal,
    purely-subtractive deletion can be established -- see the module comment above for
    the full rationale. Never invents, never rewrites: what survives is the article's own
    words, minus the ones the Ledger does not license."""
    quote = str(finding.get("quote") or "").strip()
    if not quote:
        return None
    licensed = _local_licensed_words(quote, ledger)
    # Raw quote words only (fold=False) -- _content_words(fold=True) unions in each
    # word's own stem, which would make "increases"/"increas" two entries for one real
    # word and could push a single overclaim over DETERMINISTIC_SUBTRACTION_MAX_WORDS,
    # or leave nothing left to delete on the second entry once the first's regex has
    # already consumed it. Each raw word is still checked against the licensed
    # vocabulary BOTH as itself and by its own stem, so a quote's plural still matches a
    # licensed singular (or vice versa) without duplicating the word being judged.
    unsupported = {w for w in ST._content_words(quote, fold=False)
                  if w not in licensed and ST._stem(w) not in licensed}
    if not unsupported or len(unsupported) > DETERMINISTIC_SUBTRACTION_MAX_WORDS:
        return None
    idx = _sentence_containing_quote(article_text, quote)
    if idx is None:
        return None
    original_sentence = CE.sentences(article_text)[idx]
    repaired = original_sentence
    for w in sorted(unsupported):
        new_repaired, n = re.subn(r"\b%s\w*\b\s*" % re.escape(w), "", repaired,
                                  count=1, flags=re.IGNORECASE)
        if n == 0:
            return None
        repaired = new_repaired
    repaired = re.sub(r"\s+([.,;:!?])", r"\1", repaired).strip()
    repaired = re.sub(r"\s{2,}", " ", repaired)
    if not repaired or repaired == original_sentence:
        return None
    return {"finding_id": finding.get("id"), "operation": "DELETE",
           "original": original_sentence, "repaired": repaired, "fact_ids": [],
           "what_was_removed": ", ".join(sorted(unsupported))}


# ══════════════════════════════════════════════════════════════════════════════
# SUGGESTED_PATCH -- the correction the Grounder already wrote (owner-directed,
# 2026-09-09)
# ══════════════════════════════════════════════════════════════════════════════
# WHY. Retained Poetry continuation …-2026-09-09T214338 HELD on ONE finding:
#
#   quote           "In a separate experiment with 27 German-speaking participants"
#   why             the source says only "one experiment that involved 27 German-
#                   speaking participants"; "separate" asserts a relationship it
#                   does not settle
#   suggested_patch "In one experiment that involved 27 German-speaking participants"
#
# The completion loop then spent all five iterations -- one deterministic candidate and
# four model repair calls -- trying to invent that sentence, and made the article worse
# every time (1 -> 3, 1 -> 2, safety-rejected, 1 -> 2, 1 -> 4). Zero accepted. The
# correction was sitting in the finding the loop was reading.
#
# suggested_patch IS NOT FACTUAL AUTHORITY and is not trusted here. It is a CANDIDATE
# SOURCE, nothing more: the Grounder has already spent a model call diagnosing the claim
# and sometimes states the narrow fix, so testing what it said costs no repair-model call
# at all. Whether the article changes is still decided by apply_local_grounding_repair(),
# then Safety, then a fresh Grounding recheck, then strict blocker shrink -- the same
# acceptance path a deterministic candidate and a model proposal go through, with no
# privileged route for any origin.
#
# THE SPAN QUESTION, which is what makes this safe or unsafe. The Grounder's schema calls
# suggested_patch "a minimal replacement for that clause" -- the clause being the
# finding's own `quote`. But apply_local_grounding_repair() replaces the whole SENTENCE
# containing `original`. Handing it (original=quote, repaired=patch) would therefore
# delete everything else in that sentence -- in the case above, the entire
# psychophysiology clause -- while looking like a minimal fix. So the candidate is built
# at SENTENCE granularity: find the one sentence carrying the quote, substitute the patch
# for the quote INSIDE it, and offer the whole before/after sentence pair. Anything that
# cannot be established exactly -- the quote is absent, appears more than once, spans
# more than one sentence, or the substitution changes nothing -- is ineligible and falls
# through to the operators below, which is the same fail-closed rule every other locator
# in this file uses.


def suggested_patch_edit(article_text: str, finding: dict) -> dict | None:
    """A NARROW candidate edit for ONE finding built from its own suggested_patch, or
    None when the span relationship cannot be established exactly.

    Never widens the edit beyond the sentence the quote lives in, and never invents: the
    repaired sentence is the article's own sentence with the Grounder's replacement
    substituted for the flagged clause, character for character.
    """
    quote = str(finding.get("quote") or "").strip()
    patch = str(finding.get("suggested_patch") or "").strip()
    if not quote or not patch or patch == quote:
        return None
    # UNIQUELY LOCATABLE, verbatim. Two occurrences means an edit here would silently
    # fix one and leave the other, and guessing which is exactly what this refuses.
    if article_text.count(quote) != 1:
        return None
    hosts = [x for x in CE.sentences(article_text) if quote in x]
    if len(hosts) != 1:
        return None
    sentence = hosts[0]
    repaired = sentence.replace(quote, patch, 1)
    if repaired.strip() == sentence.strip():
        return None
    return {"finding_id": str(finding.get("id")), "operation": "NARROW",
            "original": sentence, "repaired": repaired, "fact_ids": [],
            "what_was_removed": "the wording the grounder flagged, replaced by the "
                                "narrower one it proposed"}


def suggested_patch_candidate(article_text: str, findings: list, ledger: dict,
                              packet: dict) -> dict | None:
    """The suggested-patch candidate for a WHOLE target list -- eligible only if EVERY
    finding in it yields a locally constructible patch edit, the same all-or-nothing rule
    deterministic_subtraction_candidate uses and for the same reason: mixing origins
    inside one proposal makes a rejection impossible to attribute. Verified by the SAME
    apply_local_grounding_repair() every other Grounding repair here uses -- there is no
    separate validator for this origin, and it cites no fact_ids, so its wording is
    licensed by exactly what its own sentence already carried."""
    edits = []
    for f in findings:
        e = suggested_patch_edit(article_text, f)
        if e is None:
            return None
        edits.append(e)
    text, prov, errs = apply_local_grounding_repair(article_text, edits, findings,
                                                    ledger, packet)
    if not prov or errs:
        return None
    return {"status": PASS, "article_text": text, "edits": prov,
            "findings_answered": sorted({str(e.get("finding_id")) for e in prov}),
            "rejected_edits": errs, "model_calls": 0, "suggested_patch": True}


def deterministic_subtraction_candidate(article_text: str, findings: list, ledger: dict,
                                        packet: dict) -> dict | None:
    """The deterministic candidate for a WHOLE target list -- eligible only if EVERY
    finding in it gets its own valid deletion-only edit; one finding a simple deletion
    cannot resolve falls the entire batch through to the model path rather than mixing
    a deterministic edit for some findings with a model edit for others in the same
    proposal. Verified by the SAME apply_local_grounding_repair() every other Grounding
    repair in this file uses -- not a private, weaker check."""
    edits = []
    for f in findings:
        e = deterministic_subtractive_edit(article_text, f, ledger)
        if e is None:
            return None
        edits.append(e)
    text, prov, errs = apply_local_grounding_repair(article_text, edits, findings,
                                                     ledger, packet)
    if not prov or errs:
        return None
    return {"status": PASS, "article_text": text, "edits": prov,
           "findings_answered": sorted({str(e.get("finding_id")) for e in prov}),
           "rejected_edits": errs, "model_calls": 0, "deterministic": True}


def grounding_repair_proposal(provider, article_text: str, findings: list, ledger: dict,
                              packet: dict, rejection: dict | None = None) -> dict:
    """ONE surgical, local repair proposal for the progress-bounded completion loop.
    Exactly one model call. Verified by the SAME apply_local_grounding_repair()
    grounding_repair() (Stage 8b) already uses -- claim-local, never packet-wide.

    Unlike grounding_repair(), this NEVER raises on an empty or wholly-refused result: a
    proposal that produces nothing usable is one more piece of information for the loop
    (try a different target, or stop), not a terminal failure of the whole article.
    """
    if not findings:
        return {"status": SKIPPED, "reason": "no repairable finding", "model_calls": 0}
    obj, ident = _ask(provider, GROUNDING_COMPLETION_LOOP_SYSTEM,
                      grounding_completion_prompt(article_text, findings, ledger,
                                                  rejection),
                      6_000, GROUNDING, GROUNDING_HOLD)
    edits = obj.get("edits")
    if not isinstance(edits, list) or not edits:
        return {"status": HOLD, "reason": "the repair proposal returned no edits",
                "model_calls": 1, "provider": ident}
    text, prov, errs = apply_local_grounding_repair(article_text, edits, findings,
                                                     ledger, packet)
    if not prov:
        return {"status": HOLD,
                "reason": ("the repair proposal did not stay within its permissions"
                          if errs else "the repair proposal answered no finding"),
                "failures": errs, "model_calls": 1, "provider": ident}
    if not text.strip():
        return {"status": HOLD, "reason": "the repair proposal deleted the whole article",
                "model_calls": 1, "provider": ident}
    return {"status": PASS, "article_text": text, "edits": prov,
            "findings_answered": sorted({str(e.get("finding_id")) for e in prov}),
            "rejected_edits": errs, "provider": ident, "model_calls": 1}


def _edit_signature(edits: list) -> tuple:
    """A hashable fingerprint of a proposal's edits, to detect the model repeating the
    same effective edit after a rejection -- not by string identity, by (finding, before,
    after)."""
    return tuple(sorted((str(e.get("finding_id")), str(e.get("original")),
                         str(e.get("repaired"))) for e in (edits or [])))


ORIGIN_SUGGESTED_PATCH = "SUGGESTED_PATCH"
ORIGIN_DETERMINISTIC = "DETERMINISTIC_SUBTRACTION"
ORIGIN_MODEL = "MODEL"

GROUNDING_COMPLETION_DETAIL_KEYS = (
    "grounding_completion_phase", "grounding_completion_history",
    "grounding_completion_iterations", "grounding_repair_proposals",
    "grounding_repairs_accepted", "grounding_repairs_rejected",
    "grounding_deterministic_attempts", "grounding_deterministic_accepted",
    "grounding_suggested_patch_attempts", "grounding_suggested_patch_accepted",
    "accepted_edits", "initial_blocker_count", "final_blocker_count", "model_calls",
    "repairs")


def grounding_completion_detail(result: dict | None) -> dict | None:
    """The audit-bearing subset of a grounding_completion_loop() result.

    Exists because record(GROUNDING, ...) REPLACES st[GROUNDING] wholesale, and both the
    furniture repackage and the post-repackage loop-back record a later Grounding result
    over an earlier completion phase's. Without carrying this forward, a run that
    repaired the article, repackaged, then repaired again persists only the last phase --
    the earlier accepted edits become unreconstructable from the artifact, which is
    exactly how a production repair sequence was lost on 2026-09-09. Returns None for a
    plain grounding result that never went through the loop.
    """
    if not result or "grounding_completion_history" not in result:
        return None
    return {k: result[k] for k in GROUNDING_COMPLETION_DETAIL_KEYS if k in result}


# ── CANDIDATE BLOCKER SNAPSHOTS (audit only, owner-directed, 2026-09-10) ──────────
# WHY. A rejected candidate's own Grounding findings were discarded, so a no_progress
# entry said only "grounding blocker count did not shrink (3 -> 5)". On the retained
# Poetry continuation …-2026-09-09T215810 that made the one question that mattered --
# did the article-surface blocker actually clear, or did it survive? -- unanswerable
# without rerunning a non-deterministic model call, and so the surface-local progress
# question could not be decided either way. The counts were kept and the evidence thrown
# away.
#
# This changes NOTHING about repair, acceptance, progress or the fuse. It records what
# was already computed. Surfaces come from surface_of(), the SAME classifier the loop's
# own target selection and the furniture repackage already use -- no new classification
# anywhere.
BLOCKER_SNAPSHOT_MAX = 12
BLOCKER_SNAPSHOT_QUOTE_CHARS = 160


def blocker_snapshot(findings, package: dict | None) -> list:
    """A compact, inspectable record of a Grounding blocking set: id, classification,
    surface and a trimmed quote per finding. Diagnostic fields only -- never a prompt, a
    transcript, or a copy of the article or the sources."""
    out = []
    for f in (findings or [])[:BLOCKER_SNAPSHOT_MAX]:
        if not isinstance(f, dict):
            out.append({"quote": str(f)[:BLOCKER_SNAPSHOT_QUOTE_CHARS]})
            continue
        quote = str(f.get("quote") or f.get("claim") or "")
        out.append({"id": f.get("id"),
                    "classification": f.get("classification"),
                    "surface": surface_of(quote, package),
                    "quote": quote[:BLOCKER_SNAPSHOT_QUOTE_CHARS]})
    return out


def grounding_completion_loop(
        provider, article_text: str, package: dict | None, initial: dict, ledger: dict,
        packet: dict, arch: dict | None, pack: dict, source_text: str, source_sha: str,
        audit_fn, max_iterations: int = GROUNDING_COMPLETION_MAX_ITERATIONS) -> dict:
    """TRANSACTIONAL, PROGRESS-BOUNDED Grounding completion. Replaces the fixed
    one-repair-plus-one-completion-pass budget (Stage 8b + Stage 8c) with a loop that
    keeps trying bounded local repairs only as long as each one demonstrably leaves the
    article in a strictly better state, subject to a mechanical iteration fuse.

    `initial` is the grounding result already computed by the caller (one model call the
    caller already paid for -- never repeated here). `audit_fn` is the caller's own
    safety_audit() closure (bound to the run's draft/packet/arch/ledger/cut/negative
    lineage), reused exactly as every other post-Writer stage in this run uses it, so a
    candidate is checked against the SAME Safety this run enforces everywhere else.

    Returns a dict shaped like ground_candidate()'s own result (status/blocking/
    grounding_status/...), PLUS `article_text` (the accepted text, `article_text` on the
    input if nothing was ever accepted) and the bookkeeping the caller folds into its own
    calls/repairs dicts: `model_calls`, `iterations`, `proposals`, `accepted`, `rejected`,
    `initial_blocker_count`, `final_blocker_count`.
    """
    accepted_text = article_text
    g = initial
    iterations = proposals = accepted = rejected = 0
    deterministic_attempts = deterministic_accepted = 0
    suggested_patch_attempts = suggested_patch_accepted = 0
    model_calls = 0
    tried = set()
    rejection = None
    history: list = []
    # Every accepted proposal's own edit provenance, flat and in acceptance order -- so
    # "what changed and why" stays fully auditable without a caller having to reassemble
    # it from `history`, the same way g["repair"]["edits"] used to answer that question
    # for the single fixed repair this loop replaces.
    accepted_edits: list = []
    # The Safety verdict for the LAST accepted candidate, exactly as computed inside the
    # loop (with that candidate's own `repair=` baseline widening already applied) -- the
    # caller records THIS, never a fresh re-audit outside the loop, which could omit that
    # widening and reject a candidate this loop already proved passes.
    final_safety = None

    while g["status"] != PASS and iterations < max_iterations:
        # ARTICLE-SURFACE ONLY. This loop edits article text through
        # apply_local_grounding_repair() and nothing else -- it structurally cannot
        # construct an edit for a PACKAGE-surface finding (the quote is never found in
        # the article, so both the deterministic and model paths refuse it every time).
        # Letting a package finding sit in `target` regardless would spend a real
        # iteration -- and a real repair-model call -- discovering that fact anew each
        # time, instead of once. split_by_surface() is the SAME classification the
        # furniture-repackage mechanism already uses to decide what it may rewrite; a
        # package-surface survivor is authoritative here exactly as it is there: it
        # blocks the run (the caller's own terminal check sees it in `g["blocking"]`
        # either way), it just never consumes an article-repair attempt doing so.
        target, _package_only = split_by_surface(repairable_findings(g["blocking"]),
                                                  package)
        if not target:
            break

        iterations += 1
        # PREFERRED ORDER, cheapest-and-most-already-known first:
        #   1. SUGGESTED_PATCH -- the narrow correction the Grounder already wrote when
        #      it diagnosed the claim. Costs no repair-model call at all.
        #   2. DETERMINISTIC_SUBTRACTION -- a model-free deletion decided against the
        #      Ledger. Also free.
        #   3. MODEL -- one repair call, when neither of the above can be constructed.
        # `sig not in tried` is what makes each of these "try once, then fall through":
        # a free candidate that was already rejected would reconstruct identically here,
        # so it is skipped in favour of the next origin rather than retried forever.
        # ORIGIN CHANGES NOTHING ABOUT ACCEPTANCE -- every candidate below reaches the
        # identical Safety check, Grounding recheck and strict-shrink test.
        origin = None
        prop = None
        patch = suggested_patch_candidate(accepted_text, target, ledger, packet)
        if patch is not None and _edit_signature(patch["edits"]) not in tried:
            prop, origin = patch, ORIGIN_SUGGESTED_PATCH
            suggested_patch_attempts += 1
        if prop is None:
            det = deterministic_subtraction_candidate(accepted_text, target, ledger,
                                                      packet)
            if det is not None and _edit_signature(det["edits"]) not in tried:
                prop, origin = det, ORIGIN_DETERMINISTIC
                deterministic_attempts += 1
        if prop is None:
            prop = grounding_repair_proposal(provider, accepted_text, target, ledger,
                                             packet, rejection)
            origin = ORIGIN_MODEL
        used_deterministic = origin == ORIGIN_DETERMINISTIC
        proposals += 1
        model_calls += prop.get("model_calls", 0)

        if prop["status"] != PASS:
            rejected += 1
            rejection = {"reason": prop.get("reason", "the proposal was refused")}
            history.append({"iteration": iterations, "outcome": "no_usable_proposal",
                            "origin": origin, "reason": rejection["reason"],
                            "blockers_before": blocker_snapshot(g["blocking"], package)})
            break

        sig = _edit_signature(prop.get("edits"))
        if sig in tried:
            rejected += 1
            history.append({"iteration": iterations, "outcome": "repeated_proposal",
                            "origin": origin,
                            "blockers_before": blocker_snapshot(g["blocking"], package)})
            break
        tried.add(sig)

        candidate_text = prop["article_text"]
        # `repair=prop` -- same as every other post-repair audit in this run -- so the
        # facts THIS proposal's own edits cited widen the approved baseline exactly as
        # much as they are entitled to, and no more. Without it a legitimate CORRECT_TIME
        # /CORRECT_DATE or attribution-restoring edit could be rejected here for
        # "introducing" surface its own cited facts already license.
        candidate_safety = audit_fn(candidate_text, package, repair=prop)
        model_calls += candidate_safety.get("model_calls", 0)

        if candidate_safety["status"] != PASS:
            rejected += 1
            rejection = {"reason": "introduced a new Safety blocker",
                        "detail": candidate_safety["blocking"][:4]}
            # No blockers_after: Safety rejected this candidate before any Grounding
            # recheck was run, so there is no candidate blocking set to record. `detail`
            # is the SAFETY blocking list, which is the diagnostic for this outcome.
            history.append({"iteration": iterations, "outcome": "safety_rejected",
                            "origin": origin,
                            "deterministic": used_deterministic,
                            "detail": rejection["detail"],
                            "blockers_before": blocker_snapshot(g["blocking"], package)})
            continue

        candidate_grounding = ground_candidate(
            provider, bundle_text(candidate_text, package), source_text, source_sha,
            pack, arch, packet)
        model_calls += candidate_grounding.get("model_calls", 0)

        before_count = len(g["blocking"])
        # Taken BEFORE `g` is replaced by an accepted candidate below.
        before_snapshot = blocker_snapshot(g["blocking"], package)
        if len(candidate_grounding["blocking"]) < before_count:
            accepted += 1
            if used_deterministic:
                deterministic_accepted += 1
            if origin == ORIGIN_SUGGESTED_PATCH:
                suggested_patch_accepted += 1
            accepted_text = candidate_text
            g = candidate_grounding
            final_safety = candidate_safety
            accepted_edits.extend(prop.get("edits") or [])
            rejection = None
            history.append({"iteration": iterations, "outcome": "accepted",
                            "origin": origin,
                            "deterministic": used_deterministic,
                            "blocking_before": before_count,
                            "blocking_after": len(g["blocking"]),
                            "blockers_before": before_snapshot,
                            "blockers_after": blocker_snapshot(g["blocking"], package),
                            "findings_answered": prop.get("findings_answered")})
        else:
            rejected += 1
            rejection = {
                "reason": "grounding blocker count did not shrink (%d -> %d)"
                          % (before_count, len(candidate_grounding["blocking"])),
                "detail": [str(f.get("quote") or "")[:100]
                          for f in candidate_grounding["blocking"][:4]]}
            # THE ENTRY THIS WHOLE CHANGE EXISTS FOR. Both sides, by surface, so
            # "did the article blocker clear while package findings grew?" is answerable
            # off the artifact alone.
            history.append({"iteration": iterations, "outcome": "no_progress",
                            "origin": origin,
                            "deterministic": used_deterministic,
                            "reason": rejection["reason"],
                            "blockers_before": before_snapshot,
                            "blockers_after": blocker_snapshot(
                                candidate_grounding["blocking"], package)})

    out = dict(g)
    out["article_text"] = accepted_text
    out["model_calls"] = model_calls
    out["repairs"] = accepted
    out["grounding_completion_iterations"] = iterations
    out["grounding_repair_proposals"] = proposals
    out["grounding_repairs_accepted"] = accepted
    out["grounding_repairs_rejected"] = rejected
    out["initial_blocker_count"] = len(initial["blocking"])
    out["final_blocker_count"] = len(g["blocking"])
    out["grounding_completion_history"] = history
    out["final_safety"] = final_safety
    out["accepted_edits"] = accepted_edits
    out["grounding_deterministic_attempts"] = deterministic_attempts
    out["grounding_deterministic_accepted"] = deterministic_accepted
    out["grounding_suggested_patch_attempts"] = suggested_patch_attempts
    out["grounding_suggested_patch_accepted"] = suggested_patch_accepted
    return out


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 9b -- ONE SAFETY REPAIR (owner-directed, 2026-09-09)
# ══════════════════════════════════════════════════════════════════════════════
# WHY THIS EXISTS. Real production evidence (three retained Worth-PASS runs, one day)
# showed articles discarded outright for defects this module's own machinery can already
# name precisely and that a bounded, mechanically-verified subtractive edit can already
# fix -- a leaked "the evidence shows" left over from Prose Finish, one unlicensed sensory
# word Continuity's discard fell back onto. Before this stage existed, ANY Safety block
# was terminal: no repair was ever attempted, and a good article with one bad clause died
# exactly like a wrong story. The owner's ruling: a wrong story is refused; a good story
# with a bad sentence is fixed. This is that fix, and nothing more than that fix.
#
# WHAT MAKES A SAFETY FINDING ELIGIBLE. Only categories this module already knows how to
# turn into a QUOTED, LOCATABLE span: MACHINE_LANGUAGE, PACKAGE_MACHINE_LANGUAGE,
# CUT_LEAKAGE, PACKAGE_CUT_LEAKAGE (hard-confidence cut-term leakage only -- the same
# threshold the audit itself already applies), and the unapproved numbers/entities/sensory
# tokens behind NEW_UNSUPPORTED_FACTS / PACKAGE_UNSUPPORTED_FACTS. If EVERY blocking entry
# can be turned into a span, repair is attempted; if even one cannot -- CUT_AUDIT_BLIND
# above all, which the audit's own comment calls "a derivation bug" rather than a named
# defect -- the whole run stays exactly as terminal as it always was. Fail-closed, same as
# every other guard in this file: an unfamiliar category is refused, not guessed at.
#
# THE MECHANICAL GUARANTEE IS THE SAME ONE GROUNDING ALREADY HAS. Synthetic findings in
# Grounding's own {id, classification, quote} shape are handed to the SAME
# apply_grounding_repair() and the SAME REPAIR_OPS/REPAIR_GROUNDING_SCHEMA contract Stage
# 8b already uses, unmodified. No new verification code, no new way for an edit to add a
# fact, an entity or a relation the ledger does not already license -- this stage supplies
# a different set of findings to prove the identical machine check.
#
# ONE CALL. The caller re-audits the result with the existing safety_audit() (unchanged)
# before doing anything else with it. If the repaired text does not pass, that is a
# terminal HOLD: no second repair, no Writer regeneration, no loop.
SAFETY_REPAIRABLE_PREFIXES = (
    "MACHINE_LANGUAGE", "PACKAGE_MACHINE_LANGUAGE",
    "CUT_LEAKAGE", "PACKAGE_CUT_LEAKAGE",
    "NEW_UNSUPPORTED_FACTS", "PACKAGE_UNSUPPORTED_FACTS",
    "CONTINUITY_ADDED_MATERIAL",
    # Article surface only (owner-directed, 2026-09-09, one observed production case).
    # PACKAGE_UNSUPPORTED_NEGATIVES is the package-surface sibling of this same audit and
    # is deliberately NOT included -- this fix is scoped to the one blocker observed.
    "UNSUPPORTED_NEGATIVES",
)

_DELTA_ADDED_RELATION = re.compile(r"^editing added \d+ (\w+) relation")
_DELTA_ADDED_SURFACE = re.compile(
    r"^editing added (numbers|entities|sensory|spatial|scene): (\[.*\])$")


def _nearest_sentence(sentence: str, candidates: list) -> tuple[str, float]:
    """The most similar sentence to `sentence` among `candidates`, by
    difflib.SequenceMatcher ratio -- a deterministic, dependency-free similarity measure,
    used only to tell a rewritten sentence apart from a genuinely new one."""
    best, best_ratio = "", 0.0
    for c in candidates:
        r = difflib.SequenceMatcher(None, sentence, c).ratio()
        if r > best_ratio:
            best, best_ratio = c, r
    return best, best_ratio


# Below this similarity ratio, a candidate sentence has no real counterpart in the
# writer's draft and is read as wholly new rather than reworded.
_REWORDED_SIMILARITY_FLOOR = 0.5


def _continuity_added_spans(draft_text: str, final_text: str,
                            delta_errs: list) -> list | None:
    """Deterministically locate the exact FINAL-text sentence(s) an unexplained
    CONTINUITY_ADDED_MATERIAL error refers to, from a sentence-level diff against the
    writer's own draft -- never a model guessing which prose was added. (Despite the
    error's name, the surface that actually diverged from the draft may be Continuity's
    edit or a later Prose Finish polish -- see the comment on `f = a["continuity_final"]`
    above; this locator does not care which stage did it, only that `final_text` is the
    one the blocking finding was computed from.)

    validate_semantic_delta() (continuity.py) reports two distinct error shapes, and both
    are read here as diagnosis, never as fact: an "added surface" error names its own
    token, which only needs the sentence carrying it. An "added relation" error names
    only a KIND and a whole-article COUNT, with no span of its own -- and a sentence
    merely differing byte-for-byte from every draft sentence is not evidence by itself: a
    single comma moved elsewhere in an otherwise-untouched paragraph makes every sentence
    in it "different" without adding a single relation. So each candidate sentence is
    matched against its own nearest draft counterpart (by difflib ratio) and the relation
    counts are diffed against THAT counterpart, not against zero -- a sentence with no
    real counterpart is compared against nothing, since there is nothing it could have
    carried over. Only a sentence whose OWN relation count of the flagged kind grew
    relative to its nearest counterpart is a candidate. Locating a span this way asserts
    nothing about whether the sentence is TRUE -- that judgment is still the repair
    prompt's and the recheck's -- it only says where to look.

    Fails closed exactly like every other locator in this module: an error shape this
    function does not recognise, or a kind whose added sentence cannot be found, makes
    the WHOLE attempt ineligible rather than partially attempted.
    """
    if not draft_text or not final_text:
        return None
    draft_sents = CE.sentences(draft_text)
    draft_norm = {normalize_span(s) for s in draft_sents}
    added = [s for s in CE.sentences(final_text)
            if normalize_span(s) not in draft_norm]
    out = []
    for err in delta_errs:
        m = _DELTA_ADDED_RELATION.match(err)
        if m:
            kind = m.group(1)
            hits = []
            for s in added:
                nearest, ratio = _nearest_sentence(s, draft_sents)
                before = CE.relations(nearest) if ratio >= _REWORDED_SIMILARITY_FLOOR else {}
                if CE.relations(s).get(kind, 0) > before.get(kind, 0):
                    hits.append(s)
            if not hits:
                return None
            out.extend((s, "continuity added a %s relation not in the writer's own "
                          "draft" % kind) for s in hits)
            continue
        m2 = _DELTA_ADDED_SURFACE.match(err)
        if m2:
            try:
                toks = ast.literal_eval(m2.group(2))
            except (ValueError, SyntaxError):
                return None
            found_any = False
            for tok in toks:
                sent = _sentence_containing(final_text, str(tok))
                if sent and normalize_span(sent) not in draft_norm:
                    out.append((sent, "continuity added %s not in the writer's own "
                                      "draft: %r" % (m2.group(1), tok)))
                    found_any = True
            if not found_any:
                return None
            continue
        return None                        # an error shape this locator does not know
    return out or None


def _safety_locate_findings(sa: dict, allowed_prefixes=SAFETY_REPAIRABLE_PREFIXES
                           ) -> list | None:
    """Turn a passed safety_audit's OWN structured sub-data into quoted, Grounding-shaped
    findings ({id, classification, quote, why}), or None if any blocking category present
    cannot be confidently and safely turned into one. Never guesses a span: a category
    this function does not recognise, or a token/phrase it cannot find verbatim in the
    text, makes the whole result ineligible rather than partially attempted.

    `allowed_prefixes` narrows eligibility below the full SAFETY_REPAIRABLE_PREFIXES set
    -- used by the package-only completion pass (STAGE 9c) to refuse anything but the
    exact machine/provenance-surface categories it is bounded to, even though this
    function already knows how to locate the others too.
    """
    blocking = sa.get("blocking") or []
    if not blocking or any(not any(b.startswith(p) for p in allowed_prefixes)
                           for b in blocking):
        return None
    text = sa.get("audited_text") or ""
    pkg_text = sa.get("audited_package_text") or ""
    findings, seen, n = [], set(), 0

    def add(quote: str, why: str, on_package: bool = False):
        nonlocal n
        span = (quote or "").strip()
        target = pkg_text if on_package else text
        if not span or normalize_span(span) not in normalize_span(target):
            return False
        if span in seen:
            return True
        seen.add(span)
        n += 1
        findings.append({"id": "SF%d" % n, "classification": "TRUE_UNSUPPORTED",
                         "quote": span, "why": why})
        return True

    # blocking is always built from a["continuity_final"] -- screens(final_text) -- which
    # is the surface actually publishing whether or not Continuity's own edit survived
    # (composition.py's own "f = a['continuity_final']" is unconditional; the key name
    # predates the fallback and does not mean Continuity specifically). Never look at
    # a["writer_draft"] here: it is a different, pre-fallback surface the blocking list
    # was not computed from, and locating a finding against it could quote text that
    # was never actually published.
    for surface, key in (("article", "continuity_final"),
                         ("publication_package", "publication_package")):
        audits = (sa.get("audits") or {}).get(key) or {}
        on_pkg = surface == "publication_package"
        for frame, _n in (audits.get("prose_leaks") or {}).get("frames") or []:
            sent = _sentence_containing(pkg_text if on_pkg else text, frame)
            if not add(sent or frame, "machine/provenance language: %r" % frame, on_pkg):
                return None
        for name in (audits.get("scaffold") or {}).get("leaked") or []:
            sent = _sentence_containing(pkg_text if on_pkg else text, name)
            if not add(sent or name, "scaffold name leaked into prose: %r" % name, on_pkg):
                return None
        for v in (audits.get("cut_adherence") or {}).get("violations") or []:
            if cut_term_confidence(v["term"]) != CUT_HIGH:
                continue
            sent = _sentence_containing(pkg_text if on_pkg else text, v["match"])
            if not add(sent or v["match"],
                       "cut term leaked into prose: %r" % v["match"], on_pkg):
                return None
        surf = (audits.get("factual_surface") or {})
        for tok in (list(surf.get("unapproved_sensory") or [])
                   + list(surf.get("unapproved_numbers") or [])):
            sent = _sentence_containing(pkg_text if on_pkg else text, str(tok))
            if not add(sent, "unlicensed factual surface: %r" % tok, on_pkg):
                return None
        for ent in surf.get("unapproved_entities") or []:
            sent = _sentence_containing(pkg_text if on_pkg else text, ent)
            if not add(sent, "unlicensed entity: %r" % ent, on_pkg):
                return None

    # CONTINUITY_ADDED_MATERIAL is article-only (Continuity never touches the package),
    # and unlike the categories above it has no per-surface sub-audit to read spans from
    # -- it is a whole-article delta against the writer's own draft. See
    # _continuity_added_spans for how a span is recovered from that delta.
    delta_errs = sa.get("semantic_delta_errors") or []
    if delta_errs:
        spans = _continuity_added_spans(sa.get("audited_draft_text") or "", text,
                                        delta_errs)
        if not spans:
            return None
        for span, why in spans:
            if not add(span, why):
                return None

    # UNSUPPORTED_NEGATIVES is article-only for this fix (its package-surface sibling,
    # PACKAGE_UNSUPPORTED_NEGATIVES, is out of scope -- see SAFETY_REPAIRABLE_PREFIXES).
    # Unlike CONTINUITY_ADDED_MATERIAL, the finding already carries the exact offending
    # sentence -- negative_admission_audit (story.py) reports the full sentence, not a
    # fragment -- so no diff or token search is needed, only the same verbatim-in-text
    # check every other category here already uses.
    neg = ((sa.get("audits") or {}).get("continuity_final") or {}).get(
        "negative_admission") or {}
    for h in neg.get("unmatched") or []:
        sent = h.get("sentence") or ""
        if not add(sent, "unsupported negative relation -- no ledger fact licenses "
                         "this negation: %r" % sent):
            return None
    return findings or None


def safety_repair_findings(sa: dict, article_text: str, pkg_text: str = "",
                           draft_text: str = "",
                           allowed_prefixes=SAFETY_REPAIRABLE_PREFIXES) -> list | None:
    """Public entry: attach the audited surfaces safety_audit did not carry forward on
    its own result, then locate. See _safety_locate_findings for the eligibility rule.

    `draft_text` is the writer's own draft (pre-Continuity) -- needed only to locate a
    CONTINUITY_ADDED_MATERIAL span (see _continuity_added_spans); every other category
    locates from `sa` and `article_text` alone, as before.

    `allowed_prefixes` -- see _safety_locate_findings.
    """
    sa = dict(sa, audited_text=article_text, audited_package_text=pkg_text,
             audited_draft_text=draft_text)
    return _safety_locate_findings(sa, allowed_prefixes)


REPAIR_SAFETY_SYSTEM = (
    "You are removing specific safety-screen defects from a finished, otherwise-approved "
    "article. A mechanical screen has named the exact passages: language that names the "
    "article's own machinery (\"the evidence\", \"the record\", a scaffold name), a term "
    "that was supposed to stay cut, or a word/number/name the frozen evidence does not "
    "carry. The evidence is frozen and is the same evidence the article was written from.\n"
    "\n"
    "YOU ARE AN EXCISING EDITOR, NOT A WRITER. You take words OUT of a sentence that is "
    "already there. You do not compose a better sentence and put it back.\n"
    "\n"
    "PREFER DELETION OVER REPLACEMENT. In order: cut the offending word or phrase and "
    "leave the rest of the sentence untouched; if that will not do, cut the clause; if "
    "that will not do, delete the sentence. Re-writing the sentence around the problem is "
    "the one move that is never available.\n"
    "\n"
    "COPY `original` VERBATIM. Character for character from the article, including "
    "punctuation and capitalisation. An `original` that is not found in the article word "
    "for word is refused and the finding goes unanswered.\n"
    "\n"
    "THE REPAIRED SENTENCE MUST BE WEAKER THAN THE ORIGINAL, NEVER STRONGER, and may "
    "introduce no number, name or relation (cause, consequence, equivalence, comparison, "
    "superlative, generalisation, negation, absence, time) the original did not already "
    "carry, unless a fact you cite carries it. If deleting the flagged word leaves an "
    "ungrammatical sentence, delete the smallest surrounding unit that reads cleanly "
    "instead -- a clause, or the whole sentence.\n"
    "\n"
    "Use operation DELETE for anything you can simply remove; use NARROW only when a "
    "narrower true wording, licensed by a cited fact, survives.\n"
    "\n"
    "UNSUPPORTED NEGATIVE RELATIONS HAVE ZERO FACTUAL PERMISSION. A finding that quotes a "
    "sentence asserting an absence, an exclusivity or a comparison (\"none of them are\", "
    "\"the only one that\", \"unlike the others\") with no ledger fact behind it is not "
    "fixed by asserting the opposite -- \"none are alike\" does not become \"they are "
    "alike\". Both directions are claims the evidence does not make. Delete the negative "
    "relation, or narrow the sentence to what the cited fact actually states; never turn "
    "an unsupported \"not X\" into an unsupported (or any) \"X\".\n"
    "\n"
    "You may not touch a sentence no finding names, and you may not improve style "
    "anywhere else."
)


def safety_repair(provider, article_text: str, findings: list, ledger: dict,
                  packet: dict) -> dict:
    """STAGE 9b. Exactly one call. Subtractive, mechanically audited by the SAME
    apply_grounding_repair() Stage 8b uses, and never repeated."""
    if not findings:
        return {"status": SKIPPED, "reason": "no repairable finding", "model_calls": 0}
    obj, ident = _ask(provider, REPAIR_SAFETY_SYSTEM,
                      repair_prompt(article_text, findings, ledger),
                      4_000, SAFETY, SAFETY_HOLD)
    edits = obj.get("edits")
    if not isinstance(edits, list) or not edits:
        return {"status": HOLD, "reason": "the safety repair returned no edits",
                "model_calls": 1, "provider": ident}
    text, prov, errs = apply_grounding_repair(article_text, edits, findings, ledger, packet)
    if not prov or not text.strip():
        return {"status": HOLD,
                "reason": "the safety repair did not stay within its permissions"
                         if errs else "the safety repair deleted the whole article",
                "failures": errs, "model_calls": 1, "provider": ident}
    return {"status": PASS, "article_text": text, "edits": prov,
            "findings_answered": [f.get("id") for f in findings],
            "rejected_edits": errs,
            "provider": ident, "model_calls": 1, "repairs": 1}


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 9c -- ONE PACKAGE-ONLY SAFETY REPAIR (owner-directed, 2026-09-09)
# ══════════════════════════════════════════════════════════════════════════════
# WHY THIS EXISTS. Two live continuations of the same retained Worth-PASS article
# reproduced an identical mechanism: the article-body Safety repair (Stage 9b) correctly
# removed a machine-language leak, the package is then REGENERATED from the repaired
# article by its own fresh model call (make_package() -> editorial_package(), a real
# call this module has always made and does not touch here), and the regenerated
# title/dek reintroduced the exact same leaked phrase -- "the evidence" -- because the
# article's actual subject matter makes that a natural phrase to reach for. The one
# general Safety repair had already been spent on the article body, so a defect in prose
# that did not exist until AFTER that repair ran had no opportunity of its own, and the
# article HELD on a surface Stage 9b was never shown.
#
# THE DIAGNOSIS THE OWNER GAVE, exactly: Safety was not too strict. A new model-generated
# surface (the regenerated package) is created AFTER the article repair, and the article
# repair cannot repair text that did not exist yet.
#
# NARROW ON PURPOSE. Eligible ONLY for the exact machine/provenance-surface categories
# this module already knows how to locate on the package surface --
# PACKAGE_MACHINE_LANGUAGE and PACKAGE_CUT_LEAKAGE (the same hard-confidence threshold
# CUT_LEAKAGE itself uses) -- via the SAME _safety_locate_findings() Stage 9b uses,
# restricted to just these two prefixes. PACKAGE_UNSUPPORTED_FACTS and
# PACKAGE_UNSUPPORTED_NEGATIVES are deliberately excluded: those are factual-surface
# claims, not machine language, and this stage is not the place to widen factual
# permission. If ANY remaining blocking finding is outside this pair -- including a
# genuine factual package defect -- the whole attempt is ineligible and the run falls
# straight through to the unchanged terminal HOLD below, exactly as before this stage
# existed.
#
# THIS RUNS ONLY AFTER THE ARTICLE ITSELF IS ALREADY SAFETY-CLEAN. The eligibility check
# above is also the proof of that: PACKAGE_* categories can only be present in
# `sa["blocking"]` alongside a clean article, because every article-surface category
# uses a different, non-"PACKAGE_"-prefixed name. There is no separate flag to keep in
# sync with that fact -- it falls out of the same one check.
#
# THE PACKAGE FIELDS ONLY -- never the article body. apply_package_safety_repair()
# verifies each edit the same way apply_grounding_repair() verifies Safety's and
# Grounding's own repairs: `original` must be an exact quote found in the ONE package
# field it names (title/dek/homepage_excerpt/meta_description/social_hook), and
# `repaired` may add no number or entity the article or the licensed packet did not
# already carry. No fact_ids, no Ledger-cited widening -- a package fix only ever
# subtracts or paraphrases machine language, it never needs to add anything a citation
# could license.
#
# NO REGENERATION AFTER THIS. The repaired package dict, once accepted, IS what proceeds
# downstream -- there is no second make_package() call here and none after this stage
# returns, so the surface Safety's final recheck approves is the exact surface Grounding,
# Fact Check and the Reader (and the publication bridge, downstream of all of them) will
# see. That is the sequencing bug this stage exists to close, not just its eligible
# category list.
#
# ONE CALL, then the SAME final safety recheck Stage 9b already runs. No second package
# repair, no article regeneration, no roulette.
PACKAGE_ONLY_SAFETY_REPAIRABLE_PREFIXES = ("PACKAGE_MACHINE_LANGUAGE", "PACKAGE_CUT_LEAKAGE")


def _package_field_containing(text: str, package: dict) -> str | None:
    """Which PACKAGE FIELD KEY (not the human-facing surface label surface_of() returns)
    carries this quote, so an edit can be applied to the exact field it targets."""
    q = normalize_span(text or "")
    if not q or not package:
        return None
    for field, _label in PACKAGE_SURFACE_LABELS:
        v = normalize_span(str(package.get(field) or ""))
        if len(v) >= 12 and len(q) >= 12 and (q in v or v in q):
            return field
    return None


def apply_package_safety_repair(package: dict, edits: list, findings: list,
                                packet: dict) -> tuple:
    """Apply subtractive edits to PACKAGE FIELDS only. Returns (package, provenance,
    errs) -- a new package dict, never a mutation of the one passed in.

    Same discipline as apply_grounding_repair(), adapted to a package's shape (five
    named fields, not one string): every edit answers a real finding, its `original`
    must be found verbatim in the ONE field it names, and its `repaired` wording may add
    no number or entity the article/packet did not already license. There is no
    fact_ids widening here -- this stage only ever subtracts or paraphrases machine
    language, which needs no new permission to remove.
    """
    ids = {str(f.get("id")) for f in findings}
    approved = ST.render(packet)
    a_nums = _numbers_of(approved)
    a_ents = ST._entities(approved, skip_sentence_initial=False)
    out = dict(package or {})
    prov, errs = [], []
    for i, e in enumerate(edits or [], 1):
        if not isinstance(e, dict):
            errs.append("edit %d is not an object" % i)
            continue
        fid = str(e.get("finding_id") or "")
        orig = (e.get("original") or "").strip()
        rep = (e.get("repaired") or "").strip()
        op = e.get("operation")
        if fid not in ids:
            errs.append("edit %d cites finding %r, which was not reported" % (i, fid))
            continue
        if op not in REPAIR_OPS:
            errs.append("edit %d has operation %r, not one of %s"
                        % (i, op, ", ".join(REPAIR_OPS)))
            continue
        field = _package_field_containing(orig, out)
        if field is None:
            errs.append("edit %d: the original is not in any package field: %r"
                        % (i, orig[:80]))
            continue
        target = out.get(field) or ""
        if not orig or normalize_span(orig) not in normalize_span(target):
            errs.append("edit %d: the original is not in field %s: %r"
                        % (i, field, orig[:80]))
            continue
        if orig not in target:
            errs.append("edit %d: quoted text does not match field %s exactly "
                        "(whitespace or punctuation drift) -- refused rather than "
                        "guessed at" % (i, field))
            continue
        new_nums = sorted(_numbers_of(rep) - _numbers_of(orig) - a_nums)
        new_ents = sorted(ST._entities(rep) - ST._entities(orig) - a_ents)
        if new_nums or new_ents:
            errs.append("edit %d ADDS rather than subtracts -- numbers=%s entities=%s "
                        "(a package fix may only remove or paraphrase, never add)"
                        % (i, new_nums, new_ents))
            continue
        out[field] = target.replace(orig, rep, 1) if rep else target.replace(orig, "", 1)
        prov.append({"finding_id": fid, "operation": op, "field": field,
                     "original": orig, "repaired": rep})
    return out, prov, errs


REPAIR_PACKAGE_SAFETY_SYSTEM = (
    "You are removing specific safety-screen defects from the PUBLICATION PACKAGE of a "
    "finished, already-approved, already Safety-clean article -- its title, dek, "
    "homepage excerpt, meta description and social hook. A mechanical screen has named "
    "the exact package field and the exact phrase: language that names the article's "
    "own machinery (\"the evidence\", \"the record\") or a term that was supposed to "
    "stay cut.\n"
    "\n"
    "YOU ARE EDITING PACKAGE FIELDS ONLY. Not the article body -- it is not shown to "
    "you and no finding here concerns it. Each field stands alone; a fix to the dek "
    "does not touch the title, the excerpt, or any other field.\n"
    "\n"
    "PREFER DELETION OVER REPLACEMENT. Cut the offending word or phrase and leave the "
    "rest of the field untouched; if that leaves the field ungrammatical or empty, "
    "paraphrase the field into ordinary reader-facing language that says the same "
    "thing without naming the article's own apparatus.\n"
    "\n"
    "COPY `original` VERBATIM from the field you are fixing. An `original` not found "
    "word for word in that field is refused and the finding goes unanswered.\n"
    "\n"
    "ADD NOTHING. No number, name, place or claim the field did not already carry. A "
    "package fix only ever removes or rephrases; it never adds a fact, an entity, an "
    "angle, or a reason for the article to exist that the article itself does not "
    "already carry.\n"
    "\n"
    "You may not touch a field no finding names."
)


def package_repair_prompt(package: dict, findings: list, ledger: dict) -> str:
    L = ["THE PACKAGE FIELDS"]
    for field, label in PACKAGE_SURFACE_LABELS:
        v = str((package or {}).get(field) or "").strip()
        if v:
            L += ["", "%s (%s)" % (label, field), "  %s" % v]
    L += ["", "WHAT THE SAFETY SCREEN FOUND"]
    for f in findings:
        L += ["", "FINDING %s  [%s]" % (f.get("id"), f.get("classification")),
             "  passage : %s" % str(f.get("quote"))[:400],
             "  why     : %s" % str(f.get("why"))[:600]]
    L += ["", REPAIR_GROUNDING_SCHEMA]
    return "\n".join(L)


def package_safety_repair(provider, package: dict, findings: list, ledger: dict,
                          packet: dict) -> dict:
    """STAGE 9c. Exactly one call. Subtractive, package-fields-only, mechanically
    audited by apply_package_safety_repair(), and never repeated."""
    if not findings:
        return {"status": SKIPPED, "reason": "no repairable package finding",
                "model_calls": 0}
    obj, ident = _ask(provider, REPAIR_PACKAGE_SAFETY_SYSTEM,
                      package_repair_prompt(package, findings, ledger),
                      2_000, SAFETY, SAFETY_HOLD)
    edits = obj.get("edits")
    if not isinstance(edits, list) or not edits:
        return {"status": HOLD, "reason": "the package repair returned no edits",
                "model_calls": 1, "provider": ident}
    pkg, prov, errs = apply_package_safety_repair(package, edits, findings, packet)
    if not prov:
        return {"status": HOLD,
                "reason": "the package repair did not stay within its permissions",
                "failures": errs, "model_calls": 1, "provider": ident}
    return {"status": PASS, "package": pkg, "edits": prov,
            "findings_answered": [f.get("id") for f in findings],
            "rejected_edits": errs,
            "provider": ident, "model_calls": 1, "repairs": 1}


# ══════════════════════════════════════════════════════════════════════════════
# POST-REPAIR SAFETY COMPLETION -- the ONE semantic owner of STAGE 9c, shared
# ══════════════════════════════════════════════════════════════════════════════
# WHY THIS EXISTS. STAGE 9c above was written once, for the article-repair path: repair
# the article body, make_package() regenerates the package from the repaired article, and
# the fresh package can reintroduce the exact machine-language leak the article repair
# just removed ("the evidence" is a natural phrase to reach for on this subject). That
# path already tries one package-only repair before holding.
#
# But the article-repair path is not the only place this module calls make_package() on
# text a repair produced and then re-audits the result: Reader repair regenerates a
# package from its rewritten article the same way, and Grounding's furniture-only
# repackage (see repackage_if_only_the_furniture_failed, below) regenerates a package with
# explicit refusals for the same reason. Both used to go straight to a HOLD on a Safety
# failure, because STAGE 9c's package-only retry lived only in the article-repair branch
# -- copying its body into each new call site would give this rule three places to drift
# out of sync. This function is the one place it is implemented; every call site above
# calls it and does its own re-audit + bookkeeping afterward, exactly as STAGE 9c always
# has.
#
# NOT A NEW MECHANISM. Same eligibility (PACKAGE_ONLY_SAFETY_REPAIRABLE_PREFIXES, via the
# same safety_repair_findings()/_safety_locate_findings() STAGE 9b uses), same one-call
# package_safety_repair(), same "article must already be Safety-clean" property that falls
# out of the prefix check rather than a separate flag. It does not audit and does not touch
# a caller's calls/repairs/record() bookkeeping -- those differ by call site (attributed to
# SAFETY, READER or GROUNDING's own stage depending on who is calling), so bookkeeping stays
# with the caller, the same way it always has for STAGE 9c.
# ── WHY ONE SHOT WAS NEVER ENOUGH (owner-directed, 2026-09-09; production-verified) ──
# Retained Poetry continuation …-2026-09-09T203816 HELD at SAFETY on
# `PACKAGE_MACHINE_LANGUAGE: frames [('the evidence', 2)]` with
# after_package_safety_repair already true. The repair had not failed, and it had not
# stalled. It had been shown one third of the problem:
#
#   dek              "Among THE EVIDENCE that poems move anyone: ..."   <- repaired
#   homepage_excerpt "THE EVIDENCE cited for it is bodily: ..."         <- never shown
#   meta_description "... and THE EVIDENCE behind it."                  <- never shown
#
# The audit reports machine language as FRAMES -- (phrase, count) -- so three leaks in
# three different fields collapse into the single frame ('the evidence', 3), and
# _safety_locate_findings emits one finding per FRAME, quoting the FIRST sentence that
# carries it. One finding, one field, one correct edit, 3 -> 2, budget spent, terminal
# HOLD. Reconstructed deterministically from the retained artifact, not inferred.
#
# So the missing capability is not a better locator or a cleverer prompt: each pass does
# exactly what it should and each pass strictly improves the package. What was arbitrary
# was stopping after the first one. This replaces MAX = 1 with STRICT PROGRESS, the same
# semantics grounding_completion_loop already uses on the article surface: keep going
# only while the canonical package blocker set genuinely shrinks.
#
# NOTHING ELSE WIDENS. Same two eligible categories, same one-call
# package_safety_repair(), same apply_package_safety_repair() permission check, same five
# package prose fields, never the article body. Article Safety repair semantics are
# untouched.
#
# NO DETERMINISTIC PATH HERE, DELIBERATELY. The article surface has one
# (deterministic_subtraction_candidate) because a sentence can be dropped from a
# paragraph and leave prose behind. A package field is one or two sentences that must
# still read as a dek or a meta description afterwards, and "delete the sentence carrying
# the frame" can empty the field of its only substance. Deleting just the phrase leaves
# grammar this module cannot mechanically verify. Per the owner's own escape clause --
# if deterministic deletion is not clearly safe, use the model repair -- there is no
# deterministic package edit in this task, and no vocabulary rewriter.
PACKAGE_SAFETY_COMPLETION_MAX_ITERATIONS = 5


def package_blocker_signature(sa: dict) -> list:
    """The CANONICAL package blocker multiset for a safety_audit result -- what "strict
    progress" is measured against.

    Read from the audit's OWN structured publication_package sub-data, never from the
    blocking STRINGS, because a string is not a count: three leaks of one phrase in three
    fields render as the one entry `PACKAGE_MACHINE_LANGUAGE: frames [('the evidence',
    3)]`, and so do two, and so does one. Counting strings would call 3 -> 2 "no
    progress" and stop the loop on its first genuinely successful iteration. A frame with
    count n therefore contributes n entries.

    Sorted, so it compares as a multiset: strictly fewer entries is progress; the same
    number of DIFFERENT entries is not.
    """
    a = (sa.get("audits") or {}).get("publication_package") or {}
    sig: list = []
    for frame, n in (a.get("prose_leaks") or {}).get("frames") or []:
        try:
            n = int(n)
        except (TypeError, ValueError):
            n = 1
        sig.extend([("machine_language", str(frame))] * max(n, 1))
    for name in (a.get("scaffold") or {}).get("leaked") or []:
        sig.append(("scaffold", str(name)))
    for v in (a.get("cut_adherence") or {}).get("violations") or []:
        if cut_term_confidence(str(v.get("term") or "")) == CUT_HIGH:
            sig.append(("cut_term", str(v.get("match"))))
    surf = a.get("factual_surface") or {}
    for key in ("unapproved_entities", "unapproved_numbers", "unapproved_sensory",
                "unapproved_spatial", "unapproved_scene"):
        for tok in surf.get(key) or []:
            sig.append((key, str(tok)))
    return sorted(sig)


def _package_blockers_only(sa: dict) -> bool:
    """Every blocking entry is package-surface. An article-body blocker appearing during
    a package-only loop means something outside this loop's remit changed, and the
    candidate is refused rather than reasoned about."""
    b = sa.get("blocking") or []
    return bool(b) and all(str(x).startswith("PACKAGE_") for x in b)


def _carry_package_completion(sa: dict, prep: dict) -> None:
    """Attach the package completion's own audit to the Safety record that replaces it.

    record(SAFETY, ...) writes a fresh safety_audit result, which knows nothing about the
    repair sequence that produced the package it just approved. Without this, a run that
    took three package iterations persists as though the package had simply been clean --
    the same audit loss grounding_completion_detail() exists to prevent on the article
    side. Cheap, additive, and read straight off the completion result."""
    for k in ("package_completion_iterations", "package_completion_history",
              "package_repairs_accepted", "package_repairs_rejected",
              "package_initial_blocker_count", "package_final_blocker_count"):
        if k in prep:
            sa[k] = prep[k]


def package_only_safety_completion(provider, sa: dict, final_text: str, package: dict | None,
                                   ledger: dict, packet: dict, draft_text: str,
                                   audit_fn=None,
                                   max_iterations: int = PACKAGE_SAFETY_COMPLETION_MAX_ITERATIONS
                                   ) -> dict:
    """PROGRESS-BOUNDED package-only Safety completion (STAGE 9c). Given a FAILED
    safety_audit() result `sa` for (final_text, package), repair the package -- and only
    the package -- for as long as each accepted repair provably shrinks the canonical
    package blocker set.

    Returns {"attempted": False} if nothing in `sa["blocking"]` is eligible (no model call
    spent), else {"attempted": True, "findings": <the first pass's findings>, "repair":
    {...}}. `repair` keeps the shape every existing call site already reads: status PASS
    with the accepted package at repair["package"] when at least one repair was accepted,
    HOLD otherwise, and `model_calls` totalling the whole loop. Callers re-audit
    afterwards exactly as they always have -- safety_audit() is deterministic and
    model-free, so that costs nothing and keeps each call site's own bookkeeping
    unchanged.

    TRANSACTIONAL. Every proposal is applied to a TEMPORARY package and re-audited
    against the EXACT same article; the accepted package is replaced only once a
    candidate has passed all three acceptance rules, so a rejected proposal leaves it
    byte-for-byte as it was. `audit_fn(article, package)` is the caller's own
    safety_audit closure -- the same Safety this run enforces everywhere else, never a
    re-derivation. Omitting it keeps the historical single-attempt behaviour, so a caller
    that cannot supply one is never silently upgraded to a loop it did not ask for.
    """
    pfindings = safety_repair_findings(
        sa, final_text, package_prose(package), draft_text=draft_text,
        allowed_prefixes=PACKAGE_ONLY_SAFETY_REPAIRABLE_PREFIXES)
    if not pfindings:
        return {"attempted": False}

    prep = package_safety_repair(provider, package, pfindings, ledger, packet)
    if audit_fn is None:
        return {"attempted": True, "findings": pfindings, "repair": prep}

    accepted_pkg = package
    accepted = rejected = 0
    model_calls = prep.get("model_calls", 0)
    iterations = 1
    history: list = []
    accepted_edits: list = []
    tried = set()
    before_sig = package_blocker_signature(sa)
    initial_count = len(before_sig)
    current = prep

    while True:
        if current["status"] != PASS:
            rejected += 1
            history.append({"iteration": iterations, "outcome": "no_usable_proposal",
                            "reason": current.get("reason", "the proposal was refused")})
            break

        sig = _edit_signature(current.get("edits"))
        if sig in tried:
            rejected += 1
            history.append({"iteration": iterations, "outcome": "repeated_proposal"})
            break
        tried.add(sig)

        candidate_pkg = current["package"]
        candidate_sa = audit_fn(final_text, candidate_pkg)
        model_calls += candidate_sa.get("model_calls", 0)
        after_sig = package_blocker_signature(candidate_sa)

        # RULE 1: no article-body blocker introduced. RULE 2: no new factual package
        # surface -- an entity, number or relation the package did not carry shows up
        # here as a PACKAGE_ category outside the two this stage is bounded to, and is
        # refused rather than repaired. RULE 3: the canonical set strictly shrinks.
        if candidate_sa["status"] != PASS and not _package_blockers_only(candidate_sa):
            rejected += 1
            history.append({"iteration": iterations, "outcome": "article_blocker_introduced",
                            "detail": (candidate_sa.get("blocking") or [])[:4]})
            break
        ineligible = [b for b in (candidate_sa.get("blocking") or [])
                      if not any(str(b).startswith(pre)
                                 for pre in PACKAGE_ONLY_SAFETY_REPAIRABLE_PREFIXES)]
        if ineligible:
            rejected += 1
            history.append({"iteration": iterations, "outcome": "factual_blocker_introduced",
                            "detail": ineligible[:4]})
            break
        if len(after_sig) >= len(before_sig):
            rejected += 1
            history.append({"iteration": iterations, "outcome": "no_progress",
                            "reason": "package blocker count did not shrink (%d -> %d)"
                                      % (len(before_sig), len(after_sig))})
            break

        accepted += 1
        accepted_pkg = candidate_pkg
        accepted_edits.extend(current.get("edits") or [])
        history.append({"iteration": iterations, "outcome": "accepted",
                        "blocking_before": len(before_sig),
                        "blocking_after": len(after_sig),
                        "fields": sorted({e.get("field")
                                          for e in current.get("edits") or []})})
        before_sig = after_sig
        sa = candidate_sa

        if candidate_sa["status"] == PASS or not after_sig:
            break
        if iterations >= max_iterations:
            history.append({"iteration": iterations, "outcome": "iteration_ceiling"})
            break

        nxt = safety_repair_findings(
            sa, final_text, package_prose(accepted_pkg), draft_text=draft_text,
            allowed_prefixes=PACKAGE_ONLY_SAFETY_REPAIRABLE_PREFIXES)
        if not nxt:
            history.append({"iteration": iterations, "outcome": "no_eligible_findings"})
            break
        iterations += 1
        current = package_safety_repair(provider, accepted_pkg, nxt, ledger, packet)
        model_calls += current.get("model_calls", 0)

    if accepted:
        repair = {"status": PASS, "package": accepted_pkg, "edits": accepted_edits,
                  "findings_answered": [f.get("id") for f in pfindings],
                  "provider": current.get("provider") or prep.get("provider"),
                  "model_calls": model_calls, "repairs": accepted}
    elif prep.get("status") == PASS:
        # THE TRANSACTIONAL BOUNDARY. package_safety_repair() said PASS because the EDIT
        # was within its permissions -- that is not the same thing as the loop having
        # accepted the resulting package, which it did not (no progress, or the candidate
        # introduced a blocker). Returning prep unchanged here would hand every existing
        # call site a `repair["package"]` to adopt, silently publishing a package the
        # acceptance rules had just refused. Caught by
        # test_a_new_factual_package_blocker_stops_the_loop.
        repair = {"status": HOLD,
                  "reason": "the package repair was refused by the completion rules: %s"
                            % (history[-1].get("outcome") if history else "no progress"),
                  "provider": prep.get("provider"), "model_calls": model_calls}
    else:
        repair = dict(prep, model_calls=model_calls)
    repair["package_completion_iterations"] = iterations
    repair["package_completion_history"] = history
    repair["package_repairs_accepted"] = accepted
    repair["package_repairs_rejected"] = rejected
    repair["package_initial_blocker_count"] = initial_count
    repair["package_final_blocker_count"] = len(before_sig)
    return {"attempted": True, "findings": pfindings, "repair": repair}


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 8c -- ONE GROUNDING COMPLETION PASS
# ══════════════════════════════════════════════════════════════════════════════
# WHY THIS EXISTS, and why it is not "another repair". Two production runs showed the
# same shape: the one repair was correct, applied cleanly, added nothing, and was still
# incomplete, because the article made ONE unsupported claim in TWO places.
#
#   production-20260907T173433Z-ab65bb22 (Lubetkin)
#       "for buildings of exceptional interest"          <- repaired
#       "marks the building as of exceptional interest"  <- survived, same claim
#
#   production-20260907T191059Z-90687a49 (Daily Nous)
#       "a single dial standing for how far a democracy falls short of fully
#        transferring policy authority to the majority"  <- repaired
#       "The dial the veto is mapped onto measures the arrangement: it records
#        that redistributive authority can now be overridden"  <- survived
#
# The second pair shares almost no wording. Seeing them as one proposition is semantic
# work, and instructing the first repair to "find every occurrence" did not achieve it --
# #104 shipped that instruction and the Daily Nous run still left one behind. What DID
# work, both times, is the recheck: it found the survivor precisely and described it.
#
# So the missing capability is not a better first repair. It is one more subtractive pass
# aimed at a residue the Grounder has already located and named. That is a much smaller
# problem than the first repair solves, and it is bounded accordingly.
#
# WHAT KEEPS THIS FROM BECOMING A RETRY LOOP. Completion runs at most once, only after a
# first repair that actually applied edits, only on findings the Grounder itself marked
# repairable, only when at most COMPLETION_MAX_FINDINGS of them survive, and its edits go
# through the SAME apply_grounding_repair contract -- the same relation checks, the same
# refusal to add. One final recheck follows, and whatever it says is final. There is no
# third pass and the code has nowhere to put one.
COMPLETION_MAX_FINDINGS = 2

COMPLETION_GROUNDING_SYSTEM = (
    "One correction pass has already run on this article and was accepted. The grounder "
    "has read the corrected article and found that a claim it does not support is still "
    "there -- usually because the article made the same claim twice and only one place "
    "was fixed. Your job is to remove what is left.\n"
    "\n"
    "THIS IS THE LAST PASS. Nothing runs after it except the grounder, once. A claim you "
    "leave standing is a claim that stays in the article or costs it publication.\n"
    "\n"
    "REMOVE, DO NOT REPHRASE. Prefer deleting the sentence. If the sentence carries "
    "something the evidence does support, cut only the unsupported part and leave the "
    "rest exactly as it is. Do not re-say the claim more carefully -- a more careful "
    "version of an unsupported claim is an unsupported claim.\n"
    "\n"
    "COPY `original` VERBATIM, character for character from the article below. An "
    "`original` that is not found word for word is refused and the finding goes "
    "unanswered.\n"
    "\n"
    "THE SAME MACHINE CHECK APPLIES TO YOU. Your wording may introduce no number, no "
    "name, and no relation the original sentence and your cited facts did not already "
    "carry. Connectives are relations: cause, consequence, equivalence, comparison, "
    "superlative, generalisation, negation, absence and time. Join surviving halves with "
    "a full stop rather than a connective, or delete one of them.\n"
    "\n"
    "AND LOOK ONCE MORE FOR ANOTHER COPY. The reason you are here is that a claim was "
    "made in more than one place. Before you finish, read the whole article again for the "
    "same claim in different words. Emit one edit per place, all citing the same "
    "finding_id.\n"
    "\n"
    "You may not touch a sentence that no finding names, and you may not improve style "
    "anywhere. If a flagged passage cannot be fixed by removing words, delete it."
)


def completion_prompt(article_text: str, findings: list, ledger: dict) -> str:
    """Deliberately thin. The corrected article, the surviving findings, and the facts
    those findings cite -- nothing else. No architecture, no writer packet, no worth, no
    research beyond the cited support, and none of the findings the first repair already
    answered."""
    L = ["THE ARTICLE, AS ALREADY CORRECTED ONCE", article_text, "",
         "WHAT THE GROUNDER STILL FINDS UNSUPPORTED"]
    for f in findings:
        L += ["", "FINDING %s  [%s]" % (f.get("id"), f.get("classification")),
              "  passage : %s" % str(f.get("quote"))[:400],
              "  why     : %s" % str(f.get("why"))[:600]]
        if f.get("suggested_patch"):
            L.append("  a narrower wording the grounder believes is supported: %s"
                     % str(f["suggested_patch"])[:300])
        rel = _relevant_facts(str(f.get("quote") or ""), ledger,
                              str(f.get("why") or ""))
        if rel:
            L.append("  THE FROZEN EVIDENCE FOR THIS PASSAGE:")
            for fid, fact in rel:
                L.append("    %s  %s" % (fid, fact.get("proposition", "")[:220]))
                if fact.get("support_span"):
                    L.append("        span: %r" % fact["support_span"][:200])
    L += ["", REPAIR_GROUNDING_SCHEMA]
    return "\n".join(L)


def completion_eligible(grounding: dict, repair: dict | None) -> tuple:
    """May the one completion pass run? (ok, reason, findings).

    Every condition is a reason to NOT run it. Pure and side-effect free so the decision
    can be tested without a provider.
    """
    if not isinstance(repair, dict) or repair.get("status") != PASS:
        return False, "the first repair did not pass; there is nothing to complete", []
    if not (repair.get("edits") or []):
        # Nothing was actually corrected, so the residue is not residue -- it is the
        # original problem, and a second call would only rediscover it.
        return False, "the first repair applied no edit", []
    if grounding.get("status") == PASS:
        return False, "the recheck passed; no completion needed", []
    blocking = grounding.get("blocking") or []
    if not blocking:
        return False, "no blocking finding survived the recheck", []
    if len(blocking) > COMPLETION_MAX_FINDINGS:
        return False, ("%d blocking findings survived, over the completion limit of %d -- "
                       "that is a broken article, not a residue"
                       % (len(blocking), COMPLETION_MAX_FINDINGS)), []
    # The grounder's own verdict decides what is answerable by removing words. A finding
    # it did not mark repairable needs evidence this pass does not have and will not get.
    eligible = [f for f in repairable_findings(blocking) if f.get("repairable") is True]
    if len(eligible) != len(blocking):
        return False, ("%d of %d surviving findings are not repairable by subtraction"
                       % (len(blocking) - len(eligible), len(blocking))), []
    return True, "%d repairable finding(s) survived one accepted repair" % len(eligible), eligible


def grounding_completion(provider, article_text: str, findings: list, ledger: dict,
                         packet: dict) -> dict:
    """STAGE 8c. Exactly one call, subtractive, validated by the SAME contract as 8b."""
    if not findings:
        return {"status": SKIPPED, "reason": "no completable finding", "model_calls": 0}
    obj, ident = _ask(provider, COMPLETION_GROUNDING_SYSTEM,
                      completion_prompt(article_text, findings, ledger),
                      6_000, GROUNDING, GROUNDING_HOLD)
    edits = obj.get("edits")
    if not isinstance(edits, list) or not edits:
        return {"status": SKIPPED, "reason": "the completion pass proposed no edit",
                "model_calls": 1, "provider": ident}
    # THE SAME VALIDATOR. Not a relaxed one, not a copy: the identical claim-local
    # function the first repair goes through (apply_local_grounding_repair(), not the
    # packet-wide apply_grounding_repair() Safety and the package-only repair keep
    # using), so a completion edit that adds a relation, or an entity from elsewhere in
    # the packet, is refused for the same reason and with the same message.
    text, prov, errs = apply_local_grounding_repair(article_text, edits, findings,
                                                    ledger, packet)
    if errs and not prov:
        # Every edit refused. The article is unchanged, so a further grounder call would
        # only rediscover the same findings. Report and let the existing HOLD stand.
        return {"status": SKIPPED, "reason": "every completion edit was refused",
                "rejected_edits": errs, "model_calls": 1, "provider": ident}
    if not text.strip():
        raise CompositionHold(GROUNDING, GROUNDING_HOLD,
                              ["the completion pass deleted the whole article"])
    return {"status": PASS, "article_text": text, "edits": prov,
            "findings_answered": [f.get("id") for f in findings],
            "rejected_edits": errs,
            "findings_left_unanswered": sorted(
                {str(f.get("id")) for f in findings}
                - {str(e.get("finding_id")) for e in prov}),
            "provider": ident, "model_calls": 1, "repairs": 1}


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


def advisory_block(advisories: list) -> str:
    """Low-confidence lexical findings, handed to the stage that can read a sense.

    They are NOT verdicts and are not presented as ones: each says which token matched,
    which rule matched it, and why the machine declined to decide. The reader is asked to
    settle them, which is exactly what a screen keyed on a bare word cannot do.
    """
    if not advisories:
        return ""
    L = ["", "", "ADVISORY FLAGS -- machine screens that matched a WORD and could not "
                 "decide its sense. Not findings. Settle each one as a reader:"]
    for a in advisories[:12]:
        L.append("  [%s] %r in: %s"
                 % (a["kind"], a["token"], (a.get("sentence") or "")[:180]))
    L.append("  If any of these sentences asserts something the article has not earned, "
             "say so under the dimension it damages. If it reads as ordinary English, "
             "ignore it.")
    return "\n".join(L) + "\n"


def reader_gate(provider, article_text: str, advisories: list | None = None) -> dict:
    """STAGE 10. Nine dimensions. Exact passages on a HOLD. No auto-rewrite."""
    obj, ident = _ask(provider, READER_SYSTEM,
                      "THE ARTICLE\n\n" + article_text
                      + advisory_block(advisories or [])
                      + "\n\n" + READER_SCHEMA,
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
            "advisories_shown": len(advisories or []),
            "provider": ident, "model_calls": 1}


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 10b -- ONE READER REPAIR, LOCAL EDITS ONLY (owner-directed, 2026-09-09;
# revised to a surgical local-edit contract 2026-09-09 after real production evidence)
# ══════════════════════════════════════════════════════════════════════════════
# WHY THIS EXISTS. A real Worth-PASS article held on eight of nine Reader dimensions at
# once, including CRIP_MINDS_FIT -- and the Reader's own note said the material EARNED
# the reading and the prose never delivered it: "the piece comes within one sentence of
# the material that would earn it... and walks past it without a word". That is a
# description of execution, not of a wrong story, and Worth had already settled that the
# story belongs here. Before this stage existed, that HOLD was terminal regardless.
#
# CRIP_MINDS_FIT IS NOT SPECIAL-CASED OUT OF REPAIR, AND NOT TRUSTED BLINDLY EITHER. The
# owner's own distinction -- is Reader rejecting the reading Worth approved, or only
# saying the article failed to make it legible -- is not decided by parsing the Reader's
# prose for which one it meant. It is decided by what happens next: repair is attempted
# on WHATEVER dimensions are held, in ONE bounded batch of LOCAL edits, using only
# material the article or the packet already licenses -- and then the SAME reader_gate()
# checks the result again, once. If CRIP_MINDS_FIT genuinely could not be earned because
# the reading was never really there, no set of local edits will manufacture it, and the
# recheck will say so -- which is the terminal HOLD, exactly as before. The distinction is
# proven by the outcome, not asserted in advance.
#
# WHY THIS IS NO LONGER A FREE WHOLE-ARTICLE REWRITE. The first version of this stage
# built on PROSE_FINISH's own contract -- free rewrite, checked only afterward by
# safety_audit(). Real production evidence (Gabriele Taylor, and the first live batch this
# revision replaces) showed the failure mode that contract permits: asked to fix eight
# dimensions at once, the rewrite reached past what it needed and introduced new NEGATION,
# CAUSAL, COMPARISON and TEMPORAL relations the writer never licensed -- caught by the
# mandatory safety recheck every time, so nothing false ever published, but every one of
# those attempts failed for the same avoidable reason: a whole-article rewrite has no
# reason to stay narrow. This version replaces the free rewrite with a bounded set of
# LOCAL EDITS, each an ({original, repaired} pair inside exactly one paragraph, mechanically
# verified by apply_reader_repair() the same way apply_grounding_repair() already verifies
# Safety and Grounding's own repairs -- a wider blast radius was never the fix a Reader
# hold needed, it was just the shape the first version happened to have.
#
# ONE CALL, ONE MANDATORY SAFETY RECHECK, ONE READER RECHECK. No second batch of edits
# regardless of outcome, and no rerun of Worth, Ledger or Architecture -- the reading and
# the facts are not this stage's to revisit.
READER_REPAIR_OPS = ("REPHRASE", "COMPRESS", "DELETE")

READER_REPAIR_SYSTEM = (
    "One or more readers have already approved this article's subject and its central "
    "reading. A hard reader has now read the finished prose and held it on specific "
    "dimensions, each with the exact passage that failed and the paragraph it lives in.\n"
    "\n"
    "YOU ARE NOT REWRITING THE ARTICLE. YOU ARE PERFORMING LOCAL LINE EDITS ON SPECIFIED "
    "SPANS ONLY. Each edit touches text inside ONE paragraph and nothing outside it. "
    "DO NOT TOUCH OTHER PARAGRAPHS, including ones that read badly for reasons no "
    "dimension named -- a paragraph not implicated by a held dimension is not yours to "
    "improve.\n"
    "\n"
    "DO NOT ADD FACTS OR RELATIONS. No number, date, name, place, quotation, cause, "
    "consequence, comparison, generalisation or negation beyond what the edited "
    "paragraph or the PERMITTED MATERIAL below already carries. If a dimension asks for "
    "more concrete material (BREATHING, RESEARCH_LOAD, CRIP_MINDS_FIT) it means: bring "
    "forward the specific, particular material already available and not yet given "
    "room in THAT paragraph -- not invented detail, however plausible, and never a new "
    "sentence asserting the reading in the abstract.\n"
    "\n"
    "PREFER DELETE, THEN COMPRESS, THEN REPHRASE -- in that order of preference. Deleting "
    "a redundant sentence or a machine-language phrase is always available and never "
    "adds anything. Compressing (shortening, simplifying syntax) is the next choice. "
    "Only rephrase when the words themselves, not just their number, are the problem, "
    "and even then say the same thing the paragraph already said.\n"
    "\n"
    "DO NOT CHANGE THE ARGUMENT OR THE READING anywhere in the article. Same subject, "
    "same central claim, same facts, same conclusion -- you are making a held paragraph "
    "deliver what the piece already earns, not reframing anything.\n"
    "\n"
    "ADDRESS ONLY THE HELD DIMENSIONS. One dimension may need edits in more than one "
    "paragraph -- submit one edit per paragraph, never one edit spanning two. A "
    "dimension not named was already passing.\n"
    "\n"
    "RETURN ONLY THE EDIT OPERATIONS, not the article. No preamble, no notes, no prose "
    "outside the JSON."
)

READER_REPAIR_SCHEMA = (
    "Reply with ONE JSON object:\n"
    '{"edits": [\n'
    '    {"dimension": "OPENING",     the HELD dimension this edit answers\n'
    '     "operation": "REPHRASE",    REPHRASE | COMPRESS | DELETE\n'
    '     "original": "the exact text, verbatim, from inside ONE paragraph",\n'
    '     "repaired": "the replacement text, or \\"\\" for DELETE"}\n'
    "]}\n"
    "Every edit's `original` must fall inside a SINGLE paragraph -- never spanning two. "
    "If a fix needs two paragraphs, submit two edits. One dimension may have several "
    "edits, each at a different place.\n"
    "No prose outside the JSON."
)


def _numbered_paragraphs(text: str) -> str:
    """Paragraph boundaries shown to the model for orientation only -- it must still
    quote the paragraph's own text VERBATIM in `original`, never a bracket tag."""
    return "\n\n".join("[paragraph %d]\n%s" % (i, p)
                       for i, p in enumerate(CE.paragraphs(text), 1))


def reader_repair_prompt(article_text: str, held: dict, packet: dict,
                        rejection: dict | None = None) -> str:
    L = ["THE ARTICLE, BY PARAGRAPH", _numbered_paragraphs(article_text), "",
        "WHAT THE READER HELD"]
    for dim, v in held.items():
        L += ["", "DIMENSION %s" % dim, "  note: %s" % str((v or {}).get("note", ""))[:500]]
        for p in (v or {}).get("passages") or []:
            L.append("  passage: %s" % str(p)[:300])
    L += ["", "PERMITTED MATERIAL -- the writer packet this article was licensed from. "
             "Nothing outside the article and this packet may be added:",
         ST.render(packet)[:6000]]
    if rejection:
        # CONCISE AND STRUCTURED, never a transcript -- the same shape
        # grounding_completion_prompt() already uses on its own retries.
        L += ["", "YOUR PREVIOUS PROPOSAL WAS REJECTED.",
             "REJECTED_BECAUSE: %s" % str(rejection.get("reason", ""))[:200]]
        if rejection.get("detail"):
            L.append("BLOCKING_PASSAGES: %s" % str(rejection["detail"])[:500])
        if rejection.get("reason") in (READER_REJECTED_GROUNDING,
                                       READER_REJECTED_SAFETY):
            # The one instruction that matters here. It is NOT "fix the facts": the
            # Reader has no factual authority and asking it to repair its own factual
            # damage is how a prose gate quietly becomes a second grounder.
            L.append("Your previous prose edit introduced factual assertions the "
                    "evidence does not carry. Try a SMALLER readability edit that uses "
                    "only the factual content already in the original sentence -- "
                    "delete or simplify, do not recharacterise what a study showed or "
                    "what a method proves.")
        else:
            L.append("That edit did not reduce what the reader is holding. Try a "
                    "different passage, or a smaller edit to the same one.")
    L += ["", READER_REPAIR_SCHEMA]
    return "\n".join(L)


def _beat_local_licensing(packet: dict, paragraph_index: int,
                          paragraph_count: int) -> tuple:
    """The numbers/entities a LOCAL edit to paragraph `paragraph_index` may draw on,
    from the ledger facts already attached to that paragraph's own architecture beat --
    never the whole packet.

    The Writer was given the architecture's beats in order and one paragraph per beat
    is the contract it wrote to (writer_packet()/build_packet() render `packet["beats"]`
    in that same order, each already carrying only the facts its OWN beat licenses --
    `facts_allowed` on the architecture beat, unchanged). Paragraph index and beat index
    are therefore the same position in the same sequence -- an EXISTING correspondence
    this reuses, not a new one this invents.

    FAILS CLOSED, on purpose, whenever that correspondence cannot be trusted: a
    paragraph count that does not match the beat count means something upstream (a
    Continuity merge/split, an earlier local edit) has already broken the 1:1 mapping,
    and guessing which beat a paragraph now belongs to is exactly the packet-wide
    permission this function exists to replace. Returns EMPTY sets in that case -- a
    local edit can still delete or narrow using only what its own span already carries,
    it just cannot pull in anything new.
    """
    beats = packet.get("beats") or []
    if paragraph_count != len(beats) or not (0 <= paragraph_index < len(beats)):
        return set(), set()
    facts = beats[paragraph_index].get("facts") or []
    text = " ".join("%s %s" % (f.get("proposition", ""), f.get("support_span", ""))
                    for f in facts if isinstance(f, dict))
    return _numbers_of(text), ST._entities(text, skip_sentence_initial=False)


def apply_reader_repair(article_text: str, edits: list, held: dict,
                        packet: dict) -> tuple:
    """Apply LOCAL, mechanically-verified edits. Returns (text, provenance, errs).

    The same discipline apply_grounding_repair() already enforces for Safety and
    Grounding's own repairs, adapted to a Reader finding's shape: every edit must name a
    HELD dimension, its `original` must be an exact quote found inside a SINGLE
    paragraph of the article -- never spanning more, which is what keeps this a local
    edit rather than a rewrite wearing an edit's clothes -- and its `repaired` wording
    may add no relation the edited paragraph did not already carry, and no number or
    entity that paragraph's OWN architecture beat did not already license (see
    _beat_local_licensing) -- never merely because it appears somewhere ELSE in the
    packet. An edit that widens the claim, reaches past its own paragraph, or pulls in
    an entity licensed only for a DIFFERENT paragraph, is refused, not applied.

    A real production replay is why this is claim-local rather than packet-wide: a
    repair rewriting one paragraph introduced "German" and "German-speaking", both
    genuinely present elsewhere in the packet (a different beat's own material), and
    packet-wide permission let them through into a paragraph whose own facts never
    licensed them. The mandatory Safety recheck caught it there; this stops it earlier,
    at the edit that was never entitled to it.
    """
    paras = CE.paragraphs(article_text)
    n_paras = len(paras)
    out, prov, errs = article_text, [], []
    for i, e in enumerate(edits or [], 1):
        if not isinstance(e, dict):
            errs.append("edit %d is not an object" % i)
            continue
        dim = str(e.get("dimension") or "")
        orig = (e.get("original") or "").strip()
        rep = (e.get("repaired") or "").strip()
        op = e.get("operation")
        if dim not in held:
            errs.append("edit %d cites dimension %r, which was not held" % (i, dim))
            continue
        if op not in READER_REPAIR_OPS:
            errs.append("edit %d has operation %r, not one of %s"
                        % (i, op, ", ".join(READER_REPAIR_OPS)))
            continue
        if not orig or normalize_span(orig) not in normalize_span(out):
            errs.append("edit %d: the original is not in the article: %r"
                        % (i, orig[:80]))
            continue
        # Located against the ORIGINAL, unedited paragraph list: an edit's home
        # paragraph and beat are fixed at the moment the edit is proposed, not
        # recomputed against a text an earlier edit in this same batch may have
        # already changed the shape of.
        host_idx = next((j for j, p in enumerate(paras)
                        if normalize_span(orig) in normalize_span(p)), None)
        if host_idx is None:
            errs.append("edit %d spans more than one paragraph -- not a local edit: %r"
                        % (i, orig[:80]))
            continue
        if orig not in out:
            errs.append("edit %d: quoted text does not match the article exactly "
                        "(whitespace or punctuation drift) -- refused rather than "
                        "guessed at" % i)
            continue
        lic_nums, lic_ents = _beat_local_licensing(packet, host_idx, n_paras)
        new_nums = sorted(_numbers_of(rep) - _numbers_of(orig) - lic_nums)
        new_ents = sorted(ST._entities(rep) - ST._entities(orig) - lic_ents)
        before_rel, after_rel = CE.relations(orig), CE.relations(rep)
        new_rel = {k: after_rel[k] - before_rel.get(k, 0)
                  for k in after_rel if after_rel[k] > before_rel.get(k, 0)}
        if new_nums or new_ents or new_rel:
            errs.append("edit %d ADDS rather than edits -- numbers=%s entities=%s "
                        "relations=%s (licensed only by this paragraph's own beat, "
                        "not the whole packet)"
                        % (i, new_nums, new_ents, new_rel))
            continue
        out = out.replace(orig, rep, 1)
        prov.append({"dimension": dim, "operation": op, "original": orig,
                     "repaired": rep})
    out = re.sub(r"[ \t]{2,}", " ", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip(), prov, errs


# ══════════════════════════════════════════════════════════════════════════════
# TRANSACTIONAL, PROGRESS-BOUNDED READER COMPLETION (owner-directed, 2026-09-09)
# ══════════════════════════════════════════════════════════════════════════════
# WHY THIS EXISTS, from the run that produced it. Retained Poetry continuation
# …-2026-09-09T211900: Safety PASS, Grounding PASS, Fact Check PASS, and the Reader then
# held EIGHT of its nine dimensions across fourteen implicated passages. One editorial
# repair ran, made five local edits -- four of them good -- and the fifth rewrote the
# closing sentence's characterisation:
#
#   before  "rests on a method that names a bodily reaction as its measure of success
#            and bodily perception as the way to take part"     <- Grounder accepted this
#   after   "rests on a method that TAKES CHILLS AND GOOSEBUMPS AS PROOF A POEM HAS
#            WORKED, and hearing, smelling, seeing and feeling as the way to take part"
#
# "proof a poem has worked" is a claim the evidence does not make. make_package() then
# regenerated the package from the damaged article and propagated that exact
# characterisation into the title, dek, excerpt and meta description -- so ONE bad local
# edit became six blocking Grounding findings, five of them on package surfaces. The run
# terminal-HELD, and the factually clean article that had passed three gates was gone.
#
# THE SEMANTIC ERROR IN THE OLD CODE was not the budget. It was ownership: a Reader
# repair was treated as an ACCEPTED article that Grounding then judged, so a Reader
# failure was recorded as a Grounding failure and the only way forward would have been to
# have Grounding repair the Reader's invention. That makes "Reader creates factual damage
# -> Grounding cleans it up" a normal architecture. It is not one.
#
# A READER REPAIR IS A PROPOSAL. It is not accepted until it survives factual validation.
# Safety and Grounding here are ACCEPTANCE TESTS FOR THE PROPOSAL, never repair triggers:
# if either fails, the PROPOSAL is rejected, the previously accepted article and package
# stand byte-for-byte, and the Reader may try a different, smaller edit with a concise
# reason why the last one was refused. Nothing asks the Reader to fix facts.
#
# PROGRESS IS PER PASSAGE, NOT PER DIMENSION. READABILITY holding on three passages and
# then on one is real progress even though READABILITY still says HOLD -- counting
# dimensions would call that "no progress" and stop on the iteration that worked. See
# reader_blocker_signature.
READER_COMPLETION_MAX_ITERATIONS = 5

READER_REJECTED_SAFETY = "SAFETY_INTRODUCED_BLOCKERS"
READER_REJECTED_GROUNDING = "GROUNDING_INTRODUCED_UNSUPPORTED_CLAIMS"
READER_REJECTED_NO_PROGRESS = "NO_READER_PROGRESS"


def reader_blocker_signature(rg: dict) -> list:
    """The CANONICAL Reader blocker multiset: one entry per (dimension, implicated
    passage), or one entry for the dimension itself when it holds without naming a
    passage.

    Counting HOLD DIMENSIONS would be the wrong measure -- the production run held
    READABILITY on two passages and ENGINE_LANGUAGE_LEAK on three, and fixing one passage
    leaves the dimension holding. That is progress and must be allowed to continue.
    Passages are normalised (the same normalize_span every other locator here uses) so a
    whitespace difference in the Reader's own quoting is not mistaken for a new blocker.
    Sorted, so it compares as a multiset: strictly fewer entries is progress, the same
    number of different entries is not.
    """
    out = []
    for dim, v in (rg.get("held") or {}).items():
        passages = [p for p in ((v or {}).get("passages") or []) if str(p).strip()]
        if not passages:
            out.append((str(dim), ""))
            continue
        for p in passages:
            out.append((str(dim), normalize_span(str(p))))
    return sorted(out)


def reader_completion_loop(provider, article_text: str, package: dict | None, rg: dict,
                           packet: dict, ledger: dict, draft_text: str, pack: dict,
                           arch: dict | None, source_text: str, source_sha: str,
                           audit_fn, package_fn, gate_fn,
                           package_completion_fn=None,
                           max_iterations: int = READER_COMPLETION_MAX_ITERATIONS
                           ) -> dict:
    """TRANSACTIONAL, PROGRESS-BOUNDED Reader completion. Replaces the one-repair budget
    with a loop that keeps proposing local editorial repairs only as long as each one
    provably leaves the article BETTER FOR THE READER and NO WORSE FACTUALLY.

    `rg` is the Reader gate result the caller already paid for -- never re-run here for
    the initial state. `audit_fn`, `package_fn` and `gate_fn` are the caller's own
    safety_audit / make_package / reader_gate closures, reused exactly, so a candidate is
    judged by the SAME Safety, the SAME package generation and the SAME Reader this run
    enforces everywhere else. `package_completion_fn(sa, article, package)` is the
    already-merged progress-bounded package Safety completion, applied to a candidate's
    TEMPORARY package only.

    Returns a dict carrying `article_text` and `package` (the ACCEPTED ones -- the inputs
    unchanged if nothing was ever accepted), the final Reader gate result at `gate`, and
    the audit the caller persists: reader_completion_iterations, reader_repair_proposals,
    reader_repairs_accepted, reader_repairs_rejected, reader_completion_history,
    reader_initial_blocker_count, reader_final_blocker_count, plus `model_calls` and the
    accepted candidate's own `final_safety` / `final_grounding`.

    EVERY REJECTION IS TOTAL. A candidate that fails Safety or Grounding takes its
    regenerated package down with it: no package built from a rejected article can become
    accepted state, which is the whole reason the package is regenerated inside the loop
    rather than by the caller afterwards.
    """
    accepted_text = article_text
    accepted_pkg = package
    accepted_gate = rg
    accepted_safety = None
    accepted_grounding = None
    iterations = proposals = accepted = rejected = 0
    # SPLIT BY STAGE, not lumped into READER. A candidate's Safety re-audit and Grounding
    # recheck are Safety's and Grounding's own calls wherever they are made -- the same
    # attribution every other repair path in this module already uses. Only the repair
    # proposals and the Reader rechecks belong to READER.
    reader_calls = safety_calls = grounding_calls = 0
    package_repair_used = False
    tried = set()
    rejection = None
    history: list = []
    before_sig = reader_blocker_signature(rg)
    initial_count = len(before_sig)

    while accepted_gate["status"] != PASS and iterations < max_iterations:
        held = accepted_gate.get("held") or {}
        if not held:
            break
        iterations += 1
        prop = reader_repair(provider, accepted_text, held, packet, rejection)
        proposals += 1
        reader_calls += prop.get("model_calls", 0)

        if prop["status"] != PASS:
            rejected += 1
            history.append({"iteration": iterations, "outcome": "no_usable_proposal",
                            "reason": prop.get("reason", "the proposal was refused"),
                            "blockers_before": len(before_sig)})
            break

        sig = _reader_edit_signature(prop.get("edits"))
        if sig in tried:
            rejected += 1
            history.append({"iteration": iterations, "outcome": "repeated_proposal",
                            "blockers_before": len(before_sig)})
            break
        tried.add(sig)

        candidate_text = prop["article_text"]
        entry = {"iteration": iterations, "blockers_before": len(before_sig),
                 "edits": [{k: e.get(k) for k in ("dimension", "paragraph", "original",
                                                  "repaired")}
                           for e in (prop.get("edits") or [])]}

        # ONE package regeneration per candidate, on the TEMPORARY article. It is
        # discarded with the candidate if anything below refuses it.
        candidate_pkg = package_fn(candidate_text)
        candidate_sa = audit_fn(candidate_text, candidate_pkg)
        safety_calls += candidate_sa.get("model_calls", 0)
        candidate_pkg_repaired = False
        if candidate_sa["status"] != PASS and package_completion_fn is not None:
            fixed_pkg, extra_calls, candidate_sa = package_completion_fn(
                candidate_sa, candidate_text, candidate_pkg)
            safety_calls += extra_calls
            if fixed_pkg is not None:
                candidate_pkg = fixed_pkg
                candidate_pkg_repaired = True
        entry["safety"] = candidate_sa["status"]
        entry["package_repaired"] = candidate_pkg_repaired
        if candidate_sa["status"] != PASS:
            rejected += 1
            rejection = {"reason": READER_REJECTED_SAFETY,
                         "detail": (candidate_sa.get("blocking") or [])[:4]}
            entry.update(outcome="safety_rejected", reason=rejection["detail"])
            history.append(entry)
            continue

        candidate_g = ground_candidate(provider, bundle_text(candidate_text,
                                                             candidate_pkg),
                                       source_text, source_sha, pack, arch, packet)
        grounding_calls += candidate_g.get("model_calls", 0)
        entry["grounding"] = candidate_g["status"]
        if candidate_g["status"] != PASS:
            # THE POINT OF THE WHOLE MECHANISM. Not "now repair these findings" -- the
            # Reader's proposal is simply refused, and the factually clean article that
            # reached this stage is still the accepted one.
            rejected += 1
            rejection = {"reason": READER_REJECTED_GROUNDING,
                         "detail": [str(f.get("quote") or f.get("claim") or "")[:120]
                                    for f in (candidate_g.get("blocking") or [])[:4]]}
            entry.update(outcome="grounding_rejected", reason=rejection["detail"])
            history.append(entry)
            continue

        candidate_gate = gate_fn(candidate_text, candidate_sa.get("advisories"))
        reader_calls += candidate_gate.get("model_calls", 0)
        after_sig = reader_blocker_signature(candidate_gate)
        entry["blockers_after"] = len(after_sig)
        if len(after_sig) >= len(before_sig):
            rejected += 1
            rejection = {"reason": READER_REJECTED_NO_PROGRESS,
                         "detail": "reader blocker count did not shrink (%d -> %d)"
                                   % (len(before_sig), len(after_sig))}
            entry.update(outcome="no_progress", reason=rejection["detail"])
            history.append(entry)
            continue

        accepted += 1
        accepted_text = candidate_text
        accepted_pkg = candidate_pkg
        accepted_gate = candidate_gate
        accepted_safety = candidate_sa
        accepted_grounding = candidate_g
        package_repair_used = candidate_pkg_repaired
        before_sig = after_sig
        rejection = None
        entry.update(outcome="accepted")
        history.append(entry)

    return {"status": accepted_gate["status"], "article_text": accepted_text,
            "package": accepted_pkg, "gate": accepted_gate,
            "final_safety": accepted_safety, "final_grounding": accepted_grounding,
            "model_calls": reader_calls + safety_calls + grounding_calls,
            "reader_model_calls": reader_calls,
            "safety_model_calls": safety_calls,
            "grounding_model_calls": grounding_calls,
            "package_repair_used": package_repair_used,
            "reader_completion_iterations": iterations,
            "reader_repair_proposals": proposals,
            "reader_repairs_accepted": accepted,
            "reader_repairs_rejected": rejected,
            "reader_completion_history": history,
            "reader_initial_blocker_count": initial_count,
            "reader_final_blocker_count": len(before_sig)}


def _reader_edit_signature(edits: list) -> tuple:
    """A hashable fingerprint of a Reader proposal, to catch the model re-proposing an
    edit that was already refused. Same idea as _edit_signature, keyed on the fields a
    Reader edit actually has."""
    return tuple(sorted((str(e.get("dimension")), str(e.get("paragraph")),
                         str(e.get("original")), str(e.get("repaired")))
                        for e in (edits or [])))


def reader_repair(provider, article_text: str, held: dict, packet: dict,
                  rejection: dict | None = None) -> dict:
    """STAGE 10b. ONE proposal, local edits only -- never a full-article rewrite.
    Mechanically verified by apply_reader_repair(), the same discipline
    apply_grounding_repair() already applies to Safety and Grounding's own repairs.
    Verification here does not replace the caller's mandatory re-run of the existing
    safety_audit() and ground_candidate() (both unchanged); it is the first guard, not
    the only one. `rejection` carries the previous proposal's refusal reason on a
    retry -- concise and structured, never a transcript."""
    if not held:
        return {"status": SKIPPED, "reason": "no held dimension", "model_calls": 0}
    obj, ident = _ask(provider, READER_REPAIR_SYSTEM,
                      reader_repair_prompt(article_text, held, packet, rejection),
                      4_000, READER, READER_HOLD)
    edits = obj.get("edits")
    if not isinstance(edits, list) or not edits:
        return {"status": HOLD, "reason": "the editorial repair returned no edits",
                "model_calls": 1, "provider": ident}
    text, prov, errs = apply_reader_repair(article_text, edits, held, packet)
    if not prov or not text.strip():
        return {"status": HOLD,
                "reason": "the editorial repair did not stay within its permissions"
                         if errs else "the editorial repair deleted the whole article",
                "failures": errs, "model_calls": 1, "provider": ident}
    return {"status": PASS, "article_text": text, "edits": prov,
            "rejected_edits": errs,
            "dimensions_addressed": sorted({e["dimension"] for e in prov}),
            "provider": ident, "model_calls": 1, "repairs": 1}


# ══════════════════════════════════════════════════════════════════════════════
# THE ENTRYPOINT
# ══════════════════════════════════════════════════════════════════════════════
PROSE_FINISH_SYSTEM = (
    "You are the last writer to touch a finished article before it is checked. Your job is "
    "to make it read as though one person wrote it from beginning to end. It is already "
    "correct; you are not here to make it more correct, more interesting or more "
    "important.\n"
    "\n"
    "ADD NOTHING. No fact, number, date, name, place, quotation, cause, consequence or "
    "comparison that is not already in the text in front of you. No scene, no sensory "
    "detail, no motive, no dialogue, no invented particular. If you find yourself needing "
    "a fact to make a sentence land, the sentence does not land and you cut it instead. "
    "Everything you write is checked against a frozen evidence ledger afterwards, and an "
    "addition fails the article rather than improving it.\n"
    "\n"
    "DO NOT CHANGE THE ARGUMENT. Same thesis, same order of ideas, same conclusion, same "
    "emphasis. You are working on the surface.\n"
    "\n"
    "AND DO NOT TIDY AWAY A QUALIFIER. The commonest way a polish breaks an article is by "
    "removing the condition that made a claim true: a scope, a sample or team size, a time "
    "window, a place, a may against a does, an attribution, a technical distinction, a "
    "dependency of the form \"as X increased from A to B\". A sentence reads better without "
    "it and is then a bigger claim than the evidence. Two articles were refused this week "
    "for exactly that -- \"flush-pointed\" tightened into \"laid flush\", and \"from 57% to "
    "88% as team size increased from 2 to 16\" tightened into \"from 57% to 88%\". If a "
    "qualifier is making a sentence clumsy, rebuild the sentence around it; never drop it.\n"
    "\n"
    "WHAT TO FIX:\n"
    "  - sentence rhythm: vary the lengths, let a short one land after a long one\n"
    "  - paragraph flow: one job per paragraph, and a reason to move to the next\n"
    "  - concrete before abstract: give the reader the thing before the idea about it\n"
    "  - transitions that do not announce themselves. Cut 'this reveals', 'that is the "
    "point', 'here is where', 'what this means is'\n"
    "  - ordinary precise words. Anglo-Saxon over Latinate, short over long\n"
    "  - breathing room: let a fact sit without a moral attached in the same breath\n"
    "  - research-report cadence: cut 'the source says', 'the paper reports', 'the "
    "evidence shows', 'the record states', 'according to'. Say the thing, or name who "
    "said it if the naming matters\n"
    "  - explanatory repetition: if a point is made twice, keep the better one\n"
    "  - manufactured clinchers: an epigram at the end of a paragraph that summarises "
    "what the paragraph just said is a tic. Cut it and let the paragraph end on its "
    "material\n"
    "\n"
    "WHAT NOT TO DO. No literary decoration, no purple prose, no rhetorical questions, no "
    "second-person address, no imitation of a particular writer, no formulaic ending. A "
    "calm, confident magazine surface, not a performance. If a passage is already good, "
    "leave it exactly as it is -- an unnecessary edit is a cost, not a contribution.\n"
    "\n"
    "Return ONLY the finished article body. No preamble, no notes, no explanation of what "
    "you changed, no frontmatter, no headers."
)


def prose_finish(provider, article_text: str, arch: dict) -> dict:
    """STAGE 6b. One pass for surface quality, BEFORE anything factual is checked.

    WHY IT SITS HERE. Safety, Grounding and Fact Check must evaluate the exact bytes that
    will publish. A polish applied after them would invalidate every stamp they issued, and
    a polish applied after Fact Check would publish prose nothing had checked. So it runs
    last among the writing stages and first among nothing -- the text it returns is the
    text the whole factual stack then reads.

    FAIL-SAFE, exactly like CONTINUITY above it. The article arriving here is already
    publishable; this stage is an optional improvement over it and is not permitted to
    cost the run. Any failure -- provider error, empty return, a reply that looks like
    commentary rather than an article, a length that suggests the model rewrote rather
    than polished -- discards the edit whole and carries the incoming text forward. There
    is no retry and no second call: one pass, taken or dropped.

    The additions it must not make are caught downstream anyway, by the same safety stack
    that audits the Writer and Continuity. This stage's own guard is about not wasting the
    run on an obviously bad edit, not about factual authority.
    """
    incoming = article_text
    try:
        intent = "\n".join([
            "THE STORY THIS ARTICLE IS TELLING (do not change it)",
            "  " + str(arch.get("story_spine") or "")[:400],
            "  ending: " + str(arch.get("ending_move") or "")[:200], "",
            "THE ARTICLE", incoming])
        comp = provider.complete(system=PROSE_FINISH_SYSTEM, user=intent, max_tokens=6_000)
        out = (getattr(comp, "text", "") or "").strip()
        ident = comp.identity() if hasattr(comp, "identity") else {}
    except Exception as e:                                        # noqa: BLE001
        return {"status": SKIPPED, "article_text": incoming, "applied": False,
                "reason": "provider failure: %s: %s" % (type(e).__name__, str(e)[:160]),
                "model_calls": 1, "repairs": 0}

    # PRESERVE THE TITLE, never strip it. An article legitimately opens with its H1, so a
    # blanket "drop a leading # line" removed the real first line -- caught by the suite,
    # which saw an empty article come back. If the polish dropped the heading, put the
    # incoming one back; if it kept or rewrote one, leave it alone.
    head = incoming.split("\n", 1)[0]
    if head.startswith("# ") and out and not out.lstrip().startswith("#"):
        out = head + "\n\n" + out.lstrip()
    inw, outw = len(incoming.split()), len(out.split())
    reason = ""
    if not out:
        reason = "returned nothing"
    elif outw < inw * 0.75:
        reason = "returned %d words from %d -- that is a cut, not a polish" % (outw, inw)
    elif outw > inw * 1.25:
        reason = "returned %d words from %d -- that is an expansion, not a polish" % (outw, inw)
    if reason:
        return {"status": SKIPPED, "article_text": incoming, "applied": False,
                "reason": reason, "words_in": inw, "words_out": outw,
                "provider": ident, "model_calls": 1, "repairs": 0}
    return {"status": PASS, "article_text": out, "applied": True, "reason": "",
            "words_in": inw, "words_out": outw, "provider": ident,
            "model_calls": 1, "repairs": 0}


# ── EDITORIAL PACKAGE ────────────────────────────────────────────────────────
PACKAGE_SYSTEM = (
    "You are the editor who decides how a finished article is presented. The article "
    "below is done: checked, grounded, and going out as it stands. You are not editing "
    "it. You are writing the five short things a reader meets BEFORE it.\n"
    "\n"
    "THE READER YOU ARE WRITING FOR has never heard of this person, place, paper, "
    "building or device, and has no reason to care yet. They are looking at a card on a "
    "homepage among other cards. Your job is to give them a reason to spend five minutes, "
    "and the reason has to be true.\n"
    "\n"
    "ADD NOTHING. Every name, number, date, place and claim you use must already be in "
    "the article. You may not quote anything the article does not quote. This is checked "
    "mechanically afterwards and a package that adds material is thrown away.\n"
    "\n"
    "QUALIFIER FIDELITY, and this is where packaging fails most often. A card is short, so "
    "the condition that makes a claim true is the first thing to go -- and the claim is "
    "then bigger than the evidence. Keep, exactly: the ATTRIBUTION (whose words are these "
    "-- the article's author, or the person being written about?), the SCOPE, any COUNT, "
    "any TIME SPAN, the MODALITY (may, can, does, will), and QUOTED LANGUAGE as quoted.\n"
    "  Three real refusals of this article's own cards, all in one afternoon: a project "
    "date range of 2014-2025 sold as a house 'built over eleven years'; three lines in an "
    "awards list counted as 'three awards' when they named five honours; and a phrase from "
    "the article's own prose attributed to 'its architects', who never said it. Every one "
    "read better than the truthful version. That is the trap, and it is the same one the "
    "Writer is warned about.\n"
    "  If a qualifier will not fit the line, write a different line.\n"
    "\n"
    "AND THE HARDER RULE, WHICH NO WORD-LEVEL CHECK CATCHES. You may use only the "
    "RELATIONS the article already asserts, not new ones between words it happens to "
    "contain. Specifically, you may not:\n"
    "  - turn two facts that sit next to each other into cause and effect\n"
    "  - turn adjacency into contradiction, or a difference into a scandal\n"
    "  - widen scope: a record about one station is not a claim about buildings, a "
    "measure of one year is not a trend, one person is not a group\n"
    "  - harden a hedge. If the article says a thing may be so, the card may not say it "
    "is so, and 'no record of X' is not 'there is no X'\n"
    "  - manufacture relevance to disability, access or the body that the article does "
    "not itself establish\n"
    "The article you are given has been through a factual stack; your five lines go "
    "through the same one, and they hold the article back when they fail.\n"
    "\n"
    "TITLE. Curiosity, tension or recognition, from a reader who does not know the "
    "subject. Not a label for the topic, not a summary, not a question you do not answer, "
    "and not clickbait. It may name the concrete thing the piece stands on. Under twelve "
    "words, no trailing full stop.\n"
    "\n"
    "DEK. One or two sentences answering WHY SHOULD I READ THIS. Name the concrete "
    "tension, surprise or contradiction. Do not exhaust the story: the dek sets up what "
    "the article then does. Fifteen to forty words.\n"
    "\n"
    "HOMEPAGE_EXCERPT. The hardest one. Two or three sentences on a card, and by the end "
    "of the first the reader should know what is strange here, what changes when you look "
    "closer, or what is unexpectedly at stake. It is NOT the article's first paragraph "
    "unless that paragraph happens to do this job, and it usually does not -- an opening "
    "written to be read second is rarely written to be read first. Twenty-five to sixty "
    "words.\n"
    "\n"
    "META_DESCRIPTION. Plain, factual, for a search result. Under 160 characters.\n"
    "\n"
    "SOCIAL_HOOK. One or two sentences for a post, no hashtags, no emoji, no 'thread', no "
    "'here is why'. Under 240 characters.\n"
    "\n"
    "REGISTER. Calm and specific. No 'in a world where', no 'this raises questions', no "
    "'a fascinating look at', no 'we are all'. Say the concrete thing."
)

PACKAGE_SCHEMA = (
    "Reply with ONE JSON object:\n"
    '{"package": {"title": "...", "dek": "...", "homepage_excerpt": "...",\n'
    '             "meta_description": "...", "social_hook": "..."}}\n'
    "No prose outside the JSON."
)

PACKAGE_FIELDS = ("title", "dek", "homepage_excerpt", "meta_description", "social_hook")

# Bounds are a shape check, not a taste check: a title that runs to thirty words or an
# excerpt of four is not a judgement call, it is a stage that misunderstood its job.
PACKAGE_BOUNDS = {
    "title": (2, 14, 110),
    "dek": (10, 45, 320),
    "homepage_excerpt": (20, 70, 460),
    "meta_description": (10, 34, 160),
    "social_hook": (8, 45, 240),
}

_QUOTED = re.compile(r"[\"“]([^\"”]{12,})[\"”]")

_PACKAGE_BANNED = (
    "in a world where", "raises questions", "fascinating look", "we are all",
    "a must-read", "here's why", "here is why", "dives into", "unpacks", "explores what",
)


def package_additions(field_text: str, article_text: str, title_case: bool = False) -> list:
    """What does this line assert that the article does not already carry?

    Three channels, the same ones the safety stack trusts, applied to five short lines:
    a NUMBER the article does not contain, a NAME the article does not contain, and a
    QUOTATION that is not a span of the article.

    THE NAME CHANNEL IS OFF FOR THE TITLE, deliberately. A title is title-cased, so
    capitalisation stops carrying information -- "The Upper Room With No Lock" offers four
    capitals and not one of them is a name. Applying the screen there would refuse every
    ordinary title and teach the stage to write worse ones. In the prose fields capitals
    mean what they usually mean, so a mid-sentence capital that the article does not
    contain is what it looks like.

    AND THIS IS A SCREEN, NOT VALIDATION. It sees words. The additions that matter most in
    a package are made out of words the article already contains -- a cause invented
    between two facts, a station's record widened into a claim about a building -- and it
    cannot see any of them. Those are the Grounder's and the Fact Check's, on the bundle.
    """
    low = (article_text or "").lower()
    out = []
    if not title_case:
        for tok in sorted(ST._entities(field_text or "", skip_sentence_initial=True)):
            t = re.sub(r"['\u2019]s$", "", tok).lower().strip(".,")
            if len(t) > 2 and t not in low and t not in ST._FUNCTION_WORDS \
                    and ST._stem(t) not in _COMMON_ENGLISH:
                out.append("name not in the article: %r" % tok)
    for n in sorted(ST._numbers(field_text or "") - ST._numbers(article_text or "")):
        out.append("number not in the article: %r" % n)
    art = normalize_span(article_text or "")
    for q in _QUOTED.findall(field_text or ""):
        if normalize_span(q) not in art:
            out.append("quotation not in the article: %r" % q[:60])
    return out


def check_package(pkg: dict, article_text: str) -> list:
    """Deterministic. No model reviews this; the failures below are the whole contract."""
    errs = []
    if not isinstance(pkg, dict):
        return ["package is not an object"]
    for f in PACKAGE_FIELDS:
        v = pkg.get(f)
        if not isinstance(v, str) or not v.strip():
            errs.append("%s is missing or empty" % f)
            continue
        v = v.strip()
        lo, hi, chars = PACKAGE_BOUNDS[f]
        n = len(v.split())
        if n < lo:
            errs.append("%s is %d words, under the %d-word minimum" % (f, n, lo))
        if n > hi:
            errs.append("%s is %d words, over the %d-word maximum" % (f, n, hi))
        if len(v) > chars:
            errs.append("%s is %d characters, over the %d-character maximum"
                        % (f, len(v), chars))
        errs += ["%s: %s" % (f, a)
                 for a in package_additions(v, article_text, title_case=(f == "title"))]
        lowv = v.lower()
        for b in _PACKAGE_BANNED:
            if b in lowv:
                errs.append("%s uses %r, which is packaging language rather than the "
                            "story" % (f, b))
        if "\n" in v:
            errs.append("%s spans more than one line" % f)
    t = str(pkg.get("title") or "").strip()
    if t.endswith("."):
        errs.append("title ends in a full stop")
    return errs


def editorial_package(provider, article_text: str, arch: dict, worth: dict,
                      refusals: list | None = None) -> dict:
    """The five lines a reader meets before the article, written from the exact bytes that
    publish and then checked as part of the same publication bundle.

    WHERE IT SITS. After Prose Finish, before Safety. The package is public prose, so the
    factual stack has to see it -- Safety screens its surface, and the Grounder and the
    Fact Check read it inside the bundle with the article. It is written last among the
    writing stages for the same reason the polish is: the text it sells has to be the text
    that ships.

    WHAT KEEPS IT HONEST is two things, and only the second one is real validation.
    `check_package` is a cheap deterministic screen that refuses a name, number or
    quotation the article does not carry -- it costs nothing and catches the obvious. It
    is NOT factual validation: the same words the article grants can still be arranged
    into a proposition it never made, which is the failure mode a title is most prone to.
    That one is caught downstream, by the gates, on the bundle.

    TECHNICAL FAILURE IS NOT AN EDITORIAL REJECTION. A provider or parser failure returns
    TECHNICAL_FAILURE and leaves the article intact and unpublished, for an owner to look
    at. A package that was written and refused returns REFUSED. Neither is a HOLD: the
    article did nothing wrong, and saying it did would put a technical fault into the
    editorial record.
    """
    ctx = "\n".join([
        "THE STORY THIS ARTICLE TELLS",
        "  " + str((arch or {}).get("story_spine") or "")[:400],
        "WHAT THIS PUBLICATION SEES IN IT",
        "  " + str((worth or {}).get("lens_claim") or "")[:300],
        "  it stands on: " + str((worth or {}).get("lens_carrier") or "")[:200],
        "",
        "THE FINISHED ARTICLE",
        article_text or "",
        "",
        PACKAGE_SCHEMA])
    if refusals:
        # A regeneration after a GATE refused the previous package. It is told exactly what
        # was found and on which line, and nothing else changes.
        ctx = "\n".join([
            "A PREVIOUS PACKAGE FOR THIS ARTICLE WAS REFUSED BY THE FACTUAL GATES. Write a "
            "new one that does not make these claims. The article is unchanged.",
            *["  - " + str(r)[:300] for r in refusals[:8]], "", ctx])

    def _fail(status, reason, calls, repairs=0, failures=None):
        return {"status": SKIPPED, "package": None, "applied": False,
                "package_status": status, "reason": reason[:300],
                "failures": (failures or [])[:10], "model_calls": calls,
                "repairs": repairs}

    calls = 0
    try:
        obj, ident = _ask(provider, PACKAGE_SYSTEM, ctx, 1_500, PACKAGE, PACKAGE_SKIPPED)
        calls = 1
    except CompositionHold as e:
        return _fail(PACKAGE_TECHNICAL_FAILURE,
                     "the package could not be produced: %s" % "; ".join(e.reasons), 1)
    pkg = obj.get("package") or {}
    errs = check_package(pkg, article_text)
    if not errs:
        return {"status": PASS, "package": _clean_package(pkg), "applied": True,
                "package_status": PACKAGE_OK, "repaired": False, "provider": ident,
                "model_calls": calls, "repairs": 0}
    # ONE repair, on the exact failures and the same article. No second one.
    try:
        fix = "\n".join(["Your package was refused. Fix exactly these and change nothing "
                         "else. Use only what the article already says.",
                         *["  - " + e for e in errs[:10]], "", ctx])
        obj2, ident = _ask(provider, PACKAGE_SYSTEM, fix, 1_500, PACKAGE, PACKAGE_SKIPPED)
        calls = 2
    except CompositionHold as e:
        return _fail(PACKAGE_TECHNICAL_FAILURE,
                     "the package repair could not be produced: %s" % "; ".join(e.reasons),
                     2, 1, errs)
    pkg2 = obj2.get("package") or {}
    errs2 = check_package(pkg2, article_text)
    if not errs2:
        return {"status": PASS, "package": _clean_package(pkg2), "applied": True,
                "package_status": PACKAGE_OK, "repaired": True,
                "first_attempt_failures": errs[:10], "provider": ident,
                "model_calls": calls, "repairs": 1}
    return _fail(PACKAGE_REFUSED,
                 "package refused after one repair: %s" % "; ".join(errs2), calls, 1, errs2)


def _clean_package(pkg: dict) -> dict:
    return {f: str(pkg.get(f) or "").strip() for f in PACKAGE_FIELDS}


def run_story_architecture_composition(
        provider, *, pack: dict, source_text: str, source_sha: str,
        subject: str = "", fact_check: bool = True, reader: bool = True,
        package: bool = True, stop_after: str = "",
        fact_check_fn=None, out_dir=None, frozen: dict | None = None,
        compose_mode: str = COMPOSE_NORMAL) -> dict:
    """Approved research material in; a final article candidate out, or a HOLD.

    Ten stages, each one either PASS or the stage that stopped the run. There is no
    stage that reruns an earlier stage, and no stage that regenerates prose to get a
    better verdict: the first HOLD is the answer, and it names itself.

    `fact_check_fn` is injected the same way `runner.run` injects research: the
    authoritative Fact Check lives outside this package (see `fact_check_unavailable`),
    and a test can exercise the orchestration without two live credentials.

    `frozen` replays a previous run's LEDGER, WORTH and ARCHITECTURE from its artifacts
    instead of executing them, so a change to a later stage can be tested without paying
    seven minutes for two stages that already produced a valid result. Those stages then
    report REPLAYED rather than PASS and the result carries `replay: True` -- a replay is
    not evidence of autonomy and must never be able to look like it.
    """
    P = composition_provider(provider)
    subject = subject or pack.get("subject") or ""
    st = {s: {"status": NOT_RUN} for s in STAGES}
    calls: dict[str, int] = {}
    repairs: dict[str, int] = {}
    t0 = time.time()

    # Wall-clock per stage, measured rather than inferred from provider durations: a
    # stage's own validators, span checks and deterministic derivations do not appear in
    # any model call's duration_ms, and on a hundred-fact ledger they are not free.
    elapsed: dict[str, float] = {}
    marks = {"_last": time.time()}

    def record(stage, payload):
        now = time.time()
        elapsed[stage] = round(now - marks["_last"], 1)
        marks["_last"] = now
        st[stage] = payload
        calls[stage] = payload.get("model_calls", 0)
        repairs[stage] = payload.get("repairs", 0)
        return payload

    def out(failure_stage=None, failure_reason=None, code=None, article=None,
            package_out=None, article_surface=SURFACE_PROSE_FINISH):
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
            # THE PUBLICATION BUNDLE, and the two facts that make it verifiable: which
            # surface it belongs to, and the hash of each half. A consumer can prove the
            # package it is about to publish was written from the article it is about to
            # publish, which is the whole point of discarding a package with a polish.
            "package": package_out,
            "package_status": (st.get(PACKAGE) or {}).get("package_status", NOT_RUN),
            "article_surface": article_surface,
            "article_sha256": C.sha256_text(article or ""),
            "bundle_sha256": C.sha256_text(bundle_text(article or "", package_out)),
            # Publication needs an article AND the furniture it publishes behind. A
            # missing package is not an editorial rejection and never reads as one: the
            # article stands, and the candidate goes to the owner instead of to the site.
            "stopped_after": stop_after or "",
            "publication_ready": bool(failure_stage is None and package_out
                                      and not stop_after),
            "owner_review": bool(failure_stage is None and not package_out),
            "words": len((article or "").split()),
            "model_calls_by_stage": dict(calls),
            "model_calls_total": sum(calls.values()),
            "repairs_by_stage": {k: v for k, v in repairs.items() if v},
            "advisories": (st.get(SAFETY) or {}).get("advisories") or [],
            "runtime_by_stage": dict(elapsed),
            "compose_mode": compose_mode,
            "replay": bool(replay),
            "replayed_stages": sorted(s for s in STAGES
                                      if st[s].get("status") == REPLAYED),
            "runtime_seconds": round(time.time() - t0, 1),
            "subject": subject,
        }
        if out_dir is not None:
            persist(out_dir, result)
        return result

    replay = frozen or {}
    surface = SURFACE_PROSE_FINISH
    pkg = None
    try:
        if replay.get("ledger"):
            ledger = replay["ledger"]
            st[LEDGER] = {"status": REPLAYED, "ledger": ledger, "facts": len(ledger),
                          "model_calls": 0, "repairs": 0}
            calls[LEDGER] = repairs[LEDGER] = 0
        else:
            led = record(LEDGER, freeze_ledger(P, pack, subject))
            ledger = led["ledger"]

        if replay.get("worth"):
            w = replay["worth"]
            st[WORTH] = dict(w, status=REPLAYED, model_calls=0, repairs=0)
            calls[WORTH] = repairs[WORTH] = 0
        else:
            w = record(WORTH, worth_gate(P, ledger, subject))

        # CHEAP TRIAGE. Two model calls answer "does this subject belong here, and what
        # does the reading stand on" -- and that is the whole question a selector needs
        # before deciding which candidates deserve a composition. Stopping here is not a
        # HOLD and is never recorded as one: the run did what it was asked to do.
        if stop_after == WORTH:
            return out(article=None, package_out=None, article_surface=surface)

        frozen_article = replay.get("article")
        if replay.get("architecture"):
            arch = replay["architecture"]
            errs = check_architecture(arch, ledger)
            if errs:
                raise CompositionHold(
                    ARCHITECTURE, ARCHITECTURE_HOLD,
                    ["the replayed architecture does not validate against the replayed "
                     "ledger"] + errs[:8], {"architecture": arch, "failures": errs})
            st[ARCHITECTURE] = {"status": REPLAYED, "architecture": arch,
                                "beats": len(arch.get("beats") or []),
                                "model_calls": 0, "repairs": 0}
            calls[ARCHITECTURE] = repairs[ARCHITECTURE] = 0
        else:
            a = record(ARCHITECTURE, architect(
                P, ledger, w, subject,
                visual_context=load_visual_context(out_dir)))
            arch = a["architecture"]

        cut = record(CUT_TERMS, derive_cut_watch_terms(arch, ledger))

        if frozen_article:
            # Resume at the grounder/repair boundary on prose that already passed the
            # Writer, Continuity and the safety stack. The packet is rebuilt from the
            # same architecture and ledger, deterministically, so nothing is guessed.
            packet_r, prompt_r = writer_packet(arch, ledger, cut.get("prohibitions"))
            wr = {"status": REPLAYED, "article_text": frozen_article,
                  "packet": packet_r, "prompt": prompt_r, "model_calls": 0, "repairs": 0,
                  "words": len(frozen_article.split()),
                  "negative_lineage_verified": replay.get("negative_lineage") or {}}
            st[WRITER] = wr
            calls[WRITER] = repairs[WRITER] = 0
            draft = frozen_article
        else:
            wr = record(WRITER, write_article(P, arch, ledger, cut.get("prohibitions"),
                                              compose_mode=compose_mode))
            draft = wr["article_text"]

        if frozen_article:
            cont = {"status": REPLAYED, "article_text": frozen_article, "edits": [],
                    "semantic_delta_errors": [], "model_calls": 0, "repairs": 0,
                    "words": len(frozen_article.split())}
            st[CONTINUITY] = cont
            calls[CONTINUITY] = repairs[CONTINUITY] = 0
        else:
            cont = record(CONTINUITY, continuity_pass(P, draft, arch))

        # CONTINUITY IS FAIL-SAFE, and this is the whole point of the stage's position in
        # the ladder. It is an OPTIONAL linguistic improvement over an article that is
        # already correct, so it is not allowed to destroy one. If its delta is clean the
        # edited prose is used; if it added a fact, event, relation or negative the edit
        # is DISCARDED WHOLE and the Writer draft carries on in its place.
        #
        # Deterministic: no second Continuity call, no Writer regeneration, no repair
        # prose. The fallback is the draft the Writer already produced, and the full
        # post-writer safety stack then runs on whichever text was chosen -- so nothing
        # reaches the Grounder on the strength of an audit performed against other prose.
        delta_errs = cont["semantic_delta_errors"]
        if delta_errs:
            final = draft
            carried = "writer_draft"
            cont["discarded"] = True
            cont["discard_reason"] = delta_errs
            # A discarded edit inherits nothing. Only the Writer's own verified lineage
            # over its own sentences applies, which is what forward-only means.
            lineage = wr["negative_lineage_verified"]
        else:
            final = cont["article_text"]
            carried = "continuity_final"
            lineage = carry_negative_lineage(
                cont["edits"], draft, final, wr["negative_lineage_verified"])
        cont["carried_text"] = carried
        cont["negative_lineage_carried"] = lineage

        # PROSE FINISH -- surface only, and BEFORE anything factual is checked, so the
        # exact bytes Safety, Grounding and Fact Check read are the bytes that publish.
        # Fail-safe like Continuity: a discarded polish carries the incoming text forward
        # and costs the run nothing. Skipped on a replay, where the article is frozen.
        pre_polish = None
        if frozen_article:
            st[PROSE_FINISH] = {"status": REPLAYED, "article_text": final,
                                "applied": False, "reason": "replay: article is frozen",
                                "model_calls": 0, "repairs": 0}
            calls[PROSE_FINISH] = repairs[PROSE_FINISH] = 0
        else:
            pf = record(PROSE_FINISH, prose_finish(P, final, arch))
            if pf.get("applied"):
                pre_polish = final
                final = pf["article_text"]
                # The polish rewrote sentences, so the Writer's per-sentence negative
                # lineage no longer maps onto them. Safety re-derives what it needs from
                # the packet and the ledger; carrying a stale sentence map would be worse
                # than carrying none.
                lineage = wr["negative_lineage_verified"]

        # THE PACKAGE, written from the bytes that publish and checked with them. It is
        # public prose, so it goes into the same bundle the gates read; it is written here
        # rather than after the Reader because a title can be factually wrong and the only
        # honest place to find that out is the factual stack.
        def make_package(text, refusals=None):
            if not package:
                st[PACKAGE] = {"status": SKIPPED, "package": None,
                               "package_status": SKIPPED, "model_calls": 0, "repairs": 0}
                calls[PACKAGE] = repairs[PACKAGE] = 0
                return None
            return record(PACKAGE, editorial_package(
                P, text, arch, (w or {}).get("worth_gate"), refusals)).get("package")

        def audit(text, pkg_, **kw):
            # The lineage this call actually saw is recorded ON the result, because it is
            # the one Safety input that is REBOUND during the run -- Continuity may carry
            # it forward, a discarded polish resets it to the Writer's own. Persisting
            # `cont["negative_lineage_carried"]` instead would file a value Safety may
            # never have been given, and a re-audit built on it would not be a re-audit.
            r = safety_audit(draft, text, wr["packet"], arch, ledger, cut["terms"],
                             cut, lineage, package=pkg_, **kw)
            r["negative_lineage_used"] = lineage
            r["audited_text_sha256"] = C.sha256_text(text or "")
            return r

        def _reader_gate_of(text, advisories):
            """The run's own reader_gate, as a plain callable for the completion loop.
            Never records: a CANDIDATE's gate result is not the run's Reader verdict
            until the loop accepts it."""
            return reader_gate(P, text, advisories)

        def _candidate_package_completion(sa_c, article_c, package_c):
            """Progress-bounded package Safety completion on a CANDIDATE's temporary
            package. Returns (package_or_None, model_calls, safety_result). Nothing here
            touches accepted state or the run's counters -- if the Reader candidate is
            refused further down, this package is discarded with it."""
            comp = package_only_safety_completion(
                P, sa_c, article_c, package_c, ledger, wr["packet"], draft,
                audit_fn=audit)
            if not comp["attempted"]:
                return None, 0, sa_c
            prep = comp["repair"]
            n = prep.get("model_calls", 0)
            if prep["status"] != PASS:
                return None, n, sa_c
            sa_new = audit(article_c, prep["package"])
            sa_new["after_package_safety_repair"] = True
            _carry_package_completion(sa_new, prep)
            return prep["package"], n, sa_new

        pkg = make_package(final)
        pkg_ref = [pkg]
        sa = record(SAFETY, audit(final, pkg))
        sa["carried_text"] = carried

        # A POLISH MAY NOT COST A RUN THE UNPOLISHED TEXT WOULD HAVE WON. Prose Finish is
        # an optional improvement over an article that was already publishable, and this
        # audit is deterministic and free -- so when the polished surface fails, ask
        # whether the text that went into it is clean before losing the article to an
        # optional stage. No second polish and no rewrite: the incoming text is the same
        # fallback Continuity already uses one stage above.
        #
        # AND THE FALLBACK IS VERSION-COHERENT. The package was written from the polished
        # prose; if the polish is discarded, that package describes text that will not
        # publish, and publishing the two together would be a mixed-version bundle. So the
        # package is discarded with the polish and rewritten from the surface that is
        # actually shipping, and the whole bundle is audited again.
        if sa["status"] != PASS and pre_polish is not None:
            probe = audit(pre_polish, None)
            if probe["status"] == PASS:
                st[PROSE_FINISH]["discarded_at_safety"] = sa["blocking"][:6]
                st[PROSE_FINISH]["applied"] = False
                final, surface = pre_polish, PRE_POLISH_FALLBACK
                pkg = pkg_ref[0] = make_package(final)
                sa = record(SAFETY, audit(final, pkg))
                sa["carried_text"] = carried
                sa["polish_discarded_at_safety"] = True
        sa["continuity_discarded"] = bool(delta_errs)

        # ONE SAFETY REPAIR, tried before the pre-polish fallback's own failure becomes
        # terminal. See safety_repair_findings/safety_repair above for the eligibility
        # rule and the mechanical guarantee (the SAME apply_grounding_repair() Stage 8b
        # uses). A category this stage does not recognise makes the whole attempt
        # ineligible, and the run falls straight through to the unchanged HOLD below.
        if sa["status"] != PASS:
            sfindings = safety_repair_findings(sa, final, package_prose(pkg),
                                              draft_text=draft)
            if sfindings:
                srep = safety_repair(P, final, sfindings, ledger, wr["packet"])
                # Counted here, unconditionally, because the model call happened whether
                # or not the repair was accepted -- a repair that HOLDs still cost one
                # call, and the line below (after record()'s reset, on PASS only) would
                # otherwise leave a rejected repair attempt invisible to the bookkeeping.
                calls[SAFETY] = calls.get(SAFETY, 0) + srep.get("model_calls", 0)
                if srep["status"] == PASS:
                    final = srep["article_text"]
                    pkg = pkg_ref[0] = make_package(final)
                    # record() would reset calls[SAFETY] to 0 (safety_audit() is a
                    # deterministic, model-free check, same as every other call to it in
                    # this function) -- so the repair's own one call is added AFTER, the
                    # same way Grounding's repair attributes its cost to its own stage
                    # rather than to the re-audit that follows it.
                    sa = record(SAFETY, audit(final, pkg, repair=srep))
                    sa["carried_text"] = carried
                    sa["continuity_discarded"] = bool(delta_errs)
                    sa["after_safety_repair"] = True
                    repairs[SAFETY] = 1
                    calls[SAFETY] = calls.get(SAFETY, 0) + srep.get("model_calls", 0)

        # ONE PACKAGE-ONLY SAFETY REPAIR (STAGE 9c), tried only when every remaining
        # blocking finding is package-surface machine language -- see the STAGE 9c
        # comment above for the eligibility rule and why "the article is clean" falls
        # out of that same check rather than needing a separate flag. This is the fix
        # for a package REGENERATED just above (by make_package(), inside the article
        # repair's own PASS branch) reintroducing a leak the article repair had no way
        # to see coming, because the text it would need to fix did not exist yet.
        if sa["status"] != PASS:
            comp = package_only_safety_completion(
                P, sa, final, pkg, ledger, wr["packet"], draft, audit_fn=audit)
            if comp["attempted"]:
                prep = comp["repair"]
                calls[SAFETY] = calls.get(SAFETY, 0) + prep.get("model_calls", 0)
                if prep["status"] == PASS:
                    # No make_package() call here or after -- the repaired package IS
                    # what proceeds downstream, so nothing model-generated can silently
                    # invalidate this recheck the way the regeneration above did.
                    pkg = pkg_ref[0] = prep["package"]
                    sa = record(SAFETY, audit(final, pkg))
                    sa["carried_text"] = carried
                    sa["continuity_discarded"] = bool(delta_errs)
                    sa["after_package_safety_repair"] = True
                    _carry_package_completion(sa, prep)
                    repairs[SAFETY] = 1
                    calls[SAFETY] = calls.get(SAFETY, 0) + prep.get("model_calls", 0)

        if sa["status"] != PASS:
            why = "; ".join(sa["blocking"])[:600]
            if delta_errs:
                why = ("continuity was discarded (%s) and the Writer draft did not pass "
                       "either: %s" % ("; ".join(str(e) for e in delta_errs)[:200], why))
            return out(SAFETY, why, SAFETY_HOLD, final, pkg, surface)

        g = record(GROUNDING, ground_candidate(P, bundle_text(final, pkg), source_text,
                                               source_sha, pack, arch, wr["packet"]))

        # A GROUNDING FAILURE THAT IS ENTIRELY IN THE FURNITURE is repaired by rewriting
        # the furniture, not the article -- ONCE per run, on the exact findings. The
        # article did nothing wrong and regenerating it would be the expensive way to fix
        # a dek.
        #
        # It is tried at BOTH grounding decision points, and the first live run is why:
        # the article took its one factual repair, passed, and the run then died on two
        # findings that were both in the META_DESCRIPTION and the EXCERPT. A clean article
        # lost to its own homepage card is the exact waste this stage was added to prevent.
        # The budget is one rewrite for the run, not one per decision point.
        repackaged = [False]

        def repackage_if_only_the_furniture_failed(gr):
            """Returns a new grounding result, or the one it was given."""
            if gr["status"] == PASS or not pkg_ref[0] or repackaged[0]:
                return gr
            art_bad, pkg_bad = split_by_surface(gr["blocking"], pkg_ref[0])
            if art_bad or not pkg_bad:
                return gr
            repackaged[0] = True
            pkg_ref[0] = make_package(final, refusals=[
                "%s on %s: %s" % (f.get("classification"), f.get("surface"),
                                  str(f.get("quote") or f.get("claim") or "")[:200])
                for f in pkg_bad])
            sa_p = record(SAFETY, audit(final, pkg_ref[0]))
            sa_p["after_repackage"] = True
            if sa_p["status"] != PASS:
                # The furniture-only rewrite above is itself a freshly regenerated
                # package, exactly the shape package_only_safety_completion exists for --
                # it may reintroduce the same class of machine-language leak the rewrite
                # was trying to avoid. This spends its OWN one-shot budget (a distinct
                # regenerated surface from any package-only repair already used earlier
                # in the run), not a second attempt on the same surface, and does not
                # change the one-repackage-per-run rule above (`repackaged[0]` is already
                # set).
                comp_p = package_only_safety_completion(
                    P, sa_p, final, pkg_ref[0], ledger, wr["packet"], draft,
                    audit_fn=audit)
                if comp_p["attempted"]:
                    prep_p = comp_p["repair"]
                    calls[SAFETY] = calls.get(SAFETY, 0) + prep_p.get("model_calls", 0)
                    if prep_p["status"] == PASS:
                        pkg_ref[0] = prep_p["package"]
                        sa_p = record(SAFETY, audit(final, pkg_ref[0]))
                        sa_p["after_repackage"] = True
                        sa_p["after_package_safety_repair"] = True
                        _carry_package_completion(sa_p, prep_p)
                        repairs[SAFETY] = 1
                        calls[SAFETY] = calls.get(SAFETY, 0) + prep_p.get(
                            "model_calls", 0)
                if sa_p["status"] != PASS:
                    raise CompositionHold(
                        SAFETY, SAFETY_HOLD,
                        ["the rewritten package did not pass the safety stack"]
                        + sa_p["blocking"][:6])
            # Captured BEFORE record() below overwrites both st[GROUNDING] and the
            # GROUNDING counters with this bare recheck's own (repairs 0). Whatever the
            # pre-repackage completion phase accepted really happened and is still in
            # `final`; the artifact has to keep saying so.
            carried = grounding_completion_detail(gr)
            g_repairs = repairs.get(GROUNDING, 0)
            g_new = record(GROUNDING, ground_candidate(P, bundle_text(final, pkg_ref[0]),
                                                       source_text, source_sha, pack,
                                                       arch, wr["packet"]))
            g_new["after_repackage"] = True
            g_new["repackage_findings"] = [f.get("surface") for f in pkg_bad]
            if carried:
                g_new["pre_repackage_completion"] = carried
            repairs[GROUNDING] = g_repairs + g_new.get("repairs", 0)
            calls[GROUNDING] = calls.get(GROUNDING, 0) + 1
            repairs[PACKAGE] = repairs.get(PACKAGE, 0) + 1
            return g_new

        g = repackage_if_only_the_furniture_failed(g)

        # PROGRESS-BOUNDED GROUNDING COMPLETION (owner-directed, 2026-09-09) replaces the
        # old fixed one-repair-plus-one-completion-pass budget (Stage 8b + Stage 8c) --
        # see grounding_completion_loop for why. Repair continues only as long as each
        # accepted proposal is TRANSACTIONALLY proven better -- a strictly smaller
        # Grounding blocking set, no new Safety blocker -- subject to
        # GROUNDING_COMPLETION_MAX_ITERATIONS as a runaway fuse, never as a target. No
        # Writer regeneration, no architecture rerun, no new research, at any point; the
        # package is untouched throughout (a Grounding factual repair changes only the
        # article, exactly as before).
        if g["status"] != PASS:
            gc = grounding_completion_loop(P, final, pkg, g, ledger, wr["packet"], arch,
                                           pack, source_text, source_sha, audit)
            # gc["model_calls"] is ONLY this call's own (proposals + rechecks) -- added to
            # what calls[GROUNDING] already carries from the initial check (and any
            # furniture repackage above) before record() overwrites it with the total,
            # the same accumulate-then-record pattern every repair path in this run uses.
            gc["model_calls"] = calls.get(GROUNDING, 0) + gc["model_calls"]
            # PHASE MARKER, not a second loop: this IS the same grounding_completion_loop
            # -- tagged so its own history survives being read even after a later phase
            # (below) has to overwrite st[GROUNDING] with its own result. See
            # test_pre_and_post_repackage_completion_histories_survive_persistence.
            gc["grounding_completion_phase"] = "PRE_REPACKAGE"
            g = record(GROUNDING, gc)
            if gc["grounding_repairs_accepted"]:
                final = gc["article_text"]
                # The winning candidate's OWN Safety verdict, computed inside the loop
                # with that candidate's own `repair=` baseline widening -- reused exactly,
                # never re-derived here, so this can never disagree with what the loop
                # itself already proved. See grounding_completion_loop's `final_safety`.
                sa_gc = gc["final_safety"]
                sa_gc["after_grounding_completion"] = True
                if sa_gc["status"] != PASS:
                    return out(SAFETY,
                               "an accepted grounding repair did not survive the safety "
                               "stack: %s" % "; ".join(sa_gc["blocking"])[:400],
                               SAFETY_HOLD, final, pkg, surface)

        pkg = pkg_ref[0]
        _repackaged_before = repackaged[0]
        g = repackage_if_only_the_furniture_failed(g)
        pkg = pkg_ref[0]

        # POST-REPACKAGE LOOP-BACK (owner-directed, 2026-09-09). Real production
        # evidence, retained Poetry: the furniture repackage's own mandatory recheck can
        # discover a brand-new ARTICLE-surface finding nothing has tried to fix yet --
        # the one-shot furniture rewrite did not touch the article, so this is not a
        # residue of that rewrite, it is a fresh Grounding read that simply did not agree
        # with an earlier one. Before this fix, such a finding went straight to a
        # terminal HOLD with zero repair attempts of any kind -- not a repair-quality
        # failure and not a ceiling failure, an integration gap: nothing routed it back
        # into completion at all.
        #
        # ONE semantic owner: the SAME grounding_completion_loop() the pre-repackage
        # phase already used, on the CURRENT accepted article and the EXACT
        # just-rebuilt package (pkg_ref[0] -- never regenerated here; if an accepted
        # article repair makes that package invalid, the loop's own Grounding recheck
        # against it is what would expose that, same as any other candidate). Fires
        # ONLY when repackage fired AT THIS CALL (not when call-site-1's repackage
        # already ran and fed its result into the phase above through the ordinary
        # `g["status"] != PASS` path) -- `_repackaged_before` distinguishes the two so
        # this never re-processes findings the phase above already had its own chance
        # at. The one-repackage-per-run rule is untouched: this loop only ever edits
        # article text, so it cannot itself trigger a second repackage, and
        # `repackaged[0]` is already spent by the time this runs.
        if repackaged[0] and not _repackaged_before and g["status"] != PASS:
            carried_pre = g.get("pre_repackage_completion")
            art_bad, _pkg_bad = split_by_surface(g["blocking"], pkg_ref[0])
            if art_bad:
                gc2 = grounding_completion_loop(P, final, pkg_ref[0], g, ledger,
                                                wr["packet"], arch, pack, source_text,
                                                source_sha, audit)
                gc2["model_calls"] = calls.get(GROUNDING, 0) + gc2["model_calls"]
                gc2["grounding_completion_phase"] = "POST_REPACKAGE"
                # Carried by the repackage itself (single source), not re-derived here:
                # grounding_completion_loop() returns dict(g) of its LAST grounding
                # result, so an accepted post-repackage repair would otherwise drop the
                # key the un-repaired path happens to inherit.
                if carried_pre is not None:
                    gc2["pre_repackage_completion"] = carried_pre
                g = record(GROUNDING, gc2)
                if gc2["grounding_repairs_accepted"]:
                    final = gc2["article_text"]
                    sa_gc2 = gc2["final_safety"]
                    sa_gc2["after_grounding_completion"] = True
                    sa_gc2["after_repackage"] = True
                    if sa_gc2["status"] != PASS:
                        return out(SAFETY,
                                   "an accepted post-repackage grounding repair did not "
                                   "survive the safety stack: %s"
                                   % "; ".join(sa_gc2["blocking"])[:400],
                                   SAFETY_HOLD, final, pkg_ref[0], surface)

        if g["status"] != PASS:
            _iters = g.get("grounding_completion_iterations")
            _after = (" AFTER %d repair attempt(s) over %d iteration(s), %d accepted, "
                      "%d rejected"
                      % (g.get("grounding_repair_proposals", 0), _iters,
                         g.get("grounding_repairs_accepted", 0),
                         g.get("grounding_repairs_rejected", 0))
                      if _iters else "")
            return out(GROUNDING,
                       "grounding status %r; %d blocking finding(s)%s: %s"
                       % (g["grounding_status"], len(g["blocking"]), _after,
                          [("%s %s %s" % (f.get("classification"),
                                          surface_of(str(f.get("quote") or ""), pkg),
                                          str(f.get("quote") or f.get("claim") or "")[:70]))
                           for f in g["blocking"]][:4]),
                       GROUNDING_HOLD, final, pkg, surface)

        if fact_check:
            fc = record(FACT_CHECK,
                        (fact_check_fn or fact_check_unavailable)(bundle_text(final, pkg)))
            # A fact check that COULD NOT RUN is deliberately not blocked here: it flows on
            # to the Reader carrying its own status, so an infrastructure failure is never
            # recorded as an editorial rejection. Publication is refused elsewhere, twice --
            # publication_safety_bridge will not stamp publication_eligible or
            # fact_check_status without a real strict check, and publish_best additionally
            # requires fact_check_extraction_status "ok" with claims_extracted > 0 (added
            # 2026-08-25, after a candidate carried publication_eligible true while its
            # extraction had raised).
            #
            # What was wrong was the BRIDGE calling an extraction failure HOLD, making it
            # indistinguishable from a found contradiction: the only candidate ever to reach
            # this stage produced "FACT_CHECK HOLD, blocking contradiction(s): []" on an
            # article nothing had checked. Fixed in the bridge's status taxonomy.
            if fc.get("status") == HOLD:
                bad = fc.get("blocking_contradictions") or []
                fc["surfaces"] = sorted({surface_of(str(c), pkg) for c in bad})
                return out(FACT_CHECK,
                           "blocking contradiction(s) on %s: %s"
                           % (", ".join(fc["surfaces"]) or ARTICLE_SURFACE, bad[:4]),
                           FACT_CHECK_HOLD, final, pkg, surface)
        else:
            st[FACT_CHECK] = {"status": SKIPPED}

        if reader:
            rg = record(READER, reader_gate(P, final, sa.get("advisories")))

            # TRANSACTIONAL, PROGRESS-BOUNDED EDITORIAL COMPLETION (owner-directed,
            # 2026-09-09) replaces the old one-repair-then-terminal budget -- see
            # reader_completion_loop for the production run that forced it. The
            # difference that matters is not the count: a Reader repair is now a
            # PROPOSAL, and the SAME safety_audit() and ground_candidate() this run
            # already uses are its ACCEPTANCE TESTS, not repair triggers. A proposal that
            # invents anything is refused whole -- with the package it regenerated -- and
            # the article that reached this stage factually clean stays exactly as it is.
            if rg["status"] != PASS:
                rc = reader_completion_loop(
                    P, final, pkg, rg, wr["packet"], ledger, draft, pack, arch,
                    source_text, source_sha,
                    audit_fn=audit, package_fn=make_package, gate_fn=_reader_gate_of,
                    package_completion_fn=_candidate_package_completion)
                # Per stage, never lumped: the proposals and Reader rechecks are
                # READER's, the candidate audits and any package repair are SAFETY's, the
                # candidate rechecks are GROUNDING's -- the same attribution every other
                # repair path in this function uses.
                calls[READER] = calls.get(READER, 0) + rc["reader_model_calls"]
                _loop_safety_calls = rc["safety_model_calls"]
                _loop_grounding_calls = rc["grounding_model_calls"]
                if rc["reader_repairs_accepted"]:
                    # ONLY here does accepted state move -- and article and package move
                    # together, because the package is the one the accepted article's own
                    # Safety and Grounding actually approved.
                    final, pkg = rc["article_text"], rc["package"]
                    pkg_ref[0] = pkg
                    repairs[READER] = 1
                    if rc["final_safety"] is not None:
                        # record() resets calls[SAFETY]/repairs[SAFETY] to this audit's
                        # own (model-free) counts, so the loop's Safety cost and any
                        # package repair it accepted are restored on top, the same
                        # accumulate-after-record pattern used everywhere above.
                        sa_r = record(SAFETY, rc["final_safety"])
                        sa_r["carried_text"] = carried
                        sa_r["after_reader_repair"] = True
                        calls[SAFETY] = calls.get(SAFETY, 0) + _loop_safety_calls
                        if rc["package_repair_used"]:
                            repairs[SAFETY] = 1
                    if rc["final_grounding"] is not None:
                        g_r = record(GROUNDING, rc["final_grounding"])
                        g_r["after_reader_repair"] = True
                        calls[GROUNDING] = calls.get(GROUNDING, 0) + _loop_grounding_calls
                reader_calls_so_far = calls[READER]
                rg = record(READER, rc["gate"])
                calls[READER] = reader_calls_so_far
                repairs[READER] = 1 if rc["reader_repairs_accepted"] else 0
                rg["after_editorial_repair"] = True
                for k in ("reader_completion_iterations", "reader_repair_proposals",
                          "reader_repairs_accepted", "reader_repairs_rejected",
                          "reader_completion_history", "reader_initial_blocker_count",
                          "reader_final_blocker_count"):
                    rg[k] = rc[k]

            if rg["status"] != PASS:
                return out(READER,
                           "reader HOLD on %s" % ", ".join(sorted(rg["held"])),
                           READER_HOLD, final, pkg, surface)
        else:
            st[READER] = {"status": SKIPPED}

        return out(article=final, package_out=pkg, article_surface=surface)

    except CompositionHold as e:
        elapsed[e.stage] = round(time.time() - marks["_last"], 1)
        st[e.stage] = dict(e.payload, status=HOLD, code=e.code, reasons=e.reasons)
        return out(e.stage, "; ".join(e.reasons)[:600], e.code,
                   st.get(CONTINUITY, {}).get("article_text")
                   or st.get(WRITER, {}).get("article_text"),
                   package_out=pkg, article_surface=surface)


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

    # ── THE SAFETY STAGE'S OWN INPUTS, AS DATA (2026-09-06, issue #91) ──────────────
    # WRITER_PACKET.txt is the RENDERED PROMPT. It is the right thing to read and the
    # wrong thing to re-run: `safety_audit` takes the packet DICT, the ledger DICT and
    # the WHOLE cut report -- `cut_without_distinctive_terms` decides which cut material
    # is explained rather than blocking. None of those three was ever written, so a
    # published article could be re-grounded and re-fact-checked but never re-audited
    # for safety. That is what a live article turned out not to be able to prove.
    #
    # Written beside the artifacts that already exist, in the same plain way, and
    # additive: no existing file changes name, shape or content.
    if det.get(WRITER, {}).get("packet"):
        dump("WRITER_PACKET.json", det[WRITER]["packet"])
    if det.get(LEDGER, {}).get("ledger"):
        # First-class, not nested inside FINAL_EVIDENCE_MANIFEST. The manifest is an
        # evidence record for a reader; this is the argument the function takes.
        dump("LEDGER.json", det[LEDGER]["ledger"])
    if det.get(CUT_TERMS, {}).get("terms") is not None:
        dump("CUT_REPORT.json", {k: v for k, v in det[CUT_TERMS].items()
                                 if k != "status"})
    if det.get(SAFETY, {}).get("negative_lineage_used") is not None:
        dump("NEGATIVE_LINEAGE.json", det[SAFETY]["negative_lineage_used"])
    if result.get("article_text"):
        # The exact bytes Safety last audited, written here rather than relied upon from
        # runner.py's article.md: this file must exist for a HOLD too, and a bundle that
        # depends on a caller having written its final text is not a bundle.
        (d / "ARTICLE_FINAL.md").write_text(result["article_text"])
    if det.get(FACT_CHECK, {}).get("status") not in (None, NOT_RUN, SKIPPED):
        # UNDER ITS OWN NAME. new_engine_production writes the publication-safety
        # bridge's FACT_CHECK.json into this same directory AFTER the run returns, so
        # the composition stage's own record was overwritten on every ACCEPT and no
        # error was raised. Both are wanted; only one may be called FACT_CHECK.json.
        dump("COMPOSITION_FACT_CHECK.json", det[FACT_CHECK])
    if det.get(SAFETY, {}).get("audits"):
        _sd = det[SAFETY]
        dump("SAFETY_REPLAY.json", {
            "function": "new_engine_v1.composition.safety_audit",
            "retention_contract": "publication-audit-v1",
            "deterministic": True,
            "note": ("safety_audit makes no model call and reaches no network. Given the "
                     "files named below it reproduces its verdict exactly. Grounding and "
                     "Fact Check do NOT have this property."),
            "inputs": {
                "draft_text": "WRITER_DRAFT.md",
                "final_text": "ARTICLE_FINAL.md",
                "packet": "WRITER_PACKET.json",
                "arch": "ARCHITECTURE.json",
                "ledger": "LEDGER.json",
                "cut_terms": "CUT_REPORT.json#terms",
                "cut_report": "CUT_REPORT.json",
                "negative_lineage": "NEGATIVE_LINEAGE.json",
                "package": "EDITORIAL_PACKAGE.json",
                "repair": "FACTUAL_REPAIR.json",
            },
            "draft_sha256": C.sha256_text(det.get(WRITER, {}).get("article_text") or ""),
            "final_sha256": C.sha256_text(result.get("article_text") or ""),
            "audited_text_sha256": _sd.get("audited_text_sha256", ""),
            "repair_applied": bool((det.get(GROUNDING) or {}).get("repair")),
            "package_present": bool((det.get(PACKAGE) or {}).get("package")),
            "status": _sd.get("status", ""),
        })
    if det.get(WRITER, {}).get("article_text"):
        (d / "WRITER_DRAFT.md").write_text(det[WRITER]["article_text"])
    if det.get(CONTINUITY, {}).get("article_text"):
        (d / "CONTINUITY_FINAL.md").write_text(det[CONTINUITY]["article_text"])
    if det.get(SAFETY, {}).get("audits"):
        dump("SAFETY_AUDIT.json", {k: v for k, v in det[SAFETY].items()
                                   if k != "status"})
    if det.get(GROUNDING, {}).get("grounding"):
        dump("GROUNDING_FINDINGS.json", det[GROUNDING]["grounding"])
    if det.get(GROUNDING, {}).get("repair"):
        # Auditable by construction: every edit, what authorised it, and what it removed.
        dump("FACTUAL_REPAIR.json", det[GROUNDING]["repair"])
    # THE COMPLETION AUDIT, ONTO DISK (owner-directed, 2026-09-10).
    #
    # The completion pass gets its own file rather than being merged into the repair:
    # they are two different calls answering two different finding sets, and a later
    # auditor must be able to tell which pass removed what.
    #
    # WHAT WAS BROKEN. This wrote `det[GROUNDING]["completion"]` -- a key nothing in the
    # codebase has ever set (one reader, no writer). So the file appeared in 0 of 181
    # retained production runs, and every completion history since the loop was
    # introduced was computed and then dropped at the boundary. f13e719 added
    # blockers_before/blockers_after to those entries and asserted their survival
    # against `out["detail"][GROUNDING]` -- in memory, upstream of the loss, so it could
    # not see it. COMPOSITION_RESULT.json cannot cover for it either: it is written
    # `{k: v for k, v in result.items() if k != "detail"}`.
    #
    # The projection is grounding_completion_detail(), UNCHANGED and already the single
    # owner of which completion fields are audit-bearing: it returns None for a plain
    # grounding result that never entered the loop, and its whitelist carries no article
    # text, source text, packet, prompt or transcript. `pre_repackage_completion` is
    # added explicitly because it is a nested detail of that same shape and carrying a
    # phase over a later record() is the whole reason it exists -- a run that repaired,
    # repackaged and stopped keeps only that key, and it has to reach disk too.
    #
    # OBSERVATION ONLY. Nothing reads this file back: no gate, decision, safety check or
    # publication path depends on it, and every decision in this module is already final
    # by the time persist() runs.
    _completion = grounding_completion_detail(det.get(GROUNDING))
    _pre_completion = (det.get(GROUNDING) or {}).get("pre_repackage_completion")
    if _completion or _pre_completion:
        dump("FACTUAL_COMPLETION.json",
             dict(_completion or {},
                  **({"pre_repackage_completion": _pre_completion}
                     if _pre_completion else {})))
    if det.get(FACT_CHECK, {}).get("status") not in (None, NOT_RUN, SKIPPED):
        dump("FACT_CHECK.json", det[FACT_CHECK])
    if det.get(PACKAGE, {}).get("package"):
        dump("EDITORIAL_PACKAGE.json", det[PACKAGE]["package"])
    if det.get(READER, {}).get("dimensions"):
        dump("READER_AUDIT.json", {k: det[READER].get(k)
                                   for k in ("dimensions", "held", "one_line", "status")})


# ══════════════════════════════════════════════════════════════════════════════
# TWO COMPOSITIONS PER WORTH-PASS STORY (owner-directed, 2026-09-10)
# ══════════════════════════════════════════════════════════════════════════════
# THE RULE. After Worth PASSes, a story gets at most TWO complete compositions:
#
#   A  the normal engine, with every bounded local completion it already has
#   B  ONE fresh SAFE_RECOMPOSE from the SAME frozen upstream authority
#
# and then it is terminal. No third draft, no roulette, and no point at which the owner
# is asked to arbitrate wording -- the system publishes autonomously or HOLDs
# autonomously.
#
# WHY B IS NOT "REPAIR A". Local repair already exists and already runs inside each
# attempt; B sits ABOVE those mechanisms, not beside them. The whole value of B is
# INDEPENDENCE: a bad local wording choice in A must not contaminate B, so B is given no
# article, no package, no repair prose, no Grounding rewrite and no Reader edit from A.
# It shares exactly one thing with A -- the frozen upstream authority both were written
# from. That is enforced structurally rather than by instruction: `_frozen_upstream_of()`
# can only return ledger/worth/architecture, and the replay slot that would carry an
# article (`frozen["article"]`) is never populated here.
#
# WHY THIS NEEDS NO NEW REPLAY CONCEPT. run_story_architecture_composition already
# accepts `frozen=` to reuse LEDGER, WORTH and ARCHITECTURE instead of executing them,
# and publication_safety_bridge already treats REPLAYED as equivalent to PASS for those
# three stages and ONLY those three -- every later gate is re-run fresh, "`frozen=` or
# not", in the bridge's own words. So B cannot bypass Safety, Grounding, Fact Check or
# the Reader even by accident, and it costs nothing to reuse upstream: no Research call,
# no Ledger call, no Worth call, no Architecture call.
MAX_COMPOSITION_ATTEMPTS = 2

# ELIGIBLE A TERMINALS. A fresh composition can only plausibly help where the defect is
# in the COMPOSITION SURFACE -- the prose or the furniture written from a sound ledger.
FALLBACK_ELIGIBLE = {SAFETY: SAFETY_HOLD, GROUNDING: GROUNDING_HOLD,
                     FACT_CHECK: FACT_CHECK_HOLD, READER: READER_HOLD}
# Upstream authority B would inherit. If any of these did not actually succeed in A,
# there is nothing sound to recompose FROM.
FALLBACK_REQUIRED_UPSTREAM = (LEDGER, WORTH, ARCHITECTURE)
# Never a composition-surface defect: the remedy is different code, a different provider
# or different evidence, and a second draft would only spend a second full composition
# discovering that.
FALLBACK_REFUSED_CODES = (CLAUDE_SUBSCRIPTION_LIMIT, PACKAGE_TECHNICAL_FAILURE,
                          LEDGER_HOLD, WORTH_HOLD, ARCHITECTURE_HOLD, CUT_TERMS_HOLD,
                          WRITER_HOLD, CONTINUITY_HOLD)


def fallback_recomposition_eligible(result: dict | None) -> tuple:
    """(eligible, reason) -- can a FRESH composition plausibly resolve this WITHOUT
    changing Research, the Ledger, Worth or the Architecture?

    Deterministic and fail-closed. It reads the stage/reason record the run already
    produced and nothing else: no model opinion, no prose inspection, no guess about what
    a gate "probably meant". Anything it does not positively recognise is refused, so a
    new failure mode costs a HOLD rather than a silent second composition.
    """
    if not isinstance(result, dict):
        return False, "no composition result"
    if result.get("status") == PASS:
        return False, "attempt passed; no fallback needed"
    # A fallback that could itself trigger a fallback is the third draft this rule
    # exists to forbid. Checked first, and by the attempt's own recorded mode.
    mode = result.get("compose_mode")
    if mode is None:
        return False, "result records no compose_mode; refusing rather than assuming one"
    if mode != COMPOSE_NORMAL:
        return False, ("attempt was already %s; %d compositions is the maximum"
                       % (mode, MAX_COMPOSITION_ATTEMPTS))
    code = result.get("reason_code") or ""
    if code in FALLBACK_REFUSED_CODES:
        return False, "%s is not a composition-surface defect" % code
    stage = result.get("failure_stage")
    if stage not in FALLBACK_ELIGIBLE:
        return False, "HOLD at %s is not an eligible composition terminal" % (stage or "?")
    if code != FALLBACK_ELIGIBLE[stage]:
        return False, "reason_code %r is not %s's own editorial HOLD" % (code, stage)
    stages = result.get("stages") or {}
    for s in FALLBACK_REQUIRED_UPSTREAM:
        if stages.get(s) not in (PASS, REPLAYED):
            return False, ("%s did not succeed (%s); there is no sound upstream to "
                           "recompose from" % (s, stages.get(s)))
    det = result.get("detail") or {}
    if not (det.get(LEDGER) or {}).get("ledger"):
        return False, "no frozen ledger to recompose from"
    if not (det.get(ARCHITECTURE) or {}).get("architecture"):
        return False, "no frozen architecture to recompose from"
    if not str(result.get("article_text") or "").strip():
        return False, "attempt produced no article; the defect is not in its prose"
    return True, "%s at %s is composition-surface with sound frozen upstream" % (code,
                                                                                 stage)


def _frozen_upstream_of(result: dict) -> dict:
    """The ONLY state that crosses from one attempt to the next.

    Three keys, by construction: the frozen ledger, the Worth verdict and the frozen
    architecture. There is deliberately no branch here that could add the article, the
    package, an edit list, a finding or a repair history -- the isolation B depends on is
    this function's return type, not a promise made in a prompt.
    """
    det = result.get("detail") or {}
    return {"ledger": (det.get(LEDGER) or {}).get("ledger"),
            "worth": det.get(WORTH),
            "architecture": (det.get(ARCHITECTURE) or {}).get("architecture")}


def _attempt_record(label: str, result: dict, out_dir) -> dict:
    """One audit row per composition. Enough to tell which article, package and gate
    verdicts belong to which attempt, without carrying either article's prose."""
    return {"attempt": label,
            "mode": result.get("compose_mode"),
            "status": result.get("status"),
            "terminal_stage": result.get("failure_stage"),
            "reason_code": result.get("reason_code"),
            "failure_reason": str(result.get("failure_reason") or "")[:400] or None,
            "stages": dict(result.get("stages") or {}),
            "article_sha256": result.get("article_sha256"),
            "bundle_sha256": result.get("bundle_sha256"),
            "words": result.get("words"),
            "package_present": bool(result.get("package")),
            "package_status": result.get("package_status"),
            "publication_ready": bool(result.get("publication_ready")),
            "model_calls_total": result.get("model_calls_total"),
            "model_calls_by_stage": dict(result.get("model_calls_by_stage") or {}),
            "repairs_by_stage": dict(result.get("repairs_by_stage") or {}),
            "artifact_dir": str(out_dir) if out_dir is not None else None}


def run_composition_with_fallback(
        provider, *, pack: dict, source_text: str, source_sha: str, subject: str = "",
        fact_check: bool = True, reader: bool = True, package: bool = True,
        stop_after: str = "", fact_check_fn=None, out_dir=None,
        frozen: dict | None = None) -> dict:
    """Composition A, and -- only for an eligible composition-surface HOLD -- ONE fresh
    SAFE_RECOMPOSE composition B. Returns the attempt that decides the run.

    The returned dict IS a composition result, of exactly the shape
    run_story_architecture_composition returns, so every existing consumer (the runner's
    WRITER_OUTPUT emission, the decision, the safety bridge, publish_best) keeps working
    unchanged -- and, because it is the WINNING attempt's own result, a held article or a
    refused package from A structurally cannot reach publication state. A's artifacts are
    never overwritten: B persists to its own subdirectory.
    """
    import pathlib
    a = run_story_architecture_composition(
        provider, pack=pack, source_text=source_text, source_sha=source_sha,
        subject=subject, fact_check=fact_check, reader=reader, package=package,
        stop_after=stop_after, fact_check_fn=fact_check_fn, out_dir=out_dir,
        frozen=frozen, compose_mode=COMPOSE_NORMAL)
    attempts = [_attempt_record("A", a, out_dir)]
    eligible, why = fallback_recomposition_eligible(a)

    def decorate(winner, triggered):
        r = dict(winner)
        r["composition_attempts"] = attempts
        r["composition_attempts_count"] = len(attempts)
        # Per attempt, never summed into either attempt's own count: A's calls are A's.
        r["attempt_a_model_calls"] = a.get("model_calls_total")
        r["attempt_b_model_calls"] = (attempts[1]["model_calls_total"]
                                      if len(attempts) > 1 else None)
        r["composition_model_calls_total"] = sum(
            x["model_calls_total"] or 0 for x in attempts)
        r["fallback_recomposition_triggered"] = triggered
        r["fallback_recomposition_reason"] = why
        r["winning_attempt"] = attempts[-1]["attempt"] if triggered else "A"
        return r

    if not eligible:
        # THE SINGLE-ATTEMPT LAYOUT IS UNTOUCHED. A already persisted to out_dir and
        # nothing moves, so every existing consumer of a run directory -- the night
        # driver, publish_best, the safety bridge -- sees exactly what it saw before this
        # module existed. That is deliberate: the fallback must cost the common case
        # nothing, including nothing in its artifact shape.
        return decorate(a, False)

    # ── ATTEMPT ARTIFACT INTEGRITY (2026-09-10, cycle 1) ──────────────────────────
    # WHY THIS EXISTS. Production run production-20260910T093541Z-8a338f42 held one
    # directory describing TWO different articles: COMPOSITION_RESULT.json and
    # ARTICLE_FINAL.md were A's (HOLD at READER, article 145d18e2), while the
    # runner-level WRITER_OUTPUT.json the decision and the bridge are built from was B's
    # (HOLD at GROUNDING, article 3eb5a36f). A had persisted to out_dir during its own
    # run and nothing ever re-persisted the winner over it, so the top-level record
    # contradicted the decision -- and the night driver, which reads
    # COMPOSITION_RESULT.json, duly reported the wrong terminal stage for the run.
    #
    # Both attempts held there, so nothing mispublished. The dangerous shape is A HOLD
    # with B PASS: the top level would read HOLD while the run legitimately publishes B,
    # and any consumer trusting that file would refuse a good article -- suppressing the
    # exact throughput this whole mechanism exists to produce.
    #
    # THE FIX IS PERSISTENCE ONLY. A's artifacts move, whole, into attempt-A/ BEFORE B
    # runs, so they are safe from anything B does and are never overwritten. Then the
    # attempt the run's verdict actually came from is persisted at top level. Moving
    # FILES only, and before runner._persist has written anything of its own, is what
    # makes this exact rather than a hardcoded filename list: whatever composition wrote
    # for A goes to A's directory, and whatever it writes for the winner lands on top.
    # No acceptance rule, no eligibility rule, no gate and no publication rule moves.
    a_dir = None
    if out_dir is not None:
        root = pathlib.Path(out_dir)
        a_dir = root / "attempt-A"
        a_dir.mkdir(parents=True, exist_ok=True)
        for f in sorted(root.iterdir()):
            if f.is_file():
                f.replace(a_dir / f.name)
        attempts[0] = _attempt_record("A", a, a_dir)

    # B. Same frozen upstream, no article, no package, its own artifact directory. The
    # gates it will meet are the ones A met, unmodified.
    b_dir = (root / "attempt-B") if out_dir is not None else None
    b = run_story_architecture_composition(
        provider, pack=pack, source_text=source_text, source_sha=source_sha,
        subject=subject, fact_check=fact_check, reader=reader, package=package,
        stop_after=stop_after, fact_check_fn=fact_check_fn, out_dir=b_dir,
        frozen=_frozen_upstream_of(a), compose_mode=COMPOSE_SAFE_RECOMPOSE)
    attempts.append(_attempt_record("B", b, b_dir))
    # The top level now describes the attempt the run's verdict came from, and says which
    # one that is. B is what run_composition_with_fallback returns, so B is what the
    # runner builds WRITER_OUTPUT, the decision and publication state from -- the file
    # and the decision can no longer disagree.
    if out_dir is not None:
        persist(out_dir, b)
    return decorate(b, True)
