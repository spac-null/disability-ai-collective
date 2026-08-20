# Batch 1 — Preserved State (before containment fix)

Recorded 2026-08-20, immediately before the `_config.yml` / `robots.txt`
containment commit. Source files are **not** deleted or modified by this
batch — only the Jekyll build inclusion changes. This file plus
`BATCH1-PRESERVED-STATE-sha256.txt` and the two `.before` copies are the
preservation record required by the containment directive.

## Files preserved as-is (SHA-256 in `BATCH1-PRESERVED-STATE-sha256.txt`)

20 files across `calibration/` (18) and `reader-lab/` (2 tracked +
`RL-2026-003.json` untracked at time of this batch — likely concurrent
Phase-2 capture activity, left untouched). Note: 4 of the 20 were untracked
in git at the time of this batch (`calibration/candidates/RL-2026-003-*`,
`calibration/research-context/RL-2026-003.json`,
`reader-lab/rounds/drafts/RL-2026-003.json`) — this batch does not add,
remove, or commit those data files; it only changes what Jekyll builds.

## Config/robots snapshots

- `BATCH1-PRESERVED-_config.yml.before` — full `_config.yml` prior to adding
  the `calibration/`/`reader-lab/` exclusion.
- `BATCH1-PRESERVED-robots.txt.before` — full `robots.txt` prior to adding
  the `Disallow` lines.

## Known public URLs (live-confirmed 2026-08-20, immediately before fix)

Calibration (from the original audit, `inventory.json` → `unintended_exposure_surface`):
- `https://cripminds.com/calibration/research-context/RL-2026-002.json` — HTTP 200
- `https://cripminds.com/calibration/workflows/analyze-human-round-v1/` — HTTP 200
- sitemap.xml listed: `calibration/workflows/analyze-human-round-v1/`, `-v2/`,
  `prepare-calibration-candidates-v1/`, `prepare-next-round-v1/`,
  `calibration/candidates/`, `calibration/runner/`
- `https://cripminds.com/calibration/` (bare index) — HTTP 404 (no directory listing;
  individual file paths are directly fetchable)

Reader Lab — **correction to the original audit's T-2 finding**: T-2 described
`reader-lab/` as "currently empty/unexposed... latent." That was **not
accurate at the time of this batch**: `reader-lab/rounds/drafts/RL-2026-001.json`
and `RL-2026-002.json` are tracked in git (commit `ffe44fb`, "Reader Lab
control plane and calibration orchestrator") and were **live-confirmed HTTP
200** immediately before this fix:
- `https://cripminds.com/reader-lab/rounds/drafts/RL-2026-001.json` — HTTP 200
- `https://cripminds.com/reader-lab/` (bare index) — HTTP 404 (same pattern as calibration/)

This means Finding T-1's severity class (live, real, sitemap-reinforced
exposure) applies to `reader-lab/` too, not just the preventive/latent framing
in T-2. Treated as equally in-scope for this containment batch regardless.

## Secret scan result (containment step 6)

Scanned all 20 files (patterns: api_key, secret, token, password, passwd,
authorization, bearer, cookie, PEM headers, ssh-rsa, AWS AKIA, Slack xox*,
GitHub ghp_, JWT-shaped strings, quoted `"token": "..."` /
`"secret": "..."` / `"api_key": "..."` / `"password": "..."` with an 8+ char
value).

**Result: NONE FOUND.** All hits were token/secret **names** and file-path
references to where real secrets live outside the repo
(`/srv/secrets/cripminds-calibration/*.env`, `CALIBRATION_RUNNER_TOKEN` read
via `os.environ.get(..., "")` at runtime, never a literal value), plus one
README describing the rotation procedure in the abstract. No literal
credential value, API key, password, or auth header value was found in any
scanned file. This is standard secrets-out-of-repo practice, not an incident.
