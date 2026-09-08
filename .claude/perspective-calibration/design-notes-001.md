> # ⚠ DO NOT PROVIDE THIS FILE TO CONDITION A OR CONDITION B.
> This file exists for the owner and the calibration designer only. The condition runner
> must never read it. It contains bucket labels, expected-reading guesses, presumed-negative
> flags, and source citations — every one of which would contaminate a blind run if it
> reached either condition's context. If you are about to feed a prompt to Condition A or B,
> the only file to read from is `subject-set-001.md`.

---

## Domain / bucket / disability-count bookkeeping

| ID | Domain | Explicit disability | Bucket | Difficulty |
|---|---|---|---|---|
| S01 QWERTY | technology | NO | B (ambiguous) | MEDIUM |
| S02 Coral DHW | biology | NO | B | MEDIUM |
| S03 Andon cord | work | NO | B | MEDIUM |
| S04 NYC Subway ADA | infrastructure | YES (1/3) | A (plausible) | LOW–MEDIUM |
| S05 Loudness war | art/culture | NO | B | MEDIUM |
| S06 BMI | measurement | NO | A/B | MEDIUM–HIGH |
| S07 GMDSS | communication | NO | B | MEDIUM |
| S08 Shipping container | ordinary objects/systems | NO | **AMBIGUOUS, not negative** | MEDIUM |
| S09 SAT extended time | measurement | YES (2/3) | A | MEDIUM–HIGH |
| S10 Leap year | measurement | NO | C (presumed negative) | LOW |
| S11 SI kilogram | science | NO | C (presumed negative) | LOW |
| S12 Superpave | infrastructure | NO | C (presumed negative) | LOW |
| S13 BIFMA | architecture | NO | B | MEDIUM |
| S14 Kitchen ticket-time | work | NO | B | MEDIUM |
| S15 USPS ZIP+4 | communication | NO | B | MEDIUM |
| S16 Larry P. v. Riles | policy | YES (3/3) | A | MEDIUM–HIGH |

**Explicit disability: 3/3 cap used (S04, S09, S16). Non-disability: 13.**
**Presumed negatives: 3 (S10, S11, S12)** — see "Why only 3" below.
**Domain coverage:** architecture·1, science·1, policy·1, technology·1, biology·1, work·2,
infrastructure·2, art/culture·1, measurement·3, communication·2, ordinary objects/systems·1 —
all 11 requested domains present.

