#!/usr/bin/env python3
"""
publication_audit_test.py -- the retention contract, proved rather than described.

Bounded and offline: one synthetic run directory, one synthetic published article, no
provider, no network, no repo mutation. What it proves is the whole point of issue #91 --
that the retained bundle survives deletion of the run workspace and still lets the
authoritative Safety function run to the same verdict.

USAGE: python3 automation/publication_audit_test.py
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import publication_audit as PA                                       # noqa: E402
from new_engine_v1 import composition as CP                          # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    print("%s  %s%s" % ("PASS" if cond else "FAIL", name,
                        "" if cond else "  -- %s" % detail))
    if not cond:
        FAILURES.append(name)


DRAFT = "The pavilion stands on six columns.\n\nWater passes beneath it.\n"
FINAL = "The pavilion stands on six columns.\n\nWater passes beneath it.\n"

LEDGER = {"F1": {"fact_id": "F1", "proposition": "The pavilion stands on six columns.",
                 "support_span": "six columns", "source_id": "S1"}}
ARCH = {"article_type": "field_note", "story_spine": "a pavilion above the forest floor",
        "opening_object_or_event": "six columns", "reader_initial_state": "unfamiliar",
        "beats": [{"beat_id": "B1", "happens": "the pavilion is described",
                   "concrete_carrier": "six columns", "facts_allowed": ["F1"],
                   "concept_introduced": "", "must_not_say_yet": ""}],
        "turn": "", "crip_turn": "", "ending_move": "", "use_facts": ["F1"],
        "definitions": {}, "prohibitions": []}
CUT_REPORT = {"terms": {}, "prohibitions": [], "cut_without_distinctive_terms": []}
PACKET = {"article_type": "field_note", "story_spine": ARCH["story_spine"],
          "opening": "six columns", "reader_initial_state": "unfamiliar",
          "beats": [{"beat_id": "B1", "happens": "the pavilion is described",
                     "carrier": "six columns", "facts": [LEDGER["F1"]],
                     "concept": "", "withhold": ""}],
          "turn": "", "crip_turn": "", "lens": "", "ending_move": "",
          "facts": [LEDGER["F1"]], "quotes": [], "definitions": {}, "prohibitions": []}

POST = """---
layout: "post"
title: "A pavilion on six columns"
author: "Maya Flux"
date: 2026-09-06
engine_generation: "CURRENT_ENGINE"
editorial_engine: "NEW_ENGINE_V1"
engine_version: "v1.0"
engine_decision: "ACCEPT"
engine_run: "production-20260906T000000Z-deadbeef"
source_url: "https://example.invalid/pavilion"
source_sha256: "%s"
provider_model: "claude-opus-5"
fact_check_status: "verified"
fact_check_extraction_status: "ok"
fact_check_claims_extracted: 2
publication_eligible: true
publication_safety_version: 1
dek: "Six columns, and the water goes under."
excerpt: "A pavilion above the forest floor."
sources:
  - title: "Example"
    url: "https://example.invalid/pavilion"
    publisher: "example.invalid"
---

The pavilion stands on six columns.

