#!/usr/bin/env python3
"""
STYLE LAB — 10 image aesthetic experiments
Generates one image per style using the same subject, saves to assets/,
writes style-lab.html overview page.
"""

import os, sys, urllib.parse, urllib.request, time, json
from pathlib import Path

POLLINATIONS_KEY = os.environ.get("POLLINATIONS_API_KEY", "")
BASE = Path("/srv/data/openclaw/workspaces/ops/disability-ai-collective")
ASSETS = BASE / "assets"
W, H = 800, 450

# ── Fixed subject (consistent across all styles for comparison) ──────────────
PERSON = "person in manual wheelchair, hands gripping wheel rim, low-angle close"
PLACE  = "cracked urban sidewalk at dusk, broken curb cut, amber puddle reflections"
OBJ    = "worn wheelchair wheel cross-section, tread and spokes in raking side light"
ACCENT = "cobalt blue"

# ── 10 style recipes ─────────────────────────────────────────────────────────
STYLES = [
    {
        "id": "raw-linocut",
        "name": "Raw Linocut",
        "desc": "Deep hand-carved relief, stark black & cream, visible gouge marks",
        "prompt": (
            f"raw woodblock linocut relief print, {OBJ} as bold central motif, "
            f"deep hand-carved gouge lines, stark black ink on cream paper, "
            f"visible tool marks and pressure ridges, uneven ink coverage, "
            f"irregular stamp edges, protest woodcut tradition, "
            f"no color, no gradients, no photorealism, no text"
        ),
    },
    {
        "id": "silkscreen-pop",
        "name": "Silkscreen Pop",
        "desc": "Warhol-style off-registration, flat {accent} field, ink bleed",
        "prompt": (
            f"silkscreen print, {PERSON}, "
            f"deliberate off-registration color separation in {ACCENT} and black, "
            f"flat bold color fields, ink bleed and haloing at edges, "
            f"Warhol factory energy meets disability pride poster, "
            f"post-pop activist visual language, no gradients, no text"
        ),
    },
    {
        "id": "glitch-corrupt",
        "name": "Glitch Corrupt",
        "desc": "RGB channel split, VHS artifacts, pixel sorting, broken codec",
        "prompt": (
            f"digital glitch art, {PERSON}, "
            f"RGB channel split displacement, VHS scan-line artifacts, "
            f"pixel sorting vertical bands, broken codec freeze frame, "
            f"data corruption aesthetic, {ACCENT} channel dominant, "
            f"net art meets crip cyborg theory, no clean edges, no text"
        ),
    },
    {
        "id": "scratch-film",
        "name": "Scratch Film",
        "desc": "Hand-scratched emulsion, Brakhage-style, light leaks, celluloid damage",
        "prompt": (
            f"hand-scratched film emulsion, {PLACE}, {PERSON}, "
            f"Stan Brakhage experimental film still, light leak burns at frame edges, "
            f"physical celluloid scratches and abrasion, amber and {ACCENT} chemical stains, "
            f"sprocket holes visible on border, grain storm in shadows, "
            f"structural film energy, no digital clean, no text"
        ),
    },
    {
        "id": "pixel-strict",
        "name": "Strict 8-bit Pixel",
        "desc": "16-color ZX Spectrum palette, chunky grid, demoscene, no anti-aliasing",
        "prompt": (
            f"strict 8-bit pixel art, {PERSON}, "
            f"ZX Spectrum 16-color limited palette with {ACCENT} dominant, "
            f"large chunky pixel grid, zero anti-aliasing, color clash artifacts, "
            f"demoscene aesthetic, crip tech nostalgia, "
            f"no gradients, no smooth edges, no text"
        ),
    },
    {
        "id": "split-montage",
        "name": "Split Montage",
        "desc": "Hard razor-edge split, two opposing visual worlds, Barbara Kruger energy",
        "prompt": (
            f"photomontage hard split composition, left half {PLACE} in {ACCENT} duotone, "
            f"right half {OBJ} in stark black and white, "
            f"razor-clean vertical divide, Barbara Kruger compositional language, "
            f"flat color field against coarse texture, cut-paper collage energy, "
            f"disability justice visual politics, no text"
        ),
    },
    {
        "id": "dada-collage",
        "name": "Dada Collage",
        "desc": "Torn magazine paste-up, Hannah Höch energy, mismatched scales, crip body politics",
        "prompt": (
            f"Dada photomontage collage, {PERSON} fragmented and reassembled, "
            f"torn magazine page textures layered, Hannah Höch energy, "
            f"mismatched scales and perspectives, paste residue at torn edges, "
            f"{ACCENT} newsprint fragments, crip body politics visual language, "
            f"overlapping cut-and-paste fragments, no clean composition, no text"
        ),
    },
    {
        "id": "mimeograph",
        "name": "Mimeograph Newsletter",
        "desc": "1970s activist pamphlet, smeared purple ink, ghosting, crip liberation document",
        "prompt": (
            f"mimeograph newsletter print, {PERSON}, "
            f"1970s crip liberation movement pamphlet quality, "
            f"smeared purple-blue duplicator ink, double-impression ghosting, "
            f"uneven ink saturation, slightly skewed frame, lo-fi activist document, "
            f"visible paper grain, no halftone dots, no clean lines, no text"
        ),
    },
    {
        "id": "cyanotype",
        "name": "Cyanotype Blueprint",
        "desc": "Prussian blue photogram, white silhouette contact print, sun-exposure marks",
        "prompt": (
            f"cyanotype photogram, {OBJ} as white silhouette on prussian blue ground, "
            f"sun-exposure marks and uneven wash, chemical tide lines at edges, "
            f"technical blueprint meets body politics, "
            f"Anna Atkins tradition meets crip material culture, "
            f"two-tone only, no color photography, no text"
        ),
    },
    {
        "id": "letterpress-broadside",
        "name": "Letterpress Broadside",
        "desc": "Deep impression on cotton stock, ink squeeze, wood type, disability broadside",
        "prompt": (
            f"letterpress printing, {PLACE}, "
            f"deep impression on thick cotton paper, ink squeeze at image edges, "
            f"mixed wood type and {ACCENT} ink, "
            f"disability justice broadside tradition, "
            f"visible paper compression marks, slight over-inking in shadows, "
            f"political print shop energy, no digital clean, no text"
        ),
    },
]

