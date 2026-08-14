# Human-Detail Provenance + Source-Packet Truncation Closure — 2026-08-14

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

**S3 realized as a clean, mechanical fix**, closest to S1 in practice: the
separate "canonical cache" (`discovery.py`'s `_SOURCE_TEXT_CACHE_MAX_CHARS`,
was 6000) and "model view" (`generate.py`'s `_SOURCE_TEXT_MAX_CHARS`, was
3000) are now **unified at one generous ceiling: 20,000 characters** — a
multiple of the longest real source measured this session (~10,800 chars),
not a literal "no limit," still a safety ceiling against a genuinely
malformed/runaway extraction. `fetch_source_article`'s and
`get_source_text`'s own default `max_chars` parameters now reference the
same module constant directly (previously two independently-hardcoded `3000`
literals that had to be manually kept in sync — now structurally impossible
to drift apart).

**Invariants preserved, verified, not assumed:**
- `source_hash`/`evidence_packet_hash`: unaffected in kind — a larger
  `source_text` simply hashes to a different (correct, larger-identity)
  value, exactly as `build_evidence_packet`'s own docstring already
  describes ("two packets are only hash-equal when their full provenance...
  is identical"). No invariant broken; a bigger evidence packet is a
  different, more complete packet, not a corrupted one.
- The "exactly one evidence_packet object threaded by reference through
  every stage" invariant: untouched — this change only affects what goes
  INTO the packet at construction time, not how many times it's built or
  passed.
- CJ2 bridge's same-evidence_packet invariant: unaffected — `cj2_winner_bridge`
  receives whatever `evidence_packet` the run already built, regardless of
  its `source_text` size; `cj2_shadow_integration_test.py` (unmodified) still
  passes.
- `source_truncated` semantics: unchanged in meaning, correctly now less
  often `True` in practice (honestly reflecting that less real material now
  gets cut) — verified directly (`source_truncation_test.py`) that a
  genuinely oversized source still gets sliced and correctly flagged.

`snapshot_test.py`: **no drift** — none of the 6 snapshotted fixture
articles' source material exceeded the OLD 3000-char cap, so this change is
safe for existing fixtures while ready for real sources that do.

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
- `source_truncation_test.py`: 15 checks — fixture shape validation, the OLD
  cap mechanically reproduced dropping late testimony, the NEW constants
  confirmed raised, `fetch_source_article`/`get_source_text`/
  `build_evidence_packet` all exercised through the REAL call path (only
  network fetch + HTML extraction mocked) proving the fix reaches all the
  way to what Fable/the writer receive, and a genuinely oversized source
  still correctly capped and flagged. ALL PASS.
- Full battery: **18/18 test files pass, 0 failures.** `snapshot_test.py`:
  no drift.

---

## 13. ISOLATION

Confirmed: this task's isolated worktree/branch
(`human-detail-provenance-2026-08-14`) never touched `main`,
`opening-quality-shadow-2026-08-14`, `ops-release-hardening-2026-08-14`, or
`testimony-architecture-2026-08-14`. No Reader Lab inspection. No CJ/B2
semantic change. No push, merge, or deploy.
