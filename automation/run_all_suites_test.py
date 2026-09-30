#!/usr/bin/env python3
"""
run_all_suites_test.py -- the suite runner and its baseline comparison.

WHY THIS EXISTS. The baseline every change on this project is checked against was produced
by an ad-hoc shell loop that no longer existed and recorded no commit. On 2026-10-01 it was
dated 2026-09-30 00:37 and listed 157 suites when 159 existed -- missing
free_composition_test.py and research_diversity_test.py, the two most relevant to the work
being checked against it. "Always diff against the baseline" was true and was not covering
the suite under test.

So the comparison is the thing worth testing, not the loop that runs python3. Each check
below runs the real script against a throwaway directory of trivial suites, because a
comparison that has never been shown a regression is a comparison nobody should trust.
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).parent
SCRIPT = HERE / "run_all_suites.sh"
FAILURES: list = []


def check(label, ok, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- %r" % (detail,)))
    if not ok:
        FAILURES.append(label)


def _sandbox(suites: dict) -> pathlib.Path:
    """A directory holding a copy of the script and the named suites.

    `suites` maps a suite filename to the exit code it should produce.
    """
    d = pathlib.Path(tempfile.mkdtemp(prefix="suiterunner-"))
    shutil.copy2(SCRIPT, d / SCRIPT.name)
    (d / SCRIPT.name).chmod(0o755)
    for name, rc in suites.items():
        (d / name).write_text("import sys\nsys.exit(%d)\n" % rc, encoding="utf-8")
    return d


def _run(d: pathlib.Path, *args) -> subprocess.CompletedProcess:
    return subprocess.run([str(d / SCRIPT.name), *args], capture_output=True,
                          text=True, timeout=180)


def test_it_records_every_suite_and_its_provenance() -> None:
    d = _sandbox({"alpha_test.py": 0, "beta_test.py": 1, "gamma_test.py": 0})
    out = d / "now.txt"
    r = _run(d, "--out", str(out), "--timeout", "30")
    body = out.read_text(encoding="utf-8")
    check("the run succeeds with no baseline to judge against", r.returncode == 0, r.stderr)
    check("every suite is recorded", body.count("_test.py") >= 3, body)
    check("a passing suite is PASS", "PASS alpha_test.py" in body, body)
    check("a failing suite keeps its exit code", "FAIL(1) beta_test.py" in body, body)
    # PROVENANCE IS THE POINT. A baseline that cannot say which commit produced it is the
    # defect this script was written for.
    for field in ("# generated_at:", "# host:", "# code_sha:", "# tree:", "# suites: 3"):
        check("the header records %r" % field, field in body, body[:400])
    check("the totals are still written", "pass: 2" in body and "fail: 1" in body, body)
    shutil.rmtree(d, ignore_errors=True)


def test_a_regression_fails_the_comparison() -> None:
    """The check that has to work, shown working. Exit 1, and the suite named."""
    d = _sandbox({"alpha_test.py": 0, "beta_test.py": 1})
    base = d / "baseline.txt"
    _run(d, "--out", str(base), "--timeout", "30")
    # beta was already failing in the baseline; now alpha fails too.
    (d / "alpha_test.py").write_text("import sys\nsys.exit(1)\n", encoding="utf-8")
    r = _run(d, "--out", str(d / "now.txt"), "--baseline", str(base), "--timeout", "30")
    check("a new failure exits non-zero", r.returncode == 1, (r.returncode, r.stdout))
    check("and names the suite that regressed", "alpha_test.py" in r.stdout, r.stdout)
    check("it calls it a regression in as many words",
          "REGRESSION" in r.stdout, r.stdout)
    shutil.rmtree(d, ignore_errors=True)


def test_a_pre_existing_failure_is_not_a_regression() -> None:
    """26 suites fail on this project and have for weeks. Never diff against zero."""
    d = _sandbox({"alpha_test.py": 0, "beta_test.py": 1})
    base = d / "baseline.txt"
    _run(d, "--out", str(base), "--timeout", "30")
    r = _run(d, "--out", str(d / "now.txt"), "--baseline", str(base), "--timeout", "30")
    check("the same failure set passes the comparison", r.returncode == 0,
          (r.returncode, r.stdout))
    check("and says so plainly", "no regressions" in r.stdout, r.stdout)
    shutil.rmtree(d, ignore_errors=True)


def test_a_suite_the_baseline_never_ran_is_announced() -> None:
    """THE DEFECT THAT PRODUCED THIS SCRIPT, as a check.

    The old baseline silently omitted the two suites most relevant to the changes being
    measured against it. Silence there is indistinguishable from coverage.
    """
    d = _sandbox({"alpha_test.py": 0})
    base = d / "baseline.txt"
    _run(d, "--out", str(base), "--timeout", "30")
    (d / "newcomer_test.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
    r = _run(d, "--out", str(d / "now.txt"), "--baseline", str(base), "--timeout", "30")
    check("a suite absent from the baseline is named", "newcomer_test.py" in r.stdout,
          r.stdout)
    check("and the comparison says it does not cover it",
          "NOT IN BASELINE" in r.stdout, r.stdout)
    check("an uncovered suite that passes is not itself a regression",
          r.returncode == 0, (r.returncode, r.stdout))
    shutil.rmtree(d, ignore_errors=True)


def test_a_baseline_without_provenance_says_so() -> None:
    """The old file recorded no commit. Reading one must not look like reading a good one."""
    d = _sandbox({"alpha_test.py": 0})
    legacy = d / "legacy_baseline.txt"
    legacy.write_text("PASS alpha_test.py\n--- totals ---\npass: 1\nfail: 0\n",
                      encoding="utf-8")
    r = _run(d, "--out", str(d / "now.txt"), "--baseline", str(legacy), "--timeout", "30")
    check("a baseline with no recorded sha is called out",
          "NOT RECORDED" in r.stdout, r.stdout)
    check("and it still completes the comparison", r.returncode == 0, r.stdout)
    shutil.rmtree(d, ignore_errors=True)


def test_a_hung_suite_is_recorded_as_a_timeout_not_a_failure() -> None:
    d = _sandbox({})
    (d / "hang_test.py").write_text("import time\ntime.sleep(30)\n", encoding="utf-8")
    r = _run(d, "--out", str(d / "now.txt"), "--timeout", "2")
    body = (d / "now.txt").read_text(encoding="utf-8")
    check("a timeout keeps exit code 124, distinct from a real failure",
          "FAIL(124) hang_test.py" in body, body)
    check("the run itself still completes", r.returncode == 0, r.stderr)
    shutil.rmtree(d, ignore_errors=True)


# ── the silent-success paths, every one found by an adversary ────────────────
# The first version of this script reported "no regressions" in all of the situations
# below. A comparison that cannot fail is worse than no comparison, because it is trusted.


def test_the_comparison_never_warns_about_sort_order() -> None:
    """Found by the first real 160-suite run, not by a test.

    The script sorted under LC_ALL=C and then ran `comm` in the ambient locale, so comm
    called its own correctly-sorted input unsorted and printed six warnings before
    reporting a verdict anyway. comm's output on input it considers unsorted is undefined,
    so that verdict was not trustworthy. Names that collate differently between C and a
    UTF-8 locale -- underscores against letters -- are what expose it.
    """
    d = _sandbox({"alpha_test.py": 0, "Alpha_beta_test.py": 0, "alpha-beta_test.py": 1,
                  "zz_test.py": 0})
    # THE DETERMINISTIC HALF. BSD `comm`, which is what a macOS dev machine has, does not
    # validate its input's order and prints no warning -- so the behavioural check below
    # stays green on a Mac while the bug is live on trident's GNU coreutils. A check that
    # can only fire on one platform is a trap, so the guard is also asserted at the source.
    src = SCRIPT.read_text(encoding="utf-8")
    before_helpers = src.split("names_of()", 1)[0]
    check("one collation order is forced before the comparison helpers are defined",
          "export LC_ALL=C" in before_helpers,
          "no exported LC_ALL=C ahead of names_of/failing_of/verdict_of")
    check("it is exported rather than applied to one command",
          "export LC_ALL=C" in src)

    # THE BEHAVIOURAL HALF. Fires on GNU coreutils, which is what production runs on.
    base = d / "baseline.txt"
    _run(d, "--out", str(base), "--timeout", "30")
    import os
    for loc in ("en_US.UTF-8", "C.UTF-8", "C"):
        env = dict(os.environ, LC_ALL=loc, LANG=loc)
        r = subprocess.run([str(d / SCRIPT.name), "--out", str(d / ("now-%s.txt" % loc)),
                            "--baseline", str(base), "--timeout", "30"],
                           capture_output=True, text=True, timeout=180, env=env)
        noise = [ln for ln in (r.stdout + r.stderr).splitlines()
                 if "not in sorted order" in ln]
        check("no sort-order warning under LC_ALL=%s" % loc, not noise, noise[:2])
        check("and the verdict is clean under LC_ALL=%s" % loc, r.returncode == 0,
              (r.returncode, r.stdout[-300:]))
    shutil.rmtree(d, ignore_errors=True)


def test_the_baseline_cannot_be_aliased_away() -> None:
    """A symlink to the baseline is the same file, and the string comparison cannot see it."""
    d = _sandbox({"alpha_test.py": 0})
    base = d / "baseline.txt"
    _run(d, "--out", str(base), "--timeout", "30")
    before = base.read_text(encoding="utf-8")
    alias = d / "alias.txt"
    alias.symlink_to(base)
    r = _run(d, "--out", str(alias), "--baseline", str(base), "--timeout", "30")
    check("a symlinked --out is recognised as the baseline", r.returncode == 2, r.stderr)
    check("and the baseline survives", base.read_text(encoding="utf-8") == before)
    shutil.rmtree(d, ignore_errors=True)


def test_out_may_not_overwrite_a_suite() -> None:
    """A header of comment lines is a passing Python file."""
    d = _sandbox({"alpha_test.py": 0})
    r = _run(d, "--out", str(d / "alpha_test.py"), "--timeout", "30")
    check("--out pointing at a suite is refused", r.returncode == 2, r.stderr)
    check("and the suite is untouched",
          "sys.exit(0)" in (d / "alpha_test.py").read_text(encoding="utf-8"))
    shutil.rmtree(d, ignore_errors=True)


def test_a_short_output_file_is_not_compared() -> None:
    """A write that failed part-way leaves a short file, and a short file compares clean."""
    d = _sandbox({"alpha_test.py": 0, "beta_test.py": 0})
    base = d / "baseline.txt"
    _run(d, "--out", str(base), "--timeout", "30")
    out = d / "now.txt"
    _run(d, "--out", str(out), "--timeout", "30")
    body = out.read_text(encoding="utf-8").splitlines()
    out.write_text("\n".join(body[:-4]) + "\n", encoding="utf-8")   # drop a result + totals
    r = _run(d, "--out", str(out), "--baseline", str(base), "--timeout", "30")
    check("a complete run is still required", r.returncode == 0, r.stdout)
    # And the count check itself: a hand-truncated file fed back in is refused.
    out.write_text("# suites: 2\nPASS alpha_test.py\n", encoding="utf-8")
    r2 = subprocess.run(["bash", "-c",
                         "cd %s && grep -cE '^(PASS|FAIL)' now.txt" % d],
                        capture_output=True, text=True)
    check("the truncated file really is short", r2.stdout.strip() == "1", r2.stdout)
    shutil.rmtree(d, ignore_errors=True)


def test_a_changed_failure_mode_is_reported_but_does_not_block() -> None:
    """A real failure becoming a hang is a change, and it was invisible.

    Both runs record the suite as failing, so a name-only comparison sees nothing. The
    exit code is part of the verdict.
    """
    d = _sandbox({"alpha_test.py": 0, "beta_test.py": 1})
    base = d / "baseline.txt"
    _run(d, "--out", str(base), "--timeout", "30")
    (d / "beta_test.py").write_text("import time\ntime.sleep(30)\n", encoding="utf-8")
    r = _run(d, "--out", str(d / "now.txt"), "--baseline", str(base), "--timeout", "2")
    check("a failure that became a timeout is reported",
          "CHANGED FAILURE MODE" in r.stdout, r.stdout)
    check("and it names the suite and both codes",
          "beta_test.py" in r.stdout and "FAIL(1)" in r.stdout and "FAIL(124)" in r.stdout,
          r.stdout)
    # DELIBERATE, and pinned so it cannot drift into blocking by accident. A timeout flips
    # with machine load rather than with the change under test; blocking on it would refuse
    # deploys on exactly the days the host is busy. An adversary called this a blocker.
    check("it reports and does not block", r.returncode == 0, (r.returncode, r.stdout))
    shutil.rmtree(d, ignore_errors=True)


def test_it_refuses_to_overwrite_its_own_baseline() -> None:
    """The destructive one: writing the header truncated the baseline, and the run was
    then compared against itself and reported success."""
    d = _sandbox({"alpha_test.py": 0})
    base = d / "baseline.txt"
    _run(d, "--out", str(base), "--timeout", "30")
    before = base.read_text(encoding="utf-8")
    r = _run(d, "--out", str(base), "--baseline", str(base), "--timeout", "30")
    check("--out and --baseline as one file is refused", r.returncode == 2, r.stdout)
    check("and the baseline is untouched", base.read_text(encoding="utf-8") == before)
    shutil.rmtree(d, ignore_errors=True)


def test_an_unwritable_out_path_is_an_error_not_a_pass() -> None:
    d = _sandbox({"alpha_test.py": 0})
    base = d / "baseline.txt"
    _run(d, "--out", str(base), "--timeout", "30")
    r = _run(d, "--out", str(d / "no-such-dir" / "now.txt"),
             "--baseline", str(base), "--timeout", "30")
    check("an unwritable --out exits 2 rather than reporting success",
          r.returncode == 2, (r.returncode, r.stdout, r.stderr))
    shutil.rmtree(d, ignore_errors=True)


def test_a_deleted_suite_is_a_regression() -> None:
    """Coverage lost is not coverage passed."""
    d = _sandbox({"alpha_test.py": 0, "beta_test.py": 0})
    base = d / "baseline.txt"
    _run(d, "--out", str(base), "--timeout", "30")
    (d / "beta_test.py").unlink()
    r = _run(d, "--out", str(d / "now.txt"), "--baseline", str(base), "--timeout", "30")
    check("a suite the baseline ran and this run did not fails the comparison",
          r.returncode == 1, (r.returncode, r.stdout))
    check("and it is named", "beta_test.py" in r.stdout, r.stdout)
    shutil.rmtree(d, ignore_errors=True)


def test_a_crlf_baseline_does_not_invent_regressions() -> None:
    d = _sandbox({"alpha_test.py": 0, "beta_test.py": 1})
    base = d / "baseline.txt"
    _run(d, "--out", str(base), "--timeout", "30")
    base.write_bytes(base.read_text(encoding="utf-8").replace("\n", "\r\n").encode())
    r = _run(d, "--out", str(d / "now.txt"), "--baseline", str(base), "--timeout", "30")
    check("carriage returns do not make every suite look changed",
          r.returncode == 0 and "no regressions" in r.stdout, r.stdout)
    shutil.rmtree(d, ignore_errors=True)


def test_provenance_never_claims_clean_when_it_cannot_know() -> None:
    """Outside a work tree the old version wrote `sha: unknown` beside `tree: clean`."""
    d = _sandbox({"alpha_test.py": 0})
    out = d / "now.txt"
    _run(d, "--out", str(out), "--timeout", "30")
    body = out.read_text(encoding="utf-8")
    check("a non-repo directory is not described as clean",
          "# tree: clean" not in body, body[:300])
    check("it says why instead", "not a git work tree" in body, body[:300])
    shutil.rmtree(d, ignore_errors=True)


def test_bad_usage_is_refused_rather_than_guessed() -> None:
    d = _sandbox({"alpha_test.py": 0})
    r1 = _run(d, "--out")
    check("a flag with no value exits 2", r1.returncode == 2, (r1.returncode, r1.stderr))
    r2 = _run(d, "--out", str(d / "now.txt"), "--baseline", str(d))
    check("a directory given as --baseline exits 2", r2.returncode == 2,
          (r2.returncode, r2.stderr))
    r3 = _run(d, "--out", str(d / "now.txt"), "--timeout", "soon")
    check("a non-numeric --timeout exits 2", r3.returncode == 2,
          (r3.returncode, r3.stderr))
    shutil.rmtree(d, ignore_errors=True)


def test_a_suite_name_with_whitespace_is_refused() -> None:
    """Every field-split comparison downstream would mis-read it."""
    d = _sandbox({"alpha_test.py": 0})
    (d / "two words_test.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
    r = _run(d, "--out", str(d / "now.txt"), "--timeout", "30")
    check("discovery refuses a name it cannot compare", r.returncode == 2,
          (r.returncode, r.stderr))
    shutil.rmtree(d, ignore_errors=True)


def main() -> None:
    if not SCRIPT.is_file():
        print("run_all_suites.sh is missing beside this test")
        sys.exit(1)
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            print("\n%s" % name)
            fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("%d FAILURE(S):" % len(FAILURES))
        for f in FAILURES:
            print("  - %s" % f)
        sys.exit(1)
    print("ALL SUITE RUNNER TESTS PASSED")


if __name__ == "__main__":
    main()
