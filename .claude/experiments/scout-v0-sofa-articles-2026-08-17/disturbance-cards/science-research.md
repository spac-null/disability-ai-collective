# Disturbance Cards — Science & Research Reporting

5 cards. Category: science/research (non-disability). All fragments verbatim
or near-verbatim from the cited primary sources or their direct press coverage.

---

## CARD 1 — Soil carbon: the exclusion that produces the estimate

**SOURCE**: *SOIL* (Copernicus/EGU journal); Contreras et al., "Challenges in soil carbon modelling and measurement: a decade of experimental data vs. RothC simulations in an organic olive grove"
**URL / SOURCE ID**: https://soil.copernicus.org/articles/12/773/2026/ (DOI: 10.5194/soil-12-773-2026)
**DATE**: 2026

**EXACT DISTURBANCE FRAGMENT** (verbatim):
"biochar remains concentrated in discrete particles, making its quantification highly dependent on the specific location of soil sampling" and "the exclusion of these values may have influenced the final estimate of SOC accumulation." (RothC model fit for the biochar treatment: RMSE 19.44 Mg C ha⁻¹, R² = 0.10 — the worst of all treatments tested.)

**LOCAL CONTEXT**: A decade-long field trial compared measured soil organic carbon (SOC) against RothC model simulations across several amendment treatments in an olive grove; biochar was one of the treatments tested for long-term carbon storage.

**WHY THIS IS STRANGE**: The paper is measuring "how much carbon this treatment stored," but the treatment's own physical form — biochar sitting as discrete lumps rather than distributed evenly through soil — makes the measurement depend on exactly where you happen to stick the corer. The sampling method's blind spot and the material being measured are the same shape.

**WHAT THE SOURCE ITSELF SAYS IS HAPPENING**: Biochar's heterogeneous spatial distribution and concentrated carbon content introduce sampling uncertainty; some anomalous values were excluded from the final SOC accumulation estimate, and the RothC model still could not track the treatment well (lowest R² of any treatment).

**WHAT THAT EXPLANATION MAY FAIL TO EXPLAIN**: "Heterogeneity" describes why sampling is noisy, but doesn't establish which excluded values were errors and which were the real (if inconvenient) signal — i.e., whether the exclusion filtered out noise or filtered out the very lumps that store most of the carbon.

**POSSIBLE HIDDEN MECHANISM (hypothesis)**: If biochar carbon storage is genuinely dominated by a small number of dense, spatially rare particles, then *any* discrete-core sampling scheme will systematically undercount storage in "unlucky" plots and overcount it in "lucky" ones — meaning the reported average SOC for biochar treatments may be a sampling artifact more than a biological one, regardless of how outliers are handled.

**WHAT WOULD HAVE TO BE VERIFIED**:
- The actual number and magnitude of excluded values, and whether excluding them changed the sign or just the size of the treatment effect
- Whether a denser or exhaustive-excavation sampling scheme (impractical at scale) converges to a different mean than the sparse-coring method used
- Whether other labs studying biochar SOC report the same exclusion pattern

**WHAT WOULD MAKE THIS A BAD ARTICLE**: Framing it as "scientists don't know if biochar works" rather than "the standard way of measuring a lumpy substance may be structurally unable to measure it."

---

## CARD 2 — Ice cores from tropical mountains say the opposite of what the models say

**SOURCE**: *Communications Earth & Environment* (Nature Portfolio); Bao, Y. et al., Ohio State University / Byrd Polar and Climate Research Center
**URL / SOURCE ID**: https://www.nature.com/articles/s43247-025-02188-2 (verbatim text sourced via OSU press release: https://news.osu.edu/tropical-mountain-ice-cores-help-decipher-climate-riddles-in-earths-history/)
**DATE**: published April 25, 2025

**EXACT DISTURBANCE FRAGMENT** (verbatim): "Ice core data from tropical mountains like Kilimanjaro in Tanzania and Huascarán in Peru suggest possible cooling by 0.8 to 1.8 degrees Celsius, whereas models suggest a prolonged warming by 1.5 degrees." Lead author: "the model-data mismatch over tropical mountains presents a challenge for researchers in explaining the underlying causes of tropical mountain oxygen isotopic ratios."

