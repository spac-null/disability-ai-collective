#!/usr/bin/env python3
"""
render_writer_prompt.py -- deterministic renderer for the Real Article Test 2
writer prompt. Reads the frozen source snapshot, emits writer-system.txt,
writer-user.txt, writer-prompt.txt and packet.json with SHA-256 hashes.

NO LEGACY PRODUCTION PROMPT IS IMPORTED OR INJECTED. Nothing here reads
automation/orchestrator/*. The prompt is built only from this experiment's
DISCOVERY.md / ARTICLE-FORM.md / GROUNDING-BOUNDARIES.md decisions.

Run: python3 render_writer_prompt.py
Idempotent: same inputs -> same hashes.
"""
import hashlib, json, pathlib

HERE = pathlib.Path(__file__).parent
SRC = HERE / "source" / "source-snapshot.txt"


def sha(t):
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


SYSTEM = """Write a narrative nonfiction article from the material below. You are not filling in labelled sections -- write it as one continuous piece of thinking. The material below is a supply to draw on, not a running order; the route is the route given here.

Follow this route:
1. Begin with the crossing as the report describes it: no pedestrian light signals, no physical barrier, and safe use reliant on pedestrians responding to the signage and markings and on observing or hearing approaching trams. Give the place concretely. End this movement with the two channels named as the report names them, and no comment on them yet.
2. Then take the second channel apart, using only the report's facts, in this order: the audible warning board about 30 metres before the crossing, and that it was installed after a 2005 accident at this same crossing; that outside one named location it is the driver's decision whether to sound the bell or the horn; that the operator's rules ask for an 'appropriate' audible warning of 'adequate length' and the training document repeats the same words; that RAIB's own observation after the accident found passing drivers using either device, generally choosing louder and longer warnings during darkness; and that the on-tram data recorder logs bell and horn on the same channel. Do not say what this means. Let the facts do the narrowing.
3. Then the accident itself, plainly and chronologically, in seconds. Then the two recorder findings: no bell recorded at the warning board, and RAIB's conclusion that it is probably the case none was sounded; and the horn recorded less than a second before the collision, with insufficient time to act as an effective warning. Keep RAIB's hedge -- 'probably' stays 'probably'.
4. Then, immediately, before the reader can settle into the reading that the driver simply failed to ring the bell: the two earlier accidents in which a warning WAS given and people still died -- Morden Hall Park in 2008 and Saughton in 2018. Then the other prior occurrences as the report gives them. Then the twenty-year line: the 2005 remedy at this crossing was to install a board reminding a person to act; RAIB's 2017 recommendation after the 2016 death asked that all tram drivers work to the same set of requirements; RAIB now states that more effective implementation of it could have addressed the inconsistencies in audible warnings that were a factor here.
5. Arrive, and stop there.

The piece should land on this: looking is a property of the crossing, and hearing is a message with a sender. The ordinary state of that second channel is silence. The two pedestrians had crossed this tramway fewer than ten times and had never encountered a tram while crossing, so every silence they had met there had been true. A channel that is almost always silent, and almost always silent truthfully, teaches the people who use it that silence is information.

Do not extend this into any recommendation. Do not propose lights, barriers, automatic warnings, better training or better management, and do not say the accident was preventable or that any remedy would have prevented it. RAIB's own formulation is 'could have addressed' -- do not strengthen it.

The arrival is the end of the piece. Nothing follows it. Do not restate the landing a second or third time in different words, and do not write anything shaped like 'These are two different things...', 'The first is... The second is...', or 'That is the distinction...' followed by another paraphrase. A piece may end immediately after its strongest precise arrival -- it does not need a conventional closing paragraph. Do not widen at the end to trams in general, to other senses, to other crossings, or to society.

Attribute in the ordinary way prose does ('the report finds', 'RAIB concludes', 'the operator's standards require'). Quote the report directly where the wording matters -- 'observing or hearing', 'appropriate', 'adequate length', 'probably the case', 'could have addressed'. But do not discuss attribution with the reader: no sentences about whose view something is or is not, and never state what someone did not say.

Do not invent scenes, biography, motives, interior life, or dialogue. Do not write a scene inside the driving cab. Do not say why the driver did not sound the bell, what they were thinking, or that they were at fault -- the report does not establish it. Do not characterise the two pedestrians beyond what the report states, and do not name anyone; the report names no individual involved.

Do not state or imply that either pedestrian was deaf, hard of hearing, or disabled in any way. Nothing in the report suggests it. Do not introduce a disabled person, a disability example, or an access anecdote anywhere in the piece.

Give no acoustic measurement of any kind -- no decibels, no frequencies, no audibility distances. The report gives none. Do not assert how loud or how quiet a tram is.

Write in third person. Do not adopt a first-person narrator. You are not a character and have no biography.

Roughly 900-1,200 words. There is no requirement to reach 1,200. Do not pad. If the arrival has genuinely landed at 900 words, stop there.

Write only the article, with a title on the first line."""

