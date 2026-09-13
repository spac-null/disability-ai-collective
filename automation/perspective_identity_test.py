#!/usr/bin/env python3
"""Focused tests for the canonical perspective identity (PINA / MIRA / SIIRI / ZENO).

Covers the checks named in the 2026-09-13 owner brief, A-R. Nothing here calls a model,
opens a network connection, sends mail, or publishes.

Run: python3 automation/perspective_identity_test.py
"""

import datetime
import json
import os
import pathlib
import re
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import knowledge_first as KF                      # noqa: E402
import new_engine_candidate as CAND               # noqa: E402

FAILS = []
PASSES = []


def check(label, cond, detail=""):
    (PASSES if cond else FAILS).append(label)
    print("  %-4s %s%s" % ("PASS" if cond else "FAIL", label,
                           "" if cond else "  -- %s" % detail))


def read(p):
    return pathlib.Path(p).read_text(encoding="utf-8")


PERSPECTIVE_DIR = ROOT / ".claude" / "perspective-research"
DOCTRINE = ROOT / ".claude" / "crip-minds-perspective-doctrine.md"

# ── A. Active current MAYA became MIRA ───────────────────────────────────────
print("\nA. active MAYA -> MIRA")
lib_stray = [p.name for p in sorted(PERSPECTIVE_DIR.glob("*.md"))
             if re.search(r"\bMAYA\b", read(p))]
check("A1a no bare MAYA anywhere in the question library", not lib_stray, str(lib_stray))
# The doctrine may state, once, that MAYA was renamed. That is the historical record of
# the rename; what it must not do is still USE MAYA as a live perspective.
doc_maya = re.findall(r"[^\n]*\bMAYA\b[^\n]*", read(DOCTRINE))
check("A1b doctrine mentions MAYA only as a recorded rename",
      len(doc_maya) == 1 and "renamed to" in doc_maya[0], str(doc_maya))
check("A2 MIRA present in the doctrine", re.search(r"\bMIRA\b", read(DOCTRINE)))
check("A3 MIRA is a declared perspective in code", "MIRA" in KF.PERSPECTIVES)
check("A4 MAYA is not a declared perspective in code", "MAYA" not in KF.PERSPECTIVES)

# ── B. Legacy "Maya Flux" untouched ──────────────────────────────────────────
print("\nB. legacy Maya Flux preserved")
legacy_posts = [p for p in (ROOT / "_posts").glob("*.md")
                if 'author: "Maya Flux"' in read(p)]
check("B1 legacy posts still carry author: Maya Flux", len(legacy_posts) > 0,
      "expected historical posts to keep their author string")
check("B2 legacy persona canon still on disk",
      (ROOT / "automation" / "persona_canon" / "maya-flux.md").is_file())
check("B3 doctrine still references the legacy persona path as history",
      "maya-flux" in read(DOCTRINE))
check("B4 no code maps Maya Flux to MIRA",
      not re.search(r"Maya Flux[^\n]{0,40}MIRA|MIRA[^\n]{0,40}Maya Flux",
                    "\n".join(read(p) for p in (ROOT / "automation").rglob("*.py")
                              if "_test" not in p.name)))

# ── C. The 48 approved questions survive the rename ──────────────────────────
print("\nC. approved question library")
qs = KF.load_questions()
check("C1 48 approved questions", len(qs) == 48, "got %d" % len(qs))
check("C2 all APPROVED_DURABLE", all(q["status"] == "APPROVED_DURABLE" for q in qs))
ids = [q["id"] for q in qs]
check("C3 ids unique and well-formed",
      len(set(ids)) == len(ids) and all(re.fullmatch(r"PR\d{3}-\d{2}", i) for i in ids))
dist = {}
for q in qs:
    dist[q.get("perspective", "SHARED")] = dist.get(q.get("perspective", "SHARED"), 0) + 1
check("C4 distribution PINA10/MIRA11/SIIRI8/ZENO10/SHARED9",
      dist == {"PINA": 10, "MIRA": 11, "SIIRI": 8, "ZENO": 10, "SHARED": 9}, str(dist))
