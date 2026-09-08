# Trial 002 — Targeted Research

## HYPOTHESIS 1 (selected as the strongest candidate)

**HYPOTHESIS.** The NOTAM/flight-release channel assumes a uniform reader
who can reliably extract safety-critical information from dense,
undifferentiated text under real operational conditions, with no mechanism
to register relevance or priority.

**EVIDENCE SOUGHT.** A formal safety investigation naming information
*presentation* — not system uptime — as a causal factor in a real incident,
per the disconfirming shape set in `perspective.md`.

**EVIDENCE FOUND.** Direct, primary, decisive. NTSB Aircraft Incident Report
**NTSB/AIR-18/01**, "Taxiway Overflight, Air Canada Flight 759... San
Francisco, California, July 7, 2017" (adopted September 25, 2018), read in
full from the primary PDF (`ntsb.gov/investigations/AccidentReports/Reports/AIR1801.pdf`).

On the night of July 7, 2017, Air Canada 759 (A320, 5 crew, 135 passengers)
was cleared to land on runway 28R at SFO but lined up with parallel taxiway
C, where four widebody/narrowbody jets sat awaiting takeoff clearance. The
airplane descended to 100 ft AGL and overflew the first airplane on the
taxiway; a go-around reached a minimum of about 60 ft over the second
airplane before climbing away. No injuries, no damage — but this incident is
widely regarded as one of the closest calls to a mass-casualty runway
disaster in modern aviation history.

**Directly on point, quoted from the report (§2.3.1, p.48 of the PDF):**

> "The NTSB considered the presentation and priority of the runway 28L
> closure information compared with other information that the flight crew
> received. The flight release package was 27 pages long... The NOTAM
> indicating the runway 28L closure ('RWY 10R/28L CLSD') appeared on page 8
> of the package... Features of the NOTAM text emphasized the closure
> information, such as the use of bold font for the words 'RWY' and 'CLSD'
> and a '**NEW**' designation in red font... However, this level of emphasis
> was not effective in prompting the flight crewmembers to review and/or
> retain this information, especially given the NOTAM's location (toward
> the middle of the release), which was not optimal for information recall.
> A phenomenon known as 'serial position effect' describes the tendency to
> recall the first and last items in a series better than the middle items."

> "The ACARS message providing ATIS information Quebec... was 14 continuous
> lines with all text capitalized in the same font... the NOTAM indicating
> the runway 28L closure appeared at the end of line 8 and the beginning of
> line 9. The uniform presentation of the ATIS information could have
> contributed to the flight crew's oversight of the runway closure
> information."

> "The NTSB concludes that, although the NOTAM about the runway 28L closure
> appeared in the flight release and the ACARS message that were provided
> to the flight crew, the presentation of the information did not
> effectively convey the importance of the runway closure information and
> promote flight crew review and retention. Multiple events in the...
> aviation safety reporting system (ASRS) database showed that this issue
> has affected other flight crews, indicating that all air carriers could
> benefit from improved information display in flight releases and ACARS
> messages."

Footnote 99 names seven specific ASRS accession numbers (1282309, 1409095,
1414185, 1447318, 1540033, 1544364, 820437) as exemplar cases the NTSB found
in a structured search of confusion incidents tied to ACARS/flight-plan
information formatting since 2010 — i.e., this is not a single-incident
finding; the NTSB's own search established a recurring, cross-carrier
pattern.

**Formal recommendation issued (NTSB Safety Recommendation A-18-23, p.49):**
the NTSB recommends the FAA "(1) establish a group of human factors experts
to review existing methods for presenting flight operations information to
pilots, including flight releases and general aviation flight planning
services (preflight) and ACARS messages and other in-flight information;
(2) create and publish guidance on best practices to organize, prioritize,
and present this information in a manner that optimizes pilot review and
retention of relevant information; and (3) work with air carriers and
service providers to implement solutions that are aligned with the
guidance." This is a *formal, numbered* government safety recommendation —
resolving the "unresolved and load-bearing" uncertainty flagged in
`subject.md`.

**SOURCE STATUS.** Primary document, read directly and in full via the
official NTSB PDF (not a summary, not a secondary account). Verified.

