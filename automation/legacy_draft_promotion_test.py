#!/usr/bin/env python3
"""
legacy_draft_promotion_test.py — legacy-draft auto-promotion fail-closed
closure (2026-08-16), triggered by the "Reached by Boat or Plane" remediation
audit.

WHAT THE AUDIT FOUND (read-only, against the actual pre-fix publish_best.py):
an Era-D draft generated 2026-08-11 -- three days before AP1/APE2 and five
days before PS1 existed -- was promoted to _posts/ on 2026-08-15 by
publish_best.py on nothing but a five-day-old `fact_check_status: verified`
stamp. publish_best.py has never imported anything from
automation.orchestrator (confirmed: no `_fable_editorial_review`,
`persona_biography`, `grounding`, or `validate_article` reference anywhere in
the module, before or after this fix) -- it re-runs NOTHING at promotion
time. Its only content-safety check was `fm.get("fact_check_status") ==
"blocked"`, which reads BOTH a missing field AND a legacy "verified" value as
eligible, with zero distinction between "checked under whatever regime was
current at generation time" and "checked under what's current NOW".

CONFIRMED PRE-FIX (via direct calls against publish_best.py's own dict-based
logic, run before any code changed):
  fm_missing.get("fact_check_status") == "blocked"          -> False (so: eligible)
  fm_legacy_verified.get("fact_check_status") == "blocked"  -> False (so: eligible)
  fm_blocked.get("fact_check_status") == "blocked"          -> True  (so: skipped, unchanged)
  publish_best.py source contains any of {_fable_editorial_review,
    persona_biography, grounding, validate_article}         -> False (no revalidation existed)

This file proves the fix: _ordinary_eligibility_ok (bullet A -- fact_check_status
must be the EXPLICIT literal "verified") and _current_safety_contract_ok
(bullet B -- publication_safety_version must be >= REQUIRED_SAFETY_VERSION,
proving the CURRENT safety contract actually ran and cleared on this exact
draft, not some past pipeline version). Both must hold or the draft is HELD
(NEEDS_CURRENT_REVALIDATION), not promoted -- and left untouched on disk for
a later remediation pass to decide its fate. This task does NOT solve the
legacy corpus; it only closes the auto-promotion path as a way NEW legacy
publications can happen.

Zero network, zero model calls, zero article generation. Uses temp
directories for every main()/dry_run integration case -- never touches the
real repo's _drafts/_posts.

USAGE: python3 automation/legacy_draft_promotion_test.py
Exit code 0 = all pass. Exit code 1 = at least one failure (printed).
"""
import io
import shutil
import sys
import tempfile
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path

AUTOMATION_DIR = Path(__file__).parent
sys.path.insert(0, str(AUTOMATION_DIR))

import publish_best as pb  # noqa: E402
from snapshot_test import _import_orchestrator  # noqa: E402

FAILURES = []


def check(name, condition):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}")
        FAILURES.append(name)


# ─────────────────────────────────────────────────────────────────────────
# (1) Unit-level: the two new gate functions in isolation
# ─────────────────────────────────────────────────────────────────────────

def case_bullet_a_ordinary_eligibility():
    check("A: missing fact_check_status -> NOT ordinary-eligible (THE FIX -- "
          "was silently eligible before)",
          pb._ordinary_eligibility_ok({}) is False)
    check("A: fact_check_status: verified -> ordinary-eligible",
          pb._ordinary_eligibility_ok({"fact_check_status": "verified"}) is True)
    check("A: fact_check_status: blocked -> NOT ordinary-eligible (caught earlier "
          "in main() anyway, but the helper itself must also agree)",
          pb._ordinary_eligibility_ok({"fact_check_status": "blocked"}) is False)
    check("A: any other/typo'd value -> NOT ordinary-eligible (no implicit pass)",
          pb._ordinary_eligibility_ok({"fact_check_status": "pending"}) is False)