**LOCAL CONTEXT**: Researchers compared Holocene-epoch (last ~11,700 years) climate model simulations against ice-core proxy records from Greenland, Antarctica, and tropical high-altitude sites. Polar sites match; tropical mountain sites do not.

**WHY THIS IS STRANGE**: This isn't a small discrepancy or noise — it's a sign flip. The physical archive says the mountain got colder over the Holocene; the model of the same period, driven by the same orbital forcing, says it got warmer. Both can't be describing the same climate history, yet both are treated as legitimate inputs to the same field.

**WHAT THE SOURCE ITSELF SAYS IS HAPPENING**: The paper proposes that models may be missing vegetation and land-use feedbacks, and that both temperature and precipitation jointly (not just temperature alone) drive the oxygen-isotope signal recorded in tropical mountain ice — meaning the proxy may not be a pure temperature thermometer at these sites.

**WHAT THAT EXPLANATION MAY FAIL TO EXPLAIN**: If the isotope record is actually tracking precipitation change more than temperature at these sites, that would mean decades of using tropical ice-core oxygen isotopes as a temperature proxy in other contexts could be systematically miscalibrated — a much bigger claim than "our model needs vegetation feedbacks," and the paper stops short of asserting it directly ("no single factor... could effectively explain these Holocene-era patterns").

**POSSIBLE HIDDEN MECHANISM (hypothesis)**: The isotope ratio at tropical high-altitude sites may respond primarily to shifts in moisture-source/convective regime (an atmospheric circulation signal) rather than local temperature — meaning the proxy and the model are each internally consistent but are answering different physical questions while being read as the same variable.

**WHAT WOULD HAVE TO BE VERIFIED**:
- Independent (non-isotope) paleo-temperature proxies at the same tropical sites (e.g., borehole thermometry, pollen) to see if they side with the model or the ice core
- Whether isotope-enabled models (which simulate the isotope signal directly rather than just temperature) close the gap
- Dating precision of the tropical cores versus the polar ones, to rule out a chronology artifact producing an apparent sign flip

**WHAT WOULD MAKE THIS A BAD ARTICLE**: "Scientists find climate models are wrong" — the actual finding is narrower and more interesting: a specific proxy may not mean what it's assumed to mean at a specific class of sites.

---

## CARD 3 — The camera fails exactly when the animal is present

**SOURCE**: *Movement Ecology*; Kays, R., Hody, A., Jachowski, D.S., Parsons, A.W., "Empirical evaluation of the spatial scale and detection process of camera trap surveys"
**URL / SOURCE ID**: https://doi.org/10.1186/s40462-021-00277-3 (PMC full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC8364038/)
**DATE**: published August 14, 2021

**EXACT DISTURBANCE FRAGMENT** (verbatim): Cameras "frequently (14–71%) fail to record passing animals." Failures split into "trigger failures ('no photos')" — "always more common than failures due to rapid animal movement ('empty photos')" — and animals that "moved out of frame before the image was taken; this was particularly true for smaller, faster moving species." "Trigger probability... apparently increasing with body mass." Detection rates ranged from 29% (gray foxes) to 86% (deer).

**LOCAL CONTEXT**: Camera traps are the standard tool for estimating wildlife occupancy and density; this study directly measured, rather than assumed, how often an animal that is genuinely in front of the camera fails to be recorded.

**WHY THIS IS STRANGE**: The instrument's failure rate is not random noise around the thing it measures — it is *correlated with the thing itself* (species body size, movement speed). A device meant to count how many foxes pass by fails to record foxes specifically because they are fox-sized and fox-fast, and succeeds more with deer because they are large and slow. The measurement's blind spot has the same shape as the ecological variable of interest.

**WHAT THE SOURCE ITSELF SAYS IS HAPPENING**: Two independent failure modes (motion-sensor trigger latency, and frame-composition timing) combine, and both are worse for small, fast animals, producing systematic undercounts for exactly the species least often surveyed by other means.

