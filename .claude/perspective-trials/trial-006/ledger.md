# Trial 006 — Frozen Ledger

Format follows `automation/new_engine_v1/ledger.py`: each fact has a
verbatim support_span quoted from the source, a claim_type from the
engine's taxonomy, and evidence_ids. No fact here was minted by
interpretation — see NOTE ON CAUSAL ARCHITECTURE below for one place a
looser earlier draft (`evidence.md`) blurred two separate facts together;
corrected here against the actual primary source.

## SOURCES

- **E1** — USGS, PAGER Scientific Background,
  earthquake.usgs.gov/data/pager/background.php (public agency page, read
  directly for verbatim text).
- **E2** — D.J. Wald, K.S. Jaiswal, K.D. Marano, D. Garcia, E. So, M.
  Hearne, "Impact-Based Earthquake Alerts with the U.S. Geological
  Survey's PAGER System: What's Next?", Proceedings of the 15th World
  Conference on Earthquake Engineering, Lisbon, 2012 (peer-reviewed
  conference paper, USGS authors; read directly in full from the primary
  PDF, iitk.ac.in/nicee/wcee/article/WCEE2012_0956.pdf).

## FACTS

**F01** [POSITIVE_FACT, E1] — "PAGER results are generally available
within 30 minutes of a significant earthquake."

**F02** [POSITIVE_FACT, E1] — "Demanding or awaiting observations or loss
estimates with a high level of accuracy may delay response and increase
the loss."

**F03** [POSITIVE_FACT, E1] — "Though PAGER uses simple and intuitive
color-coded alerting criteria, it preserves the necessary uncertainty
measures by which one can gauge the likelihood for the alert to be
over- or underestimated."

**F04** [POSITIVE_FACT, E1] — "Users of PAGER exposure estimates should
account for uncertainty and always seek the most current PAGER release
for any earthquake."

**F05** [POSITIVE_FACT, E2] — "We have instituted a review process for
PAGER alerting whereby initially 'green' and 'yellow' alerts run through
the system and alert automatically but the rare 'orange' or 'red' alerts
are initially embargoed (up to about 20 min) until source parameters
stabilize to the comfort level of the seismic expert on call."

**F06** [POSITIVE_FACT, E2] — "The review process can delay the initial
alert message, but we have found that a minor delay for very critical
events outweighs the increased potential for sending out a premature,
erroneous alert based on preliminary source parameters."

**F07** [POSITIVE_FACT, E2] — "While any such alert is pending, a
'pending' message goes to all critical users and on the web pages that
signals a 'heads up' -- that a potentially significant earthquake
occurred and is currently under manual review."

**F08** [POSITIVE_FACT, E2] — "One notable initial overestimation of
losses by PAGER was triggered by the 2011 M7.2 Van, Turkey, earthquake.
PAGER's initial alert (at 27 min) was 'red' for both fatalities and
economic losses. A day later, revised hazard inputs resulted in orange
and red alerts for fatalities and economic losses, consistent with
eventual losses."

**F09** [ATTRIBUTION, E2] — "We have learned that initial errors on the
side of under-prediction are preferable since a low magnitude will result
in an under-prediction and may not alert many recipients initially;
minutes later a upwardly-revised magnitude could up the alert level,
resulting in correct initial alerts to many recipients who are normally
no-worse off for a slightly delayed notification. On the other hand,
initial high-level alerts which are later revised downward can potential
initiate organizational response in the absence of non-collaborating
information or revised PAGER alerts." *(The PAGER team's own stated
general lesson/judgment — not a claim that this specifically happened in
the Van case; see note below.)*

**F10** [POSITIVE_FACT, E2] — "In contrast, initial rapid estimates
in-country (Kamer et al., 2012) proved more accurate, suggesting that
their better source information, prediction equations and inventory data
at a sub-country scale could indeed improve our more general country-wide
PAGER models."

**F11** [POSITIVE_FACT, E2] — "Development of the USGS PAGER system began
in 2005 after the 2004 Great (M9.1) Sumatra tsunami earthquake."

**F12** [POSITIVE_FACT, E2] — "In September 2010, the USGS began publicly
releasing earthquake alerts for significant earthquakes around the globe
based on estimates of potential casualties and economic losses with its
Prompt Assessment of Global Earthquakes for Response (PAGER) system."

**F13** [POSITIVE_FACT, E2] — "Alert levels are characterized by alerts of
green (little or no impact), yellow (regional impact and response), orange
(national-scale impact and response), and red (international response)."

**F14** [POSITIVE_FACT, E2] — "On the PAGER one-pager summary, each
individual alert level is based on the median loss estimate; uncertainty
in the alert level can be gauged by the histogram showing the likelihood
that adjacent alert levels (or loss/fatality ranges) occur."

## NOTE ON CAUSAL ARCHITECTURE (correcting `evidence.md`)

`evidence.md`, written before the primary paper was read in full, stated
that "organizations mobilized on an alert... revised a day later" as if
this were a documented consequence of the Van case specifically, and
implied the stability-review step (F05–F07) was added *because of* Van
(F08). Neither is what the primary source actually supports:

- F09 is the PAGER team's *general* stated professional judgment about a
  risk pattern across their whole experience ("can potential[ly]
  initiate organizational response") — it is not tied in the text to the
  Van event by name. Treating it as "what happened in Van" would be
  exactly the CHRONOLOGICAL_ADJACENCY-as-causation error the ledger
  system exists to catch.
- The paper presents the review process (F05–F07) in Section 2.3 and the
  Van case (F08) in Section 3 as two real, separate facts about the same
  system; it does not state F05–F07 was instituted *because of* F08.
  No SUPPORTED_CAUSAL link between them is asserted here.

What the Ledger actually supports, stated correctly: PAGER is a real
system that (a) explicitly chooses speed over certainty by design (F01,
F02, F03, F04), (b) has a narrow, bounded exception to that choice for
its rarest, most severe alerts (F05–F07), (c) has at least one real,
named case where the fast-first choice produced an overestimate later
revised (F08, F10), and (d) the same team that runs it has separately and
explicitly named, as a general lesson from their operating experience,
the exact risk this trial's seed predicted (F09) — three real,
verifiable facts sitting next to each other, not one continuous causal
story invented to connect them.
