# FORM-1.3-R3 — frozen FORM-1.3 variance replicate

**NOT a new Form version.** This repeats the EXACT frozen FORM-1.3 writer condition.
Nothing in the Form, packet, rendered prompt, source or commission differs from the
original FORM-1.3 run. The fixed FORM-1.3 prompt is itself the experimental object.

## Frozen condition (copied from FORM-1.3 and hash-verified, not rebuilt)
| artifact | sha256 |
|---|---|
| source-snapshot | fee0a03b8bb0c56b88b0806a9120576c87f0983764d8620c77c56b59531d4753 |
| packet | a620d0ce700a501de1695cc63253b518da283397388dba4dfb1f570af8f8e8ab |
| rendered writer prompt | 12e520e449752ed89522963c77a48fc2b86636a31a20d8f3ca47ac4ec276cdfd |

## Execution
- mode: LOCAL_CLAUDE_SUBSCRIPTION — manual architecture-development run, NOT a
  production-path replay. No OpenRouter, no Trident, no Fable.
- model: `claude-opus-5[1m]` (enforced by the runner; it refuses to record any other
  identity rather than silently introduce a confound)
- writer generations: 1. No retries. No candidate selection.

## Output
| artifact | sha256 |
|---|---|
| form-1.3-r3-article.md (646 words) | 27b1038c80af9890ca07b5b4ab1533670b3425f11c41d2898d2a61d806086d94 |

## Auditor
Prompt construction byte-identical to FORM-1/1.1/1.2/1.3
(`build_shadow_grounding_audit_prompt`). Auditor MODEL is the local subscription, not
the production review/audit chain. Verdicts treated as evidence, not authority;
independent adjudication applied on top.
