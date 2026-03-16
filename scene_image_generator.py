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

import logging
import os
import hashlib
import re
import struct
import urllib.parse
import json
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
        "keywords": ["protest", "broken", "curb cut", "inaccessible", "rage", "fight", "riot", "activist"],
    },
    "glitch-corrupt": {
        "prompt": (
            "digital glitch art, {person}, "
            "RGB channel split displacement, VHS scan-line artifacts, "
            "pixel sorting vertical bands, broken codec freeze frame, "
            "data corruption aesthetic, {accent} channel dominant, "
            "net art meets crip cyborg theory, scene: {place}, no clean edges, no text"
        ),
        "keywords": ["ai", "digital", "tech", "interface", "algorithm", "data",
                     "screen", "app", "software", "code", "caption", "captions", "subtitle", "subtitles", "automation"],
    },
    "dada-sculpture": {
        "prompt": (
            "photograph of Dada assemblage sculpture, {obj} as found-object monument, "
            "Kurt Schwitters Merzbau energy, wire mesh and torn newspaper and plaster mixed, "
            "mismatched material textures layered in physical space, {place}, "
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
            "dense overlapping paper layers, white gaps where paper doesnt meet, imagery evoking {place}, no text"
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
    "soviet-poster": {
        "prompt": (
            "Soviet constructivist propaganda poster style, flat graphic silhouette of {person}, "
            "bold flat red and black only, strong diagonal composition, "
            "geometric sans-serif forms, Rodchenko energy meets disability justice, "
            "high contrast flat color blocking, no gradients, no text"
        ),
        "keywords": ["collective", "movement", "justice", "rights", "access", "community", "solidarity"],
    },
    "letterpress-spot": {
        "prompt": (
            "letterpress printed broadside, {obj} as central typographic element, "
            "deep {accent} ink impression on cream cotton paper, "
            "visible letterform impression depth, ink squeeze at edges, "
            "wood type and metal type mixed sizes, craft print tradition, no text"
        ),
        "keywords": ["language", "text", "words", "voice", "communication", "AAC", "sign", "caption", "captions"],
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

NEAR_BW_STYLES = {"punk-pamphlet", "urbit-pixel", "mimeograph", "dada-sculpture"}

def _build_linocut(obj, accent=None, use_riso=False):
    """Image 1 — linocut, alternates B&W and two-color risograph."""
    if accent and use_riso:
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

def _build_sauce(sauce_key, person, obj, accent, place=""):
    """Render a sauce prompt with extracted subjects."""
    tmpl = SAUCE_CATALOG[sauce_key]["prompt"]
    return tmpl.format(person=person, obj=obj, accent=accent, place=place or "sparse interior")


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

    def _parse_frontmatter(self, content):
        """Parse Jekyll frontmatter. Returns (categories, excerpt)."""
        fm_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
        excerpt = ""
        categories = []
        if fm_match:
            fm = fm_match.group(1)
            exc_m = re.search(r'^excerpt:\s*["\']?(.*?)["\']?\s*$', fm, re.MULTILINE)
            if exc_m:
                excerpt = exc_m.group(1).strip('"\'')
            cats_m = re.search(r'^categories:\s*\[(.*?)\]', fm, re.MULTILINE)
            if cats_m:
                categories = [c.strip(' "\'') for c in cats_m.group(1).split(',')]
        return categories, excerpt

    def _any_kw(self, words, corpus):
        """Word-boundary check for single words, substring for phrases."""
        for w in words:
            if ' ' in w:
                if w in corpus:
                    return True
            elif re.search(r'\b' + re.escape(w) + r'\b', corpus):
                return True
        return False

    def _extract_subjects(self, content, title):
        """Extract visual subjects from article frontmatter. No LLM needed."""
        categories, excerpt = self._parse_frontmatter(content)

        # Use title first — most reliable signal, then corpus for broader match
        title_lower = title.lower()
        # Include first ~3 body paragraphs for richer keyword matching
        body_text = ""
        fm_end = content.find('\n---', content.find('---') + 3)
        if fm_end > 0:
            body_start = content[fm_end + 4:].strip()
            body_paras = [p.strip() for p in body_start.split('\n\n') if p.strip() and not p.strip().startswith('#')]
            body_text = ' '.join(body_paras[:3])
        corpus = (title + ' ' + ' '.join(categories) + ' ' + excerpt + ' ' + body_text).lower()

        # Specific objects from excerpt (skip overly generic ones)
        obj_words = re.findall(
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

        elif any(w in title_lower for w in ['oscar', 'oscars', 'sound of exclusion']):
            person = "figure in empty cinema row, projection light on one side of face"
            place = "empty multiplex theater, rows of vacant seats, screen light beyond"
            obj = found_obj or "35mm film reel, half-unspooled, iridescent celluloid"

        elif any(w in title_lower for w in ['architect', 'wrong sense', 'acoustic']):
            person = "figure casting sharp shadow across polished concrete atrium floor"
            place = "cavernous open-plan office atrium, glass ceiling, empty, late hour"
            obj = found_obj or "architectural scale model fragment, exposed balsa wood and glue"

        elif any(w in title_lower for w in ['mapmaker', 'cartograph'])\
                or bool(re.search(r'\bmap\b', title_lower)):
            person = "hands tracing a careful line on large drafting paper, light pressure"
            place = "sparse studio table, scattered notebooks, diffuse north window light"
            obj = found_obj or "hand-drawn topographic map fragment, ink contours visible"

        elif any(w in title_lower for w in ['access story', 'transportation', 'deaf culture'])\
                or bool(re.search(r'\btransit\b', title_lower)):
            person = "two hands mid-ASL sign, backlit silhouette, wrists and fingers close"
            place = "empty transit corridor, harsh fluorescent overhead strip light"
            obj = found_obj or "vintage TTY terminal on steel desk, handset resting"

        elif self._any_kw(['vibration', 'frequency', 'sonic', 'sound wave', 'acoustic design', 'resonance'], corpus):
            person = "figure casting sharp shadow across polished concrete atrium floor"
            place = "cavernous reverberant hall, hard parallel surfaces, no soft furnishing"
            obj = found_obj or "cross-section of acoustic panel, layered foam and perforated metal"

        elif self._any_kw(['deaf', 'hearing loss', 'asl', 'sign language', 'tty', 'caption', 'captions'], corpus):
            person = "two hands mid-ASL sign, backlit silhouette, wrists and fingers close"
            place = "empty transit corridor, harsh fluorescent overhead strip light"
            obj = found_obj or "vintage TTY terminal on steel desk, handset resting"

        elif self._any_kw(['autistic', 'neurodivergent', 'adhd', 'sensory', 'cognitive', 'interface design'], corpus):
            person = "figure bent over ergonomic desk, silhouette lit by cold monitor glow"
            place = "sparse low-lit room, single monitor, wires taped to desk, late night"
            obj = found_obj or "single mechanical key lifted from keyboard, backlit from below"

        elif self._any_kw(['blind', 'low vision', 'braille', 'screen reader'], corpus):
            person = "fingertip pressed to embossed surface, slight pressure visible in skin"
            place = "sunlit wood desk, scattered tactile materials, warm afternoon light"
            obj = found_obj or "braille cell with six raised dots, close detail, warm light"

        elif self._any_kw(['film', 'cinema', 'theater', 'performance', 'oscar'], corpus):
            person = "performer under single harsh spotlight, empty audience chairs behind"
            place = "empty black-box theater, one spot lit on stage, rest in darkness"
            obj = found_obj or "vintage condenser microphone, stand and cable, close detail"

        elif self._any_kw(['wheelchair', 'mobility', 'ramp', 'curb'], corpus):
            person = "hands gripping wheel rim from low angle, knuckles and veins in side light"
            place = "rain-slicked urban sidewalk at dusk, amber puddle reflections"
            obj = found_obj or "worn wheelchair tire cross-section, rubber tread and spoke"

        else:
            person = "figure partially silhouetted in doorframe, bright light behind them"
            place = "empty corridor, harsh overhead fluorescent strip light"
            obj = found_obj or "folded printed document, corner turned up, raking side light"

        logger.info("Subjects — person: %r  place: %r  obj: %r", person, place, obj)
        return person, place, obj

    # ── Prompt generation ─────────────────────────────────────────────────────

    def _generate_prompts(self, content, title, num_images=3, slug=""):
        """Image 1 = raw linocut always. Images 2+ = context-matched sauces."""
        accent = ACCENTS[int(hashlib.md5((title + slug).encode()).hexdigest(), 16) % len(ACCENTS)]
        person, place, obj = self._extract_subjects(content, title)
        use_riso = int(hashlib.md5((title + slug + 'riso').encode()).hexdigest(), 16) % 2 == 0
        prompts = [_build_linocut(obj, accent=accent, use_riso=use_riso)]
        sauces = self._pick_sauces(content, title, n=num_images - 1)
        for key in sauces:
            prompts.append(_build_sauce(key, person, obj, accent, place=place))
        return prompts

    def _focus_corpus(self, content, title):
        """Return focused corpus: title + categories + excerpt + first body paragraphs."""
        categories, excerpt = self._parse_frontmatter(content)
        body_text = ""
        fm_end = content.find('\n---', content.find('---') + 3)
        if fm_end > 0:
            body_start = content[fm_end + 4:].strip()
            body_paras = [p.strip() for p in body_start.split('\n\n') if p.strip() and not p.strip().startswith('#')]
            body_text = ' '.join(body_paras[:3])
        return (title + ' ' + ' '.join(categories) + ' ' + excerpt + ' ' + body_text).lower()

    def _pick_sauces(self, content, title, n=2):
        """Score each sauce against focused article corpus, return top-n distinct keys."""
        corpus = self._focus_corpus(content, title)
        scores = {}
        for key, sauce in SAUCE_CATALOG.items():
            scores[key] = sum(
                1 for kw in sauce["keywords"]
                if (kw in corpus if ' ' in kw
                    else bool(re.search(r'\b' + re.escape(kw) + r'\b', corpus)))
            )
        ranked = sorted(scores, key=lambda k: scores[k], reverse=True)
        # Pick top-n, fall back to SAUCE_FALLBACK_ORDER if ties at 0
        picked = [k for k in ranked if scores[k] > 0][:n]
        if len(picked) < n:
            for k in SAUCE_FALLBACK_ORDER:
                if k not in picked:
                    picked.append(k)
                if len(picked) == n:
                    break
        # Color diversity guard: if both picks are near-B&W, swap last for best color style
        if len(picked) >= 2 and all(p in NEAR_BW_STYLES for p in picked):
            color_ranked = [k for k in ranked if k not in NEAR_BW_STYLES and k not in picked]
            if color_ranked:
                picked[-1] = color_ranked[0]
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


    def _generate_alt_text(self, prompt, title, image_type):
        """Generate accessible alt text from the image prompt.

        Uses local Ollama (qwen3:14b) for a one-line description.
        Falls back to extracting key visual terms from prompt string.
        """
        # Try Ollama first
        try:
            ollama_prompt = (
                f"Write one concise image description for screen readers (under 25 words). "
                f"The image is a {image_type} illustration for an article titled \"{title}\". "
                f"The art prompt was: {prompt[:300]}\n\n"
                f"Respond with ONLY the alt text, no quotes, no prefix. "
                f"Describe what a viewer would see, in plain language."
            )
            payload = json.dumps({
                "model": "qwen3.5:9b",
                "prompt": ollama_prompt,
                "stream": False,
                "options": {"num_predict": 60, "temperature": 0.3},
            }).encode()
            req = urllib.request.Request(
                "http://127.0.0.1:11434/api/generate",
                data=payload, method="POST",
            )
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
            text = result.get("response", "").strip()
            # Clean: remove thinking tags, quotes, prefixes
            text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
            text = text.strip('"\'')
            text = re.sub(r'^(alt text:|description:|image:)\s*', '', text, flags=re.IGNORECASE).strip()
            if len(text) > 15 and len(text) < 300:
                logger.info("  Ollama alt text: %s", text[:80])
                return text
        except Exception as e:
            logger.debug("  Ollama alt text failed (%s), using fallback", e)

        # Fallback: extract key visual terms from the prompt
        return self._extract_alt_from_prompt(prompt, title, image_type)

    def _extract_alt_from_prompt(self, prompt, title, image_type):
        """Extract a meaningful alt text from the prompt string itself."""
        # Remove boilerplate phrases
        cleaned = prompt
        for phrase in [
            'no readable text', 'no text', 'no gradients', 'no photorealism',
            'no clean edges', 'no smooth edges', 'no background',
            'no organic forms', 'no figures', 'no clean composition',
            'absolutely no photography', 'no color',
        ]:
            cleaned = cleaned.replace(phrase, '')

        # Identify the art style (first clause usually)
        style_match = re.match(r'^([^,]+)', cleaned)
        style = style_match.group(1).strip() if style_match else image_type

        # Find the main subject — look for obj/person descriptions
        subject = ""
        # Check for "X as bold central motif" or "X as found-object" patterns
        motif_match = re.search(r'([^,]+?)\s+as\s+(bold central motif|found-object|central typographic)', cleaned)
        if motif_match:
            subject = motif_match.group(1).strip()
        else:
            # Check for figure/person descriptions
            fig_match = re.search(r'(figure [^,]+|hands [^,]+|fingertip [^,]+)', cleaned)
            if fig_match:
                subject = fig_match.group(1).strip()

        if subject and style:
            return f"{style.rstrip(',')} depicting {subject}"
        elif style:
            return f"{style.rstrip(',')} illustration for {title}"
        else:
            return f"{image_type.title()} illustration for {title}"


    def _generate_prompts_llm(self, content, title, num_images=3, slug=""):
        """Use Ollama qwen3:14b to generate article-specific FLUX prompts.
        Falls back to template system if Ollama fails or returns malformed output.
        """
        accent = ACCENTS[int(hashlib.md5((title + slug).encode()).hexdigest(), 16) % len(ACCENTS)]

        categories, excerpt = self._parse_frontmatter(content)
        fm_end = content.find('\n---', content.find('---') + 3)
        body_text = ""
        if fm_end > 0:
            body_start = content[fm_end + 4:].strip()
            body_paras = [p.strip() for p in body_start.split('\n\n')
                          if p.strip() and not p.strip().startswith('#')]
            body_text = ' '.join(body_paras[:4])
        article_context = (
            f"Title: {title}\n"
            f"Categories: {', '.join(categories)}\n\n"
            f"{excerpt}\n\n"
            f"{body_text[:1000]}"
        )

        style_guide = (
            "SITE AESTHETIC: punk-pamphlet / dis.art. Confronting, intimate, uncanny. "
            "Never literal, never stock photo. "
            "\n\nPRINT TECHNIQUES that FLUX renders beautifully — choose what fits: "
            "woodblock linocut (hand-carved gouges, uneven ink, stark B&W or two-color), "
            "risograph (misregistered ink layers, halftone grain, ink overlap creates third color), "
            "xerox zine (photocopier distortion, roller drag, maximum grain, overexposure), "
            "Soviet constructivist poster (flat bold silhouettes, strong diagonals, red+black), "
            "Dada photomontage (torn fragments, mismatched scales, paste residue), "
            "cyanotype (prussian blue chemistry, tide-mark rings, botanical silhouettes), "
            "mimeograph (purple-blue ghost impressions, ink starvation, abstract overprint), "
            "paper cut-out collage (Matisse scale, flat saturated torn shapes, white gaps), "
            "glitch/VHS (RGB channel split, scan-line artifacts, pixel sorting), "
            "letterpress (deep ink impression, cream paper, wood+metal type mixed). "
            "\n\nFLUX RENDERS WELL: high contrast chiaroscuro, single dominant color + near-black, "
            "extreme close-up of texture or material, silhouettes with strong rim light, "
            "dramatic raking sidelight, industrial materials (concrete, perforated metal, foam, paper), "
            "hands and fingers in action, unexpected scale (tiny object filling full frame), "
            "layered flat shapes, surreal object combinations, shadow as subject."
        )

        editorial_voice = (
            "EDITORIAL IDENTITY: Crip Minds — disability as culture, expertise, political position. "
            "Not tragedy, not suffering, not inspiration. "
            "Bodies are agents. Aesthetics of resistance, wit, absurdity, beauty. "
            "\n\nEMOTIONAL REGISTERS available: "
            "wit (visual pun, unexpected juxtaposition that lands as funny-because-true), "
            "tension (tight composition, dramatic light, something about to happen), "
            "wonder (extreme close-up reveals hidden structure nobody usually sees), "
            "resistance (body in motion, material under pressure, system being pushed against), "
            "absurdity (surreal object scale or combination that captures the article's argument), "
            "tenderness (intimate detail, quiet material, raking light on something worn). "
            "\n\nNEVER: pity, medicalized imagery, wheelchair-as-helplessness, "
            "inspirational poster composition, generic diversity stock aesthetic."
        )

        llm_prompt = (
            f"You are an art director for a disability-led editorial site. "
            f"Generate 3 distinct FLUX image generation prompts for this article.\n\n"
            f"ARTICLE:\n{article_context}\n\n"
            f"{style_guide}\n\n"
            f"{editorial_voice}\n\n"
            f"ACCENT COLOR for this article: {accent}\n\n"
            f"Generate 3 visually distinct images for this article. Full artistic freedom — "
            f"each image can be anything: a close-up nobody expected, an oblique angle on the argument, "
            f"a visual joke, a quiet absurd detail, pure texture, a figure, an object, pure abstraction, "
            f"confrontational or funny or tricky or beautiful. "
            f"No prescribed roles. Let the article suggest what it wants visually.\n\n"
            f"Rules:\n"
            f"- The 3 prompts must be visually distinct from each other (different styles, scales, moods)\n"
            f"- Each must reference something SPECIFIC from this article — not generic disability imagery\n"
            f"- Use {accent} as dominant color in at least one prompt\n"
            f"- Each prompt is 2-4 comma-separated clauses\n"
            f"- End each with: no text, no gradients\n"
            f"- Output ONLY a JSON array of 3 strings: [\"prompt1\", \"prompt2\", \"prompt3\"]"
        )

        def _parse_prompts(text):
            """Extract JSON array of prompts from LLM response text."""
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
            arr_match = re.search(r"\[.*?\]", text, re.DOTALL)
            if not arr_match:
                return None
            try:
                prompts = json.loads(arr_match.group())
            except json.JSONDecodeError:
                return None
            if not isinstance(prompts, list):
                return None
            prompts = [p.strip() for p in prompts if isinstance(p, str) and len(p.strip()) > 20]
            if not prompts:
                return None
            while len(prompts) < num_images:
                prompts.append(prompts[-1])
            return prompts[:num_images]

        # Primary: Claude Haiku via CLIProxyAPI (Anthropic messages format)
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        api_base = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
        if api_key:
            try:
                payload = json.dumps({
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 800,
                    "temperature": 0.8,
                    "messages": [{"role": "user", "content": llm_prompt}],
                }).encode()
                req = urllib.request.Request(
                    api_base.rstrip("/") + "/v1/messages",
                    data=payload, method="POST",
                )
                req.add_header("Content-Type", "application/json")
                req.add_header("x-api-key", api_key)
                req.add_header("anthropic-version", "2023-06-01")
                with urllib.request.urlopen(req, timeout=60) as resp:
                    result = json.loads(resp.read())
                text = result.get("content", [{}])[0].get("text", "").strip()
                prompts = _parse_prompts(text)
                if prompts:
                    logger.info("Haiku-generated prompts for %r:", title)
                    for i, p in enumerate(prompts):
                        logger.info("  [%d] %s...", i + 1, p[:100])
                    return prompts
                logger.warning("Haiku returned unparseable output: %s", text[:200])
            except Exception as e:
                logger.warning("Haiku prompt generation failed (%s) — trying Ollama", e)

        # Fallback: qwen3.5:9b via Ollama
        try:
            payload = json.dumps({
                "model": "qwen3.5:9b",
                "prompt": llm_prompt,
                "stream": False,
                "options": {"num_predict": 3000, "temperature": 0.75},
            }).encode()
            req = urllib.request.Request(
                "http://127.0.0.1:11434/api/generate",
                data=payload, method="POST",
            )
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())
            text = result.get("response", "").strip()
            prompts = _parse_prompts(text)
            if prompts:
                logger.info("Ollama-generated prompts for %r:", title)
                return prompts
        except Exception as e:
            logger.warning("Ollama prompt generation also failed (%s) — using templates", e)

        return self._generate_prompts(content, title, num_images=num_images, slug=slug)

    def generate_content_aware_images(self, content, title, slug, num_images=3):
        """Generate num_images gallery-quality images via Pollinations FLUX."""
        images = []
        labels = ['setting', 'moment', 'symbol']

        try:
            logger.info("Generating prompts for: %s", title)
            prompts = self._generate_prompts_llm(content, title, num_images=num_images, slug=slug)

            for i, prompt in enumerate(prompts):
                label = labels[i] if i < len(labels) else f"scene{i+1}"
                logger.info("Image %d/%d [%s]: %s...", i+1, num_images, label, prompt[:100])
                try:
                    img_data = self._fetch_pollinations(prompt)
                    filename = f"{slug}_{label}_{i+1}.jpg"
                    alt_text = self._generate_alt_text(prompt, title, label)
                    images.append({
                        'data': img_data,
                        'filename': filename,
                        'description': f"{label.title()} — {title}",
                        'alt_text': alt_text,
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
            images = []
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
    return [{'data': i['data'], 'filename': i['filename'], 'alt_text': i.get('alt_text') or i['description']} for i in imgs]


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
