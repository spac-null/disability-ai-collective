# Human-Detail Provenance + Source-Packet Truncation Closure — 2026-08-14

**Amended by a semantics-check follow-up commit (after `312e956`): `## 10`'s
original "S3 realized as S1-in-practice" classification was wrong and is
corrected below to S2A, with real truncation-disclosure metadata added.
Everything else in this document (sections 1-9, 11-13) is unchanged from
the original audit.**

**Isolated worktree.** Branch `human-detail-provenance-2026-08-14`, built from
current `origin/main` (`64d1658`, verified before starting). Does not touch
`opening-quality-shadow-2026-08-14`, `ops-release-hardening-2026-08-14`, or
`testimony-architecture-2026-08-14`. No CJ/B2/RL touched, no live
companion-source retrieval, no push/merge/deploy.

---

## 1. HUMAN-DETAIL ENTRY PATHWAY MAP (traced from current code)

| Path | What it is | Classification |
|---|---|---|
| **A. Raw primary source text** | `fetch_source_article`/`get_source_text`, cached, threaded via `evidence_packet.source_text` | SOURCE-ANCHORED, but was position-blind-truncated (see `## 7`) |
| **B. Fable `resisting_example`** | Structured evidence-candidate object | GROUNDING-VALIDATED — `grounding.validate_evidence_field` verifies `source_excerpt` is a literal substring of source_text, `direct_quote` verbatim within it AND inside real quotation marks, `named_person`/dates checked the same way |
| **C. Fable `correction_moment`** | Same shape as B | GROUNDING-VALIDATED, same mechanism |
| **D. Other Fable/editorial fields** (`opening_scene`, `seed_sentence`, `angle`, `cross_cite`) | Planner-authored prose | `opening_scene`/`seed_sentence`: **no longer injected into the writer prompt at all** — a structural fix (not a validator) after an earlier attempt to scan them for unsupported specifics was found to only catch some shapes. `angle`/`cross_cite`: prompt-instructed only to stay "abstract" (no specific quote/name/date), no deterministic backstop — WEAK/PASSIVE by comparison to B/C but scope-restricted by instruction |
| **E. Writer free-form use of source_text** | The writer receives the SAME raw (now un-truncated) source_text directly, instructed to "use 2-4 specific facts, names, dates, or quotes as anchors" | SOURCE-ANCHORED in principle, but **quotes are one equally-weighted option among facts/dates/names — nothing prioritizes surfacing a person's own words**, and nothing deterministically checks the writer's OWN free-form prose against source_text at generation time |
| **F. Writer/model general knowledge** | Anything the model asserts from training data, not from the fetched source | **UNGOVERNED** — confirmed live, twice (see `## 4`) |
| **G. Revision/polish stages** | `_opus_targeted_revision`, `_fable_polish_rewrite`, `rewrite_with_opus` | GROUNDING-VALIDATED for NEW quotes/numbers introduced during a revision (`grounding.find_new_unsupported_specifics`) — but this **only runs on revisions, comparing revised-vs-original text; it never checks the very first draft against source_text at all** |
| **H. Citation/fact-check** | `review.py`'s CITATION_SYSTEM + `fact_check.py`'s `_web_verify_quote`/`_web_verify_claim` | ARTICLE-LEVEL FACT-CHECKED, but **only for text inside actual quotation marks with a named attribution** — real web verification, hard-blocks on CONTRADICTED for QUOTE/STUDY types — see `## 5` for exactly what this misses |

---

## 2. THE FAILURE CLASS (precise, per instruction)

