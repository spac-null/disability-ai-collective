# cripminds-calibration-runner

Persistent Trident service that polls `lab.cripminds.com` for claimable
calibration jobs and executes exactly the workflow version named by each
job (`calibration_runner.py`'s `JOB_HANDLERS`). No interactive Claude
session or open shell is required for it to run — it survives logout,
and systemd restarts it on failure or reboot.

See `../workflows/analyze-human-round-v1.md` and
`../workflows/prepare-next-round-v1.md` for what each job type actually
computes. This README is deployment/ops only.

## What it needs, and what it deliberately does not have

- `CALIBRATION_RUNNER_TOKEN` — a narrow credential (see
  `reader-lab-worker/src/index.js`'s `requireCalibrationRunner`) that can
  only claim/heartbeat/complete/fail a calibration job. It cannot create
  or revoke a reviewer, publish a Reader Lab round, alter a response or
  export, or reach any `/admin` route. It is a *different* secret from
  `ADMIN_TOKEN`/`EXPORT_TOKEN` — never reuse either of those here.
- The existing local CLIProxyAPI route (`127.0.0.1:8317`, already used
  by `automation/cj2_b2_probe*.py` on this same host) — only for the
  optional, non-authoritative `notes` field in `analyze_human_round`
  results. If CLIProxyAPI is down, jobs still complete correctly;
  `notes` is simply `null`.
- Outbound HTTPS to `lab.cripminds.com`. **No inbound port, no public
  exposure** — this service only ever makes outbound polling requests;
  Cloudflare has no way to reach Trident directly, by design.

## First-time install

```bash
# 1. Secret file (chmod 600, matches every other bot's secrets convention)
sudo mkdir -p /srv/secrets/cripminds-calibration
sudo tee /srv/secrets/cripminds-calibration/cripminds-calibration-runner.env <<'EOF'
CALIBRATION_RUNNER_TOKEN=<the real production value — from wrangler secret put, never pasted into chat/logs>
CALIBRATION_BASE_URL=https://lab.cripminds.com
CALIBRATION_RUNNER_ID=trident-1
CALIBRATION_POLL_INTERVAL=30
CLIPROXY_URL=http://127.0.0.1:8317/v1
CLIPROXY_MODEL=openrouter/claude-sonnet-4.6
EOF
sudo chown jascha:jascha /srv/secrets/cripminds-calibration/cripminds-calibration-runner.env
sudo chmod 600 /srv/secrets/cripminds-calibration/cripminds-calibration-runner.env

# 2. Wrapper script (git-pull-then-run, matches cripminds-daily.sh's own convention)
cp calibration/runner/cripminds-calibration-runner.sh /srv/scripts/ops/cripminds-calibration-runner.sh
chmod +x /srv/scripts/ops/cripminds-calibration-runner.sh

# 3. systemd unit
sudo cp calibration/runner/cripminds-calibration-runner.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now cripminds-calibration-runner

# 4. Verify
systemctl status cripminds-calibration-runner
journalctl -u cripminds-calibration-runner -f
```

## Health check

```bash
systemctl is-active cripminds-calibration-runner   # should print "active"
journalctl -u cripminds-calibration-runner -n 20   # should show periodic
                                                     # poll activity, no
                                                     # auth/connection errors
```

A healthy runner logs nothing when there's no pending job (deliberately
quiet — no need to log every empty poll) and logs `claimed job <id>
(<job_type>)` whenever it picks one up.

## Updating the runner

The checkout is pinned to an exact commit, not a moving branch — the
wrapper script reads
`/srv/secrets/cripminds-calibration/deployed-commit-sha.txt` and
`git checkout --detach`s exactly that SHA on every start, refusing to
start if the file is missing content or the commit can't be resolved. A
normal update is therefore:

```bash
echo <new-commit-sha> > /srv/secrets/cripminds-calibration/deployed-commit-sha.txt
sudo systemctl restart cripminds-calibration-runner
```

Never edit the pin file to track `main` again — a moving pin defeats the
whole point (Trident running code nobody deliberately deployed). If the
pin file doesn't exist yet at all (a fresh install, before any commit has
ever been pinned), the wrapper falls back to `git pull origin main` and
logs a warning — pin a real commit as soon as one exists rather than
relying on that fallback.

## What this service must NEVER be given

- `ADMIN_TOKEN` or `EXPORT_TOKEN` — no capability it has requires either.
- Any Cloudflare API token — this service only talks to
  `lab.cripminds.com`'s own `/ops/calibration/jobs/*` routes over plain
  HTTPS, never the Cloudflare control-plane API.
- Write access outside `/srv/data/hermes/workspace/disability-ai-collective`
  — `ProtectSystem=strict` + explicit `ReadWritePaths` in the systemd
  unit enforce this at the OS level, not just by convention.

## Rotating the token

```bash
# On the Worker side:
cd reader-lab-worker && npx wrangler secret put CALIBRATION_RUNNER_TOKEN
# On Trident:
sudo nano /srv/secrets/cripminds-calibration/cripminds-calibration-runner.env  # update the value
sudo systemctl restart cripminds-calibration-runner
```