Water passes beneath it.
""" % ("0" * 64)

RUN_ID = "production-20260906T000000Z-deadbeef"


def build_run(root: pathlib.Path) -> pathlib.Path:
    d = root / RUN_ID
    d.mkdir(parents=True)

    def j(name, obj):
        (d / name).write_text(json.dumps(obj, indent=1, sort_keys=True, default=str))

    j("WRITER_PACKET.json", PACKET)
    j("ARCHITECTURE.json", ARCH)
    j("LEDGER.json", LEDGER)
    j("CUT_REPORT.json", CUT_REPORT)
    j("NEGATIVE_LINEAGE.json", {})
    j("SAFETY_AUDIT.json", {"blocking": [], "audits": {}})
    j("SAFETY_REPLAY.json", {"function": "new_engine_v1.composition.safety_audit",
                             "deterministic": True})
    j("RESEARCH_PACK.json", {"stage": "RESEARCH_PACK", "payload": {"subject": "pavilion"}})
    j("SOURCE_SNAPSHOT.json", {"stage": "SOURCE_SNAPSHOT"})
    j("GROUNDING_FINDINGS.json", {"status": "settled", "findings": []})
    j("FACT_CHECK.json", {"findings": []})
    (d / "WRITER_DRAFT.md").write_text(DRAFT)
    (d / "ARTICLE_FINAL.md").write_text(FINAL)
    (d / "WRITER_PACKET.txt").write_text("rendered prompt, not a packet")
    return d


def run_safety_from(bundle: pathlib.Path) -> dict:
    """The authoritative function, called with nothing but retained bytes."""
    r = bundle / "run"
    load = lambda n: json.loads((r / n).read_text())          # noqa: E731
    cut = load("CUT_REPORT.json")
    return CP.safety_audit(
        (r / "WRITER_DRAFT.md").read_text(), (r / "ARTICLE_FINAL.md").read_text(),
        load("WRITER_PACKET.json"), load("ARCHITECTURE.json"), load("LEDGER.json"),
        cut["terms"], cut, load("NEGATIVE_LINEAGE.json"))


def promotion_boundary() -> None:
    """The real publisher, driven end to end over a temp repo.

    Proves the two behaviours that matter at the boundary: a draft whose run is intact
    is promoted AND retained in one step, and a draft whose run is gone is held in
    _drafts/ rather than published unauditable.
    """
    import types
    import publish_best as PB

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="pubboundary-"))
    saved = (PB.REPO, PB.DRAFTS, PB.POSTS, PB.ARCHIVE, PB.subprocess)
    fake_images = types.ModuleType("gen_images")
    fake_images.has_image_field = lambda _t: True
    fake_images.illustrate_post = lambda _p: {"ok": True, "assets": [], "figures": 0}
    sys.modules["gen_images"] = fake_images
    try:
        ev = tmp / "evidence"
        build_run(ev)
        store = tmp / "store"
        PB.REPO = tmp
        PB.DRAFTS = tmp / "_drafts"
        PB.POSTS = tmp / "_posts"
        PB.ARCHIVE = PB.DRAFTS / "_archive"
        PB.DRAFTS.mkdir()
        PB.POSTS.mkdir()
        PB.subprocess = types.SimpleNamespace(
            run=lambda *a, **k: types.SimpleNamespace(returncode=0),
            CalledProcessError=Exception)
        os_environ_restore = dict(os.environ)
        os.environ["NEW_ENGINE_EVIDENCE_ROOT"] = str(ev)
        os.environ["CRIPMINDS_PUBLICATION_AUDIT_ROOT"] = str(store)

        draft = PB.DRAFTS / "2026-09-06-a-pavilion-on-six-columns.md"
        draft.write_text(POST)
        check("publish_best promoted the draft", PB.main() == 0)
        promoted = PB.POSTS / draft.name
        check("the article is in _posts", promoted.is_file())
        check("a bundle was retained at the boundary",
              (store / draft.stem / "PUBLICATION.json").is_file())
        check("the promoted article points at it",
              PA.read_post(promoted)[0].get("audit_bundle") == draft.stem)

        # And now the run is gone before the next cycle.
        shutil.rmtree(ev)
        draft2 = PB.DRAFTS / "2026-09-06-a-second-pavilion.md"
        draft2.write_text(POST.replace("A pavilion on six columns", "A second pavilion"))
        rc = PB.main()
        check("a draft whose run has vanished is not published", rc == 0)
        check("it stays in _drafts, unarchived", draft2.is_file())
        check("and never reached _posts", not (PB.POSTS / draft2.name).exists())
        check("its bytes were not rewritten",
              draft2.read_text() == POST.replace("A pavilion on six columns",
                                                 "A second pavilion"))
        os.environ.clear()
        os.environ.update(os_environ_restore)
    finally:
        PB.REPO, PB.DRAFTS, PB.POSTS, PB.ARCHIVE, PB.subprocess = saved
        sys.modules.pop("gen_images", None)
        for q in sorted(tmp.rglob("*"), reverse=True):
            try:
                q.chmod(0o700)
            except OSError:
                pass
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="pubaudit-"))
    try:
        ev, audit_root = tmp / "evidence", tmp / "store"
        run_dir = build_run(ev)
        post = tmp / "_posts" / "2026-09-06-a-pavilion-on-six-columns.md"
        post.parent.mkdir(parents=True)
        post.write_text(POST)

        # ── the gate ────────────────────────────────────────────────────────────
        fm, _ = PA.read_post(post)
        ok, why = PA.retention_feasible(fm, roots=[ev])
        check("a modern draft with a complete run is retainable", ok, why)
        ok2, why2 = PA.retention_feasible(dict(fm, engine_run=""), roots=[ev])
        check("a CURRENT_ENGINE article with no engine_run is refused", not ok2, why2)
        ok3, _ = PA.retention_feasible({"title": "legacy"}, roots=[ev])
        check("a legacy article is NOT blocked and no run is invented", ok3)
        # RETENTION FEASIBILITY IS NOT STAGE-SCHEMA COMPLETENESS (corrected 2026-09-07).
        # This assertion used to read "a run missing the packet DICT is REFUSED". That
        # doctrine was wrong and it was total: no recorded production run has ever
        # carried WRITER_PACKET.json, CUT_REPORT.json and ARTICLE_FINAL.md, so the gate
        # refused every CURRENT_ENGINE candidate that reached it and 13 scheduled runs
        # produced 0 publications. The run is retainable; what the missing file costs is
        # deterministic Safety REPLAY, and the manifest is required to say so plainly
        # rather than the publisher pretending the article does not exist.
        (run_dir / "WRITER_PACKET.json").unlink()
        ok4, why4 = PA.retention_feasible(fm, roots=[ev])
        check("a run missing one composition-engine Safety file is still retainable",
              ok4, why4)
        check("and feasibility says which replay input is absent",
              "WRITER_PACKET.json" in why4 and "INCOMPLETE" in why4, why4)
        check("the .txt still does not count as the packet",
              "WRITER_PACKET.json" in PA.missing_safety_inputs(run_dir)
              and (run_dir / "WRITER_PACKET.txt").is_file())
        check("that run's SAFETY replay is declared INCOMPLETE, not replayable",
              PA._reaudit_report(run_dir)["SAFETY"]["kind"] == "INCOMPLETE"
              and PA._reaudit_report(run_dir)["SAFETY"]["possible"] is False)
        (run_dir / "WRITER_PACKET.json").write_text(
            json.dumps(PACKET, indent=1, sort_keys=True))

        # ── retention ───────────────────────────────────────────────────────────
        before = PA.published_bundle_sha256(post)
        body_before = PA.read_post(post)[1]
        man = PA.retain(post, audit_root=audit_root, roots=[ev])
        bundle = audit_root / man["bundle_id"]
        check("the bundle exists", bundle.is_dir())
        check("it holds the published bytes", (bundle / "PUBLISHED.md").is_file())
        check("it holds a verbatim run copy", (bundle / "run" / "ARCHITECTURE.json").is_file())
        check("safety re-audit is declared DETERMINISTIC_REPLAY",
              man["reaudit"]["SAFETY"]["kind"] == "DETERMINISTIC_REPLAY")
        check("grounding is NOT declared replayable",
              man["reaudit"]["GROUNDING"]["kind"] == "INPUTS_AND_RESULT_PRESERVED")
        check("fact check is NOT declared replayable",
              man["reaudit"]["FACT_CHECK"]["kind"] == "INPUTS_AND_RESULT_PRESERVED")
        check("no secret was retained", man["secret_scan"]["hits"] == [])
        check("the binding is the published bundle hash",
              man["binding"]["published_bundle_sha256"] == before)

        # ── the pointer, and that stamping it did not move the binding ──────────
        fm2, _ = PA.read_post(post)
        check("the article names its bundle", fm2.get("audit_bundle") == man["bundle_id"])
        check("stamping the pointer did not change the binding",
              PA.published_bundle_sha256(post) == before)
        check("stamping rewrote no article prose", PA.read_post(post)[1] == body_before)

        # ── the whole point: survive the run workspace ──────────────────────────
        expected = run_safety_from(bundle)
        shutil.rmtree(ev)
        check("the ephemeral run directory is gone", not ev.exists())
        res = PA.verify(post, audit_root=audit_root)
        check("the article still resolves to its bundle after the run is deleted",
              res["ok"], res.get("problems"))
        replayed = run_safety_from(bundle)
        check("SAFETY re-runs from the retained bundle alone",
              replayed["status"] == expected["status"])
        check("and reaches the identical verdict",
              json.dumps(replayed, sort_keys=True, default=str)
              == json.dumps(expected, sort_keys=True, default=str))

        # ── immutability and tamper detection ───────────────────────────────────
        f = bundle / "run" / "ARCHITECTURE.json"
        check("retained files are read-only", not (f.stat().st_mode & 0o222))
        f.chmod(0o644)
        f.write_text(json.dumps({"tampered": True}))
        bad = PA.verify(post, audit_root=audit_root)
        check("an altered bundle fails verification", not bad["ok"], bad["problems"])
        f.chmod(0o444)

        # ── an edited article no longer matches its bundle ──────────────────────
        post.write_text(post.read_text().replace("six columns", "seven columns"))
        drift = PA.verify(post, audit_root=audit_root)
        check("an edited published article is reported as drifted", not drift["ok"],
              drift["problems"])

        # ── classification cannot be defeated by dropping one line ──────────────
        check("a stripped engine_generation does not downgrade a modern article",
              PA.is_current_engine({"editorial_engine": "NEW_ENGINE_V1"})
              and PA.is_current_engine({"engine_run": "production-x"}))
        check("a genuinely legacy article is still legacy",
              not PA.is_current_engine({"title": "t", "author": "a"}))
        stripped = dict(fm)
        stripped.pop("engine_generation")
        stripped["engine_run"] = ""
        okS, whyS = PA.retention_feasible(stripped, roots=[ev])
        check("an article claiming NEW_ENGINE_V1 with no run is still refused",
              not okS, whyS)

        # ── a bundle whose pointer cannot be written is withdrawn ───────────────
        ev2 = tmp / "evidence2"
        build_run(ev2)
        post2 = tmp / "_posts" / "2026-09-06-a-third-pavilion.md"
        post2.write_text(POST.replace("A pavilion on six columns", "A third pavilion"))
        real_stamp = PA._stamp
        PA._stamp = lambda *_a, **_k: (_ for _ in ()).throw(OSError("disk full"))
        try:
            PA.retain(post2, audit_root=audit_root, roots=[ev2])
            check("a failed stamp aborts the retention", False, "it returned")
        except OSError:
            check("a failed stamp aborts the retention", True)
        finally:
            PA._stamp = real_stamp
        check("and the orphan bundle was withdrawn, not left to block the next attempt",
              not (audit_root / post2.stem).exists())
        check("so the same publication can be retained cleanly afterwards",
              PA.retain(post2, audit_root=audit_root,
                        roots=[ev2])["bundle_id"] == post2.stem)

        # ── refusing to overwrite ───────────────────────────────────────────────
        try:
            PA.retain(post, audit_root=audit_root, roots=[ev])
            check("a second retain is refused", False, "it was allowed")
        except PA.RetentionError:
            check("a second retain is refused", True)
    finally:
        for p in sorted(tmp.rglob("*"), reverse=True):
            try:
                p.chmod(0o700)
            except OSError:
                pass
        shutil.rmtree(tmp, ignore_errors=True)

    promotion_boundary()

    print("\n%d check(s) failed" % len(FAILURES) if FAILURES else "\nall checks passed")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
