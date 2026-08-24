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


def build_frontmatter(*, title: str, author: str, engine_meta: dict,
                      rehearsal: bool = True) -> str:
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
        # explicit publication interlock
        ("cutover_rehearsal", bool(rehearsal)),
        ("publication_eligible", False),
    ]
    lines = ["---"]
    lines += ["%s: %s" % (k, _yaml_scalar(v)) for k, v in fields]
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def persist_candidate(*, drafts_dir: pathlib.Path, slug: str, body: str,
                      title: str, author: str, engine_meta: dict,
                      rehearsal: bool = True) -> pathlib.Path:
    """Write ONE accepted candidate into the normal draft location. No git, no publish."""
    drafts_dir.mkdir(parents=True, exist_ok=True)
    path = drafts_dir / ("%s-%s.md" % (engine_meta["generated_at"][:10], slug))
    path.write_text(build_frontmatter(title=title, author=author,
                                      engine_meta=engine_meta, rehearsal=rehearsal)
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
