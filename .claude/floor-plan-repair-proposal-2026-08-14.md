# Floor-plan article repair — proposal, NOT executed

`_posts/2026-03-31-the-floor-plan-of-disappearance.md` — prepared per instruction
13 of the rewrite-integrity task. Deterministic comparison only. **No prose
rewritten. Article file not touched. This is a proposal for human review.**

## Side-by-side comparison (deterministic diff of the two copies)

Copy 1 = paragraphs before the leaked line. Copy 2 = paragraphs after it.
Aligning by prose content (ignoring the two `<figure>` blocks a later retrofit
inserted at different relative positions in each copy — confirmed both copies
have the SAME 11 prose paragraphs, i.e. this is a clean full-body duplication,
not two different drafts):

**Identical in both copies (9 of 11 paragraphs, byte-for-byte):** the opening
Almere paragraph, the case-study-quote paragraph, "The Almere portal also
passes every audit," the "Here is what nobody calls it" paragraph, "The
award-winning firms start from a different question," the Rotterdam
anecdote, the "Care is arithmetic" paragraph (except the one word noted
below), and the closing "Miriam Sherwood's paper form" line.

**Two genuine wording differences:**

1. **Haringey/Miriam Sherwood paragraph** —
   - Copy 1: *"It was, by every measure, **non-compliant with no one's
     expectations and compliant with every rule**."* + carries a markdown
     citation link: `[WCAG standards](https://www.w3.org/WAI/WCAG21/quickref/)`
   - Copy 2: *"It was, by every measure, **compliant**."* + plain text
     "WCAG standards", no link.
2. **"Care is arithmetic" paragraph** —
   - Copy 1: *"...prevents users from **recording** it..."*
   - Copy 2: *"...prevents users from **documenting** it..."*

## Which copy is the safer canonical base — evidence, not a guess

**Copy 2.** The leaked line itself states this directly: *"I need to stop and
return the correct article. Let me apply only the listed fixes precisely."*
— the model is explicitly labeling what follows as the corrected version with
its fixes applied, not a second, unrelated draft. The content confirms this
self-description: copy 1's sentence *"non-compliant with no one's
expectations and compliant with every rule"* is garbled and self-contradictory
(reads as though it's negating itself mid-sentence); copy 2's *"It was, by
every measure, compliant"* delivers the same intended irony (technically
compliant, practically useless) cleanly. This is a real editorial fix, not
noise. "recording" vs. "documenting" is a minor, directionally-neutral word
swap either way.

**One caveat, not a reason to prefer copy 1:** copy 1 carries the WCAG
markdown link, copy 2 doesn't. This is very likely NOT a deliberate content
choice by either copy — `git log --follow` on this file shows a later,
separate commit, `19f4bcf` ("audit: inject missing links in 2 article(s)"),
whose own name describes a targeted link-injection retrofit script. Such a
script doing a single (not replace-all) substring match against "WCAG
standards" would patch only the FIRST occurrence in the file, landing in
copy 1's territory, regardless of which copy is the "correct" one. The
missing link in copy 2 is best read as an artifact of that retrofit's own
single-replace behavior, not evidence against copy 2.

**Recommendation: copy 2's prose, with copy 1's WCAG link re-applied to
copy 2's "WCAG standards" mention.** This is the only content decision this
proposal makes beyond mechanical deduplication, and it's flagged explicitly
as a small editorial judgment call, not a deterministic fact — a human should
confirm before it's applied.

## Figures

Original creation commit (`2c6a252`, 2026-03-31) had zero images. Both
`<figure>` blocks were added later, by two separate retrofit commits
(`c550972`, `e0907de`) that inserted them at computed positions within the
already-duplicated (roughly double-length) body — which is why one figure
landed inside copy 1's territory and the other inside copy 2's. A repaired,
single-copy body needs both images repositioned, spaced through the
surviving ~11 paragraphs (matching this publication's usual one-image-per-
few-paragraphs convention): proposed placement is after paragraph 3
(gouache illustration) and after paragraph 8 (linocut symbol) of the
surviving body — a mechanical repositioning of the same two existing image
files/alt text/captions, not new content.

## Proposed repaired body (PROPOSAL ONLY — not written to `_posts/`)

