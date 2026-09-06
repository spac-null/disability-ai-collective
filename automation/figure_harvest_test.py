#!/usr/bin/env python3
"""figure_harvest_test.py -- publisher captions become text evidence; file names do not.

Deterministic HTML fixtures only. No network, no image bytes, no model, no fetch. Every
fixture below is hand-written except where a comment says it is reduced from a real page,
in which case the shapes (ArchDaily's `Image 3 of 31` gallery numbering, its `Content
Loader` spinner alt, Dezeen's <figure>/<figcaption> pairs, lazy-loaded data-src) are
copied from what those pages actually served on 2026-09-06.

The two things this file is really guarding:
  1. A sentence a publisher WROTE reaches the pack.
  2. Nothing a machine generated about a FILE ever does.

Stdlib only.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from new_engine_v1 import contracts as C
from new_engine_v1 import figures as F

FAILURES = []
CHECKS = [0]


def check(label, cond, detail=""):
    CHECKS[0] += 1
    print(("  PASS  %s" if cond else "  FAIL  %s") % label
          + (("" if cond else " -- " + str(detail)) if detail else ""))
    if not cond:
        FAILURES.append(label)


def caps(figs):
    return [f["caption"] for f in figs if f["caption"]]


def alts(figs):
    return [f["alt"] for f in figs if f["alt"]]


# ── 1. figure + figcaption ────────────────────────────────────────────────────
print("test_figure_with_figcaption")
FIXTURE_FIGCAPTION = """
<article>
  <p>The pavilion is 280 square metres.</p>
  <figure>
    <img src="/img/upper.jpg" alt="Wild Sumaco Research Pavilion">
    <figcaption>The upper level contains a bird observatory</figcaption>
  </figure>
  <figure>
    <img src="/img/lower.jpg" alt="Wild Sumaco Research Pavilion">
    <figcaption>The lower level contains research and analysis spaces</figcaption>
  </figure>
</article>
"""
figs = F.harvest(FIXTURE_FIGCAPTION, "https://example.org/a/b/page")
check("both captions are harvested", len(figs) == 2, figs)
check("the caption text is verbatim",
      "The upper level contains a bird observatory" in caps(figs), caps(figs))
check("provenance says it came from a figcaption",
      all(f["caption_source"] == "figcaption" for f in figs))
check("alt is kept alongside the caption",
      figs[0]["alt"] == "Wild Sumaco Research Pavilion", figs[0])
check("a relative reference is resolved against the page",
      figs[0]["image_url"] == "https://example.org/img/upper.jpg", figs[0]["image_url"])
check("no image byte is implied by the record",
      set(figs[0]) == set(C.FIGURE_FIELDS), sorted(figs[0]))

# ── 2. img alt, no figure ─────────────────────────────────────────────────────
print("\ntest_bare_img_alt")
FIXTURE_ALT = """
<div class="gallery">
  <img src="https://cdn.example.com/1.jpg" alt="Grey-brick facades of Irish house">
  <img src="https://cdn.example.com/2.jpg" alt="Wooden kitchen">
  <img src="https://cdn.example.com/3.jpg">
