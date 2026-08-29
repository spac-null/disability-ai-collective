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
import time
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
        self.deadlines = []
        self.prompts = []

    def complete(self, system, user, max_tokens=3000, timeout=180,
                 temperature=None, deadline=None):
        self.deadlines.append(deadline)
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
                         boosters=NF.DISABILITY_BOOSTERS,
                         keyword_matches=NF._keyword_matches, now=NOW, **kw)


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
                                  boosters=NF.DISABILITY_BOOSTERS,
                                  keyword_matches=NF._keyword_matches)
    via = {p["row"]["id"]: p["exposed_via"] for p in picked}
    check("about a dozen candidates, bounded", len(picked) <= SV.DAILY_CANDIDATES)
    check("the near-expiry news item is exposed", "urgent" in via, via)
    check("it came in on urgency, not score", via.get("urgent") == "urgency", via)
    check("low-score material reaches evaluation", any(k.startswith("low") for k in via), via)
    check("exploration is deterministic across runs",
          [p["row"]["id"] for p in picked]
          == [p["row"]["id"] for p in SV.select_candidates(
              pool, now=NOW, score_item=NF.score_item, boosters=NF.DISABILITY_BOOSTERS,
              keyword_matches=NF._keyword_matches)])
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
    before_weights = dict(NF.THEME_WEIGHTS)
    sig = lambda ti, su: SV.theme_signal(ti, su, NF.score_item, NF.DISABILITY_BOOSTERS,
                                         NF._keyword_matches)
    boosted_title = "an accessible wheelchair braille study of cities"
    with_terms = sig(boosted_title, "urban policy")
    real, _ = NF.score_item({"title": boosted_title, "summary": "urban policy"})
    check("the production scorer still applies its booster",
          abs(real - with_terms - SV.BOOSTER_CONTRIBUTION) < 1e-9, (real, with_terms))
    check("the shadow signal is the unboosted value", with_terms < real, (with_terms, real))
    plain_title = "a study of cities"
    plain_real, _ = NF.score_item({"title": plain_title, "summary": "urban policy"})
    check("a text with no booster term is unchanged by the shadow signal",
          abs(sig(plain_title, "urban policy") - plain_real) < 1e-9)
    check("the production booster list was never mutated", NF.DISABILITY_BOOSTERS == before)
    check("no production scoring global was mutated", NF.THEME_WEIGHTS == before_weights)


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
    check("one candidate per call, so 12 candidates want 12 calls",
          out["metrics"]["candidates"] == 12)
    check("but the run stops at the ceiling", p.calls == SV.MAX_CALLS_PER_RUN, p.calls)
    check("metrics report the spend", out["metrics"]["model_calls"] == p.calls)
    check("the surplus is recorded, not silently dropped",
          out["metrics"]["over_call_budget"] == 2, out["metrics"])
    over = [r for r in out["records"]
            if r["assessment_status"] == SV.NOT_ASSESSED_CALL_BUDGET]
    check("and recorded as unassessed, never as weak material", len(over) == 2, over)
    check("nothing over budget can win",
          all(r.get("shadow_rank") is None for r in over))
    check("the winner came from within budget",
          out["shadow_winner"]["assessment_status"] == SV.OK)



def test_no_production_global_is_mutated_even_transiently():
    """A shadow that clears a production list and restores it in a finally block is not
    observationally isolated -- a raise or a concurrent caller between those two lines
    would be a real production bug caused by an experiment. The theme signal is pure."""
    src = (HERE / "selector_v2.py").read_text()
    for pattern in (".clear()", ".extend(", ".append(", ".pop(", "setattr(", "globals()"):
        offenders = [ln.strip() for ln in src.splitlines()
                     if pattern in ln and "booster" in ln.lower()]
        check("no %s on the booster list anywhere" % pattern, not offenders, offenders)
    # and behaviourally: a scoring call inside the shadow leaves the globals identical
    before_b, before_w = list(NF.DISABILITY_BOOSTERS), dict(NF.THEME_WEIGHTS)
    conn = _db([("a", "https://x.example/rich", "an accessible wheelchair study",
                 MP.CULTURE, 1, 0.5, None, "P1")])
    _run(conn, StubProvider({"Phreatichthys": "STRONG_CANDIDATE"}))
    check("boosters unchanged after a full shadow run", NF.DISABILITY_BOOSTERS == before_b)
    check("theme weights unchanged after a full shadow run", NF.THEME_WEIGHTS == before_w)
    check("the shadow never reassigns a production module attribute",
          "NF." not in src and "news_fetcher" not in src)


