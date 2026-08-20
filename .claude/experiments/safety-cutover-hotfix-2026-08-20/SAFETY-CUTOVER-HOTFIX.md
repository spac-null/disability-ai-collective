# Safety-Cutover Compatibility — Investigation and Decision

**Outcome: NO backfill. NO code hotfix. NO safety requirement weakened.**
The two at-risk drafts will archive unpublished, which is the correct result.

Read-only on production except for one new evidence file in the capture root (the selector
observation anchor). Phase-2 capture remained enabled throughout.

## Pre-hotfix freeze

| | |
|---|---|
| Trident HEAD | `ad7b8c7f1dd8dc84c48ed1a892169dca41a6bbaa` |
| Tracked modifications | 0 |
| `publish_best.py` sha256 | `1dbc4fac8179cf27bfe0b69b5f4a53696f70f989c36da4b44106f24b2f30ca76` |
| `generate.py` (stamper) sha256 | `21b0111baaae593f307e164fd97599874fe525b42db1acdaf600cf3771b12099` |

All seven draft hashes and front matter recorded in `PRE-HOTFIX-FREEZE.txt`. Nothing was
mutated.

## The exact safety-stamp predicate

From `generate.py::_maybe_stamp_publication_safety_version`, called once at line 1415,
immediately after `validate_article`:

```
stamp iff:
      should_block is falsy
  AND re.search(r"^fact_check_status:\s*verified\s*$", <file re-read from disk>, MULTILINE)
  AND no existing ^publication_safety_version:      # idempotent, never overwrites
```

where, from `_compute_should_block(self._degraded_stages)`:

```
should_block =    "fable_brief"                  in stages
               or "gate_llm"                     in stages
               or "persona_biography_unresolved"  in stages
               or len(stages) >= 2
```

**Inputs:** in-memory `self._degraded_stages` accumulated across the run, plus the article
file's own `fact_check_status` re-read from disk (deliberately, because three later call
sites can still set it to `blocked`).

**No LLM call. No network.** It is pure file I/O over run-local state.

## Can that predicate be reconstructed for an existing draft?

`_degraded_stages` is persisted to front matter as `pipeline_degraded: [...]` by
`publish.py::create_article_file` — but **only when non-empty**, and the field itself was
introduced 2026-08-10 (`e4922e6`), before both candidate drafts. So for a draft written after
that date, absence of `pipeline_degraded` does mean the list was empty **at the moment the
file was written** (line 1326, after the gate at 1302 — so `fable_brief`, `gate_llm` and
`editorial_revision` would all have been captured).

That is necessary but not sufficient, and here it fails on one specific term.

### The blocking term: `persona_biography_unresolved`

That stage was introduced 2026-08-16 in `89cd082` / `169e8ff`. **Trident's own reflog settles
when it arrived:**

```
394a02e HEAD@{2026-08-16 09:09:00}: commit: Add new article: 2026-08-16-sniff-it-out-...
169e8ff HEAD@{2026-08-16 11:20:38}: pull origin main: Fast-forward
```

The 2026-08-16 draft was written at **09:09**. The persona-biography fail-closed check
arrived at **11:20** — two hours and eleven minutes later. It never ran on that draft. The
2026-08-14 draft precedes it by a further two days.

So for both candidates, `"persona_biography_unresolved" not in stages` is **not verifiable**.
Its absence from `pipeline_degraded` means *never evaluated*, not *evaluated and passed*.

That is precisely the distinction the gate's own docstring insists on: **UNKNOWN safety is not
safety.** Treating "the check did not exist yet" as "the check passed" would silently bypass
the requirement for exactly the drafts the requirement was written to catch.

`_compute_should_block` itself also changed on 2026-08-14 (`b1d919c`, lone `gate_llm` now
blocks) and again on 2026-08-16 (`667633f`), so the 08-14 draft was additionally evaluated
under an older, weaker rule.

**Verdict: `CANNOT_SAFELY_BACKFILL` for both drafts.**

## The two expiring drafts

### `2026-08-14-modular-means-it-comes-apart-the-same-way-every-time.md`

| Field | Value |
|---|---|
| Author / title | Zen Circuit — *Modular Means It Comes Apart the Same Way Every Time* |
| Draft date | 2026-08-14 (expires 2026-08-21) |
| `fact_check_status` | `verified` |
| `pipeline_degraded` | absent |
| `publish_attempts` | 1 |
| `draft_score` | absent → would score the 7.0 default |
| sha256 | `5a7e243b5a79f7755dd29cbd3eea064bb1a4421d25b990bda825a7aa971028a9` |

**Predicate components:** `fact_check_status == "verified"` **PASS** · no existing stamp
**PASS** · `should_block` falsy **UNVERIFIABLE** (`persona_biography_unresolved` never
evaluated; `_compute_should_block` was also mid-change on this date).

