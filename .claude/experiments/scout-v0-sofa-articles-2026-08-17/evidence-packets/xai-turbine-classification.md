# Evidence Packet — xAI Gas Turbine "Non-Road Engine" Classification

**Disturbance (already selected, not re-litigated here):** xAI classified fixed-site gas
turbines powering its Memphis-area data centers as "non-road engines" — a category built
for mobile/trailer-mounted equipment — based on physical form (wheels/trailer-mounting)
rather than actual function (continuous, long-term, fixed-site operation). EPA found this
violated the Clean Air Act in January 2026.

**IMPORTANT — there are two distinct facilities/legal tracks. Do not conflate them.**
The original disturbance quote (Winbuzzer, 15 permitted / up to 35 operated) describes
**Colossus I** in Memphis, TN, under **Shelby County Health Department (SCHD)**
jurisdiction. A second, larger, better-documented dispute involves **Colossus II**, whose
turbines sit across the state line in **Southaven, Mississippi**, under **Mississippi
Dept. of Environmental Quality (MDEQ)** jurisdiction. Same mechanism (mobile/temporary
non-road classification), different regulator, different turbine counts, different
paper trail. A writer should pick one as the spine and mention the other only for scale/
pattern — mixing their turbine counts in one sentence will produce a factual error.

---

## 1. Re-verified and deepened core regulatory facts

### 1.1 Who actually regulates this (jurisdiction, corrected)

- Air permitting for both Tennessee and Mississippi sites is **locally/state
  administered under EPA-approved State Implementation Plans (SIPs)** — EPA does not
  issue permits directly. Shelby County Health Department is Memphis/Shelby County's
  delegated local permitting authority; Mississippi Dept. of Environmental Quality
  (MDEQ) is the state authority for Southaven (DeSoto County), MS.
  Source: Feb 13, 2026 NAACP/SELC/Earthjustice Notice of Intent to Sue letter (full
  PDF fetched and read directly — see §1.3), pp. 12–13, citing 42 U.S.C. §7410 and
  40 CFR §52.1270(c).
- EPA's role in the January 2026 action was **national rulemaking** (see §1.2) plus,
  separately, EPA statements/enforcement pressure on the Memphis situation — not a
  site-specific permit decision. Multiple outlets (CNBC, Jan 16 2026; Winbuzzer,
  Jan 20 2026) describe this as EPA "ruling" xAI illegally operated turbines, but the
  primary EPA document available (the NSPS fact sheet, see below) is a generally
  applicable rule, not an adjudication naming xAI. This is a real gap between headline
  framing and the primary document — flagged explicitly in §1.2 and §6.

### 1.2 The actual EPA document, and how it differs from the "loophole closed" headline

