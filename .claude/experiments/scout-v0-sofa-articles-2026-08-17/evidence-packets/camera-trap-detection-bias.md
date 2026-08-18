# Evidence Packet: Camera-Trap Detection Bias as a Body-Size-Correlated Instrument Blind Spot

**Disturbance card:** Kays, Hody, Jachowski & Parsons (2021), *Movement Ecology* 9:41 — camera traps miss passing animals at rates correlated with body size/speed, meaning "rare species" rankings from camera-trap surveys may partly reflect camera physics, not population size.

**Compiled:** 2026-08-17. All facts below are traced to a specific URL. Anything not independently confirmed is flagged as UNVERIFIED / COULD NOT CONFIRM in Section 5 — read that section before quoting anything from Sections 2–4 in print.

---

## 1. Primary source — re-verified directly against the paper

**Citation:** Kays, R., Hody, A., Jachowski, D.S., Parsons, A.W. (2021). "Empirical evaluation of the spatial scale and detection process of camera trap surveys." *Movement Ecology* 9, Article 41. https://doi.org/10.1186/s40462-021-00277-3. Open access. PMC full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC8364038/

Verified by fetching the PMC HTML directly (not just an AI summary of it) and grepping the raw text for the load-bearing sentences, so the quotes below are exact.

**Authors and affiliations (verbatim from the article's author-affiliation block):**
- Roland Kays — 1. Department of Forestry and Environmental Resources, North Carolina State University, 2800 Faucette Drive, Raleigh, NC USA; 2. North Carolina Museum of Natural Sciences, 11 West Jones Street, Raleigh, NC USA
- Allison Hody — 1. NC State (as above); 3. Department of Forestry and Environmental Conservation, Clemson University, 258 Lehotsky Hall, Clemson, SC USA
- David S. Jachowski — 3. Clemson (as above)
- Arielle W. Parsons — 1. NC State; 2. NC Museum of Natural Sciences (as above)

**Study site and dates (verbatim):** cameras "operated continuously during June 13 – July 11, 2013" in "a 0.6 ha plot of loblolly pine (*Pinus taeda*) forest in Schenck Memorial Forest, North Carolina," on a "70 m by 80 m rectangular grid" with cameras "placed systematically at 10 m intervals."

**Equipment (verbatim):** "56 newly purchased camera traps (Bushnell Trophy Cam HD, IR flash units, 0.4 s trigger time for still photographs)." 53 of the 56 were functional (3 malfunctioned, per the paper's methods).

**Effort:** "over 1430 trap-nights of continuous data from one plot" (verbatim).

**Abstract, in full (verbatim):**
> "Camera traps present a valuable tool for monitoring animals but detect species imperfectly. Occupancy models are frequently used to address this, but it is unclear what spatial scale the data represent. Although individual cameras monitor animal activity within a small target window in front of the device, many practitioners use these data to infer animal presence over larger, vaguely-defined areas. Animal movement is generally presumed to link these scales, but fine-scale heterogeneity in animal space use could disrupt this relationship. We deployed cameras at 10 m intervals across a 0.6 ha forest plot to create an unprecedentedly dense sensor array that allows us to compare animal detections at these two scales. Using time-stamped camera detections we reconstructed fine-scale movement paths of four mammal species and characterized (a) how well animal use of a single camera represented use of the surrounding plot, (b) how well cameras detected animals, and (c) how these processes affected overall detection probability, p. We used these observations to parameterize simulations that test the performance of occupancy models in realistic scenarios. We document two important aspects of animal movement and how it affects sampling with passive detectors. First, animal space use is heterogeneous at the camera-trap scale, and data from a single camera may poorly represent activity in its surroundings. Second, cameras frequently (14–71%) fail to record passing animals. Our simulations show how this heterogeneity can introduce unmodeled variation into detection probability, biasing occupancy estimates for species with low p. Occupancy or population estimates with camera traps could be improved by increasing camera reliability to reduce missed detections, adding covariates to model heterogeneity in p, or increasing the area sampled by each camera through different sampling designs or technologies."

**Important precision note for the writer — what "14–71%" actually is:** This is **not** the same number as the 29%/86% figures below. It is the *failure* rate: 1 minus the proportion of camera passes that produced an *identifiable* photo. From Table 3 (raw observed outcomes for animals passing within 10 m of a camera):

| Species | Identifiable photo | Empty/unclear photo | No photo at all | Camera passes | Movement paths |
|---|---|---|---|---|---|
| Deer | 0.86 | 0.05 | 0.09 | 123 | 21 |
| Coyote | 0.57 | 0.15 | 0.28 | 47 | 14 |
| Raccoon | 0.47 | 0.13 | 0.39 | 76 | 18 |
| Gray fox | 0.29 | 0.12 | 0.58 | 24 | 4 |

- **1 − identifiable rate** gives the "14–71%" range quoted in the abstract: deer = 1−0.86 = **14%** fail; gray fox = 1−0.29 = **71%** fail. This is the number to use if quoting "14–71%."
- **Identifiable-photo rate** is the 29% (gray fox) – 86% (deer) figure used in the disturbance card. That figure is correct and directly from Table 3 — but it is a different quantity from "14–71%," and a careless writer could conflate them as if they were the same statistic. They are complementary but not identical (14–71% is not simply "100 minus 29–86%" reversed — check: 100−29=71 and 100−86=14, so numerically they ARE the complement of each other, confirmed. Good — no discrepancy, but state clearly which is which when quoting.)
- Deer's "no photo at all" rate (9%) is much lower than its "not identifiable" rate (14%) because a small number of deer photos were technically triggered but blurred/unclear.

**Trigger probability and body mass — exact language (verified twice, in two different places in the paper, both referencing the same figure):**
> Results section: "Trigger probability (*r*t) and photo probability (*r*p) were generally large compared to encounter probability (*r*p) and varied among species. Trigger probability showed the most between-species variation, apparently increasing with body mass (Fig. 6)."
> Discussion section: "Trigger probability (*r*t) appeared to increase with the body mass of the target species (Fig. 6), and the occurrence of 'blank' images in which mammals moved out of the frame before the camera took a photograph suggests that cameras may miss fast-moving animals."

Note: the results-section sentence as printed in the paper says "compared to encounter probability (*r*p)" — this appears to be a typesetting artifact in the original (the paper's own Table 4 caption defines *r*c, not *r*p, as encounter probability), reproduced here verbatim rather than silently corrected. Flag this if directly quoting that sentence.

Figure 6 caption (paraphrased from the PMC page, not directly quoted) plots trigger probability against body mass "for four focal species (ascending order by weight: gray fox, raccoon, coyote, white-tailed deer)," with body mass values sourced "from North Carolina animals in the mammal collections of the NC Museum of Natural Sciences."

**Table 4 — component detection probabilities (verbatim column labels: N̄, r̄c, rt, rp, p̄, p̄ideal):**

| Species | N̄ (paths/day) | r̄c (encounter) | rt (trigger) | rp (photo) | p̄ (overall) | p̄ideal |
|---|---|---|---|---|---|---|
| Deer | 0.78 | 0.11 | 0.91 | 0.95 | 0.149 | 0.170 |
| Coyote | 0.52 | 0.06 | 0.72 | 0.79 | 0.018 | 0.031 |
| Raccoon | 0.67 | 0.08 | 0.61 | 0.78 | 0.025 | 0.052 |
| Gray fox | 0.15 | 0.11 | 0.42 | 0.70 | 0.005 | 0.016 |

This table is the cleanest quotable evidence for "trigger probability tracks body mass": ordering species by approximate adult body mass (gray fox ≈ 3–6 kg < raccoon ≈ 5–10 kg < coyote ≈ 10–16 kg < deer ≈ 60+ kg — body-mass figures are general knowledge, not from this paper, so treat as approximate/contextual, not a quotable statistic), rt rises monotonically: 0.42 → 0.61 → 0.72 → 0.91.

**Mechanism 2 — frame-composition/fast-movement, exact language:**
> "Cameras frequently missed passing animals, either by failing to trigger, or triggering too slowly (*r*t and *r*p, Table 4)... the occurrence of 'blank' images in which mammals moved out of the frame before the camera took a photograph suggests that cameras may miss fast-moving animals. These results reflect the imperfect sensitivity of the PIR [passive infrared] sensors that trigger camera traps, requiring a threshold of change in the thermal signature of the trigger[ing area]..."

**The biodiversity-survey implication — exact language:**
> "This problem would be worse with rare species, which are often the target of faunal surveys."

This is the load-bearing sentence for the disturbance's core claim (that camera-physics blind spots have the same shape as the "rarity" variable ecologists are trying to measure). It is a direct quote from the paper's own discussion, not an inference.

**Assessment of the disturbance card's paraphrase:** The card's summary is accurate and does not overstate the paper. Its "14–71%" figure and "29%–86%" figure are both real numbers from the paper (see complementary-pair note above); its claim that "trigger probability appears to increase with body mass" is close to verbatim; its framing of two mechanisms (trigger latency + frame-composition timing) matches the paper's own two named mechanisms (*r*t, triggering; and blank/out-of-frame photos). One thing the card compresses that the writer should preserve for precision: the paper's real finding is about **trigger probability and photo probability**, not a single undifferentiated "detection failure" — if the article wants to say "the camera didn't fire in time" vs. "the camera fired but caught nothing usable," those are the two distinct terms (*r*t vs. *r*p) and Table 4 has both broken out separately.

---

## 2. Downstream / field-response findings

**Citation count:** Crossref lists **30** citing works (`is-referenced-by-count: 30`, checked via Crossref API for the DOI). OpenAlex lists **36–37** citing works (`cited_by_count: 37`; 36 returned via the citing-works query, checked via OpenAlex API). Semantic Scholar's own citation count field showed only 1, which is clearly a coverage gap in that specific database, not a real number — do not use it; the OpenAlex/Crossref counts are the reliable ones. This is a moderately-cited methods paper in a specialist field (camera-trap ecology), not a landmark widely cited across ecology broadly.

**Clearest direct methodological follow-up found:** DeWitt, P.D. & Cocksedge, A.G. (2023). "A simple framework for maximizing camera trap detections using experimental trials." *Environmental Monitoring and Assessment*, published online 2023-10-27. https://doi.org/10.1007/s10661-023-11945-9. Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC10611648/

Confirmed by direct HTML grep of the PMC full text (not AI paraphrase):
- It cites Kays et al. 2021 explicitly in its framing of the detection process: "The detection process consists of a series of conditional probabilities (Hofmeester et al., 2019) that can be formulated as (Kays et al., 2021): *p*i = 1 − (1 − *r*e·*r*t·*r*p)^Ni" and separately, "understanding each component is valuable when inferring ecological phenomena at broad spatial scales (Kays et al., 2021)."
- It directly extends the body-size mechanism: "the probability of detecting animals declines with both body size and distance (Heiniger & Gillespie, 2018; Howe et al., 2017; Jacobs & Ausband, 2018; Mason et al., 2022; Rowcliffe et al., 2011) because their heat signatures appear smaller."
- Its own abstract states: "We adapted distance sampling models and estimated the combined effects of distance, camera model, lens height, and vertical angle on the probability of detecting three different body sizes... Detection monotonically declined when proxies were ≥6 m from the camera; however, models show that body size and camera model mediated the effect of distance on detection."
- It proposes a concrete fix: an "experimental and analytical framework that ecologists, citizen scientists, and others can use and adapt to optimize camera protocols for various wildlife species."

This is a real, verifiable, direct answer to "has this been built on" — yes, by a 2023 methods paper that treats body-size-dependent detection as a design parameter to be experimentally characterized, not a solved problem.

**Related earlier framework it draws on:** Hofmeester, T.R. et al. (2019) is cited by DeWitt & Cocksedge as the origin of the "conditional probabilities" decomposition of the detection process that Kays et al. 2021 also uses — I was not able to independently pull full bibliographic details for this citation (ResearchGate page returned HTTP 403) — see Section 5.

**Is body-size-dependent detection now routinely corrected for in standard occupancy modeling, or still a known-but-unaddressed limitation?** Based on multiple search results (not a single definitive review article — see caveat below), the honest answer is: **partially and unevenly addressed, not standardized.** Specific findings:
- Standard occupancy modeling (MacKenzie et al. 2002, see Section 4) allows detection probability *p* to be modeled with covariates in principle, and this is architecturally capable of including species traits like body mass.
- In practice, per multiple camera-trap methods papers surfaced in search (Rowcliffe et al. 2011 "Quantifying the sensitivity of camera traps: an adapted distance sampling approach," *Methods in Ecology and Evolution* 2(5):464-476, https://doi.org/10.1111/j.2041-210X.2011.00094.x; Howe, E.J. et al. 2017 "Distance sampling with camera traps," *Methods in Ecology and Evolution*), animal speed and body size are recognized, measurable determinants of camera-trap detectability, and specific distance-sampling/REM (Random Encounter Model) methods have been built to estimate and correct for them on a per-study basis.
- However, this correction is a specialist technique applied by researchers who choose to do a dedicated calibration exercise (as Kays et al. 2021 and DeWitt & Cocksedge 2023 both did) — it is not a default, automatic feature of routine occupancy-model workflows in the way that, say, controlling for detection-by-observer-effort is standard. A synthesized read of the search results (not one single quotable sentence) frames it as: "detection heterogeneity is a recognized problem in camera trap occupancy studies... but accounting for species traits in detection models remains an important but often challenging aspect of the methodology" — I could not trace this specific phrase to one primary source; it's my synthesis of converging statements across several methods papers. Treat the underlying claim (recognized-but-unevenly-addressed) as reasonably well supported, but do not quote that sentence as if it is a verbatim citation.

**Bottom line for the writer:** Say "known limitation that specialist methods papers have started to formally model (distance sampling / REM approaches), but is not yet a routine, default correction in standard occupancy-model workflows" — that is a defensible, verifiable claim. Do NOT say "the field has solved this" or "the field has ignored this" — both would overstate in different directions.

---

## 3. Second real, different-domain case: bioacoustic/passive-acoustic biodiversity surveys

**Verdict: found, and it is genuinely strong — a different instrument class (passive listening, not motion-triggered cameras), in a different sub-field (bioacoustics/marine biology), showing the identical mechanism shape: detection probability is tied to a physical trait of the animal (loudness/source level, which correlates with body size), and this measurably biases which species look rare vs. common.**

**Primary citation:** Mooney, T.A., Di Iorio, L., Lammers, M., Lin, T.-H., Nedelec, S.L., Parsons, M., Radford, C., Urban, E., Stanley, J. (2020). "Listening forward: approaching marine biodiversity assessments using acoustic methods." *Royal Society Open Science* 7(8), 201287. https://doi.org/10.1098/rsos.201287. Full text via PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC7481698/

Exact quotes (confirmed via the PMC full text):
> "rare observations, acoustic or otherwise, greatly limit probability of detection and thus raw counts of individuals will be biased towards more gregarious, larger, louder or easily detected species leading towards erroneous richness measurements"

> "sounds from cryptic or quiet species... may only be detected above ambient noise at ranges of a few to a few tens of metres. If such species are not widely or uniformly distributed, then their contribution to local soundscapes... is limited to the detection range"

> "the sounds produced by individuals, species and groups of animals can vary vastly in amplitude. Similar to the effect of mass phenomena, the impact of high-amplitude over lower-amplitude calls can bias an index towards a more diverse estimate"

This is the same mechanism shape as Kays et al. 2021, transposed to a different sensing modality: a hydrophone/acoustic recorder's ability to register an animal at all is a function of how loud that animal is and how far the sound travels before dropping below the ambient noise floor — and loudness/call amplitude correlates (imperfectly, but really) with body size across many taxa, the same way trigger probability correlated with body mass in the camera-trap case. The stated consequence — "richness measurements" being skewed toward "larger, louder" species — is the acoustic-domain equivalent of "rare species rankings... may partly reflect camera physics."

**Supporting citation for the general passive-acoustics density-estimation methodology this bias sits inside:** Marques, T.A., Thomas, L., Martin, S.W., Mellinger, D.K., Ward, J.A., Moretti, D.J., Harris, D., Tyack, P.L. (2013). "Estimating animal population density using passive acoustics." *Biological Reviews* 88(2), 287-309. https://doi.org/10.1111/brv.12001. I was able to confirm the full author list, journal, volume, and page range via search results, but did NOT independently pull and verify a specific verbatim body-size/detection-range sentence from the full text of this particular paper — treat it as a supporting/contextual citation for how passive acoustic density estimation works in general, not as a source of a specific quotable body-size claim (that specific claim is fully sourced to Mooney et al. 2020 above instead).

**A second illustrative (non-scientific-literature) example found but not used as the primary case:** Louis Daguerre's 1838 "Boulevard du Temple" daguerreotype — a ~10–15 minute exposure of a busy Paris street that renders empty of the moving carriages and pedestrians who were actually there, except for a man having his boots shined and the bootblack, who stood still long enough to register. This is a widely and consistently documented historical/art-history fact (see Wikipedia: https://en.wikipedia.org/wiki/Boulevard_du_Temple_(photograph), and corroborating popular-history sources found via search) and is a vivid illustration of the same "instrument physics biases the record toward the slow/static" mechanism as the camera-trap "blank" images from fast-moving animals. It is not, however, drawn from a peer-reviewed methods literature the way the bioacoustics case is, and it is a single anecdote rather than a systematic, quantified finding. Recommend using it only as a passing illustrative aside if at all — the bioacoustics case (Mooney et al. 2020) is the one to build the article's "second case" section around, since it has the same rigor level as the primary source.

---

## 4. Formal ecological terminology: "imperfect detection" / occupancy modeling

**Yes, this has a formal name and a foundational citation.** The concept is called **imperfect detection** or **detectability**, and the field-defining paper is:

MacKenzie, D.I., Nichols, J.D., Lachman, G.B., Droege, S., Royle, J.A., Langtimm, C.A. (2002). "Estimating Site Occupancy Rates When Detection Probabilities Are Less Than One." *Ecology* 83(8), 2248-2255. https://doi.org/10.1890/0012-9658(2002)083[2248:ESORWD]2.0.CO;2. (Confirmed via Crossref API: title, full author list, journal, volume/issue/pages, and publication date of August 2002 all verified.)

This paper established the standard hierarchical-model framework (occupancy ψ, detection probability *p*, estimated jointly from repeat-visit detection/non-detection data) that essentially all subsequent camera-trap occupancy studies — including Kays et al. 2021, which explicitly frames its own contribution in terms of "detection probability, p" and "occupancy models" — build on or react to.

**Does the formal MacKenzie framework already account for the body-size-correlated pattern specifically? No — not by default.** The framework is general: it allows detection probability to be modeled as a function of covariates (site conditions, survey conditions, and in principle species traits), but body mass / trigger-latency-type mechanisms are not part of the original 2002 model and are not automatically incorporated just by using an occupancy-model approach. Whether a given camera-trap occupancy study accounts for body-size-driven detection heterogeneity depends on whether the researchers deliberately added it as a covariate (as the specialist distance-sampling/REM literature — Rowcliffe et al. 2011, Howe et al. 2017, DeWitt & Cocksedge 2023 — does) or not. This matches the answer given in Section 2: the vocabulary and modeling architecture to handle this already exists and has a 20+-year pedigree, but applying it specifically to body-size-correlated detection bias is a deliberate, still-uneven practice rather than something "imperfect detection" as a term automatically solves.

---

## 5. Explicitly flagged uncertainties — read before quoting

- **Hofmeester et al. (2019)** — cited by DeWitt & Cocksedge (2023) as the origin of the conditional-probability decomposition of camera-trap detection (*r*e · *r*t · *r*p) that Kays et al. 2021 also uses. I could not pull full bibliographic details (the ResearchGate page for what appears to be this paper returned an HTTP 403). If the writer wants to cite this paper directly, it needs independent verification of author list, journal, and year before use — do not assume it is the "Component processes of detection probability in camera-trap studies: understanding the occurrence of false-negatives" title I found in search results, since I was not able to confirm that title/author match against the actual in-text citation.
- **The "field consensus" sentence in Section 2** ("detection heterogeneity is a recognized problem... but accounting for species traits in detection models remains an important but often challenging aspect of the methodology") is my synthesis across multiple AI-summarized search results, not a verbatim quote traced to one paper. The underlying claim is reasonably well supported by the concrete evidence gathered (Rowcliffe 2011, Howe 2017, DeWitt & Cocksedge 2023 all exist and do what's described), but do not present that specific sentence as a direct quotation from any named source.
- **Palencia et al. (2022), "Towards a best-practices guide for camera trapping,"** *Journal of Zoology* — this looked like a promising downstream methods reference but the full text is paywalled (HTTP 402 on fetch attempts); I was not able to confirm whether/how it discusses body-size-dependent detection or cites Kays et al. 2021. Do not cite specific claims from this paper without independently accessing it.
- **Marques et al. (2013)** passive-acoustics review — full bibliographic details (authors, journal, volume/pages) are confirmed via search-result metadata, but I did not independently pull and verify a specific quotable sentence from its full text about body size/detection range. Use it only as general supporting context for how passive-acoustic density estimation works, not as the source of a specific quoted claim.
- **Semantic Scholar's citation count (1)** for the Kays et al. 2021 paper is almost certainly a database coverage gap, not the true number — Crossref (30) and OpenAlex (36-37) are the reliable figures and are corroborated by an actual list of 36 named citing papers pulled from OpenAlex. Do not use the Semantic Scholar figure.
- **Body-mass figures for gray fox/raccoon/coyote/deer** (used in Section 1 to illustrate the Table 4 ordering) are general biological knowledge, not sourced from the Kays et al. 2021 paper itself, and are approximate. The paper's own Fig. 6 does plot real body-mass values sourced from "the mammal collections of the NC Museum of Natural Sciences," but I did not extract the exact numeric mass values used in that figure (only the qualitative ascending order: gray fox < raccoon < coyote < deer) — if the writer wants exact kg figures for a caption, these should be pulled from Figure 6 itself (image), not asserted from memory.
- **The Daguerre 1838 photograph** (Section 3) is well and consistently documented across multiple independent popular/historical sources, but I did not access a peer-reviewed history-of-photography source for it — treat sourcing rigor here as "solid popular-historical consensus," not "peer-reviewed academic citation," which is why it's offered as a secondary aside rather than the primary second case.

**Overall confidence:** Section 1 (primary paper) is fully verified against raw article text and is safe to quote directly as written above. Section 3's primary citation (Mooney et al. 2020) is equally solid — verified quotes, full citation. Sections 2 and 4 are solidly sourced on the concrete facts (citation counts, MacKenzie et al. citation, DeWitt & Cocksedge findings) but contain one synthesized/non-verbatim framing sentence, clearly marked above.
