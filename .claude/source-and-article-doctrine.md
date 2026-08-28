# Crip Minds — Source & Article Doctrine

**Owner decision, 2026-08-28. Durable.** This is the editorial constraint that future
NEWS/POOL and engine work must satisfy. It is doctrine, not a status tracker: current
state lives in `.claude/WORK.md`, history in `.claude/LOGBOOK.md`, and this file says
what the publication is trying to be.

It supersedes nothing that is live in code. Where the engine's own prompts already
express a rule (the prose doctrine and article-form rules in
`automation/new_engine_v1/stages.py`, the fabrication and evidence boundaries), those
remain the enforcing text; this file is what they are for.

`MANIFESTO.md` at the repository root is the public-facing statement and predates the
current engine — where it describes long-form first-person theses held to the end, read
this file instead for how articles are actually meant to work now.

---

## 1. Find material worth investigating, not "disability news"

Crip Minds does not primarily look for articles already framed around disability. A
strong anchor may come from anywhere: daily news, long-form journalism, essays, opinion,
interviews, science and research, academic papers, whitepapers, reports, datasets and
documentation, art and cultural criticism, history, technology, design, labour, cities,
policy and legal material, archives, obscure and evergreen writing.

The disability perspective may emerge through research and discovery. It does not have to
be present in the source headline, and a source that already announces it is not
therefore a better source.

## 2. No disability-led quota

Disability-led sources are often valuable — first-hand knowledge, criticism, context,
specialist expertise, perspectives missing everywhere else. Their share of the anchor
pool is **not** a target metric.

Do not boost a source because it is disability-led. Do not penalise it either. Quality,
material richness and editorial potential decide.

## 3. Different source types make different articles

- **News** — what happened, and what does it reveal?
- **Essay / opinion** — an interesting argument. What holds up, what does not, and what
  does it let us see? Opinion is an invitation to investigate, never factual authority.
- **Research, paper, whitepaper, report** — there is important knowledge here that is
  hard to reach. Do the reading, then make it unusually easy to understand.
- **Art, culture, history** — use a real work, person, event, object or archive to reveal
  the larger mechanism.
- **Evergreen or obscure material** — freshness is not required when the discovery is
  still worth telling.

## 4. Research before writing

Anchor → Research Pack → Discovery → Form → Writer. Not: thin source → clever thesis →
the same fact interpreted five ways.

A thin source may honestly produce `SHORT_ARTICLE`, `NARROW`, or
`HOLD_INSUFFICIENT_RESEARCH`. **That is success, not failure.**

## 5. Difficult ideas, very easy reading

The central product goal. The thinking may be sophisticated; the reading should feel
unusually easy. The most valuable work is taking difficult research, technical papers,
dense reports, obscure arguments and complicated systems, and making them understandable
to an intelligent general reader.

## 6. Narrative momentum, no fiction

An article may move like a good book: a concrete beginning, people and objects and events
the reader can follow, discovery unfolding step by step, real tension, consequential
detail, a reason to keep reading.

Never invent scenes, dialogue, motives, experiences, chronology, personal testimony,
institutional mechanisms, or factual detail. The momentum comes from researched reality
or it does not exist.

## 7. Let real material carry the idea

Prefer facts, people, objects, events, decisions, numbers, documents, contrasts and
properly sourced quotes over paragraphs of abstract interpretation. Do not manufacture
depth by reading one fact five ways.

## 8. Genuine tension, never forced contrarianism

A strong article usually holds a real tension: something appears to mean one thing, and
the research shows something more interesting or more complicated. Research discovers
that tension. The writer does not manufacture one, and never asserts "everyone thinks X,
actually Y" where the evidence will not carry it.

## 9. Freshness is contextual

Freshness matters strongly for news. It matters much less for research, essays, culture,
archival material and evergreen discoveries. **The current universal three-day selector
window is therefore not the desired final model.**

## 10. What selection should optimise for

Editorial potential · material richness · researchability · novelty · source and topic
diversity · a genuine question or tension · freshness appropriate to that source type.

Not: disability keyword count · a disability-led quota · freshness alone · publisher
volume · rigid category quotas.

## 11. One broad material world, not four silos

Prefer one intake system carrying useful source/content metadata — current/news,
essay/opinion, research/evidence, culture, evergreen, other — over four isolated
ingestion machines. That metadata exists to inform selection behaviour, not to enforce
quotas. The Research Pack stays free to research across every source type regardless of
where the anchor came from.

## 12. The publication, in one place

> **Difficult ideas, very easy reading.**
> Research widely. Find one thing worth telling. Let reality provide the story. Make the
> reader want to continue. Never make the story cleaner than the evidence allows.