check("C5 no question carries MAYA", not any(q.get("perspective") == "MAYA" for q in qs))

# ── primary_perspective rule ─────────────────────────────────────────────────
print("\nC(rule). primary_perspective")
check("Cr1 explicit primary", KF.primary_perspective("MIRA primarily -- x") == "MIRA")
check("Cr2 single bare name", KF.primary_perspective("ZENO.") == "ZENO")
check("Cr3 shared opener -> None", KF.primary_perspective("Shared -- ZENO on x, SIIRI on y") is None)
check("Cr4 two names, no primary -> None",
      KF.primary_perspective("SIIRI on a; PINA on b.") is None)
check("Cr5 empty -> None", KF.primary_perspective("") is None
      and KF.primary_perspective(None) is None)
check("Cr6 legacy name is never a perspective",
      KF.primary_perspective("Maya Flux primarily") is None)

# ── D/E/F/G. frontmatter contract ────────────────────────────────────────────
print("\nD-G. perspective in front matter")


def meta(**over):
    m = {"run": "r", "generated_at": "2026-09-13T09:00:00+00:00", "decision": "ACCEPT",
         "source_url": "", "source_sha256": "s", "discovery_hash": "",
         "article_form_hash": "", "grounding_status": "settled",
         "grounding_unsupported": 0, "provider_model": "m"}
    m.update(over)
    return m


fm_kf = CAND.build_frontmatter(title="T", author=CAND.PUBLIC_AUTHOR,
                               engine_meta=meta(perspective="PINA"), rehearsal=False)
check("D1 KNOWLEDGE_FIRST perspective persisted", 'perspective: "PINA"' in fm_kf, fm_kf)

fm_ow = CAND.build_frontmatter(title="T", author=CAND.PUBLIC_AUTHOR,
                               engine_meta=meta(perspective="MIRA"), rehearsal=False)
check("E1 ordinary-world explicit perspective persisted", 'perspective: "MIRA"' in fm_ow)

fm_none = CAND.build_frontmatter(title="T", author=CAND.PUBLIC_AUTHOR,
                                 engine_meta=meta(), rehearsal=False)
check("F1 no perspective -> field absent entirely", "perspective:" not in fm_none)
check("F2 no 'unknown' placeholder", "nknown" not in fm_none)

# G. legacy author never determines perspective
fm_legacy = CAND.build_frontmatter(title="T", author="Maya Flux",
                                   engine_meta=meta(), rehearsal=False)
check("G1 legacy author does not produce a perspective",
      "perspective:" not in fm_legacy)
def _code_only(src, fn):
    """EXACTLY one function's executable source, docstring and comments removed.

    Parsed rather than sliced: a substring search runs past the function into whatever
    follows it, and then a test is really asserting on unrelated prose.
    """
    import ast as _ast
    tree = _ast.parse(src)
    node = next(n for n in _ast.walk(tree)
                if isinstance(n, (_ast.FunctionDef, _ast.AsyncFunctionDef)) and n.name == fn)
    body = list(node.body)
    if (body and isinstance(body[0], _ast.Expr)
            and isinstance(getattr(body[0], "value", None), _ast.Constant)
            and isinstance(body[0].value.value, str)):
        body = body[1:]                      # drop the docstring
    return "\n".join(_ast.unparse(s) for s in body)


src_kf = read(HERE / "knowledge_first.py")
check("G2 perspective resolution reads no author field",
      not re.search(r"""author""", _code_only(src_kf, "primary_perspective")))
check("G3 perspective resolution reads only MINDS SHARPENED",
      "minds_sharpened" in _code_only(src_kf, "primary_perspective"))

# ── H. normal and resume publication use the SAME contract ───────────────────
print("\nH. normal vs retained/resume")
prod = read(HERE / "new_engine_production.py")
resume = read(HERE / "publish_retained_fast_lane.py")
check("H1 both publish via persist_candidate",
      "persist_candidate(" in prod and "persist_candidate(" in resume)