</div>
"""
figs = F.harvest(FIXTURE_ALT)
check("alt-only images are harvested", len(figs) == 2, figs)
check("the alt text is verbatim", "Wooden kitchen" in alts(figs), alts(figs))
check("provenance distinguishes alt from figcaption",
      all(f["caption_source"] == "alt" for f in figs))
check("caption stays empty when the publisher wrote none",
      all(f["caption"] == "" for f in figs))
check("an image with no words at all is not carried", len(figs) == 2)

# ── 3. plan / section labels ──────────────────────────────────────────────────
print("\ntest_type_hint_only_when_explicit")
FIXTURE_DRAWINGS = """
<figure><img src="/d1.png"><figcaption>Site plan</figcaption></figure>
<figure><img src="/d2.png"><figcaption>Cross section through the courtyard</figcaption></figure>
<figure><img src="/d3.png"><figcaption>Axonometric</figcaption></figure>
<figure><img src="/d4.png"><figcaption>Location map</figcaption></figure>
<figure><img src="/d5.png"><figcaption>Exterior Photography, Wood, Forest</figcaption></figure>
<figure><img src="/d6.png"><figcaption>The team sought to integrate the building into the surrounding forest</figcaption></figure>
<figure><img src="/d7.png"><figcaption>The practice had no plan to flatten the contours, and worked with them instead</figcaption></figure>
"""
figs = F.harvest(FIXTURE_DRAWINGS)
kinds = {f["caption"]: f["type_hint"] for f in figs}
check("an explicit site plan is PLAN", kinds.get("Site plan") == F.PLAN, kinds)
check("an explicit cross section is SECTION",
      kinds.get("Cross section through the courtyard") == F.SECTION, kinds)
check("an axonometric is DIAGRAM", kinds.get("Axonometric") == F.DIAGRAM, kinds)
check("a location map is MAP", kinds.get("Location map") == F.MAP, kinds)
check("publisher-typed photography is PHOTO",
      kinds.get("Exterior Photography, Wood, Forest") == F.PHOTO, kinds)
check("an ordinary sentence is OTHER",
      kinds.get("The team sought to integrate the building into the surrounding forest")
      == F.OTHER, kinds)
check("'plan' used as an intention in prose is NOT a drawing",
      kinds.get("The practice had no plan to flatten the contours, and worked with them "
                "instead") == F.OTHER, kinds)
check("every hint is in the contract's vocabulary",
      all(f["type_hint"] in C.FIGURE_TYPE_HINTS for f in figs))

print("\ntest_type_hint_is_never_read_off_a_url")
FIXTURE_URL_BAIT = """
<figure>
  <img src="https://cdn.example.com/site-plan-section-diagram-map.jpg">
  <figcaption>A room with the door open</figcaption>
</figure>
"""
figs = F.harvest(FIXTURE_URL_BAIT)
check("a filename full of drawing words hints nothing",
      figs[0]["type_hint"] == F.OTHER, figs[0])

# ── 4. credit ─────────────────────────────────────────────────────────────────
print("\ntest_credit")
FIXTURE_CREDIT = """
<figure><img src="/1.jpg"><figcaption>&copy; JAG Studio</figcaption></figure>
<figure><img src="/2.jpg" alt="Tollymore &copy;Johan Dehlin"></figure>
<figure><img src="/3.jpg"><figcaption>The courtyard in rain. Photography by Aisling Ward</figcaption></figure>
<figure><img src="/4.jpg"><figcaption>A stepped concrete plinth</figcaption></figure>
"""
figs = F.harvest(FIXTURE_CREDIT)
creds = [f["credit"] for f in figs]
check("a bare copyright line yields the credit", "JAG Studio" in creds, creds)
check("a credit inside alt text is found", "Johan Dehlin" in creds, creds)
check("'Photography by X' is found", "Aisling Ward" in creds, creds)
check("a caption with no credit yields none", "" in creds, creds)
check("the entity is decoded, not carried as &copy;",
      not any("&copy;" in (f["caption"] + f["alt"]) for f in figs), figs)

# ── 5. duplicates ─────────────────────────────────────────────────────────────
print("\ntest_duplicates")
FIXTURE_DUPES = """
<figure><img src="/hero.jpg" alt="Tollymore"><figcaption>A cluster of grey volumes</figcaption></figure>
<figure><img src="/hero.jpg" alt="Tollymore"><figcaption>A cluster of grey volumes</figcaption></figure>
<img src="/hero.jpg" alt="Tollymore">
<img src="/hero.jpg" alt="Tollymore">
<figure><img src="/hero.jpg" alt="Tollymore"><figcaption>Seen from the lane</figcaption></figure>
"""
figs = F.harvest(FIXTURE_DUPES)
check("an identical figure is carried once", len(caps(figs)) == 2, caps(figs))
check("the same photo under a different caption is kept",
      sorted(caps(figs)) == ["A cluster of grey volumes", "Seen from the lane"], caps(figs))
check("repeated alt-only thumbnails collapse to one", len(figs) == 3, figs)

# ── 6. gallery bound ──────────────────────────────────────────────────────────
print("\ntest_a_huge_gallery_cannot_dominate_a_pack_entry")
BIG = "".join(
    '<figure><img src="/g%d.jpg" alt="gallery shot %d">'
    '<figcaption>Gallery image number %d in the set</figcaption></figure>' % (i, i, i)
    for i in range(400))
figs = F.harvest(BIG)
check("the collection is bounded", len(figs) == F.MAX_FIGURES, len(figs))
check("the bound is the documented one", F.MAX_FIGURES == 12, F.MAX_FIGURES)

print("\ntest_captioned_figures_outrank_alt_only_ones_at_the_bound")
MIXED = ("".join('<img src="/t%d.jpg" alt="thumbnail caption %d">' % (i, i)
                 for i in range(30))
         + "".join('<figure><img src="/f%d.jpg">'
                   '<figcaption>A sentence a person wrote, number %d</figcaption>'
                   '</figure>' % (i, i) for i in range(5)))
figs = F.harvest(MIXED)
check("all five written captions survive the cut", len(caps(figs)) == 5, caps(figs))
check("the alt-only thumbnails fill only the remaining room",
      len(figs) == F.MAX_FIGURES, len(figs))
check("a written caption is never dropped for a generated one",
      all(f["caption_source"] == "figcaption" for f in figs[:5]), figs[:5])

# ── 7. machine metadata must never become evidence ────────────────────────────
print("\ntest_machine_metadata_is_refused")
# Reduced from a real ArchDaily page: gallery numbering, the spinner, and a CDN slug.
FIXTURE_METADATA = """
<img src="https://images.adsttc.com/media/images/6a47/6064/estacion.jpg"
     alt="WildSumaco Research Pavilion / Caa Pora Arquitectura - Image 2 of 31">
