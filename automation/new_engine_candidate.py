#!/usr/bin/env python3
"""
new_engine_candidate.py -- the production adapter that maps NEW_ENGINE_V1's
ACCEPT / HOLD onto real production state.

    HOLD   -> private run evidence only. No candidate. No publication. Deterministic reason.
    ACCEPT -> EDITORIALLY ELIGIBLE CANDIDATE persisted through the normal draft mechanism.

ACCEPT is not "publish now". The periodic selector still decides PUBLISH ONE / PUBLISH
NONE on its own schedule, which this file does not touch.

PUBLICATION-SAFETY INTERLOCK
While cutover preparation is in progress a new-engine candidate must not be publishable,
and that must be true by an EXPLICIT deterministic field rather than by a field happening
to be absent. Every candidate written here carries:

    cutover_rehearsal: true
    publication_eligible: false

`publish_best.py` skips any draft carrying either, before it evaluates anything else.

ENGINE-ERA METADATA
Legacy drafts have none of this, and we do not pretend otherwise. A new-engine candidate
is identifiable at a glance and by machine.

Lives OUTSIDE the new_engine_v1 package on purpose: this is the layer that is allowed to
know about `_drafts/`, so the engine package itself stays provably free of publication
paths.
"""
from __future__ import annotations

import json
import pathlib

ENGINE_GENERATION = "CURRENT_ENGINE"
EDITORIAL_ENGINE = "NEW_ENGINE_V1"
ENGINE_VERSION = "v1.0"

INTERLOCK_FIELDS = ("cutover_rehearsal", "publication_eligible")


def _yaml_scalar(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v).replace('"', '\\"')
    return '"%s"' % s


# ── PUBLIC SOURCES ────────────────────────────────────────────────────────────
# The reader-facing "Go deeper" list, and nothing else. It is a projection of material
# the RESEARCH_PACK already fetched, hashed and kept -- this selects and formats, it does
# not search, rank, score or reach the network, and it has no vote in any gate.
#
# It carries no evidence id, no hash, no run id and no pack internals: those are machine
# identity and a reader has no use for them. An entry that cannot be shown honestly --
# no title, or a URL that is not a plain public http(s) address -- is dropped rather than
# repaired, and a pack that yields nothing clean yields no field at all. There is no
# fallback URL anywhere in here: an invented link would be worse than an absent one.
PUBLIC_SOURCES_MAX = 5

# A fetched page's <title> usually ends in the site's own name -- "... | ArchDaily",
# "... - Francis Marion University". On a page that already prints the publisher beside
# the link, that tail is said twice. Trimming it is typography, not editing: the tail
# comes off ONLY when it is the publisher the entry already carries, so no title can
# lose a word that was telling the reader something.
_TITLE_SEPARATORS = ("|", "-", "\u2013", "\u2014", "\u00b7", "\u2022")


def _squash(s: str) -> str:
    return "".join(c for c in s.lower() if c.isalnum())


def _tidy_title(title: str, publisher: str) -> str:
    pub = _squash(publisher).removeprefix("www.")
    if not pub:
        return title
    for _ in range(2):                      # at most two tails; never a whole title
        for sep in _TITLE_SEPARATORS:
            head, found, tail = title.rpartition(" %s " % sep)
            if not found or not head.strip():
                continue
            t = _squash(tail)
            if t and (t in pub or pub in t):
                title = head.strip()
                break
        else:
            break
    return title


def public_sources(pack_payload: dict | None) -> list:
    """The publishable source list from a frozen RESEARCH_PACK payload, in pack order."""
    out, seen = [], set()
    for src in ((pack_payload or {}).get("sources") or []):
        if not isinstance(src, dict):
            continue
        url = str(src.get("url") or "").strip()
        title = " ".join(str(src.get("title") or "").split())
        if not title or not (url.startswith("http://") or url.startswith("https://")):
            continue
        if url in seen:
            continue
        seen.add(url)
        publisher = " ".join(str(src.get("publisher") or "").split())
        entry = {"title": _tidy_title(title, publisher), "url": url}
        if publisher:
            entry["publisher"] = publisher
        out.append(entry)
        if len(out) >= PUBLIC_SOURCES_MAX:
            break
    return out


