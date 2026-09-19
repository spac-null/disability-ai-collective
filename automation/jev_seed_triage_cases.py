#!/usr/bin/env python3
"""jev_seed_triage_cases.py -- as-of-seed reconstruction for the seed triage benchmark.

EXPERIMENTAL. Read-only. Imports no production stage and changes no production
behaviour. It reconstructs, for historical candidates, only what was visible
BEFORE Research, and pairs that with the frozen later outcome so the outcome can
be used for evaluation and never as model input.

THE ONE RULE THIS MODULE EXISTS TO ENFORCE. A seed state may carry only fields
in ALLOWED_STATE_KEYS. Everything a later stage produced -- research verdict,
ledger, worth, composition, safety, publication, article prose, the fetched
source body -- is held in a separate outcome record that never reaches the
model. seed_state() is the only constructor, and it raises rather than pass a
key it does not recognise.

WHAT HISTORY ACTUALLY RETAINED. Raw pre-commissioning discovery pools were not
kept. What survives is:

  COHORT B  one record per distinct seed that entered the pipeline, rebuilt from
            SOURCE_SNAPSHOT.provenance (seed_id, seed title, url, source name)
            plus the run's own later artifacts for the outcome.
  COHORT A  the 4-candidate knowledge-first pools inside COMMISSION.json, where
            one candidate was chosen and three were not. Not raw discovery, and
            an unchosen candidate is not a failure.

STAGE SCHEMA AVAILABILITY IS NOT AN EDITORIAL OUTCOME. RESEARCH_PACK artifacts
begin 2026-08-29, WORTH_AND_CANDIDATE 2026-09-04, LEDGER 2026-09-07. A candidate
that ran before its gate's artifact existed is marked unevaluable for that gate
rather than counted as a failure of it.
"""
from __future__ import annotations

import ast
import collections
import glob
import hashlib
import json
import os
import random
import re
import urllib.parse

ENGINE_ROOT = os.environ.get(
    "JEV_SEED_TRIAGE_ENGINE_ROOT", "/srv/data/cripminds-new-engine-v1"
)

# Only these may ever reach the model.
ALLOWED_STATE_KEYS = (
    "title",
    "snippet",
    "source",
    "source_domain",
    "discovery_date",
    "source_language",
    "subject_country",
    "discovery_context",
)

# Anything post-seed. Used as a tripwire on assembled states.
FORBIDDEN_STATE_KEYS = (
    "worth_status",
    "worth_verdict",
    "research_status",
    "ledger_status",
    "publication_eligible",
    "engine_decision",
    "decision",
    "terminal_reason",
    "article",
    "article_md",
    "word_count",
    "source_text",
    "research_pack",
    "safety",
    "grounding",
    "fact_check",
    "reader",
    "final_title",
    "outcome",
    "evidence",
    "run_id",
    "seed_id",
    "path",
)

# First date on which each stage wrote an artifact at all.
STAGE_FIRST_DATE = {
    "research": "20260829",
    "worth": "20260904",
    "ledger": "20260907",
}

RESEARCH_PASS_VERDICTS = ("NARROW", "ARTICLE", "SHORT_ARTICLE")

MAX_TITLE_CHARS = 400
MAX_SNIPPET_CHARS = 900
MAX_STATE_BYTES = 4096


# ------------------------------------------------------------------ helpers


def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:  # noqa: BLE001 -- a missing or broken artifact is data
        return None


def _provenance(run_dir):
    payload = _read_json(os.path.join(run_dir, "SOURCE_SNAPSHOT.json"))
    if not isinstance(payload, dict):
        return {}
    prov = (payload.get("payload") or {}).get("provenance")
    if isinstance(prov, str):
        try:
            prov = ast.literal_eval(prov)
        except Exception:  # noqa: BLE001
            return {}
    return prov if isinstance(prov, dict) else {}


def run_date(run_dir):
    match = re.search(r"-(\d{8})T\d{6}Z", os.path.basename(run_dir))
    return match.group(1) if match else None


