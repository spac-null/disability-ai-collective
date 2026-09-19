"""
subjects.py -- select and FREEZE the pilot's subjects from retained production evidence.

Section 10. A subject qualifies only if the retained run carries every input the
comparison needs, already validated by the run that produced it:

    RESEARCH_PACK.json     the frozen source set   (sources, text, sha256, url)
    LEDGER.json            the frozen facts
    ARCHITECTURE.json      the original plan       -- must validate against the ledger
    COMPOSITION_RESULT.json  the run's own outcome

AND the architecture must still validate against the ledger under CURRENT code. A run
whose architecture no longer validates cannot give Experiment A a legitimate frozen plan,
so it is EXCLUDED and the exclusion is reported rather than quietly repaired.

WHAT IS DELIBERATELY WITHHELD FROM GENERATION WORKERS (section 10). The frozen subject
carries sources, ledger and architecture. It does NOT carry -- and `writer_inputs()` will
not return -- the historical final prose, the historical repairs, the gate findings, the
reason codes or any owner label. Those live in `evaluation_only` on the manifest, are
written to a separate file, and are read by the analysis, never by a model worker.

HEAVILY STUDIED CASES ARE EXCLUDED AS EVALUATION SUBJECTS, per sections 9 and 10: the
14 September Italian gloss, the 16 September Cem detector false positive, the
17 September archive/weather conflations and the SFMOMA owner-repair lineage. They remain
available as regression evidence; they are not untouched validation.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
AUTOMATION = HERE.parent
if str(AUTOMATION) not in sys.path:
    sys.path.insert(0, str(AUTOMATION))

from new_engine_v1 import composition as CP                        # noqa: E402

EVIDENCE_ROOT = pathlib.Path("/srv/data/cripminds-new-engine-v1")

REQUIRED = ("RESEARCH_PACK.json", "LEDGER.json", "ARCHITECTURE.json",
            "COMPOSITION_RESULT.json")

# Section 9/10. Run-id substrings of the heavily studied cases. Regression material only.
HEAVILY_STUDIED = {
    "production-20260914T070213Z-d20b3807": "14 September Italian gloss",
    "production-20260916T070723Z-5a4e7891": "16 September Cem detector false positive",
    "production-20260917T070213Z-67554ae5": "17 September archive/weather conflations",
    "production-20260911T111356Z-669582be": "SFMOMA owner-repair lineage",
    "production-20260913T083824Z-f83f4b8a": "SFMOMA owner-repair lineage",
}

# Heuristic source-language detection. The research pack carries NO language field on a
# source record -- verified by absence across all 54 candidate runs -- so language has to
# be read off the text. This is a selection aid for the multilingual requirement and it is
# reported as a heuristic, never as a metadata fact the pack asserts.
_STOPWORDS = {
    "it": {"che", "della", "questo", "perche", "sono", "gli", "nel", "alla", "delle"},
    "nl": {"het", "een", "van", "niet", "zijn", "voor", "maar", "worden"},
    "de": {"und", "der", "die", "nicht", "wird", "auch", "eine", "werden"},
    "fr": {"les", "des", "dans", "pour", "est", "une", "que", "sur"},
    "es": {"los", "las", "para", "con", "una", "que", "por", "del"},
    "tr": {"bir", "ile", "olan", "daha", "icin", "gibi", "ancak", "kadar"},
    "pt": {"uma", "para", "com", "dos", "nao", "que", "por"},
}


def sha256_text(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()


def load_artifact(path: pathlib.Path):
    """Unwrap the {stage, payload, content_hash, ...} envelope the engine persists."""
    d = json.loads(path.read_text())
    if isinstance(d, dict) and "payload" in d and "stage" in d:
        return d["payload"]
    return d


def detect_language(text: str) -> str:
    t = (text or "")[:6000].lower()
    if sum(1 for ch in t if ord(ch) > 0x2000 or 0x0370 <= ord(ch) <= 0x1cff) > 80:
        return "non-latin"
    words = set(re.findall(r"[a-z]{3,}", t))
    best, score = "en", 0
    for lg, sw in _STOPWORDS.items():
        n = len(words & sw)
        if n > score:
            best, score = lg, n
    return best if score >= 3 else "en"


def scan(evidence_root=EVIDENCE_ROOT) -> list:
    """Every retained run that carries the four required artifacts, with the facts a
    selection needs and no model call."""
    rows = []
    for run in sorted(pathlib.Path(evidence_root).iterdir()):
        if not run.is_dir() or not all((run / n).exists() for n in REQUIRED):
            continue
        try:
            cr = load_artifact(run / "COMPOSITION_RESULT.json")
            pack = load_artifact(run / "RESEARCH_PACK.json")
            led = load_artifact(run / "LEDGER.json")
            arch = load_artifact(run / "ARCHITECTURE.json")
        except Exception as exc:                                   # noqa: BLE001
            rows.append({"run": run.name, "excluded": "unreadable artifact: %s" % exc})
            continue
        ledger = led.get("ledger") if isinstance(led.get("ledger"), (dict, list)) else led
        architecture = arch.get("architecture", arch)
        sources = pack.get("sources") or []

        # THE PLAN MUST STILL VALIDATE. Production's own checker, on current code.
        try:
            arch_errors = CP.check_architecture(architecture, ledger)
        except Exception as exc:                                   # noqa: BLE001
            arch_errors = ["check_architecture raised: %s" % exc]

        langs = [detect_language(s.get("text") or "")
                 for s in sources if isinstance(s, dict)]
        rows.append({
            "run": run.name,
            "subject": cr.get("subject") or pack.get("subject") or "",
            "historical_status": cr.get("status"),
            "historical_failure_stage": cr.get("failure_stage"),
            "sources": len(sources),
            "source_chars": sum(len(s.get("text") or "")
                                for s in sources if isinstance(s, dict)),
            "facts": len(ledger) if isinstance(ledger, (dict, list)) else 0,
            "beats": len(architecture.get("beats") or []),
            "use_facts": len(architecture.get("use_facts") or []),
            "languages": sorted(set(langs)),
            "multilingual": bool(set(langs) - {"en"}),
            "architecture_validates": not arch_errors,
            "architecture_errors": arch_errors[:4],
            "had_article": bool(cr.get("article_text")),
            "heavily_studied": HEAVILY_STUDIED.get(run.name),
        })
    return rows


def eligible(rows: list) -> list:
    """Section 10 eligibility, each rejection carrying its own reason."""
    out = []
    for r in rows:
        if r.get("excluded"):
            continue
        why = None
        if r.get("heavily_studied"):
            why = "heavily studied case (%s) -- regression material, not untouched " \
                  "validation" % r["heavily_studied"]
        elif not r["architecture_validates"]:
            why = "the retained architecture does not validate against its ledger " \
                  "under current code"
        elif not r["had_article"]:
            why = "the run produced no article, so there is no comparable historical " \
                  "narrative structure"
        elif r["sources"] < 3:
            why = "fewer than three retained sources"
        r = dict(r, ineligible_reason=why, eligible=why is None)
        out.append(r)
    return out


# THE EVIDENCE-HIERARCHY CONTRACT POSTDATES MOST RETAINED RUNS, and that is contract
# drift rather than a defective plan. `EVIDENCE_HIERARCHY` -- evidence_roles,
# primary_carrier, per-beat beat_function -- landed in e155c35 on 2026-09-11 ("feat:
# Architecture must declare an evidence hierarchy, not just a selection"). Every run
# frozen before that date validates cleanly on every OTHER rule and fails only on fields
# its own contract version never asked the architect to emit. Measured: of 46 retained
# architectures that do not validate under current code, 43 fail ONLY on
# EVIDENCE_HIERARCHY, and the 3 that fail on anything else are exactly the three runs
# whose own production result was an ARCHITECTURE hold.
#
# Excluding all 46 would throw away the pilot's entire pool to enforce a rule that did
# not exist when the plans were written. Excluding the 3 keeps the rule that did.
EVIDENCE_HIERARCHY_PREFIX = "EVIDENCE_HIERARCHY"
EVIDENCE_HIERARCHY_COMMIT = "e155c35 (2026-09-11)"


def plan_contract_of(errors: list) -> str:
    """Which architecture contract a retained plan was written against."""
    if not errors:
        return "CURRENT"
    if all(str(e).startswith(EVIDENCE_HIERARCHY_PREFIX) for e in errors):
        return "PRE_EVIDENCE_HIERARCHY"
    return "INVALID"


def eligible_v2(rows: list) -> list:
    """Section 10 eligibility, with contract drift separated from plan defects."""
    out = []
    for r in rows:
        if r.get("excluded"):
            continue
        contract = plan_contract_of(r.get("architecture_errors") or [])
        why = None
        if r.get("heavily_studied"):
            why = "heavily studied case (%s) -- regression material, not untouched " \
                  "validation" % r["heavily_studied"]
        elif contract == "INVALID":
            why = "the retained plan fails a rule that is not evidence-hierarchy drift " \
                  "(%s)" % "; ".join(str(e)[:70] for e in r["architecture_errors"][:2])
        elif not r["had_article"]:
            why = "the run produced no article, so there is no comparable historical " \
                  "narrative structure"
        elif r["sources"] < 3:
            why = "fewer than three retained sources"
        out.append(dict(r, plan_contract=contract, ineligible_reason=why,
                        eligible=why is None))
    return out


def freeze_subject(run_name: str, *, split: str, evidence_root=EVIDENCE_ROOT) -> dict:
    """The frozen manifest for one subject.

    `generation_inputs` is everything a model worker may see. `evaluation_only` is
    everything it may not. They are separate keys so that handing the wrong one to a
    worker has to be a deliberate act rather than an oversight.
    """
    run = pathlib.Path(evidence_root) / run_name
    pack = load_artifact(run / "RESEARCH_PACK.json")
    led = load_artifact(run / "LEDGER.json")
    arch = load_artifact(run / "ARCHITECTURE.json")
    cr = load_artifact(run / "COMPOSITION_RESULT.json")

    ledger = led.get("ledger") if isinstance(led.get("ledger"), (dict, list)) else led
    architecture = arch.get("architecture", arch)
    sources = [s for s in (pack.get("sources") or []) if isinstance(s, dict)]

    source_set = [{
        "source_id": s.get("source_id"),
        "title": s.get("title"),
        "publisher": s.get("publisher"),
        "url": s.get("url"),
        "role": s.get("role"),
        "sha256": s.get("sha256"),
        "chars": len(s.get("text") or ""),
        "detected_language": detect_language(s.get("text") or ""),
    } for s in sources]

    source_set_hash = sha256_text("|".join(sorted(
        "%s:%s" % (s["source_id"], s["sha256"]) for s in source_set)))

    return {
        "subject_id": run_name,
        "split": split,
        "subject": cr.get("subject") or pack.get("subject") or "",
        "source_set_hash": source_set_hash,
        "ledger_sha256": sha256_text(json.dumps(ledger, sort_keys=True)),
        "ledger_facts": len(ledger) if isinstance(ledger, (dict, list)) else 0,
        "plan_sha256": sha256_text(json.dumps(architecture, sort_keys=True)),
        "source_set": source_set,
        "languages": sorted({s["detected_language"] for s in source_set}),
        "generation_inputs": {
            "ledger": ledger,
            "architecture": architecture,
            "sources": [{"source_id": s.get("source_id"), "title": s.get("title"),
                         "publisher": s.get("publisher"), "url": s.get("url"),
                         "role": s.get("role"), "sha256": s.get("sha256"),
                         "text": s.get("text") or ""} for s in sources],
            "subject": cr.get("subject") or "",
        },
        # NOT FOR ANY MODEL WORKER. Section 10: historical prose, repairs, gate findings
        # and owner labels are unavailable to generation, and are not answers for judges.
        "evaluation_only": {
            "historical_status": cr.get("status"),
            "historical_failure_stage": cr.get("failure_stage"),
            "historical_reason_code": cr.get("reason_code"),
            "historical_words": cr.get("words"),
            "historical_article_sha256": cr.get("article_sha256"),
            "historical_advisories": cr.get("advisories") or [],
        },
    }
