#!/usr/bin/env python3
"""
figures.py -- publisher-written captions and alt text, harvested from HTML already fetched.

WHY THIS EXISTS
Extraction is text-only by explicit configuration, and has been since it was written:
`strip_html` drops every tag, and the legacy path calls trafilatura with
`include_images=False`. That is the right default for body prose and the wrong one for
the sentences a publisher writes UNDER a photograph, which are ordinary editorial text
and frequently say things the article body does not.

Measured on the two subjects that prompted this (6 September 2026, pages re-fetched live):

    dezeen.com  WildSumaco   7 figcaptions, incl. "The upper level contains a bird
                             observatory" and "The lower level contains research and
                             analysis spaces"
    archdaily.com WildSumaco a Plan and a Section on the page; gallery alt text typed by
                             the publisher ("Exterior Photography, Wood, Forest")
    dezeen.com  Tollymore    10 figcaptions, incl. "It is formed of a cluster of grey
                             volumes"

The ArchDaily source in the live WildSumaco pack is 3,064 characters and contains none of
"upper level", "lower level" or "bird observatory". The page said all three -- in its
drawings and its gallery. Only the Dezeen anchor happened to repeat it in prose, so one
publisher's choice of where to put a sentence decided whether a fact existed.

WHAT THIS IS
A deterministic parser over HTML the fetcher is already holding. Nothing else.

WHAT THIS IS NOT, and none of these is a future extension of this module
  - No image is downloaded. No byte of any image is read, hashed or stored.
  - No vision model, no OCR, no image classifier, no inference from an image.
  - No network of any kind. This module cannot open a socket; it is given a string.
  - No model call. Every rule here is a regex and a table.
  - `include_images=True` is NOT switched on anywhere. Body extraction is untouched, so
    `text`, `content_length` and `sha256` are byte-identical to what they were.

VERBATIM, AND HOW IT IS GUARANTEED
Every caption and alt string here is a substring of the fetched HTML, entity-decoded and
whitespace-collapsed -- exactly the normalisation `strip_html` already applies to body
text, and exactly what `verified_excerpts` compares against. Verbatimness holds BY
CONSTRUCTION: no model is in this path, and the only operations are substring extraction
and that normalisation. There is deliberately no post-hoc verbatim check, for the same
reason `documents.py` has none: a deterministic extractor's output cannot disagree with
its input.

THAT GUARANTEE IS LOAD-BEARING AND IT ENDS THE MOMENT A MODEL TOUCHES THIS DATA. If a
later stage ever has a model propose, rewrite or summarise a caption, that stage owes a
verbatim check against `text`/HTML before the result may be carried. Do not remove this
paragraph when that day comes; act on it.

A URL IS A REFERENCE, NEVER EVIDENCE
`image_url` is recorded so a later phase can find the file. Nothing in this module reads
meaning out of it: no type is inferred from a filename, no caption is ever synthesised
from a path, and a CDN slug is not a fact about the world. `_looks_like_machine_metadata`
exists to keep generated strings (gallery numbering, loader alt text, dimensions, file
names) out of the caption fields entirely.

WHERE THE OUTPUT GOES TODAY
Onto the pack source, as `figures`, riding along only where a source has any -- the same
shape `document` provenance already uses, so an HTML page with no figures serialises
exactly as it did before this file existed.

IT IS NOT YET WIRED INTO THE LEDGER. The freeze prompt does not see `figures`, and no
fact can rest on a caption yet. That is deliberate: feeding captions to the freeze would
change what the composition engine reads, which is a decision to take on its own evidence
rather than as a side effect of a parser landing. This module retains; a later phase
decides what may stand on it.
"""
from __future__ import annotations

import html as _html
import re
import urllib.parse

# ── bounds ────────────────────────────────────────────────────────────────────
# A Dezeen article page carried 426 distinct image URLs and 82 <img> tags on the day
# this was measured, most of them related-article thumbnails and site furniture. The
# caps are set so a gallery cannot dominate a pack entry, and so parse cost stays flat
# on a page whose image count is unbounded.
MAX_FIGURES = 12                # figures carried per source
MAX_IMG_TAGS_SCANNED = 400      # <img> elements examined before we stop looking
MAX_FIGURE_BLOCKS_SCANNED = 200 # <figure> elements examined before we stop looking
MAX_HTML_SCANNED = 500_000      # characters of HTML parsed; matches the fetch-side cap
MAX_CAPTION_CHARS = 300
MAX_ALT_CHARS = 300
MAX_CREDIT_CHARS = 80
MAX_URL_CHARS = 500