**WHAT THAT EXPLANATION MAY FAIL TO EXPLAIN**: Standard occupancy models treat detection probability as roughly constant per site/session; if detection probability instead varies continuously with each individual animal's size and gait, then community-level biodiversity comparisons (which species are "rare" vs. "common") partly reflect camera physics rather than population sizes — and the paper only estimates this correction for the specific species it directly measured, not the broader taxonomic range camera trap networks report on globally.

**POSSIBLE HIDDEN MECHANISM (hypothesis)**: Because the two failure modes (trigger latency, frame timing) both scale with speed/size in the same direction, their combined effect may be multiplicative rather than additive, meaning current statistical corrections — which usually treat detection as a single scalar probability — could be underestimating the undercount for the smallest, fastest species by more than either mechanism alone would suggest.

**WHAT WOULD HAVE TO BE VERIFIED**:
- Whether the multiplicative-vs-additive failure interaction has been tested directly (paired ground-truth video vs. camera-trap trigger data) for the smallest species
- Whether existing global camera-trap biodiversity datasets have ever been re-analyzed with body-size-dependent detection curves rather than per-site constants
- How much this shifts published "rarity" rankings for small mesocarnivores specifically

**WHAT WOULD MAKE THIS A BAD ARTICLE**: Reducing it to "camera traps miss small animals" (already well known) instead of the sharper point — the measurement error is patterned exactly like the variable being estimated, which is a different and harder problem than random noise.

---

## CARD 4 — The safe dose is real only for ten days

**SOURCE**: *Communications Biology* (Nature Portfolio); Tosi, S., Nieh, J.C., Brandt, A. et al., "Long-term field-realistic exposure to a next-generation pesticide, flupyradifurone, impairs honey bee behaviour and survival"
**URL / SOURCE ID**: https://doi.org/10.1038/s42003-021-02336-2 (PMC full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC8238954/)
**DATE**: published June 28, 2021

**EXACT DISTURBANCE FRAGMENT** (verbatim): "FPF impaired bee survival and behaviour at field-realistic doses (down to 11 ng/bee/day)... that were up to 101-fold lower than those reported by risk assessments (1110 ng/bee/day)." "FPF significantly increased the frequency of bees exhibiting abnormal behaviours... between 1–30 days." "These effects would not be measured with the standard 10-day trials recommended for official risk assessments."

**LOCAL CONTEXT**: A seven-laboratory, standardized ring-test in Europe and North America tested long-term (30-day+) field-realistic exposure of honey bees to flupyradifurone, a pesticide marketed partly on being safer for bees than neonicotinoids, and compared results against the regulatory reference dose.

**WHY THIS IS STRANGE**: The regulatory safety threshold was not wrong about the dose that harms bees — it was measuring the right dose, for the wrong duration. The pesticide's real toxicity threshold is 101-fold below the tested one, but only becomes visible after the regulatory clock has already stopped counting. Time, not concentration, is the axis the protocol got wrong.

**WHAT THE SOURCE ITSELF SAYS IS HAPPENING**: The abnormal behaviors and mortality effects emerged specifically in the 1–30 day window of chronic exposure — a period the standard 10-day acute risk-assessment trial never observes, so the effect exists in biological reality but not in the regulatory record.

**WHAT THAT EXPLANATION MAY FAIL TO EXPLAIN**: A 10-day cutoff is a bureaucratic convenience, not a biological boundary — nothing about bee physiology resets at day 10. The paper doesn't fully address why regulatory testing duration became fixed at a timescale shorter than the compound's demonstrated mechanism of harm, or whether other approved "bee-safe" pesticides share compounds with similarly delayed-onset chronic effects that would also be invisible to the same protocol.

