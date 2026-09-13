#!/usr/bin/env python3
"""Focused tests for the 2026-09-13 article/homepage presentation polish.

Four things are pinned here:
  1. the duplicate opening title is suppressed, and ONLY when it is genuinely a duplicate
  2. the homepage carries no closing authorship/about block
  3. the Go Deeper source footer keeps every source, link and title
  4. the perspective block renders only when the article has the metadata

No model call, no network, no publish. Ruby/Jekyll is not available on this host, so the
Liquid guard is asserted structurally and the MATCHING RULE it implements is executed
directly against the real posts and against negative fixtures.

Run: python3 automation/presentation_polish_test.py
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent

FAILS, PASSES = [], []


def check(label, cond, detail=""):
    (PASSES if cond else FAILS).append(label)
    print("  %-4s %s%s" % ("PASS" if cond else "FAIL", label,
                           "" if cond else "  -- %s" % detail))


def read(p):
    return pathlib.Path(p).read_text(encoding="utf-8")


POST_LAYOUT = read(ROOT / "_layouts" / "post.html")
INDEX = read(ROOT / "index.html")
CSS = read(ROOT / "assets" / "css" / "main-redesign.css")


# ── the rule the Liquid implements, executed here ────────────────────────────
def _norm(s):
    """Normalise for comparison exactly as the layout does."""
    for a, b in (("’", "'"), ("‘", "'"), ("“", '"'),
                 ("”", '"'), ("—", "-"), ("–", "-")):
        s = s.replace(a, b)
    return re.sub(r"<[^>]+>", "", s).strip().lower()


def suppresses(body_html, page_title):
    """True when the layout would drop the body's opening heading."""
    b = body_html.lstrip()
    if "</h1>" not in b:
        return False
    h1_open = b.split("</h1>")[0]
    if h1_open[:3] != "<h1":              # H1 must be the FIRST element
        return False
    return _norm(h1_open) == _norm(page_title)


# ── 1. duplicate title ───────────────────────────────────────────────────────
print("\n1. duplicate opening title")
check("1a layout guards on the first element being an h1",
      "| slice: 0, 3" in POST_LAYOUT and "_lead == '<h1'" in POST_LAYOUT)
check("1b layout compares heading text to page.title",
      "_h1_text == _page_title" in POST_LAYOUT)
check("1c layout normalises smart quotes before comparing",
      "’" in POST_LAYOUT and "—" in POST_LAYOUT)
check("1d removal is first-occurrence only, never global",
      "remove_first: _h1_open" in POST_LAYOUT and "remove_first: '</h1>'" in POST_LAYOUT)
check("1e no blanket 'hide every body h1' rule in CSS",
      not re.search(r"\.post-content\s+h1\s*\{[^}]*display:\s*none", CSS))

# real posts
print("\n1(real posts). the rule against every published article")
suppressed, kept = [], []
for p in sorted((ROOT / "_posts").glob("*.md")):
    t = read(p)
    try:
        fm, body = t[:t.index("\n---", 3)], t[t.index("\n---", 3) + 4:]
    except ValueError:
        continue
    m = re.search(r'^title:\s*"?(.*?)"?\s*$', fm, re.M)
    if not m:
        continue
    first = next((l for l in body.split("\n") if l.strip()), "")
    if not first.startswith("# "):
        continue
    # markdown "# X" becomes "<h1 id=...>X</h1>"
    html = '<h1 id="x">%s</h1>\n\n<p>rest</p>' % first[2:]
    (suppressed if suppresses(html, m.group(1)) else kept).append(p.name)
check("1f exactly the two engine-written posts are suppressed",
      len(suppressed) == 2, str(suppressed))
check("1g SFMOMA suppressed",
      any("sfmoma" in s for s in suppressed), str(suppressed))
check("1h ASL suppressed",
      any("interpreter" in s for s in suppressed), str(suppressed))
check("1i no post has a leading H1 that is NOT a duplicate", kept == [], str(kept))

# negative cases -- the rule must NOT fire
print("\n1(negative). the rule must leave real headings alone")
cases = [
    ("different leading h1 kept",
     '<h1 id="a">A Different Heading</h1>\n<p>x</p>', "Real Title", False),
    ("matching leading h1 dropped",
     '<h1 id="a">Real Title</h1>\n<p>x</p>', "Real Title", True),
    ("smart-quoted heading still matches",
     '<h1 id="a">The President’s Image</h1>', "The President's Image", True),
    ("later h1 untouched (body opens with a paragraph)",
     '<p>opening</p>\n<h1 id="a">Real Title</h1>', "Real Title", False),
    ("h2 first is not an h1",
     '<h2 id="a">Real Title</h2>\n<h1>Real Title</h1>', "Real Title", False),
    ("no headings at all",
     '<p>just prose</p>', "Real Title", False),
]
for label, html, title, want in cases:
    check("1n %s" % label, suppresses(html, title) is want)

# ── 2. homepage ──────────────────────────────────────────────────────────────
print("\n2. homepage closing block")
check("2a no 'Written and edited by'", "Written and edited" not in INDEX)
check("2b no homepage about mini-nav", "home-intro__nav" not in INDEX)
check("2c no what-this-is section", 'id="what-this-is"' not in INDEX)
check("2d scroll tracker no longer names a removed section",
      "'what-this-is'" not in INDEX)
