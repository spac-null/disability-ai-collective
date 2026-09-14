#!/usr/bin/env python3
"""
publication_epoch_test.py -- the current-publication corpus contract.

The site splits readable posts into the CURRENT publication (what /research/, the
homepage and /feed.xml put forward) and EARLIER WORK (/archive/). The split is derived,
never stored on an article: the predicate lives in _includes/backlist.html and reads
_data/backlist.yml. See the long note at the top of _data/backlist.yml for the rule and
for why `pre_epoch` is a closed list rather than a date.

WHAT THIS PINS

  1. The boundary authority is the marker the publishing system already writes --
     `engine_generation: CURRENT_ENGINE` / `editorial_engine: NEW_ENGINE_V1` -- and not a
     calendar comparison and not a hand-maintained whitelist of titles.
  2. The cutover fixtures: the two essays of the September 2026 editorial system classify
     CURRENT; representative earlier essays, including ones that were carried before the
     boundary existed, classify EARLIER.
  3. The future-publication contract: front matter built by the REAL publication path
     (new_engine_candidate.build_frontmatter) classifies CURRENT with nothing edited here.
     This is the property that keeps the corpus from needing a manual list.
  4. Classification stays off the articles: no post carries an epoch/selection field.

WHAT THIS DELIBERATELY DOES NOT PIN

  The SIZE of the current corpus. `len(current) == 2` is true at cutover and false the
  day the next article publishes, so asserting it would turn a correct publication into
  a failing test. The cutover fixtures below name articles, never a count.

No network, no model calls. No production database. No git. Nothing published.

Run (from repo root):
  python3 automation/publication_epoch_test.py
"""

import datetime
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import new_engine_candidate as CAND                          # noqa: E402

POSTS = ROOT / "_posts"
BACKLIST_YML = ROOT / "_data" / "backlist.yml"
BACKLIST_LIQUID = ROOT / "_includes" / "backlist.html"

FAILURES = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + ("" if cond else "  " + str(detail)))
    if not cond:
        FAILURES.append(name)


# ── the data file, read the way Jekyll reads it ─────────────────────────────────────

def load_epoch_config():
    """`legacy_through`, `editor_byline` and the `pre_epoch` slugs from _data/backlist.yml.

    Deliberately a small hand parser rather than PyYAML: the test must not acquire a
    dependency the site build does not have, and the shapes it needs are three scalars
    and one list of plain slugs.
    """
    cfg = {"pre_epoch": [], "selected": []}
    key = None
    for raw in BACKLIST_YML.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        m = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val:
                cfg[key] = val.strip('"').strip("'")
            continue
        m = re.match(r"^\s+-\s+(\S+)\s*$", line)
        if m and key in ("pre_epoch", "selected"):
            cfg[key].append(m.group(1))
    return cfg