def test_cache_hash_covers_the_whole_source_not_the_model_slice():
    """If a source changes past the 1,100 words the assessor sees, the cache must still
    know the source changed."""
    # Deliberately past BODY_WORDS_TO_MODEL: the point of the test is a change the
    # assessor's window cannot see, so the body has to be longer than that window.
    long_body = RICH_BODY + ("\n\nTail section beyond the assessor's window. "
                             * (SV.BODY_WORDS_TO_MODEL // 2))
    BODIES["https://x.example/long"] = long_body
    try:
        conn = _db([("a", "https://x.example/long", "one", MP.CULTURE, 1, 0.5, None, "P1")])
        p1 = StubProvider({"Phreatichthys": "STRONG_CANDIDATE"})
        out1 = _run(conn, p1)
        sha1 = out1["records"][0]["source_sha256"]
        prompt_words = len(p1.prompts[0].split())
        check("the model saw a truncated slice",
              prompt_words < len(long_body.split()), prompt_words)
        # change ONLY the tail, far beyond the model's window
        BODIES["https://x.example/long"] = long_body + "\n\nA correction was appended."
        p2 = StubProvider({"Phreatichthys": "POSSIBLE_CANDIDATE"})
        out2 = _run(conn, p2)
        check("a change outside the model window changes the cache hash",
              out2["records"][0]["source_sha256"] != sha1)
        check("and it is reassessed rather than served from cache", p2.calls == 1, p2.calls)
        check("the hash is of the acquired body, not of the prompt or the title",
              sha1 == __import__("hashlib").sha256(long_body.encode()).hexdigest())
    finally:
        BODIES.pop("https://x.example/long", None)


def test_flag_off_means_nothing_happens():
    """The runtime hook is the flag; with it off there is no fetch, no call, no write."""
    os.environ.pop(SV.SHADOW_ENV, None)
    check("enabled() is the only gate and it is off", SV.enabled() is False)
    fetches = []

    def counting_acquire(url):
        fetches.append(url)
        return acquire(url)

    conn = _db([("a", "https://x.example/rich", "one", MP.CULTURE, 1, 0.5, None, "P1")])
    p = StubProvider({"Phreatichthys": "STRONG_CANDIDATE"})
    if SV.enabled():                      # exactly what a caller must do
        SV.run_shadow(conn, p, acquire=counting_acquire, score_item=NF.score_item,
                      boosters=NF.DISABILITY_BOOSTERS,
                      keyword_matches=NF._keyword_matches, now=NOW)
    check("no fetch happened", fetches == [])
    check("no model call happened", p.calls == 0)
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    check("no shadow table was even created", SV.TABLE not in tables, tables)



# ── enablement safety (PR #50) ────────────────────────────────────────────────
def test_one_candidate_per_assessment_call():
    """Measured on frozen bytes: a Guardian gallery read POSSIBLE five times out of
    five assessed alone, and WEAK when it shared a prompt with two unrelated
    candidates. The verdict is this selector's primary ordering key, so a seed's rank
    must not depend on which unrelated stories happened to be exposed the same day."""
    check("BATCH_SIZE is 1", SV.BATCH_SIZE == 1, SV.BATCH_SIZE)
    conn = _db([("a", "https://x.example/rich", "one", MP.CULTURE, 1, 0.5, None, "P1"),
                ("b", "https://x.example/thin", "two", MP.CULTURE, 1, 0.5, None, "P2"),
                ("c", "https://x.example/roundup", "three", MP.CULTURE, 1, 0.5, None, "P3")])
    p = StubProvider({"Phreatichthys": "STRONG_CANDIDATE", "Lebowitz": "WEAK_CANDIDATE"})
    out = _run(conn, p)
    check("three candidates cost three calls", p.calls == 3, p.calls)
    for i, prompt in enumerate(p.prompts):
        check("prompt %d carries exactly one candidate" % i,
              prompt.count("ID: ") == 1, prompt.count("ID: "))
        check("prompt %d carries exactly one body" % i,
              prompt.count("<<<BODY") == 1)

    # and the same seed produces the same prompt whatever else is exposed
    conn2 = _db([("a", "https://x.example/rich", "one", MP.CULTURE, 1, 0.5, None, "P1")])
    p2 = StubProvider({"Phreatichthys": "STRONG_CANDIDATE"})
    _run(conn2, p2)
    alone = p2.prompts[0]
    with_others = [q for q in p.prompts if "ID: a" in q.split("\n")[0]][0]
    check("a seed's prompt is identical alone and alongside others",
          alone == with_others, (len(alone), len(with_others)))


def test_the_assessment_contract_is_untouched():
    """Only the batching changed. The question, the schema, the validation, the model
    window and the cache key are the same, or the stability measurements taken before
    this PR would no longer describe what runs after it."""
    src = (HERE / "selector_v2.py").read_text()
    check("model window unchanged", SV.BODY_WORDS_TO_MODEL == 1_100)
    check("temperature 0 is still explicit", "temperature=0" in src)
    check("the schema still names all eleven fields",
          all(f in src for f in ("concrete_subject", "subject_anchor_quote",
                                 "investigable_question", "question_basis_quote",
                                 "material_richness", "researchability",
                                 "narrative_material", "source_shape", "specificity",
                                 "assessment", "reason")))
    check("validation still requires both quotes verbatim",
          "not verbatim in the source body" in src)
    check("the cache key is still (seed_id, full-source sha256)",
          "PRIMARY KEY (seed_id, source_sha256)" in src
          and 'sha = hashlib.sha256(text.encode("utf-8")).hexdigest()' in src)
    check("the assessment question is unchanged",
          "is there enough concrete reality in this source to justify researching" in src)


def test_the_acquisition_budget_stops_fetching_and_says_so():
    """One fetch is hard-bounded now, but twelve in a row still add up, and this runs
    before the authoritative article work."""
    seeds = [("s%d" % i, "https://x.example/rich?%d" % i, "t%d" % i, MP.CULTURE, 1,
              0.5, None, "P%d" % i) for i in range(6)]
    conn = _db(seeds)
    fetched = []

    def slow(url):
        fetched.append(url)
        time.sleep(0.4)
        return acquire(url)

    real = SV.ACQUISITION_BUDGET_SECONDS
    SV.ACQUISITION_BUDGET_SECONDS = 1.0
    try:
        out = SV.run_shadow(conn, StubProvider({"Phreatichthys": "STRONG_CANDIDATE"}),
                            acquire=slow, score_item=NF.score_item,
                            boosters=NF.DISABILITY_BOOSTERS,
                            keyword_matches=NF._keyword_matches, now=NOW)
    finally:
        SV.ACQUISITION_BUDGET_SECONDS = real
    check("it stopped fetching before the end of the exposure set",
          0 < len(fetched) < 6, len(fetched))
    check("the exposure set itself is unchanged", out["metrics"]["candidates"] == 6)
    check("the unattempted candidates are recorded",
          out["metrics"]["not_attempted"] == 6 - len(fetched), out["metrics"])
    check("with an explicit budget status, never a material verdict",
          all(r["assessment_status"] == SV.NOT_ATTEMPTED_ACQUISITION_BUDGET
              for r in out["not_attempted"]), out["not_attempted"][:1])
    check("their slots were NOT refilled with fresh candidates",
          len(fetched) + out["metrics"]["not_attempted"] == 6)
    check("nothing unattempted can rank",
          all(r["seed_id"] not in {x["seed_id"] for x in out["not_attempted"]}
              for r in out["records"] if r.get("shadow_rank")))
    check("a winner was still found from what was read",
          out["shadow_winner"] is not None)


def test_no_budget_state_is_ever_a_material_verdict():
    """Running out of time or money is not evidence about a source."""
    for status in (SV.NOT_ATTEMPTED_ACQUISITION_BUDGET, SV.NOT_ASSESSED_CALL_BUDGET,
                   SV.ACQUISITION_FAILED):
        check("%s is not a verdict" % status, status not in SV.VERDICTS)
        check("%s is not a richness level" % status, status not in SV.RICHNESS)
    src = (HERE / "selector_v2.py").read_text()
    bad = [l.strip() for l in src.splitlines()
           if "WEAK_CANDIDATE" in l and ("status" in l or "assessment_status" in l)]
    check("no line ever assigns WEAK_CANDIDATE alongside a status", not bad, bad)
    check("only OK assessments are ranked", 'r["assessment_status"] == OK' in src)


def test_flag_off_leaves_authoritative_selection_untouched():
    """Shared acquisition code changed in this PR, so separate the two claims: source
    acquisition may become MORE RELIABLE (that is the point), but which seed the old
    selector reaches for, and in what order, must be bit-identical."""
    disc = (HERE / "orchestrator" / "discovery.py").read_text()
    check("the Priority 1/2 ordering is unchanged",
          disc.count("ORDER BY relevance_score DESC, pub_date DESC") == 2,
          disc.count("ORDER BY relevance_score DESC, pub_date DESC"))
    check("the acquisition retry budget is unchanged",
          "MAX_SOURCE_ACQUISITION_ATTEMPTS = 3" in disc)
    check("the source-usability definition is unchanged",
          "_SOURCE_MIN_USABLE_CHARS = 600" in disc
          and "_SOURCE_MIN_USABLE_PARAGRAPHS = 3" in disc)
    check("relevance scoring is not defined or altered in discovery.py",
          "def score_item" not in disc and "THEME_WEIGHTS = " not in disc)
    check("the production disability booster is still in the production scorer",
          len(NF.DISABILITY_BOOSTERS) > 0)
    # ordering is decided by SQL, before a single byte is fetched -- so a change to
    # acquisition can only change WHETHER a seed's source is usable, never its rank
    # get_news_seed() runs the ordered SQL and returns a seed; only then is anything
    # fetched. So acquisition can change WHETHER that seed's source is usable, and
    # therefore whether the loop moves on, but never the order it considers them in.
    sel = disc.split("def get_news_seed_with_usable_source(")[1].split("\n    def ")[0]
    check("the ordered SQL picks the seed before any fetch",
          sel.index("self.get_news_seed(") < sel.index("text = self.get_source_text("),
          (sel.index("self.get_news_seed("), sel.index("text = self.get_source_text(")))
    check("and the ordering lives in get_news_seed, which this PR did not touch",
          "ORDER BY relevance_score DESC, pub_date DESC" in
          disc.split("def get_news_seed(")[1].split("\n    def ")[0])
    check("discovery.py does not import or enable the shadow",
          "selector_v2" not in disc and SV.SHADOW_ENV not in disc)
    v2 = (HERE / "selector_v2.py").read_text()
    check("the shadow still writes no SQL against news_seeds",
          not any(("UPDATE news_seeds" in l or "INSERT INTO news_seeds" in l)
                  for l in v2.splitlines()))


def test_a_slow_model_stops_the_run_instead_of_overrunning_it():
    """Acquisition being bounded is not enough. Assessment is sequential provider
    calls, and provider.complete tries two legs that would each otherwise get a fresh
    timeout -- so ten candidates could cost an hour while the real 09:00 pipeline
    waits. The run budget has to cover the model work too."""
    seeds = [("s%d" % i, "https://x.example/rich?%d" % i, "t%d" % i, MP.CULTURE, 1,
              0.5, None, "P%d" % i) for i in range(6)]
    conn = _db(seeds)

    class _SlowProvider(StubProvider):
        def complete(self, *a, **kw):
            time.sleep(0.5)
            return super().complete(*a, **kw)

    p = _SlowProvider({"Phreatichthys": "STRONG_CANDIDATE"})
    real_run, real_min = SV.RUN_BUDGET_SECONDS, SV.MIN_ASSESSMENT_SECONDS
    SV.RUN_BUDGET_SECONDS, SV.MIN_ASSESSMENT_SECONDS = 2.0, 0.6
    t0 = time.monotonic()
    try:
        out = _run(conn, p)
    finally:
        SV.RUN_BUDGET_SECONDS, SV.MIN_ASSESSMENT_SECONDS = real_run, real_min
    elapsed = time.monotonic() - t0
    check("it stopped starting calls before the end of the set",
          0 < p.calls < 6, p.calls)
    check("the run stayed inside its budget plus slack (%.1fs <= 2.0s + 1.5s)" % elapsed,
          elapsed <= 3.5, elapsed)
    skipped = [r for r in out["records"]
               if r["assessment_status"] == SV.NOT_ASSESSED_RUN_BUDGET]
    check("the rest are recorded against the run budget",
          len(skipped) == 6 - p.calls, (len(skipped), p.calls))
    check("and the metric says so", out["metrics"]["over_run_budget"] == len(skipped),
          out["metrics"])
    check("a run-budget skip is not a material verdict",
          all(r.get("assessment") is None and r.get("shadow_rank") is None
              for r in skipped))
    check("what was assessed still ranked", out["shadow_winner"] is not None)


def test_one_overlong_call_cannot_outlive_the_remaining_budget():
    """The half that matters. Checking the clock BETWEEN calls is useless if the call
    about to start can run for six minutes on its own, so the run deadline is handed
    to the provider and both of its fallback legs share it."""
    conn = _db([("a", "https://x.example/rich", "one", MP.CULTURE, 1, 0.5, None, "P1")])

    class _HangingProvider(StubProvider):
        def complete(self, *a, deadline=None, **kw):
            self.deadlines.append(deadline)
            self.calls += 1
            # behave like a provider that would run far past the budget, but honour
            # the deadline it was handed -- which is exactly the contract under test
            if deadline is None:
                time.sleep(30)
            time.sleep(max(0.0, min(30.0, deadline - time.monotonic())))
            raise TimeoutError("provider exceeded the shadow deadline")

    p = _HangingProvider()
    real_run, real_min = SV.RUN_BUDGET_SECONDS, SV.MIN_ASSESSMENT_SECONDS
    # low enough that the call IS started -- the point is what happens to a call that
    # has begun, not the between-calls check the previous test covers
    SV.RUN_BUDGET_SECONDS, SV.MIN_ASSESSMENT_SECONDS = 1.5, 0.2
    t0 = time.monotonic()
    try:
        out = _run(conn, p)
    finally:
        SV.RUN_BUDGET_SECONDS, SV.MIN_ASSESSMENT_SECONDS = real_run, real_min
    elapsed = time.monotonic() - t0
    check("the call was actually started", p.calls == 1, p.calls)
    check("and was given an absolute deadline, not a static timeout",
          p.deadlines and p.deadlines[0] is not None, p.deadlines)
    check("the run ended within its budget plus slack (%.1fs <= 1.5s + 1.5s)" % elapsed,
          elapsed <= 3.0, elapsed)
    check("the failure is an assessment error, not a material verdict",
          out["records"][0]["assessment_status"] == SV.ASSESSMENT_ERROR,
          out["records"][0]["assessment_status"])
    check("nothing ranked on a failed call", out["shadow_winner"] is None)


def test_the_provider_shares_one_deadline_across_both_fallback_legs():
    """CLIProxy then OpenRouter, each of which used to get its own fresh timeout, so
    one complete() could cost twice its argument. A deadline cannot be spent twice."""
    import inspect
    from new_engine_v1 import provider as P
    src = inspect.getsource(P)
    check("complete accepts an absolute deadline", "deadline: float | None = None" in src)
    check("it is off by default, so the authoritative pipeline is untouched",
          "deadline=None" in src or "deadline: float | None = None" in src)
    body = src.split("def complete(")[1].split("\ndef ")[0]
    check("each leg is sized from what is LEFT, not from the static timeout",
          "remaining = deadline - time.monotonic()" in body
          and "leg_timeout = max(1, int(min(timeout, remaining)))" in body)
    check("a leg is not started once the deadline has passed",
          "deadline reached before the attempt" in body)
    check("and the deadline itself is handed down to the transport",
          "_post(url, key, payload, leg_timeout, deadline)" in body)
    post = src.split("def _post(")[1].split("\ndef ")[0]
    check("the transport reads under the deadline, not merely a socket timeout",
          "bounded_http.bounded_opener(" in post)
    check("with no deadline the old path is byte-for-byte the old path",
          "urllib.request.urlopen(req, timeout=timeout)" in post)


def test_the_budget_hierarchy_never_sums_past_the_total():
    check("acquisition sub-budget fits inside the run budget",
          SV.ACQUISITION_BUDGET_SECONDS < SV.RUN_BUDGET_SECONDS,
          (SV.ACQUISITION_BUDGET_SECONDS, SV.RUN_BUDGET_SECONDS))
    from orchestrator import discovery as D
    candidate_max = D._SOURCE_LEG_DEADLINE + D._SOURCE_IMPERSONATED_TIMEOUT
    check("acquisition plus one in-flight candidate still fits (%d + %d <= %d)"
          % (SV.ACQUISITION_BUDGET_SECONDS, candidate_max, SV.RUN_BUDGET_SECONDS),
          SV.ACQUISITION_BUDGET_SECONDS + candidate_max <= SV.RUN_BUDGET_SECONDS)
    src = (HERE / "selector_v2.py").read_text()
    check("the acquisition deadline is clamped to the run deadline, not added to it",
          "min(time.monotonic() + ACQUISITION_BUDGET_SECONDS, run_deadline)" in src)
    check("assessment is bounded by the run deadline",
          "assess(provider, prepared, deadline=run_deadline)" in src)


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
               test_bounds_are_declared,
               test_no_production_global_is_mutated_even_transiently,
               test_cache_hash_covers_the_whole_source_not_the_model_slice,
               test_flag_off_means_nothing_happens,
               test_one_candidate_per_assessment_call,
               test_the_assessment_contract_is_untouched,
               test_the_acquisition_budget_stops_fetching_and_says_so,
               test_no_budget_state_is_ever_a_material_verdict,
               test_flag_off_leaves_authoritative_selection_untouched,
               test_a_slow_model_stops_the_run_instead_of_overrunning_it,
               test_one_overlong_call_cannot_outlive_the_remaining_budget,
               test_the_provider_shares_one_deadline_across_both_fallback_legs,
               test_the_budget_hierarchy_never_sums_past_the_total):
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