def case_bullet_b_current_safety_contract():
    check("B: missing publication_safety_version -> NOT current-safe (THE FIX)",
          pb._current_safety_contract_ok({}) is False)
    check("B: publication_safety_version: 0 -> NOT current-safe",
          pb._current_safety_contract_ok({"publication_safety_version": "0"}) is False)
    check(f"B: publication_safety_version: {pb.REQUIRED_SAFETY_VERSION} -> current-safe",
          pb._current_safety_contract_ok(
              {"publication_safety_version": str(pb.REQUIRED_SAFETY_VERSION)}) is True)
    check("B: publication_safety_version higher than required -> current-safe "
          "(forward compatible with a future contract bump)",
          pb._current_safety_contract_ok(
              {"publication_safety_version": str(pb.REQUIRED_SAFETY_VERSION + 1)}) is True)
    check("B: malformed non-numeric value -> NOT current-safe, no crash",
          pb._current_safety_contract_ok({"publication_safety_version": "not-a-number"}) is False)


def case_structural_no_revalidation_import_exists():
    # Confirms this fix did NOT quietly start re-running AP1/APE2/PS1/grounding/
    # review at promotion time -- the task explicitly scopes this to a metadata
    # gate, not a live revalidation engine. Mirrors should_block_policy_test.py's
    # "cj2_shadow.py never appends to _degraded_stages" structural-check pattern.
    src = (AUTOMATION_DIR / "publish_best.py").read_text()
    for needle in ("_fable_editorial_review", "persona_biography", "build_evidence_packet",
                   "validate_article", "import orchestrator"):
        check(f"publish_best.py still does not import/call {needle!r} "
              f"(gate is metadata-only, by design -- no live revalidation added)",
              needle not in src)


# ─────────────────────────────────────────────────────────────────────────
# (1b) Generation-path unit tests: GenerateMixin._maybe_stamp_publication_
# safety_version -- the other half of this fix (Step 6: "Update the CURRENT
# generation path so a genuinely successful new draft can receive the
# current-safety marker"). Calls the extracted staticmethod-shaped instance
# method directly against a temp file, exactly the way should_block_policy_
# test.py calls _compute_should_block directly -- no full pipeline mock
# needed, since the method's only inputs are a Path and a bool.
# ─────────────────────────────────────────────────────────────────────────

def _write_fm_file(tmp_path, fact_check_status=None, publication_safety_version=None):
    lines = ["---", "title: \"x\""]
    if fact_check_status is not None:
        lines.append(f"fact_check_status: {fact_check_status}")
    if publication_safety_version is not None:
        lines.append(f"publication_safety_version: {publication_safety_version}")
    lines += ["---", "", "body"]
    tmp_path.write_text("\n".join(lines), encoding="utf-8")
    return tmp_path


def case_stamp_fires_when_verified_and_not_should_block():
    po = _import_orchestrator()
    orch = po.ProductionOrchestrator()
    with tempfile.TemporaryDirectory() as d:
        f = _write_fm_file(Path(d) / "a.md", fact_check_status="verified")
        orch._maybe_stamp_publication_safety_version(f, should_block=False)
        text = f.read_text()
        check("stamps publication_safety_version when should_block=False and "
              "fact_check_status: verified -- THE HAPPY PATH new drafts must "
              "hit to ever become promotion-eligible",
              f"publication_safety_version: {orch.PUBLICATION_SAFETY_CONTRACT_VERSION}" in text)


def case_stamp_withheld_when_should_block_true():
    po = _import_orchestrator()
    orch = po.ProductionOrchestrator()
    with tempfile.TemporaryDirectory() as d:
        f = _write_fm_file(Path(d) / "a.md", fact_check_status="verified")
        orch._maybe_stamp_publication_safety_version(f, should_block=True)
        check("does NOT stamp when should_block=True, even though fact_check_status "
              "says verified -- a known unresolved authoritative finding (e.g. "
              "persona_biography_unresolved) must never earn current-safety "
              "eligibility regardless of what the unrelated fact-check pass concluded",
              "publication_safety_version" not in f.read_text())