check("H2 resume no longer hardcodes a legacy persona author",
      'author="Maya Flux"' not in resume)
check("H3 both use PUBLIC_AUTHOR",
      "CAND.PUBLIC_AUTHOR" in prod and "CAND.PUBLIC_AUTHOR" in resume)
check("H4 one frontmatter builder, not two",
      "def build_frontmatter" not in resume and "def build_frontmatter" not in prod)

# ── I/J. public author, and perspective is never schema.org author ───────────
print("\nI-J. public authorship")
check("I1 PUBLIC_AUTHOR is Jascha Blume", CAND.PUBLIC_AUTHOR == "Jascha Blume")
cfg = read(ROOT / "_config.yml")
check("I2 site.public_author is Jascha Blume", 'public_author: "Jascha Blume"' in cfg)
default_layout = read(ROOT / "_layouts" / "default.html")
post_layout = read(ROOT / "_layouts" / "post.html")
feed = read(ROOT / "feed.xml")
check("I3 RSS dc:creator uses public_author", "site.public_author" in feed)
check("I4 meta author uses public_author",
      'name="author" content="{{ site.public_author }}"' in default_layout)

for name, txt in (("default.html", default_layout), ("post.html", post_layout)):
    # every JSON-LD "author" block must name public_author, never a perspective
    for block in re.findall(r'"author"\s*:\s*\{.*?\}', txt, re.S):
        check("J1 %s JSON-LD author is public_author" % name,
              "site.public_author" in block, block[:120])
        check("J2 %s JSON-LD author has no perspective" % name,
              "perspective" not in block, block[:120])
check("J3 perspective never assigned to an author field in templates",
      not re.search(r'author[^\n]{0,40}page\.perspective', default_layout + post_layout))

# ── K/L/M. templates ─────────────────────────────────────────────────────────
print("\nK-M. templates")
check("K1 perspective rendered only under a conditional",
      "{% if page.perspective %}" in post_layout)
check("K2 perspective is not labelled as a byline",
      not re.search(r"(Written by|By)\s*\{\{\s*page\.perspective", post_layout))
index = read(ROOT / "index.html")
check("L1 homepage has no fictional collective block",
      "voice-strip" not in index and "home-collective" not in index)
check("L2 homepage names no legacy persona",
      not re.search(r"Pixel Nova|Siri Sage|Maya Flux|Zen Circuit", index))
research = read(ROOT / "research.html")
check("M1 articles page has no perspective filter",
      "persona-filter" not in research and "data-perspective" not in research)
check("M2 articles page still has search",
      'id="article-search"' in research)

# ── N-Q. newsletter ──────────────────────────────────────────────────────────
print("\nN-Q. newsletter")
impl_path = HERE / "newsletter_weekly_digest.py"
check("O0 canonical implementation is in the repo", impl_path.is_file())
sys.modules.pop("newsletter_weekly_digest", None)
import newsletter_weekly_digest as NL             # noqa: E402