**Safe to stamp: NO. Stamp applied: NO.**

### `2026-08-16-sniff-it-out-follow-your-nose-whatever-your-legs-can.md`

| Field | Value |
|---|---|
| Author / title | Maya Flux — *Sniff It Out, Follow Your Nose, Whatever Your Legs Can* |
| Draft date | 2026-08-16 (expires 2026-08-23) |
| `fact_check_status` | `verified` |
| `pipeline_degraded` | absent |
| `publish_attempts` | absent (0) |
| `draft_score` | **9** — the highest-scoring candidate on disk |
| sha256 | `e198d8db52841c14dcb6abbd9d68748c5c4f3cde19f035ac3c3f2043448a13a1` |

**Predicate components:** `fact_check_status == "verified"` **PASS** · no existing stamp
**PASS** · `should_block` falsy **UNVERIFIABLE** — proven by reflog: written 09:09, check
landed 11:20 the same morning.

**Safe to stamp: NO. Stamp applied: NO.**

This is the painful one — a 9/10 draft, on the Edinburgh source, will age out unpublished on
2026-08-23. Archiving is nevertheless preferable to bypassing publication safety, and the
brief says so explicitly. It is not stamped.

## Why no code hotfix

The cutover trap is real but **self-limiting**: it only affects drafts written before
`667633f` reached Trident. Those are exactly the three now on disk (08-13 archiving today,
08-14 on 08-21, 08-16 on 08-23). After 2026-08-23 no pre-cutover draft remains, and the gate
behaves normally for anything generated under current code.

Any code change to rescue them would have to take the form of "pre-2026-08-16 drafts don't
need `publication_safety_version`" — the permanent legacy bypass the brief explicitly
forbids, added to rescue two drafts, one of which expires tomorrow.

**Correct action: none.** The remaining barrier after 08-23 is `fact_check_status: blocked`
on recent runs, which is the safety system working as intended, not a cutover artefact.

## Stamper verification — it has never fired, so it was verified

0 of 165 articles carry the stamp, so the mechanism was unproven. Verified deterministically
against temp fixtures — no article created, no model call, no production file touched.
**23/23 checks pass** (`STAMPER-VERIFICATION.txt`, `verify_stamper.py`):

- pass condition writes `publication_safety_version: 1` exactly once, inside front matter
- every unrelated front-matter field and the body are preserved; exactly one line added
- repeat invocation is idempotent
- `should_block=True` writes nothing
- `fact_check_status` of `blocked` / `unverified` / `VERIFIED` (wrong case) / empty / missing
  all write nothing
- an existing stamp is never overwritten and never duplicated
- `publish_best.py`'s own `_ordinary_eligibility_ok` **and** `_current_safety_contract_ok`
  both accept a correctly stamped draft, and correctly reject an unstamped one

The stamper is sound. It has simply never had a run satisfying both conditions.

Kept as evidence rather than added to the deployable branch, so the observability patch under
review stays unchanged. Promoting it to a permanent test is a reasonable follow-up.

## Selector observation for 2026-08-21 — armed, zero change

`publish_best.py` already prints its full scoring table and gate verdicts, and cron already
appends its stdout to `automation.log`. No logrotate rule matches that log, so the slice will
survive.

Rather than touch cron, a byte-offset anchor was written to the capture root:

```
/srv/data/cripminds-shadow-capture/selector/ANCHOR-before-2026-08-21.json
  byte_offset          211415
  log_sha256_at_anchor 260ada9d26e9abe06ee0e2270671ccf749790ea7e652a770aa9a6856e4aeaa0f
  anchored_at_utc      2026-08-20T11:55:30Z
  extract_command      tail -c +211416 automation.log > selector-2026-08-21.log
```

Everything appended after that offset contains the natural 08:00 selector run — candidate set,
eligibility verdicts, scores, selection or none, archive actions, and the git result. **No
cron change, no code change, no manual trigger.**

## Migration debt recorded — not implemented

**Cadence.** Current `0 8 */2 * *` fires on odd days of the month and can fire on consecutive
days at 31st → 1st. Target should enforce a real cooldown — *publish only if the last
publication was ≥ 48 hours ago* — evaluated independently of calendar day-of-month, with the
selector free to run daily.

**Ranking.** `draft_score` is absent on most drafts and defaults to 7.0, so freshness, persona
rotation and aging dominate despite the nominal 60% weight. The ranking must stop presenting
that default as measured editorial quality. Decide during selector adaptation.

**Cutover discipline.** The root failure was shipping a requirement and its producer in one
commit with no compatibility path and no alarm for "eligible pool empty across consecutive
cycles". Any future gate of this kind needs a migration plan for in-flight artefacts before it
goes live.
