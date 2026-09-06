#!/usr/bin/env python3
"""translation_test.py -- the derivative edition stage, on its bounds only.

The English bundle is canonical and already checked. What this suite holds down is that a
translation cannot quietly change what is true, cannot reach back into the English article,
and cannot publish while held.

Stdlib only, no network.
"""
import json
import os
import pathlib
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import translate_publication as TP

FAILURES, CHECKS = [], [0]


def check(label, cond, detail=""):
    CHECKS[0] += 1
    print(("  PASS  %s" if cond else "  FAIL  %s") % label
          + (("" if cond else " -- " + str(detail)) if detail else ""))
    if not cond:
        FAILURES.append(label)


EN = {"article": "The pavilion is 280 square metres, completed in 2025. The directory "
                 "entry for WildSumaco records ADA accessibility as No. The architects "
                 "say the upper room may be open to all.",
      "title": "The Upper Room", "dek": "A pavilion and a directory entry.",
      "homepage_excerpt": "An excerpt.", "meta_description": "A meta description.",
      "social_hook": "A hook."}


def nl(article, **kw):
    d = {"article": article, "title": "De bovenkamer", "dek": "Een paviljoen.",
         "homepage_excerpt": "Een fragment.", "meta_description": "Een omschrijving.",
         "social_hook": "Een haakje."}
    d.update(kw)
    return d


print("test_the_cheap_pass_sees_what_arithmetic_can")
good = nl("Het paviljoen is 280 vierkante meter, opgeleverd in 2025. De registratie voor "
          "WildSumaco vermeldt ADA-toegankelijkheid als No. De architecten zeggen dat de "
          "bovenste ruimte voor iedereen open kan zijn.")
check("a faithful edition passes the mechanical pass",
      TP.mechanical_findings(EN, good) == [], TP.mechanical_findings(EN, good))
f = TP.mechanical_findings(EN, nl("Het paviljoen is opgeleverd in 2025. De registratie "
                                  "voor WildSumaco vermeldt ADA-toegankelijkheid als No."))
check("a dropped number is caught", any(x["category"] == "NUMBERS" for x in f), f)
f = TP.mechanical_findings(EN, nl("Het paviljoen is 280 vierkante meter, opgeleverd in "
                                  "2025. De registratie vermeldt toegankelijkheid als "
                                  "No."))
check("a dropped name is caught", any(x["category"] == "NAMES" for x in f), f)
f = TP.mechanical_findings(EN, nl("Het paviljoen is 280 vierkante meter uit 2025 en kostte "
                                  "1400000 euro. WildSumaco vermeldt No."))
check("an added number is caught",
      any(x["category"] == "NUMBERS" and x["translated"] for x in f), f)
check("an inflected demonym is not a dropped name",
      not [x for x in TP.mechanical_findings(
          {"article": "The Ecuadorian studio worked on the Andean slope with WildSumaco."},
          {"article": "De Ecuadoriaanse studio werkte op de Andes-helling met WildSumaco."})
          if x["category"] == "NAMES"],
      TP.mechanical_findings(
          {"article": "The Ecuadorian studio worked on the Andean slope with WildSumaco."},
          {"article": "De Ecuadoriaanse studio werkte op de Andes-helling met WildSumaco."}))
check("a name that is genuinely nowhere is still caught",
      [x for x in TP.mechanical_findings(
          {"article": "The Ecuadorian studio Caa Pora worked on the slope."},
          {"article": "De Ecuadoriaanse studio werkte op de helling."})
       if x["category"] == "NAMES"])
check("Dutch decimal and thousand separators are not a changed number",
      TP._numbers("3.5 and 1,000") == TP._numbers("3,5 en 1.000"),
      (TP._numbers("3.5 and 1,000"), TP._numbers("3,5 en 1.000")))

print("\ntest_a_held_translation_cannot_publish")
src = pathlib.Path(TP.__file__).read_text()
check("the writer refuses a non-PASS verdict",
      'if fid["verdict"] != "PASS":' in src and "refusing to write a held translation" in src)
check("preview is the default and writes nothing into the repo",
      '"--write", action="store_true"' in src)
check("one correction pass, then no loop",
      src.count("corrections=fid[\"findings\"]") == 1)