Not "the model knows things outside the source" (tolerated, governed by
existing factuality policy). The target class is narrower: a
**HUMAN-DETAIL PROVENANCE CLAIM** — a statement presented as direct
quotation, first-person testimony, attributed personal experience, or a
specific anecdote about a real person ("X told me...", "X said...") — where
supporting provenance is absent or unclear. Explicitly excludes: citation of
an independent, dated, named third-party publication ("in a 2014 interview
with Wired") — a lower-risk, already-tolerated pattern, not this module's
target.

---

## 3. CORPUS PROVENANCE AUDIT

Deterministic harvest across all 141 published articles for personal-contact
language ("told me", "said to me", "I spoke with", etc.) not accompanied by a
third-party-publication citation:

- **36 raw candidate matches, 27 articles** (initial harvester) — a real
  false-positive class exists and is documented, not hidden: metaphorical
  "told me" with an inanimate subject ("the road told me", "the recording
  told me", "one gesture told me everything") matches the same phrase
  pattern. Roughly a third of raw matches are this shape.
- Of the genuine personal-contact-with-a-human-source candidates, direct
  source-tracing (frontmatter `source_url` presence + live fetch where
  fetchable — **Guardian.com blocks this session's fetch tool entirely**,
  confirmed on every attempt):
  - **2 CONFIRMED, directly verified, real incidents** (`## 4`) — elaborate,
    specific, checkable-sounding personal-contact claims with zero
    relationship to the actual fetched primary source.
  - **5 more articles carry a personal-contact claim with NO source_url at
    all** (`the-mapmakers`, `the-room-that-sings-and-the-three-steps-that-
    stop-me`, `the-case-study-with-no-second-act`, `the-pattern-that-waited`,
    `the-good-week`) — structurally guaranteed ungrounded, by construction,
    since no fetch ever happened for these articles.
  - The remainder cite Guardian sources, unverifiable this session.

**Direct quotes vs. attributed anecdotes vs. general named-person facts**:
the two confirmed incidents are both in the higher-risk categories — one a
direct quote (museum), one an attributed personal-experience anecdote with
no quote marks (floor-plan). General named-figure citations (Liz Carr, Bruce
Young, Sunaura Taylor) that name an independent public appearance are lower
risk and explicitly excluded from this module's scope.

---

## 4. THE TWO CONFIRMED INCIDENTS

1. `_posts/2026-05-04-the-floor-plan-they-can-t-read.md`: "Their facilitators
   told me, in a February 2024 call, that their strongest students were
   consistently the ones with ADHD or autism diagnoses." Verified directly
   (WebFetch) against the actual primary source (a Conversation article on
   AI literacy frameworks): **zero quotes from any teacher, student, or
   facilitator anywhere in it.**
2. `_posts/2026-05-20-sixty-four-dollars-an-hour-is-museum-language-for-we.md`:
   "One manager said it in a staff meeting, recorded in meeting notes I
   obtained through a public records request: 'We offer an experience most
   people would pay to have.'" Verified directly against the actual primary
   source (a Hyperallergic article about Seattle Art Museum unionizing):
   contains only a collective SAMWU union-letter quote and a quote from CEO
   Scott Stulen — **nothing about Tacoma Art Museum, no public-records
   claim, no such manager quote, at all.** This is the sharper of the two —
   an elaborate, specific, verifiable-SOUNDING provenance claim (a named
   institution, a named mechanism: "a public records request") attached to
   a quote with no relationship to the real fetch.

---

## 5. FACT_CHECK.PY COVERAGE AGAINST THIS EXACT CLASS

`review.py`'s CITATION_SYSTEM explicitly extracts "Direct quotes attributed
to named people" — **requiring quotation marks** — plus named studies/stats/
events. `fact_check.py`'s claim-extraction prompt is equally explicit:
"QUOTE: exact text inside quotation marks attributed to a specific [person]".
QUOTE/STUDY types get REAL web verification and hard-block on CONTRADICTED.

**What this misses, confirmed from code, not guessed:** an unquoted,
paraphrased personal-contact claim ("X told me that Y", "records I
obtained") has no quotation marks, so it is not extracted as a QUOTE at all.
It might be caught as an EVENT if the LLM extraction judges it "a specific
event cited as fact" — but EVENT-type contradictions are **advisory only**,
never blocking, and extraction is capped at 4 claims per run, so it may not
even be checked. Both confirmed incidents (`## 4`) are exactly this shape —
neither has quotation marks around the CLAIM of contact itself (the museum
one has a quote, but the claim of HOW it was obtained — "meeting notes...
through a public records request" — is the ungoverned part).

---

## 6. REVISION-PATH COVERAGE

`grounding.find_new_unsupported_specifics` (used by `_opus_targeted_revision`
and `_fable_polish_rewrite` via `_reject_if_unsupported_specifics`) is
genuinely rigorous: checks NEW quoted spans and NEW multi-digit numbers
(present in the revision but not the original) against source_text, INCLUDING
a misattribution check (a real quote reassigned to a fabricated speaker).
**But it only ever compares revised_text against original_text** — it has
no way to flag a claim that was already present in the very FIRST draft and
never touched by a revision pass. Both confirmed incidents originated in
initial drafts, not revisions — this guard would not have caught either one,
by design, not by a bug in it.

`rewrite_with_opus`'s new integrity guard (added earlier this session) checks
for catastrophic duplication and malformed structure — a different failure
class entirely, not personal-contact provenance.

---

## 7. SOURCE TRUNCATION — ORIGIN, REPRODUCTION, REAL SIZES

**Origin (git history, not assumption):** the 3000-char default was set in
commit `7213b03` (2026-03-15 21:32), the VERY FIRST commit that added source
fetching at all — no comment, no calculation, no documented reasoning
found. `d2992e0` (2026-08-11) later added a NAMED constant
(`_SOURCE_TEXT_MAX_CHARS`) that only documented the existing default, did not
introduce it. **Same class of stale, unrevisited limit as item H's
engagement-read truncation, fixed earlier this session** — never revisited
as the rest of the pipeline's token budgets grew (writer max_tokens is
5000+ today).

**Reproduced directly** (`source_truncation_test.py`): a synthetic fixture
with testimony before AND after char 3000 proves the OLD plain
`text[:3000]` slice keeps the early testimony and DROPS the late testimony
outright.

**Real source sizes measured this session** (limited by Guardian blocking —
honestly reported, not padded):
- Hyperallergic (museum-workers piece): ~650 words ≈ ~3,800 chars — already
  exceeds the old 3000-char cap.
- The Conversation (AI-literacy piece): ~1,800-1,900 words ≈ ~10,800 chars —
  the old cap captured roughly a quarter of it; even the old 6000-char
  repair-path cache misses over 40%.
- Frontiers (academic review paper): length not measured, but academic
  review articles in this genre routinely exceed 4,000+ words.
- **Guardian dominates this corpus's sources (50/85 articles with a
  source_url) and is entirely unfetchable this session** — the true
  distribution of real source sizes across the corpus cannot be measured
  directly; the two/three measured samples both already exceed the old cap,
  which is the strongest signal available.

---

## 8. GOVERNANCE BOUNDARY — WHAT WAS NOT DONE

Per explicit instruction, this pass does **not** require every sentence in
every article to trace to the primary source — that would destroy the
editorial system, and this corpus's own strongest pieces (Eyebrow Was Never
About Feeling, Stockpile Is the Body) carry zero external testimony and are
among the best work in the whole multi-pass audit series. The stricter rule
applies narrowly to personal-contact claims specifically (`## 2`). General
background/contextual knowledge remains governed by existing fact_check
policy, unchanged.

---

## 9. IMPLEMENTATION DECISION — PROVENANCE

**P1 — HUMAN-DETAIL PROVENANCE GAP MATERIAL.** Two confirmed real incidents
(not hypothetical), plus 5 more articles with a personal-contact claim and
literally no source ever fetched (structurally guaranteed ungrounded), out
of a corpus where source verification was possible for only a minority of
sampled articles (Guardian blocking). The mechanism is clear and reuses
existing provenance structures (`grounding.py`'s own quote/attribution
techniques) — implemented as a shadow-only detector, per instruction.

**Implemented**: `automation/orchestrator/human_detail_provenance.py` —
`find_personal_contact_claims`/`check_provenance`. Deterministic (regex),
zero model cost. Scoped narrowly to claims of the PERSONA's OWN personal
contact with a source (an interview, call, records request) — explicitly
excludes citation of an independent, named, dated third-party publication.
Classifies each candidate: `GROUNDED_QUOTE` (quoted span verified verbatim
in source_text), `UNGROUNDED_QUOTE` (quoted span not found in source_text),
`UNVERIFIABLE_PARAPHRASE` (no quote marks — structurally unverifiable by
exact match, surfaced for human attention, never silently passed),
`NO_SOURCE_AVAILABLE` (no source_text at all — every personal-contact claim
in such an article is ungrounded by construction). **Shadow only. Never
blocks. Never feeds `_should_block` or `gate.py`'s `_pre_commit_gate`**
(structural tests confirm this). Known, documented, accepted limitation:
the deterministic harvester does not distinguish a human subject from an
inanimate one ("the road told me") — a real false-positive shape, same
discipline as every other shadow check this week (G's figure-captions, B/C's
template-phrase miss) — not fixed, recorded.

Wired into `validate_article` (new `source_text=None` parameter, threaded
from `generate.py`'s `evidence_packet.get("source_text")`), persisted to a
new `shadow_human_detail_provenance` column (migration-safe ALTER TABLE),
rendered in the review sidecar.

---

## 10. IMPLEMENTATION DECISION — SOURCE TRUNCATION

**CORRECTED 2026-08-14 (semantics-check follow-up, commit after `312e956`):
this is S2, not S3.** The original report's "S3 realized as S1-in-practice"
framing was wrong, caught on re-audit, not preserved for neatness.

**Audited directly**: `fetch_source_article`'s `text = self._extract_paragraphs
(html)` is the ONLY place the full, unsliced extraction ever exists — a
local variable, never cached, never hashed, never returned. `return
text[:max_chars]` means the canonical cache (`_source_text_cache`), the
hash (`source_hash`/`evidence_packet_hash`), and everything Fable/the
writer receive (`evidence_packet.source_text`) all operate on the
ALREADY-SLICED text only. There is no separate canonical full-source
representation stored anywhere in this pipeline — true S3 was never built.

**Decision: S2A** — 20,000 chars remains a temporary BOUNDED source
representation, honestly documented as such, with real truncation
observability added (previously promised, never delivered):

- `discovery.py`'s `_SOURCE_TEXT_CACHE_MAX_CHARS` and `generate.py`'s
  `_SOURCE_TEXT_MAX_CHARS` unified at 20,000 chars (unchanged from the
  `312e956` commit) — a multiple of the longest real source measured this
  session (~10,800 chars), not a literal "no limit."
- **NEW**: `fetch_source_article` now records the TRUE pre-slice length via
  a side channel (`self._last_fetch_original_length`, same pattern as the
  existing `_last_fetch_origin`), cached per-URL by `get_source_text` and
  exposed via a new `get_source_original_length(url)` accessor.
- **NEW**: `build_evidence_packet` gained a `source_original_length_chars`
  parameter — turns that field from an always-`None` promise (its own
  docstring previously said "not recoverable at this call site") into a
  real, honest number wherever a caller threads it through. `generate.py`
  now does, at both call sites (news_seed and discovery branches).
- `validate_brief` already stamped `source_original_length_chars` from
  `evidence_packet` onto Fable's brief object — **zero changes needed
  there**, the plumbing already existed, it was just being fed a constant
  `None`.

**Why S2A and not true S3 in this pass**: building true S3 would mean
storing/hashing a genuinely separate "full source" identity alongside the
existing `source_text`/`source_hash` — and then deciding whether Fable's
grounding validation (`validate_evidence_field`) should check candidate
excerpts against the FULLER text instead of the bounded view. That's a real
editorial/architecture decision (does more available evidence change what
counts as "grounded"?), not a mechanical fix — exactly the kind of
migration/compatibility complexity the semantics-check instructions said to
avoid forcing. S2A gets the disclosure benefit (nothing disappears
*silently* anymore) without that decision.

**What >20K fixtures prove** (`source_truncation_test.py`, cases A-D):
- **A (19,999 chars)**: stored in full, `source_truncated=False`,
  `source_original_length_chars == source_length_chars` (confirms nothing lost).
- **B (exactly 20,000 chars)**: the pre-existing `>=` heuristic
  conservatively flags `source_truncated=True` even though nothing was
  actually cut — a real, pre-existing characteristic of this heuristic
  (unchanged by this pass) — but now **disambiguated**:
  `source_original_length_chars == source_length_chars` lets a consumer
  tell "flagged truncated but actually complete" apart from a real cut,
  which was impossible before (the field was always `None`).
- **C (20,001 chars)**: sliced to exactly 20,000; `get_source_original_length`
  reports 20,001 — a consumer can now compute exactly 1 character was cut.
- **D (40,000 chars, critical evidence at char 25,000)**: the evidence
  **is still genuinely lost** — `"CRITICAL_TESTIMONY_HERE" not in
  evidence_packet["source_text"]`, confirmed directly. This pass does not
  eliminate the loss (that needs true S3); it makes the loss disclosed —
  `source_original_length_chars` reports 40,000, `source_length_chars`
  reports 20,000, so a consumer can compute exactly how much (20,000
  characters) went missing, deterministically, instead of never knowing.

**Answering the exact questions posed:**
- What is stored canonically? Only the ≤20,000-char slice.
- What is hashed? The same ≤20,000-char slice (`source_hash`/`evidence_packet_hash`).
- What reaches Fable? What reaches the writer? The identical ≤20,000-char
  slice, both from the same `evidence_packet.source_text` — no separate view exists.
- Can evidence after 20K disappear silently? **The material still
  disappears. It is no longer silent** — `source_truncated` plus the new
  `source_original_length_chars` disclose it deterministically.
- Does any metadata indicate truncation? Yes, both fields above, already
  threaded through `validate_brief`'s existing stamping.

**Invariants preserved, verified, not assumed** (unchanged from the original
audit, re-confirmed after this follow-up):
- `source_hash`/`evidence_packet_hash`: unaffected in kind — computed over
  `source_text` exactly as before; the new `source_original_length_chars`
  parameter adds one more field to `identity_payload` (participates in
  `evidence_packet_hash`, consistent with every other provenance-relevant
  field there), it does not change what `source_text`/`source_hash` mean.
- The "exactly one evidence_packet object threaded by reference through
  every stage" invariant: untouched.
- CJ2 bridge's same-evidence_packet invariant: unaffected —
  `cj2_shadow_integration_test.py` and `cj2_winner_bridge_test.py`
  (unmodified) both still pass.
- No duplicated/conflicting evidence identity was created — exactly one
  `source_text`/`source_hash` per run, as before; the new field is pure
  observability metadata, not a second source representation.

`snapshot_test.py`: **no drift** — none of the 6 snapshotted fixture
articles' source material exceeded the OLD 3000-char cap, so this change
remains safe for existing fixtures while ready for real sources that do.

---

## 11. REVISED L1/L2 ROADMAP

**SOURCE COMPLETENESS + PROVENANCE FIRST → then L1 → then L2 only if residual
evidence supports it** — exactly the ordering this pass's own instructions
anticipated, now executed:
- **Source completeness**: DONE this pass (`## 10`).
- **Provenance shadow**: DONE this pass (`## 9`) — will begin accumulating
  real signal on natural production runs (zero backfill, per this session's
  own established discipline for every shadow check).
- **L1 (expand Fable's resisting_example/correction_moment scope, or add a
  general testimony-candidate hoisting field)**: still NOT implemented.
  With source truncation closed, L1's remaining gap is now purely the
  narrow-scope question (`## 1`, path E) — a genuine editorial-policy
  decision (does this publication want a general "surface the subject's
  voice" slot, separate from correction/resistance?), not a mechanical fix.
  Revisit once the provenance shadow has real accumulated data — several
  weeks of natural runs, same discipline as every other shadow check.
- **L2 (live companion-source search)**: still NOT implemented, still the
  last item. The residual gap is smaller than the original 8/15 "none"
  estimate (several of those cases are legitimate persona-voice-only
  pieces with no real gap) — but genuinely hard to size with confidence
  given Guardian's blocking this session. Do not build before L1's
  narrow-scope question is resolved and the provenance shadow has real data.

---

## 12. TESTS

- `human_detail_provenance_test.py`: 13 checks — both confirmed real
  incidents (paraphrased, not depending on the live files), synthetic
  fixtures A-E from the audit brief, no-source-available, the documented
  metaphorical false-positive shape, malformed-input safety, and structural
  no-blocking-authority proofs. ALL PASS.
- `source_truncation_test.py`: 27 checks (15 original + 12 added in the
  semantics-check follow-up) — fixture shape validation, the OLD cap
  mechanically reproduced dropping late testimony, the NEW constants
  confirmed raised, `fetch_source_article`/`get_source_text`/
  `build_evidence_packet` all exercised through the REAL call path (only
  network fetch + HTML extraction mocked), a genuinely oversized source
  still correctly capped and flagged, and the four >20K boundary fixtures
  (A: 19,999 chars, B: exactly 20,000, C: 20,001, D: 40,000 with evidence
  at char 25,000) proving the disclosure mechanism works exactly as
  specified. ALL PASS.
- Full battery: **18/18 test files pass, 0 failures.** `snapshot_test.py`:
  no drift. CJ2 bridge, grounding, and lineage suites explicitly re-confirmed
  individually, not just as part of the batch count.

---

## 13. ISOLATION

Confirmed: this task's isolated worktree/branch
(`human-detail-provenance-2026-08-14`) never touched `main`,
`opening-quality-shadow-2026-08-14`, `ops-release-hardening-2026-08-14`, or
`testimony-architecture-2026-08-14`. No Reader Lab inspection. No CJ/B2
semantic change. No push, merge, or deploy.
