"""
arms.py -- the three variants, run from one frozen subject.

  A  CURRENT EDITING     the production Continuity + Prose Finish behaviour, reached
                         through the production functions themselves
  B  ONE GUARDED EDIT    the bounded, reversible patch editor, on EXACTLY the same
                         Writer draft bytes as A
  C  PLAN + GUARDED EDIT Codex reviews the evidence and improves the plan; the SAME
                         incumbent Claude Writer drafts it; the SAME guarded editor runs

A AND B SHARE ONE WRITER CALL, and that is the point of the design. Section 11 asks what
editing does to a draft, so both arms must start from identical prose; generating two
drafts would confound the editing comparison with Writer variance and would cost six
extra subscription calls to do it. C necessarily draws a second draft, because a
different plan is the thing being tested -- which is why section 13 warns that B vs C is
an exploration of a strategy, not a controlled attribution, and why this module records
`shared_pre_edit_sha256` so the A/B comparison can be proved to be controlled and the
B/C comparison can be proved not to be.

WHAT IS REUSED RATHER THAN REBUILT. The Writer is `composition.write_article`, on the
production Writer contract. Continuity is `composition.continuity_pass` and Prose Finish
is `composition.prose_finish`, called directly, with the run's own discard rules
reproduced here from `run_story_architecture_composition` -- not softened, and not
replaced by a local reimplementation of what production already does correctly.

NOTHING HERE PUBLISHES. Every variant is written under the experiment root with
NOT_PUBLISHABLE_EXPERIMENT on it. No candidate is persisted to _posts/, _drafts/, _nl/
or _social/, no publication bridge is called, and no production database is touched.
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
AUTOMATION = HERE.parent
if str(AUTOMATION) not in sys.path:
    sys.path.insert(0, str(AUTOMATION))

from new_engine_v1 import composition as CP                        # noqa: E402
from new_engine_v1 import continuity as CE                         # noqa: E402
from evidence_to_draft_pilot import guarded_editor as GE           # noqa: E402

NOT_PUBLISHABLE = "NOT_PUBLISHABLE_EXPERIMENT"


def write_draft(claude_provider, arch: dict, ledger: dict) -> dict:
    """The incumbent Writer, on the production contract. One call (its own internal
    retry only fires when the reply is mechanically unusable)."""
    cut = CP.derive_cut_watch_terms(arch, ledger)
    wr = CP.write_article(claude_provider, arch, ledger, cut.get("prohibitions"))
    wr["cut"] = cut
    return wr


def arm_a_current_editing(claude_provider, wr: dict, arch: dict) -> dict:
    """Production Continuity + Prose Finish, including production's discard rules.

    Reproduced from `run_story_architecture_composition`: a Continuity edit whose
    semantic delta is dirty is DISCARDED WHOLE and the Writer draft carries on; an
    applied Prose Finish resets the negative lineage to the Writer's own.
    """
    draft = wr["article_text"]
    out = {"arm": "A", "pre_edit_sha256": CP.C.sha256_text(draft), "model_calls": 0}

    cont = CP.continuity_pass(claude_provider, draft, arch)
    out["model_calls"] += cont.get("model_calls", 0)
    delta_errs = cont["semantic_delta_errors"]
    if delta_errs:
        final = draft
        out["continuity"] = {"applied": False, "discarded": True,
                             "discard_reason": delta_errs,
                             "edits": len(cont.get("edits") or [])}
    else:
        final = cont["article_text"]
        out["continuity"] = {"applied": True, "discarded": False,
                             "edits": len(cont.get("edits") or []),
                             "deletes": cont.get("deletes")}
    out["after_continuity_sha256"] = CP.C.sha256_text(final)

    pf = CP.prose_finish(claude_provider, final, arch)
    out["model_calls"] += pf.get("model_calls", 0)
    if pf.get("applied"):
        out["prose_finish"] = {"applied": True}
        final = pf["article_text"]
    else:
        out["prose_finish"] = {"applied": False, "reason": pf.get("reason")}

    out["article_text"] = final
    out["article_sha256"] = CP.C.sha256_text(final)
    out["words"] = len(final.split())
    out["not_publishable"] = NOT_PUBLISHABLE
    return out


def arm_b_guarded_edit(claude_provider, wr: dict) -> dict:
    """ONE guarded edit, on the SAME bytes arm A started from."""
    draft = wr["article_text"]
    g = GE.guarded_edit(claude_provider, draft)
    return {
        "arm": "B",
        "pre_edit_sha256": CP.C.sha256_text(draft),
        "model_calls": g["model_calls"],
        "editor": {k: g[k] for k in (
            "status", "accepted", "proposed", "accepted_patches", "rejected_patches",
            "combined_delta_errors", "parse_errors", "resolves_nothing")},
        "article_text": g["article_text"],
        "article_sha256": CP.C.sha256_text(g["article_text"]),
        "words": len(g["article_text"].split()),
        "not_publishable": NOT_PUBLISHABLE,
    }


def arm_c_planned(claude_provider, plan_cell: dict, ledger: dict) -> dict:
    """The Writer on Codex's improved plan, then the SAME guarded editor."""
    out = {"arm": "C", "model_calls": 0,
           "planner_status": plan_cell.get("status")}
    if plan_cell.get("status") != "PASS":
        # A plan that did not validate, or an honest NO_SUPPORTED_PLAN, produces no
        # article. Reported in the completion denominator, never as a silent skip.
        out["status"] = plan_cell.get("status")
        out["article_text"] = None
        out["not_publishable"] = NOT_PUBLISHABLE
        return out

    arch = plan_cell["architecture"]
    wr = write_draft(claude_provider, arch, ledger)
    out["model_calls"] += wr.get("model_calls", 0)
    draft = wr["article_text"]
    out["pre_edit_sha256"] = CP.C.sha256_text(draft)
    out["pre_edit_words"] = len(draft.split())

    g = GE.guarded_edit(claude_provider, draft)
    out["model_calls"] += g["model_calls"]
    out["editor"] = {k: g[k] for k in (
        "status", "accepted", "proposed", "accepted_patches", "rejected_patches",
        "combined_delta_errors", "parse_errors", "resolves_nothing")}
    out["status"] = "PASS"
    out["article_text"] = g["article_text"]
    out["article_sha256"] = CP.C.sha256_text(g["article_text"])
    out["words"] = len(g["article_text"].split())
    out["writer_packet"] = wr["packet"]
    out["cut"] = wr["cut"]
    out["negative_lineage_verified"] = wr["negative_lineage_verified"]
    out["not_publishable"] = NOT_PUBLISHABLE
    return out


