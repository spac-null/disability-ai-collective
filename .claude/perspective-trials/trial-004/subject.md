# Trial 004 — Subject

## SUBJECT

The Great Molasses Flood: on January 15, 1919, a 50-foot-tall, 90-foot-
diameter steel storage tank holding roughly 2.3 million gallons of molasses
burst in Boston's North End, killing 21 people and injuring about 150.

## SOURCE / CANDIDATE ORIGIN

No live production candidate-discovery feed was inspectable in this
worktree without running the production pipeline (which this trial is
explicitly not to do — shadow trial, no production system run). The
repository's `calibration/candidates/*.json` files are calibration-round
material, not an ordinary production feed, and are excluded from this trial
on the same basis as the calibration subject set itself. This subject was
therefore selected manually by the controlling session, as Trials 001–003
were, honestly recorded as such rather than presented as if it came from an
automated feed it did not come from.

## WHY THIS ORDINARY SUBJECT WAS SELECTED

An industrial-accident/institutional-negligence story: a company's storage
tank, an engineering failure, a documented six-year legal investigation.
Deliberately picked outside the shape of everything used so far — not a
governed facility (Trial 001), not an information/notification system
(Trial 002), not a standards-committee/equipment-interoperability story
(Trial 003), and not, on its face, itself a literal instance of a
measurement, timing, or classification device (unlike several calibration
subjects — a keyboard layout, a loudness standard, a calendar rule, a
weight-classification threshold — whose entire premise already sits inside
one axis's vocabulary). This is a plain accident-and-lawsuit story. I do
not have a preformed sense of which axis, if any, applies, and did not
check before recording this rationale.

## FRESHNESS CHECK: PASS

**Checked against:**
- The 16-subject calibration SCORED SET, the 3-subject DIAGNOSTIC SET, and
  the 4-subject SACRIFICIAL PILOT SET (`.claude/perspective-calibration/
  subject-set-001.md`, read from `research/perspective-library-calibration`
  @ `b579e91`): S01 QWERTY, S02 NOAA Coral Reef Watch DHW, S03 Toyota andon
  cord, S04 NYC Subway ADA elevator settlement, S05 ITU-R BS.1770/*Death
  Magnetic*, S06 BMI, S07 GMDSS/SOS, S08 ISO 668 shipping container, S09
  SAT/ACT extended-time flagging, S10 Gregorian leap-year rule, S11 SI
  kilogram redefinition, S12 Superpave asphalt spec, S13 BIFMA furniture
  standards, S14 restaurant kitchen expediting, S15 USPS ZIP+4, S16 *Larry
  P. v. Riles*; D01 Tollymore, D02 Roman Space Telescope, D03 Beetaloo
  Basin; P01 McDermitt Caldera lithium, P02 ICO coffee estimate, P03 FAA
  insulin-diabetes special-issuance protocol. No overlap.
- Doctrine worked examples (`.claude/crip-minds-perspective-doctrine.md`
  §6 and its research corpus): WildSumaco, the cochlear implant example,
  McGonigle (= D01/Tollymore, already checked above), the Herschel Museum,
  Ryno's rooftop rail, AUTONOMOUS/Brutus, Van Abbemuseum. No overlap.
- Trials 001–003 of this experiment: Svalbard Global Seed Vault, the FAA
  NOTAM system, the intermodal shipping container. No overlap.
- A repository-wide grep for "molasses" and "Boston.*flood"/"great
  molasses" across the full `origin/main` tree (this worktree) returned no
  results — the subject does not appear anywhere in this codebase.
- Not checked directly: a live "published Crip Minds articles" content
  store was not located in this worktree (no `content/` or `articles/`
  directory found; site content likely lives in a database or a separate
  deployment this worktree does not contain) — the repo-wide text grep
  above is the closest available substitute and returned clean.

**Why it passed:** clean on every list actually available to check against
in this worktree; the one unavailable check (a live published-articles
store) is noted rather than silently skipped.

## PRIMARY / STRONG SOURCES

- Wikipedia — "Great Molasses Flood," https://en.wikipedia.org/wiki/Great_Molasses_Flood
  (fetched and read in full; the primary source for this pass)
- Boston Magazine — "Timeline: The Great Boston Molasses Flood," https://www.bostonmagazine.com/news/2019/01/12/great-boston-molasses-flood-timeline/
- HISTORY — "Boston shocked by deadly molasses flood" and "The Great
  Molasses Flood of 1919," https://www.history.com/this-day-in-history/january-15/molasses-floods-boston-streets
  and https://www.history.com/articles/the-great-molasses-flood-of-1919
- Britannica — "Great Molasses Flood," https://www.britannica.com/topic/Great-Molasses-Flood
- New England Historical Society — "The Great Boston Molasses Flood of
  1919," https://newenglandhistoricalsociety.com/great-boston-molasses-disaster-1919/
- Boston.gov — "100 years ago today: Molasses crashes through Boston's
  North End," https://www.boston.gov/news/100-years-ago-today-molasses-crashes-through-bostons-north-end
- Not yet read directly, flagged as a gap: the 2014/2016 Harvard
  fluid-dynamics re-analysis of the flood (widely cited in secondary
  sources for the non-Newtonian-fluid mechanics and the tank's steel
  thickness/manganese-content findings) — everything below attributed to
  "a 2014 engineering analysis" comes from the Wikipedia synthesis of that
  work, not from the original paper.

## PLAIN WORLD SUMMARY

At about 12:30 p.m. on January 15, 1919, a steel tank at 529 Commercial
Street in Boston's North End — 50 feet tall, 90 feet in diameter, owned by
the United States Industrial Alcohol Company (USIA), holding roughly 2.3
million gallons (about 13,000 short tons) of molasses destined for
fermentation into industrial ethanol — burst apart at its rivets. A wave
estimated at 25 feet high moved through the streets at an estimated 35 mph.
Molasses is roughly 40% denser than water and behaves as a non-Newtonian
fluid: it hit hard enough to demolish structures and knock a streetcar off
its tracks, then thickened into a gelatinous mass that trapped people who
had survived the initial wave. Twenty-one people died; about 150 were
injured. Several blocks flooded 2–3 feet deep. Cadets from the training
ship USS Nantucket, docked nearby, were the first responders, followed by
police, the Red Cross, and Army and Navy personnel; rescue work continued
into the night and recovery took four days, with more bodies recovered
from Boston Harbor three to four months later.

USIA had bought the underlying Purity Distilling Company in 1917 and, with
Prohibition approaching (the Eighteenth Amendment was ratified the day
after the flood), was under commercial pressure to maximize alcohol
production before it became illegal. The tank had been built quickly years
earlier, filled to capacity only eight times, and reportedly leaked from
its very first filling — USIA's response was to paint it brown to hide the
leaks rather than address them. Arthur Jell, USIA's treasurer, was
responsible for the facility and, per the investigation, never filled the
tank with water to test it for leaks and dismissed workers' reports of
groaning sounds during filling. A widely cited 2014 engineering
re-analysis found the steel used was about half the thickness required for
a tank that size, and lacked sufficient manganese, making it more brittle;
cracks had formed at rivet holes. A rise in temperature and a fresh,
warmer batch of molasses added two days before the collapse likely raised
internal pressure through thermal expansion and possibly fermentation-
produced carbon dioxide.

USIA first claimed anarchists had bombed the tank. A group of 119 North End
residents brought one of Massachusetts's earliest class-action lawsuits
against the company. A court-appointed auditor, Hugh W. Ogden, ran hearings
for roughly six years, hearing about 3,000 witnesses across 45,000 pages of
testimony, and in 1925 found USIA responsible for negligent construction.
The company paid $628,000 in damages (about $11.7 million in 2025 dollars);
families of the dead received roughly $7,000 each. The case is widely
credited with tightening construction-oversight law, including requiring
that a licensed engineer or architect sign off on structures like storage
tanks — a requirement that did not exist when this tank was built.

## WHAT ACTUALLY HAPPENS

- A private company built a large industrial storage structure without
  meaningful engineering oversight (no licensed-engineer sign-off was
  legally required at the time), under commercial time pressure (the race
  to produce alcohol before Prohibition took effect), and ignored its own
  workers' warning signs (leaking, groaning sounds) rather than testing or
  fixing the structure.
- The people killed and injured were the ordinary working population of
  the neighborhood the tank stood in: laborers, teamsters, a firefighter,
  a blacksmith, municipal paving-yard workers, children as young as 10, and
  at least one 78-year-old messenger — not a selected or specialized
  population, just whoever was in the North End at 12:30 p.m. on a working
  weekday.
- The physical harm mechanism was in two stages, not one: a fast-moving
  wave capable of structural destruction, followed by the same substance
  thickening and trapping survivors who had not been killed by the initial
  impact — the two stages of a non-Newtonian fluid's behavior are what a
  1919 rescuer or investigator would have had no name for at the time.
- Legal and regulatory consequence significantly lagged the event: roughly
  six years of investigation before a finding of fault, and durable
  regulatory change (engineer sign-off requirements) only after the
  litigation concluded.

## IMPORTANT PEOPLE / OBJECTS / SYSTEMS

- **United States Industrial Alcohol Company (USIA)** — tank owner and
  operator; found negligent.
- **Arthur Jell** — USIA treasurer responsible for the facility; ignored
  leak/groaning warnings.
- **Purity Distilling Company** — original builder, acquired by USIA in
  1917.
- **The tank itself** — 50 ft tall, 90 ft diameter, ~2.3 million gallon
  capacity, at 529 Commercial Street, North End, Boston.
- **USS Nantucket cadets**, under Lt. Cmdr. H. J. Copeland — first
  responders.
- **Hugh W. Ogden** — court-appointed auditor who ran the ~six-year
  investigation and found USIA at fault (1925).
- Named victims per secondary sources: Maria Di Stasio and Pasquale
  Iantosca (both age 10); Michael Sinnott (78, messenger); George Layhe
  (firefighter, Engine 31); Anthony di Stasio (child survivor, carried by
  the wave, lost consciousness when molasses clogged his throat).
- **Boston's North End** — the working-class immigrant neighborhood where
  the tank stood and the flood occurred.

## KNOWN UNCERTAINTIES

- The "2014 engineering analysis" (steel thickness, manganese content,
  rivet-hole cracking) is cited here only via Wikipedia's synthesis; the
  original paper/study was not identified by name, author, or venue and
  was not read directly in this pass.
- Exact circumstances of each of the 21 deaths (occupation, location,
  cause of death — impact vs. drowning/suffocation in the thickening
  molasses) are only partly established here; only a handful of names and
  circumstances were confirmed via secondary sources in this pass, not a
  complete victim list from a primary record (e.g., the Massachusetts
  Vital Records or the Ogden hearing record itself).
- The exact chain of custody for the $628,000 settlement figure (total
  damages vs. per-victim vs. property-damage claims) was not verified
  against a primary legal document — figure is repeated consistently
  across secondary sources but not confirmed from the Ogden report or a
  court record directly.
- Whether the "licensed engineer/architect sign-off" regulatory change
  attributed to this case was Boston-specific, Massachusetts-wide, or
  influenced building codes more broadly was not confirmed with a primary
  legislative or code-history source in this pass.