# ── type hints ────────────────────────────────────────────────────────────────
# ONLY WHEN EXPLICIT. The publisher has to have said it, in words, in a caption or an alt
# attribute. Nothing is guessed from a filename, a URL, an image's position on the page
# or its dimensions.
PHOTO = "PHOTO"
PLAN = "PLAN"
SECTION = "SECTION"
DIAGRAM = "DIAGRAM"
MAP = "MAP"
OTHER = "OTHER"
TYPE_HINTS = (PHOTO, PLAN, SECTION, DIAGRAM, MAP, OTHER)

# Unambiguous multi-word labels: these mean what they say wherever they appear.
_STRONG_LABELS = (
    (r"\b(?:site|floor|ground[- ]floor|first[- ]floor|roof|upper[- ]level|"
     r"lower[- ]level)\s+plans?\b", PLAN),
    (r"\bplan\s+(?:drawing|view)\b", PLAN),
    (r"\b(?:cross|long|longitudinal|building)[- ]sections?\b", SECTION),
    (r"\bsections?\s+(?:drawing|through)\b", SECTION),
    (r"\b(?:axonometric|isometric|exploded\s+view)\b", DIAGRAM),
    (r"\b(?:elevation\s+drawing|elevations?\b(?=[^a-z]*(?:drawing|north|south|east|west)))",
     SECTION),
    (r"\bdiagrams?\b", DIAGRAM),
    (r"\b(?:location|site|context)\s+maps?\b", MAP),
    (r"\bphotograph(?:y|s)?\b", PHOTO),
)

# Ambiguous single words. "section" appears in navigation and prose constantly; "plan"
# is a noun about intentions as often as about drawings; "map" is a verb. These count
# ONLY in a string short enough to be a label rather than a sentence.
_WEAK_LABEL_MAX_CHARS = 60
_WEAK_LABELS = (
    (r"\bplans?\b", PLAN),
    (r"\bsections?\b", SECTION),
    (r"\bmaps?\b", MAP),
    (r"\bphotos?\b", PHOTO),
)

# ── machine metadata, which must never become evidence ────────────────────────
# Every pattern here was taken from a real page. `Image 3 of 31` is ArchDaily's gallery
# numbering; `Content Loader` is its spinner's alt text.
_METADATA_PATTERNS = (
    r"^\s*$",
    # ANCHORLESS on purpose. ArchDaily serves this numbering as a SUFFIX on an otherwise
    # real-looking string -- "WildSumaco Research Pavilion / Caa Pora Arquitectura -
    # Image 2 of 31" -- so an anchored rule matched none of the 31 and let the whole
    # gallery in. Nothing a person writes about a picture counts it out of a set.
    r"\bimage\s+\d+\s+of\s+\d+\b",
    r"^\d+\s+of\s+\d+\s*$",
    r"^(?:content\s+)?loader$",
    r"^loading(?:\.\.\.)?$",
    r"^(?:advertisement|advert|ad)$",
    r"^(?:logo|icon|spacer|placeholder|thumbnail|thumb|avatar|banner)$",
    r"^\d+\s*[x×]\s*\d+$",                       # 1600x900
    r"^[\d\s.,:%+\-×x]+$",                       # digits and punctuation only
    r"\.(?:jpe?g|png|gif|webp|svg|avif|bmp|tiff?)\s*$",  # a file name
    r"^(?:https?:)?//",                               # a URL
    r"^data:",
    r"^[a-z0-9_\-]{16,}$",                            # a slug or hash with no words
)
_METADATA_RE = tuple(re.compile(p, re.I) for p in _METADATA_PATTERNS)

# A string with no whitespace at all and a long alphanumeric run is a path segment or an
# identifier, whatever else it looks like.
_OPAQUE_TOKEN_RE = re.compile(r"^\S{24,}$")