def deterministic_checks(*, variant_text: str, draft_text: str, packet: dict,
                         arch: dict, ledger: dict, cut: dict, lineage) -> dict:
    """The deterministic validators, applied IDENTICALLY to every variant (section 17).

    This is `composition.safety_audit` -- the production post-writer audit, which takes
    no provider and makes no model call -- plus the production semantic-delta reading of
    the variant against the draft it came from.

    WHAT THIS IS NOT. It is not the full canonical factual tail: the Grounder, the
    authoritative Fact Check, the Claim Mapper and the Reader gate all cost model calls
    and are not run here. Section 17 is explicit that a partial evaluation may never be
    called ALL_GATES_PASS, so the result names exactly which checks ran and nothing
    aggregates them into a publication verdict.
    """
    out = {"checks_run": ["composition.safety_audit", "continuity.semantic_delta"],
           "checks_not_run": ["grounding", "authoritative fact check", "claim mapper",
                              "reader gate", "editorial package"],
           "is_not_a_publication_verdict": True}
    try:
        sa = CP.safety_audit(draft_text, variant_text, packet, arch, ledger,
                             cut["terms"], cut, lineage, package=None)
        out["safety_audit"] = {
            "blocking": [str(f)[:300] for f in (sa.get("blocking") or [])],
            "advisories": [str(a)[:200] for a in (sa.get("advisories") or [])],
            "blocking_count": len(sa.get("blocking") or []),
        }
    except Exception as exc:                                       # noqa: BLE001
        out["safety_audit_error"] = str(exc)[:300]
    out["semantic_delta_vs_draft"] = CE.semantic_delta(draft_text, variant_text)
    out["semantic_delta_errors_vs_draft"] = CE.validate_semantic_delta(
        draft_text, variant_text)
    return out