def case_stamp_withheld_when_fact_check_not_verified():
    po = _import_orchestrator()
    orch = po.ProductionOrchestrator()
    with tempfile.TemporaryDirectory() as d:
        f_missing = _write_fm_file(Path(d) / "a.md")
        orch._maybe_stamp_publication_safety_version(f_missing, should_block=False)
        check("does NOT stamp when fact_check_status is entirely missing, even "
              "with should_block=False",
              "publication_safety_version" not in f_missing.read_text())

        f_blocked = _write_fm_file(Path(d) / "b.md", fact_check_status="blocked")
        orch._maybe_stamp_publication_safety_version(f_blocked, should_block=False)
        check("does NOT stamp when fact_check_status: blocked",
              "publication_safety_version" not in f_blocked.read_text())


def case_stamp_is_idempotent_never_overwrites():
    po = _import_orchestrator()
    orch = po.ProductionOrchestrator()
    with tempfile.TemporaryDirectory() as d:
        f = _write_fm_file(Path(d) / "a.md", fact_check_status="verified",
                            publication_safety_version=999)
        orch._maybe_stamp_publication_safety_version(f, should_block=False)
        check("never overwrites an existing publication_safety_version "
              "(idempotent, matches every other guarded front-matter write "
              "in this file)",
              "publication_safety_version: 999" in f.read_text())


def case_current_generation_output_satisfies_publish_bests_own_gate():
    # Closes the loop end-to-end without a full pipeline mock: whatever
    # generate.py stamps must independently satisfy publish_best.py's two
    # gate functions -- proves the two halves of this fix actually agree with
    # each other, not just individually pass their own tests.
    po = _import_orchestrator()
    orch = po.ProductionOrchestrator()
    with tempfile.TemporaryDirectory() as d:
        f = _write_fm_file(Path(d) / "a.md", fact_check_status="verified")
        orch._maybe_stamp_publication_safety_version(f, should_block=False)
        fm = pb.parse_frontmatter(f.read_text())
        check("a freshly-stamped current draft passes publish_best.py's bullet A",
              pb._ordinary_eligibility_ok(fm) is True)
        check("a freshly-stamped current draft passes publish_best.py's bullet B",
              pb._current_safety_contract_ok(fm) is True)


# ─────────────────────────────────────────────────────────────────────────
# (2) Integration: main(dry_run=...) against constructed temp drafts
# ─────────────────────────────────────────────────────────────────────────

def _today_minus(days):
    """YYYY-MM-DD string for `days` before the real host clock's today --
    used for both filenames (draft_date() reads only the filename prefix for
    age-window classification) and front-matter `date:` fields, so mixed-pool
    tests stay correct regardless of what day they actually run on."""
    from datetime import timedelta
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")


def _draft_text(fact_check_status=None, publication_safety_version=None, author="Zen Circuit",
                 title="A Test Draft", date=None):
    date = date or datetime.now().strftime("%Y-%m-%d")
    lines = ["---", f"title: \"{title}\"", f"author: \"{author}\"", f"date: {date}"]
    if fact_check_status is not None:
        lines.append(f"fact_check_status: {fact_check_status}")
    if publication_safety_version is not None:
        lines.append(f"publication_safety_version: {publication_safety_version}")
    lines.append("---")
    lines.append("")
    lines.append("Body text for the test draft. " * 20)
    return "\n".join(lines)


class _TempRepo:
    """Points pb.DRAFTS/POSTS/ARCHIVE at an isolated temp tree for the duration
    of a `with` block, restoring the real module globals afterward -- so
    main() (even with dry_run=False) can never touch the real repo's
    _drafts/_posts, regardless of what future test cases in this file do."""
    def __enter__(self):
        self._tmp = tempfile.mkdtemp(prefix="legacy_draft_promotion_test_")
        self._orig = (pb.REPO, pb.DRAFTS, pb.POSTS, pb.ARCHIVE)
        root = Path(self._tmp)
        pb.REPO = root
        pb.DRAFTS = root / "_drafts"
        pb.POSTS = root / "_posts"
        pb.ARCHIVE = pb.DRAFTS / "_archive"
        pb.DRAFTS.mkdir(parents=True)
        pb.POSTS.mkdir(parents=True)
        return self

    def write_draft(self, filename, **kwargs):
        (pb.DRAFTS / filename).write_text(_draft_text(**kwargs), encoding="utf-8")
        return pb.DRAFTS / filename

    def __exit__(self, *exc):
        pb.REPO, pb.DRAFTS, pb.POSTS, pb.ARCHIVE = self._orig
        shutil.rmtree(self._tmp, ignore_errors=True)