def _domain(url):
    if not url:
        return ""
    try:
        host = urllib.parse.urlparse(url).netloc.lower()
    except Exception:  # noqa: BLE001
        return ""
    return host[4:] if host.startswith("www.") else host


def stage_available(stage, date):
    first = STAGE_FIRST_DATE.get(stage)
    if not first or not date:
        return False
    return date >= first


# ------------------------------------------------------------- seed states


class StateError(ValueError):
    pass


def seed_state(fields):
    """The only way a state is built. Unknown or post-seed keys raise."""
    state = {}
    for key, value in fields.items():
        if key not in ALLOWED_STATE_KEYS:
            raise StateError("state key not allowed at seed time: %r" % key)
        if value in (None, "", [], {}):
            continue
        if not isinstance(value, str):
            raise StateError("state value for %r is not text: %r" % (key, value))
        text = " ".join(value.split())
        if key == "title":
            text = text[:MAX_TITLE_CHARS]
        elif key in ("snippet", "discovery_context"):
            text = text[:MAX_SNIPPET_CHARS]
        if text:
            state[key] = text
    if not state.get("title") and not state.get("snippet"):
        raise StateError("state carries neither title nor snippet")
    assert_no_leakage(state)
    encoded = len(json.dumps(state, sort_keys=True).encode("utf-8"))
    if encoded > MAX_STATE_BYTES:
        raise StateError("state too large (%d bytes); minimise it" % encoded)
    return state


def assert_no_leakage(state):
    for key in state:
        if key in FORBIDDEN_STATE_KEYS or key not in ALLOWED_STATE_KEYS:
            raise StateError("post-seed key in state: %r" % key)
    return True