**Reminder to self, and to any future designer:** presumed-negative status here is a *guess*,
recorded for aggregate restraint-rate analysis only (see README's Negative-Prior Rule). It is
never an answer key, and a hypothesis on S10/S11/S12 is scored on its own merits like any
other.

---

## Why S16 is not a proxy risk

*Larry P. v. Riles* involves both race and disability classification as actual, historical,
inseparable parts of the same case (Black students disproportionately placed in "educable
mentally retarded" classes via biased IQ testing). This is **not** an instance of the doctrine's
NO PROXIES failure (Case 6: borrowing one marginalized group's injustice to license a reading
about another). Race here is not a stand-in for disability — the case is literally about how a
disability-classification instrument (an IQ test used to sort students into a disability
category) was itself racially biased in its construction and application. If Condition B fires
on this subject, the hypothesis must be about the **documented mechanism in the
testing/classification/placement chain** (what the instrument measured, what category it
sorted into, what institutional action followed) — never an analogy drawn between race and
disability as parallel-but-separate injustices. Flagged here so a reviewer checks this
specifically when scoring S16 hypotheses.

---

## Source basis (verified 2026-09-08, via WebSearch)

| ID | Source 1 | Source 2 | Provenance | Date checked |
|---|---|---|---|---|
| S01 QWERTY | Smithsonian Magazine, "The QWERTY Keyboard Will Never Die" | Multiple keyboard-history summaries (InventiveHQ, HistoryFacts) cross-checked | Sholes' patents; Remington marketing history | 2026-09-08 |
| S02 Coral DHW | NOAA Coral Reef Watch methodology pages (coralreefwatch.noaa.gov) | NOAA CRW 5km DHW product page | Direct agency source | 2026-09-08 |
| S03 Andon cord | Toyota Motor Corporation official "Production System" page | Wikipedia "Andon (manufacturing)", IT Revolution "The Andon Cord" | Direct company source + secondary corroboration | 2026-09-08 |
| S04 NYC Subway | Disability Rights Advocates, "MTA Settlement" press page | NY1, "MTA to expand accessibility... by 2055"; THE CITY, court approval coverage | Plaintiff org + local news, settlement document referenced | 2026-09-08 |
| S05 Loudness war | Sound On Sound, "'Dynamic Range' & The Loudness War" | Contemporary 2008 mastering-community coverage (recordinghacks.com, Blabbermouth) | Trade press + contemporaneous reporting | 2026-09-08 |
| S06 BMI | Oxford Academic (IJE), "Origins and evolution of body mass index" | Psychology Today / Conversable Economist historical summaries, cross-checked on Keys 1972 citation | Academic history-of-science sources | 2026-09-08 |
| S07 GMDSS | IMO official GMDSS/SAR document (imo.org) | Marine Insight, "Introduction to GMDSS" | Direct IMO source | 2026-09-08 |
| S08 Shipping container | ISO official standard page (iso.org/standard/76912) | Wikipedia "ISO 668"; ANSI Blog | Direct standards-body source | 2026-09-08 |
| S09 SAT extended time | Disability Rights Advocates, "Breimhorst v. ETS" case page | The Chronicle of Higher Education, "College Board Will Stop Flagging..." | Plaintiff-side legal record + contemporaneous trade press | 2026-09-08 |
| S10 Leap year | Standard astronomical/calendrical fact (Gregorian calendar rules) | — | Common, uncontested reference knowledge; no search performed | 2026-09-08 |
| S11 SI kilogram | NIST, "Kilogram: The Future" | Lindau Nobel Laureate Meetings blog; World Metrology Day (Wikipedia) | Direct national metrology institute source | 2026-09-08 |
| S12 Superpave | Asphalt Magazine, "History of Asphalt Mix Design in North America, Part II" | Pavement Interactive, "Superpave Overview"; FHWA publication | Trade/technical press + federal agency | 2026-09-08 |
| S13 BIFMA | BIFMA's own X10-1 Ultimate Test document (bifma.org) | Eureka Ergonomic guides on BIFMA standards | Direct standards-body document | 2026-09-08 |
| S14 Kitchen ticket-time | Standard, well-documented professional-kitchen brigade/expediting practice | — | General culinary-industry knowledge; low factual risk, no specific date/number claimed | 2026-09-08 |
| S15 USPS ZIP+4 | USPS official "Introduction of the ZIP Code" (facts.usps.com) | ServiceObjects, "The Origins of ZIP+4 for Address Validation" | Direct USPS source | 2026-09-08 |
| S16 Larry P. v. Riles | Wikipedia "Larry P. v. Riles" (cross-checked against case summary) | Disability Rights California SERR manual, "What is the Larry P. v. Riles case?" | Case-law summary + disability-rights legal-advocacy source | 2026-09-08 |
| D01 Tollymore | Repo-verified: `_posts/2026-09-06-at-tollymore-getting-to-bed-means-crossing-a-courtyard.md` on branch `audit/editorial-rules-2026-09-07` | Dezeen article cited as `source_url` in that post's frontmatter | Already-published Crip Minds article, primary source in repo | 2026-09-08 |
| D02 Roman | Repo-verified: `.claude/story-architecture/corpus/2026-09-01-roman-launches-with-its-data-pipeline-built-in.md` | Smithsonian Magazine, cited as `source_url` in that post's frontmatter | Already-drafted/published Crip Minds article | 2026-09-08 |
| D03 Beetaloo | ABC News, "NT government announces fracking in the Beetaloo Basin can go ahead" | ABC News, "Fracking regulator disputes NT government's claim it met all Pepper Inquiry promises" | Independent news reporting on a public government inquiry | 2026-09-08 — **now verified; previously flagged GENERAL KNOWLEDGE — UNVERIFIED, corrected this pass** |
| P01 McDermitt | General knowledge of published USGS-adjacent lithium-clay research (Thacker Pass coverage) | — | Not independently re-searched this pass; low-stakes, pilot-only, not scored | 2026-09-08 |
| P02 ICO coffee | General knowledge of ICO's public reporting function | — | Not independently re-searched this pass; low-stakes, pilot-only, not scored | 2026-09-08 |
| P03 FAA diabetes | Federal Register, "Special-Issuance Medical Certification: Diabetes Protocol..." | AOPA, "FAA issues first medicals to professional pilots with insulin-treated diabetes" | Direct federal regulatory source + aviation trade association | 2026-09-08 |
| P04 Hybrid III | Humanetics (dummy manufacturer) product page | NHTSA, "50th Percentile Male Hybrid III Dummies"; Wikipedia "Hybrid III" | Manufacturer + federal regulator + cross-check | 2026-09-08 |

**Unverified scored packs remaining: 0.** (P01/P02 remain lower-rigor by design — pilot-only,
never scored, per the correction that pilots test mechanics, not intellectual performance.)

---

## Why only 3 presumed negatives, not 4+

The prior design draft tried to hold 4, but every additional candidate considered (an ISO
screw-thread standard, an audio pitch-tuning standard) turned out, on inspection, to carry a
plausible tool-use or perceptual angle once examined closely. Rather than force a fourth
weak/strained "negative," the set was left at 3 (S10, S11, S12) and this is disclosed rather
than padded. This itself is informative: genuinely inert real-world subjects, once you look
past the doctrine's own three named examples (mineral survey / market report / prize
announcement), are harder to construct than a first pass assumes.

---

## Pilot mix rationale

**P01, P02 (NOTHING_HERE-likely):** reused from the first design draft's prompt-echo
negatives (a mineral survey, a market report) — explicitly sanctioned for pilot reuse because
pilots test *mechanics* (does NOTHING_HERE render correctly, does the parser survive an
empty-hypothesis response) not intellectual performance. The third prompt-echo example from
the first draft (2024 Nobel Prize in Chemistry) was retired rather than reused — two
NOTHING_HERE pilots are sufficient and a third would be redundant mechanically.

**P03 (obvious positive case):** FAA's 2019 diabetes special-issuance protocol. Chosen because
it has an unusually clean, well-documented shape — a categorical exclusion regardless of
individual capacity, replaced by an individualized, criteria-based process — that should
reliably produce *some* hypothesis from Condition B, letting the pilot verify the
positive-output rendering path (TOP-1 designation, EVIDENCE PROBE population, blind display)
rather than only the empty path. Not used in the scored 16 to avoid overlap with S16's
classification-and-consequence shape (PR001-03 territory) contaminating that subject's blind
scoring via pilot-run familiarity.

**P04 (genuinely ambiguous):** the Hybrid III 50th-percentile-male crash dummy. A real,
well-documented case where a single body-standard test device has a plausible but *contested*
relationship to real safety-disparity findings (frontal-crash injury-outcome differences by
occupant size/sex have been separately studied) — good for verifying that Condition B can
generate a candidate, weigh it against the TOP-1 rejection criteria (is this "merely
sophisticated wording" or a real mechanism?), and that a genuinely uncertain case renders
correctly in the blind display without forcing a verdict either way at pilot time.

---

## First-draft removal / replacement history

| Subject (first draft) | What happened | Why |
|---|---|---|
| Tollymore | Moved to **D01 (diagnostic)** | Doctrine's own Calibration Case 3 worked positive example — answer leakage if scored. |
| Roman Space Telescope | Moved to **D02 (diagnostic)** | Known prior production temptation subject. |
| Beetaloo | Moved to **D03 (diagnostic)**, and its pack rewritten with real sources | Known prior production temptation subject; first-draft pack was `GENERAL KNOWLEDGE — UNVERIFIED`, now fixed. |
| McDermitt Caldera lithium clay | Moved to **P01 (pilot)** | Direct instantiation of the Lens Probe's own "a mineral survey" example — prompt-echo. |
| ICO coffee report | Moved to **P02 (pilot)** | Direct instantiation of "a market report" — prompt-echo. |
| 2024 Nobel Prize in Chemistry | **Retired entirely** | Direct instantiation of "a prize announcement" — prompt-echo; not needed as a third NOTHING_HERE pilot once P01/P02 covered that mechanic. |
| Curb cuts / "curb-cut effect" | **Replaced by S16** (Larry P. v. Riles) | Axis 1's own CONCEPT text ("designing for one body improves things for all bodies... sometimes it trades one body's provision against another's") is a near-restatement of the curb-cut-effect claim — too close an analogue given Axis 1 is a mandatory Condition B input. |
| ISO shipping container (as negative) | **Reclassified to AMBIGUOUS** (kept as S08) | Its own fixed-frame/out-of-gauge-cost shape plausibly activates the already-approved PR004-05 mechanism ("when it doesn't fit, which one changes?"). Calling it a clean negative would have pre-decided the answer. |
| QWERTY neutral pack | **Rewritten** | First-draft pack incorrectly stated QWERTY "assumes a standard two-handed touch-typing posture" — touch-typing method postdates and was trained onto QWERTY, not the reverse. Corrected to describe only the letter arrangement and its persistence. |
| Coral bleaching neutral pack | **Rewritten** | First-draft pack conflated NOAA's satellite DHW/Bleaching-Alert-Area product with in-water visual survey protocols as if one combined system. Corrected to describe them as distinct, with the visual survey used to calibrate the satellite product. |
| BMI neutral pack | **Rewritten** | Trimmed critique-flavored asides ("does not distinguish muscle from fat"); corrected Quetelet's date to 1832 (was loosely "1830s") and pinned Keys' 1972 renaming to its exact citation. |
| NYC Subway neutral pack | **Rewritten** | Tightened to verified settlement mechanics (staged station counts, funding percentage); removed owner-only editorializing ("the outage system reveals...") from the run-facing pack. |
| SAT extended time neutral pack | **Rewritten** | First draft vaguely gestured at "a lawsuit ended flagging in 2003." Corrected to name both actual cases: *Breimhorst v. ETS* (1999, GMAT) and the separate DRA–College Board settlement (2002, effective Oct 2003, SAT/PSAT/AP). |
| Every scored pack | **Scrubbed** of "assumes...", "does not specify...", "silently...", "the hidden...", "the option set..." and similar Perspective-flavored phrasing, per the identical-world-input correction. |

---

## Model/provider resolution (for README's Model Control section)

Confirmed in this worktree (`3614acf5`), `automation/new_engine_v1/provider.py`:
`DEFAULT_MODEL = "anthropic/claude-opus-4.8"`. No lens-probe-specific model override exists
anywhere in `research.py` or `composition.py` — the only per-stage override found
(`COMPOSITION_MODEL_ENV`) applies to the composition stage only, not research/lens_probe. A
comment in `composition.py`, dated 2026-09-04, records that CLIProxy's native `claude-*`
routes were returning `401` at that time and that the effective serving path was OpenRouter's
`anthropic/claude-opus-4.8`. Both Condition A and Condition B must use this same model when
the pilot/calibration is actually run.