def _run_dry(*args, **kwargs):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = pb.main(dry_run=True)
    return rc, buf.getvalue()


def case_missing_status_is_held_not_promoted():
    with _TempRepo() as repo:
        repo.write_draft("2026-08-16-missing-status.md")  # no fact_check_status at all
        rc, out = _run_dry()
        check("missing fact_check_status -> HELD, not published (integration, THE FIX)",
              "HELD" in out and "NEEDS_CURRENT_REVALIDATION" in out)
        check("missing-status draft never appears as 'Would publish'",
              "Would publish" not in out)


def case_legacy_verified_no_marker_is_held():
    with _TempRepo() as repo:
        # Exact shape of the real "Reached by Boat or Plane" incident: verified,
        # but generated before publication_safety_version existed at all.
        repo.write_draft("2026-08-11-legacy-shaped.md", fact_check_status="verified")
        rc, out = _run_dry()
        check("legacy fact_check_status: verified with NO publication_safety_version "
              "-> HELD, not published (THE FIX -- this is the exact bug shape)",
              "HELD" in out and "NEEDS_CURRENT_REVALIDATION" in out)
        check("legacy-verified draft never appears as 'Would publish'",
              "Would publish" not in out)


def case_old_verified_stale_version_is_held():
    with _TempRepo() as repo:
        # A draft stamped under some EARLIER version of the safety contract --
        # not merely absent, but explicitly stale. Must still be held once
        # REQUIRED_SAFETY_VERSION is bumped past it.
        repo.write_draft("2026-08-12-stale-version.md", fact_check_status="verified",
                          publication_safety_version=0)
        rc, out = _run_dry()
        check("verified draft with publication_safety_version below the required "
              "floor -> HELD, not published",
              "HELD" in out and "NEEDS_CURRENT_REVALIDATION" in out)


def case_blocked_status_still_skipped_unchanged():
    with _TempRepo() as repo:
        repo.write_draft("2026-08-15-blocked.md", fact_check_status="blocked")
        rc, out = _run_dry()
        check("fact_check_status: blocked -> still SKIPPED with its original "
              "message (unchanged pre-existing behavior)",
              "SKIPPED" in out and "fact_check_status: blocked" in out)
        check("blocked draft is not reported as HELD (distinct, pre-existing "
              "classification, not folded into the new gate's message)",
              "2026-08-15-blocked.md: HELD" not in out)


def case_current_safe_draft_still_eligible():
    with _TempRepo() as repo:
        repo.write_draft("2026-08-16-current-safe.md", fact_check_status="verified",
                          publication_safety_version=pb.REQUIRED_SAFETY_VERSION)
        rc, out = _run_dry()
        check("fact_check_status: verified + current publication_safety_version "
              "-> genuinely eligible, reaches scoring (REGRESSION GUARD -- the fix "
              "must not block legitimate current drafts)",
              "Would publish: 2026-08-16-current-safe.md" in out)
        check("current-safe draft is not HELD",
              "current-safe.md: HELD" not in out)


def case_forward_compatible_higher_version_still_eligible():
    with _TempRepo() as repo:
        repo.write_draft("2026-08-16-future-safe.md", fact_check_status="verified",
                          publication_safety_version=pb.REQUIRED_SAFETY_VERSION + 5)
        rc, out = _run_dry()
        check("publication_safety_version higher than currently required -> still "
              "eligible (forward compatible with later contract bumps)",
              "Would publish: 2026-08-16-future-safe.md" in out)