print("\ntest_nothing_flows_back_into_the_english_article")
with tempfile.TemporaryDirectory() as d:
    p = pathlib.Path(d) / "2026-09-06-the-upper-room-at-wildsumaco.md"
    p.write_text('---\nlayout: "post"\ntitle: "The Upper Room"\ndate: 2026-09-06\n'
                 'author: "Maya Flux"\nengine_run: "production-x"\n'
                 'fact_check_text_sha256: "abc"\nimage: /assets/x.jpg\n---\n\nBody text.\n')
    fm, body = TP.read_post(p)
    TP.link_english(p, "nl")
    after_fm, after_body = TP.read_post(p)
    check("the English body is untouched", after_body == body, after_body[:60])
    check("only a link is added", set(after_fm) - set(fm) == {"translation_nl"},
          set(after_fm) - set(fm))
    check("and it points at the language collection",
          after_fm["translation_nl"] == "/nl/the-upper-room-at-wildsumaco/",
          after_fm.get("translation_nl"))
    TP.link_english(p, "nl")
    check("linking twice adds nothing",
          pathlib.Path(p).read_text().count("translation_nl") == 1)

    en = {"article": "Body text.", "front_matter": after_fm, "title": "The Upper Room",
          "dek": "", "homepage_excerpt": "", "meta_description": "", "social_hook": "",
          "image_alt": ""}
    TP.REPO = pathlib.Path(d)
    out = TP.write_translation("nl", p, en, nl("Nederlandse tekst."))
    text = out.read_text()
    check("the translation lands in the language collection",
          out.parent.name == "_nl", str(out))
    check("it carries the Dutch title", '"De bovenkamer"' in text)
    check("it declares its language", 'lang: "nl"' in text)
    check("it links back to the English article",
          'translation_of: "/2026/09/06/the-upper-room-at-wildsumaco/"' in text, text[:400])
    check("it names the exact frozen bundle it renders, not just the body",
          "translation_source_bundle_sha256" in text, text[:500])
    check("and that hash covers the packaging too",
          TP.bundle_sha256(en) != TP.bundle_sha256(dict(en, dek="a new dek")))
    check("NO ENGINE PROVENANCE IS COPIED",
          all(k not in text for k in ("engine_run", "fact_check_text_sha256",
                                      "publication_eligible", "provider_model",
                                      "engine_generation")), text[:500])
    check("the persona and the date are the English article's",
          '"Maya Flux"' in text and "date: 2026-09-06" in text)
    check("and the image is not regenerated, only referenced",
          '"/assets/x.jpg"' in text)

print("\ntest_the_four_correctness_rules")
src = pathlib.Path(TP.__file__).read_text()
check("the correction pass is handed the edition it corrects",
      "previous=tr" in src and "a correction pass needs the edition it is correcting" in src)
check("image alt text is inside both fidelity passes",
      '("article", "image_alt") + BUNDLE_FIELDS' in src and 'IMAGE_ALT: %s" % en' in src)
en_img = {"article": 'Text.\n<figure><img src="{{ site.baseurl }}/assets/a_moment_2.jpg" '
                     'alt="x"></figure>\nMore.', "image_alt": "A caption"}
tr_same = {"article": 'Tekst.\n<figure><img src="{{ site.baseurl }}/assets/a_moment_2.jpg" '
                      'alt="y"></figure>\nMeer.', "image_alt": "Een onderschrift"}
check("translated alt text alone is not a finding",
      not [f for f in TP.mechanical_findings(en_img, tr_same) if f["category"] == "IMAGES"],
      TP.mechanical_findings(en_img, tr_same))
tr_moved = {"article": "Tekst. Meer.", "image_alt": "Een onderschrift"}
check("a dropped figure is a finding",
      [f for f in TP.mechanical_findings(en_img, tr_moved) if f["category"] == "IMAGES"])
tr_renamed = {"article": 'Tekst.\n<figure><img src="{{ site.baseurl }}/assets/other.jpg" '
                         'alt="y"></figure>\nMeer.', "image_alt": "x"}
check("a renamed asset is a finding",
      [f for f in TP.mechanical_findings(en_img, tr_renamed) if f["category"] == "IMAGES"])
check("no English packaging is generated for a pre-package article",
      "editorial_package" not in src and "fields_absent" in src)

print("\ntest_an_edition_carries_no_line_the_original_lacks")
src = pathlib.Path(TP.__file__).read_text()
check("the schema is built from the fields that exist",
      "def translate_schema(present" in src and "translate_schema(present," in src)
check("the prompt says so explicitly", "THIS ARTICLE HAS NO %s" in src)
check("and a field the English lacks is dropped from the result, not trusted",
      'if f in present else ""' in src)


print("\ntest_the_checker_knows_the_packaging_is_rewritten")
check("the fidelity prompt says a retitle is not a changed name",
      "THE PACKAGING IS REWRITTEN BY DESIGN" in TP.FIDELITY_SYSTEM
      and "is not a changed NAME" in TP.FIDELITY_SYSTEM)
check("and still holds packaging to the no-new-claim rule",
      "a fact, a relationship or a certainty" in TP.FIDELITY_SYSTEM)


print("\ntest_the_language_registry_is_the_whole_configuration")
check("Dutch is configured", "nl" in TP.LANGUAGES)
check("the collection file is named for the slug the permalink renders",
      TP.translation_path("nl", pathlib.Path("2026-09-06-the-upper-room.md")).name
      == "the-upper-room.md")
for k in ("name", "endonym", "collection", "url_prefix", "register"):
    check("nl declares %s" % k, k in TP.LANGUAGES["nl"])
cfg = pathlib.Path(TP.__file__).parent.parent / "_config.yml"
check("the site has a matching collection", "\n  nl:\n" in cfg.read_text())

print("\n" + "-" * 60)
if FAILURES:
    print("%d FAILURE(S):" % len(FAILURES))
    for f in FAILURES:
        print("  - " + f)
    sys.exit(1)
print("ALL %d TRANSLATION TESTS PASSED" % CHECKS[0])
