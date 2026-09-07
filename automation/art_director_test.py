#!/usr/bin/env python3
"""art_director_test.py -- the art director's contract. Stdlib only, no network, no model.

What is tested is the BOUND and the PROHIBITION, not the taste: one call, zero images is a
real answer, disability iconography is refused rather than discouraged, a visual
observation cannot become an assertion, and a failure falls back instead of blocking.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art_director as AD

FAILURES, CHECKS = [], [0]

# A settled-article stand-in that actually supports the default anchors. Reconciliation
# measures a brief against the final prose, so a one-word body would legitimately strip
# every anchor -- which is the fix working, not a test failing.
ARTICLE = ("The pavilion stands on a cleared forest floor at the edge of the trees. "
           "A raised timber structure sits above sloping ground, and the timber remains "
           "exposed across the spans. The walls are bahareque, packed earth over woven "
           "cane, and the upper level rises toward the canopy.")


def check(label, cond, detail=""):
    CHECKS[0] += 1
    if cond:
        print("  PASS  %s" % label)
    else:
        FAILURES.append(label)
        print("  FAIL  %s %s" % (label, detail))


def _img(**kw):
    base = {"function": "ESTABLISH_PLACE", "register": "ATMOSPHERIC_OBSERVATIONAL",
            "editorial_purpose": "see the clearing the structure stands in",
            "factual_anchors": ["a raised timber structure on a forest floor"],
            "visual_anchors": [], "must_not_invent": ["signage"], "people": "NONE",
            "composition_note": "low horizon, structure off-centre",
            "alt_text": "A raised timber structure standing on a cleared forest floor.",
            "placement": "HERO"}
    base.update(kw)
    return base


def _brief(n=1, **kw):
    b = {"image_count": n, "count_reasoning": "one spatial claim to establish",
         "images": [_img() for _ in range(n)]}
    b.update(kw)
    return b


class _P:
    """A provider stand-in. Counts calls so 'one model call maximum' is measured."""
    def __init__(self, payload, raise_it=None):
        self.payload, self.raise_it, self.calls = payload, raise_it, 0

    def complete(self, **kw):
        self.calls += 1
        if self.raise_it:
            raise self.raise_it
        class C:
            text = self.payload if isinstance(self.payload, str) else json.dumps(self.payload)
            def identity(self):
                return {"actual_model": "claude-opus-5"}
        return C()


def test_image_count_is_the_first_decision():
    print("\ntest_image_count_is_the_first_decision")
    check("zero images is a valid brief", AD.validate_brief(_brief(0)) == [])
    for n in (1, 2, 3):
        check("%d image(s) validates" % n, AD.validate_brief(_brief(n)) == [])
    check("four images is refused", AD.validate_brief(_brief(4)) != [])
    check("a count that disagrees with the list is refused",
          any("image_count is 1 but 2" in e for e in
              AD.validate_brief({"image_count": 1, "images": [_img(), _img()]})))
    check("no filler is manufactured for a 0 brief",
          (AD.validate_brief(_brief(0)) == []) and _brief(0)["images"] == [])


def test_never_illustrate_disability():
    print("\ntest_never_illustrate_disability")
    for term, field in [("wheelchair pictogram", "composition_note"),
                        ("an accessibility symbol", "editorial_purpose"),
                        ("a glowing brain", "alt_text"),
                        ("a puzzle piece", "composition_note"),
                        ("a ramp as metaphor", "editorial_purpose")]:
        b = _brief(1)
        b["images"][0][field] = "Show %s in the centre." % term
        errs = AD.validate_brief(b)
        check("refused: %s (in %s)" % (term, field),
              any("forbidden disability iconography" in e for e in errs), errs[:1])
    b = _brief(1)
    b["images"][0]["factual_anchors"] = ["the tribunal classified a wheelchair as equipment"]
    check("also refused when it arrives via factual_anchors",
          any("forbidden" in e for e in AD.validate_brief(b)))


def test_a_visual_observation_cannot_become_an_assertion():
    print("\ntest_a_visual_observation_cannot_become_an_assertion")
    cases = [("the deck sits 3 metres above the floor", "vision_read_number"),
             ("a ramp of gentle gradient", "measurement_language"),
             ("the entrance is step-free", "accessibility_claim"),
             ("the stair is the only route to the upper room", "route_exclusivity"),
             ("there is no other way up", "absence_of_alternatives"),
             ("a visitor cannot reach the upper room", "human_capability_claim")]
    for line, reason in cases:
        check("blocked as a visual anchor (%s)" % reason,
              AD.visual_anchor_violation(line) == reason,
              AD.visual_anchor_violation(line))
        b = _brief(1)
        b["images"][0]["visual_anchors"] = [line]
        check("  and the brief carrying it is refused",
              any("visual anchor asserts" in e for e in AD.validate_brief(b)))
    ok = ["a corrugated metal roof", "bamboo and timber posts",
          "an earthen wall below a deck", "the roof sits above an open room"]
    for line in ok:
        check("permitted as vocabulary: %r" % line, AD.visual_anchor_violation(line) == "")


def test_sidecar_digest_takes_only_the_allowed_slice():
    print("\ntest_sidecar_digest_takes_only_the_allowed_slice")
    side = {"status": "NON_CLAIM_BEARING", "observations": [{
        "observable_facts": ["a corrugated metal roof", "the entrance is step-free"],
        "spatial_relationships": ["the roof sits above an open room",
                                  "the stair is the only route up"],
        "not_established": ["whether this is the only route is not established"],
        "questions_raised": ["who maintains the path"],
        "printed_labels": [{"index": "05", "label": "UPPER ROOM"}]}],
        "rejected": [{"text": "eleven rooms are numbered"}]}
    d = AD.visual_context_digest(side)
    check("present", d["present"] is True)
    check("keeps object/material vocabulary", "a corrugated metal roof" in d["objects_and_materials"])
    check("drops an accessibility claim", "the entrance is step-free" not in d["objects_and_materials"])
    check("keeps a broad spatial relationship",
          "the roof sits above an open room" in d["spatial_relationships"])
    check("drops route exclusivity", "the stair is the only route up" not in d["spatial_relationships"])
    check("keeps printed labels", "UPPER ROOM" in d["printed_labels"])
    check("counts what it dropped", d["dropped"] == 2, d["dropped"])
    blob = json.dumps(d)
    check("never carries not_established", "not established" not in blob)
    check("never carries questions_raised", "who maintains" not in blob)
    check("never reuses guard-audit rejects", "eleven rooms" not in blob)
    check("a non-sidecar object yields nothing", AD.visual_context_digest({"status": "X"})["present"] is False)
    check("None yields nothing", AD.visual_context_digest(None)["present"] is False)


def test_the_prompt_withholds_what_it_must():
    print("\ntest_the_prompt_withholds_what_it_must")
    arch = {"article_type": "FIELD_NOTE", "story_spine": "a spine",
            "beats": [{"beat_id": "B1", "happens": "the deck is reached",
                       "concrete_carrier": "the timber deck", "facts_allowed": ["F01"],
                       "must_not_say_yet": "the withheld thing"}],
            "lens": "THE WORTH LENS REASONING", "lens_claim": "worth reasoning here"}
    art = ARTICLE + " The timber deck is reached from the ground."
    u = AD.build_user_prompt(art, "T", "D", arch, "Maya Flux", None)
    check("carries the article", "cleared forest floor" in u)
    check("carries beat ids", "B1" in u)
    check("carries the carrier", "the timber deck" in u)
    check("withholds Worth reasoning", "WORTH LENS REASONING" not in u and "worth reasoning" not in u)
    check("withholds fact-permission ids", "F01" not in u)
    check("withholds pacing instructions", "the withheld thing" not in u)
    check("says persona is tone only", "tone only" in u)
    d = AD.architecture_digest(arch, art)
    check("digest is a whitelist", set(d) <= {"article_type", "story_spine", "opening",
                                              "turn", "ending_move", "beats",
                                              "beats_omitted_as_unsupported_by_the_settled_article"})


def test_alt_text_must_be_real():
    print("\ntest_alt_text_must_be_real")
    for bad in ["The Upper Room at WildSumaco — editorial illustration",
                "Something — detail illustration", "A thing — conceptual image"]:
        b = _brief(1)
        b["images"][0]["alt_text"] = bad
        check("template alt text refused: %r" % bad[:34],
              any("alt_text is a template" in e for e in AD.validate_brief(b)))
    check("a real description passes", AD.validate_brief(_brief(1)) == [])


def test_placement_is_editorial_not_arithmetic():
    print("\ntest_placement_is_editorial_not_arithmetic")
    for pl in ("HERO", "END"):
        b = _brief(1); b["images"][0]["placement"] = pl
        check("%s accepted" % pl, AD.validate_brief(b) == [])
    b = _brief(1); b["images"][0]["placement"] = "AFTER_BEAT:B2"
    check("a known beat is accepted", AD.validate_brief(b, ["B1", "B2"]) == [])
    check("an unknown beat is refused",
          any("not in the architecture" in e for e in AD.validate_brief(b, ["B1"])))
    b = _brief(1); b["images"][0]["placement"] = "40%"
    check("a paragraph percentage is refused", AD.validate_brief(b) != [])


def test_composition_may_not_reference_a_photograph():
    print("\ntest_composition_may_not_reference_a_photograph")
    for bad in ["recreate the framing", "same angle as the photo",
                "as in the photograph", "match the photo"]:
        b = _brief(1); b["images"][0]["composition_note"] = bad
        check("refused: %r" % bad,
              any("refers to a source photograph" in e for e in AD.validate_brief(b)))


def test_people_are_none_by_default():
    print("\ntest_people_are_none_by_default")
    p = AD.build_image_prompt(_img())
    check("prompt states no people", "No people in frame." in p)
    p2 = AD.build_image_prompt(_img(people="the named architect, from the article"))
    check("an explicit human subject is carried through", "named architect" in p2)


def test_one_model_call_maximum_and_a_safe_fallback():
    print("\ntest_one_model_call_maximum_and_a_safe_fallback")
    p = _P(_brief(2))
    r = AD.art_direct(p, ARTICLE, "T", arch=None)
    check("exactly one model call", p.calls == 1, p.calls)
    check("ok", r["ok"] is True, r["reason"])
    check("brief returned", r["brief"]["image_count"] == 2)

    p2 = _P(None, raise_it=RuntimeError("subscription limit"))
    r2 = AD.art_direct(p2, ARTICLE)
    check("a provider failure does not raise", r2["ok"] is False)
    check("and names the reason", "subscription limit" in r2["reason"])
    check("still only one call attempted", p2.calls == 1)

    r3 = AD.art_direct(_P("not json at all"), ARTICLE)
    check("unparseable output does not raise", r3["ok"] is False and r3["brief"] is None)

    bad = _brief(1); bad["images"][0]["composition_note"] = "recreate the photo"
    r4 = AD.art_direct(_P(bad), ARTICLE)
    check("an invalid brief is rejected, not used", r4["ok"] is False)
    check("and the reason is legible", "brief rejected" in r4["reason"])


def test_recraft_receives_text_only():
    print("\ntest_recraft_receives_text_only")
    im = _img(register="SPATIAL_DIAGRAMMATIC",
              visual_anchors=["a corrugated metal roof", "the deck sits 3 metres up"],
              must_not_invent=["people", "signage"])
    p = AD.build_image_prompt(im, "Maya Flux")
    check("prompt is a string", isinstance(p, str) and len(p) > 80)
    check("register direction is present", "linework" in p or "drawing" in p)
    check("factual anchor carried", "raised timber structure" in p)
    check("clean visual anchor carried", "corrugated metal roof" in p)
    check("a violating visual anchor is stripped even here", "3 metres" not in p)
    check("must_not_invent carried", "signage" in p)
    check("no lettering instruction", "No lettering" in p)
    check("no named-artist imitation", "No named artist" in p)
    check("no base64 or path leaked", "data:" not in p and ".jpg" not in p)
    check("ratio follows function, not a fixed slot",
          AD.ratio_for(_img(function="SHOW_MECHANISM")) == "1:1"
          and AD.ratio_for(_img(function="ESTABLISH_PLACE")) == "16:9")


def test_registers_and_functions_are_the_declared_set():
    print("\ntest_registers_and_functions_are_the_declared_set")
    check("four registers", len(AD.REGISTERS) == 4)
    check("the four are the brief's four",
          set(AD.REGISTERS) == {"SPATIAL_DIAGRAMMATIC", "MATERIAL_EDITORIAL",
                                "ATMOSPHERIC_OBSERVATIONAL", "CONCEPTUAL_SYSTEMIC"})
    check("six functions", len(AD.FUNCTIONS) == 6)
    check("every register has prompt direction",
          all(r in AD._REGISTER_DIRECTION for r in AD.REGISTERS))
    check("no persona palette is enforced anywhere",
          "palette" not in AD.ART_DIRECTOR_SYSTEM.split("does not dictate")[0].split("PERSONA")[-1]
          or "does not dictate a medium" in AD.ART_DIRECTOR_SYSTEM)
    check("the core rule is in the prompt",
          "NEVER ILLUSTRATE DISABILITY" in AD.ART_DIRECTOR_SYSTEM)
    check("zero-is-valid is in the prompt",
          "ZERO IS A REAL ANSWER" in AD.ART_DIRECTOR_SYSTEM)
    check("never-more-certain is in the prompt",
          "NEVER MORE CERTAIN THAN THE ARTICLE" in AD.ART_DIRECTOR_SYSTEM)


def test_stale_architecture_cannot_become_a_factual_anchor():
    """THE WILDSUMACO REGRESSION, deterministic and offline.

    The run's ARCHITECTURE.json still argued from an ADA accessibility field. The settled
    article contains "ADA" and "accessib" zero times, because that claim was withdrawn
    from the live piece. Handed both, the art director spent one of two image slots on the
    withdrawn argument. This proves it cannot happen again at three separate points.
    """
    print("\ntest_stale_architecture_cannot_become_a_factual_anchor")
    settled = ("The pavilion floor is lifted above the natural ground and water passes "
               "beneath it. The station has an entry in a field-station directory where "
               "conditions are recorded field by field. The station is recorded as not "
               "open to the public.")
    check("the settled article really lacks the withdrawn terms",
          "ADA" not in settled and "accessib" not in settled.lower())

    stale = {"article_type": "FIELD_NOTE",
             "story_spine": "a pavilion read against its ADA accessibility field",
             "ending_move": "two records side by side, one of them the ADA field",
             "beats": [
                 {"beat_id": "B2", "concrete_carrier": "the pavilion floor above the natural ground",
                  "happens": "the floor is lifted", "concept_introduced": "permeability"},
                 {"beat_id": "B6", "concrete_carrier": "the ADA accessibility field on the "
                                                       "station's directory entry",
                  "happens": "the directory records accessibility as No",
                  "concept_introduced": "a foreign legal framework"},
             ]}

    # 1. THE DIGEST NEVER OFFERS THE STALE BEAT.
    d = AD.architecture_digest(stale, settled)
    ids = [b["beat_id"] for b in d["beats"]]
    check("the supported beat survives", "B2" in ids)
    check("the withdrawn beat is omitted", "B6" not in ids, ids)
    check("and the omission is recorded",
          "B6" in d.get("beats_omitted_as_unsupported_by_the_settled_article", []))
    check("architecture prose carrying the withdrawn term is dropped",
          "story_spine" not in d and "ending_move" not in d, sorted(d))
    blob = json.dumps(d)
    check("no ADA anywhere in the digest", "ADA" not in blob)
    check("no accessibility anywhere in the digest", "accessib" not in blob.lower())
    check("beat argument prose is withheld when reconciling",
          "happens" not in blob and "permeability" not in blob)

    # 2. THE PROMPT NEVER CARRIES IT EITHER.
    u = AD.build_user_prompt(settled, "The Upper Room", "", stale, "Maya Flux", None)
    check("prompt carries no ADA", "ADA" not in u)
    check("prompt carries no accessibility claim", "accessib" not in u.lower())
    check("prompt still carries the usable beat", "B2" in u)
    check("prompt states the article is authoritative",
          "THE SETTLED ARTICLE IS AUTHORITATIVE" in u or
          "THE SETTLED ARTICLE IS AUTHORITATIVE" in AD.ART_DIRECTOR_SYSTEM)

    # 3. A BRIEF THAT REACHES PAST IT ANYWAY IS STRIPPED.
    reaching = {"image_count": 2, "count_reasoning": "x", "images": [
        _img(placement="AFTER_BEAT:B2",
             factual_anchors=["the pavilion floor is lifted above the natural ground"]),
        _img(function="CONCEPTUAL_COVER", register="CONCEPTUAL_SYSTEMIC",
             placement="END",
             factual_anchors=["the directory records ADA accessibility as No"],
             alt_text="A record sheet with a row for accessibility marked No."),
    ]}
    rec, notes = AD.reconcile_brief(reaching, settled)
    check("the withdrawn anchor is stripped", notes["anchors_dropped"] and
          "ADA" in notes["anchors_dropped"][0])
    check("the image left with no anchor is dropped", notes["images_dropped"] == 1)
    check("image_count follows the drop", rec["image_count"] == 1, rec["image_count"])
    check("the supported image survives", rec["images"][0]["placement"] == "AFTER_BEAT:B2")
    check("no ADA survives reconciliation", "ADA" not in json.dumps(rec))

    # 4. THE TOKEN TEST ITSELF: ALL, not most.
    check("a majority overlap is not enough (the original bug)",
          AD.text_supports("the ADA accessibility field on the station's directory entry",
                           settled) is False)
    check("acronyms are caught despite being short",
          "ADA" in AD.content_tokens("the ADA field"))
    check("a fully supported phrase passes",
          AD.text_supports("the pavilion floor above the natural ground", settled) is True)
    check("ordinary inflection is not read as drift",
          AD.text_supports("conditions recorded field by field", settled) is True)
    check("an empty phrase supports nothing", AD.text_supports("", settled) is False)
    check("with no article text the digest is unfiltered",
          "B6" in [b["beat_id"] for b in AD.architecture_digest(stale)["beats"]])


def main():
    for fn in [test_image_count_is_the_first_decision,
               test_never_illustrate_disability,
               test_a_visual_observation_cannot_become_an_assertion,
               test_sidecar_digest_takes_only_the_allowed_slice,
               test_the_prompt_withholds_what_it_must,
               test_alt_text_must_be_real,
               test_placement_is_editorial_not_arithmetic,
               test_composition_may_not_reference_a_photograph,
               test_people_are_none_by_default,
               test_one_model_call_maximum_and_a_safe_fallback,
               test_recraft_receives_text_only,
               test_registers_and_functions_are_the_declared_set,
               test_stale_architecture_cannot_become_a_factual_anchor]:
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d of %d" % (len(FAILURES), CHECKS[0]))
        for f in FAILURES:
            print("   - %s" % f)
        sys.exit(1)
    print("ALL %d ART DIRECTOR CONTRACT CHECKS PASSED" % CHECKS[0])


if __name__ == "__main__":
    main()
