# L2 active human-testimony retrieval — design (A-M reconciliation item L)

Implemented tonight (`automation/orchestrator/testimony_l2.py`, OFF by default, see
its module docstring): the deterministic testimony-needed heuristic, the companion-
candidate eligibility checks, the `evidence_packet["companion_source"]` slot with
provenance kept structurally separate from the primary factual source, and
fixture-based SHADOW-mode bridging — same "fixture only, no live orchestration"
discipline as `cj2_shadow.py`. 30 tests pass (`automation/testimony_l2_test.py`).

**Not implemented, by design: live companion-source SEARCH.** This is the piece
still missing before L2 could ever do anything in a real run. Preregistered here
so a future pass can implement against a fixed contract rather than improvising.

## What's missing

`_l2_testimony_attempt` today can only bridge a companion candidate that's already
sitting in a fixture file (`L2_COMPANION_FIXTURE`). Nothing in this codebase can go
from "testimony needed, primary source X lacks it" to "here is a real candidate
URL/quote/person" — that step doesn't exist.

## Candidate mechanism: reuse `_web_verify_claim`'s Sonar call, don't build new infrastructure

`fact_check.py`'s `_web_verify_quote`/`_web_verify_claim` already make live,
production-approved calls to Perplexity Sonar (via OpenRouter) — the only real web-
search-capable mechanism anywhere in this codebase. They're narrow verification
queries today ("is this specific quote/claim true"), not open-ended search, but the
same underlying capability (an LLM with live web browsing) is the natural fit for
"find a first-person account of X" — standing up a second, unrelated search
integration (SerpAPI, a custom scraper) would be new infrastructure this repo has
never needed and doesn't need now.

## Query contract (not implemented)

Given `evidence_packet["source_text"]` and the run's topic/title, a new function
`_search_companion_testimony(topic, source_text)` would:

1. Build a Sonar query along the lines of: "Find a first-person account, interview
   quote, or testimony from someone who has directly experienced <topic>. Return the
   speaker's name, the source URL, and the exact quoted text. If none exists, say so
   plainly." — a retrieval query, not a verification query, which is the actual new
   capability being asked of Sonar here, and the reason this isn't "just wire the
   existing function with a different string."
2. Parse the response into the same `{"url", "person", "text", "quote"}` shape
   `_check_companion_eligibility` already expects — zero change needed to the
   eligibility/attachment code written tonight.
3. Feed the result through the EXACT SAME `_check_companion_eligibility` gate
   already implemented and tested — a live search result gets no more trust than a
   fixture does; eligibility is the single chokepoint either way.

## Open questions a live implementation would need to resolve (not resolved here)

- **Cost/latency budget.** Sonar calls cost money and add latency to every run where
  testimony is judged needed (roughly the essay/pleasure/fury/confusion/indefensible
  majority, per the heuristic's own false-negative-prone nature — see its docstring).
  Needs a decision: every degraded run, a sampled fraction, or gated behind a
  separate `L2_LIVE_SEARCH_ENABLED` flag on top of `L2_TESTIMONY_MODE=SHADOW`.
- **Ranking among multiple results.** Sonar may surface more than one candidate.
  Tonight's eligibility check accepts/rejects one candidate; a live version needs a
  tie-break rule (most specific quote? most recent? shortest path to source?) —
  a real ranking design, not a mechanical extension.
- **Source-type trust.** Should a companion source ever come from the same outlet as
  the primary (a second article on the same site) versus requiring a genuinely
  different, independent source? Not decided.
- **False-negative rate of the needed-heuristic itself.** The heuristic's own
  docstring documents real false negatives (testimony phrased without a classic
  attribution verb reads as "needed" when it may not be) and false positives (a
  quote containing "I" without being genuine lived-experience testimony). Live
  search makes these costlier (a real API call instead of a no-op), so calibrating
  the heuristic before turning on live search matters more than it does for the
  current SHADOW-with-fixtures mode.
- **Persona/doctrine fit.** Per `.claude/original-blueprint-A-M-reconciliation-
  2026-08-13.md` item K ("disability as instrument, not default topic"), a companion
  testimony search must not implicitly assume the topic IS disability — the
  heuristic and search query both operate on whatever the article's actual subject
  is, disability-related or not. Nothing in tonight's implementation violates this
  (the heuristic runs on `source_text` regardless of topic), but a live search
  query's exact wording should be reviewed against this doctrine before shipping.

## Recommended next step (not taken tonight)

A small, isolated SHADOW-only experiment: run `_search_companion_testimony` against
~10-20 already-published articles' primary sources (offline, using each article's
`source_url` already in frontmatter, one Sonar call per article, results only
logged, never attached to a real evidence_packet) to see what real candidates look
like before writing the ranking/trust rules above. This mirrors G's own "gather
real evidence before threshold decisions" discipline.
