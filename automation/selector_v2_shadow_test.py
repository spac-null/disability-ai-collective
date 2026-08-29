#!/usr/bin/env python3
"""
selector_v2_shadow_test.py -- exposure, reading, judgement, and powerlessness.

The authoritative selector spends its daily budget asking a model to invent a
disability angle from a headline, then treats that invention as the ticket into
selection. Measured on 24 read sources: the angle approved weak material in 5 of 8
cases, and relevance_score -- which orders everything -- was uncorrelated with material
quality (47% strong above 0.55, 43% below 0.4). Selector V2 reads the source instead.

Two things are under test in equal measure: that it exposes and judges material the way
the measurements say it should, and that it cannot touch production. No network: source
acquisition and the model are both injected.
"""
from __future__ import annotations

import json
import os
import pathlib
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import material_policy as MP                                    # noqa: E402
import news_fetcher as NF                                       # noqa: E402
import selector_v2 as SV                                        # noqa: E402
from new_engine_v1.provider import Completion, ProviderError    # noqa: E402

FAILURES: list = []
NOW = datetime(2026, 8, 29, 9, 0, 0)


def check(label, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- " + str(detail)[:220]))
    if not ok:
        FAILURES.append(label)


# ── fixtures: bodies, never fetched ───────────────────────────────────────────
RICH_BODY = ("The Nautilus reported that a blind, pale, worm-like fish was filmed in a "
             "flooded cave near Lugh in 2026 by a diver who posted the footage to "
             "TikTok. Dr Elena Marris of the University of Bologna identified it as a "
             "possible new species of Phreatichthys. The cave system has been surveyed "
             "twice, in 1974 and 2011, and neither survey recorded the animal. "
             "Marris says the specimen has not been collected and no tissue sample "
             "exists.\n\nThe find matters because the aquifer feeds three towns.\n\n"
             + "Detail follows about the survey record and the aquifer. " * 90)
THIN_BODY = ("De Brigard and Robins have won the 2026 Lebowitz Prize. The prize is worth "
             "$25,000. It will be awarded at a symposium next spring.\n\nMore soon.")
ROUNDUP_BODY = ("School Shows: projects from the Academy\n\nCargo Bench by Ada Moreno\n"
                "\"A public seat that folds into a trolley.\"\n\nReading Rail by Bo "
                "Lindqvist\n\"A tactile handrail carrying route information.\"\n\n"
                "Chapati Machine by Cal Ndiaye\n\"A vending machine for flatbread.\"\n"
                + "Filler paragraph. " * 40)

BODIES = {"https://x.example/rich": RICH_BODY, "https://x.example/thin": THIN_BODY,
          "https://x.example/roundup": ROUNDUP_BODY,
          "https://x.example/urgent": RICH_BODY.replace("Lugh", "Ravenna"),
          "https://x.example/explore": RICH_BODY.replace("Lugh", "Trieste"),
          "https://x.example/blocked": None}


def acquire(url):
    """Stands in for the production acquisition path. Keyed by the URL's shape so a test
    can give many seeds distinct URLs (news_seeds.url is UNIQUE) that share one body."""
    for key, body in BODIES.items():
        if url.startswith(key):
            return (body, "USABLE") if body else ("", "SOURCE_ACQUISITION_FAILED")
    return RICH_BODY, "USABLE"


def _assessment(cid, verdict, body, rich="RICH", res="HIGH"):
    quote = " ".join(body.split()[:9])
    return {"id": cid, "concrete_subject": "the thing itself",
            "subject_anchor_quote": quote, "investigable_question": "what is left open",
            "question_basis_quote": quote, "material_richness": rich,
            "researchability": res, "narrative_material": "HIGH",
            "source_shape": "SINGLE_SUBJECT", "specificity": "HIGH",
            "assessment": verdict, "reason": "because the body says so"}


class StubProvider:
    """Verdicts keyed by URL substring, so a test can say what the reader found."""

    def __init__(self, verdicts=None, raise_on_call=False, malformed=False,
                 bad_quote=False, bad_enum=False, drop_ids=False):
        self.verdicts = verdicts or {}
        self.raise_on_call = raise_on_call
        self.malformed = malformed
        self.bad_quote = bad_quote
        self.bad_enum = bad_enum
        self.drop_ids = drop_ids
        self.calls = 0
        self.prompts = []

    def complete(self, system, user, max_tokens=3000, timeout=180, temperature=None):
        self.calls += 1
        self.prompts.append(user)
        if self.raise_on_call:
            raise ProviderError("stub: assessment provider failure")
        if self.malformed:
            return Completion(text="not json", requested_model="m", actual_model="m",
                              provider_label="stub")
        out = []
        for block in user.split("ID: ")[1:]:
            cid = block.split("\n", 1)[0].strip()
            body = block.split("<<<BODY\n", 1)[1].split("\nBODY>>>")[0]
            verdict = next((v for k, v in self.verdicts.items() if k in block),
                           "POSSIBLE_CANDIDATE")   # keys are body/title substrings
            a = _assessment(cid, verdict, body)
            if self.bad_quote:
                a["subject_anchor_quote"] = "a sentence that is nowhere in the body"
            if self.bad_enum:
                a["assessment"] = "PROBABLY_FINE"
            out.append(a)
        if self.drop_ids:
            out = out[:-1]
        return Completion(text=json.dumps({"assessments": out}), requested_model="m",
                          actual_model="m", provider_label="stub")


def _db(seeds):
    """seeds: (id, url, title, class, days_old, score, angle, source_name)"""
    d = pathlib.Path(tempfile.mkdtemp()) / "t.db"
    conn = sqlite3.connect(str(d))
    NF.init_db(conn)
    for col in ("ce_attempt_terminal INTEGER DEFAULT 0", "ce_retry_after TEXT",
                "ce_attempted_date TEXT"):
        try:
            conn.execute("ALTER TABLE news_seeds ADD COLUMN %s" % col)
        except sqlite3.OperationalError:
            pass
    for sid, url, title, cls, age, score, angle, pub in seeds:
        day = (NOW - timedelta(days=age)).strftime("%Y-%m-%d")
        conn.execute(
            "INSERT INTO news_seeds (id,url,title,summary,source_name,source_tier,"
            "pub_date,fetched_date,relevance_score,themes,disability_angle,used,"
            "material_class) VALUES (?,?,?,?,?,1,?,?,?,'[]',?,0,?)",
            (sid, url, title, title, pub, day, day, score, angle, cls))
    conn.commit()
    return conn


def _run(conn, provider, **kw):
    return SV.run_shadow(conn, provider, acquire=acquire, score_item=NF.score_item,
                         boosters=NF.DISABILITY_BOOSTERS, now=NOW, **kw)


# ── flag ──────────────────────────────────────────────────────────────────────
def test_shadow_is_off_by_default():
    os.environ.pop(SV.SHADOW_ENV, None)
    check("OFF when unset", SV.enabled() is False)
    for v in ("0", "off", "false", "", "no", "later"):
        os.environ[SV.SHADOW_ENV] = v
        check("stays OFF for %r" % v, SV.enabled() is False)
    os.environ[SV.SHADOW_ENV] = "1"
    check("ON only when explicitly set", SV.enabled() is True)
    os.environ.pop(SV.SHADOW_ENV, None)


# ── exposure ──────────────────────────────────────────────────────────────────
def test_exposure_is_three_streams_not_the_score():
    seeds = [("hi%d" % i, "https://x.example/rich?%d" % i, "accessible design study %d" % i,
              MP.ESSAY_OPINION, 5, 0.9, None, "BigPub") for i in range(8)]
    seeds += [("urgent", "https://x.example/urgent", "a quiet local story",
               MP.CURRENT_NEWS, 3, 0.05, None, "SmallPub")]
    seeds += [("low%d" % i, "https://x.example/explore?%d" % i, "a sparse concrete piece %d" % i,
               MP.EVERGREEN, 40, 0.05, None, "TinyPub") for i in range(20)]
    conn = _db(seeds)
    pool = SV.eligible_pool(conn, NOW)
    picked = SV.select_candidates(pool, now=NOW, score_item=NF.score_item,
                                  boosters=NF.DISABILITY_BOOSTERS)
    via = {p["row"]["id"]: p["exposed_via"] for p in picked}
    check("about a dozen candidates, bounded", len(picked) <= SV.DAILY_CANDIDATES)
    check("the near-expiry news item is exposed", "urgent" in via, via)
    check("it came in on urgency, not score", via.get("urgent") == "urgency", via)
    check("low-score material reaches evaluation", any(k.startswith("low") for k in via), via)
    check("exploration is deterministic across runs",
          [p["row"]["id"] for p in picked]
          == [p["row"]["id"] for p in SV.select_candidates(
              pool, now=NOW, score_item=NF.score_item, boosters=NF.DISABILITY_BOOSTERS)])
    check("no material-class quota exists in the module",
          "quota" not in (HERE / "selector_v2.py").read_text().lower().replace(
              "no material-class quotas", "").replace("no quota", ""))


def test_v2_ignores_disability_angle_and_the_keyword_booster():
    src = (HERE / "selector_v2.py").read_text()
    body = src[src.index("def select_candidates"):src.index("def rank(")]
    for banned in ("disability_angle", "angle_checked"):
        check("exposure and ranking never read %s" % banned, banned not in body)
    # the booster is neutralised in the theme signal, and production is left alone
    before = list(NF.DISABILITY_BOOSTERS)
    plain = SV.theme_signal("a study of cities", "urban policy", NF.score_item,
                            NF.DISABILITY_BOOSTERS)
    boosted_title = "an accessible wheelchair braille study of cities"
    with_terms = SV.theme_signal(boosted_title, "urban policy", NF.score_item,
                                 NF.DISABILITY_BOOSTERS)
    real, _ = NF.score_item({"title": boosted_title, "summary": "urban policy"})
    check("the production scorer still applies its booster", real > with_terms, (real, with_terms))
    check("the shadow theme signal does not", with_terms <= plain + 0.001, (plain, with_terms))
    check("the production booster list is restored", NF.DISABILITY_BOOSTERS == before)


# ── publisher repetition ──────────────────────────────────────────────────────
def test_publisher_repetition_is_soft_and_decays():
    recent = [("Dezeen", NOW.strftime("%Y-%m-%d")),
              ("Aeon", (NOW - timedelta(days=4)).strftime("%Y-%m-%d")),
              ("Nature", (NOW - timedelta(days=9)).strftime("%Y-%m-%d"))]
    today, _ = SV.publisher_penalty(recent, "Dezeen", NOW)
    mid, _ = SV.publisher_penalty(recent, "Aeon", NOW)
    old, _ = SV.publisher_penalty(recent, "Nature", NOW)
    never, _ = SV.publisher_penalty(recent, "Hyperallergic", NOW)
    check("selected today gets the largest penalty", today == SV.PUBLISHER_PENALTY_MAX, today)
    check("it decays with age", 0 < mid < today, (mid, today))
    check("it is gone after a week", old == 0.0, old)
    check("an unselected publisher is untouched", never == 0.0, never)
    check("the penalty is small enough to be overridden by material",
          SV.PUBLISHER_PENALTY_MAX <= 0.5)
    # behavioural, not textual: the penalty is a number that orders, never a filter
    check("the penalty is a bounded number, never an exclusion",
          isinstance(today, float) and 0 <= today <= SV.PUBLISHER_PENALTY_MAX)
    many = [("Dezeen", NOW.strftime("%Y-%m-%d"))] * 20
    check("repeated recent use does not compound into a ban",
          SV.publisher_penalty(many, "Dezeen", NOW)[0] == SV.PUBLISHER_PENALTY_MAX)


def test_a_repeated_publisher_still_wins_on_better_material():
    conn = _db([("a", "https://x.example/rich", "one", MP.CULTURE, 1, 0.5, None, "Dezeen"),
                ("b", "https://x.example/thin", "two", MP.CULTURE, 1, 0.5, None, "Other")])
    conn.execute("UPDATE news_seeds SET ce_attempted_date = ? WHERE id='a'",
                 (NOW.strftime("%Y-%m-%dT09:00:00"),))
    conn.commit()
    out = _run(conn, StubProvider({"Phreatichthys": "STRONG_CANDIDATE", "Lebowitz": "WEAK_CANDIDATE"}))
    check("the recently-used publisher still wins with stronger material",
          out["shadow_winner"]["seed_id"] == "a", out["shadow_winner"])
    check("and its penalty is recorded rather than hidden",
          out["shadow_winner"]["publisher_penalty"] > 0)


# ── acquisition ───────────────────────────────────────────────────────────────
def test_acquisition_failure_is_not_weak_material():
    conn = _db([("blocked", "https://x.example/blocked", "a blocked source",
                 MP.CULTURE, 1, 0.9, None, "Dezeen"),
                ("ok", "https://x.example/rich", "a readable source",
                 MP.CULTURE, 1, 0.1, None, "Other")])
    out = _run(conn, StubProvider({"Phreatichthys": "POSSIBLE_CANDIDATE"}))
    fails = out["acquisition_failures"]
    check("the unreadable source is recorded as an acquisition failure",
          len(fails) == 1 and fails[0]["assessment_status"] == SV.ACQUISITION_FAILED, fails)
    check("it is NOT called weak material",
          all(f["assessment_status"] != "WEAK_CANDIDATE" for f in fails))
    check("it is not assessed at all",
          all(r["seed_id"] != "blocked" for r in out["records"]))
    check("and it cannot win", out["shadow_winner"]["seed_id"] == "ok")


def test_production_acquisition_is_injected_not_reimplemented():
    import ast
    tree = ast.parse((HERE / "selector_v2.py").read_text())
    imports = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imports |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            imports.add(n.module.split(".")[0])
    check("the shadow imports nothing that can fetch",
          not (imports & {"urllib", "requests", "curl_cffi", "socket", "http"}), imports)
    src = (HERE / "selector_v2.py").read_text()
    check("acquisition is a required injected callable",
          "def run_shadow(conn, provider, *, acquire," in src)


# ── assessment validity ───────────────────────────────────────────────────────
def test_invalid_assessments_fail_closed_and_cannot_win():
    for label, provider in (
            ("non-verbatim quote", StubProvider({"Phreatichthys": "STRONG_CANDIDATE"}, bad_quote=True)),
            ("unknown enum", StubProvider({"Phreatichthys": "STRONG_CANDIDATE"}, bad_enum=True)),
            ("unparseable reply", StubProvider(malformed=True)),
            ("provider failure", StubProvider(raise_on_call=True)),
            ("missing id in reply", StubProvider(drop_ids=True))):
        conn = _db([("a", "https://x.example/rich", "one", MP.CULTURE, 1, 0.5, None, "P1")])
        out = _run(conn, provider)
        statuses = {r["assessment_status"] for r in out["records"]}
        check("%s: not recorded as OK" % label, SV.OK not in statuses, statuses)
        check("%s: nothing invalid becomes WEAK_CANDIDATE" % label,
              all(r.get("assessment") != "WEAK_CANDIDATE" for r in out["records"]
                  if r["assessment_status"] != SV.OK))
        check("%s: cannot win" % label, out["shadow_winner"] is None, out["shadow_winner"])
        check("%s: the failure is persisted for audit" % label,
              conn.execute("SELECT COUNT(*) FROM %s WHERE assessment_status != ?"
                           % SV.TABLE, (SV.OK,)).fetchone()[0] >= 1)


# ── cache ─────────────────────────────────────────────────────────────────────
def test_unchanged_source_is_not_reassessed_and_changed_source_is():
    conn = _db([("a", "https://x.example/rich", "one", MP.CULTURE, 1, 0.5, None, "P1")])
    p1 = StubProvider({"Phreatichthys": "STRONG_CANDIDATE"})
    _run(conn, p1)
    check("first run assesses", p1.calls == 1, p1.calls)
    p2 = StubProvider({"Phreatichthys": "STRONG_CANDIDATE"})
    out2 = _run(conn, p2)
    check("second run on unchanged bytes spends nothing", p2.calls == 0, p2.calls)
    check("and still produces a winner from cache",
          out2["shadow_winner"]["seed_id"] == "a" and out2["shadow_winner"]["cached"])
    BODIES["https://x.example/rich"] = RICH_BODY + "\n\nA correction was added."
    try:
        p3 = StubProvider({"Phreatichthys": "POSSIBLE_CANDIDATE"})
        out3 = _run(conn, p3)
        check("a materially changed source is reassessed", p3.calls == 1, p3.calls)
        check("the new assessment is used", out3["shadow_winner"]["assessment"]
              == "POSSIBLE_CANDIDATE")
        rows = conn.execute("SELECT COUNT(*) FROM %s WHERE seed_id='a'" % SV.TABLE).fetchone()[0]
        check("both assessments are kept, keyed by content hash", rows == 2, rows)
    finally:
        BODIES["https://x.example/rich"] = RICH_BODY
    bad = StubProvider({"Phreatichthys": "STRONG_CANDIDATE"}, bad_quote=True)
    conn2 = _db([("b", "https://x.example/thin", "two", MP.CULTURE, 1, 0.5, None, "P1")])
    _run(conn2, bad)
    again = StubProvider({"Lebowitz": "STRONG_CANDIDATE"})
    _run(conn2, again)
    check("an invalid assessment is never cached as a judgment", again.calls == 1, again.calls)


# ── ordering ──────────────────────────────────────────────────────────────────
def test_ordering_is_material_first_and_explainable():
    conn = _db([("weakhi", "https://x.example/thin", "a prize announcement",
                 MP.ESSAY_OPINION, 1, 0.95, "an angle exists", "P1"),
                ("strongloc", "https://x.example/rich", "a cave fish",
                 MP.ESSAY_OPINION, 1, 0.05, None, "P2"),
                ("roundup", "https://x.example/roundup", "school shows",
                 MP.CULTURE, 1, 0.9, "an angle exists", "P3")])
    out = _run(conn, StubProvider({"Phreatichthys": "STRONG_CANDIDATE",
                                   "Lebowitz": "WEAK_CANDIDATE",
                                   "School Shows": "POSSIBLE_CANDIDATE"}))
    order = [r["seed_id"] for r in out["records"] if r["assessment_status"] == SV.OK]
    check("strong low-score material wins over weak high-score material",
          order[0] == "strongloc", order)
    check("the high-score weak candidate is last", order[-1] == "weakhi", order)
    w = out["shadow_winner"]
    for field in ("exposed_via", "assessment", "material_richness", "researchability",
                  "publisher_penalty", "theme_signal", "shadow_rank",
                  "legacy_relevance_score", "legacy_disability_angle"):
        check("the winner explains its %s" % field, field in w, sorted(w))
    check("a disability_angle is shown but did not decide",
          w["legacy_disability_angle"] is False and w["seed_id"] == "strongloc")
    check("deterministic source features are recorded",
          all(k in w for k in ("body_words", "paragraph_count", "det_roundup",
                               "det_promotional")))
    rd = next(r for r in out["records"] if r["seed_id"] == "roundup")
    check("a roundup is flagged as a feature, not rejected",
          rd["det_roundup"] is True and rd["assessment_status"] == SV.OK)


# ── authority ─────────────────────────────────────────────────────────────────
def test_shadow_cannot_touch_production():
    import inspect
    from orchestrator import discovery
    conn = _db([("a", "https://x.example/rich", "one", MP.CULTURE, 1, 0.5, "angle", "P1"),
                ("b", "https://x.example/thin", "two", MP.CULTURE, 1, 0.9, "angle", "P2")])
    before = [tuple(r) for r in conn.execute(
        "SELECT id, disability_angle, angle_checked, used, relevance_score "
        "FROM news_seeds ORDER BY id")]
    out = _run(conn, StubProvider({"Phreatichthys": "STRONG_CANDIDATE", "Lebowitz": "WEAK_CANDIDATE"}),
               old_winner={"id": "b", "title": "two"})
    after = [tuple(r) for r in conn.execute(
        "SELECT id, disability_angle, angle_checked, used, relevance_score "
        "FROM news_seeds ORDER BY id")]
    check("news_seeds is not modified at all", before == after, (before, after))
    check("the shadow wrote only its own table",
          {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
          >= {SV.TABLE, "news_seeds"})
    check("the old winner is reported, not replaced",
          out["old_authoritative_winner"]["id"] == "b")
    check("the shadow winner differs and says so",
          out["shadow_winner"]["seed_id"] == "a" and out["same_winner"] is False)
    check("the report declares it has no authority", "NONE" in out["authority"])
    src = (HERE / "selector_v2.py").read_text()
    code = [n for n in src.splitlines() if not n.strip().startswith("#")]
    joined = "\n".join(code)
    for banned in ("get_news_seed_with_usable_source", "run_scheduled",
                   "production_orchestrator", "_posts", "_drafts", "mark_news_seed",
                   "new_engine_v1.runner", "commit_to_git"):
        check("the shadow cannot reach %s" % banned, banned not in joined)
    check("discovery.py's authoritative selection does not import the shadow",
          "selector_v2" not in inspect.getsource(discovery))


def test_bounds_are_declared():
    for name, v, ceiling in (("DAILY_CANDIDATES", SV.DAILY_CANDIDATES, 20),
                             ("BATCH_SIZE", SV.BATCH_SIZE, 6),
                             ("BATCH_MAX_CHARS", SV.BATCH_MAX_CHARS, 60_000),
                             ("BATCH_MAX_TOKENS", SV.BATCH_MAX_TOKENS, 4_000),
                             ("MAX_CALLS_PER_RUN", SV.MAX_CALLS_PER_RUN, 10),
                             ("BODY_WORDS_TO_MODEL", SV.BODY_WORDS_TO_MODEL, 3_000)):
        check("%s bounded (%s)" % (name, v), 0 < v <= ceiling)
    conn = _db([("s%d" % i, "https://x.example/rich?%d" % i, "t%d" % i, MP.CULTURE, 1, 0.5, None,
                 "P%d" % i) for i in range(12)])
    p = StubProvider({"Phreatichthys": "POSSIBLE_CANDIDATE"})
    out = _run(conn, p)
    check("12 candidates cost at most 4 calls at batch size 3", p.calls <= 4, p.calls)
    check("and never more than the ceiling", p.calls <= SV.MAX_CALLS_PER_RUN)
    check("metrics report the spend", out["metrics"]["model_calls"] == p.calls)


def main():
    for fn in (test_shadow_is_off_by_default,
               test_exposure_is_three_streams_not_the_score,
               test_v2_ignores_disability_angle_and_the_keyword_booster,
               test_publisher_repetition_is_soft_and_decays,
               test_a_repeated_publisher_still_wins_on_better_material,
               test_acquisition_failure_is_not_weak_material,
               test_production_acquisition_is_injected_not_reimplemented,
               test_invalid_assessments_fail_closed_and_cannot_win,
               test_unchanged_source_is_not_reassessed_and_changed_source_is,
               test_ordering_is_material_first_and_explainable,
               test_shadow_cannot_touch_production,
               test_bounds_are_declared):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL SELECTOR V2 SHADOW TESTS PASSED")


if __name__ == "__main__":
    main()
