#!/usr/bin/env python3
"""
GALLERY-QUALITY AI IMAGE GENERATOR

Architecture:
  1. Extract visual subjects from article frontmatter (pure Python, no LLM)
  2. Build art-direction prompts using curated dis.art-inspired templates
  3. Pollinations.ai FLUX generates images (seed=-1, non-deterministic)
  4. Gradient fallback if network unavailable

Aesthetic: dis.art — confronting, intimate, uncanny. Never literal. Never stock photo.
Three fixed modes per article: CONFRONTING (chiaroscuro) / INTIMATE (cinematic) / ABSTRACT (macro)
Requires: POLLINATIONS_API_KEY env var
"""

import json
import logging
import os
import re
import struct
import urllib.parse
import urllib.request
import zlib
from pathlib import Path

# Load secrets from env file (no export statements — must parse manually)
_ENV_FILE = Path("/srv/secrets/openclaw.env")
if _ENV_FILE.exists():
    for _line in _ENV_FILE.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())


logger = logging.getLogger(__name__)

# ── Accent color palette ───────────────────────────────────────────────────────
ACCENTS = ["crimson red", "cobalt blue", "acid yellow", "burnt orange",
           "emerald green", "deep violet", "teal", "chalk white", "rose gold"]

# ── Sauce catalog: context-matched style library ──────────────────────────────
# Image 1 = always raw linocut. Images 2+ = scored against article keywords.
SAUCE_CATALOG = {
    "punk-pamphlet": {
        "prompt": (
            "hand-drawn xerox zine, NYC punk 1977, {person}, "
            "crude thick black marker drawings and ink sketches on copier paper, "
            "severe photocopier distortion and roller drag artifacts, "
            "staple holes fold marks ink bleed smear, maximum grain maximum overexposure, "
            "pure drawing and print marks absolutely no photography, "
            "Xerox machine as artistic medium, crip punk rage, no readable text"
        ),
        "keywords": ["access", "barrier", "exclusion", "tax", "crip", "justice",
                     "navigation", "mobility", "ramp", "protest", "broken", "curb"],
    },
    "glitch-corrupt": {
        "prompt": (
            "digital glitch art, {person}, "
            "RGB channel split displacement, VHS scan-line artifacts, "
            "pixel sorting vertical bands, broken codec freeze frame, "
            "data corruption aesthetic, {accent} channel dominant, "
            "net art meets crip cyborg theory, no clean edges, no text"
        ),
        "keywords": ["ai", "digital", "tech", "interface", "algorithm", "data",
                     "screen", "app", "software", "code", "caption", "subtitle", "automation"],
    },
    "dada-sculpture": {
        "prompt": (
            "photograph of Dada assemblage sculpture, {obj} as found-object monument, "
            "Kurt Schwitters Merzbau energy, wire mesh and torn newspaper and plaster mixed, "
            "mismatched material textures layered in physical space, rough studio floor, "
            "harsh single directional light casting deep shadows, "
            "crip body politics as three-dimensional object, no background, no text"
        ),
        "keywords": ["prosthetic", "device", "aid", "wheelchair", "cane", "hearing",
                     "braille", "tool", "object", "instrument", "body", "physical"],
    },
    "pixel-strict": {
        "prompt": (
            "strict 8-bit pixel art, {person}, "
            "ZX Spectrum 16-color limited palette with {accent} dominant, "
            "large chunky pixel grid, zero anti-aliasing, color clash artifacts, "
            "demoscene aesthetic, crip tech nostalgia, no gradients, no smooth edges, no text"
        ),
        "keywords": ["game", "interface", "computer", "digital", "screen",
                     "app", "software", "tech", "web", "keyboard"],
    },
    "popart-collage": {
        "prompt": (
            "paper cut-out collage only, bright colored magazine paper snippets assembled, "
            "absolutely no photography, pure cut paper shapes and fragments, "
            "raw scissor and torn edges visible, glue stain halos around pieces, "
            "flat saturated color paper fragments at wildly competing scales, "
            "Matisse cut-out scale and flatness meets disability activism poster, "
            "dense overlapping paper layers, white gaps where paper doesnt meet, no text"
        ),
        "keywords": ["film", "cinema", "oscar", "media", "culture", "art",
                     "visual", "performance", "theater", "show", "casting", "hollywood"],
    },
    "dada-collage": {
        "prompt": (
            "Dada photomontage collage, {person} fragmented and reassembled, "
            "torn magazine page textures layered, Hannah Hoch energy, "
            "mismatched scales and perspectives, paste residue at torn edges, "
            "{accent} newsprint fragments, crip body politics visual language, "
            "overlapping cut-and-paste fragments, no clean composition, no text"
        ),
        "keywords": ["identity", "culture", "deaf", "blind", "neurodivergent",
                     "history", "community", "collective", "crip", "sign", "language"],
    },
    "mimeograph": {
        "prompt": (
            "extreme mimeograph overprint, severely uneven ink roller coverage, "
            "abstract purple-blue ghost impressions stacked and misaligned, "
            "ink starvation white patches alternating with over-inked black blobs, "
            "multiple skewed impressions, crumpled duplicator paper texture, "
            "illegible smeared forms as abstract texture field, "
            "maximum print entropy, no clean edges, no text"
        ),
        "keywords": ["archive", "history", "movement", "document", "research",
                     "policy", "report", "study", "score", "beethoven", "mathematical"],
    },
    "cyanotype": {
        "prompt": (
            "cyanotype composite photogram, multiple overlapping sun-print exposures, "
            "botanical specimen silhouettes layered with mechanical part shadows, "
            "full prussian blue to white spectrum with mid-tone halos, "
            "chemical tide-mark rings and wash lines as compositional elements, "
            "no single readable subject, Anna Atkins meets Laszlo Moholy-Nagy photogram, "
            "accidental chemistry as aesthetic, no text"
        ),
        "keywords": ["design", "architecture", "blueprint", "space", "building",
                     "urban", "plan", "system", "map", "acoustic", "sound", "wave"],
    },
    "urbit-pixel": {
        "prompt": (
            "isometric pixel art, strict modular grid structure, "
            "repeating geometric tile unit with clear internal logic, "
            "Urbit sigil symmetry four-fold rotational structure, "
            "black and white two-tone, hard pixel edges, "
            "each tile a self-contained geometric module, "
            "visible grid axis, structured like circuit board or floor plan, "
            "no organic forms, no figures, no gradients, no text"
        ),
        "keywords": ["pattern", "math", "algorithm", "system", "structure",
                     "neurodivergent", "cognitive", "code", "logic", "wayfinding", "grid"],
    },
}

