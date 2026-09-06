#!/usr/bin/env python3
"""
translation_sources_test.py -- the Go deeper block survives re-derivation.

The defect: `write_translation` emitted no `sources`, so re-deriving an existing edition
deleted its whole Go deeper block. Observed on WildSumaco -- five curated entries gone,
restored by hand, and it would have gone again on the next run.

Narrow by design. No provider, no network, no repo mutation: `write_translation` is pure
given a bundle, so the whole reconciliation is testable offline.

USAGE: python3 automation/translation_sources_test.py
"""
from __future__ import annotations

import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import translate_publication as TP                                   # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    print("%s  %s%s" % ("PASS" if cond else "FAIL", name, "" if cond else "  -- %s" % detail))
    if not cond:
        FAILURES.append(name)


EN_SOURCES = """sources:
  - title: "Station page"
    url: "https://example.invalid/station"
    publisher: "example.invalid"
  - title: "Studio"
    url: "https://studio.invalid/"
    publisher: "studio.invalid"
  - title: "Magazine piece"
    url: "https://magazine.invalid/piece"
    publisher: "Magazine"
"""

def en_post(with_sources=True, extra=""):
    return ('---\nlayout: "post"\ntitle: "A pavilion"\nauthor: "Maya Flux"\n'
            'date: 2026-09-06\nimage: "/assets/x.jpg"\nkeywords: [a, b]\n'
            'dek: "A dek."\nexcerpt: "An excerpt."\n'
            'engine_run: "production-x"\nsource_sha256: "%s"\n%s%s---\n\nBody text.\n'
            % ("0" * 64, EN_SOURCES if with_sources else "", extra))


TR = {"title": "Een paviljoen", "article": "Nederlandse tekst.", "dek": "Een dek.",
      "homepage_excerpt": "Een samenvatting.", "image_alt": "Alt"}


def build(tmp, with_sources=True):
    repo = tmp / "repo"
    (repo / "_posts").mkdir(parents=True, exist_ok=True)
    (repo / "_nl").mkdir(parents=True, exist_ok=True)
    post = repo / "_posts" / "2026-09-06-a-pavilion.md"
    post.write_text(en_post(with_sources), encoding="utf-8")
    return repo, post


def main() -> int:
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="nlsources-"))
    saved_repo = TP.REPO
    try:
        repo, post = build(tmp)
        TP.REPO = repo

        # ── 1. a curated Dutch list survives re-derivation ───────────────────────
        first = TP.write_translation("nl", post, TP.english_bundle(post), TR)
        fm1, _ = TP.read_post(first)
        check("a first derivation carries the English list forward",
              [s["url"] for s in fm1["sources"]]
              == [s["url"] for s in TP.read_post(post)[0]["sources"]])

        # A human localises the labels, the way WildSumaco's edition was localised.
        text = first.read_text(encoding="utf-8")
        text = (text.replace('publisher: "example.invalid"', 'publisher: "example.invalid, Engelstalig"')
                    .replace('publisher: "Magazine"', 'publisher: "Magazine, Engelstalig"'))
        first.write_text(text, encoding="utf-8")
        curated = TP.read_post(first)[0]["sources"]

        TP.write_translation("nl", post, TP.english_bundle(post), TR)
        fm2, _ = TP.read_post(first)
        check("re-derivation retains the curated list (THE BUG)",
              len(fm2.get("sources") or []) == 3,
              "got %r" % (fm2.get("sources"),))
        check("URLs unchanged",
              [s["url"] for s in fm2["sources"]] == [s["url"] for s in curated])
        check("order unchanged",
              [s["title"] for s in fm2["sources"]] == [s["title"] for s in curated])
        check("localised publisher labels are NOT overwritten by the English ones",
              [s.get("publisher") for s in fm2["sources"]]
              == ["example.invalid, Engelstalig", "studio.invalid", "Magazine, Engelstalig"],
              [s.get("publisher") for s in fm2["sources"]])

        # ── 2. English stays authoritative for membership and order ─────────────
        p = post.read_text(encoding="utf-8").replace(
            '  - title: "Studio"\n    url: "https://studio.invalid/"\n    publisher: "studio.invalid"\n',
            '  - title: "New source"\n    url: "https://new.invalid/x"\n    publisher: "New"\n')
        post.write_text(p, encoding="utf-8")
        TP.write_translation("nl", post, TP.english_bundle(post), TR)
        fm3, _ = TP.read_post(first)
        check("a source dropped in English is dropped from the edition",
              "https://studio.invalid/" not in [s["url"] for s in fm3["sources"]])
        check("a source added in English arrives with its English label",
              {"title": "New source", "url": "https://new.invalid/x", "publisher": "New"}
              in fm3["sources"])
        check("the surviving localised labels are still localised",
              fm3["sources"][0]["publisher"] == "example.invalid, Engelstalig")

        # ── 3. absence carries forward ──────────────────────────────────────────
        repo2, post2 = build(tmp / "b", with_sources=False)
        TP.REPO = repo2
        out2 = TP.write_translation("nl", post2, TP.english_bundle(post2), TR)
        fm4, _ = TP.read_post(out2)
        check("an article with no sources produces an edition with none",
              not fm4.get("sources") and "sources:" not in out2.read_text())

        # ── 4. nothing else about the front matter moved ────────────────────────
        TP.REPO = repo
        check("carried English fields unchanged",
              (fm3.get("date") is not None and fm3.get("author") == "Maya Flux"
               and fm3.get("image") == "/assets/x.jpg" and fm3.get("keywords") == ["a", "b"]))
        check("translation identity fields intact",
              fm3.get("lang") == "nl" and fm3.get("translation_of")
              and fm3.get("translation_source_bundle_sha256"))
        leaked = [k for k in ("engine_run", "source_sha256") if k in fm3]
        check("no engine provenance leaked with the sources: %s" % (leaked or "none"),
              not leaked)
        check("sources are the LAST front-matter key, after the scalars",
              out2 is not None and first.read_text().index("translation_source_bundle_sha256")
              < first.read_text().index("sources:"))
    finally:
        TP.REPO = saved_repo
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n%d check(s) failed" % len(FAILURES) if FAILURES else "\nall checks passed")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