<img src="https://assets.adsttc.com/doodles/flat/loader-blue.gif" alt="Content Loader">
<figure><img src="/x.jpg"><figcaption>estacion-wildsumaco-hero-1600x900.jpg</figcaption></figure>
<figure><img src="/y.jpg"><figcaption>1600x900</figcaption></figure>
<figure><img src="/z.jpg"><figcaption>https://cdn.example.com/z.jpg</figcaption></figure>
<figure><img src="/w.jpg"><figcaption>a1f4c9e02b77d3ff5cab8801</figcaption></figure>
<img src="/logo.svg" alt="Logo">
<img src="/sp.gif" alt="  ">
<figure><img src="/real.jpg"><figcaption>The lower level contains research and analysis spaces</figcaption></figure>
"""
figs = F.harvest(FIXTURE_METADATA)
check("only the one real sentence survives", len(figs) == 1, figs)
check("...and it is the sentence a person wrote",
      figs[0]["caption"] == "The lower level contains research and analysis spaces", figs)
for bad in ("Image 2 of 31", "Content Loader", "1600x900", "Logo",
            "estacion-wildsumaco-hero-1600x900.jpg", "a1f4c9e02b77d3ff5cab8801"):
    check("refused: %r" % bad,
          not any(bad in (f["caption"] + f["alt"]) for f in figs))
check("a URL never lands in a caption",
      not any(f["caption"].startswith("http") for f in figs))

print("\ntest_the_metadata_rule_is_directly_addressable")
for s in ("Image 12 of 31", "Content Loader", "1600 x 900", "hero.jpg",
          "https://x.example/a.png", "", "  ", "ab"):
    check("rejected: %r" % s, F._looks_like_machine_metadata(s))
for s in ("The upper level contains a bird observatory", "Site plan",
          "It is formed of a cluster of grey volumes", "© JAG Studio"):
    check("accepted: %r" % s, not F._looks_like_machine_metadata(s))

# ── 8. malformed markup ───────────────────────────────────────────────────────
print("\ntest_malformed_markup_never_raises")
MALFORMED = [
    "<figure><img src=/a.jpg alt=Unquoted><figcaption>Half a caption",
    "<figure><figcaption>No image here at all</figcaption></figure>",
    "<img src='/b.jpg' alt='Single quotes'>",
    "<IMG SRC='/c.jpg' ALT='Upper case tags'>",
    "<figure><img src='/d.jpg' alt='nested'><figure><img src='/e.jpg'>"
    "<figcaption>Inner</figcaption></figure></figure>",
    "<img src=",
    "<figure" * 500,
    "<img src='/f.jpg' alt='&amp; entities &lt;here&gt;'>",
]
for i, frag in enumerate(MALFORMED):
    try:
        got = F.harvest(frag)
        ok = isinstance(got, list)
    except Exception as e:                                            # noqa: BLE001
        ok = False
        got = "%s: %s" % (type(e).__name__, e)
    check("malformed fixture %d parses to a list" % i, ok, got)
check("an unquoted attribute is still read",
      F.harvest(MALFORMED[0])[0]["alt"] == "Unquoted", F.harvest(MALFORMED[0]))
check("uppercase tags are read",
      F.harvest(MALFORMED[3])[0]["alt"] == "Upper case tags")
check("entities are decoded",
      F.harvest(MALFORMED[7])[0]["alt"] == "& entities <here>",
      F.harvest(MALFORMED[7]))

# ── 9. no images ──────────────────────────────────────────────────────────────
print("\ntest_no_images")
for label, frag in (("empty string", ""), ("None", None), ("not a string", 12),
                    ("prose only", "<p>Six volumes on a stepped plinth.</p>"),
                    ("images with no words", '<img src="/a.jpg"><img src="/b.jpg">')):
    check("%s yields no figures" % label, F.harvest(frag) == [], F.harvest(frag))

# ── 10. the contract ──────────────────────────────────────────────────────────
print("\ntest_the_pack_contract_accepts_and_polices_figures")


def pack_with(figures):
    text = ("The pavilion is 280 square metres and was completed in 2025. " * 6)
    src = {"source_id": "S0", "role": "ANCHOR", "url": "https://example.org/a",
           "accessed_at": "2026-09-06T00:00:00Z", "sha256": C.sha256_text(text),
           "fetch_status": "ok", "content_length": len(text), "text": text,
           "excerpts": []}
    if figures is not None:
        src["figures"] = figures
    return C.Artifact(stage=C.RESEARCH_PACK, created_at="2026-09-06T00:00:00Z",
                      payload={"subject": "s", "sources": [src],
                               "coverage": {}, "pack_sha256": "x",
                               "sufficiency": {"verdict": "ARTICLE"}})


GOOD = [{"image_url": "https://example.org/1.jpg",
         "caption": "The upper level contains a bird observatory",
         "caption_source": "figcaption", "alt": "Wild Sumaco", "credit": "",
         "type_hint": "OTHER"}]


def violates(figures):
    try:
        C.validate(pack_with(figures))
        return ""
    except C.ContractViolation as e:
        return str(e)


check("a pack with no figures key still validates", violates(None) == "", violates(None))
check("an empty list validates", violates([]) == "", violates([]))
check("a well-formed figure validates", violates(GOOD) == "", violates(GOOD))

bad_missing = [dict(GOOD[0])]
del bad_missing[0]["type_hint"]
check("a missing field is refused", "missing field" in violates(bad_missing),
      violates(bad_missing))
check("an unknown type_hint is refused",
      "type_hint" in violates([dict(GOOD[0], type_hint="PHOTOGRAPH")]))
check("an unknown caption_source is refused",
      "caption_source" in violates([dict(GOOD[0], caption_source="model")]))
check("a figure with no words is refused",
      "no caption and no alt" in violates([dict(GOOD[0], caption="", alt="")]))
check("a caption that is a URL is refused",
      "image reference, not text" in violates(
          [dict(GOOD[0], caption="https://example.org/1.jpg")]))
check("an alt that repeats the image reference is refused",
      "image reference, not text" in violates(
          [dict(GOOD[0], alt="https://example.org/1.jpg")]))
check("a non-object figure is refused", "non-object" in violates(["a string"]))

print("\ntest_harvest_output_satisfies_the_contract_it_ships_under")
for name, frag in (("figcaption", FIXTURE_FIGCAPTION), ("alt", FIXTURE_ALT),
                   ("drawings", FIXTURE_DRAWINGS), ("credit", FIXTURE_CREDIT),
                   ("dupes", FIXTURE_DUPES), ("metadata", FIXTURE_METADATA),
                   ("gallery", BIG), ("mixed", MIXED)):
    check("%s fixture validates as a pack" % name, violates(F.harvest(frag)) == "",
          violates(F.harvest(frag)))

# ── 11. the promises this phase makes ─────────────────────────────────────────
print("\ntest_phase_1_promises")
HERE = os.path.dirname(os.path.abspath(__file__))
fig_src = open(os.path.join(HERE, "new_engine_v1", "figures.py")).read()
res_src = open(os.path.join(HERE, "new_engine_v1", "research.py")).read()

def code_of(src):
    """Source with its module docstring removed.

    These files DISCUSS what they must not do -- figures.py says in prose that it never
    downloads an image and that `include_images=True` is not switched on anywhere -- so a
    naive substring scan of the whole file reports its own documentation as a violation.
    Found exactly that way on the first run of this test. Scan the code, read the prose.
    """
    parts = src.split('"""')
    return "".join(parts[2:]) if len(parts) >= 3 else src


