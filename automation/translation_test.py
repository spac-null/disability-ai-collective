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
    check("it names the exact English bytes it renders",
          "translation_source_sha256" in text)
    check("NO ENGINE PROVENANCE IS COPIED",
          all(k not in text for k in ("engine_run", "fact_check_text_sha256",
                                      "publication_eligible", "provider_model",
                                      "engine_generation")), text[:500])
    check("the persona and the date are the English article's",
          '"Maya Flux"' in text and "date: 2026-09-06" in text)
    check("and the image is not regenerated, only referenced",
          '"/assets/x.jpg"' in text)

print("\ntest_the_language_registry_is_the_whole_configuration")
check("Dutch is configured", "nl" in TP.LANGUAGES)
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