```markdown
---
layout: post
title: "The Floor Plan of Disappearance"
date: 2026-03-31
author: "Pixel Nova"
category: visual design
image: /assets/the-floor-plan-of-disappearance_setting_1.jpg
image_alt: "Overhead shot of architectural floor plan blueprints layered and folded into each other until they become illegible illustration for The Floor Plan of Disappearance"
excerpt: "Websites designed to meet every accessibility standard simultaneously make care harder to access for disabled people."
keywords: [digital accessibility compliance paradox, WCAG standards, Miriam Sherwood, Haringey housing benefits portal, Almere care portal redesign, dark patterns in government services, accessibility theater]
---
In February 2024, the Dutch municipality of Almere published a redesigned care portal. New typeface, new color palette, new logo. The navigation had been reorganized by a design firm that won an award for it. I pulled up the site on my laptop and counted: fourteen clicks to reach the page where a resident could report that their home care hours had been cut. Fourteen. The old site took three.

The firm's case study called this "streamlined information architecture."

---

In January 2012, the London Borough of Haringey rebuilt its housing benefits portal. This 2012 redesign matters because it shows how the problem I'm describing isn't new. A caseworker named Miriam Sherwood told the *Hackney Citizen* that month: "The new system is beautiful. My clients can't find anything." She described residents arriving at her desk holding printouts of pages they couldn't navigate past. The design had passed every accessibility audit. It met [WCAG standards](https://www.w3.org/WAI/WCAG21/quickref/)—the Web Content Accessibility Guidelines, which set the bar for digital accessibility—meaning it technically complied with official requirements for readability and usability. It had alt text, keyboard navigation, sufficient contrast ratios. It was, by every measure, compliant. Sherwood kept a paper form in her drawer. She filled it in by hand for people who couldn't get through the digital version. She did this for two years until someone told her to stop.

The Almere portal also passes every audit.

<figure class="article-figure">
<img src="{{ site.baseurl }}/assets/the-floor-plan-of-disappearance_moment_2.jpg" alt="The Floor Plan of Disappearance — intimate gouache illustration on textured paper" width="800" height="450" loading="lazy" decoding="async">
<figcaption>The Floor Plan of Disappearance — intimate gouache illustration on textured paper</figcaption>
</figure>

Here is what nobody calls it: when you bury the thing people need most behind enough beautiful pages, some of them stop looking. Not all. Not even most. Enough. The ones who stop are disproportionately older, disproportionately disabled, disproportionately the people the system was built to serve. This is not a design flaw. A design flaw is an accident. Fourteen clicks is a choice someone made in a meeting.

Otto Neurath, a 20th-century philosopher and designer, understood this in the 1930s. He created the isotype system, a simplified visual language designed so that anyone could grasp it without requiring reading. He failed in specific ways. His pictograms still assumed a particular body, a particular literacy. But he started from the right question: who cannot reach this, and what have I built between them and the thing they need?

The award-winning firms start from a different question. They start from: what looks clean.

I design information systems. I know the seduction of clean. I have sat in a room in Rotterdam in May 2023 and watched a designer move a "report a problem" button from the top navigation to a submenu because it "cluttered the hero image." Everyone nodded. I said the button needed to stay. The project lead said users could find it through search. Search requires you to know what you've lost.

<figure class="article-figure">
<img src="{{ site.baseurl }}/assets/the-floor-plan-of-disappearance_symbol_3.jpg" alt="The Floor Plan of Disappearance — abstract linocut symbol" width="800" height="450" loading="lazy" decoding="async">
<figcaption>The Floor Plan of Disappearance — abstract linocut symbol</figcaption>
</figure>

Care is arithmetic. Hours multiplied by weeks multiplied by the body that needs them. Cut the hours, the math collapses. But deliberately hiding the path to reporting the cut prevents users from documenting it—the math never changes, only the floor plan does.

Miriam Sherwood's paper form, pulled from a drawer, outlasted two portal redesigns.
```

## Status

**NOT COMMITTED.** `_posts/2026-03-31-the-floor-plan-of-disappearance.md` is
unchanged on disk. This proposal is ready for a human editorial decision —
specifically whether to (a) accept copy 2's prose as canonical, (b) accept
re-adding the WCAG link to copy 2, and (c) accept the proposed figure
placement — before anyone applies it as a real commit.
