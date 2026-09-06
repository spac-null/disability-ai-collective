#!/usr/bin/env python3
"""
translate_publication.py -- the derivative edition stage.

WHERE IT SITS, and the position is the contract. It runs on a PUBLISHED English article:
after Safety, Grounding, Fact Check and the Reader or the owner have passed the exact bytes
that shipped. It does not translate a draft, and nothing it produces can reach the English
article -- the flow is one way by construction, because the English bundle it reads is
already on disk and it writes only into a language collection of its own.

    ENGLISH FINAL BUNDLE -> TRANSLATE -> FIDELITY CHECK -> PUBLISH EN + NL

WHAT A TRANSLATION MAY AND MAY NOT DO. It may reach for the sentence a Dutch editor would
actually write, including a different order and a different shape, because a sentence-by-
sentence rendering of English syntax is not Dutch. It may retitle: a title's job is to make
a reader who has never heard of the subject want it, and that job is language-specific. It
may not add a fact, drop an inconvenient one, explain what the English leaves implicit,
harden a hedge, widen a scope, or manufacture a clearer disability angle. Natural Dutch,
same evidence.

THE FIDELITY CHECK IS TWO PASSES, and the cheap one runs first. Numbers, dates and names
are compared mechanically -- they survive translation unchanged or something is wrong -- and
then one model call reads both bundles for what arithmetic cannot see: modality, negation,
scope, causal strength, attribution and who did what to whom. ONE correction pass on what
it names, and no loop.

LANGUAGE REGISTRY. `LANGUAGES` is the whole configuration. A second language is an entry
here plus a Jekyll collection; there is no framework and no rollout.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from new_engine_v1 import composition as CP          # noqa: E402
from new_engine_v1.provider import parse_json_object  # noqa: E402
from new_engine_v1.contracts import sha256_text     # noqa: E402

REPO = HERE.parent

LANGUAGES = {
    "nl": {
        "name": "Dutch",
        "endonym": "Nederlands",
        "collection": "_nl",
        "url_prefix": "/nl/",
        "register": (
            "Schrijf zoals een goede Nederlandse tijdschriftredacteur schrijft: gewone "
            "woorden, korte hoofdzinnen waar het kan, geen anglicismen, geen "
            "naamwoordstijl, geen 'men'. Vermijd letterlijke vertaling van Engelse "
            "zinsbouw -- als het Nederlands de zin anders zou ordenen, orden hem anders."),
    },
}

# The bundle fields, and the two that may be rewritten rather than rendered.
BUNDLE_FIELDS = ("title", "dek", "homepage_excerpt", "meta_description", "social_hook")
REPACKAGEABLE = ("title", "dek", "homepage_excerpt", "meta_description", "social_hook")

# Front matter a translation carries. Deliberately short: the engine's provenance --
# run ids, hashes, model names, gate stamps -- belongs to the English article that earned
# it and is not copied onto a derivative. `translation_of` is the link back to it.
CARRY_FROM_ENGLISH = ("date", "author", "category", "image", "keywords")


TRANSLATE_SYSTEM = (
    "You are the editor of the %(name)s edition of a magazine. An article has been "
    "published in English, checked and settled, and you are producing the %(name)s "
    "edition of it.\n"
    "\n"
    "%(register)s\n"
    "\n"
    "WRITE IT, DO NOT RENDER IT. A sentence-by-sentence transposition of English syntax "
    "reads as a translation, and a translation is not what is being published -- an "
    "edition is. Where the target language would order a sentence differently, order it "
    "differently. Where it would break one sentence in two, break it.\n"
    "\n"
    "AND CHANGE NOTHING THAT IS TRUE. Every fact, name, date, number, attribution, "
    "quotation, hedge, negation, scope and causal claim survives exactly as it is:\n"
    "  - a 'may' does not become a 'does', and a 'does' does not become a 'may'\n"
    "  - 'no record of X' does not become 'there is no X'\n"
    "  - a record about one place does not become a claim about a category\n"
    "  - two facts that sit next to each other do not acquire a 'daardoor'\n"
    "  - who said a thing keeps saying it, and who did a thing keeps doing it\n"
    "  - nothing the English leaves implicit is explained, and nothing inconvenient is "
    "dropped\n"
    "  - no local context, comparison or example is added that the English does not have\n"
    "  - the article's reading of its subject is neither sharpened nor softened\n"
    "\n"
    "NAMES AND TITLES stay in their own language: institutions, works, people, products "
    "and quoted labels are not translated. Numbers keep their values; write them the way "
    "the target language writes them.\n"
    "\n"
    "THE PACKAGING IS REWRITTEN, NOT RENDERED. The title, dek, homepage excerpt, meta "
    "description and social hook exist to make a reader who has never heard of this "
    "subject want it, and that job is language-specific -- so the title need not be the "
    "English title in another language. It may not introduce a claim or a relationship "
    "the article does not carry.\n"
    "\n"
    "IMAGE ALT TEXT is translated as description, not as caption prose.\n"
    "\n"
    "Return the article as markdown, with the same paragraph structure and the same "
    "figures in the same places."
)

TRANSLATE_SCHEMA = (
    "Reply with ONE JSON object:\n"
    '{"title": "...", "dek": "...", "homepage_excerpt": "...",\n'
    ' "meta_description": "...", "social_hook": "...",\n'
    ' "image_alt": "...",\n'
    ' "article": "the complete article as markdown"}\n'
    "No prose outside the JSON."
)

FIDELITY_SYSTEM = (
    "You compare a published English article with its translated edition and report what "
    "the translation changed about what is TRUE. You are not judging style, and you do "
    "not reward fluency: a beautiful sentence that hardens a hedge is a failure and a "
    "clumsy one that keeps it is not.\n"
    "\n"
    "Check, in this order, and report only what actually differs:\n"
    "  NAMES          people, places, institutions, works, products, quoted labels\n"
    "  NUMBERS        values, units, magnitudes\n"
    "  DATES          days, months, years, durations, order of events\n"
    "  QUOTED_LABELS  a field name, a status, a category, a term in quotation marks\n"
    "  NEGATION       a negative that became positive, or disappeared, or was added\n"
    "  MODALITY       may / can / does / will / would, and any hedge that hardened\n"
    "  SCOPE          one case became a class, a part became a whole, a place a category\n"
    "  CAUSAL         a correlation or adjacency that became a cause, or a cause lost\n"
    "  ATTRIBUTION    who says it, who found it, who did it\n"
    "  RELATIONS      subject and object swapped, or a relation reversed\n"
    "  IMAGES         alt text that describes a different picture than the English does\n"
    "\n"
    "A finding must quote both sides. If the two texts say the same thing in different "
    "words, that is not a finding -- it is a translation."
)

FIDELITY_SCHEMA = (
    "Reply with ONE JSON object:\n"
    '{"verdict": "PASS|HOLD",\n'
    ' "findings": [{"category": "NAMES|NUMBERS|DATES|QUOTED_LABELS|NEGATION|MODALITY|\n'
    '                            SCOPE|CAUSAL|ATTRIBUTION|RELATIONS|IMAGES",\n'
    '               "english": "the exact English", "translated": "the exact translation",\n'
    '               "what_changed": "one sentence"}]}\n'
    "PASS means you found nothing. No prose outside the JSON."
)


# ── the cheap pass: what arithmetic can see ───────────────────────────────────
_FIG = re.compile(r"<figure.*?</figure>", re.S)
_NUM = re.compile(r"\b\d[\d.,]*\b")
_YEAR = re.compile(r"\b(?:1[6-9]|20)\d{2}\b")
_ASSET = re.compile(r'(?:src=|!\[[^\]]*\]\()\s*"?\{?\{?[^"\')>]*?/assets/([^"\')\s>]+)')


def _plain(text: str) -> str:
    return _FIG.sub(" ", text or "")


def _numbers(text: str) -> set:
    """Values, normalised across decimal conventions: Dutch writes 3,5 for 3.5 and
    1.000 for 1,000, so a separator difference is not a changed number."""
    out = set()
    for n in _NUM.findall(_plain(text)):
        core = n.rstrip(".,")
        digits = re.sub(r"[.,]", "", core)
        out.add(digits.lstrip("0") or "0")
    return out


def mechanical_findings(en: dict, tr: dict) -> list:
    """Numbers, years and names must survive. Reported, never repaired here.

    Numbers and years are checked across the whole bundle; NAMES only across the ARTICLE,
    because the packaging is title-cased and is deliberately rewritten rather than
    rendered -- "The Upper Room" offers three capitals and no names.
    """
    out = []
    fields = ("article", "image_alt") + BUNDLE_FIELDS
    en_all = " ".join(str(en.get(k) or "") for k in fields)
    tr_all = " ".join(str(tr.get(k) or "") for k in fields)
    lost = sorted(_numbers(en_all) - _numbers(tr_all))
    added = sorted(_numbers(tr_all) - _numbers(en_all))
    if lost:
        out.append({"category": "NUMBERS", "english": ", ".join(lost)[:200],
                    "translated": "", "what_changed": "value(s) present in English and "
                                                      "absent from the translation"})
    if added:
        out.append({"category": "NUMBERS", "english": "", "translated": ", ".join(added)[:200],
                    "what_changed": "value(s) in the translation that the English "
                                    "does not contain"})
    for y in sorted(set(_YEAR.findall(_plain(en_all))) - set(_YEAR.findall(_plain(tr_all)))):
        out.append({"category": "DATES", "english": y, "translated": "",
                    "what_changed": "year dropped"})
    # Names: capitalised tokens the English uses more than once, which a translation has
    # no reason to lose. Single mentions are skipped -- they are where sentence-initial
    # capitals and ordinary nouns live.
    # Names: a capital used MID-SENTENCE, where capitalisation means something, or any
    # capital the English uses twice. Sentence-initial singletons are skipped -- that is
    # where ordinary nouns wear a capital and where the false positives live.
    from new_engine_v1 import story as ST
    counts = {}
    for tok in re.findall(r"\b[A-Z][A-Za-z’'-]{2,}\b", _plain(en.get("article") or "")):
        counts[tok] = counts.get(tok, 0) + 1
    named = {t for t, n in counts.items() if n >= 2}
    named |= ST._entities(_plain(en.get("article") or ""), skip_sentence_initial=True)
    low = _plain(tr_all).lower()
    # IMAGE IDENTITY AND PLACEMENT ARE NOT TRANSLATABLE. Alt text is prose and may be
    # rewritten; the asset a figure points at, and how many figures the body carries, are
    # structure. A translation that drops a figure or renames an asset has changed the
    # article, not its language.
    en_src = _ASSET.findall(en.get("article") or "")
    tr_src = _ASSET.findall(tr.get("article") or "")
    if en_src != tr_src:
        out.append({"category": "IMAGES", "english": ", ".join(en_src)[:200],
                    "translated": ", ".join(tr_src)[:200],
                    "what_changed": "the body's image assets differ in identity or order"})
    en_fig = (en.get("article") or "").count("<figure")
    tr_fig = (tr.get("article") or "").count("<figure")
    if en_fig != tr_fig:
        out.append({"category": "IMAGES", "english": "%d figures" % en_fig,
                    "translated": "%d figures" % tr_fig,
                    "what_changed": "figure count changed"})
    for tok in sorted(named):
        base = re.sub(r"['’]s$", "", tok)
        # A NAME CAN CHANGE SHAPE WITHOUT GOING MISSING. Demonyms and adjectival forms are
        # inflected differently in every language -- "Andean" is "Andes-", "Ecuadorian" is
        # "Ecuadoriaanse" -- and the first Dutch edition was held on exactly those two,
        # both of which were present and correct. A stem match keeps the check where it
        # belongs, on a name that is NOWHERE; the model pass reads the rest.
        # Four characters, deliberately loose: "Andean" becomes "Andes-", which shares
        # only "Ande". This pass exists to catch a name that is NOWHERE, and a false HOLD
        # costs a correction pass on prose that was right -- the model pass reads for the
        # subtler NAMES failures.
        stem = base.lower()[:4]
        if base.lower() in low or (len(base) >= 5 and stem in low):
            continue
        if base.lower() in ST._FUNCTION_WORDS:
            continue
        if ST._stem(base.lower()) in CP._COMMON_ENGLISH:      # ordinary word, capitalised
            continue
        out.append({"category": "NAMES", "english": tok, "translated": "",
                    "what_changed": "named in English, absent from the translation"})
    return out


# ── the stage ─────────────────────────────────────────────────────────────────
def translate_bundle(provider, bundle: dict, lang: str, corrections: list | None = None,
                     previous: dict | None = None) -> dict:
    cfg = LANGUAGES[lang]
    user = ["THE PUBLISHED ENGLISH EDITION", ""]
    for f in BUNDLE_FIELDS:
        if bundle.get(f):
            user.append("%s: %s" % (f.upper(), bundle[f]))
    if bundle.get("image_alt"):
        user.append("IMAGE_ALT: %s" % bundle["image_alt"])
    user += ["", "ARTICLE", bundle["article"], "", TRANSLATE_SCHEMA]
    if corrections:
        # AN EDIT, NOT A SECOND TRANSLATION. "Change nothing else" is only meaningful if
        # the thing to change is in front of the model, so the held edition is handed back
        # whole and the findings name what to touch. Regenerating from the English instead
        # -- which this did until it was pointed out -- produces a different edition whose
        # other sentences nobody has compared to anything.
        if not previous:
            raise ValueError("a correction pass needs the edition it is correcting")
        prev = ["THE EDITION BELOW WAS HELD BY THE FIDELITY CHECK. Return it again with "
                "ONLY these findings fixed. Every other sentence, including its wording "
                "and its rhythm, comes back unchanged.", ""]
        prev += ["  - [%s] English: %s | your edition: %s | %s"
                 % (c.get("category"), str(c.get("english"))[:140],
                    str(c.get("translated"))[:140], c.get("what_changed", ""))
                 for c in corrections[:10]]
        prev += ["", "YOUR PREVIOUS EDITION", ""]
        for f in BUNDLE_FIELDS:
            if previous.get(f):
                prev.append("%s: %s" % (f.upper(), previous[f]))
        if previous.get("image_alt"):
            prev.append("IMAGE_ALT: %s" % previous["image_alt"])
        prev += ["", previous.get("article") or "", "", "=" * 60, ""]
        user = prev + user
    comp = provider.complete(system=TRANSLATE_SYSTEM % cfg,
                             user="\n".join(user), max_tokens=12_000)
    obj = parse_json_object(comp.text)
    out = {f: str(obj.get(f) or "").strip() for f in BUNDLE_FIELDS}
    out["image_alt"] = str(obj.get("image_alt") or "").strip()
    out["article"] = str(obj.get("article") or "").strip()
    out["lang"] = lang
    out["provider"] = comp.identity() if hasattr(comp, "identity") else {}
    missing = [f for f in ("article", "title") if not out[f]]
    if missing:
        raise ValueError("the translation returned no %s" % ", ".join(missing))
    return out


def fidelity_check(provider, en: dict, tr: dict) -> dict:
    """One bounded check: the mechanical pass, then one model call."""
    mech = mechanical_findings(en, tr)
    user = ["ENGLISH", ""]
    for f in BUNDLE_FIELDS:
        if en.get(f):
            user.append("%s: %s" % (f.upper(), en[f]))
    if en.get("image_alt"):
        user.append("IMAGE_ALT: %s" % en["image_alt"])
    user += ["", en["article"], "", "=" * 60, "", "TRANSLATION", ""]
    for f in BUNDLE_FIELDS:
        if tr.get(f):
            user.append("%s: %s" % (f.upper(), tr[f]))
    if tr.get("image_alt"):
        user.append("IMAGE_ALT: %s" % tr["image_alt"])
    user += ["", tr["article"], "", FIDELITY_SCHEMA]
    comp = provider.complete(system=FIDELITY_SYSTEM, user="\n".join(user), max_tokens=3_000)
    obj = parse_json_object(comp.text)
    model = [f for f in (obj.get("findings") or []) if isinstance(f, dict)]
    findings = mech + model
    return {"verdict": "HOLD" if findings else "PASS",
            "findings": findings,
            "mechanical_findings": mech,
            "model_findings": model,
            "provider": comp.identity() if hasattr(comp, "identity") else {}}


# ── reading the English edition, writing the derivative one ───────────────────
def read_post(path: pathlib.Path) -> tuple:
    """Front matter as YAML, body as text.

    yaml.safe_load rather than a regex, so a value keeps its type: `keywords` is a flow
    sequence and must come back a list, or the edition would re-emit it quoted as one
    long string and every consumer of that field would silently see one keyword.
    """
    import yaml
    raw = path.read_text(encoding="utf-8")
    _, fm_text, body = raw.split("---", 2)
    fm = yaml.safe_load(fm_text) or {}
    return fm, body.strip()


def _yaml_value(v) -> str:
    """Emit a value in its own shape: a list stays a flow sequence, a date stays a date."""
    if isinstance(v, list):
        return "[%s]" % ", ".join(str(x) for x in v)
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()[:10] if isinstance(v, datetime.date) else v.isoformat()
    return json.dumps(str(v))


def english_bundle(path: pathlib.Path) -> dict:
    """The frozen English bundle: the public fields the article ACTUALLY HAS.

    An article published before the packaging stage existed has a title and an image alt
    and nothing else, and that is what its edition gets. Generating a dek and a homepage
    excerpt here and translating those would put two unchecked English claims into the
    world through the side door -- they would never have passed Safety, the Grounder or
    the Fact Check, which read the bundle, and the Dutch edition would be the first place
    they appeared. If such an article should have packaging, it earns it in the pipeline
    that checks it, and the edition is remade afterwards.

    No model call. This function reads a file.
    """
    fm, body = read_post(path)
    bundle = {"article": body, "title": fm.get("title", ""),
              "dek": fm.get("dek", ""), "homepage_excerpt": fm.get("excerpt", ""),
              "meta_description": fm.get("meta_description", ""),
              "social_hook": fm.get("social_hook", ""),
              "image_alt": fm.get("image_alt", ""), "front_matter": fm}
    bundle["fields_present"] = [f for f in BUNDLE_FIELDS if bundle.get(f)]
    bundle["fields_absent"] = [f for f in BUNDLE_FIELDS if not bundle.get(f)]
    return bundle


def bundle_sha256(bundle: dict) -> str:
    """The hash of the WHOLE frozen public bundle, not the article body: the edition is
    made from the article AND its packaging, so the article's hash alone would not detect
    a dek that changed under it."""
    return sha256_text(json.dumps(
        {k: bundle.get(k) or "" for k in ("article", "image_alt") + BUNDLE_FIELDS},
        sort_keys=True, ensure_ascii=False))


def slug_of(en_path: pathlib.Path) -> str:
    return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", en_path.stem)


def translation_path(lang: str, en_path: pathlib.Path) -> pathlib.Path:
    """WITHOUT the date prefix, and that is not cosmetic. The collection's permalink is
    /nl/:name/, and :name is the filename stem -- a dated filename would publish the
    edition at /nl/2026-09-06-the-upper-room/ while every link written for it points at
    /nl/the-upper-room/. The date is in the front matter, where the collection reads it."""
    return REPO / LANGUAGES[lang]["collection"] / ("%s.md" % slug_of(en_path))


def write_translation(lang: str, en_path: pathlib.Path, en: dict, tr: dict) -> pathlib.Path:
    """One file in the language collection. No engine provenance is copied."""
    fm = en["front_matter"]
    out = translation_path(lang, en_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = ["---", 'layout: "post"', 'title: %s' % json.dumps(tr["title"]),
             'lang: "%s"' % lang]
    for k in CARRY_FROM_ENGLISH:
        if fm.get(k):
            lines.append("%s: %s" % (k, _yaml_value(fm[k])))
    if tr.get("image_alt"):
        lines.append("image_alt: %s" % json.dumps(tr["image_alt"]))
    for field, key in (("dek", "dek"), ("homepage_excerpt", "excerpt"),
                       ("meta_description", "meta_description"),
                       ("social_hook", "social_hook")):
        if tr.get(field):
            lines.append("%s: %s" % (key, json.dumps(tr[field])))
    lines.append('translation_of: "%s"' % english_url(en_path, fm))
    # The bytes this edition was made from. Not engine provenance -- the one fact a
    # reader of the file needs: which English article, in which state, it renders.
    lines.append('translation_source_bundle_sha256: "%s"' % bundle_sha256(en))
    lines = [x for x in lines if x]
    lines.append("---")
    out.write_text("\n".join(lines) + "\n\n" + tr["article"].strip() + "\n",
                   encoding="utf-8")
    return out


def english_url(path: pathlib.Path, fm: dict) -> str:
    """The URL Jekyll will actually render, which is built from the front-matter `date`
    when there is one -- and there always is here, because publish_best rewrites it to the
    real promotion date, which can differ from the date in the filename."""
    d = fm.get("date")
    if isinstance(d, (datetime.date, datetime.datetime)):
        y, m_, dd = d.year, d.month, d.day
    else:
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(d or path.name))
        if not m:
            return "/"
        y, m_, dd = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return "/%04d/%02d/%02d/%s/" % (y, m_, dd, slug_of(path))


def link_english(en_path: pathlib.Path, lang: str) -> None:
    """Add the forward link to the English article. The only write this stage makes to an
    English file, and it adds no claim: one front-matter field naming the translation."""
    raw = en_path.read_text(encoding="utf-8")
    key = "translation_%s" % lang
    if key in raw.split("---", 2)[1]:
        return
    head, fm, body = raw.split("---", 2)
    url = LANGUAGES[lang]["url_prefix"] + slug_of(en_path) + "/"
    en_path.write_text("%s---%s%s: \"%s\"\n---%s" % (head, fm.rstrip("\n") + "\n", key, url, body),
                       encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--post", required=True)
    ap.add_argument("--lang", default="nl", choices=sorted(LANGUAGES))
    ap.add_argument("--write", action="store_true",
                    help="write the translation into the language collection "
                         "(default is a preview that writes nothing into the repo)")
    ap.add_argument("--out", default="", help="preview directory")
    a = ap.parse_args(argv)

    import claude_cli_provider as CCP
    P = CCP.ClaudeCLIProvider()
    post = pathlib.Path(a.post)
    en = english_bundle(post)
    if en["fields_absent"]:
        print("NOTE: the English article carries no %s -- it predates the packaging "
              "stage. The edition translates the public fields that exist; it does not "
              "invent English packaging, which would enter the world unchecked."
              % ", ".join(en["fields_absent"]))
    tr = translate_bundle(P, en, a.lang)
    fid = fidelity_check(P, en, tr)
    if fid["verdict"] == "HOLD":
        # ONE correction pass, on the named findings only.
        tr = translate_bundle(P, en, a.lang, corrections=fid["findings"], previous=tr)
        fid2 = fidelity_check(P, en, tr)
        fid2["after_correction"] = True
        fid2["first_pass_findings"] = fid["findings"]
        fid = fid2

    out_dir = pathlib.Path(a.out or ("/tmp/translation-%s-%s" % (a.lang, post.stem)))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ENGLISH_BUNDLE.json").write_text(json.dumps(
        {k: v for k, v in en.items() if k != "front_matter"}, indent=1, ensure_ascii=False))
    (out_dir / "TRANSLATED_BUNDLE.json").write_text(json.dumps(
        {k: v for k, v in tr.items() if k != "provider"}, indent=1, ensure_ascii=False))
    (out_dir / "FIDELITY.json").write_text(json.dumps(fid, indent=1, ensure_ascii=False))
    (out_dir / "ARTICLE.md").write_text(tr["article"], encoding="utf-8")

    print("TRANSLATION_FIDELITY: %s%s" % (fid["verdict"],
                                          " (after one correction)" if fid.get("after_correction") else ""))
    for f in fid["findings"]:
        print("  [%s] %s -> %s : %s" % (f.get("category"), str(f.get("english"))[:70],
                                        str(f.get("translated"))[:70],
                                        f.get("what_changed", "")))
    if a.write:
        if fid["verdict"] != "PASS":
            print("refusing to write a held translation")
            return 1
        p = write_translation(a.lang, post, en, tr)
        link_english(post, a.lang)
        print("wrote %s and linked %s" % (p, post))
    else:
        print("preview only -- nothing written into the repository")
    print("artifacts: %s" % out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
