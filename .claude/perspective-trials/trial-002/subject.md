# Trial 002 — Subject

## SUBJECT

The FAA's NOTAM (Notice to Air Missions) system: the January 11, 2023
nationwide outage/ground stop caused by a database failure, and the
decades-long, separately-documented problem that the notices themselves are
formatted in a way many pilots and at least one NTSB board member have called
functionally unreadable at volume.

This subject was selected and recorded by the controlling session before any
lens ran (see the original selection rationale, carried over unedited from
the pre-Trial-001 draft): institutional process / infrastructure / ordinary
mechanism category; not Tollymore, WildSumaco, Roman Space Telescope,
Beetaloo, Minnie Evans, Jolly's Mill Pond, the Gen Z painting subject, a
PR001–PR004 example, or a calibration-batch subject; no disability
vocabulary informed the choice.

## PRIMARY / STRONG SOURCES

- U.S. DOT — "The Federal Aviation Administration's NOTAM System Failure and
  its Impacts on a Resilient National Airspace,"
  https://www.transportation.gov/federal-aviation-administrations-notam-system-failure-and-its-impacts-resilient-national-airspace
- FAA Newsroom — "FAA NOTAM Statement," https://www.faa.gov/newsroom/faa-notam-statement
- Wikipedia — "2023 FAA system outage," https://en.wikipedia.org/wiki/2023_FAA_system_outage
  (full body fetched and used as the anchor text for the baseline run below)
- CNBC, Jan 11 2023 — "FAA orders airlines to pause departures until 9 a.m. ET
  after system outage," https://www.cnbc.com/2023/01/11/faa-orders-airlines-to-pause-departures-until-9-am-et-after-system-outage.html
- Washington Post, Jan 11 2023 — "FAA looking into what caused system outage
  that resulted in mass delays," https://www.washingtonpost.com/nation/2023/01/11/faa-notam-outage-flights-us/
- FAA Newsroom, 2026 — "U.S. Transportation Secretary Sean P. Duffy Deploys
  Brand New 'Notice to Airmen' System," https://www.faa.gov/newsroom/us-transportation-secretary-sean-p-duffy-deploys-brand-new-notice-airmen-system-provide