FIG_CODE, RES_CODE = code_of(fig_src), code_of(res_src)

check("figures.py opens no socket",
      not any(m in FIG_CODE for m in ("urllib.request", "urlopen", "socket", "requests",
                                      "http.client", "urlretrieve")),
      "urllib.parse is imported, for urljoin only")
check("figures.py makes no model call",
      not any(m in FIG_CODE for m in ("provider", ".complete(", "_ask(", "openai",
                                      "openrouter", "anthropic")))
check("figures.py opens no file and reads no image bytes",
      not any(m in FIG_CODE for m in ("open(", ".read()", "base64", "b64decode",
                                      "Image.", "PIL")))
check("figures.py hashes nothing -- it has no bytes to hash",
      "sha256" not in FIG_CODE and "hashlib" not in FIG_CODE)
check("include_images was NOT switched on",
      "include_images=True" not in RES_CODE and "include_images=True" not in FIG_CODE)
check("body extraction is untouched -- text, length and hash come from strip_html",
      "content_length=len(text), sha256=sha256_text(text)" in RES_CODE)
check("the harvest reads the SAME html the body text came from",
      'figs = FIG.harvest(html, rec.get("url", ""))' in RES_CODE)
check("figures ride along only when present, like document provenance",
      'if s.get("figures"):' in RES_CODE)
check("research.py gained no new network call",
      RES_CODE.count("urlopen") == 2,
      "two before this change (the ordinary fetch and the search POST), two after; "
      "got %d" % RES_CODE.count("urlopen"))
check("...and figures.py contributes none of its own",
      "urlopen" not in FIG_CODE)
check("the module says plainly it is not yet wired into the ledger",
      "IT IS NOT YET WIRED INTO THE LEDGER" in fig_src)

comp_src = open(os.path.join(HERE, "new_engine_v1", "composition.py")).read()
check("the composition engine does not import the harvester",
      "figures" not in comp_src.split("\n\n")[0] and "import figures" not in comp_src)
check("no composition stage reads the pack's figures field",
      '"figures"' not in comp_src and "'figures'" not in comp_src
      and '.get("figures")' not in comp_src,
      "retention only in this phase; feeding the ledger is a separate decision "
      "taken on its own evidence")

print("\n" + "=" * 62)
if FAILURES:
    print("FIGURE HARVEST: %d of %d CHECKS FAILED" % (len(FAILURES), CHECKS[0]))
    for f in FAILURES:
        print("  - %s" % f)
    sys.exit(1)
print("ALL %d FIGURE HARVEST CHECKS PASSED" % CHECKS[0])