I located and read **the primary EPA document** directly: *Fact Sheet — New Source
Performance Standards for Stationary Combustion Turbines: Final Rule*, 40 CFR Part 60,
Subpart KKKKa, dated January 2026, published at
https://www.epa.gov/system/files/documents/2026-01/correct_fact-sheet-nsps-stationary-combustion-turbines.pdf
(final rule at Federal Register, published Jan 15, 2026:
https://www.federalregister.gov/documents/2026/01/15/2026-00677/new-source-performance-standards-review-for-stationary-combustion-turbines-and-stationary-gas).

Key facts from the primary document (exact text, read directly):

- **Finalized/signed January 9, 2026.**
- It creates NOx emission subcategories by turbine size/efficiency/utilization, and —
  separately — **"finalizes an additional subcategory for stationary temporary
  combustion turbines."**
- Exact quoted definition: *"a temporary combustion turbine that remains in place for
  longer than 24 months would not be considered temporary for any period of its
  operation, and any failure of the owner or operator to comply with the otherwise
  applicable requirements of the NSPS would be an enforceable violation of the CAA."*
  **This is a 24-month threshold, not 12 months and not "364 days."**
- Critically: *"EPA is including a provision in this NSPS that will allow portable
  combustion turbines regulated as title II-covered engines to be exempt from this
  NSPS as nonroad engines."* **The nonroad/mobile-engine exemption pathway was not
  eliminated — it was preserved, alongside a new, separate "temporary" stationary
  subcategory with its own (lighter) emissions standard (25 ppm NOx) and reduced
  monitoring/recordkeeping.**
- The rule applies to units that **commenced construction, modification, or
  reconstruction after December 13, 2024** — i.e., it is prospective, not a retroactive
  finding against xAI's already-installed turbines.
- Nowhere in this fact sheet is xAI, Memphis, or any data center named.

**This matters for the article.** The widely repeated framing ("EPA closes the
loophole that let xAI pollute for a year without a permit") is a journalistic
compression of a more technical, more ambiguous regulatory action. What EPA actually
did was (a) write a new, formal "temporary turbine" category with its own 24-month
clock and lighter-but-real emissions/recordkeeping requirements, while (b)
**explicitly keeping a nonroad-engine exemption alive** for genuinely portable,
Title-II-compliant units. A more separate EPA statement — quoted identically across
several outlets (Winbuzzer via CNBC reporting; SELC press release header, and echoed
in a legal-industry summary, Encino Environmental Services,
https://encinoenviron.com/epa-closes-permitting-loophole-used-by-ai-data-centers/)
— reads: *"Historically, however, the EPA has not regulated combustion turbines, even
those that may be portable, as nonroad engines, but rather as stationary sources."*
I could not independently verify the exact document this sentence is drawn from
(preamble language, applicability determination, or a public statement) — see §6.
It functions as EPA's position that the nonroad classification xAI/MDEQ relied on was
a **misapplication of an existing category**, not a genuinely new interpretation.

**A second, later legal-industry analysis (Frantz Ward LLP, May 19, 2026,
https://www.frantzward.com/epa-moving-to-regulate-data-center-turbines-as-mobile-sources/)
describes EPA as actively considering formalizing a path for data-center turbines to
qualify as "mobile sources"** to get lighter permitting — the opposite direction from
"closing the loophole." This is a genuine tension in the record, not a reporting error
on my part: press coverage in January framed EPA as shutting the door; industry/legal
analysis in May describes EPA weighing how to keep a version of the door open for
compliant equipment. A rigorous article should not flatten this into a clean "regulator
punishes company" arc.

### 1.3 The separate, older "non-road engine" dwell-time rule (Title II, 40 CFR 1068.30/1068.31)

This is a **different, pre-existing regulation** from the new NSPS Subpart KKKKa above,
and is the one actually invoked by MDEQ to justify exempting xAI's Southaven turbines.
Confirmed via eCFR (https://www.ecfr.gov/current/title-40/chapter-I/subchapter-U/part-1068/subpart-A/section-1068.30
and .../section-1068.31):

- A nonroad engine ceases to be "nonroad" and becomes a **stationary engine** if it "is
  used or will be used in a single specific location for 12 months or longer."
- If an engine will be, or has been, used at one location for 12 consecutive months or
  more, it is treated as having stopped being nonroad **from the date it was placed
  there** — i.e., the reclassification can apply retroactively to the placement date,
  not just prospectively from month 13.
- Replacement engines performing the same function at the same location have their time
  periods **combined** for this calculation — explicitly meant to prevent swapping
  units in and out to avoid hitting 12 months.
- I could **not** find codified regulatory text using the figure "364 days." Multiple
  outlets and even one source document (a letter referenced in search results to Shelby
  County Health Department) use "364 days" colloquially as shorthand for "one day under
  the 12-month/one-year trigger." Treat "364 days" as **journalistic shorthand for the
  12-month rule, not a separately codified number**, unless a primary document
  specifying exactly 364 days can be located (I could not find one — see §6).

### 1.4 What MDEQ actually told xAI, in writing (primary source: read directly)

I obtained and read (via the Feb 13, 2026 NAACP/SELC/Earthjustice Notice of Intent to
Sue, a public legal notice letter — full citation below) MDEQ's own written
determination. This is the single strongest piece of documentary evidence in the whole
case, because it shows the exemption was **not xAI unilaterally self-declaring** — a
state regulator put the two-part test in writing:

> "the referenced turbines will be [1] 'mobile' as each will remain affixed to a
> portable unit (i.e., a flatbed trailer) and [2] 'temporary' as it is intended for
> each to remain on-site (2875 Stanton Road South; Southaven, MS) for less than
> twelve (12) months."
> — Letter from Jaricus Whitlock, Chief, Air Div., Miss. Dep't of Env't Quality, to
> Brent Mayo, VP of Operations, xAI, RE: Determination on Portable Gas-Fired
> Combustion Turbines (July 29, 2025), cited in NAACP/SELC/Earthjustice NOI letter at
> p. 4, citing 11 Mississippi Administrative Code Part 2, Chapter 2, Rule 2.13.D.

This is exact, quotable, and it is the clearest available textual proof that the
"form, not function" classification (wheels + trailer-mounted + a stated intent to
stay under 12 months) was the **official, written legal test the state itself applied**
— not an inference or a hostile characterization by critics.

MDEQ's letter also "implore[d]" xAI to operate "in a manner that minimizes emissions,"
which is a non-binding request, not an enforceable condition — worth noting as a soft
regulatory gesture with no teeth.

### 1.5 Exact turbine counts and dates (both sites, cross-checked across sources)

**Colossus I, Memphis, TN (Shelby County):**
- xAI announced Colossus I in June 2024, at 3231 Paul R. Lowry Road, adjacent to the
  historically Black community of Boxtown.
  (Source: NOI letter, p. 3, citing Greater Memphis Chamber, June 5, 2024,
  https://memphischamber.com/economic-development/xai/)
- Within months, the public discovered xAI was powering Colossus I with an estimated
  **35 unpermitted turbines**.
- Shelby County Health Department later permitted **15 turbines** (July 2025) —
  reported by TechCrunch, July 3, 2025:
  https://techcrunch.com/2025/07/03/xai-gets-permits-for-15-natural-gas-generators-at-memphis-data-center
- EPA's January 2026 finding (as reported): xAI ran **20 unpermitted turbines** beyond
  the 15 permitted (consistent with the 15-permitted/35-total figures).
  Source: CNBC, Jan 16, 2026, https://www.cnbc.com/2026/01/16/musks-xai-faces-tougher-road-expanding-memphis-area-after-epa-update.html
  (fetch of full article text was blocked by a 403; figure corroborated via search-result
  summary and cross-referenced against Winbuzzer's identical 15/35 figures).
- By the end of summer 2025, both the permitted turbines and Tennessee Valley Authority
  grid power supplied Colossus I. (NOI letter, p. 3.)
- SCHD's July 2025 permit decision was appealed by NAACP and other groups
  (Tennessee Lookout, https://tennesseelookout.com/briefs/naacp-others-appeal-xai-turbine-permits-for-memphis-data-center/;
  full appeal PDF: https://cdn.arstechnica.net/wp-content/uploads/2025/07/NAACP-and-YGGs-xAI-Air-Permit-Appeal-7-15-2025.pdf).
  Reporting indicates the appeals board later **dismissed the appeals as moot** (per
  search-result summary of later 2026 coverage) — I could not independently confirm
  the exact dismissal date/order from a primary document; flagged in §6.

**Colossus II, Southaven, MS (MDEQ) — the richer documentary trail:**
- xAI acquired the Southaven site (2875 Stanton Road S.) in **July 2025**.
- xAI began installing/operating combustion turbines there **August 1, 2025**, without
  preconstruction or operating permits.
- Turbine count grew steadily and was **not proactively disclosed**:
  - Early August 2025: 3 turbines (SMT-130 model) on-site.
  - By Sept. 6, 2025: 17 turbines planned (10 TM2500s, 7 SMT-130s).
  - Confirmed via aerial photography: **18 turbines on-site as of Oct. 31, 2025**
    (documented with aerial and thermal-imaging photos in the NOI letter, credited to
    Steve Jones/SouthWings; thermal imaging showed at least 9 of 18 actively operating
    that day).
  - December 2025: xAI told MDEQ 9 more turbines were coming, bringing the total to
    **27**.
  - Satellite photos from **February 9, 2026** confirm **27 turbines** on-site,
    combined generating capacity **at least 495 MW** (14 SMT-130s, 1 M35, 4 Gen6
    TM2500s, 5 Gen7 TM2500s, 3 Gen8 TM2500s), with potential emissions "multiples of
    250 tons of NOx per year and at least 10 tons of formaldehyde per year."
  - **May 2026: reported at 46 turbines** (per search-result summary of Mississippi
    Today reporting: "when the number grew to 46 units in May, MDEQ said xAI didn't
    have to notify the agency when adding more 'temporary-mobile' turbines").
  - **April 2026 lawsuit filing put the count at 33** (27 original + 6 added after the
    Feb. 13, 2026 legal notice — see §4).
  - **By July 2026, reporting cites 59 unpermitted turbines** — "nearly double" what
    xAI had earlier disclosed (MLQ News, https://mlq.ai/news/xai-ran-59-unpermitted-gas-turbines-at-colossus-2-double-what-it-disclosed/;
    corroborated by DataCenterDynamics, https://www.datacenterdynamics.com/en/news/xai-doubles-number-of-onsite-gas-turbines-at-memphis-data-center-in-violation-of-permit-limits/;
    and Technology.org, https://www.technology.org/2026/07/15/xai-59-unpermitted-gas-turbines-southaven-colossus-2/).
    Full text of the MLQ/DCD/Technology.org articles could not be fetched directly
    (blocked); figures are as reported in search-engine summaries of those articles,
    not independently confirmed against a primary document by me. Flagged in §6.
  - By August 2026, one headline cites **69 unpermitted turbines** and a **fourth**
    Memphis-area data center announced (Tech Times,
    https://www.techtimes.com/articles/322727/20260802/spacexai-keeps-69-unpermitted-turbines-until-july-2027-congress-demands-records.htm;
    MLQ, https://mlq.ai/news/musk-confirms-fourth-xai-data-center-in-memphis-as-69-unpermitted-turbines-face-removal/).
    **Not independently verified beyond search-result summaries — flag as
    lower-confidence, most-recent-and-least-checked figure.**

### 1.6 Current legal/procedural status (most recent confirmed)

- **June 17, 2025**: NAACP sent a Notice of Intent to sue over Colossus I (Memphis)
  turbines. (NOI letter, p. 3.)
- **July 2025**: SCHD issued the 15-turbine permit for Colossus I; NAACP and Young,
  Gifted and Green appealed it.
- **January 9, 2026**: EPA finalizes NSPS Subpart KKKKa (see §1.2).
- **January 16–20, 2026**: EPA statements/press coverage frame this as ruling against
  xAI's nonroad classification; xAI (per CNBC, via search summary) acknowledged
  27 unpermitted turbines at that point.
- **February 13, 2026**: NAACP/NAACP MS State Conference, via SELC + Earthjustice,
  send formal Notice of Intent to Sue over Colossus II/Southaven turbines (27 turbines,
  495 MW) — the document I read directly for this packet.
- **February 2, 2026**: SpaceX acquires xAI in an all-stock deal (~$1.25 trillion
  combined valuation) — cited as a footnote in the NOI letter itself (citing Reuters,
  Feb. 2, 2026). This matters because subsequent xAI actions are sometimes reported
  under "SpaceXAI."
- **March 10, 2026**: MDEQ issues the permanent PSD air permit for a planned 1.2 GW
  permanent power plant at the Southaven site — the permit that is meant to eventually
  replace the "temporary" turbines. (Per search-result summary of SELC press release,
  https://www.selc.org/press-release/groups-appeal-air-permit-for-xais-personal-power-plant-in-north-mississippi/.)
- **April 14–15, 2026**: NAACP formally sues xAI and MZX Tech in the U.S. District
  Court for the Northern District of Mississippi over the Southaven turbines
  (case reported as 3:26-cv-00074-MPM-JMV in one fetched Earthjustice summary — this
  case number could not be independently cross-verified against a second source and
  should be checked before print; flagged in §6). Groups separately appeal MDEQ's
  March 10 permanent-plant permit.
- **May 6, 2026**: NAACP/Earthjustice/SELC file a request for a preliminary injunction,
  alleging that after the Feb. 13 notice, xAI **added six more turbines** (27→33)
  instead of coming into compliance. Direct quotes (Earthjustice press release,
  https://earthjustice.org/press/2026/naacp-asks-court-for-emergency-action-to-stop-illegal-air-pollution-from-xais-data-center-power-plant):
  - Abre' Conner, NAACP Director of Environmental and Climate Justice: *"By expanding
    an unpermitted power plant despite decades of clear direction for permitting, xAI
    is showing blatant disregard for the law."*
  - Laura Thoms, Earthjustice: *"Rather than stop, they've added more turbines capable
    of inflicting even more harm to surrounding communities."*
  - Ben Grillot, SELC: *"Instead of fixing these issues, xAI installed six more massive
    turbines to its personal power plant."*
- **July 30–31, 2026**: MDEQ issues a retirement schedule for the "temporary" Southaven
  turbines — original deadline **December 31, 2026**, but MDEQ granted an extension
  allowing 13 turbines to keep running past that date, with 3 of those permitted to run
  up to 5 months longer (i.e., **to roughly July 2027**), because the planned permanent
  1.2 GW plant (41 permitted turbines) faces supply-chain delays.
  (Mississippi Today via search-result summary: https://mississippitoday.org/2026/07/31/southaven-xai-turbines-deadline/;
  corroborated by qz.com, https://qz.com/spacex-xai-unpermitted-turbines-removal-memphis-073126,
  and PC Gamer's reporting of xAI's own "we care deeply about being good neighbors"
  statement.) **Net effect: the "temporary" turbines that were exempted in July 2025 on
  the premise they'd run under 12 months are, under this schedule, still running
  roughly two years later.**
- A **DOJ involvement / "shields xAI"** story (Tech Times headline, July 15 2026,
  https://www.techtimes.com/articles/320526/20260715/xai-ran-59-unpermitted-gas-turbines-black-communities-doj-now-shields-them.htm)
  could **not be verified** — the page returned a 403 error on fetch and I was unable
  to locate independent corroboration of specific DOJ action from another outlet in the
  time available. **Do not use this claim without further direct verification** —
  flagged in §6.
- No confirmed dollar-figure fine, consent decree, or criminal referral was found as of
  the most recent sources reviewed (through early August 2026 per search results).
  Advocates are quoted expressing skepticism that "consequences will follow" — this is
  an opinion/prediction, not a confirmed enforcement outcome.

---

## 2. Community and environmental-justice context (real, sourced)

### 2.1 Location and community

- Colossus I sits adjacent to **Boxtown**, a historically Black neighborhood in
  southwest Memphis. Colossus II's data center is in **Whitehaven**, TN; its turbines
  are physically in **Southaven, MS** (DeSoto County), where the Census Bureau puts the
  population at **approximately 39% Black** (NOI letter, p. 4, citing U.S. Census
  Bureau QuickFacts, https://www.census.gov/quickfacts/fact/table/southavencitymississippi/INC110224).

### 2.2 Named organizations on record

- **NAACP** (national + Mississippi State Conference) — lead plaintiff/notice-sender,
  represented by **Southern Environmental Law Center (SELC)** and **Earthjustice**.
- **Young, Gifted and Green** — co-appellant on the Memphis permit appeal and named
  party in later Mississippi actions.
- **Memphis Community Against Pollution** and **Protect Our Aquifer** — named in the
  NOI letter as groups that "held and attended numerous large public meetings and town
  hall events, wrote hundreds of letters and public comments" opposing Colossus I's
  unpermitted turbines (NOI letter, p. 3).
- **Center of Engagement Environmental Justice and Health** — cited (per search-result
  summary of WREG/AOL reporting) alongside Memphis Community Against Pollution as
  having collected independent air-quality data "over the last four months" pointing
  to xAI and a nearby refinery as pollution sources. I was not able to fetch and read
  this underlying data/report directly — treat the specific findings as
  attorney/advocate characterizations pending direct verification (§6).

### 2.3 Emissions figures — as-claimed vs. as-measured (important distinction)

The **specific tonnage figures circulating in press and legal filings are "potential
to emit" estimates derived from manufacturer specifications and EPA's generic AP-42
emissions factors, not measured stack or ambient monitoring data.** This is stated
explicitly in the NOI letter's own footnotes (p. 9–10): the estimate of "significantly
more than 250 tons of NOx per year" is explicitly based on manufacturer-published
emissions rates, and the letter itself notes *"there exists no publicly available
documentation to confirm that the emission rates represented by xAI's consultant
reflect actual emissions."* This is a meaningful caveat a careful writer should
preserve — advocates' own filing says the actual figures could be **higher** than
claimed, not merely "high" per se, precisely **because no one has actually measured
them** absent a permit's monitoring requirements.

From the later, larger 33-turbine filing (May 2026), cited "potential to emit" figures
(sourced to "EPA 2020 National Emissions Inventory Data; PSD Air Permit documentation"
per the filing, as summarized):

| Pollutant | Annual potential | Cited health relevance |
|---|---|---|
| NOx | 2,508 tons | Smog-forming; alleged likely largest single industrial NOx source in the Memphis area |
| Fine particulate matter (PM2.5) | 236 tons | Premature death, cancer, asthma |
| Carbon monoxide | 837 tons | — |
| Formaldehyde | 25 tons | Classified a human carcinogen by HHS |

For scale, the NOI letter separately cites EPA's actual 2020 National Emissions
Inventory: the largest confirmed industrial NOx source in the 11-county Memphis
Metropolitan Statistical Area was Memphis International Airport (1,077 tons/year),
followed by the Draslovka/DuPont chemical plant (743 tons/year), Valero refinery
(342 tons/year), and the TVA Allen power plant (230 tons/year). By comparison, xAI's
**15 permitted** Colossus I turbines are permitted to emit **87.14 tons of NOx/year**
— i.e., the permitted, legal portion of Colossus I alone is a fraction of the airport's
total, but the unpermitted Southaven estimate (2,508 tons) would dwarf all of them if
accurate. (Source: NOI letter, p. 12, footnote 38, citing EPA's 2020 NEI Data,
https://www.epa.gov/air-emissions-inventories/2020-national-emissions-inventory-nei-data.)

### 2.4 Named individual quote (already verified per task, repeated for completeness)

- Patrick Anderson, SELC attorney: *"Every single time I've ever seen turbines
  anywhere, they have an air permit. So we are confused because we have not seen a
  public notice."* — Winbuzzer, Jan 20, 2026.

### 2.5 Health/cancer-risk data — what is and is not real

- A **real, peer-reviewed academic study** exists on air toxics in southwest Memphis:
  *"Air toxics concentrations, source identification, and health risks: an air
  pollution hot spot in southwest Memphis, TN,"* ScienceDirect,
  https://www.sciencedirect.com/science/article/abs/pii/S1352231013006948 (also at
  University of Memphis digital commons: https://digitalcommons.memphis.edu/facpubs/15789/).
  This study found a cumulative cancer risk from 13 monitored carcinogens in southwest
  Memphis of **2.3×10⁻⁴, described as roughly four times the U.S. national-average
  benchmark of 5.0×10⁻⁵.**
- **Critical caveat the writer must preserve**: this study's underlying monitoring data
  is from **2008–2010** — years before xAI existed or Colossus I was built (announced
  2024). **The "4x cancer risk" figure describes a pre-existing, decades-old
  industrial-pollution burden in southwest Memphis (steel, refining, food processing,
  fossil-fuel combustion, heavy mobile-source traffic), not a measured effect of xAI's
  turbines specifically.** Multiple press pieces (e.g., the widely echoed line "cancer
  rates run four times the national average" in reporting on the EPA ruling) cite this
  figure in a way that could easily be misread as being about xAI's specific
  contribution. It should be presented as: *the neighborhood already carried this
  documented burden before xAI arrived, and xAI's unpermitted emissions are additive to
  it* — not as evidence the turbines themselves caused this specific ratio.
- On whether xAI's turbines specifically have measurably changed air quality: search
  results turned up a Sept. 2025 academic/journalistic air-quality analysis
  (headlined, across multiple outlets, "Air quality analysis reveals minimal changes
  after xAI data center opens in pollution-burdened Memphis neighborhood" — phys.org,
  https://phys.org/news/2025-09-air-quality-analysis-reveals-minimal.html; Space.com;
  Inkl) using **satellite data on fine-particle pollution before/after turbine
  operation began.** I was not able to fetch and read this study/article's full text
  directly; I can confirm only the headline finding as reported: **"minimal changes"**
  detected via this specific method. This is in tension with alarm-framed coverage
  and should be presented honestly as a genuine complicating data point, not omitted.
  Separately, the City of Memphis conducted its own independent air-quality testing and
  reported (per search-summary of local coverage) **"no dangerous levels of air
  pollutants"** for benzene, toluene, formaldehyde, NO2, SO2, CO, and particulate
  matter. Environmental groups dispute the adequacy of the city's testing methodology,
  but I could not verify the specifics of that methodological dispute directly — flag
  in §6.
- Two real, sourced structural/comparative indicators (not xAI-specific, but real and
  relevant background):
  - Shelby County, TN and DeSoto County, MS both received an **"F" grade for ozone
    pollution from the American Lung Association** (2024/2025 "State of the Air"
    report), https://www.lung.org/research/sota/city-rankings/states/tennessee/shelby
    and https://www.lung.org/research/sota/city-rankings/states/mississippi/desoto.
    DeSoto County was the only Mississippi county to receive an "F."
  - Memphis was named an **"asthma capital"** by the Asthma and Allergy Foundation of
    America, 2024 rankings, https://aafa.org/wp-content/uploads/2024/09/aafa-2024-asthma-capitals-report.pdf.

---

## 3. Second real case — same mechanism, different domain

**Case found and verified: EPA's "glider kit" truck loophole (2016–2018+), under the
Clean Air Act's definition of "new motor vehicle."**

### Mechanism match
The Clean Air Act's heavy-duty truck emissions program regulates **"new motor
vehicles"** and "new motor vehicle engines" (CAA §216(3)). A "glider kit" is a brand-new
truck chassis, cab, transmission, and axle, into which manufacturers installed an
**older, salvaged, remanufactured diesel engine** — often 10–15+ years old, built to a
much looser emissions standard than current models. Under one legal reading, because
the *engine itself* was not newly manufactured (only remanufactured/reused), the
resulting vehicle could be argued not to be a "new motor vehicle" or "new motor vehicle
engine" under the statute's literal terms — even though, functionally, it was a
brand-new truck, freshly assembled, sold as new, and driven on the road exactly like
any other new heavy truck, just emitting pollution at old-engine levels. This is the
same shape as the turbine case: **a category (new vs. not-new) satisfied by a narrow
formal criterion (was a new engine block manufactured) that has little to do with the
functional reality the category exists to regulate (is this a newly operating vehicle
polluting the road today).**

### Verified facts and sourcing
- EPA's own data, cited across multiple outlets: glider trucks emit roughly **20–40
  times more NOx and particulate matter** than a comparable new diesel engine; one
  source (PopSci, https://www.popsci.com/glider-trucks-pollution-loophole/) cites an
  estimate of **~55 times more soot/fine-particle pollution**.
- Glider production grew from a few hundred per year in 2004 to **approximately
  10,000 per year by 2015** (Congressional Research Service report R45286,
  https://www.congress.gov/crs_external_products/R/PDF/R45286/R45286.7.pdf; mirrored at
  https://www.everycrsreport.com/reports/R45286.html), after EPA's Phase 1 greenhouse-
  gas standards for trucks took effect and created a cost incentive to buy exempt
  gliders instead.
- EPA under the Obama administration finalized a rule in 2016 requiring glider vehicles
  to meet emissions standards based on the year of assembly (not the engine's original
  manufacture year) — closing the loophole.
- On **November 16, 2017**, EPA under Administrator Scott Pruitt **proposed to repeal**
  that 2016 rule, explicitly proposing an interpretation under which glider vehicles/
  engines/kits would **not** be treated as "new motor vehicles," "new motor vehicle
  engines," or "incomplete new motor vehicles" under CAA §216(3) — i.e., proposing to
  make the form-over-function reading official policy. Primary source: Federal
  Register, https://www.federalregister.gov/documents/2017/11/16/2017-24884/repeal-of-emission-requirements-for-glider-vehicles-glider-engines-and-glider-kits.
  Comment period closed Jan. 5, 2018.
- The repeal became bogged down in litigation and internal EPA/OMB disputes over
  whether Pruitt's office had relied on a manufacturer-funded (Fitzgerald Glider
  Kits–funded) emissions study; the rule was never fully finalized as proposed, and
  glider manufacturers eventually wound down the business as later GHG Phase 2
  standards made it commercially unviable (Trucking industry press, TTNews,
  https://www.ttnews.com/articles/glider-truck-gone-not-forgotten; Overdrive,
  https://www.overdriveonline.com/equipment/article/14898497/emissions-regulations-squash-glider-kit-market).

This is a strong, well-documented, cross-domain match: a literal statutory/category
test (was a "new" engine manufactured) diverging sharply from the functional reality
the law was meant to govern (is this vehicle newly polluting the road) — with an
identifiable industry beneficiary and an EPA leadership fight over whether to formalize
the loophole, closely paralleling the tension found in §1.2 above (EPA simultaneously
narrowing and preserving a nonroad exemption for turbines).

I did not find a comparably strong, verifiable **second** candidate among the other
possibilities suggested in the task (mobile-home tax/zoning reclassification,
"temporary structure" building-code carve-outs, food/supplement tax categories) within
the research time available — those were not run down in depth and should be treated
as unexplored, not as ruled out.

---

## 4. Intentionality: deliberate gaming vs. genuine regulatory ambiguity

**Best-supported answer: this looks like deliberate, informed reliance on a real
regulatory ambiguity — not proof of a scheme to defraud, but also not an innocent
surprise.** Evidence, cited precisely, with the limits of what it proves:

**Evidence supporting deliberate/informed reliance:**
1. xAI's own senior infrastructure manager stated, when planning Colossus II, that xAI
   would be **"copying and pasting"** what it did at Colossus I — i.e., explicitly
   reusing the same unpermitted-turbine approach a second time, at a second site, after
   already having faced public controversy and a Notice of Intent to sue over the first
   one. Source: Memphis Commercial Appeal, July 15, 2025, cited in the NOI letter, p. 3
   n.6, https://www.commercialappeal.com (specific article: "xAI offical updates
   Colossus 2 plans in Memphis, but not how site will be powered").
2. In a July 25, 2025 email to MDEQ (quoted directly in the NOI letter, p. 4), xAI's
   Brent Mayo told the agency the company's plan was to bring "temporary turbines on
   site to be used prior to receiving the air permit," and that in xAI's own view this
   strategy was **"allowed."** This shows xAI proactively asserted the classification
   as a legal position, in writing, before deploying — i.e., not a mistake discovered
   after the fact, but a stated strategy.
3. After the Feb. 13, 2026 formal Notice of Intent to Sue, xAI's response was to **add
   six more turbines (27→33)** rather than pause or seek a permit — cited by NAACP,
   Earthjustice, and SELC attorneys as evidence of "blatant disregard for the law"
   (quotes in §1.6 above).
4. Turbine counts were **not proactively disclosed** to the regulator or the public at
   each increase; MDEQ had to request updates, and even then, per one filing, MDEQ told
   xAI it **did not need to notify the agency** when adding more turbines under the
   "temporary-mobile" designation — suggesting the growth pattern was, at minimum,
   something the state regulator chose not to police closely.

**Evidence complicating a "pure scheme" reading (genuine ambiguity was real):**
1. **The classification was not xAI's invention — a state regulator (MDEQ) put the
   "mobile + temporary <12 months" test in writing** as its own official determination
   (§1.4). Whatever xAI's intent, the agency responsible for enforcing the law
   endorsed the classification in writing before enforcement action followed.
2. EPA's own new rule (§1.2), finalized after this controversy, **did not simply
   declare the practice illegal outright** — it wrote an entirely new formal category
   ("stationary temporary combustion turbine," 24-month clock, lighter emissions
   standard) to give a legitimate, bounded version of exactly what xAI was attempting.
   If EPA felt the pre-existing rule already clearly prohibited what xAI did, writing
   a whole new accommodating category would have been a strange next move — this
   suggests genuine, agency-acknowledged ambiguity in how the pre-existing nonroad
   engine rule applied to large, grid-scale, semi-mobile turbines, not merely industry
   spin.
3. I found **no evidence of turbines being physically relocated between sites,
   swapped, or administratively re-designated specifically to "reset a compliance
   clock."** This was floated as an unverified hypothesis in this project's own
   disturbance card (design-tech.md, Card 2). Based on the primary documents I read,
   the actual documented pattern at Southaven is different: **continuous, incremental
   addition of new turbine units at the same site** (17→18→27→33→46→59+), not
   relocation of existing units. That is a meaningfully different mechanism from "moving
   equipment to dodge a clock," and the article should not assert the relocation/
   reset-the-clock version without new sourcing — see §6.
4. No source found alleges the "364-day" figure is a number xAI or MDEQ wrote into any
   agreement — the 12-month figure (not 364 days) is what appears in MDEQ's actual
   determination letter and in the codified federal nonroad-engine rule (§1.3).

**Bottom line for the writer:** the fairest, best-supported framing is that xAI
*identified and knowingly leaned on* a real, regulator-endorsed classification
ambiguity, escalated its use of that classification after being placed on formal legal
notice, and did so a second time at a second site after already facing controversy over
the first — which supports language like "knowingly exploited" or "repeated,
informed reliance on" a loophole. It does **not** currently support more specific claims
like "designed the turbines to be moved between sites to dodge a 12-month clock,"
which I could not verify and believe to be an inaccurate embellishment of what actually
happened (repeated *addition* of turbines, not *relocation* of them).

---

## 5. Source list (all URLs used above)

- Winbuzzer (Jan 20, 2026): https://winbuzzer.com/2026/01/20/epa-rules-xai-illegally-operated-gas-turbines-at-memphis-data-centers-closing-loophole-that-allowed-year-long-pollution-without-permits-xcxwbn/
- CNBC (Jan 16, 2026): https://www.cnbc.com/2026/01/16/musks-xai-faces-tougher-road-expanding-memphis-area-after-epa-update.html
- EPA NSPS Subpart KKKKa fact sheet (primary doc, read in full): https://www.epa.gov/system/files/documents/2026-01/correct_fact-sheet-nsps-stationary-combustion-turbines.pdf
- Federal Register, NSPS final rule (Jan 15, 2026): https://www.federalregister.gov/documents/2026/01/15/2026-00677/new-source-performance-standards-review-for-stationary-combustion-turbines-and-stationary-gas
- eCFR 40 CFR 1068.30 (nonroad engine definitions): https://www.ecfr.gov/current/title-40/chapter-I/subchapter-U/part-1068/subpart-A/section-1068.30
- eCFR 40 CFR 1068.31 (changing nonroad/stationary status): https://www.ecfr.gov/current/title-40/chapter-I/subchapter-U/part-1068/subpart-A/section-1068.31
- NAACP/SELC/Earthjustice Notice of Intent to Sue re: Southaven, MS (Feb. 13, 2026, primary doc, read in full): https://earthjustice.org/wp-content/uploads/2026/02/2026.02.13-final-xai-southaven-noi-with-exhibit-a.pdf
- Earthjustice press release, preliminary injunction request (May 2026): https://earthjustice.org/press/2026/naacp-asks-court-for-emergency-action-to-stop-illegal-air-pollution-from-xais-data-center-power-plant
- SELC, "xAI built an illegal power plant": https://www.selc.org/news/xai-built-an-illegal-power-plant-to-power-its-data-center/
- SELC, "Inside Memphis' fight against xAI": https://www.selc.org/news/inside-memphis-fight-against-xai/
- SELC, "EPA confirms that large methane gas turbines require permits": https://www.selc.org/press-release/epa-confirms-that-large-methane-gas-turbines-require-permits/
- SELC, appeal of Southaven permanent-plant permit: https://www.selc.org/press-release/groups-appeal-air-permit-for-xais-personal-power-plant-in-north-mississippi/
- SELC, "Resistance against Elon Musk's xAI facility in South Memphis gets stronger": https://www.selc.org/news/resistance-against-elon-musks-xai-facility-in-south-memphis-gets-stronger/
- NAACP: "NAACP Sues xAI for Illegal Pollution from Data Center Power Plant": https://naacp.org/articles/naacp-sues-xai-illegal-pollution-data-center-power-plant
- NAACP: "NAACP, SELC, Earthjustice threaten Lawsuit... in Mississippi": https://naacp.org/articles/naacp-selc-earthjustice-threaten-lawsuit-over-xais-unpermitted-gas-turbines-mississippi
- Tennessee Lookout, appeal brief: https://tennesseelookout.com/briefs/naacp-others-appeal-xai-turbine-permits-for-memphis-data-center/
- NAACP/YGG Memphis permit appeal (primary doc, not fetched in full): https://cdn.arstechnica.net/wp-content/uploads/2025/07/NAACP-and-YGGs-xAI-Air-Permit-Appeal-7-15-2025.pdf
- TechCrunch, 15 permits granted (July 3, 2025): https://techcrunch.com/2025/07/03/xai-gets-permits-for-15-natural-gas-generators-at-memphis-data-center
- MLQ News, 59-turbine report: https://mlq.ai/news/xai-ran-59-unpermitted-gas-turbines-at-colossus-2-double-what-it-disclosed/
- MLQ News, fourth data center / 69 turbines: https://mlq.ai/news/musk-confirms-fourth-xai-data-center-in-memphis-as-69-unpermitted-turbines-face-removal/
- DataCenterDynamics, doubled turbines: https://www.datacenterdynamics.com/en/news/xai-doubles-number-of-onsite-gas-turbines-at-memphis-data-center-in-violation-of-permit-limits/
- Technology.org, 59-turbine report: https://www.technology.org/2026/07/15/xai-59-unpermitted-gas-turbines-southaven-colossus-2/
- Tech Times, DOJ shielding claim (unverified, see §6): https://www.techtimes.com/articles/320526/20260715/xai-ran-59-unpermitted-gas-turbines-black-communities-doj-now-shields-them.htm
- Tech Times, 69 turbines / July 2027: https://www.techtimes.com/articles/322727/20260802/spacexai-keeps-69-unpermitted-turbines-until-july-2027-congress-demands-records.htm
- Mississippi Today, retirement deadline (July 31, 2026): https://mississippitoday.org/2026/07/31/southaven-xai-turbines-deadline/
- Mississippi Today, lawsuit filed (April 15, 2026): https://mississippitoday.org/2026/04/15/data-center-turbines-southaven/
- qz.com, turbine removal by July 2027: https://qz.com/spacex-xai-unpermitted-turbines-removal-memphis-073126
- Encino Environmental Services, loophole-closure summary: https://encinoenviron.com/epa-closes-permitting-loophole-used-by-ai-data-centers/
- Frantz Ward LLP, EPA considering mobile-source path for data centers (May 19, 2026): https://www.frantzward.com/epa-moving-to-regulate-data-center-turbines-as-mobile-sources/
- Air toxics/cancer-risk academic study (southwest Memphis, 2013): https://www.sciencedirect.com/science/article/abs/pii/S1352231013006948 and https://digitalcommons.memphis.edu/facpubs/15789/
- American Lung Association, Shelby County (TN) ozone grade: https://www.lung.org/research/sota/city-rankings/states/tennessee/shelby
- American Lung Association, DeSoto County (MS) ozone grade: https://www.lung.org/research/sota/city-rankings/states/mississippi/desoto
- Asthma and Allergy Foundation of America, 2024 Asthma Capitals report: https://aafa.org/wp-content/uploads/2024/09/aafa-2024-asthma-capitals-report.pdf
- phys.org, "minimal changes" air-quality analysis (Sept. 2025): https://phys.org/news/2025-09-air-quality-analysis-reveals-minimal.html
- U.S. Census Bureau QuickFacts, Southaven, MS: https://www.census.gov/quickfacts/fact/table/southavencitymississippi/INC110224
- Federal Register, glider kit repeal proposal (Nov. 16, 2017): https://www.federalregister.gov/documents/2017/11/16/2017-24884/repeal-of-emission-requirements-for-glider-vehicles-glider-engines-and-glider-kits
- Congressional Research Service, Glider Kit Regulations (R45286): https://www.congress.gov/crs_external_products/R/PDF/R45286/R45286.7.pdf / https://www.everycrsreport.com/reports/R45286.html
- PopSci, glider truck pollution: https://www.popsci.com/glider-trucks-pollution-loophole/
- ACEEE, glider manufacturers blog: https://www.aceee.org/blog/2018/07/epa-gives-glider-manufacturers-free
- TTNews, "The Glider Truck Is Gone, but Not Forgotten": https://www.ttnews.com/articles/glider-truck-gone-not-forgotten
- Overdrive, glider kit market squeeze: https://www.overdriveonline.com/equipment/article/14898497/emissions-regulations-squash-glider-kit-market

---

## 6. What I could NOT verify — flagged explicitly for the writer

1. **The "364-day" figure.** I could not find a codified regulation that literally
   specifies 364 days. The actual federal nonroad-engine rule (40 CFR 1068.30/.31)
   says **12 months**; the new NSPS turbine-specific "temporary" category (Subpart
   KKKKa) says **24 months**; MDEQ's letter to xAI says **less than 12 months.**
   "364 days" appears to be colloquial shorthand (from at least one letter referenced
   in search results) for "one day short of the 12-month trigger," not a distinct
   codified number. **Do not state "364 days" as if it is regulatory text.**

2. **DOJ "shielding" xAI from enforcement** (Tech Times headline, July 2026). Could not
   fetch the article (403 error) or find independent corroboration elsewhere in the
   time available. This is a significant claim (federal law-enforcement intervention on
   a company's behalf) that needs direct, primary verification before use — do not
   include in an article on the strength of a single blocked headline.

3. **Physical relocation of turbines between sites to "reset a compliance clock."**
   This was a hypothesis in the disturbance card that started this project. I found no
   supporting evidence; the documented pattern is continuous addition of new units at
   one site, not movement of existing units between sites. Treat the "reset the clock
   by moving equipment" framing as **unconfirmed and likely not what happened** —
   the real mechanism is closer to "kept adding units under an exemption granted for a
   small initial batch, without triggering fresh scrutiny at each addition."

4. **Exact case number and court details of the NAACP v. xAI/MZX Tech lawsuit**
   (cited in one source as 3:26-cv-00074-MPM-JMV, N.D. Miss.). Only one source for this
   case number was fetched; not independently cross-checked against PACER or a second
   news source. Verify before print.

5. **Whether SCHD's board actually dismissed the Memphis (Colossus I) permit appeals as
   moot**, and on what date/reasoning. This came from a search-engine summary of
   coverage I could not fetch directly (blocked or not re-verified against a primary
   board order/minutes).

6. **The exact document/context for the EPA quote** *"Historically, however, the EPA
   has not regulated combustion turbines, even those that may be portable, as nonroad
   engines, but rather as stationary sources."* This phrase is repeated identically
   across multiple secondary sources but I could not pin it to a specific named EPA
   document (preamble, applicability determination, comment-response document, or
   public statement) via direct fetch. Attribute cautiously ("EPA has stated..." rather
   than naming a specific letter) unless the exact source document is located.

7. **The Memphis Community Against Pollution / Center of Engagement Environmental
   Justice and Health independent air-quality monitoring data** referenced in WREG/AOL
   coverage. I was not able to fetch and review the underlying dataset or report
   directly — treat the "toxic air" characterization as an advocacy-group claim
   pending direct review of their data.

8. **Turbine counts for July–August 2026 (46, 59, 69)** are sourced only from
   search-engine summaries of MLQ News, DataCenterDynamics, Technology.org, and Tech
   Times articles that could not be fetched in full (blocked or not attempted in full).
   These are very likely directionally accurate (all outlets independently report
   escalating counts in the same range) but exact figures should be re-confirmed
   against at least one full-text primary or news source before being printed as
   precise numbers.

9. **No confirmed EPA fine, penalty, or consent decree amount** was found for either
   site as of the most recent sources reviewed. If the article implies a concrete
   punishment has been imposed, that would be unsupported by what I found — the record
   through mid-2026 shows enforcement pressure (lawsuits, notices, a preliminary
   injunction request) but no confirmed monetary penalty or criminal action.