check("2e no start-here cluster", "start-here" not in INDEX)
check("2f no collective block",
      "voice-strip" not in INDEX and "home-collective" not in INDEX)
check("2g no legacy persona names",
      not re.search(r"Pixel Nova|Siri Sage|Maya Flux|Zen Circuit", INDEX))
check("2h no perspective block on the homepage", "perspective" not in INDEX.lower())
check("2i latest + recent essays still present",
      "home-hero__card" in INDEX and "Recent essays" in INDEX)
# destinations survive in the footer, not on the homepage body
DEFAULT = read(ROOT / "_layouts" / "default.html")
check("2j About + creator links still in the footer",
      "/about/" in DEFAULT and "/jascha/" in DEFAULT)

# ── 3. author card ───────────────────────────────────────────────────────────
print("\n3. article author element")
check("3a large author card gone", "post-author-card" not in POST_LAYOUT)
check("3b no EDITOR badge", "post-author-role" not in POST_LAYOUT)
check("3c no biography paragraph", "post-author-bio" not in POST_LAYOUT)
check("3d no avatar", "post-author-avatar" not in POST_LAYOUT)
check("3e one quiet author link", "post-author-line" in POST_LAYOUT)
check("3f author link uses public_author",
      re.search(r'post-author-line.*?site\.public_author', POST_LAYOUT, re.S) is not None)
check("3g top meta bar still carries the byline",
      "post-meta__item--agent" in POST_LAYOUT and "site.public_author" in POST_LAYOUT)
check("3h author-line styled", ".post-author-line" in CSS)

# ── 4. source footer ─────────────────────────────────────────────────────────
print("\n4. Go Deeper source footer")
check("4a block still rendered", "post-sources" in POST_LAYOUT)
check("4b href preserved verbatim", 'href="{{ src.url }}"' in POST_LAYOUT)
check("4c title preserved verbatim", "{{ src.title }}" in POST_LAYOUT)
check("4d publisher line preserved", "post-sources__publisher" in POST_LAYOUT)
check("4e still up to five sources", "limit: 5" in POST_LAYOUT)
check("4f no accordion / details element",
      "<details" not in POST_LAYOUT and "accordion" not in POST_LAYOUT)
check("4g no JS in the source block",
      "post-sources" in POST_LAYOUT and "onclick" not in POST_LAYOUT)
check("4h nothing hidden", not re.search(r"\.post-sources[^{]*\{[^}]*display:\s*none", CSS))
link_css = re.search(r"\.post-sources__link\s*\{([^}]*)\}", CSS)
check("4i title is a block-level touch target",
      link_css and "display: block" in link_css.group(1))
check("4j title smaller than body text",
      link_css and "font-size: 0.875rem" in link_css.group(1))
check("4k underline kept (affordance not colour-only)",
      link_css and "text-decoration: underline" in link_css.group(1))
pub_css = re.search(r"\.post-sources__publisher\s*\{([^}]*)\}", CSS)
check("4l domain is its own muted line",
      pub_css and "display: block" in pub_css.group(1))
check("4m domain wraps instead of overflowing",
      pub_css and "white-space: nowrap" not in pub_css.group(1))
check("4n domain not tiny", pub_css and "0.6875rem" in pub_css.group(1))

# both reference articles keep all four sources
print("\n4(real posts). source membership")
for label, name in (("ASL", "2026-09-12-the-interpreter-and-the-presidents-image.md"),
                    ("SFMOMA", "2026-09-13-the-drawing-sfmoma-bought-about-losing-ssi.md")):
    t = read(ROOT / "_posts" / name)
    fm = t[:t.index("\n---", 3)]
    n = len(re.findall(r"^\s+- title:", fm, re.M))
    check("4o %s still lists 4 sources" % label, n == 4, "got %d" % n)
    check("4p %s source urls intact" % label,
          len(re.findall(r"^\s+url:", fm, re.M)) == 4)

# ── 5. perspective ───────────────────────────────────────────────────────────
print("\n5. perspective block")
check("5a rendered only under a conditional", "{% if page.perspective %}" in POST_LAYOUT)
check("5b links to the perspectives page", "/perspectives/" in POST_LAYOUT)
check("5c not a byline", not re.search(r"(Written by|By)\s*\{\{\s*page\.perspective", POST_LAYOUT))
check("5d no avatar for perspectives", "perspective__avatar" not in POST_LAYOUT)
sf = read(ROOT / "_posts" / "2026-09-13-the-drawing-sfmoma-bought-about-losing-ssi.md")
asl = read(ROOT / "_posts" / "2026-09-12-the-interpreter-and-the-presidents-image.md")
check("5e SFMOMA still carries perspective PINA", 'perspective: "PINA"' in sf)
check("5f ASL still carries no perspective",
      "perspective:" not in asl[:asl.index("\n---", 3)])

print("\n%s\n%d passed, %d failed" % ("=" * 60, len(PASSES), len(FAILS)))
if FAILS:
    print("FAILED:")
    for f in FAILS:
        print("  -", f)
sys.exit(1 if FAILS else 0)
