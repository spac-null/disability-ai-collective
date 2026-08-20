# Phase-2 Capture — Deployment and Sample Collection

**Deployed and enabled 2026-08-20. Sample collection in progress: 0 of 3 runs captured.**

| File | Contents |
|---|---|
| `STATUS.md` | What completed, what did not, and why |
| `DEPLOYMENT-RECORD.md` | Correction, verification, deployment, safety checks, capture root, enablement, the deferred-push consequence, rollback |
| `PHASE2-SAMPLE-MANIFEST.md` | The frozen sample rule and the manifest table to fill |
| `VALIDATION-RUNBOOK.md` | Exact mechanical steps for the three remaining runs |
| `bundles/` | Captured bundles (empty until 2026-08-21) |

Tooling lives in the sibling prep root:
`../production-migration-phase2-prep-2026-08-20/harness/` — `validate_bundle.py` (per-bundle
validation), `compare.py` (live-vs-shadow, **not** run yet).

Deployable code lives on branch `production-observability-2026-08-20` in
`../../../disability-collective-ai-production-observability`, commits `20a7e3a` + `8c4b4a5`,
deployed to Trident as `445fbbc` + `ad7b8c7`.

## One-line summary

The legacy pipeline now writes a complete, hash-verified evidence bundle for each article run
— including the four distinct source representations and the otherwise-ephemeral raw writer
output — with no change to what production decides, and the next three runs constitute the
pre-registered comparison sample.