MIN_TEXT_CHARS = 3

# ── credit ────────────────────────────────────────────────────────────────────
# Both forms below were recoverable from live pages during the audit: `© JAG Studio`
# from an ArchDaily figcaption and `©Johan Dehlin` from an alt attribute.
_CREDIT_RES = (
    re.compile(r"(?:©|&copy;|\(c\))\s*([^,;|<>()\[\]]{2,%d})" % MAX_CREDIT_CHARS, re.I),
    re.compile(r"\b(?:photos?|photography|images?|drawings?|credits?)\s*(?:by|:)\s*"
               r"([^,;|<>()\[\]]{2,%d})" % MAX_CREDIT_CHARS, re.I),
)

# ── element patterns ──────────────────────────────────────────────────────────
_FIGURE_RE = re.compile(r"(?is)<figure\b[^>]*>(.*?)</figure>")
_FIGCAPTION_RE = re.compile(r"(?is)<figcaption\b[^>]*>(.*?)</figcaption>")
_IMG_RE = re.compile(r"(?is)<img\b[^>]*>")
_ATTR_RE = re.compile(r"""(?is)\b([a-z0-9_:-]+)\s*=\s*("([^"]*)"|'([^']*)'|([^\s"'>]+))""")
_TAG_RE = re.compile(r"(?s)<[^>]+>")

# Lazy-loading means the real URL is usually not in `src`. Order is preference order.
_SRC_ATTRS = ("src", "data-src", "data-original", "data-lazy-src", "data-lazy",
              "data-echo", "data-url")
_SRCSET_ATTRS = ("srcset", "data-srcset")


def _text_of(fragment: str) -> str:
    """HTML fragment -> normalised text. Same normalisation `strip_html` applies to body
    prose: tags removed, entities decoded, whitespace collapsed. No other change."""
    return re.sub(r"\s+", " ", _html.unescape(_TAG_RE.sub(" ", fragment or ""))).strip()


def _looks_like_machine_metadata(s: str) -> bool:
    """True for a string that a machine produced about the file rather than a person
    wrote about the picture. Kept deliberately eager: losing a real caption costs one
    sentence, and admitting a filename costs the pack its meaning."""
    t = (s or "").strip()
    if len(t) < MIN_TEXT_CHARS:
        return True
    if any(r.search(t) for r in _METADATA_RE):
        return True
    if _OPAQUE_TOKEN_RE.match(t) and not re.search(r"[aeiou]{1,}\s", t):
        return True
    return False


def _clean_text(raw: str, limit: int) -> str:
    """Normalise, reject machine metadata, bound the length. Returns "" for anything
    that must not be carried."""
    t = _text_of(raw)
    if _looks_like_machine_metadata(t):
        return ""
    return t[:limit]


def _attrs(tag: str) -> dict:
    out = {}
    for m in _ATTR_RE.finditer(tag):
        name = m.group(1).lower()
        if name not in out:
            out[name] = (m.group(3) if m.group(3) is not None
                         else m.group(4) if m.group(4) is not None
                         else m.group(5) or "")
    return out


def _image_ref(tag_attrs: dict, base_url: str) -> str:
    """A reference, resolved against the page, or "". Never parsed for meaning."""
    cand = ""
    for a in _SRC_ATTRS:
        v = (tag_attrs.get(a) or "").strip()
        if v and not v.startswith("data:"):
            cand = v
            break
    if not cand:
        for a in _SRCSET_ATTRS:
            v = (tag_attrs.get(a) or "").strip()
            if v:
                # "url 320w, url 640w" -- the first entry, without its descriptor.
                first = v.split(",")[0].strip().split()
                if first and not first[0].startswith("data:"):
                    cand = first[0]
                break
    if not cand:
        return ""
    cand = _html.unescape(cand)
    if base_url:
        try:
            cand = urllib.parse.urljoin(base_url, cand)
        except Exception:
            pass
    return cand[:MAX_URL_CHARS]