MATERIAL = """MATERIAL:

The safety case, in the report's own words
- The report states: "There are no pedestrian light signals at the footpath crossing to indicate to pedestrians to stop if it is safe or unsafe to cross. The design of the crossing also does not include a physical barrier. Safe use of the crossing is reliant on pedestrians correctly responding to the signage and markings, and observing or hearing approaching trams."

The place
- A 45-metre fence divides the pavement from the tramway on the approach from the south; the first 40 metres are built primarily to prevent road vehicle incursions, and the differing gradient profiles create a drop in height between pavement and tramway. The final 5-metre section segregates pedestrians and follows the downward slope towards the crossing.
- At the end of the pedestrian fence a signal post displays a blue 'TRAMWAY LOOK BOTH WAYS' sign. On turning east to cross, a user can see two more such signs, one on either side of the crossing.
- 'LOOK BOTH WAYS' is painted on the pavement immediately before a short stretch of tactile paving leading to the crossing, reminding users of rule 33 of the Highway Code.
- Past the tactile paving the crossing surface is paved brick, with segregated ballasted track to the south and raised granite cobbles to the north.
- The pavement forms part of a National Cycle Route; segregation between pedestrians and cycles is denoted by signage and line markings.
- The crossing is at an intersection of two busy roads and the tramway.

The second channel
- An audible warning board is provided approximately 30 metres before the crossing, reminding the tram driver of a requirement to sound an audible warning on the approach to the footpath and vehicle crossings. It was originally fitted in response to an accident involving a pedestrian at the same crossing in 2005.
- The operator's rules and operational standards require drivers to "give a compulsory appropriate audible warning of the approach of the tram. All warnings must be of adequate length to ensure third parties are able to react and move clear of the tram approach."
- The standards specify the use of the horn only at Sheffield Road bridge, which is not near Staniforth Road. "At all other audible warning boards, it is the driver's decision whether to sound the bell or the horn."
- The driver training document MEI-CAT Phase Two requires an "appropriate audible warning of the approach of the tram", with warnings of "adequate length".
- The report finds: "The absence of specific details on audible warnings within operational rules and training documents creates the potential for inconsistency between drivers on the type and length of warnings which are sounded at audible warning boards across the network."
- RAIB's observations after the accident at the outbound audible warning board found that passing trams used either their bell or horn, "with drivers generally opting for louder and longer warnings during darkness".
- The bell and horn were tested after the accident against Railway Group Standard GMRT 2484 issue 2 (2007) and LRSSB standard LRSSB-LRG 5.0 (2022). They met the requirements, were fully operational, sounded clearly, and were accurately recorded on the on-tram data recorder, "which records bell and horn activation on the same channel".

The accident
- At around 16:14 on Sunday 22 June 2025 a tram collided with two pedestrians at Staniforth Road footpath crossing, Sheffield, on the South Yorkshire Supertram network, at approximately 17 mph (27 km/h).
- The driver booked on at 09:46, worked three days a week, and this was their first shift after two rest days. Tram 101 left Middlewood at 15:46 outbound to Meadowhall Interchange. The tram was lightly loaded, around 30 passengers.
- The pedestrians had raced at Woodbourn Road athletics stadium and were on a cool-down circuit. They had initially crossed the tramway at Woodbourn Road tram stop, then run on the pavement parallel to the tramway.
- No requests were made for Woodbourn Road stop, so the tram passed through without stopping. Shortly after, the driver observed the two pedestrians on the pavement, running ahead of the tram alongside the track.
- The driver accelerated to line speed, using the service brake on the descending gradient to stay at or below the 30 mph (48 km/h) limit, and made a short hazard brake application approximately 30 metres from the start of the crossing to control speed for the 15 mph (24 km/h) reduction.
- The tram signal for the junction displayed a proceed aspect from the time it came into view.
- The pedestrians turned to their right and ran across the tramway directly into the path of the tram around 1 second before they were struck. They did not look towards the approaching tram before stepping onto the crossing.
- Less than a second before the collision the driver applied the hazard brake and sounded the horn simultaneously.
- One pedestrian was pushed clear of the tram by the other and sustained minor injuries. The other fell with the lower half of their body under the front of the tram and was pushed forward by equipment underneath it for about 6 metres.
- The tram stopped approximately 4 seconds after the hazard brake application, about 12 metres from the point of collision.
- One pedestrian sustained serious injuries, the other minor injuries; both were taken to hospital. There were no injuries on board. The driver tested negative for drugs and alcohol.

What the recorders showed
- "The pedestrians did not hear a warning from the tram before the crossing. The CCTV footage from inside the driving cab shows the driver had their hand on the control to sound the bell or horn. The driver stated that they sounded the bell; however, as the movements required are only slight, the footage is unclear as to whether they did so or not. The OTDR did not record the bell being sounded at the audible warning board and it is therefore probably the case that the tram driver did not sound an audible warning as required."
- The OTDR recorded use of the warning horn just before the collision, "within a second of the pedestrians turning right into the path of the tram but less than a second before the collision, when the pedestrians were already on the crossing, and with insufficient time to act as an effective warning."

The two pedestrians, as the report describes them
- Both young people, aged 15 and 17. Not residents of Sheffield; they attend race meets at Woodbourn Road athletics stadium a few times every summer. They were not familiar with the area nor with tram networks generally.
- The cool-down route is 1.2 km (0.75 miles), takes approximately 6 minutes, and crosses the tramway twice per circuit. They had completed it fewer than 10 times before and "had never encountered a tram while crossing the tramway."
- Witness evidence shows neither pedestrian was expecting to have to stop for a tram when crossing.
- They were not wearing headphones or using electronic devices. They were talking with each other while running, which may have drawn their focus away from their surroundings.
- RAIB measurements indicate the level of passing traffic was unlikely to have hindered their ability to hear any warnings from the tram.

Prior occurrences, exactly as this report records them
- 27 October 2005, Staniforth Road footpath crossing: a tram struck and seriously injured a pedestrian who stepped onto the crossing directly in front of it. RAIB report 01/2006 found the driver's ability to assess the risk may have been negatively affected by the fence on the approach. Following the accident, the audible warning board was installed and the 24-metre section of fence immediately before the crossing was redesigned.
- 13 September 2008, Morden Hall Park footpath crossing, London Tramlink: a tram collided with a cyclist, who later died. Causal factors were that the cyclist may have been wearing headphones, preventing them hearing the audible warnings sounded by the tram driver, and that the crossing approach did not encourage cyclists to look towards eastbound trams (RAIB report 06/2009).
- 16 May 2012, near Sandilands tram stop, Croydon: a pedestrian was struck and seriously injured, falling into the space between platform and tram. They had not looked for an approaching tram, and the layout meant trams on the nearest track approached from behind (RAIB report 03/2013).
- 22 December 2016, Woodbourn Road tram stop, Sheffield: a pedestrian who had just got off an inbound tram was struck and fatally injured by a non-stop outbound tram at around 13 mph (21 km/h). They were seemingly unaware the tram was approaching, "and the tram did not give an audible warning to indicate that it was passing non-stop through the tram stop" (RAIB report 13/2017).
- 11 September 2018, near Saughton tram stop, Edinburgh: a pedestrian was struck and fatally injured. "Although the tram driver had used the tram's bell to sound repeated warnings on the approach to the crossing, the audible warning was not sufficiently loud for it to be heard and acted upon by the pedestrian until it was too late" (RAIB report 09/2019).

The twenty-year line
- RAIB states that recommendation 1 of report 13/2017, made after the 2016 fatal accident, "had the potential to address one or more factors identified in this report", and that "more effective implementation of recommendation 1 from this report could have addressed the inconsistencies in audible warnings for users of the footpath crossing which were a factor in this accident."
- That recommendation's stated intent was "that all tram drivers drive to the same set of requirements, irrespective of when they were initially trained."

Severity
- "The area beyond the crossing included raised cobbles, which possibly exacerbated one of the pedestrian's injuries."

Organisations
- South Yorkshire Future Trams Ltd (SYFTL), operator and maintainer of the network. South Yorkshire Mayoral Combined Authority (SYMCA), owner of the network. RAIB found that management of risk at Staniforth Road footpath crossing by these two "was not sufficiently effective."
"""

