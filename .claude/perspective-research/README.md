# Perspective Research — protocol

## Why this directory exists

Chat sessions are disposable context. **This directory is durable project memory.**

Work done in a conversation is gone when the conversation is. Every reconstruction from a
summary loses the provenance, the rejected alternatives and the reasons — which is exactly
the part that stops a future session from relitigating a settled question or reintroducing
an idea that was already refused.

So the repository, not a transcript, holds: what Crip Minds has learned, where it learned
it, which ideas are provisional, which were approved or rejected, why, and what still needs
research.

**A chat summary is never the canonical record.**

---

## The hierarchy

| Level | File | What it is |
|---|---|---|
| 1 | `.claude/crip-minds-perspective-doctrine.md` | **Owner-approved durable intellectual doctrine.** The 14 shared axes, the owner mechanisms, the four editorial minds, the calibration library. |
| 2 | `.claude/crip-minds-project-genesis.md` | The artistic and project motive. Why the publication exists. |
| 3 | `.claude/perspective-research/*` | **Source-backed working knowledge. NOT automatically doctrine.** Nothing here is in force until an owner promotes it. |
| 4 | Article Research Pack / frozen Ledger | Facts for **one article only**. Not perspective knowledge, ever. |

Level 3 does not become level 1 by being interesting, well argued, or long. It becomes
level 1 when an owner says so, and the decision gets a dated note.

---

## The hard boundary

> **PERSPECTIVE KNOWLEDGE MAY LICENSE A QUESTION.**
> **ONLY ARTICLE-SPECIFIC RESEARCH + THE FROZEN LEDGER MAY LICENSE AN ARTICLE CLAIM.**

This holds at every level above. An entry in this directory may never be quoted in an
article, cited as support, or used to establish that something is true of a subject. If an
entry could be quoted, it has been written wrongly.

---

## Entry status model

Only these five. No others, no half-states.

**CANDIDATE** — source-backed and potentially valuable, but not yet owner-approved as
durable Perspective Library knowledge.

**APPROVED_DURABLE** — an owner has explicitly approved it for durable perspective
knowledge. **This still grants ZERO article factual authority.**

**NEEDS_RESEARCH** — an interesting hypothesis whose current sources are insufficient. The
commonest honest status, and not a lesser one.

**REJECTED** — considered and deliberately not adopted.

**RETIRED** — previously useful or approved, later superseded.

**Never delete a REJECTED or RETIRED entry** because it stopped being used. Keep it, keep
its reason. Deleting it guarantees a future session rediscovers the same idea and pays for
the same argument twice.

---

## Decision history

Every promotion, rejection or retirement gets a compact dated note, in the cluster file and
summarised in `INDEX.md`:

```
DATE:
ENTRY:
DECISION:
OWNER/REVIEW BASIS:
WHY:
```

**Do not silently rewrite intellectual history.** If an entry's wording changes materially,
leave a one-line change note saying what changed and why. An entry that quietly became a
different claim is worse than no entry.

---

## Chat-derived ideas

An idea does not get promoted because it appeared in a conversation and sounded right.

If it is worth preserving but is not sufficiently backed by the current source set, record
it as **NEEDS_RESEARCH** with provenance `EDITORIAL CONVERSATION / OWNER DISCUSSION`. That
preserves it against context loss without letting conversation become evidence.

---

## Third-party sources

**Never commit source binaries.** PDFs, docx and other copyrighted material stay out of
git. Read them locally; commit only:

- bibliographic / source metadata
- page and section references
- our own concise distillation
- research decisions

Never copy long passages from a source into this repository. If a mechanism cannot be
stated in our own words in a few lines, it is not yet understood well enough to record.

When a named source cannot be located locally, record `SOURCE_NOT_LOCALLY_AVAILABLE` and
stop there. **Do not reconstruct a source's contents from memory** — a remembered summary
of a book is not a source, and recording one as if it were is how an unverified claim
enters durable knowledge wearing a citation.

---

## NO PROXIES still governs

Sources in disability studies frequently contain analogies between disability and race,
gender, class or other marginalised categories. Such an analogy does **not** enter the
Perspective Library merely because a source makes it. The live doctrine's NO PROXIES
principle is authoritative: another marginalised group is not a stand-in, and a reading
about one group's situation is not licensed by another's.

Historically interesting but currently incompatible formulations are recorded under
**SOURCE TENSION / NOT ADOPTED** — kept as intellectual history, not adopted as
instrumentation, never erased.

---

## Persistence rule for future sessions

**At the START of any Perspective Library task, read, in this order:**

1. `.claude/crip-minds-perspective-doctrine.md`
2. `.claude/crip-minds-project-genesis.md`
3. `.claude/perspective-research/INDEX.md`
4. the active cluster file named by INDEX

**At the END of any task that produced a real research or owner decision:**

update `INDEX.md` and the relevant cluster file **before reporting completion.**

Reporting a decision that is not yet written down is how the decision gets lost.