with tempfile.TemporaryDirectory() as td:
    posts = pathlib.Path(td) / "_posts"
    posts.mkdir()
    today = datetime.datetime.now(datetime.timezone.utc).date()
    (posts / ("%s-with-image.md" % today)).write_text(
        '---\ntitle: "With Image"\nauthor: "Maya Flux"\n'
        'image: /assets/x.jpg\nimage_alt: "Alt text here"\n'
        'perspective: "MIRA"\ndek: "A dek."\n---\n\nBody paragraph.\n', encoding="utf-8")
    (posts / ("%s-no-image.md" % today)).write_text(
        '---\ntitle: "No Image"\nauthor: "Pixel Nova"\n---\n\nPlain body.\n',
        encoding="utf-8")
    NL.POSTS_DIR = posts
    arts = NL.get_recent_articles(days=7)
    check("N1 both articles collected", len(arts) == 2, str(len(arts)))
    a_img = [a for a in arts if a["title"] == "With Image"][0]
    a_non = [a for a in arts if a["title"] == "No Image"][0]
    check("N2 hero image is an absolute URL",
          a_img["image_url"] == "https://cripminds.com/assets/x.jpg", a_img["image_url"])
    check("N3 image_alt carried", a_img["image_alt"] == "Alt text here")
    check("N4 missing image -> empty, not a placeholder", a_non["image_url"] == "")
    check("N5 perspective read from front matter", a_img["perspective"] == "MIRA")
    check("N6 absent perspective stays empty", a_non["perspective"] == "")

    html = NL.build_digest(arts, "TOK")
    check("N7 hero <img> rendered with responsive style",
          'src="https://cripminds.com/assets/x.jpg"' in html
          and "max-width:560px" in html and "height:auto" in html)
    check("N8 alt text in the email", 'alt="Alt text here"' in html)
    check("N9 exactly one img for the one article that has one",
          html.count("<img") == 1, str(html.count("<img")))
    check("N10 public author in the byline", NL.PUBLIC_AUTHOR in html)
    check("N11 perspective shown when present", "MIRA" in html)
    check("Q1 no legacy persona name in the email",
          not re.search(r"Pixel Nova|Siri Sage|Maya Flux|Zen Circuit", html))
    check("Q2 no 'from the collective' language", "from the collective" not in html)
    check("Q3 pluralised house language", "2 new Crip Minds essays this week" in html)
    check("Q4 never renders Unknown", "Unknown" not in html)

    # P. preview cannot send
    out = pathlib.Path(td) / "preview.html"
    sent = []
    real_send = NL.send_one
    NL.send_one = lambda *a, **k: sent.append(a) or True
    try:
        NL.main(["--preview", str(out)])
    finally:
        NL.send_one = real_send
    check("P1 preview wrote a file", out.is_file())
    check("P2 preview sent nothing", sent == [], str(sent))
    src_nl = read(impl_path)
    check("P3 preview() never calls send_one",
          "send_one(" not in _code_only(src_nl, "preview"))
    check("P4 preview() never opens the subscriber database",
          "get_weekly_subscribers" not in _code_only(src_nl, "preview")
          and "sqlite3" not in _code_only(src_nl, "preview"))

wrapper = pathlib.Path("/srv/scripts/ops/newsletter-weekly-digest.py")
if wrapper.is_file():
    w = read(wrapper)
    check("O1 ops wrapper points at the repo implementation",
          "newsletter_weekly_digest.py" in w)
    check("O2 ops wrapper holds no business logic",
          "build_digest" not in w and "resend.com" not in w and "subscribers" not in w)
    check("O3 ops wrapper is small", len(w.splitlines()) < 60, str(len(w.splitlines())))
else:
    print("  SKIP O1-O3 ops wrapper not installed yet")

# ── R. reference articles unchanged ──────────────────────────────────────────
print("\nR. reference articles")
asl = ROOT / "_posts" / "2026-09-12-the-interpreter-and-the-presidents-image.md"
sf = ROOT / "_posts" / "2026-09-13-the-drawing-sfmoma-bought-about-losing-ssi.md"
for label, p in (("ASL", asl), ("SFMOMA", sf)):
    t = read(p)
    body = t[t.index("\n---", 3) + 4:]
    check("R1 %s prose has no perspective/identity edit" % label,
          not re.search(r"\bMIRA\b|\bPINA\b|\bSIIRI\b|\bZENO\b", body))
    check("R2 %s keeps its historical author" % label, 'author: "Maya Flux"' in t)
    check("R3 %s keeps its sources block" % label, "sources:" in t)
    check("R4 %s keeps its hero image" % label, re.search(r"^image: ", t, re.M))
check("R5 SFMOMA carries its proven perspective", 'perspective: "PINA"' in read(sf))
check("R6 ASL carries no perspective (no commission artifact)",
      "perspective:" not in read(asl).split("\n---", 2)[0] + "\n")

print("\n%s\n%d passed, %d failed" % ("=" * 60, len(PASSES), len(FAILS)))
if FAILS:
    print("FAILED:")
    for f in FAILS:
        print("  -", f)
sys.exit(1 if FAILS else 0)
