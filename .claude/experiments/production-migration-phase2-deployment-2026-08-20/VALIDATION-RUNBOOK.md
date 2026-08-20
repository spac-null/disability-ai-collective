# Validation Runbook — collecting P2-01…P2-03

Mechanical steps only. **No shadow execution, no model call, no quality inspection.**

## After each daily run (2026-08-21, -22, -23)

### 1. List new bundles

```bash
ssh jascha@trident.tail630536.ts.net \
  'ls -1t /srv/data/cripminds-shadow-capture/ | grep -v crontab.backup | head -5'
```

Bundle ids sort chronologically (`YYYYMMDDTHHMMSSZ-<hex>`).

### 2. Pull the bundle to the research machine

```bash
mkdir -p ~/code/disability-collective-ai/.claude/experiments/production-migration-phase2-deployment-2026-08-20/bundles
rsync -a --info=progress2 \
  jascha@trident.tail630536.ts.net:/srv/data/cripminds-shadow-capture/<RUN_ID> \
  ~/code/disability-collective-ai/.claude/experiments/production-migration-phase2-deployment-2026-08-20/bundles/
```

`rsync` of a capture bundle is safe — these are append-only plain files outside any repo or
database. (The standing rule against bare-rsyncing directories that may hold gitignored
state does not apply here: this root contains no DB and no repo state.)

### 3. Validate deterministically

```bash
cd .../production-migration-phase2-prep-2026-08-20/harness
python3 validate_bundle.py ../../production-migration-phase2-deployment-2026-08-20/bundles/<RUN_ID> --index P2-0N
```

Exit **0** = VALID → assign the next chronological index and paste the emitted JSON row into
`PHASE2-SAMPLE-MANIFEST.md`.
Exit **1** = `CAPTURE_INVALID` → record it in the invalid table with the reason and take the
next chronological run.

Eleven checks run: bundle complete · atomic-completion marker · raw source persisted ·
normalized source persisted · evidence packet persisted · writer-visible evidence persisted ·
raw writer output persisted · rewrite output available · disposition available · hashes
verify · secrets scan clean.

### 4. Do NOT

- run Discovery, Article Form, Writer or Writer Grounding on the captured source
- use local Claude or OpenRouter on it
- compare prose
- read the three cases and adjust the architecture
- exclude a run because it was blocked, short, odd, or unflattering

## After P2-03 validates

### 5. Disable capture

```bash
ssh jascha@trident.tail630536.ts.net \
  "crontab -l | sed 's#^0 9 \* \* \* SHADOW_CAPTURE=1 /srv/scripts/ops/cripminds-daily.sh article#0 9 * * * /srv/scripts/ops/cripminds-daily.sh article#' | crontab -"
```

Or restore the backup wholesale:

```bash
ssh jascha@trident.tail630536.ts.net \
  'crontab /srv/data/cripminds-shadow-capture/crontab.backup-before-capture-enable'
```

Verify: `crontab -l | grep -c SHADOW_CAPTURE` → **0**.

### 6. Confirm production continues normally with capture off

```bash
ssh jascha@trident.tail630536.ts.net \
  'cd /srv/data/hermes/workspace/disability-ai-collective && python3 automation/snapshot_test.py --check'
```

**Leave the capture code in place.** It stays dormant and OFF for rollback and
reproducibility; do not remove it yet.

### 7. Freeze

Commit the three bundles and the completed manifest as evidence. Then **stop** — live-vs-shadow
execution is a separate task.

## If something goes wrong

| Symptom | Action |
|---|---|
| No bundle appears after a run | Check `SHADOW_CAPTURE` is still on the cron line and that the run actually executed (`automation.log`) |
| A bundle contains `REFUSED_POSSIBLE_SECRET` | **Stop and report.** It means an upstream bug is putting credential-shaped text into a source packet — a real finding, investigate before continuing |
| `snapshot_test` drifts | Roll back: revert `ad7b8c7 445fbbc` on Trident |
| Capture root filling | 18G free at deploy; a bundle is a few hundred KB. Investigate if growth is disproportionate |