def _type_hint(*texts: str) -> str:
    """PHOTO/PLAN/SECTION/DIAGRAM/MAP when the publisher said so in words, else OTHER.
    Reads ONLY the caption and alt text -- never a URL, a filename or a class name."""
    joined = " ".join(t for t in texts if t)
    if not joined:
        return OTHER
    for pattern, kind in _STRONG_LABELS:
        if re.search(pattern, joined, re.I):
            return kind
    for t in texts:
        if t and len(t) <= _WEAK_LABEL_MAX_CHARS:
            for pattern, kind in _WEAK_LABELS:
                if re.search(pattern, t, re.I):
                    return kind
    return OTHER


def _credit(*texts: str) -> str:
    for t in texts:
        if not t:
            continue
        for r in _CREDIT_RES:
            m = r.search(t)
            if m:
                c = m.group(1).strip(" .,:;-–—")
                if c and not _looks_like_machine_metadata(c):
                    return c[:MAX_CREDIT_CHARS]
    return ""


def _make(image_url: str, caption: str, caption_source: str, alt: str) -> dict | None:
    """One figure record, or None when there is nothing a person wrote."""
    if not caption and not alt:
        return None                       # a picture with no words is not text evidence
    return {
        "image_url": image_url,
        "caption": caption,
        "caption_source": caption_source,  # "figcaption" | "alt" | ""
        "alt": alt,
        "credit": _credit(caption, alt),
        "type_hint": _type_hint(caption, alt),
    }


def harvest(html_text: str, base_url: str = "") -> list:
    """Figures from one page's HTML. Deterministic, bounded, no network.

    Ordering is editorial, not incidental: a <figcaption> is a sentence a publisher
    WROTE, and an alt attribute is often generated, so captioned figures are kept first
    and alt-only ones fill the remaining room. Within each tier, document order.

    Returns [] for empty input, non-HTML input, or a page whose images carry no text.
    Never raises on malformed markup -- an unclosed <figure> simply does not match, and
    its <img> is then picked up by the standalone pass.
    """
    if not html_text or not isinstance(html_text, str):
        return []
    doc = html_text[:MAX_HTML_SCANNED]

    captioned, alt_only = [], []
    claimed = set()                       # img tags consumed by a <figure>

    for i, fm in enumerate(_FIGURE_RE.finditer(doc)):
        if i >= MAX_FIGURE_BLOCKS_SCANNED:
            break
        block = fm.group(1)
        cap_m = _FIGCAPTION_RE.search(block)
        caption = _clean_text(cap_m.group(1), MAX_CAPTION_CHARS) if cap_m else ""
        img_m = _IMG_RE.search(block)
        a = _attrs(img_m.group(0)) if img_m else {}
        if img_m:
            # Offset into the WHOLE document, so the standalone pass below can tell this
            # <img> has already been accounted for. It must be measured from group(1) --
            # the figure's inner content -- not from the match start, which sits on the
            # opening <figure ...> tag. Getting that wrong silently re-harvested every
            # captioned image a second time as an alt-only record.
            claimed.add(fm.start(1) + img_m.start())
        alt = _clean_text(a.get("alt", ""), MAX_ALT_CHARS)
        rec = _make(_image_ref(a, base_url), caption, "figcaption" if caption else
                    ("alt" if alt else ""), alt)
        if rec is None:
            continue
        (captioned if caption else alt_only).append(rec)

    for i, im in enumerate(_IMG_RE.finditer(doc)):
        if i >= MAX_IMG_TAGS_SCANNED:
            break
        if im.start() in claimed:
            continue
        a = _attrs(im.group(0))
        alt = _clean_text(a.get("alt", ""), MAX_ALT_CHARS)
        if not alt:
            continue
        rec = _make(_image_ref(a, base_url), "", "alt", alt)
        if rec is not None:
            alt_only.append(rec)

    out, seen = [], set()
    for rec in captioned + alt_only:
        # Identity is the words plus the reference: the same photograph reprinted under
        # two captions is two pieces of text evidence, and one caption repeated under a
        # hero and its thumbnail is one.
        key = (rec["image_url"], rec["caption"], rec["alt"])
        if key in seen:
            continue
        seen.add(key)
        out.append(rec)
        if len(out) >= MAX_FIGURES:
            break
    return out