# ── Image fetch ───────────────────────────────────────────────────────────────

def fetch(prompt, filename, retries=2):
    encoded = urllib.parse.quote(prompt, safe="")
    params = f"?width={W}&height={H}&model=flux&seed=-1&nologo=true"
    if POLLINATIONS_KEY:
        params += f"&key={urllib.parse.quote(POLLINATIONS_KEY, safe='')}"
    url = f"https://gen.pollinations.ai/image/{encoded}{params}"
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "disability-ai-collective/style-lab"})
            with urllib.request.urlopen(req, timeout=90) as r:
                data = r.read()
            if len(data) < 1000:
                raise ValueError(f"Too small: {len(data)} bytes")
            path = ASSETS / filename
            path.write_bytes(data)
            print(f"  OK  {filename}  ({len(data)//1024}KB)")
            return True
        except Exception as e:
            print(f"  ERR attempt {attempt+1}: {e}")
            if attempt < retries:
                time.sleep(5)
    return False

# ── HTML page ─────────────────────────────────────────────────────────────────

def write_html(styles):
    cards = ""
    for s in styles:
        img_src = f"/assets/stylelab_{s["id"]}.jpg"
        cards += f"""
    <div class="stylelab-card">
      <div class="stylelab-img-wrap">
        <img src="{img_src}" alt="{s[name]}" loading="lazy">
      </div>
      <div class="stylelab-meta">
        <h2>{s[name]}</h2>
        <p class="stylelab-desc">{s[desc]}</p>
        <details>
          <summary>Full prompt</summary>
          <pre class="stylelab-prompt">{s[prompt]}</pre>
        </details>
      </div>
    </div>"""

    html = f"""---
layout: default
title: "Style Lab — 10 Image Aesthetics"
description: "Experimental image style overview: linocut, silkscreen, glitch, scratch film, pixel, split, collage, mimeograph, cyanotype, letterpress."
---
<style>
.stylelab-grid {{ display:grid; grid-template-columns:1fr; gap:3rem; max-width:860px; margin:0 auto; padding:2rem 1rem; }}
.stylelab-card {{ display:flex; flex-direction:column; gap:1rem; border:1px solid #333; padding:1.5rem; background:#111; }}
.stylelab-img-wrap img {{ width:100%; height:auto; display:block; }}
.stylelab-meta h2 {{ font-size:1.25rem; font-weight:700; margin:0 0 .4rem; color:#f0f0f0; }}
.stylelab-desc {{ color:#aaa; font-size:.9rem; margin:0 0 .75rem; }}
.stylelab-prompt {{ background:#1a1a1a; color:#ccc; font-size:.75rem; padding:1rem; white-space:pre-wrap; word-break:break-word; border:1px solid #2a2a2a; margin-top:.5rem; }}
details summary {{ cursor:pointer; color:#666; font-size:.8rem; }}
details[open] summary {{ color:#999; }}
</style>

<main id="main-content">
  <header class="section section--secondary text-center">
    <div class="container">
      <h1 class="text-h1 mb-4">Style Lab</h1>
      <p class="text-lead text-secondary max-w-2xl mx-auto">
        10 image aesthetic experiments — same subject, different sauce.
        Linocut · Silkscreen · Glitch · Scratch Film · 8-bit Pixel ·
        Split Montage · Dada Collage · Mimeograph · Cyanotype · Letterpress
      </p>
    </div>
  </header>
  <section class="section section--primary">
    <div class="stylelab-grid">
{cards}
    </div>
  </section>
</main>
"""
    out = BASE / "style-lab.html"
    out.write_text(html)
    print(f"Wrote {out}")

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Generating {len(STYLES)} style-lab images...")
    for s in STYLES:
        filename = f"stylelab_{s["id"]}.jpg"
        print(f"\n[{s["id"]}]")
        fetch(s["prompt"], filename)
    write_html(STYLES)
    print("\nDone.")
