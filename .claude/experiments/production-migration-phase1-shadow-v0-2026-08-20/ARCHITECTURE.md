# Shadow V0 — Architecture

Smallest OFF-by-default vertical slice of the validated target architecture. Plumbing and
artifact integrity only. **Not an editorial calibration experiment. Not production migration.**

```
WORLD / SOURCE → DISCOVERY → ARTICLE FORM → WRITER → WRITER GROUNDING → SHADOW ACCEPT/HOLD
```

## Implementation location and isolation

`.claude/experiments/production-migration-phase1-shadow-v0-2026-08-20/impl/shadow_v0/`

Deliberately **outside `automation/`**. The Phase-1 brief allowed either location; the
experiment root was chosen because it makes "no production import" true by construction
rather than by convention, and because the repo already has a cautionary precedent —
`sofa_discovery_shadow.py` sits in `automation/orchestrator/` while being imported by nothing
in production and left untracked.

Isolation, verified rather than asserted:

| Property | Evidence |
|---|---|
| Production imports the new code | **NO** — `grep -rn "shadow_v0" automation/` returns nothing |
| Executes without an explicit flag | **NO** — `run()` raises `ShadowDisabled` unless `SHADOW_V0_MODE` is set |
| Default mode | **OFF** |
| Touches a production database | **NO** — the package contains no `sqlite3` import in executable code |
| Writes to `_posts/` or `_drafts/` | **NO** — no such path in executable code; a test also asserts `_posts` mtimes are unchanged |
| Network access | **NO** — no `requests`, `urllib`, `socket`, or `subprocess` in executable code |
| Changes any production decision | **NO** — nothing production runs reads these artifacts |

The static check scans **executable code only** — identifiers, imports and non-docstring
string literals, via AST. An earlier version scanned raw text and failed on the word
`_posts` appearing inside `runner.py`'s own safety docstring; the test now asserts what the
code does, not what its prose says.

## Modes

| Mode | Behaviour |
|---|---|
| `OFF` (default) | `run()` refuses. Nothing executes. |
| `REPLAY` | Frozen stage artifacts are ingested instead of calling models. The only executable mode in Phase 1. |
| `LIVE_SHADOW` | **Scaffolded, raises `NotImplementedError`.** Not implemented and not executed in this task. |

No paid or production API call is possible from this package: there is no network client in it.

## Stage boundaries, enforced in the artifact graph

The separation is not a comment — it is the shape of `input_hashes`, and a test asserts it:

| Stage | Consumes | Owns |
|---|---|---|
| `SOURCE_SNAPSHOT` | — | the frozen bytes and their provenance |
| `DISCOVERY` | `source` | what the evidence reveals |
| `ARTICLE_FORM` | `discovery`, `source` | selection, relationships, burden, reader path, arrival/stop |
| `WRITER_INPUT` | `article_form`, `source` | the prose instruction derived from the Form |
| `WRITER_OUTPUT` | `writer_input` | prose execution only |
| `GROUNDING_FINDINGS` | `writer_output`, `source` | sentence-level source fidelity |
| `GROUNDING_REPAIR` | `findings`, `writer_output` | patch-only repair |
| `SHADOW_DECISION` | `findings`, `writer_output`, `repair?` | ACCEPT / HOLD |

Two properties matter for the migration and are tested directly:

- **Writer Grounding receives `writer_output` + `source` and nothing else.** It does not
  receive `ARTICLE_FORM`, so grounding structurally cannot change the Form.
- **Discovery and Article Form are separate artifacts.** They are not collapsed back into a
  writer prompt, and persona does not own prose architecture — no persona material enters
  `WRITER_INPUT` at all.

## What was deliberately not built

No abstraction layer, no plugin system, no config framework, no CLI beyond a replay entry
point, no logging framework, no retry logic, no scheduler. 622 lines of package code plus a
test file. The brief asked for the smallest slice sufficient to prove the contracts, and
anything more would be Phase-2 work smuggled into Phase 1.

## Legacy surfaces absent

`WRITER_INPUT` validation rejects 29 legacy prompt markers outright (persona roleplay, canon
blocks, forbidden-word lists, testimony quotas, style-rule names, `_AGENT_BEATS` artefacts,
register selectors, the Bregman model, the prohibition surface). Both replayed fixtures pass
with zero hits, and a test proves the contract rejects an injected marker.

The 59k legacy writer prompt, the legacy writer SYSTEM, duplicated persona canon, the rewrite
SYSTEM and rules 33/33b, the style-rule bundles, and the gate/review LLM rule judges are
absent — not reimplemented, not adapted, simply not present.
