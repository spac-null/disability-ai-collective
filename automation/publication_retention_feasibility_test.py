#!/usr/bin/env python3
"""
publication_retention_feasibility_test.py -- promotion asks whether the exact run can
be KEPT, not whether it used one engine's filenames.

THE INCIDENT (2026-09-07). Thirteen scheduled CURRENT_ENGINE runs produced zero
committed publications. Part of the reason was a precondition that nothing could ever
satisfy: `retention_feasible` refused any article whose run lacked all six files in
`SAFETY_REQUIRED`. Across every recorded production-* run, WRITER_PACKET.json,
CUT_REPORT.json and ARTICLE_FINAL.md were emitted by NONE. So an article carrying
engine_decision ACCEPT, publication_eligible true and fact_check_status verified was
held with NEEDS_AUDIT_RETENTION on a checklist describing a composition engine it had
not been written by.

WHAT THESE TESTS FIX IN PLACE. Feasibility now means: this article names a run, that
EXACT run resolves, and the retention mechanism could genuinely copy, hash and freeze
it. Everything that made retention worth having is still proved here -- exact-run
identity, no borrowing, the manifest, the hash inventory, the freeze, and an honest
INCOMPLETE verdict when deterministic Safety replay is not possible.

Offline. One temp evidence root, one temp store, no provider, no network, no repo.

USAGE: python3 automation/publication_retention_feasibility_test.py
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import stat
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import publication_audit as PA                                       # noqa: E402
import publication_audit_test as PAT                                 # noqa: E402

FAILURES: list = []


def check(name, cond, detail=""):
    print("%s  %s%s" % ("PASS" if cond else "FAIL", name,
                        "" if cond else "  -- %s" % str(detail)[:240]))
    if not cond:
        FAILURES.append(name)


# The shape a REAL production-* run has actually had on disk: an acquisition record, the
# bridge and fact-check results, the grounding findings, the research pack and source
# snapshot, the candidate pointer. No WRITER_PACKET.json, no CUT_REPORT.json, no
# ARTICLE_FINAL.md -- not because they were deleted, but because the engine that wrote
# this run never emitted them.
def build_legacy_composition_run(root: pathlib.Path, run_id: str) -> pathlib.Path:
    d = root / run_id
    d.mkdir(parents=True)

    def j(name, obj):
        (d / name).write_text(json.dumps(obj, indent=1, sort_keys=True), encoding="utf-8")

    j("ACQUISITION.json", {"url": "https://example.invalid/pavilion"})
    j("SAFETY_BRIDGE.json", {"eligible": True})
    j("FACT_CHECK.json", {"findings": []})
    j("GROUNDING_FINDINGS.json", {"status": "settled", "findings": []})
    j("RESEARCH_PACK.json", {"stage": "RESEARCH_PACK", "payload": {"subject": "pavilion"}})
    j("SOURCE_SNAPSHOT.json", {"stage": "SOURCE_SNAPSHOT"})
    j("ARCHITECTURE.json", PAT.ARCH)
    j("LEDGER.json", PAT.LEDGER)
    j("CANDIDATE.json", {"path": "_drafts/x.md"})
    (d / "WRITER_DRAFT.md").write_text(PAT.DRAFT, encoding="utf-8")
    return d


def post_at(dirpath: pathlib.Path, name: str, run_id: str) -> pathlib.Path:
    p = dirpath / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(PAT.POST.replace(PAT.RUN_ID, run_id), encoding="utf-8")
    return p


# ── 1. the impossible checklist no longer refuses a real run ────────────────────────
def test_accepted_article_on_a_legacy_composition_run_is_feasible(tmp):
    ev = tmp / "ev1"
    rid = "production-20260901T090000Z-aaaaaaaa"
    run = build_legacy_composition_run(ev, rid)
    fm, _ = PA.read_post(post_at(tmp / "_posts", "2026-09-01-one.md", rid))

    check("the fixture really is an ACCEPT + eligible + verified article",
          fm.get("engine_decision") == "ACCEPT"
          and fm.get("publication_eligible") is True
          and fm.get("fact_check_status") == "verified", fm.get("engine_decision"))
    missing = PA.missing_safety_inputs(run)
    check("the fixture really lacks the Story-Architecture filenames",
          {"WRITER_PACKET.json", "CUT_REPORT.json", "ARTICLE_FINAL.md"} <= set(missing),
          missing)

    ok, why = PA.retention_feasible(fm, roots=[ev])
    check("it is feasible to retain -- publication is not refused for the checklist",
          ok, why)
    check("the reason names what replay will lack rather than hiding it",
          "INCOMPLETE" in why and "WRITER_PACKET.json" in why, why)


# ── 2. fail-closed is intact ────────────────────────────────────────────────────────
def test_unresolvable_or_unusable_runs_still_fail_closed(tmp):
    ev = tmp / "ev2"
    rid = "production-20260902T090000Z-bbbbbbbb"
    build_legacy_composition_run(ev, rid)
    fm, _ = PA.read_post(post_at(tmp / "_posts", "2026-09-02-two.md", rid))

    ok, why = PA.retention_feasible(dict(fm, engine_run="production-does-not-exist"),
                                    roots=[ev])
    check("a run id that resolves to nothing is refused", not ok, why)

    ok, why = PA.retention_feasible(dict(fm, engine_run=""), roots=[ev])
    check("a CURRENT_ENGINE article naming no run at all is refused", not ok, why)

    empty = ev / "production-20260902T090000Z-empty"
    empty.mkdir()
    ok, why = PA.retention_feasible(dict(fm, engine_run=empty.name), roots=[ev])
    check("a run directory holding nothing is refused -- there is nothing to keep",
          not ok, why)

    # A directory that exists and has content but cannot be read is the one case where
    # "the run is there" and "the run can be retained" genuinely differ.
    locked = build_legacy_composition_run(ev, "production-20260902T090000Z-locked")
    (locked / "LEDGER.json").chmod(0)
    try:
        ok, why = PA.retention_feasible(dict(fm, engine_run=locked.name), roots=[ev])
        check("a run whose bytes cannot be read is refused, not optimistically passed",
              not ok, why)
    finally:
        (locked / "LEDGER.json").chmod(0o644)

    ok, _ = PA.retention_feasible({"title": "a hand-written article"}, roots=[ev])
    check("a legacy/manual article is still not blocked and no run is invented", ok)


# ── 3. exact-run identity: nothing is ever borrowed ─────────────────────────────────
def test_retention_never_borrows_another_run(tmp):
    ev = tmp / "ev3"
    older = build_legacy_composition_run(ev, "production-20260801T090000Z-cccccccc")
    newer = build_legacy_composition_run(ev, "production-20260906T090000Z-dddddddd")
    (newer / "MARKER-NEWEST.json").write_text("{}", encoding="utf-8")
    (older / "MARKER-OLDEST.json").write_text("{}", encoding="utf-8")

    fm, _ = PA.read_post(post_at(tmp / "_posts", "2026-09-03-three.md",
                                 "production-20260903T090000Z-eeeeeeee"))
    ok, why = PA.retention_feasible(fm, roots=[ev])
    check("an article whose own run is absent is refused even though other runs exist",
          not ok, why)
    check("and the refusal names the run the ARTICLE claims, not a substitute",
          "production-20260903T090000Z-eeeeeeee" in why, why)
    check("find_run_dir returns nothing rather than the newest run",
          PA.find_run_dir("production-20260903T090000Z-eeeeeeee", [ev]) is None)

    # And when the exact run IS present, the bundle copies THAT one.
    exact = build_legacy_composition_run(ev, "production-20260903T090000Z-eeeeeeee")
    (exact / "MARKER-EXACT.json").write_text("{}", encoding="utf-8")
    store = tmp / "store3"
    post = post_at(tmp / "_posts", "2026-09-03-three.md",
                   "production-20260903T090000Z-eeeeeeee")
    man = PA.retain(post, audit_root=store, roots=[ev])
    bundle = store / man["bundle_id"]
    check("the retained run is the article's own",
          (bundle / "run" / "MARKER-EXACT.json").is_file())
    check("and neither of the other runs leaked into it",
          not (bundle / "run" / "MARKER-NEWEST.json").exists()
          and not (bundle / "run" / "MARKER-OLDEST.json").exists())
    check("the manifest records where that exact run came from",
          man["provenance"]["run_dir_origin"] == str(exact),
          man["provenance"]["run_dir_origin"])


# ── 4. the retention operation itself is unchanged ──────────────────────────────────
def test_manifest_hashing_and_freeze_are_unchanged(tmp):
    ev = tmp / "ev4"
    rid = "production-20260904T090000Z-ffffffff"
    run = build_legacy_composition_run(ev, rid)
    store = tmp / "store4"
    post = post_at(tmp / "_posts", "2026-09-04-four.md", rid)
    before = PA.published_bundle_sha256(post)

    man = PA.retain(post, audit_root=store, roots=[ev])
    bundle = store / man["bundle_id"]

    check("the bundle exists and holds the published bytes",
          (bundle / "PUBLISHED.md").is_file() and (bundle / "PUBLICATION.json").is_file())
    check("the run was copied verbatim",
          (bundle / "run" / "ARCHITECTURE.json").is_file()
          and (bundle / "run" / "WRITER_DRAFT.md").read_text() == PAT.DRAFT)

    # Hash inventory: every retained file, hashed, and the roll-up over it.
    live = PA._inventory(bundle, "run")
    check("every retained run file is in the manifest inventory with its own sha256",
          live == man["files"] and len(live) == len(list(
              p for p in (bundle / "run").rglob("*") if p.is_file())), len(live))
    rollup = PA.sha256_bytes(json.dumps(man["files"], sort_keys=True).encode("utf-8"))
    check("audit_bundle_sha256 is the roll-up of that inventory",
          rollup == man["binding"]["audit_bundle_sha256"])
    check("the binding is the published bundle hash taken before stamping",
          man["binding"]["published_bundle_sha256"] == before)

    # Freeze.
    modes = [stat.S_IMODE(p.stat().st_mode) for p in bundle.rglob("*") if p.is_file()]
    check("every retained file is read-only after publication",
          modes and all(not (m & 0o222) for m in modes), modes[:4])

    # Honest replay verdict rather than a silent pass.
    check("SAFETY replay is declared INCOMPLETE for this run, and says which files",
          man["reaudit"]["SAFETY"]["kind"] == "INCOMPLETE"
          and man["reaudit"]["SAFETY"]["possible"] is False
          and "WRITER_PACKET.json" in man["reaudit"]["SAFETY"]["missing"],
          man["reaudit"]["SAFETY"])
    check("grounding and fact check are still preserved-and-inspectable",
          man["reaudit"]["GROUNDING"]["kind"] == "INPUTS_AND_RESULT_PRESERVED"
          and man["reaudit"]["FACT_CHECK"]["kind"] == "INPUTS_AND_RESULT_PRESERVED")

    # Pointer + verify round trip.
    check("the article was stamped with its pointer",
          PA.read_post(post)[0].get("audit_bundle") == man["bundle_id"])
    res = PA.verify(post, audit_root=store)
    check("and verify() resolves the article to that bundle cleanly",
          res["ok"], res.get("problems"))

    # Immutability: a second retain without --force is refused.
    try:
        PA.retain(post, audit_root=store, roots=[ev])
        check("re-retaining an existing bundle is refused", False, "it returned")
    except PA.RetentionError:
        check("re-retaining an existing bundle is refused", True)

    # A run that cannot be resolved at retain() time still aborts the publication.
    shutil.rmtree(ev)
    post5 = post_at(tmp / "_posts", "2026-09-04-five.md", rid)
    try:
        PA.retain(post5, audit_root=store, roots=[ev])
        check("retain() still fails closed when the exact run is gone", False, "returned")
    except PA.RetentionError as e:
        check("retain() still fails closed when the exact run is gone", True)
        check("and no bundle was left behind for it",
              not (store / post5.stem).exists(), str(e)[:120])


def main() -> int:
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="retention-feasibility-"))
    saved = dict(os.environ)
    try:
        os.environ.pop("CRIPMINDS_EVIDENCE_ROOTS", None)
        for fn in (test_accepted_article_on_a_legacy_composition_run_is_feasible,
                   test_unresolvable_or_unusable_runs_still_fail_closed,
                   test_retention_never_borrows_another_run,
                   test_manifest_hashing_and_freeze_are_unchanged):
            print("\n" + fn.__name__)
            fn(tmp)
    finally:
        os.environ.clear()
        os.environ.update(saved)
        for q in sorted(tmp.rglob("*"), reverse=True):
            try:
                q.chmod(0o700)
            except OSError:
                pass
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        return 1
    print("ALL RETENTION FEASIBILITY TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
