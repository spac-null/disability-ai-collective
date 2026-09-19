"""Build CRIP_MINDS_GOLD.json.

Every label below was assigned by rechecking the candidate against the COMPLETE frozen
evidence of its run. Prior model verdicts (grounding classifications, shadow classifier
output, validator refusals, pilot reviewer objections) were used only to FIND candidates,
never as label authority -- §10 of the brief.

Two evidence regimes are emitted per case and reported apart, never combined:

  SOURCE  context = frozen source prose.
          CITED_BASIS = the sources the claim's basis cites.
          COMPLETE_FROZEN_EVIDENCE = every frozen source of the run.
  LEDGER  context = frozen fact propositions (only where an under-cited question is
          defined). CITED_BASIS = declared basis facts. COMPLETE = all ledger facts.

Leakage guard: any ledger proposition identical to the claim is removed from that
claim's context and recorded in `leakage_removed`.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cm_evidence as E  # noqa: E402

BASE = "/srv/data/cripminds-new-engine-v1/"
OUT = BASE + "experiments/factuality-bakeoff/gold/CRIP_MINDS_GOLD.json"

# ---------------------------------------------------------------------------
# claim sources:
#   FACT  -> claim text is the frozen fact's proposition; basis = its evidence_ids
#   TEXT  -> claim text is given verbatim (an article span or a lens/turn claim)
# ---------------------------------------------------------------------------
CASES = [
    # ---------------- SUPPORTED_DIRECT ----------------
    dict(case_id="CM01", run="fast-lane-v1-fresh-asl-whitehouse-20260912", article="asl-whitehouse",
         kind="TEXT", label="SUPPORTED_DIRECT", failure_type="quote",
         claim="To the extent the defendants argue that they prefer to act free from association with "
               "accessibility for people with disabilities, their gripe is with Congress and the "
               "Rehabilitation Act itself",
         authority="DIRECT_SOURCE",
         note="Appears verbatim in S3 (quoted, attributed to Ali) and in S4, the court order itself. "
              "The retained FACT_CHECK listed it under contradicted/blocking_contradictions; rechecking "
              "against the complete frozen sources shows the quote is present and correctly attributed.",
         evidence="S3/S4: \"To the extent the defendants argue ... their gripe is with Congress and the "
                  "Rehabilitation Act itself\""),
    dict(case_id="CM02", run="fast-lane-v1-fresh-asl-whitehouse-20260912", article="asl-whitehouse",
         kind="TEXT", label="SUPPORTED_DIRECT", failure_type="quote",
         claim="For the purposes of this action, the defendants concede that section 504(a) applies to "
               "them, and wanting to have an 'image' free from its requirements is not a sound basis for "
               "declining to provide reasonable accommodations.",
         authority="DIRECT_SOURCE",
         note="Present in S4 (court order) as 'reasonable accommodations' and quoted in S3 as "
              "'reasonable accommodation'. The singular/plural and quote-mark differences are "
              "representation, not a factual difference. Also listed under contradicted in the "
              "retained FACT_CHECK.",
         evidence="S4: \"the defendants concede that section 504(a) applies to them ... not a sound "
                  "basis for declining to provide reasonable accommodations.\""),
    dict(case_id="CM03", run="production-20260904T233511Z-090a77ec", article="lebowitz-prize",
         kind="FACT", fact="F02", label="SUPPORTED_DIRECT", failure_type="entity",
         authority="DIRECT_SOURCE", note="Proposition is a tight paraphrase of a verbatim span; two named "
         "winners with two named institutions."),
    dict(case_id="CM04", run="production-20260904T234616Z-ab65bb22", article="finsbury-health-centre",
         kind="FACT", fact="F02", label="SUPPORTED_DIRECT", failure_type="entity",
         authority="DIRECT_SOURCE", note="Project title and author, verbatim in the cited source."),
    dict(case_id="CM05", run="production-20260904T230758Z-544cb004", article="mars-tidal-tomography",
         kind="FACT", fact="F10", label="SUPPORTED_DIRECT", failure_type="attribution",
         authority="DIRECT_SOURCE", note="Author affiliation, verbatim in the cited source."),
    dict(case_id="CM06", run="production-20260905T000020Z-82271f1f", article="substack-paywall-dispute",
         kind="FACT", fact="F26", label="SUPPORTED_DIRECT", failure_type="attribution",
         authority="DIRECT_SOURCE", note="Attributed charge; the span is Veit's own wording and the "
         "proposition attributes it to Veit."),
    dict(case_id="CM07", run="production-20260905T002603Z-90687a49", article="epistocracy-commitment",
         kind="FACT", fact="F05", label="SUPPORTED_DIRECT", failure_type="entity",
         authority="DIRECT_SOURCE", note="Names Brennan's epistocratic veto as the target of the "
         "paper's objection; verbatim in the cited source."),
    dict(case_id="CM08", run="production-20260903T210946Z-4dd582f6", article="anguilla-eel-nottingham",
         kind="TEXT", label="SUPPORTED_DIRECT", failure_type="entity",
         claim="Lily-Grace Conradie's student proposal at the University of Nottingham is called \"Anguilla.\"",
         authority="DIRECT_SOURCE",
         note="S0 (Dezeen school show for the University of Nottingham) carries the project name "
              "Anguilla and the student credit 'Student: Lily-Grace Conradie'. The retained "
              "GROUNDING_V2_SHADOW classified this UNSUPPORTED; that verdict does not survive a "
              "recheck against the complete source.",
         evidence="S0: \"... Anguilla operates as ecological infrastructure ...\" / \"Student: "
                  "Lily-Grace Conradie Course: Architecture BArch Hons\""),

    # ---------------- SUPPORTED_RELATION ----------------
    dict(case_id="CM09", run="production-20260903T210946Z-4dd582f6", article="anguilla-eel-nottingham",
         kind="TEXT", label="SUPPORTED_RELATION", failure_type="number",
         claim="ZSL and the river obstacles survey guide both put the fall in recruitment since the "
               "1980s at 90 to 95 per cent.",
         authority="DIRECT_SOURCE",
         note="Both cited sources carry the figure independently: S1 (ZSL) 'reduced by 90-95% since "
              "the 1980's'; S2 (river obstacles survey guide) 'declines (90-95% based on best "
              "available data) ... since the 1980s'. The two-source attribution and the number both "
              "hold. Shadow classifier called it UNSUPPORTED; overturned on recheck.",
         evidence="S1: \"annual recruitment of the European eel across its range has reduced by "
                  "90-95% since the 1980's\"; S2: \"considerable declines (90-95% ...) in European "
                  "eel ... recruitment ... since the 1980s\""),
    dict(case_id="CM10", run="production-20260904T230758Z-544cb004", article="mars-tidal-tomography",
         kind="FACT", fact="F34", label="SUPPORTED_RELATION", failure_type="causality",
         authority="DIRECT_SOURCE", note="CAUSE relation ('couple with ... to produce') present in "
         "both proposition and verbatim span."),
    dict(case_id="CM11", run="production-20260904T233511Z-090a77ec", article="lebowitz-prize",
         kind="FACT", fact="F19", label="SUPPORTED_RELATION", failure_type="chronology",
         authority="DIRECT_SOURCE", note="TEMPORAL relation ('Before arriving at Duke') explicit in "
         "the verbatim span."),
    dict(case_id="CM12", run="production-20260904T234616Z-ab65bb22", article="finsbury-health-centre",
         kind="FACT", fact="F21", label="SUPPORTED_RELATION", failure_type="negation",
         authority="DIRECT_SOURCE", note="NEGATION preserved: 'walls are not parallel' against span "
         "'shanks splayed and their walls not parallel'."),
    dict(case_id="CM13", run="production-20260905T002603Z-90687a49", article="epistocracy-commitment",
         kind="FACT", fact="F11", label="SUPPORTED_RELATION", failure_type="negation",
         authority="DIRECT_SOURCE", note="Scope negation over a list, preserved verbatim."),
    dict(case_id="CM14", run="production-20260905T004901Z-e3dc5fee", article="minnie-evans",
         kind="FACT", fact="F04", label="SUPPORTED_RELATION", failure_type="chronology",
         authority="DIRECT_SOURCE", note="Date plus TEMPORAL ordering ('in 1935, after the death of "
         "her grandmother') both in the span."),
    dict(case_id="CM15", run="production-20260905T010341Z-1f4eac32", article="sophie-lewis",
         kind="FACT", fact="F03", label="SUPPORTED_RELATION", failure_type="comparison",
         authority="DIRECT_SOURCE", note="SUPERLATIVE ('most recent book') explicit in the span."),
    dict(case_id="CM16", run="production-20260905T011646Z-596835f1", article="dehnel-phenomenon",
         kind="FACT", fact="F03", label="SUPPORTED_RELATION", failure_type="attribution",
         authority="DIRECT_SOURCE", note="Attribution plus date plus 'first described' ordering."),
    dict(case_id="CM17", run="production-20260905T000020Z-82271f1f", article="substack-paywall-dispute",
         kind="FACT", fact="F29", label="SUPPORTED_RELATION", failure_type="chronology",
         authority="DIRECT_SOURCE", note="Attributed temporal claim ('after several months of "
         "observing') preserved."),
    dict(case_id="CM18", run="production-20260907T154937Z-8556915b", article="speech-bci-ovmi",
         kind="TEXT", label="SUPPORTED_RELATION", failure_type="causality",
         claim="For restoring speech for people with paralysis, the reference distribution specifies "
               "the words a user may wish to communicate, so the measure is tied to the communication "
               "target.",
         cited_facts=["F13", "F16", "F31", "F32", "F37"], ledger_regime=True,
         authority="DIRECT_SOURCE",
         note="The declared basis does carry this: F16 defines OVMI 'relative to a reference "
              "distribution over the words a user may wish to communicate' and F37 ties decoding "
              "accuracy to which words the user needs. The retained validator refused it because no "
              "cited proposition contains a CONSEQUENCE trigger word; the audit read that as an "
              "under-cited basis. On the evidence the cited basis is sufficient, so this is scored as "
              "a supported relation and the refusal as a lexical false positive.",
         evidence="F16 + F37 (declared basis)"),

    # ---------------- UNDER_CITED_BUT_SUPPORTED ----------------
    dict(case_id="CM19", run="production-20260910T190530Z-8a0dab48", article="descent-kinetic-light",
         kind="TEXT", label="UNDER_CITED_BUT_SUPPORTED", failure_type="negation",
         claim="The steep peak of the ramp is not a neutral accessibility structure: its resistance "
               "uphill and assistance downhill make the stage itself an active choreographic object.",
         cited_facts=["F33", "F39", "F40", "F43"], ledger_regime=True,
         authority="POSTMORTEM_CONFIRMED+DIRECT_SOURCE",
         note="Genuinely under-cited. The support sits in two facts the plan did not declare: F34 "
              "('An extremely steep peak ... provides resistance when the dancers move up and rapidly "
              "increases their velocity when they move down', verbatim in S1) and F50 ('access as an "
              "integral part ... not a secondary accommodation'). The declared basis alone does not "
              "carry the uphill/downhill mechanism.",
         evidence="F34, F50 (present in the frozen ledger, absent from the declared basis)"),
    dict(case_id="CM20", run="production-20260906T005037Z-d9551ea5", article="door-hardware-spec",
         kind="TEXT", label="UNDER_CITED_BUT_SUPPORTED", failure_type="comparison",
         claim=None, from_arch="final_lens.lens_claim", ledger_regime=True,
         authority="DIRECT_SOURCE",
         note="Surfaced by running the production checker offline over retained architectures: "
              "refused on the declared basis for EQUIVALENCE, passes on the complete ledger. Claim "
              "text and declared basis are read from the retained ARCHITECTURE.json.",
         evidence="see cited_facts vs complete ledger"),
    dict(case_id="CM21", run="production-20260909T132219Z-f32c587b", article="algorithm-off-switch",
         kind="TEXT", label="UNDER_CITED_BUT_SUPPORTED", failure_type="comparison",
         claim=None, from_arch="final_lens.lens_claim", ledger_regime=True,
         authority="DIRECT_SOURCE",
         note="Same provenance as CM20: refused on the declared basis for COMPARISON and "
              "GENERALIZATION, passes on the complete ledger.",
         evidence="see cited_facts vs complete ledger"),

    # ---------------- INTERPRETATION_SUPPORTED_PREMISES ----------------
    dict(case_id="CM22", run="production-20260909T112754Z-d41d6fbc", article="antonello-theft",
         kind="TEXT", label="INTERPRETATION_SUPPORTED_PREMISES", failure_type="comparison",
         claim="The theft is best understood through the partial survival made visible by the two "
               "abandoned panels and the unresolved systems around them.",
         authority="POSTMORTEM_CONFIRMED",
         note="'best understood' is a claim about which reading explains the material, not a ranking "
              "of worldly things. The audited postmortem classified it EDITORIAL_INTERPRETATION; the "
              "premises (two abandoned panels, unresolved systems) are carried by the frozen evidence.",
         evidence="postmortem C21_FAILURE_CLASSIFICATION_V2 + frozen ledger premises"),
    dict(case_id="CM23", run="production-20260913T083824Z-f83f4b8a", article="sfmoma-creative-growth",
         kind="TEXT", label="INTERPRETATION_SUPPORTED_PREMISES", failure_type="causality",
         claim="Creative Growth exists because of decisions made when Ronald Reagan was governor of "
               "California.",
         authority="DIRECT_SOURCE",
         note="S2 carries both halves: 'The institution's origins trace to historic political "
              "decisions made when Ronald Reagan was governor of California' and, after the account "
              "of eliminated care, 'In response, Florence and Elias Katz ... In 1974, they started "
              "Creative Growth'. The draft tightens 'origins trace to' into a flat causal claim; the "
              "premises are supported and no new worldly fact is asserted.",
         evidence="S2: \"origins trace to historic political decisions made when Ronald Reagan was "
                  "governor of California\" + \"In response, Florence and Elias Katz ...\""),
    dict(case_id="CM24", run="fast-lane-v1-fresh-immigration-20260912", article="deaf-deportations",
         kind="TEXT", label="INTERPRETATION_SUPPORTED_PREMISES", failure_type="entity",
         claim="One of them was Emilio, originally from Venezuela.",
         authority="DIRECT_SOURCE",
         note="S0 establishes 'more than 100 deaf immigrants who have been deported from the U.S. in "
              "2026', that Metraux spoke to Emilio, that 'Emilio's from Venezuela originally' and "
              "that he was bussed to the Mexican border without an interpreter. Placing him inside "
              "the counted group is a reading of the interview's structure, not a new fact.",
         evidence="S0: \"One of the people I spoke to, Emilio ... Emilio's from Venezuela originally, "
                  "and they didn't give an interpreter\""),
    dict(case_id="CM25", run="production-20260915T072045Z-40294a3a", article="progetto-di-vita",
         kind="TEXT", label="INTERPRETATION_SUPPORTED_PREMISES", failure_type="comparison",
         claim="The national delay makes the existing Comune route more important as a present form "
               "of the Progetto di vita framework.",
         cited_facts=["F07", "F08", "F10", "F12"], ledger_regime=True,
         authority="DIRECT_SOURCE",
         note="The premises are carried by the declared basis: the postponement and the feared "
              "receding change (F07/F08), that people can already request a Progetto di vita from "
              "their Comune (F10), and that regional law already defines its characteristics without "
              "implementing resolutions (F12). 'More important' is an editorial comparative; no fact "
              "anywhere asserts it, and it does not masquerade as a new worldly fact. The two ledger "
              "facts the audit read as carrying COMPARISON (F11 'even more evident in Lombardy', F18 "
              "'even more involved') are lexical matches that do not bear on this claim.",
         evidence="F07, F08, F10, F12 (declared basis)"),
    dict(case_id="CM26", run="production-20260910T084202Z-09d602f1", article="handmade-art-revival",
         kind="TEXT", label="INTERPRETATION_SUPPORTED_PREMISES", failure_type="causality",
         claim="Traditional art matters here because it gives people an experience of participation "
               "and agency that a finished image alone cannot provide.",
         cited_facts=["F65", "F66", "F67"], ledger_regime=True,
         authority="DIRECT_SOURCE",
         note="The declared basis carries the content, attributed to psychologist Ritz Birah: F65 "
              "(making art by hand 'moves someone from spectator to participant'), F66 (showing the "
              "work 'adds a sense of agency'), F67 ('technology can give us a result without an "
              "experience, traditional art gives us the experience back'). The lens states it in the "
              "article's own voice, which is an attribution shift, but the relation is not invented. "
              "Scored as interpretation on supported premises.",
         evidence="F65, F66, F67 (declared basis)"),
    dict(case_id="CM27", run="production-20260911T165715Z-17914595", article="tobii-responsible-ai",
         kind="TEXT", label="INTERPRETATION_SUPPORTED_PREMISES", failure_type="causality",
         claim="In these products prediction is the mechanism of speech itself.",
         authority="DIRECT_SOURCE",
         note="S1 says TD Talk's 'intuitive word-prediction ... enables quick eye gaze-based speech' "
              "and S2 describes prediction as central to conversing. The stronger framing is the "
              "writer's reading of those descriptions; it asserts no new factual state about the "
              "product.",
         evidence="S1: \"intuitive word-prediction, which enables quick eye gaze-based speech\""),

    # ---------------- UNSUPPORTED_RELATION ----------------
    dict(case_id="CM28", unsupported_span='born in the Alice Griffith public housing development', run="production-20260913T083824Z-f83f4b8a", article="sfmoma-creative-growth",
         kind="TEXT", label="UNSUPPORTED_RELATION", failure_type="entity",
         claim="William Scott, a self-taught painter, was born in the Alice Griffith public housing "
               "development in 1964 and grew up there.",
         authority="OWNER_CONFIRMED+DIRECT_SOURCE",
         note="Checked absence over the complete frozen evidence. The anchor says Alice Griffith is "
              "'near the city's Bayview-Hunters Point neighborhood, where the artist was raised'; S3 "
              "says 'Born in San Francisco's Bayview-Hunter's Point neighborhood in 1964'. No source "
              "places his birth in, or his upbringing in, Alice Griffith specifically, and S3 has "
              "Scott describing 'living in Hayward with my mom'. The owner repaired exactly this "
              "sentence for an ambiguous spatial antecedent. Same entities, wrong locative relation.",
         evidence="anchor: \"Alice Griffith ... near the city's Bayview-Hunters Point neighborhood, "
                  "where the artist was raised\"; S3: \"Born in San Francisco's Bayview-Hunter's "
                  "Point neighborhood in 1964\"; OWNER_COPYDESK_REPAIR.additional_owner_authorized_repairs"),
    dict(case_id="CM29", unsupported_span='so a sentence can be built in fewer selections', run="production-20260911T165715Z-17914595", article="tobii-responsible-ai",
         kind="TEXT", label="UNSUPPORTED_RELATION", failure_type="causality",
         claim="Word prediction is the software's running guess at the next word or phrase, offered as "
               "choices so a sentence can be built in fewer selections.",
         authority="DIRECT_SOURCE",
         note="Checked absence over the complete frozen evidence: 'fewer', 'offered as choices', "
              "'selectable' and 'keystroke' do not occur in any frozen source. S2 establishes 'fast "
              "word and phrase prediction' and S8 that prediction 'learns from the messages spoken'. "
              "The efficiency consequence -- that a sentence is built in fewer selections -- is "
              "asserted by no source.",
         evidence="absence check over S0,S1,S2,S3,S4,S5,S8"),
    dict(case_id="CM30", unsupported_span='featured eight pavilions', run="production-20260903T212459Z-601f5d23", article="jia-curated-pavilions",
         kind="TEXT", label="UNSUPPORTED_RELATION", failure_type="number",
         claim="The event featured eight pavilions.",
         authority="DIRECT_SOURCE",
         note="The source count attaches to the article's own selection, not to the event: 'Eight "
              "pavilion highlights from Jia Curated 2026', 'Here are eight of the most interesting', "
              "'Read on for more about the top eight pavilions'. No frozen source states how many "
              "pavilions the festival had. The number is transferred from a selection to an event.",
         evidence="S0: \"Eight pavilion highlights ...\" / \"Here are eight of the most interesting.\""),
    dict(case_id="CM31", unsupported_span='The learning came first', run="fast-lane-v1-replay-td-snap-20260912", article="td-snap-reset",
         kind="TEXT", label="UNSUPPORTED_RELATION", failure_type="chronology",
         evidence_run="production-20260911T165715Z-17914595",
         claim="The learning came first. The way back to default was added later.",
         authority="DIRECT_SOURCE",
         note="The frozen release notes date only the reset: S5, release 1.31 (2024-02-23), 'Learned "
              "word prediction can now be reset back to the default.' No frozen source dates the "
              "introduction of learned word prediction, so the ordering between the two is not "
              "established. Chronology asserted beyond the evidence.",
         evidence="S5 release note 1.31; no source dates learned word prediction's introduction"),

    # ---------------- PERIPHERAL_UNSUPPORTED ----------------
    dict(case_id="CM32", unsupported_span='on non-approved hardware', run="fast-lane-v1-replay-td-snap-20260912", article="td-snap-reset",
         kind="TEXT", label="PERIPHERAL_UNSUPPORTED", failure_type="qualifier",
         evidence_run="production-20260911T165715Z-17914595",
         claim="Tobii Dynavox will not offer technical support for hardware compatibility issues on "
               "non-approved hardware.",
         authority="DIRECT_SOURCE",
         note="Qualifier loss. S3 limits the exclusion to 'TD Snap installed on non-Tobii Dynavox "
              "approved hardware, by non-licensed resellers'. Dropping 'by non-licensed resellers' "
              "broadens the stated scope of the disclaimer, so the claim as written is not supported. "
              "Minor for publication; still unsupported at the factuality level.",
         evidence="S3: \"will not offer technical support for hardware compatibility issues related "
                  "to TD Snap installed on non-Tobii Dynavox approved hardware, by non-licensed "
                  "resellers\""),
]


def arch_claim(run_dir, field):
    arch = json.load(open(os.path.join(run_dir, "ARCHITECTURE.json")))
    if field == "final_lens.lens_claim":
        lens = arch.get("final_lens") or {}
        return lens.get("lens_claim"), list(lens.get("evidence_basis") or [])
    return arch.get(field), list(arch.get("use_facts") or [])


def build():
    out = []
    problems = []
    for c in CASES:
        run_dir = BASE + c["run"]
        run = E.load_run(run_dir)
        ev_run = E.load_run(BASE + c["evidence_run"]) if c.get("evidence_run") else run

        claim = c.get("claim")
        cited_facts = list(c.get("cited_facts") or [])

        if c["kind"] == "FACT":
            fact = run["facts"].get(c["fact"])
            if not fact:
                problems.append((c["case_id"], "fact missing"))
                continue
            claim = fact["proposition"]
            cited_sources = list(fact.get("evidence_ids") or [])
        elif c.get("from_arch"):
            claim, cited_facts = arch_claim(run_dir, c["from_arch"])
            cited_sources = sorted({s for f in cited_facts
                                    for s in ((run["facts"].get(f) or {}).get("evidence_ids") or [])})
        else:
            cited_sources = sorted({s for f in cited_facts
                                    for s in ((run["facts"].get(f) or {}).get("evidence_ids") or [])})
            if not cited_sources:
                cited_sources = sorted(ev_run["sources"])

        if not claim:
            problems.append((c["case_id"], "no claim text"))
            continue

        claim_norm, claim_log = E.normalize(claim)

        src_cited, src_cited_ids = E.source_text_for(ev_run, cited_sources, complete=False)
        src_all, src_all_ids = E.source_text_for(ev_run, None, complete=True)
        if not src_all:
            problems.append((c["case_id"], "no complete frozen source text"))
            continue

        rec = {
            "case_id": c["case_id"], "run_id": c["run"], "article_key": c["article"],
            "subject": (run["subject"] or ev_run["subject"] or "")[:200],
            "gold_label": c["label"], "failure_type": c["failure_type"],
            "authority": c["authority"], "adjudication_note": c["note"],
            "gold_evidence": c.get("evidence"),
            "claim_raw": claim, "claim_text": claim_norm, "claim_norm_log": claim_log,
            "claim_unit": "frozen fact proposition" if c["kind"] == "FACT" else "article span / lens claim",
            "evidence_run_id": c.get("evidence_run") or c["run"],
            "cited_source_ids": src_cited_ids, "complete_source_ids": src_all_ids,
            "context_SOURCE_CITED_BASIS": src_cited,
            "context_SOURCE_COMPLETE": src_all,
            "cited_fact_ids": cited_facts,
            "leakage_removed": [],
            "unsupported_span": c.get("unsupported_span"),
        }

        if c.get("ledger_regime") and cited_facts:
            def props(ids):
                keep, dropped = [], []
                for fid in ids:
                    p = (run["facts"].get(fid) or {}).get("proposition")
                    if not p:
                        continue
                    if E.normalize(p)[0] == claim_norm:
                        dropped.append(fid)
                        continue
                    keep.append("[%s] %s" % (fid, E.normalize(p)[0]))
                return "\n".join(keep), dropped

            cited_ctx, d1 = props(cited_facts)
            all_ctx, d2 = props(sorted(run["facts"]))
            rec["context_LEDGER_CITED_BASIS"] = cited_ctx
            rec["context_LEDGER_COMPLETE"] = all_ctx
            rec["leakage_removed"] = sorted(set(d1) | set(d2))

        out.append(rec)

    return out, problems


if __name__ == "__main__":
    rows, problems = build()
    import collections
    by_label = collections.Counter(r["gold_label"] for r in rows)
    by_article = collections.Counter(r["article_key"] for r in rows)
    by_type = collections.Counter(r["failure_type"] for r in rows)
    meta = {
        "built_at_utc": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc).isoformat(),
        "n_cases": len(rows),
        "distinct_articles": len(by_article),
        "by_label": dict(by_label), "by_article": dict(by_article),
        "by_failure_type": dict(by_type),
        "per_article_cap": 2,
        "cap_respected": all(v <= 2 for v in by_article.values()),
        "label_authority_rule": "DIRECT_SOURCE | POSTMORTEM_CONFIRMED | OWNER_CONFIRMED only; "
                                "prior model verdicts used for candidate discovery only",
        "contradicted_note": "No CONTRADICTED case reached trusted-label authority in the retained "
                             "corpus; reported as a coverage gap rather than filled with a weak label.",
    }
    with open(OUT, "w") as fh:
        json.dump({"meta": meta, "cases": rows}, fh, indent=1)
    print(json.dumps(meta, indent=1))
    if problems:
        print("PROBLEMS:", problems)
    print("wrote", OUT)
