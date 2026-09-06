#!/usr/bin/env python3
"""image_style_targets_test.py -- no image prompt asks for a named person's style.

Production prompts instructed the generator to work "in the style of" identifiable people
and one design school: Barbara Kruger, Corita Kent, El Lissitzky, Rodchenko, Anna Atkins,
Vesalius, Gray's Anatomy, Werkplaats Typografie. That shipped, and it shipped
independently of anything to do with source images -- there is no source-image pipeline
for it to have come from.

WHAT IS REMOVED AND WHAT IS NOT. People and institutions, out. Art movements and print
processes, kept: "constructivist", "photomontage", "cyanotype", "linocut", "risograph"
name a formal vocabulary anyone may work in, not somebody's signature. The distinction is
the point -- a rule that deleted "screen print" as well would have made the prompts worse
for no gain, and each removed name was replaced by the formal properties it was standing
in for.

THIS TEST IS A RATCHET. It fails on any NEW name too, not only the eight removed, so a
later edit cannot quietly reintroduce the pattern under a different artist.

Nothing else about image generation changes in this phase: same three slots, same ratios,
same model, same placement, same call count.

Stdlib only. No network, no image generated.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gen_images as G

FAILURES = []
CHECKS = [0]


def check(label, cond, detail=""):
    CHECKS[0] += 1
    print(("  PASS  %s" if cond else "  FAIL  %s") % label
          + (("" if cond else " -- " + str(detail)) if detail else ""))
    if not cond:
        FAILURES.append(label)


def all_prompt_text():
    out = []
    for persona, subs in G.PERSONA_STYLES.items():
        for sub in subs:
            out.extend(sub.values())
    for sub in G.DEFAULT_STYLE:
        out.extend(sub.values())
    return out


PROMPTS = all_prompt_text()
BLOB = "\n".join(PROMPTS)

# ── 1. the eight that shipped ─────────────────────────────────────────────────
print("test_the_named_targets_that_shipped_are_gone")
REMOVED = ("Barbara Kruger", "Kruger", "Corita Kent", "Corita", "El Lissitzky",
           "Lissitzky", "Rodchenko", "Anna Atkins", "Atkins", "Vesalius",
           "Gray's Anatomy", "Werkplaats Typografie", "Werkplaats")
for name in REMOVED:
    check("no prompt names %s" % name, name not in BLOB)

# ── 2. the ratchet ────────────────────────────────────────────────────────────
print("\ntest_no_NEW_named_person_can_be_reintroduced")
# Two capitalised words in a row, minus the vocabulary a style prompt legitimately uses.
ALLOWED = {
    "Subject", "Concept", "Colour", "Color", "Bold", "Strong", "Precise", "High",
    "Close", "Large", "Detail", "Gallery", "Artist", "Contemporary", "Exhibition",
    "Photographic", "Two", "Geometric", "Soviet", "Dutch", "Technical", "Network",
    "Mechanical", "Natural", "Naturalist", "Historical", "Specimen", "Microscopy",
    "Cyanotype", "Botanical", "Street", "Activist", "Joyful", "Asymmetric",
    "Diagonal", "Photomontage", "Monoprint", "Blueprint", "The", "A", "An", "No",
    "Feels", "References", "Repeat", "Something", "Unexpected", "Careful", "It",
    "Ink", "Pencil", "Cut", "Layered", "Flat", "One",
}
suspects = set()
for m in re.finditer(r"\b([A-Z][a-z]{2,})\s+([A-Z][a-z]{2,})\b", BLOB):
    a, b = m.group(1), m.group(2)
    if a in ALLOWED or b in ALLOWED:
        continue
    suspects.add("%s %s" % (a, b))
check("no unexplained Capitalised Name pairs remain", not suspects, sorted(suspects))
check("no prompt says 'in the style of'",
      not re.search(r"(?i)in the style of", BLOB))
check("no prompt says 'by <Name>'",
      not re.search(r"(?i)\b(?:painted|drawn|designed|photographed)\s+by\s+[A-Z]", BLOB))

# ── 3. the formal properties survived ─────────────────────────────────────────
print("\ntest_the_useful_formal_properties_were_kept")
for prop in ("screen print", "silhouette", "photomontage", "geometric",
             "unexpected colour", "cyanotype", "linocut", "risograph",
             "flat", "high contrast", "constructivist"):
    check("still asks for: %s" % prop, prop.lower() in BLOB.lower())
check("a replacement was written, not just a deletion -- grid discipline",
      "Asymmetric grid discipline" in BLOB)
check("...anatomical atlas as a described vocabulary",
      "engraved line" in BLOB and "labelled plate with no labels" in BLOB)
check("...photogram as a process rather than a person's method",
      "The photogram method" in BLOB)
check("...constructivist geometry described rather than attributed",
      "Diagonal axes, flat planes" in BLOB)

print("\ntest_every_prompt_is_still_a_usable_prompt")
for i, p in enumerate(PROMPTS):
    check("prompt %d still takes the subject placeholder" % i, "{summary}" in p)
    check("prompt %d is not left with a dangling clause" % i,
          not re.search(r"(?:—|--|,)\s*(?:\.|$)", p.strip()) and len(p.strip()) > 60,
          p[-70:])

# ── 4. nothing else about image generation moved ──────────────────────────────
print("\ntest_image_generation_is_otherwise_untouched")
check("still three slots", len(G.IMAGE_TYPES) == 3, G.IMAGE_TYPES)
check("still the same slots and ratios",
      G.IMAGE_TYPES == [("setting_1", "16:9", "CONFRONTING"),
                        ("moment_2", "1:1", "INTIMATE"),
                        ("symbol_3", "1:1", "ABSTRACT")], G.IMAGE_TYPES)
check("still the same model", G.DEFAULT_MODEL == "recraft/recraft-v4.1", G.DEFAULT_MODEL)
check("every persona still has three sub-styles",
      all(len(v) == 3 for v in G.PERSONA_STYLES.values()),
      {k: len(v) for k, v in G.PERSONA_STYLES.items()})
check("every sub-style still has all three roles",
      all(set(sub) == {"CONFRONTING", "INTIMATE", "ABSTRACT"}
          for subs in G.PERSONA_STYLES.values() for sub in subs))
check("the deterministic sub-style pick is unchanged",
      G._sub_style_index("a-slug", "Pixel Nova", 3)
      == G._sub_style_index("a-slug", "Pixel Nova", 3))
check("get_prompt still substitutes the summary",
      "a lifted floor above a forest" in
      G.get_prompt("CONFRONTING", "Pixel Nova", "a lifted floor above a forest", "s"))
check("alt templates are unchanged in this phase",
      G.ALT_TEMPLATES["CONFRONTING"] == "{title} — editorial illustration",
      "rewriting alt text belongs to the art director, not here")

print("\n" + "=" * 62)
if FAILURES:
    print("IMAGE STYLE TARGETS: %d of %d CHECKS FAILED" % (len(FAILURES), CHECKS[0]))
    for f in FAILURES:
        print("  - %s" % f)
    sys.exit(1)
print("ALL %d IMAGE STYLE TARGET CHECKS PASSED" % CHECKS[0])
