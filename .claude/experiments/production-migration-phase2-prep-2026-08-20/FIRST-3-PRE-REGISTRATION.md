# Phase-2 Comparison Set — Pre-Registration

**Registered 2026-08-20, BEFORE capture is deployed and BEFORE any run is observed.**

## The rule

> **PHASE-2 COMPARISON SET = the FIRST 3 COMPLETE ELIGIBLE ARTICLE RUNS AFTER CAPTURE
> ENABLEMENT.**

Chronological order by capture run id (`YYYYMMDDTHHMMSSZ-…`, sortable). No cherry-picking.

## Eligibility — the complete list

A run is eligible if and only if:

1. it is a normal article pipeline run (the 09:00 `cripminds-daily.sh article` cron, or an
   equivalent manual invocation of the same path);
2. source/evidence capture is complete — the bundle is sealed with `COMPLETE`, carries all
   required artifacts, and every manifest hash matches;
3. the legacy pipeline produced enough lineage for comparison — at minimum a raw writer
   output and a disposition.

## Explicitly NOT grounds for exclusion

- topic or subject matter
- article quality, length, or register
- publication state — draft, published, or promoted
- `fact_check_status: blocked`
- `_should_block` firing, or any `pipeline_degraded` stage
- which architecture appears likely to look better
- whether the source was truncated, or fell back to an RSS summary

**A blocked production article is a valid comparison case.** Production is currently blocking
4 of 7 drafts; excluding blocked runs would select for exactly the cases where the legacy
system is least representative of itself.

## Invalid captures

If a run's bundle is incomplete or corrupt, record it as **`CAPTURE_INVALID`** with the
reason, and take the **next chronological complete run**. An invalid capture is not a
comparison result and does not count toward the three.

`CAPTURE_INVALID` is determined mechanically by `harness/compare.py`, not by judgement:
unsealed bundle, missing required artifact, or any manifest hash mismatch.

## Recording

For each of the three, record: capture run id, timestamp, source URL and origin, slug,
`source_hash`, `evidence_packet_hash`, legacy disposition, degraded stages, and — once a
shadow lineage exists on the same frozen evidence — the shadow decision and the harness
report.

The register below is to be filled in strictly in the order runs occur.

| # | Capture run id | Date | Slug | Legacy disposition | Bundle status | Shadow decision |
|---|---|---|---|---|---|---|
| 1 | *(pending enablement)* | | | | | |
| 2 | *(pending enablement)* | | | | | |
| 3 | *(pending enablement)* | | | | | |

| Rejected as CAPTURE_INVALID | Run id | Reason |
|---|---|---|
| *(none yet)* | | |

## What this pre-registration prevents

Choosing the sample after seeing the outcomes. The set is defined by chronology and
mechanical eligibility alone, both fixed before a single run is observed.
