#!/usr/bin/env bash
# run_all_suites.sh -- run every automation/*_test.py and record the result WITH its provenance.
#
# WHY THIS EXISTS. The suite baseline this project checks every change against lived at
# /tmp/suites_baseline.txt, was produced by an ad-hoc shell loop that no longer existed,
# and recorded no commit. On 2026-10-01 it was found to be dated 2026-09-30 00:37 and to
# list 157 suites when 159 existed -- missing free_composition_test.py and
# research_diversity_test.py, the two most relevant to the work being checked against it.
# "Always diff against the baseline, never against zero" is the right rule, and it was
# silently not covering the suite under test.
#
# A baseline that does not say which commit produced it cannot be trusted, and one that
# nobody can regenerate goes stale the first time a suite is added. Both are fixed here.
#
# EVERY SILENT-SUCCESS PATH BELOW WAS FOUND BY AN ADVERSARY, NOT BY ME. The first version
# of this script reported "no regressions" when: a failing suite changed exit code (a real
# failure becoming a hang, or the reverse); --out and --baseline named the same file, so
# the header truncated the baseline and the run was compared against itself; the --out path
# was unwritable, so the comparison read an empty stream; or a suite name contained
# whitespace. A comparison that cannot fail is worse than no comparison, because it is
# trusted. Each of those is now a named check with a test.
#
# Usage:
#   run_all_suites.sh [--out PATH] [--baseline PATH] [--timeout SECONDS]
#
#   --out       where to write this run's results   (default: /tmp/suites_now.txt)
#   --baseline  compare against this                (default: none; just record)
#   --timeout   per-suite timeout in seconds        (default: 300)
#
# Exit: 0 when nothing regressed; 1 on a regression (a suite passing in the baseline that
# fails now, or a suite the baseline ran that is gone); 2 on a usage or environment error.
# Without --baseline it exits 0 unless the environment is broken -- recording is not judging.
#
# A CHANGED FAILURE MODE IS REPORTED AND DOES NOT EXIT 1, DELIBERATELY. A suite that was
# already failing and now times out (or the reverse) is printed under its own heading, but
# it does not block: 26 suites on this project fail for pre-existing reasons, one of them
# already records FAIL(124), and a timeout flips with machine load rather than with the
# change under test. Blocking on it would produce false refusals on exactly the days the
# host is busy. An adversary called this a blocker; it is a judgement, and the test
# `test_a_changed_failure_mode_is_reported_but_does_not_block` pins it so it cannot drift
# into being one by accident.
set -uo pipefail

OUT=/tmp/suites_now.txt
BASELINE=""
PER_SUITE_TIMEOUT=300

need_value() {
    # `shift 2` on a missing value loops forever on some shells and silently eats the next
    # flag on others. Checked rather than assumed.
    [[ $# -ge 2 && -n "${2:-}" && "${2:0:2}" != "--" ]] || {
        echo "$1 needs a value" >&2; exit 2; }
}
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)       need_value "$@"; OUT="$2";               shift 2 ;;
        --baseline)  need_value "$@"; BASELINE="$2";          shift 2 ;;
        --timeout)   need_value "$@"; PER_SUITE_TIMEOUT="$2"; shift 2 ;;
        -h|--help)   sed -n '2,30p' "$0"; exit 0 ;;
        *)           echo "unknown argument: $1" >&2; exit 2 ;;
    esac
done
[[ "$PER_SUITE_TIMEOUT" =~ ^[0-9]+$ ]] || { echo "--timeout must be a number" >&2; exit 2; }

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE" || exit 2

abspath() { # resolve without requiring the file to exist yet
    local d b
    d="$(cd "$(dirname -- "$1")" 2>/dev/null && pwd)" || return 1
    b="$(basename -- "$1")"
    printf '%s/%s\n' "$d" "$b"
}

command -v timeout >/dev/null || { echo "coreutils 'timeout' is required" >&2; exit 2; }