def state_fingerprint(state):
    return hashlib.sha256(
        json.dumps(state, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:16]


# --------------------------------------------------------------- cohort B


def _run_outcome(run_dir):
    """Frozen later result of one run. Never enters a state."""
    date = run_date(run_dir)
    manifest = _read_json(os.path.join(run_dir, "MANIFEST.json")) or {}
    research = None
    pack = _read_json(os.path.join(run_dir, "RESEARCH_PACK.json"))
    if isinstance(pack, dict):
        research = ((pack.get("payload") or {}).get("sufficiency") or {}).get("verdict")
    worth = None
    worth_doc = _read_json(os.path.join(run_dir, "WORTH_AND_CANDIDATE.json"))
    if isinstance(worth_doc, dict):
        worth = (worth_doc.get("worth_gate") or {}).get("verdict")
    ledger_doc = _read_json(os.path.join(run_dir, "LEDGER.json"))
    ledger_facts = len(ledger_doc) if isinstance(ledger_doc, dict) else None
    composition = os.path.exists(os.path.join(run_dir, "COMPOSITION_RESULT.json"))
    article_final = os.path.exists(os.path.join(run_dir, "ARTICLE_FINAL.md"))
    return {
        "run_id": os.path.basename(run_dir),
        "date": date,
        "run_status": manifest.get("run_status"),
        "engine_decision": manifest.get("decision"),
        "research_verdict": research,
        "research_pass": research in RESEARCH_PASS_VERDICTS,
        "worth_verdict": worth,
        "worth_pass": bool(worth and str(worth).startswith("STRONG")),
        "ledger_facts": ledger_facts,
        "ledger_pass": bool(ledger_facts),
        "reached_composition": composition,
        "article_final_reached": article_final,
        "provider_failure": manifest.get("run_status") == "PROVIDER_FAILURE",
    }


def _terminal_stage(outcomes):
    if any(o["article_final_reached"] for o in outcomes):
        return "ARTICLE_FINAL"
    if any(o["reached_composition"] for o in outcomes):
        return "COMPOSITION"
    if any(o["worth_pass"] for o in outcomes):
        return "WORTH_PASS"
    if any(o["ledger_pass"] for o in outcomes):
        return "LEDGER"
    if any(o["research_pass"] for o in outcomes):
        return "RESEARCH_PASS"
    if any(o["provider_failure"] for o in outcomes):
        return "PROVIDER_FAILURE"
    return "RESEARCH_HOLD"


def build_cohort_b(root=None):
    """One record per distinct commissioned seed, earliest run first."""
    root = root or ENGINE_ROOT
    by_seed = collections.OrderedDict()
    for run_dir in sorted(glob.glob(os.path.join(root, "production-*"))):
        if not os.path.isdir(run_dir):
            continue
        prov = _provenance(run_dir)
        seed_id = prov.get("seed_id")
        title = prov.get("title") or ""
        if not seed_id or not title:
            continue
        record = by_seed.get(seed_id)
        if record is None:
            record = by_seed[seed_id] = {
                "seed_id": seed_id,
                "first_run": os.path.basename(run_dir),
                "date": run_date(run_dir),
                "title": title,
                "url": prov.get("url") or "",
                "source_name": prov.get("source_name") or "",
                "source_domain": _domain(prov.get("url") or ""),
                "runs": [],
            }
        record["runs"].append(_run_outcome(run_dir))

    cohort = []
    for seed_id, record in by_seed.items():
        outcomes = record["runs"]
        dates = [o["date"] for o in outcomes if o["date"]]
        record["outcome"] = {
            "worth_pass": any(o["worth_pass"] for o in outcomes),
            "research_pass": any(o["research_pass"] for o in outcomes),
            "ledger_pass": any(o["ledger_pass"] for o in outcomes),
            "reached_composition": any(o["reached_composition"] for o in outcomes),
            "article_final_reached": any(
                o["article_final_reached"] for o in outcomes
            ),
            "terminal_stage": _terminal_stage(outcomes),
            "runs": len(outcomes),
            "all_provider_failure": all(o["provider_failure"] for o in outcomes),
            "worth_evaluable": any(stage_available("worth", d) for d in dates),
            "research_evaluable": any(stage_available("research", d) for d in dates),
            "ledger_evaluable": any(stage_available("ledger", d) for d in dates),
        }
        record["state"] = seed_state(
            {
                "title": record["title"],
                "source": record["source_name"],
                "source_domain": record["source_domain"],
                "discovery_date": _pretty_date(record["date"]),
            }
        )
        record["state_fingerprint"] = state_fingerprint(record["state"])
        record["cohort"] = "B"
        record["case_id"] = "B:%s" % seed_id
        cohort.append(record)
    return cohort


def _pretty_date(compact):
    if not compact or len(compact) != 8:
        return ""
    return "%s-%s-%s" % (compact[:4], compact[4:6], compact[6:])


def worth_evaluable(cohort):
    """Candidates whose Worth result is a real editorial outcome."""
    return [
        record
        for record in cohort
        if record["outcome"]["worth_evaluable"]
        and not record["outcome"]["all_provider_failure"]
    ]


# --------------------------------------------------------------- cohort A


# Commissioning-desk reasoning about a candidate is not seed information.
COHORT_A_DROPPED_FIELDS = (
    "carrier",
    "tests_the_question",
    "access_deficit_self_check",
    "names_to_research",
    "search_queries",
    "diversity_prior",
    "diversity_prior_effects",
    "_commission_order",
)


def build_cohort_a(root=None):
    """Commissioning-desk candidate pools: chosen and not-chosen, no labels."""
    root = root or ENGINE_ROOT
    pools = []
    for path in sorted(glob.glob(os.path.join(root, "production-*/COMMISSION.json"))):
        doc = _read_json(path)
        if not isinstance(doc, dict):
            continue
        candidates = doc.get("candidates") or []
        if not candidates:
            continue
        run_dir = os.path.dirname(path)
        chosen_subject = ((doc.get("chosen") or {}).get("subject") or "")[:120]
        entries = []
        for index, candidate in enumerate(candidates):
            subject = candidate.get("subject") or ""
            if not subject:
                continue
            metadata = candidate.get("commissioning_metadata") or {}
            state = seed_state(
                {
                    "title": subject,
                    "discovery_context": candidate.get("why_now") or "",
                    "source_language": candidate.get("source_language")
                    or metadata.get("source_language")
                    or "",
                    "subject_country": candidate.get("country")
                    or metadata.get("subject_country")
                    or "",
                }
            )
            entries.append(
                {
                    "cohort": "A",
                    "case_id": "A:%s:%d" % (os.path.basename(run_dir), index),
                    "pool": os.path.basename(run_dir),
                    "date": run_date(run_dir),
                    "lane": doc.get("lane"),
                    "selected": subject[:120] == chosen_subject,
                    "source_language": candidate.get("source_language")
                    or metadata.get("source_language"),
                    "subject_country": candidate.get("country")
                    or metadata.get("subject_country"),
                    "world_region": candidate.get("world_region")
                    or metadata.get("subject_world_region"),
                    "state": state,
                    "state_fingerprint": state_fingerprint(state),
                }
            )
        if entries:
            pools.append({"pool": os.path.basename(run_dir), "candidates": entries})
    return pools


# ------------------------------------------------------- desk attempt order


def desk_days(root=None):
    """Real commissioning days, with the historical attempt order preserved."""
    root = root or ENGINE_ROOT
    days = []
    for path in sorted(glob.glob(os.path.join(root, "commissioning-*/COMMISSIONING_DAY.json"))):
        doc = _read_json(path)
        if not isinstance(doc, dict):
            continue
        attempts = []
        for attempt in doc.get("attempts") or []:
            if not attempt.get("seed_id"):
                continue
            attempts.append(
                {
                    "attempt": attempt.get("attempt"),
                    "seed_id": attempt.get("seed_id"),
                    "lane": attempt.get("lane"),
                    "source_language": attempt.get("source_language"),
                    "subject_country": attempt.get("subject_country"),
                    "research_status": attempt.get("research_status"),
                    "ledger_status": attempt.get("ledger_status"),
                    "worth_verdict": attempt.get("worth_verdict"),
                    "terminal_reason": attempt.get("terminal_reason"),
                    "worth_pass": attempt.get("worth_verdict") == "PASS",
                }
            )
        if attempts:
            days.append(
                {
                    "day": os.path.basename(os.path.dirname(path)),
                    "attempts": sorted(attempts, key=lambda a: a["attempt"] or 0),
                }
            )
    return days


def calendar_days(cohort, min_size=2, max_size=8):
    """Proxy days: calendar dates carrying several distinct seeds.

    These are NOT desk commissioning days. Before 2026-09-13 the pipeline had no
    multi-pitch desk, and dense dates are development batches. Historical order
    inside a proxy day is chronological run order.
    """
    grouped = collections.defaultdict(list)
    for record in cohort:
        grouped[record["date"]].append(record)
    days = []
    for date in sorted(grouped):
        members = sorted(grouped[date], key=lambda r: r["first_run"])
        if min_size <= len(members) <= max_size:
            days.append({"day": date, "members": members})
    return days


def simulated_groups(cohort, size=3, seed=20260919):
    """Deterministic simulated pitch groups. Labelled simulation, not history."""
    pool = sorted(cohort, key=lambda r: r["case_id"])
    rng = random.Random(seed)
    rng.shuffle(pool)
    return [
        {"group": index, "members": pool[index : index + size]}
        for index in range(0, len(pool) - size + 1, size)
    ]


# ------------------------------------------------------------ fixed scoring


POSITIVE_SIGNALS = (
    "concrete_carrier",
    "specific_event_or_change",
    "researchable_mechanism",
    "specific_tension_or_contradiction",
    "evidence_path_visible",
    "ordinary_world_question_present",
    "concrete_human_or_material_stakes",
)

NEGATIVE_SIGNALS = ("generic_commentary_risk",)

EXPLORATORY_NOUL = ("local_language_search_may_help",)

LANE_OPTIONS = ("KNOWLEDGE_FIRST", "ORDINARY_WORLD_COLLISION", "UNCLEAR")


def positive_mean(probabilities):
    values = [float(probabilities[name]) for name in POSITIVE_SIGNALS]
    return sum(values) / len(values)


def triage_score(probabilities):
    """Eight equally weighted components. Fixed before any result was seen."""
    values = [float(probabilities[name]) for name in POSITIVE_SIGNALS]
    values += [1.0 - float(probabilities[name]) for name in NEGATIVE_SIGNALS]
    return sum(values) / len(values)


# ------------------------------------------------------------------ metrics


def auc(scores, labels):
    """Mann-Whitney AUC with tie correction. None when one class is empty."""
    positives = [s for s, y in zip(scores, labels) if y]
    negatives = [s for s, y in zip(scores, labels) if not y]
    if not positives or not negatives:
        return None
    wins = 0.0
    for p in positives:
        for n in negatives:
            if p > n:
                wins += 1.0
            elif p == n:
                wins += 0.5
    return wins / (len(positives) * len(negatives))


def describe(values):
    if not values:
        return {"n": 0}
    ordered = sorted(values)
    middle = len(ordered) // 2
    median = (
        ordered[middle]
        if len(ordered) % 2
        else (ordered[middle - 1] + ordered[middle]) / 2.0
    )
    return {
        "n": len(ordered),
        "mean": sum(ordered) / len(ordered),
        "median": median,
        "min": ordered[0],
        "max": ordered[-1],
    }


def overlap_description(pass_values, fail_values):
    if not pass_values or not fail_values:
        return "one class empty"
    lo = max(min(pass_values), min(fail_values))
    hi = min(max(pass_values), max(fail_values))
    if lo > hi:
        return "disjoint ranges"
    inside_pass = sum(1 for v in pass_values if lo <= v <= hi)
    inside_fail = sum(1 for v in fail_values if lo <= v <= hi)
    return "shared band %.3f-%.3f holds %d/%d pass and %d/%d non-pass" % (
        lo,
        hi,
        inside_pass,
        len(pass_values),
        inside_fail,
        len(fail_values),
    )


def rank_metrics(groups):
    """groups: [[(score, worth_pass), ...], ...]. Only groups with >=1 pass."""
    top1 = top2 = 0
    first_ranks = []
    random_top1 = []
    considered = 0
    for members in groups:
        if not any(y for _, y in members):
            continue
        considered += 1
        ordered = sorted(members, key=lambda m: -m[0])
        labels = [y for _, y in ordered]
        if labels[0]:
            top1 += 1
        if any(labels[:2]):
            top2 += 1
        first_ranks.append(labels.index(True) + 1)
        positives = sum(1 for y in labels if y)
        random_top1.append(positives / float(len(labels)))
    return {
        "days": considered,
        "top1_hits": top1,
        "top1_rate": (top1 / considered) if considered else None,
        "top2_hits": top2,
        "top2_rate": (top2 / considered) if considered else None,
        "mean_rank_first_pass": (
            sum(first_ranks) / float(len(first_ranks)) if first_ranks else None
        ),
        "random_top1_rate": (
            sum(random_top1) / float(len(random_top1)) if random_top1 else None
        ),
        "random_mean_rank_first_pass": (
            sum(_random_mean_rank(len(m), sum(1 for _, y in m if y)) for m in groups
                if any(y for _, y in m)) / considered
            if considered
            else None
        ),
    }


def _random_mean_rank(total, positives):
    """Expected rank of the first positive under a uniformly random order."""
    if positives <= 0 or total <= 0:
        return None
    return (total + 1) / float(positives + 1)


def attempts_to_first_pass(ordered_labels):
    """1-based position of the first pass, or None when the order holds none."""
    for index, label in enumerate(ordered_labels):
        if label:
            return index + 1
    return None