BOUNDARIES = """GROUNDING BOUNDARIES: The report does not say why the driver did not sound the bell, what they were thinking, or that they were at fault -- only that the recorder logged no bell at the warning board and that it is "probably the case" none was sounded. It gives no acoustic measurement of any kind: no decibels, no frequencies, no audibility distances, and no statement of how loud or quiet a tram is. It names no individual involved. It says nothing about either pedestrian being deaf, hard of hearing, or disabled. It records nothing about the five earlier accidents beyond the summaries given above, and the earlier reports themselves are not available to you. It does not recommend installing lights, barriers, or automatic warnings, and it does not say this accident or any earlier one would have been prevented by any remedy. Nothing outside the FULL SOURCE TEXT below is authorised -- no press coverage, no standards documents, no general knowledge about trams, Sheffield, or acoustics.

FULL SOURCE TEXT (the only source of any named person, quote, date, number, distance, or measurement you may use):
---
"""


def main():
    src = SRC.read_text(encoding="utf-8")
    user = MATERIAL + "\n" + BOUNDARIES + src + "\n---\n"
    prompt = SYSTEM + "\n\n" + user

    (HERE / "writer-system.txt").write_text(SYSTEM, encoding="utf-8")
    (HERE / "writer-user.txt").write_text(user, encoding="utf-8")
    (HERE / "writer-prompt.txt").write_text(prompt, encoding="utf-8")

    packet = {
        "experiment": "real-article-test-2",
        "frozen": "2026-08-20",
        "status": "PRE-EXECUTION -- NOT GENERATED",
        "architecture": ["DISCOVERY", "ARTICLE FORM", "WRITER", "WRITER GROUNDING"],
        "execution_target": "local Claude subscription (manual/shadow)",
        "legacy_production_prompt_injected": False,
        "source": {
            "title": ("Rail Accident Report -- Collision between a tram and two pedestrians "
                      "at Staniforth Road, Sheffield, 22 June 2025"),
            "publisher": "Rail Accident Investigation Branch (RAIB)",
            "report_number": "10/2026",
            "published": "2026-07-28",
            "pdf_url": ("https://assets.publishing.service.gov.uk/media/"
                        "6a67566bb9e28a4788aa3f61/R102026_260728_Staniforth_Road.pdf"),
            "pdf_sha256": "7b27f78f3a70355126b332aa6dba3b316facc638e842f1761666c50ce8e5603f",
            "source_sha256": sha(src),
            "source_words": len(src.split()),
        },
        "prompt": {
            "system_sha256": sha(SYSTEM),
            "user_sha256": sha(user),
            "prompt_sha256": sha(prompt),
            "system_chars": len(SYSTEM),
            "user_chars": len(user),
            "prompt_chars": len(prompt),
            "prompt_words": len(prompt.split()),
        },
        "documents": {
            n: sha((HERE / n).read_text(encoding="utf-8"))
            for n in ["DISCOVERY.md", "ARTICLE-FORM.md", "GROUNDING-BOUNDARIES.md",
                      "CANDIDATES.md", "source/PROVENANCE.md"]
        },
    }
    packet_json = json.dumps(packet, indent=2, sort_keys=True)
    packet["packet_sha256"] = sha(packet_json)
    (HERE / "packet.json").write_text(
        json.dumps(packet, indent=2, sort_keys=True), encoding="utf-8")

    print(f"source   SHA-256 {packet['source']['source_sha256']}")
    print(f"system   SHA-256 {packet['prompt']['system_sha256']}")
    print(f"user     SHA-256 {packet['prompt']['user_sha256']}")
    print(f"PROMPT   SHA-256 {packet['prompt']['prompt_sha256']}")
    print(f"PACKET   SHA-256 {packet['packet_sha256']}")
    print(f"prompt: {packet['prompt']['prompt_chars']} chars / "
          f"{packet['prompt']['prompt_words']} words "
          f"(system {packet['prompt']['system_chars']}, user {packet['prompt']['user_chars']})")


if __name__ == "__main__":
    main()