def case_mixed_pool_only_current_safe_wins():
    # The realistic shape: several legacy-shaped drafts sitting alongside one
    # genuinely current-safe draft. Only the current-safe one may be promoted;
    # the legacy ones must be reported HELD, not silently dropped or archived.
    with _TempRepo() as repo:
        # Dates chosen deliberately within AGE_WINDOW_DAYS (7) of "now" so every
        # draft here reaches the promotion gate itself, rather than being
        # filtered out first by the separate, pre-existing age-expiry path
        # (unrelated to this fix) -- filename dates use the real host clock's
        # "today" via _today_minus, not a hardcoded date, so this test stays
        # correct regardless of what day it actually runs.
        d0, d3, d4, d5 = (_today_minus(n) for n in (0, 3, 4, 5))
        repo.write_draft(f"{d5}-legacy-a.md", fact_check_status="verified", date=d5)
        repo.write_draft(f"{d4}-legacy-b.md", date=d4)  # missing status entirely
        repo.write_draft(f"{d3}-blocked-c.md", fact_check_status="blocked", date=d3)
        repo.write_draft(f"{d0}-current-safe-d.md", fact_check_status="verified",
                          publication_safety_version=pb.REQUIRED_SAFETY_VERSION, date=d0)
        rc, out = _run_dry()
        check("mixed pool: only the current-safe draft is the promotion pick",
              f"Would publish: {d0}-current-safe-d.md" in out)
        check("mixed pool: legacy-a held",
              f"{d5}-legacy-a.md: HELD" in out)
        check("mixed pool: legacy-b (missing status) held",
              f"{d4}-legacy-b.md: HELD" in out)
        check("mixed pool: blocked-c still uses the distinct SKIPPED path",
              f"{d3}-blocked-c.md: SKIPPED" in out)


def case_held_drafts_remain_on_disk_not_archived_or_altered():
    # Real (non-dry-run) run, but with zero winners AND zero expired drafts,
    # so main() hits its early `if not published and not archived: return 0`
    # before any git subprocess call -- safe to run for real in the temp repo.
    with _TempRepo() as repo:
        held_path = repo.write_draft("2026-08-14-legacy-held.md", fact_check_status="verified")
        original_bytes = held_path.read_bytes()
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = pb.main(dry_run=False)
        out = buf.getvalue()
        check("held draft is still present on disk after a real (non-dry) run",
              held_path.exists())
        check("held draft's content is byte-identical -- not rewritten, not "
              "auto-corrected, not stamped with any new field",
              held_path.exists() and held_path.read_bytes() == original_bytes)
        check("held draft was not moved into _drafts/_archive/",
              not (pb.ARCHIVE / held_path.name).exists())
        check("held draft was not moved into _posts/",
              not (pb.POSTS / held_path.name).exists())
        check("main() returned 0 (no error) even though nothing was promotable this cycle",
              rc == 0)


if __name__ == "__main__":
    case_bullet_a_ordinary_eligibility()
    case_bullet_b_current_safety_contract()
    case_structural_no_revalidation_import_exists()
    case_stamp_fires_when_verified_and_not_should_block()
    case_stamp_withheld_when_should_block_true()
    case_stamp_withheld_when_fact_check_not_verified()
    case_stamp_is_idempotent_never_overwrites()
    case_current_generation_output_satisfies_publish_bests_own_gate()
    case_missing_status_is_held_not_promoted()
    case_legacy_verified_no_marker_is_held()
    case_old_verified_stale_version_is_held()
    case_blocked_status_still_skipped_unchanged()
    case_current_safe_draft_still_eligible()
    case_forward_compatible_higher_version_still_eligible()
    case_mixed_pool_only_current_safe_wins()
    case_held_drafts_remain_on_disk_not_archived_or_altered()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    else:
        print("All legacy-draft auto-promotion fail-closed tests passed.")
        sys.exit(0)