OUT_ABS="$(abspath "$OUT")" || { echo "--out directory does not exist: $OUT" >&2; exit 2; }
# --out inside the suite directory would overwrite a suite before it runs, and a header of
# comment lines is a passing Python file.
case "$OUT_ABS" in "$HERE"/*_test.py) echo "--out would overwrite a suite: $OUT_ABS" >&2; exit 2 ;; esac

# EVERY VALIDATION RUNS BEFORE ANYTHING IS WRITTEN. Truncating --out first and checking
# afterwards still destroys a baseline passed as both -- which is this check's whole point,
# and is what the first attempt at this fix did.
if [[ -n "$BASELINE" ]]; then
    [[ -f "$BASELINE" && -r "$BASELINE" ]] || {
        echo "--baseline is not a readable file: $BASELINE" >&2; exit 2; }
    BASE_ABS="$(abspath "$BASELINE")" || { echo "bad --baseline path" >&2; exit 2; }
    # THE BASELINE IS THE ONE THING THIS SCRIPT MUST NEVER DESTROY. Writing the header to
    # it would truncate it and then compare the run against itself, reporting success.
    # Compared by identity, not by spelling: a symlink or hard link to the baseline is the
    # same file and the string comparison alone does not see it.
    same_file() {
        local a b
        a="$(stat -Lc '%d:%i' "$1" 2>/dev/null || stat -Lf '%d:%i' "$1" 2>/dev/null)"
        b="$(stat -Lc '%d:%i' "$2" 2>/dev/null || stat -Lf '%d:%i' "$2" 2>/dev/null)"
        [[ -n "$a" && "$a" == "$b" ]]
    }
    { [[ "$OUT_ABS" != "$BASE_ABS" ]] && ! same_file "$OUT_ABS" "$BASE_ABS"; } || {
        echo "--out and --baseline are the same file: $OUT_ABS" >&2; exit 2; }
    # A baseline line whose suite name carries whitespace cannot be field-compared, and a
    # mis-read name silently hides a disappearance.
    if sed 's/\r$//' "$BASE_ABS" | awk '/^(PASS|FAIL)/ && NF != 2 {exit 1}'; then :; else
        echo "baseline has a result line with a whitespace name; regenerate it" >&2; exit 2
    fi
fi

: > "$OUT_ABS" || { echo "--out is not writable: $OUT_ABS" >&2; exit 2; }

# PROVENANCE, read from the checkout that is about to run -- never inferred from a
# timestamp. Untracked files count as dirty: the suites and the code they import can both
# be untracked, and a header saying "clean" over untracked code is the misleading case.
if git -C "$HERE" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    SHA="$(git -C "$HERE" rev-parse HEAD 2>/dev/null || echo unknown)"
    # An errored `git status` returns nothing, which is indistinguishable from a clean
    # tree unless the exit code is read. "Clean" must mean checked and clean.
    if status_out="$(git -C "$HERE" status --porcelain 2>/dev/null)"; then
        if [[ -n "$status_out" ]]; then
            TREE="dirty -- the sha above does not describe what ran"
        else
            TREE="clean"
        fi
    else
        TREE="unknown -- git status failed"
    fi
else
    SHA="unknown"
    TREE="unknown -- not a git work tree"
fi

mapfile -t SUITES < <(ls -1 ./*_test.py 2>/dev/null | sed 's|^\./||' | LC_ALL=C sort)
if [[ ${#SUITES[@]} -eq 0 ]]; then
    echo "no *_test.py found in $HERE" >&2
    exit 2
fi
# A name carrying whitespace breaks every field-split comparison downstream. Refused at
# discovery rather than mis-compared later.
for suite in "${SUITES[@]}"; do
    [[ "$suite" == *[[:space:]]* ]] && {
        echo "suite name contains whitespace, refusing: $suite" >&2; exit 2; }
done

{
    echo "# generated_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "# host: $(hostname)"
    echo "# repo: $HERE"
    echo "# code_sha: $SHA"
    echo "# tree: $TREE"
    echo "# python: $(python3 --version 2>&1)"
    echo "# suites: ${#SUITES[@]}"
    echo "# per_suite_timeout: ${PER_SUITE_TIMEOUT}s"
} >> "$OUT_ABS" || { echo "cannot write $OUT_ABS" >&2; exit 2; }

pass=0
fail=0
for suite in "${SUITES[@]}"; do
    timeout "$PER_SUITE_TIMEOUT" python3 "$suite" >/dev/null 2>&1
    rc=$?
    if [[ $rc -eq 0 ]]; then
        echo "PASS $suite" >> "$OUT_ABS"
        pass=$((pass + 1))
    else
        # rc 124 is the timeout, kept distinct from a real failure -- and compared, since a
        # failure becoming a hang is a change worth seeing.
        echo "FAIL($rc) $suite" >> "$OUT_ABS"
        fail=$((fail + 1))
    fi
done

{
    echo "--- totals ---"
    echo "pass: $pass"
    echo "fail: $fail"
} >> "$OUT_ABS"

echo "suites: ${#SUITES[@]}  pass: $pass  fail: $fail  sha: ${SHA:0:12} ($TREE)"
echo "written: $OUT_ABS"

[[ -n "$BASELINE" ]] || exit 0

# The comparison reads FILES, and an empty or truncated one must not read as "nothing
# failed". Both sides are required to contain at least one result line.
# grep -c always prints a number and exits 1 when the count is zero, so the count is read
# from stdout and the exit code ignored -- `|| echo 0` would emit a second line and break
# the arithmetic test below.
lines_of() { grep -cE '^(PASS|FAIL)' "$1" 2>/dev/null; }
# EVERY SUITE MUST HAVE LANDED IN THE FILE. A write that failed part-way leaves a short
# file, and a short file compares clean against a baseline. Counting is the only way to
# tell a complete run from a truncated one, since no individual append is checked.
n_out="$(lines_of "$OUT_ABS")"
[[ "${n_out:-0}" -eq "${#SUITES[@]}" ]] || {
    echo "this run recorded ${n_out:-0} of ${#SUITES[@]} suites -- the output is incomplete" >&2
    exit 2; }
n_base="$(lines_of "$BASE_ABS")"; [[ "${n_base:-0}" -gt 0 ]] || { echo "baseline has no result lines: $BASE_ABS" >&2; exit 2; }

# ONE COLLATION ORDER FOR SORT, COMM AND JOIN ALIKE. Sorting under LC_ALL=C while `comm`
# runs in the ambient locale makes comm call its own correctly-sorted input unsorted --
# observed on the first real 160-suite run, which printed "comm: file 1 is not in sorted
# order" six times and then reported a verdict anyway. comm's output on input it considers
# unsorted is undefined, so that verdict was not trustworthy, which is the exact class of
# silent wrong answer this script exists to remove. Exported once, for every child.
export LC_ALL=C

# `\r` stripped so a CRLF baseline does not report every suite as changed. The verdict
# keeps its exit code, so FAIL(1) and FAIL(124) are different results for the same suite.
names_of()   { sed 's/\r$//' "$1" | awk '/^(PASS|FAIL)/ {print $NF}'          | LC_ALL=C sort; }
failing_of() { sed 's/\r$//' "$1" | awk '/^FAIL/        {print $NF}'          | LC_ALL=C sort; }
verdict_of() { sed 's/\r$//' "$1" | awk '/^(PASS|FAIL)/ {print $NF "\t" $1}'  | LC_ALL=C sort; }

NEW_FAILURES="$(comm -23 <(failing_of "$OUT_ABS") <(failing_of "$BASE_ABS"))"
NOW_FIXED="$(comm -13 <(failing_of "$OUT_ABS") <(failing_of "$BASE_ABS"))"
UNCOVERED="$(comm -23 <(names_of "$OUT_ABS") <(names_of "$BASE_ABS"))"
DISAPPEARED="$(comm -13 <(names_of "$OUT_ABS") <(names_of "$BASE_ABS"))"
# Same suite, still failing, different exit code: reported, never silent. `join` rather
# than a -P regex, which BSD grep does not have.
CHANGED_MODE="$(join -t "$(printf '\t')" <(verdict_of "$OUT_ABS") <(verdict_of "$BASE_ABS") 2>/dev/null \
                | awk -F'\t' '$2 ~ /^FAIL/ && $3 ~ /^FAIL/ && $2 != $3 {print $1 "   " $3 " -> " $2}')"

echo
echo "baseline: $BASE_ABS"
b_sha="$(sed -n 's/^# code_sha: //p' "$BASE_ABS" | head -1)"
if [[ -n "$b_sha" ]]; then echo "baseline sha: ${b_sha:0:12}"
else echo "baseline sha: NOT RECORDED -- regenerate it with this script"; fi

# A suite the baseline never ran is not covered by the comparison, which is the exact way
# the previous baseline hid the suite under test. Said out loud rather than left implicit.
[[ -z "$UNCOVERED" ]] || { echo "NOT IN BASELINE (this comparison does not cover them):";
                           echo "$UNCOVERED" | sed 's/^/  /'; }
[[ -z "$CHANGED_MODE" ]] || { echo "CHANGED FAILURE MODE (failing before and now, different exit code):";
                              echo "$CHANGED_MODE" | sed 's/^/  /'; }
[[ -z "$NOW_FIXED" ]] || { echo "now passing that the baseline failed:";
                           echo "$NOW_FIXED" | sed 's/^/  /'; }

rc=0
if [[ -n "$DISAPPEARED" ]]; then
    echo "REGRESSION -- in the baseline, not run now (deleted or renamed):"
    echo "$DISAPPEARED" | sed 's/^/  /'
    rc=1
fi
if [[ -n "$NEW_FAILURES" ]]; then
    echo "REGRESSION -- failing now, passing in the baseline:"
    echo "$NEW_FAILURES" | sed 's/^/  /'
    rc=1
fi
[[ $rc -eq 0 ]] && echo "no regressions against the baseline"
exit $rc