**POSSIBLE HIDDEN MECHANISM (hypothesis)**: If flupyradifurone's toxicity depends on cumulative sublethal exposure crossing a physiological threshold (e.g., metabolic detoxification capacity being gradually exhausted) rather than a fixed per-day dose, then *any* chemical with a similar slow-accumulation mode of action will systematically pass current regulatory tests regardless of its true field-realistic risk, making the 10-day window a structural blind spot in the approval process rather than a one-off oversight for this molecule.

**WHAT WOULD HAVE TO BE VERIFIED**:
- Whether flupyradifurone's mechanism is genuinely cumulative/threshold-based versus simply requiring longer exposure to reach comparable tissue concentrations
- How many other currently-approved "reduced-risk" pesticides have been tested past day 10 at field-realistic doses
- Whether regulatory bodies have since revised trial duration requirements in response to this and related findings

**WHAT WOULD MAKE THIS A BAD ARTICLE**: "This pesticide is secretly dangerous" (already the headline angle used everywhere) instead of the more precise and generalizable point — the testing clock, not the testing dose, is where the protocol and the biology disagree.

---

## CARD 5 — The watch stops listening exactly when your heart has something to say

**SOURCE**: *JMIR Formative Research*; Davis-Wilson, H. et al., "Effects of Missing Data on Heart Rate Variability Measured From A Smartwatch: Exploratory Observational Study"
**URL / SOURCE ID**: https://doi.org/10.2196/53645 (full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC11894354/)
**DATE**: published February 24, 2025

**EXACT DISTURBANCE FRAGMENT** (verbatim): "smaller data gaps may be due to movement artifacts or device malfunction"; "larger bursts of missing data may be the result of noncompliance (ie, not wearing the Garmin watch)"; "we have limited labeling of HRV data. Future studies should include daily self-reported activity logs to determine when participants are sleeping, exercising, or not wearing their watch."

**LOCAL CONTEXT**: The study used consumer smartwatch photoplethysmography (PPG) to measure heart rate variability (HRV) continuously, then simulated increasing levels of missing data (10%–60% per 5-minute window) to see how much data loss the metric could tolerate before becoming unreliable.

**WHY THIS IS STRANGE**: HRV is most clinically informative during physiologically active states — exercise, stress, acute illness, sleep-stage transitions — which are exactly the states most likely to produce motion artifacts and signal loss on a PPG sensor. The device's failure mode is not independent of what it's trying to detect; it goes dark preferentially during the moments researchers most want it awake.

**WHAT THE SOURCE ITSELF SAYS IS HAPPENING**: Missing data arises from either brief movement artifacts or longer stretches of the device simply not being worn, and the researchers state plainly that they cannot currently tell which state (sleep, exercise, non-wear) corresponds to which gap because activity labeling wasn't collected.

**WHAT THAT EXPLANATION MAY FAIL TO EXPLAIN**: Without activity labels, the paper's own statistical thresholds for "how much missingness is tolerable" are themselves estimated from a dataset that can't distinguish "missing because nothing interesting was happening" from "missing because something very interesting (an arrhythmia, a stress spike) was happening" — meaning the tolerance thresholds may be systematically optimistic exactly where they'd matter most clinically.

**POSSIBLE HIDDEN MECHANISM (hypothesis)**: If motion-artifact-driven gaps cluster in time around high-intensity physiological events (matching the wearable literature on PPG accuracy degrading sharply under movement), then HRV missingness is not "missing at random" in the statistical sense the imputation methods typically assume — it is missing *because of* the value it would have taken, a much harder problem (informative/non-ignorable missingness) that simple interpolation cannot fix.

**WHAT WOULD HAVE TO BE VERIFIED**:
- Whether gap timing correlates with independently-logged activity/stress events in a labeled follow-up study
- Whether HRV values immediately before a gap trend toward extremes (a signature of informative missingness) versus staying near baseline
- Whether imputation-based HRV metrics used in downstream clinical or wellness applications have been validated against ground-truth ECG during exactly the missing-data-prone states

**WHAT WOULD MAKE THIS A BAD ARTICLE**: "Your smartwatch's health data is unreliable" (generic wearable skepticism) instead of the specific mechanism — a measurement gap that is not random but is patterned by the very physiology it exists to capture.
