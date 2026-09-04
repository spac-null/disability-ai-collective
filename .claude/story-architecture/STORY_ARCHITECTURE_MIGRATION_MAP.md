# What survives: component map for the composition-layer migration

This exists so months of engine work are not silently written off. The Story
Architecture work is a **composition-layer migration**, not an engine replacement. No
legacy component was removed in any of this campaign, and nothing new is wired into
production.

| component | status | note |
|---|---|---|
| Selector V2 | **KEEP** | authoritative since PR #51; untouched |
| Acquisition (bounded 403/representation fallback) | **KEEP** | PR #53; untouched |
| PDF / document ingestion | **KEEP** | PR #54; untouched |
| Research Pack + source roles | **KEEP** | the ledger reads from it; it is not replaced |
| Deterministic source-anchor selection | **KEEP** | PR #61; untouched |
| Discovery source/scope safety (`check_anchor`, `check_subject_scope`) | **KEEP / REUSE** | still the backstop; the ledger narrows candidates to the researched subject |
| Discovery essay planning (`dominant_reading`, `disturbance`, `evidence_gaps`, `grounding_boundaries`) | **LEGACY / replaced in the experimental path only** | still present and still used by production; `evidence_gaps` and `grounding_boundaries` are the measured cause of the leak |
| Article Form (FORM-1.3) | **LEGACY / NOT REMOVED** | not used by the experimental path; no decision taken |
| Writer | **KEEP MODEL ROLE, NARROW INPUT CONTRACT** | same stage, 844-word packet instead of 4,796–5,840 |
| Ledger (`ledger.py`) | **NEW** | the only origin of factual permission |
| Story Finder contracts | **NEW** | in `story.py` |
| Worth Gate | **NEW** | can answer "wrong publication" |
| Story Architect | **NEW** | now semantic: rhetorical micro-direction removed |
| Continuity Editor (`continuity.py`) | **NEW** | owns paragraphing; linguistic freedom, zero factual freedom |
| Factual surface / negative-admission / cut audits | **NEW** | four screens at three stages |
| Grounder V1 | **KEEP AUTHORITATIVE DURING MIGRATION** | content-frozen; untouched |
| Grounding V2 | **KEEP** | default OFF, shadow only, 2/4 observations, paused |
| Fact Check (coverage gate, 16-claim cap, 180s deadline) | **KEEP** | untouched; the new path reduces its input load |
| Reader gate | **KEEP** | the human gate that surfaced this whole problem |
| Publication / safety bridge | **KEEP** | untouched |

## What the experimental path actually changes

```
Research Pack ──► LEDGER ──► Worth Gate ──► Story Architect ──► Writer packet
                                                                     │
                                                              Writer draft
                                                                     │
                                                          CONTINUITY EDITOR
                                                                     │
                                          existing Grounder / Fact Check / reader gate
```

Everything upstream of the ledger and everything downstream of the Continuity Editor is
the existing engine, unchanged.

## Rollback

The old path is the rollback: it is still the only wired path. Nothing imports
`story.py`, `ledger.py` or `continuity.py` from production code, so rollback is "do
nothing".
