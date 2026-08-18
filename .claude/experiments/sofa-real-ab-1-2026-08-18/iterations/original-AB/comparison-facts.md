# Comparison Facts — Sofa Real Article Test 1 A/B

| Fact | Legacy Shadow | Sofa Shadow |
|---|---|---|
| **Source status** | Real, fetched article (Edinburgh Art Festival review), 8,629 chars, `source_hash fee0a03b...` — same evidence packet for both | same |
| **Frozen commission provenance** | Earlier faithful real Fable response, offline-revalidated after the narrow terminal-punctuation fix (see CASE.md) — not regenerated, not selected for quality | same commission |
| **Writer model requested** | `openrouter/claude-opus-4.8` (production `PROVIDERS[0]`, CLIProxy) | `openrouter/claude-opus-4.8` (pinned to match) |
| **Writer model actual** | `anthropic/claude-opus-4.8` | `anthropic/claude-opus-4.8` |
| **Writer params** | max_tokens=5000, timeout=180, no_think=False, no temperature override | identical |
| **Word count** | 1,227 | 1,090 |
| **Grounding status** | FAIL | FAIL |
| **Unsupported claim count** | 6 | 4 |
| **Uncertain claim count** | 1 | 2 |
| **Total claims audited** | 10 | 7 |
| **Persona-roleplay present** | Yes (production persona-voice writer prompt: canon, state, first-person Zen Circuit perspective) | No (enforced pre-generation by `assert_no_persona_leakage`, fails closed) |
| **Mechanism sentence verbatim present** | No | No |
| **Reader-contract verbatim present** | N/A (Legacy architecture has no `reader_contract` field) — not present | No |

Both articles were audited with the same `run_shadow_grounding_audit` function, the same source snapshot, the same discovery packet (hidden_mechanism/known_gaps) as the shared reference frame, and the same audit model chain (`_call_editorial_model` default: Fable-first, Opus-fallback — production's `_fable_editorial_review` chain). Neither article was repaired after audit.