def parse_frontmatter(text):
    """Front matter as a flat dict of strings. Enough for the fields this predicate reads."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    fm = {}
    for line in text[3:end].splitlines():
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return fm


def load_posts():
    out = []
    for p in sorted(POSTS.glob("*.md")):
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})-(.*)\.md$", p.name)
        if not m:
            continue
        fm = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
        # Jekyll takes the date from front matter when present, else from the filename.
        date = fm.get("date", "")[:10] or "%s-%s-%s" % m.group(1, 2, 3)
        out.append({"slug": m.group(4), "path": p, "fm": fm, "date": date})
    return out


# ── the predicate, mirroring _includes/backlist.html ────────────────────────────────

def is_current(post, cfg):
    """CURRENT == in the publication generation now running.

    Mirrors the Liquid in _includes/backlist.html. test_predicate_matches_liquid below
    guards the mirror against drift, so a change to the rule cannot pass by editing only
    one of the two.
    """
    fm = post["fm"]
    if str(fm.get("withdrawn", "")).lower() == "true":
        return False
    if post["slug"] in cfg["pre_epoch"]:
        return False
    if fm.get("engine_generation") == "CURRENT_ENGINE":
        return True
    if fm.get("editorial_engine") == "NEW_ENGINE_V1":
        return True
    if post["date"] > str(cfg["legacy_through"]):
        return True
    if fm.get("author") == cfg["editor_byline"]:
        return True
    return False


def is_note(post, cfg):
    return post["fm"].get("author") == cfg["editor_byline"]


# ── cutover fixtures ────────────────────────────────────────────────────────────────

CURRENT_AT_CUTOVER = [
    "the-interpreter-and-the-presidents-image",
    "the-drawing-sfmoma-bought-about-losing-ssi",
]

# Earlier essays that MUST NOT be in the current corpus. The first four were among the
# essays the site carried before this boundary existed (the finished legacy reissue
# programme), which is exactly the cohort the epoch moves to earlier work. The last two
# carry the current engine's markers but published before the epoch opened, by owner
# approval during the changeover, and are held out by `pre_epoch`.
EARLIER_AT_CUTOVER = [
    "jebel-irhoud-broke-the-single-dot-i-was-trusting",
    "the-eyebrow-was-never-about-feeling",
    "the-disorder-is-a-system-property",
    "what-yallourn-sounded-like-before-anyone-photographed",
    "at-tollymore-getting-to-bed-means-crossing-a-courtyard",
    "the-upper-room-at-wildsumaco",
]


def test_cutover_fixtures():
    cfg = load_epoch_config()
    posts = {p["slug"]: p for p in load_posts()}

    for slug in CURRENT_AT_CUTOVER:
        p = posts.get(slug)
        check("current corpus contains %s" % slug, p is not None and is_current(p, cfg),
              "missing" if p is None else "classified earlier")

    for slug in EARLIER_AT_CUTOVER:
        p = posts.get(slug)
        check("current corpus excludes %s" % slug, p is not None and not is_current(p, cfg),
              "missing" if p is None else "classified current")

    # The contract at the moment of cutover, stated as a set of articles rather than a
    # size, so it keeps its meaning as the publication grows.
    current_articles = sorted(p["slug"] for p in posts.values()
                              if is_current(p, cfg) and not is_note(p, cfg))
    check("at cutover the current articles are exactly the two September 2026 essays",
          current_articles == sorted(CURRENT_AT_CUTOVER), current_articles)


def test_earlier_work_is_still_published():
    """Reclassification is not depublication: the moved essays keep their files, their
    URLs and their bodies. Nothing here may acquire `withdrawn`, which is a different
    state with different behaviour and its own front matter."""
    cfg = load_epoch_config()
    posts = {p["slug"]: p for p in load_posts()}
    for slug in EARLIER_AT_CUTOVER:
        p = posts.get(slug)
        if p is None:
            check("earlier essay %s still exists" % slug, False, "file missing")
            continue
        check("earlier essay %s is not withdrawn" % slug,
              str(p["fm"].get("withdrawn", "")).lower() != "true")


def test_classification_is_not_stored_on_articles():
    """No article carries selection state. If a future change starts stamping one, the
    'front matter unchanged' guarantee of the cutover quietly stops being true."""
    offenders = []
    for p in load_posts():
        for field in ("publication_epoch", "epoch", "carried", "archived", "backlist"):
            if field in p["fm"]:
                offenders.append("%s:%s" % (p["slug"], field))
    check("no post stores its own corpus classification", not offenders, offenders[:5])


def test_pre_epoch_list_is_closed_and_real():
    """`pre_epoch` describes a transition that has already happened. Every slug in it must
    name a real post that predates the epoch, so the list can never quietly become the
    manual whitelist this design exists to avoid."""
    cfg = load_epoch_config()
    posts = {p["slug"]: p for p in load_posts()}
    check("pre_epoch is small and explicit", 0 < len(cfg["pre_epoch"]) <= 5, cfg["pre_epoch"])
    for slug in cfg["pre_epoch"]:
        p = posts.get(slug)
        check("pre_epoch slug %s names a real post" % slug, p is not None)
        if p is None:
            continue
        check("pre_epoch slug %s carries the engine markers it is held out from" % slug,
              p["fm"].get("engine_generation") == "CURRENT_ENGINE"
              or p["fm"].get("editorial_engine") == "NEW_ENGINE_V1",
              "would be excluded anyway; the entry is misleading")
        check("pre_epoch slug %s predates the epoch" % slug,
              p["date"] <= str(cfg["legacy_through"]), p["date"])


# ── the property that matters most: the next article needs no edit here ─────────────

def test_future_publication_is_current_automatically():
    """Front matter from the REAL publication path classifies CURRENT.

    This is the future-publication contract. It builds front matter with
    new_engine_candidate.build_frontmatter -- the function the running system uses -- and
    asks the site's predicate about the result. Nothing in _data/backlist.yml is touched,
    so a passing result means a newly published article joins the current corpus on its
    own.
    """
    cfg = load_epoch_config()
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    engine_meta = {
        "generated_at": tomorrow,
        "decision": "ACCEPT",
        "run": "production-%sT000000Z-deadbeef" % tomorrow.replace("-", ""),
        "source_url": "https://example.org/a-story",
        "source_sha256": "0" * 64,
        "discovery_hash": "1" * 64,
        "article_form_hash": "2" * 64,
        "grounding_status": "settled",
        "grounding_unsupported": 0,
        "provider_model": "claude-opus-5",
    }
    text = CAND.build_frontmatter(title="A Future Article", author="Maya Flux",
                                 engine_meta=engine_meta, rehearsal=False)
    fm = parse_frontmatter(text if text.startswith("---") else "---\n" + text + "\n---\n")

    check("the publication path stamps engine_generation",
          fm.get("engine_generation") == "CURRENT_ENGINE", fm.get("engine_generation"))
    check("the publication path stamps editorial_engine",
          fm.get("editorial_engine") == "NEW_ENGINE_V1", fm.get("editorial_engine"))

    future = {"slug": "a-future-article", "fm": fm,
              "date": fm.get("date", tomorrow)[:10] or tomorrow}
    check("a newly published article classifies CURRENT with no list edited",
          is_current(future, cfg))

    # And it must not depend on the date backstop: strip the markers' only alternative
    # support by dating it inside the legacy period. The generation, not the calendar,
    # is what carries it.
    backdated = dict(future, date="2026-01-01")
    check("it is the engine marker, not the date, that makes it current",
          is_current(backdated, cfg))


def test_date_alone_does_not_make_an_article_current():
    """The mirror image: a legacy-era article does not become current by its date, and
    the epoch is not implemented as `date >= 2026-09-12`."""
    cfg = load_epoch_config()
    legacy = {"slug": "some-legacy-piece", "date": "2026-05-01",
              "fm": {"author": "Siri Sage", "pipeline_version": "3.2"}}
    check("a legacy-pipeline article is not current",
          not is_current(legacy, cfg))
    check("pipeline_version is no longer a current-generation marker",
          not is_current({"slug": "x", "date": "2026-05-01",
                          "fm": {"pipeline_version": "3.2"}}, cfg))


# ── drift guard between the Python mirror and the Liquid the site actually runs ─────

def test_predicate_matches_liquid():
    liquid = BACKLIST_LIQUID.read_text(encoding="utf-8")
    rule = [l for l in liquid.splitlines() if "backlist_active_slugs" not in l
            and "engine_generation" in l]
    check("the Liquid predicate tests engine_generation", bool(rule), "not found")
    joined = "\n".join(rule)
    check("the Liquid predicate tests editorial_engine", "editorial_engine" in joined, joined)
    check("the Liquid predicate honours pre_epoch",
          "backlist_pre_epoch_slugs" in liquid, "pre_epoch not consulted")
    check("the Liquid predicate no longer promotes on `selected`",
          "backlist_selected_slugs contains bl_key" not in liquid,
          "selected is still part of membership")
    check("the Liquid predicate no longer promotes on pipeline_version",
          "p.pipeline_version" not in liquid, "pipeline_version still promotes")


def test_current_essays_keep_their_own_facts():
    """Perspective is metadata an article either genuinely carries or does not. The
    cutover must not invent one for symmetry: SFMOMA declares PINA, the ASL essay
    declares none, and neither is back-filled from a legacy persona name."""
    posts = {p["slug"]: p for p in load_posts()}
    sfmoma = posts.get("the-drawing-sfmoma-bought-about-losing-ssi")
    asl = posts.get("the-interpreter-and-the-presidents-image")
    check("SFMOMA still declares perspective PINA",
          sfmoma is not None and sfmoma["fm"].get("perspective") == "PINA",
          sfmoma and sfmoma["fm"].get("perspective"))
    check("the ASL essay declares no perspective",
          asl is not None and not asl["fm"].get("perspective"),
          asl and asl["fm"].get("perspective"))


def main():
    for fn in [test_cutover_fixtures,
               test_earlier_work_is_still_published,
               test_classification_is_not_stored_on_articles,
               test_pre_epoch_list_is_closed_and_real,
               test_future_publication_is_current_automatically,
               test_date_alone_does_not_make_an_article_current,
               test_predicate_matches_liquid,
               test_current_essays_keep_their_own_facts]:
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL PUBLICATION-EPOCH TESTS PASSED")


if __name__ == "__main__":
    main()