def build_frontmatter(*, title: str, author: str, engine_meta: dict,
                      rehearsal: bool = True, safety: dict | None = None,
                      package: dict | None = None, sources: list | None = None) -> str:
    """Frontmatter for a new-engine candidate.

    Deliberately absent: `fact_check_status: verified` and `publication_safety_version`.
    Those are stamps the legacy pipeline earns through its own checks; a new-engine
    candidate has not been through them, so claiming them would be a lie that the
    selector would act on. Their absence already blocks selection -- and the explicit
    interlock fields below block it independently, so exclusion does not rest on absence.
    """
    fields = [
        ("layout", "post"),
        ("title", title),
        ("author", author),
        ("date", engine_meta["generated_at"]),
        # engine era -- legacy drafts carry none of this
        ("engine_generation", ENGINE_GENERATION),
        ("editorial_engine", EDITORIAL_ENGINE),
        ("engine_version", ENGINE_VERSION),
        ("engine_decision", engine_meta["decision"]),
        ("engine_run", engine_meta["run"]),
        ("source_url", engine_meta.get("source_url", "")),
        ("source_sha256", engine_meta["source_sha256"]),
        ("discovery_hash", engine_meta["discovery_hash"]),
        ("article_form_hash", engine_meta["article_form_hash"]),
        ("writer_grounding_status", engine_meta["grounding_status"]),
        ("writer_grounding_unsupported", engine_meta["grounding_unsupported"]),
        ("provider_model", engine_meta.get("provider_model", "")),
    ]
    # THE EDITORIAL PACKAGE. Written by the composition's last stage from the exact bytes
    # that publish, and absent when that stage skipped -- in which case the site falls back
    # to Jekyll's automatic excerpt, which is the article's first paragraph. That fallback
    # is what shipped for the first Story Architecture publication and it is why this field
    # exists: an opening written to be read second is rarely a homepage card.
    #
    # `excerpt` is the field the templates already consume (index.html, the author and
    # archive layouts, and every description meta tag). The other three are recorded
    # beside it: `dek` renders as the article's standfirst, and the last two are handed
    # to whatever posts the piece.
    pkg = {k: str(v).strip() for k, v in (package or {}).items() if str(v or "").strip()}
    for k in ("excerpt", "dek", "meta_description", "social_hook"):
        src = "homepage_excerpt" if k == "excerpt" else k
        if pkg.get(src):
            fields.append((k, pkg[src]))
    # Publication-safety stamp from the CURRENT_ENGINE bridge, when it granted
    # eligibility. Absent stamp => not eligible. A rehearsal candidate is NEVER
    # eligible regardless of what the bridge said.
    stamp = dict(safety or {})
    if rehearsal:
        stamp = {"publication_eligible": False,
                 "publication_safety_profile": stamp.get("publication_safety_profile",
                                                         "CURRENT_ENGINE_V1")}
    fields += [("cutover_rehearsal", bool(rehearsal))]
    if "publication_eligible" not in stamp:
        stamp["publication_eligible"] = False
    fields += sorted(stamp.items())
    lines = ["---"]
    lines += ["%s: %s" % (k, _yaml_scalar(v)) for k, v in fields]
    # The reader-facing source list, last, because it is the only block field here.
    # Absent entirely when there is nothing clean to show.
    for i, src in enumerate(sources or []):
        if i == 0:
            lines.append("sources:")
        lines.append("  - title: %s" % _yaml_scalar(src["title"]))
        lines.append("    url: %s" % _yaml_scalar(src["url"]))
        if src.get("publisher"):
            lines.append("    publisher: %s" % _yaml_scalar(src["publisher"]))
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def persist_candidate(*, drafts_dir: pathlib.Path, slug: str, body: str,
                      title: str, author: str, engine_meta: dict,
                      rehearsal: bool = True, safety: dict | None = None,
                      package: dict | None = None,
                      sources: list | None = None) -> pathlib.Path:
    """Write ONE accepted candidate into the normal draft location. No git, no publish."""
    drafts_dir.mkdir(parents=True, exist_ok=True)
    path = drafts_dir / ("%s-%s.md" % (engine_meta["generated_at"][:10], slug))
    path.write_text(build_frontmatter(title=title, author=author,
                                      engine_meta=engine_meta, rehearsal=rehearsal,
                                      safety=safety, package=package, sources=sources)
                    + body.rstrip() + "\n", encoding="utf-8")
    return path


def engine_meta_from_run(out: dict, *, run: str, generated_at: str,
                         source_url: str = "", provider_model: str = "") -> dict:
    """Collect the engine-era metadata from a finished runner result."""
    A = out["artifacts"]
    gf = A["GROUNDING_FINDINGS"].payload if "GROUNDING_FINDINGS" in A else {}
    unsupported = len([f for f in gf.get("findings", [])
                       if f.get("classification") == "TRUE_UNSUPPORTED"])
    return {
        "run": run,
        "generated_at": generated_at,
        "decision": out["decision"],
        "source_url": source_url,
        "source_sha256": A["SOURCE_SNAPSHOT"].payload["source_sha256"],
        "discovery_hash": A["DISCOVERY"].content_hash() if "DISCOVERY" in A else "",
        "article_form_hash": A["ARTICLE_FORM"].content_hash() if "ARTICLE_FORM" in A else "",
        "grounding_status": gf.get("status", "absent"),
        "grounding_unsupported": unsupported,
        "provider_model": provider_model,
    }


def final_body(out: dict) -> str:
    """The candidate body: the grounded output, i.e. the repaired text when a
    patch-only repair ran, otherwise the writer's own output."""
    A = out["artifacts"]
    if "GROUNDING_REPAIR" in A:
        return A["GROUNDING_REPAIR"].payload["article_text"]
    return A["WRITER_OUTPUT"].payload["article_text"]
