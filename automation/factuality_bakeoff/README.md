# Specialist factuality / relation checker bake-off

Offline component evaluation. **No production authority.** Nothing here runs in the
pipeline, gates publication, or is wired into Safety, Grounding, Materiality, Writer,
Architecture or cron.

Question: can an existing specialist factuality system improve Crip Minds' ability to
tell a genuinely unsupported claim or relationship from a supported one, an under-cited
one, an absent-but-not-contradicted one, and a legitimate editorial interpretation —
without becoming another mierenneuker gate?

Answer, on this evidence: **no. BEST SPECIALIST: NONE.** See
`analysis/DECISION.md` in the results root.

## Where things live

Code and tests are in this directory. Live results, model weights and corpora are
**outside git**, under:

    /srv/data/cripminds-new-engine-v1/experiments/factuality-bakeoff/

    MANIFEST.json HARDWARE.json LICENSES.json
    gold/CRIP_MINDS_GOLD.json      32 trusted claim/evidence cases
    systems/                       per-system scores, defect audit, baseline scan
    external/FRANK_*.json          external sanity
    analysis/METRICS.json ERRORS.md DECISION.md SPAN_METRICS.json

## Modules

| file | what it does |
|---|---|
| `cm_evidence.py` | loads frozen sources/facts from a retained run; representation normalization with a transform log |
| `cm_baseline.py` | current production `validate_turn_support`, imported unmodified, run offline read-only |
| `build_gold.py` | builds the trusted set; every label carries its authority and adjudication note |
| `run_entailment.py` | FactCG / MiniCheck adapters + README wiring checks |
| `run_lettuce.py` | LettuceDetect span adapter |
| `factcg_audit.py`, `factcg_defect.py` | the FactCG claim-truncation defect: blast radius and a declared workaround variant |
| `run_frank.py` | FRANK external sanity, published split respected |
| `compute_metrics.py`, `write_analysis.py`, `write_metadata.py` | metrics, error table, decision, manifest |
| `test_bakeoff.py` | 37 deterministic offline tests |
| `adjudicate.py`, `batch_adj.py`, `select_supported.py`, `dump_*.py`, `census_support.py` | candidate discovery and hand-adjudication aids |

## Rules the harness enforces

- **"Not in the supplied evidence" is never "false in the world."** Unsupported labels are
  only assigned where absence was checked over the *complete* frozen evidence.
- **Label authority** is DIRECT_SOURCE, POSTMORTEM_CONFIRMED or OWNER_CONFIRMED only.
  Prior model verdicts — grounding classifications, the shadow classifier, validator
  refusals, pilot reviewer objections — were used to *find* candidates, never to label
  them. Several did not survive rechecking.
- **Normalization is representation-only.** HTML entities, Unicode NFC, quotes, dashes and
  whitespace; never word removal, negation removal, number merging or reordering. Tested.
- **CITED_BASIS and COMPLETE_FROZEN_EVIDENCE are scored and reported apart**, never combined.
- **Thresholds are frozen before scoring**: published default 0.5, plus one global
  threshold chosen on FRANK validation only.
- **At most 2 cases per article**, so no single article or failure type can dominate.

## Running the tests

    python3 -W ignore automation/factuality_bakeoff/test_bakeoff.py

No network, no model, no GPU.

## Reproducing the scoring

Three isolated environments live outside the repo (FactCG pins `torch==2.2.1`,
LettuceDetect requires `torch>=2.6`, so they cannot share one). Checkpoints and
revisions are pinned in `MANIFEST.json`; licences, including one inconsistency in the
FactCG repository, are in `LICENSES.json`.