- Aviation International News (AIN), Kipp Lau, Oct 26 2018 — "AINsight: Notams
  Are Wall of Text and Bunch of Garbage," https://www.ainonline.com/aviation-news/blogs/ainsight-notams-are-wall-text-and-bunch-garbage
  (full body not retrievable behind dynamic page load; header/photo-caption
  text and the article's existence/date/author confirmed directly)
- Flight Safety Foundation, June 1 2021 — "Redefining NOTAMS" (NTSB Vice Chair
  Bruce Landsberg calling the system "cumbersome," pressing FAA to finish its
  "decades-long effort to modernize"), https://flightsafety.org/asw-article/redefining-notams/
  (paywalled beyond the lede — used only for the confirmed lede fact)
- Bytron Aviation Systems — "NOTAM Overload," https://www.bytron.aero/aviation-news/notam-overload
  (industry trade source; the claim that crews can face "dozens, sometimes
  hundreds" of NOTAMs per flight is unsourced in the article itself — flagged
  as a claim without its own citation, not treated as hard data)

## PLAIN WORLD SUMMARY

NOTAM = "Notice to Air Missions" (formerly "Notice to Airmen"). It is the
FAA's mechanism for telling pilots, before and during a flight, about
anything that has changed since the charts were printed: a closed runway, a
broken navigation beacon, a temporary flight restriction, construction near
an airport, GPS interference in a region, etc. Every U.S. pilot is required
to check relevant NOTAMs before flying. The system dates to a pre-digital
telegram-style notification format and was still running on that legacy
architecture (built 1985, on roughly 30-year-old software/hardware by the
FAA's own later description) as of 2023.

On January 11, 2023, a contractor (Spatial Front, Inc.) doing routine
maintenance to synchronize the live NOTAM database with its backup
unintentionally deleted files in both the primary and backup systems at
once. NOTAM system processing stopped at 3:28 p.m. ET on January 10; the FAA
issued its first advisory at 7:47 p.m. that evening; by 7:30 a.m. ET on
January 11 the FAA ordered a full nationwide pause on domestic departures —
the first nationwide ground stop since September 11, 2001. Flights already
airborne were allowed to continue. Departures resumed by roughly 8:30–9:00
a.m. ET, an outage of 11 hours 50 minutes total, delaying more than 10,000
flights. On January 13, 2023 the FAA stated preliminary findings: an
engineer "replaced one file with another," not realizing a mistake had been
made, during otherwise-routine maintenance — an "honest mistake that cost
the country millions." No cyberattack. Delta Air Lines had a working backup
system but chose not to use it "out of deference" to the FAA. The FAA
adopted a synchronization delay and a two-person rule for database
maintenance afterward.

That outage is the visible, dramatic event. Independent of it, and older
than it, is a second, quieter fact: the notices themselves have had a
persistent reputation, inside aviation, for being close to unreadable at
scale — all-caps, heavily abbreviated, ICAO-code-laden strings that read
like 1920s telegrams, with a pilot on a longer flight sometimes handed 100+
individual notices to sort through for the few relevant to their route. This
was being called out publicly as far back as 2018 (AIN) and 2021 (NTSB Vice
Chair Bruce Landsberg, on record calling the system "cumbersome"). In April
2026, the FAA retired the legacy US NOTAM System (USNS) and replaced it with
a cloud-based NOTAM Management Service (NMS) whose headline feature, per the
FAA's own announcement, is a "plain-language presentation" alongside the old
coded format — the fix FAA chose to publicize was about how information is
*presented*, not just what infrastructure it runs on.

## WHAT ACTUALLY HAPPENS

- A federal agency operates a mandatory, safety-critical information channel
  every pilot must consult before flying.
- That channel ran on 1985-vintage architecture until April 2026 — 41 years
  before the notice *format itself* was substantially revised.
- The 2023 failure was a data-integrity/infrastructure failure: a routine
  maintenance operation with no isolation between primary and backup, caused
  by one person's mistake going unnoticed.
- Separately, and for far longer, the complaint people inside the system
  actually raised was not "it goes down" but "when it works, it produces
  output humans can't reliably parse under real operating conditions — time
  pressure, route-relevant messages mixed indiscriminately with irrelevant
  ones, sheer volume."
- The 2026 replacement's marketed improvement is specifically legibility
  ("plain-language presentation") layered onto the same underlying alert
  content — a change in how the information is rendered for a human reader
  to actually process, not a change in what gets reported.

## IMPORTANT PEOPLE / OBJECTS / SYSTEMS

- **NOTAM** — Notice to Air Missions (formerly Notice to Airmen); the actual
  message/artifact pilots must consult.
- **Legacy US NOTAM System (USNS)** — the retired 1985-vintage backend,
  operational until April 2026.
- **NOTAM Management Service (NMS)** — the cloud-based 2026 replacement,
  which added a plain-language presentation layer.
- **Spatial Front, Inc.** — the FAA contractor whose maintenance work
  triggered the January 2023 database deletion.
- **Bruce Landsberg** — NTSB Vice Chair (as of the 2021 remarks) who
  publicly criticized the system's usability and pushed for modernization.
- **FAA** and **U.S. DOT** — the operating and oversight agencies.
- Pilots and dispatchers generally — the population that must read and act
  on NOTAM output under real time pressure before every flight.

## KNOWN UNCERTAINTIES

- Exact cancellation count for Jan 11, 2023 is not separated from the
  "delayed" figure in the sources reviewed (>10,000 flights delayed is the
  figure consistently reported; a clean cancellations-only number was not
  found in this pass).
- The Ops Group survey statistic ("nearly three out of four pilots had at
  some point missed an important NOTAM") appeared only in a search-engine
  summary layer, not verified against the original Ops Group survey document
  — provisional, pending direct-source verification if it becomes load
  bearing.
- **Unresolved and load-bearing for the baseline run below:** whether the
  NTSB (or FAA itself) ever issued a *formal, numbered* safety recommendation
  or human-factors study specifically about NOTAM presentation/readability
  (as opposed to individual board members' public remarks and trade-press
  commentary) was not confirmed in this pass.
- The AIN 2018 article's full body text could not be retrieved (dynamic page
  loading); only its existence, byline, date, and photo-caption text were
  confirmed directly.
- Whether the 2026 NMS "plain-language presentation" measurably reduces
  real-world missed-NOTAM incidents is not yet knowable — too recent (April
  2026) for outcome data to exist.