SAUCE_FALLBACK_ORDER = ["popart-collage", "glitch-corrupt", "pixel-strict", "dada-collage"]

def _build_linocut(obj, accent=None):
    """Image 1 — linocut, alternates B&W and two-color risograph."""
    import random
    if accent and random.random() < 0.5:
        return (
            f"two-color risograph print, {obj} as bold central motif, "
            f"misregistered {accent} and black ink layers on off-white paper, "
            f"halftone dot grain visible, ink overlap creates third color, "
            f"protest print tradition, uneven ink pressure, "
            f"visible paper texture, no gradients, no photorealism, no text"
        )
    return (
        f"raw woodblock linocut relief print, {obj} as bold central motif, "
        f"deep hand-carved gouge lines, stark black ink on cream paper, "
        f"visible tool marks and pressure ridges, uneven ink coverage, "
        f"irregular stamp edges, protest woodcut tradition, "
        f"no color, no gradients, no photorealism, no text"
    )

def _build_sauce(sauce_key, person, obj, accent):
    """Render a sauce prompt with extracted subjects."""
    tmpl = SAUCE_CATALOG[sauce_key]["prompt"]
    return tmpl.format(person=person, obj=obj, accent=accent)


class SceneImageGenerator:
    def __init__(self, width=800, height=450, pixel_size=5):
        self.width = width
        self.height = height
        self.pixel_size = max(1, min(10, pixel_size))
        self.gw = width // pixel_size
        self.gh = height // pixel_size
        self.pollinations_key = os.environ.get("POLLINATIONS_API_KEY", "")
        self.pollinations_base = "https://gen.pollinations.ai"

    # ── Subject extraction (pure Python) ─────────────────────────────────────

    def _extract_subjects(self, content, title):
        """Extract visual subjects from article frontmatter. No LLM needed."""
        import re as _re

        # Parse frontmatter
        fm_match = _re.search(r'^---\n(.*?)\n---', content, _re.DOTALL)
        excerpt = ""
        categories = []
        if fm_match:
            fm = fm_match.group(1)
            exc_m = _re.search(r'^excerpt:\s*["\']?(.*?)["\']?\s*$', fm, _re.MULTILINE)
            if exc_m:
                excerpt = exc_m.group(1).strip('"\'')
            cats_m = _re.search(r'^categories:\s*\[(.*?)\]', fm, _re.MULTILINE)
            if cats_m:
                categories = [c.strip(' "\'') for c in cats_m.group(1).split(',')]

        # Use title first — most reliable signal, then corpus for broader match
        title_lower = title.lower()
        corpus = (title + ' ' + ' '.join(categories) + ' ' + excerpt).lower()

        # Specific objects from excerpt (skip overly generic ones)
        obj_words = _re.findall(
            r'\b(hearing aid|cochlear implant|TTY|ASL interpreter|'
            r'rollator|prosthetic|brace|exoskeleton|'
            r'braille display|white cane|screen reader|magnifier|AAC device|'
            r'mechanical keyboard|blueprint|architectural model|circuit board|film reel)\b',
            excerpt.lower()
        )
        found_obj = obj_words[0] if obj_words else None

        # Topic detection — title signals take priority over corpus
        if any(w in title_lower for w in ['prosthetic', 'casting disabled', 'disabled actor', 'beats hollywood']):
            person = "figure in profile, outstretched arm mid-reach toward a single light source"
            place = "film set, theatrical lighting grid overhead, cables pooling on dark floor"
            obj = found_obj or "articulated prosthetic hand, finger joints extended, close detail"

        elif any(w in title_lower for w in ['beethoven', 'mathematical order']):
            person = "figure bent over ergonomic desk, silhouette lit by cold monitor glow"
            place = "sparse low-lit room, single monitor, wires taped to desk, late night"
            obj = found_obj or "single mechanical key lifted from keyboard, backlit from below"

        elif any(w in title_lower for w in ['navigation tax', 'wheelchair users pay', 'wheelchair user']):
            person = "hands gripping wheel rim from low angle, knuckles and veins in side light"
            place = "rain-slicked urban sidewalk at dusk, amber puddle reflections"
            obj = found_obj or "worn wheelchair tire cross-section, rubber tread and spoke"

        elif any(w in title_lower for w in ['oscar', 'oscars', 'sound of exclusion', 'exclusion']):
            person = "lone figure in empty cinema row, projection light on one side of face"
            place = "empty multiplex theater, rows of vacant seats, screen light beyond"
            obj = found_obj or "35mm film reel, half-unspooled, iridescent celluloid"

        elif any(w in title_lower for w in ['architect', 'building', 'wrong sense', 'acoustic']):
            person = "lone figure casting sharp shadow across polished concrete atrium floor"
            place = "cavernous open-plan office atrium, glass ceiling, empty, late hour"
            obj = found_obj or "architectural scale model fragment, exposed balsa wood and glue"

        elif any(w in title_lower for w in ['mapmaker', 'map', 'cartograph']):
            person = "hands tracing a careful line on large drafting paper, light pressure"
            place = "sparse studio table, scattered notebooks, diffuse north window light"
            obj = found_obj or "hand-drawn topographic map fragment, ink contours visible"

        elif any(w in title_lower for w in ['access story', 'transportation', 'transit', 'deaf culture']):
            person = "two hands mid-ASL sign, backlit silhouette, wrists and fingers close"
            place = "empty transit corridor, harsh fluorescent overhead strip light"
            obj = found_obj or "vintage TTY terminal on steel desk, handset resting"

        elif any(w in corpus for w in ['deaf', 'hearing loss', 'asl', 'sign language', 'tty', 'caption']):
            person = "two hands mid-ASL sign, backlit silhouette, wrists and fingers close"
            place = "empty transit corridor, harsh fluorescent overhead strip light"
            obj = found_obj or "vintage TTY terminal on steel desk, handset resting"

        elif any(w in corpus for w in ['autistic', 'neurodiv', 'adhd', 'sensory', 'cognitive', 'interface design']):
            person = "figure bent over ergonomic desk, silhouette lit by cold monitor glow"
            place = "sparse low-lit room, single monitor, wires taped to desk, late night"
            obj = found_obj or "single mechanical key lifted from keyboard, backlit from below"

        elif any(w in corpus for w in ['blind', 'low vision', 'braille', 'screen reader']):
            person = "fingertip pressed to embossed surface, slight pressure visible in skin"
            place = "sunlit wood desk, scattered tactile materials, warm afternoon light"
            obj = found_obj or "braille cell with six raised dots, close detail, warm light"

        elif any(w in corpus for w in ['film', 'cinema', 'culture', 'crip', 'art', 'media']):
            person = "performer under single harsh spotlight, empty audience chairs behind"
            place = "empty black-box theater, one spot lit on stage, rest in darkness"
            obj = found_obj or "vintage condenser microphone, stand and cable, close detail"

        elif any(w in corpus for w in ['wheelchair', 'mobility', 'ramp', 'curb']):
            person = "hands gripping wheel rim from low angle, knuckles and veins in side light"
            place = "rain-slicked urban sidewalk at dusk, amber puddle reflections"
            obj = found_obj or "worn wheelchair tire cross-section, rubber tread and spoke"

        else:
            person = "figure partially silhouetted in doorframe, bright light behind them"
            place = "sparse modernist interior, single chair, late afternoon light"
            obj = found_obj or "single worn wooden chair, center frame, raking side light"

        logger.info("Subjects — person: %r  place: %r  obj: %r", person, place, obj)
        return person, place, obj

    # ── Prompt generation ─────────────────────────────────────────────────────

    def _generate_prompts(self, content, title, num_images=3):
        """Image 1 = raw linocut always. Images 2+ = context-matched sauces."""
        accent = ACCENTS[abs(hash(title)) % len(ACCENTS)]
        person, place, obj = self._extract_subjects(content, title)
        prompts = [_build_linocut(obj, accent=accent)]
        sauces = self._pick_sauces(content, title, n=num_images - 1)
        for key in sauces:
            prompts.append(_build_sauce(key, person, obj, accent))
        return prompts

    def _pick_sauces(self, content, title, n=2):
        """Score each sauce against article corpus, return top-n distinct keys."""
        corpus = (title + " " + content).lower()
        scores = {}
        for key, sauce in SAUCE_CATALOG.items():
            scores[key] = sum(1 for kw in sauce["keywords"] if kw in corpus)
        ranked = sorted(scores, key=lambda k: scores[k], reverse=True)
        # Pick top-n, fall back to SAUCE_FALLBACK_ORDER if ties at 0
        picked = [k for k in ranked if scores[k] > 0][:n]
        if len(picked) < n:
            for k in SAUCE_FALLBACK_ORDER:
                if k not in picked:
                    picked.append(k)
                if len(picked) == n:
                    break
        logger.info("Sauce selection (n=%d): %s | scores: %s", n,
                    picked, {k: scores[k] for k in picked})
        return picked

    def _fetch_pollinations(self, prompt, timeout=60):
        """Fetch image from Pollinations FLUX. Returns JPEG bytes."""
        encoded = urllib.parse.quote(prompt, safe='')
        params = (
            f"?width={self.width}&height={self.height}"
            f"&model=flux&seed=-1&nologo=true"
        )
        if self.pollinations_key:
            params += f"&key={urllib.parse.quote(self.pollinations_key, safe='')}"
        url = f"{self.pollinations_base}/image/{encoded}{params}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "disability-ai-collective/1.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
        if len(data) < 1000:
            raise ValueError(f"Suspicious response: {len(data)} bytes")
        return data

    # ── Main generation ───────────────────────────────────────────────────────

    def generate_content_aware_images(self, content, title, slug, num_images=3, validate=False):
        """Generate num_images gallery-quality images via Pollinations FLUX."""
        images = []
        labels = ['setting', 'moment', 'symbol']

        try:
            logger.info("Generating prompts for: %s", title)
            prompts = self._generate_prompts(content, title, num_images=num_images)

            for i, prompt in enumerate(prompts):
                label = labels[i] if i < len(labels) else f"scene{i+1}"
                logger.info("Image %d/%d [%s]: %s...", i+1, num_images, label, prompt[:100])
                try:
                    img_data = self._fetch_pollinations(prompt)
                    filename = f"{slug}_{label}_{i+1}.jpg"
                    images.append({
                        'data': img_data,
                        'filename': filename,
                        'description': f"{label.title()} — {title}",
                        'score': 9,
                        'scene': label,
                        'prompt': prompt,
                    })
                    logger.info("  OK %s (%d bytes)", filename, len(img_data))
                except Exception as e:
                    logger.warning("  Pollinations failed (%s) — gradient fallback", e)
                    img_data = self._pixel_fallback(i)
                    images.append({
                        'data': img_data,
                        'filename': f"{slug}_{label}_{i+1}.png",
                        'description': f"{label.title()} — {title}",
                        'score': 2,
                        'scene': label,
                    })

        except Exception as e:
            logger.error("generate_content_aware_images failed: %s", e)
            for i in range(num_images):
                label = labels[i] if i < len(labels) else f"scene{i+1}"
                images.append({
                    'data': self._emergency_png(),
                    'filename': f"{slug}_{label}_{i+1}.png",
                    'description': f"{label.title()} — {title}",
                    'score': 1,
                    'scene': label,
                })

        return images

    # ── Gradient fallback ─────────────────────────────────────────────────────

    def _pixel_fallback(self, index=0):
        palettes = [
            [(15, 15, 30), (40, 40, 80), (80, 80, 140)],
            [(30, 15, 15), (80, 40, 40), (140, 80, 80)],
            [(15, 30, 15), (40, 80, 40), (80, 140, 80)],
        ]
        colors = palettes[index % len(palettes)]
        grid = [[(0, 0, 0)] * self.gw for _ in range(self.gh)]
        for y in range(self.gh):
            t = y / max(1, self.gh - 1)
            if t < 0.5:
                c = tuple(int(colors[0][k] + (colors[1][k] - colors[0][k]) * t * 2) for k in range(3))
            else:
                c = tuple(int(colors[1][k] + (colors[2][k] - colors[1][k]) * (t - 0.5) * 2) for k in range(3))
            for x in range(self.gw):
                grid[y][x] = c
        return self._grid_to_png(grid)

    def _emergency_png(self):
        grid = [[(10, 10, 20)] * self.gw for _ in range(self.gh)]
        return self._grid_to_png(grid)

    def _grid_to_png(self, grid):
        raw = b''
        for gy in range(self.gh):
            for _ in range(self.pixel_size):
                raw += b'\x00'
                for gx in range(self.gw):
                    cell = grid[gy][gx]
                    if not isinstance(cell, (tuple, list)) or len(cell) < 3:
                        cell = (0, 0, 0)
                    r = max(0, min(255, int(cell[0])))
                    g = max(0, min(255, int(cell[1])))
                    b = max(0, min(255, int(cell[2])))
                    raw += bytes([r, g, b]) * self.pixel_size
        compressed = zlib.compress(raw)
        w = self.gw * self.pixel_size
        h = self.gh * self.pixel_size
        png = b'\x89PNG\r\n\x1a\n'
        ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
        png += struct.pack('>I', len(ihdr)) + b'IHDR' + ihdr
        png += struct.pack('>I', zlib.crc32(b'IHDR' + ihdr) & 0xFFFFFFFF)
        png += struct.pack('>I', len(compressed)) + b'IDAT' + compressed
        png += struct.pack('>I', zlib.crc32(b'IDAT' + compressed) & 0xFFFFFFFF)
        png += struct.pack('>I', 0) + b'IEND'
        png += struct.pack('>I', zlib.crc32(b'IEND') & 0xFFFFFFFF)
        return png


# ─────────────────────────────────────────────────────────────────────────────

def generate_article_images(content, title, slug, num_images=3):
    gen = SceneImageGenerator()
    imgs = gen.generate_content_aware_images(content, title, slug, num_images)
    return [{'data': i['data'], 'filename': i['filename'], 'alt_text': i['description']} for i in imgs]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    from pathlib import Path as P
    content = P('_posts/2026-03-08-architects-are-designing-buildings-for-the-wrong-sense.md').read_text()
    title = "Architects Are Designing Buildings for the Wrong Sense"
    gen = SceneImageGenerator()
    imgs = gen.generate_content_aware_images(content, title, "test-architects", 3)
    for img in imgs:
        p = P(f"/tmp/{img['filename']}")
        p.write_bytes(img['data'])
        print(f"  {img['filename']}  {len(img['data'])} bytes")
        print(f"  prompt: {img.get('prompt','n/a')[:140]}\n")