**SUPPORTS / WEAKENS / KILLS: SUPPORTS**, decisively — stronger and more
specific than the disconfirming shape required. This is real,
subject-specific, falsifiable evidence naming presentation (not uptime) as
a causal safety mechanism, confirmed by a formal numbered recommendation and
a documented cross-carrier pattern, not a single anecdote.

**WHY THIS STILL DOES NOT SURVIVE THE PUBLISHABILITY BAR (Section 7 of the
doctrine, and the Axis 1/8/12 FALSE MOVEs) — recorded here rather than in
the verdict, because it is a research finding, not an opinion:**

The report's own analysis is explicit that the failure mode is *universal*,
not differential. Its own words: "human limitations (such as fatigue and
time pressure/workload) may affect the review of information" — this is
attributed to ordinary, general cognitive phenomena (serial position effect,
attention-driven salience) that the cited psychology literature (Colman
2006; FAA 2008) treats as properties of human memory and attention in
general, not of any disability-specific population. Nothing in the report,
the ASRS pattern, or the recommendation distinguishes any subgroup of
readers from any other. The captain and first officer were fatigued from
duty scheduling and circadian timing (addressed in the report's own §1.7.3
and §2.3.3) — an ordinary occupational fatigue story with its own existing
regulatory framework, not a diagnosed condition or disability differential.

A second research thread was tested specifically to see whether a genuine
differential could be found rather than assumed: FAA medical certification
does treat ADHD as presumptively disqualifying (a diagnosed history
triggers one of the FAA's most rigorous review processes; stimulant and
non-stimulant ADHD medications are categorically disqualifying with no
special-issuance pathway — sourced via Ramos Law and thepilotlawyer.com
practitioner summaries of FAA policy, cross-checked against AOPA's 2023
reporting on the FAA's eased ADHD review process). This is real and
verifiable. **But no source connects it to the AIR-18/01 finding or the
ASRS pattern** — nothing ties the population screened out by medical
certification to the population involved in this incident or the broader
ASRS pattern, which by the NTSB's own account is a "typical," medically
certified population failing at a task assumed to be within its capacity.
Constructing that connection would be an editorial adjacency with no source
behind it — the exact failure named in Calibration Case 1 (WILDSUMACO): "a
record about a neighbouring, parent or broader entity is not automatically
a particular about your subject... placing such a record beside a claim
about the subject is worse than useless." This thread is recorded as
checked and refused, not silently dropped.

## HYPOTHESIS 2 (checked, not the primary target — see selection note in
`perspective.md`)

**HYPOTHESIS.** The FAA's own 2026 replacement system explicitly frames the
old coded-format layer, not just infrastructure age, as the problem it
fixed.

**EVIDENCE SOUGHT.** A primary FAA/DOT statement specifically naming the
ICAO-code/abbreviation format itself (not database architecture) as a
safety-relevant translation problem.

**EVIDENCE FOUND.** Confirmed but generic. Trade press (AeroTime, FlyingMag,
FAA's own NMS FAQ page) consistently describes the April 2026 NOTAM
Management Service as adding plain-language presentation "alongside the
traditional dense Q-code format," explicitly addressing "a long-standing
pilot complaint about the complexity of the coded format." This is real and
subject-specific in the sense of naming the actual coded format, but it is
a routine modernization narrative — the sourced material states the change,
not a mechanism, and cites no incident, no differential population, and no
causal chain beyond "pilots found it complex."

**SOURCE STATUS.** Secondary trade coverage plus the FAA's own FAQ page
framing; no primary rulemaking record, hearing transcript, or investigation
report was found tying the code-format layer itself (as distinct from
volume/placement, which H1 already covers) to a specific safety event.

**SUPPORTS / WEAKENS / KILLS: WEAKENS** relative to H1 — real, but thinner:
it risks Calibration Case 2 (COCHLEAR IMPLANT), a true definitional
description that would appear in any legacy-to-modern-format migration
story and carries no subject-specific incident of its own. Not pursued
further once H1 had already supplied the stronger, decisively evidenced
version of essentially the same underlying observation (information design
assumes more from a reader than a reader can reliably deliver).

## HYPOTHESIS 3 — not researched

Dropped by the PERSON-ASSUMPTION CHECK before research (see `perspective.md`
for the reasoning). No evidence gathered.
