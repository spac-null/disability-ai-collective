#!/usr/bin/env python3
"""
current_engine_direct_publication_test.py -- CURRENT_ENGINE publishes what it accepted,
and nothing gets a second vote on it.

WHAT CHANGED (2026-09-07). CURRENT_ENGINE used to compose an article, accept it, stamp
publication_eligible: true -- and then drop it into a seven-day pool where publish_best
scored it against other drafts on editorial score, topic freshness and persona rotation,
and re-derived its eligibility from front-matter fields. Thirteen scheduled runs
produced zero publications. Two of the reasons were mechanical (fixed in the commit
before this one); the third is that publication ownership was in the wrong place.

It is now: this engine owns editorial eligibility, and an ACCEPT that the bridge marked
eligible is handed straight to publish_best.publish_candidate -- by path, exactly once,
with no pool, no score and no comparison. publish_best owns publication MECHANICS, and
its every-two-days cron is the legacy/manual backlog only.

These tests prove the ownership, not the composition. Offline: temp git repos, temp
evidence roots, a recorded publisher, a fake gen_images and a fake art director. No
network, no provider, no images.

USAGE: python3 automation/current_engine_direct_publication_test.py
"""
from __future__ import annotations

import ast
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import types
from datetime import datetime, timedelta

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import publish_best as PB                                            # noqa: E402
import publication_audit as PA                                       # noqa: E402
import publication_audit_test as PAT                                 # noqa: E402
import publication_retention_feasibility_test as RFT                 # noqa: E402

FAILURES: list = []


def check(label, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- " + str(detail)[:240]))
    if not ok:
        FAILURES.append(label)


# ── fixtures ────────────────────────────────────────────────────────────────────────

def _git(repo, *args):
    return subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True)


def _out(repo, *args):
    r = _git(repo, *args)
    if r.returncode != 0:
        raise RuntimeError("git %s: %s" % (" ".join(args), r.stderr[:200]))
    return r.stdout.strip()


def _repo() -> pathlib.Path:
    root = pathlib.Path(tempfile.mkdtemp(prefix="direct-publication-"))
    (root / "_drafts" / "_archive").mkdir(parents=True)
    (root / "_posts").mkdir()
    _out(root, "init", "-q", "-b", "main")
    _out(root, "config", "user.email", "test@example.org")
    _out(root, "config", "user.name", "Test")
    (root / "README.md").write_text("seed\n")
    _out(root, "add", "README.md")
    _out(root, "commit", "-q", "-m", "init")
    PB.REPO, PB.DRAFTS, PB.POSTS, PB.ARCHIVE = (
        root, root / "_drafts", root / "_posts", root / "_drafts" / "_archive")
    return root


def _candidate(root, name, run_id, *, day_offset=0, extra="", drop=()):
    """A CURRENT_ENGINE candidate as persist_candidate leaves one: untracked, in
    _drafts, carrying the terminal stamps."""
    day = (datetime.now() - timedelta(days=day_offset)).strftime("%Y-%m-%d")
    text = (PAT.POST.replace(PAT.RUN_ID, run_id)
                    .replace("date: 2026-09-06", "date: %s" % day)
                    .replace('title: "A pavilion on six columns"', 'title: "%s"' % name))
    for field in drop:
        text = "\n".join(l for l in text.splitlines()
                         if not l.startswith("%s:" % field)) + "\n"
    if extra:
        text = text.replace("---\nlayout:", "---\n%s\nlayout:" % extra, 1)
    p = root / "_drafts" / ("%s-%s.md" % (day, name))
    p.write_text(text, encoding="utf-8")
    return p


def _legacy_draft(root, name, day_offset=1, verified=True):
    day = (datetime.now() - timedelta(days=day_offset)).strftime("%Y-%m-%d")
    gate = ("fact_check_status: verified\npublication_safety_version: 1\n"
            if verified else "")
    p = root / "_drafts" / ("%s-%s.md" % (day, name))
    p.write_text('---\nlayout: "post"\ntitle: "%s"\nauthor: "Maya Flux"\ndate: "%s"\n%s'
                 '---\n\nA legacy body.\n' % (name, day, gate), encoding="utf-8")
    return p


class Env:
    """Temp evidence root + audit store + recorded art director + fake illustrator."""

    def __init__(self, root, run_ids=(), ad_result=None):
        self.root = root
        self.ev = root / ".evidence"
        self.store = root / ".store"
        for rid in run_ids:
            RFT.build_legacy_composition_run(self.ev, rid)
        self.ad_calls = []
        self.image_calls = []
        self._ad_result = ad_result
        self._saved_env = dict(os.environ)
        self._saved_sp = PB.subprocess

    def __enter__(self):
        os.environ["NEW_ENGINE_EVIDENCE_ROOT"] = str(self.ev)
        os.environ["CRIPMINDS_PUBLICATION_AUDIT_ROOT"] = str(self.store)
        outer = self

        images = types.ModuleType("gen_images")
        images.has_image_field = lambda _t: False

        def illustrate(post_path, **kw):
            outer.image_calls.append(kw)
            return {"ok": True, "assets": [], "figures": kw.get("brief", {}).get(
                "image_count", 0) if isinstance(kw.get("brief"), dict) else 0}
        images.illustrate_post = illustrate
        sys.modules["gen_images"] = images

        ad = types.ModuleType("art_director")

        def art_direct(_provider, _body, **kw):
            outer.ad_calls.append(kw)
            return outer._ad_result
        ad.art_direct = art_direct
        sys.modules["art_director"] = ad

        # A provider object that is never reached by anything but our fake.
        prov = types.ModuleType("new_engine_v1.provider")
        prov.Provider = lambda *a, **k: object()
        sys.modules.setdefault("new_engine_v1.provider", prov)

        self.calls = []
        real_run = subprocess.run

        class _Rec:
            CalledProcessError = subprocess.CalledProcessError
            DEVNULL = subprocess.DEVNULL

            def run(_self, args, **kw):
                outer.calls.append(list(args))
                if args[:2] in (["git", "push"], ["git", "pull"]):
                    return types.SimpleNamespace(returncode=0, stdout="", stderr="")
                return real_run(args, **kw)
        PB.subprocess = _Rec()
        return self

    def __exit__(self, *exc):
        PB.subprocess = self._saved_sp
        sys.modules.pop("gen_images", None)
        sys.modules.pop("art_director", None)
        os.environ.clear()
        os.environ.update(self._saved_env)
        return False


def brief(n):
    return {"image_count": n, "images": [], "visual_context_used": False}


# ── A. the engine hands over the exact candidate, once ──────────────────────────────
def test_accept_and_eligible_publishes_that_exact_candidate():
    import new_engine_production as NEP
    seen = []
    saved = sys.modules.get("publish_best")
    fake = types.ModuleType("publish_best")
    fake.publish_candidate = lambda p: (seen.append(p), 0)[1]
    sys.modules["publish_best"] = fake
    try:
        orch = types.SimpleNamespace(logger=types.SimpleNamespace(
            info=lambda *a, **k: None, error=lambda *a, **k: None,
            exception=lambda *a, **k: None))
        path = pathlib.Path("/tmp/_drafts/2026-09-07-the-accepted-one.md")
        res = {"status": "accept", "candidate": str(path), "publication_eligible": True}
        out = NEP.publish_if_eligible(orch, "production-r1", path, res)
        check("exactly one publication attempt was made", len(seen) == 1, seen)
        check("and it was handed the exact persisted candidate path",
              seen == [path], seen)
        check("the run records that it published", out["published"] is True)
        check("no scoring, pool or selector entry point was touched",
              not hasattr(fake, "main"), dir(fake))
    finally:
        if saved is not None:
            sys.modules["publish_best"] = saved
        else:
            sys.modules.pop("publish_best", None)


# ── B. an upstream hold publishes nothing at all ────────────────────────────────────
def test_ineligible_makes_no_publication_call():
    import new_engine_production as NEP
    saved = sys.modules.get("publish_best")
    for label, eligible in (("publication_eligible false", False),
                            ("publication_eligible absent", None)):
        seen = []
        fake = types.ModuleType("publish_best")
        fake.publish_candidate = lambda p: (seen.append(p), 0)[1]
        sys.modules["publish_best"] = fake
        try:
            orch = types.SimpleNamespace(logger=types.SimpleNamespace(
                info=lambda *a, **k: None, error=lambda *a, **k: None,
                exception=lambda *a, **k: None))
            res = {"status": "accept", "candidate": "/tmp/x.md"}
            if eligible is not None:
                res["publication_eligible"] = eligible
            out = NEP.publish_if_eligible(orch, "production-r2",
                                          pathlib.Path("/tmp/x.md"), res)
            check("%s -> zero publication calls" % label, seen == [], seen)
            check("%s -> published is false, not absent" % label,
                  out["published"] is False)
        finally:
            sys.modules.pop("publish_best", None)
    if saved is not None:
        sys.modules["publish_best"] = saved


def test_a_publisher_failure_is_mechanical_not_editorial():
    import new_engine_production as NEP
    saved = sys.modules.get("publish_best")
    logged = []
    for label, impl in (
            ("a refusal (rc 1)", lambda p: 1),
            ("a crash", lambda p: (_ for _ in ()).throw(RuntimeError("disk full")))):
        fake = types.ModuleType("publish_best")
        fake.publish_candidate = impl
        sys.modules["publish_best"] = fake
        try:
            orch = types.SimpleNamespace(logger=types.SimpleNamespace(
                info=lambda *a, **k: None,
                error=lambda *a, **k: logged.append(a),
                exception=lambda *a, **k: logged.append(a)))
            res = {"status": "accept", "publication_eligible": True}
            out = NEP.publish_if_eligible(orch, "production-r3",
                                          pathlib.Path("/tmp/y.md"), res)
            check("%s -> published false" % label, out["published"] is False)
            check("%s -> the ACCEPT is not rewritten into a hold" % label,
                  out["status"] == "accept" and out["publication_eligible"] is True)
            check("%s -> it is reported, not swallowed" % label, bool(logged))
        finally:
            sys.modules.pop("publish_best", None)
    if saved is not None:
        sys.modules["publish_best"] = saved


# ── C. terminal authorization: assertions, not a re-audit ───────────────────────────
def test_terminal_authorization_contract():
    root = _repo()
    rid = "production-20260907T090000Z-aaaa1111"
    with Env(root, [rid]) as env:
        good = PB.parse_frontmatter(_candidate(root, "ok", rid).read_text())
        ok, why = PB.terminal_authorization(good)
        check("ACCEPT + eligible + resolvable retainable run is authorized", ok, why)

        legacy = dict(good)
        for k in ("engine_generation", "editorial_engine", "engine_run"):
            legacy.pop(k, None)
        ok, why = PB.terminal_authorization(legacy)
        check("a non-CURRENT_ENGINE article is refused", not ok, why)

        ok, why = PB.terminal_authorization(dict(good, engine_decision="HOLD"))
        check("engine_decision other than ACCEPT is refused", not ok, why)

        for v in (False, "false", "", None, "yes"):
            ok, why = PB.terminal_authorization(dict(good, publication_eligible=v))
            check("publication_eligible=%r is refused" % (v,), not ok, why)
            if not ok:
                check("...and it is named CURRENT_ENGINE_NOT_ELIGIBLE (%r)" % (v,),
                      "CURRENT_ENGINE_NOT_ELIGIBLE" in why, why)

        ok, why = PB.terminal_authorization(dict(good, engine_run="production-nope"))
        check("an unresolvable exact run is refused", not ok, why)
        check("...named as a retention matter, not an editorial one",
              "NEEDS_AUDIT_RETENTION" in why, why)

        # NO SECOND JURY. Strip every field the legacy pool's gates read. The article
        # is still authorized, because the bridge's verdict is the contract.
        stripped = dict(good)
        for k in ("fact_check_status", "fact_check_extraction_status",
                  "fact_check_claims_extracted", "publication_safety_version"):
            stripped.pop(k, None)
        ok, why = PB.terminal_authorization(stripped)
        check("the direct path does not reconstruct fact-check or safety judgement",
              ok, why)
    shutil.rmtree(root, ignore_errors=True)


def test_direct_path_reads_no_editorial_helper():
    """Structural, because 'it did not consult X' is a claim about code, not a run."""
    tree = ast.parse((HERE / "publish_best.py").read_text())
    banned = {"_ordinary_eligibility_ok", "_current_safety_contract_ok",
              "_current_engine_strict_fact_check_missing", "_interlocked",
              "composite_score", "topic_freshness", "persona_score", "bump_attempts",
              "draft_date", "recent_personas", "published_titles_since"}
    for fname in ("terminal_authorization", "publish_candidate", "promote_candidate"):
        fn = next(n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name == fname)
        called = {getattr(n.func, "id", "") or getattr(n.func, "attr", "")
                  for n in ast.walk(fn) if isinstance(n, ast.Call)}
        check("%s consults no editorial or scoring helper" % fname,
              not (called & banned), sorted(called & banned))
        names = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}
        check("%s reads no scoring constant" % fname,
              not (names & {"DEFAULT_SCORE", "AGE_WINDOW_DAYS", "LOSS_BONUS",
                            "LOSS_BONUS_CAP", "PERSONA_WINDOW", "TOPIC_WINDOW_DAYS"}),
              sorted(names & {"DEFAULT_SCORE", "AGE_WINDOW_DAYS", "LOSS_BONUS"}))


# ── D. no second jury, behaviourally ────────────────────────────────────────────────
def test_scoring_inputs_cannot_change_a_direct_publication():
    root = _repo()
    rid = "production-20260907T090000Z-bbbb2222"
    with Env(root, [rid], ad_result={"ok": True, "brief": brief(2), "reason": ""}):
        # Everything the pool would have punished: written eight days ago (outside the
        # window and normally archived), a floor-level editorial score, a persona
        # published moments ago, and a topic already covered today.
        (root / "_posts" / "2026-09-07-same-topic-same-persona.md").write_text(
            '---\nlayout: "post"\ntitle: "A pavilion on six columns"\n'
            'author: "Maya Flux"\ndate: "%s"\n---\n\nAlready published.\n'
            % datetime.now().strftime("%Y-%m-%d"), encoding="utf-8")
        draft = _candidate(root, "the-accepted-article", rid, day_offset=8,
                           extra="draft_score: 0.1\npublish_attempts: 0")
        rc = PB.publish_candidate(draft)
        check("it published despite every scoring signal being against it", rc == 0)
        check("the article is in _posts",
              (root / "_posts" / draft.name).is_file())
        check("and it was not archived by the age window instead",
              not (root / "_drafts" / "_archive" / draft.name).exists())
    shutil.rmtree(root, ignore_errors=True)


# ── E. the legacy cron keeps its pool, and excludes CURRENT_ENGINE ──────────────────
def test_legacy_pool_keeps_working_and_excludes_current_engine():
    root = _repo()
    rid = "production-20260907T090000Z-cccc3333"
    with Env(root, [rid], ad_result=None) as env:
        current = _candidate(root, "an-accepted-current-engine-article", rid)
        old_current = _candidate(root, "a-stale-current-engine-article", rid,
                                 day_offset=30)
        legacy = _legacy_draft(root, "a-legacy-candidate")
        stale_legacy = _legacy_draft(root, "a-stale-legacy-draft", day_offset=30)

        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = PB.main(dry_run=False)
        out = buf.getvalue()

        check("the backlog selector ran", rc == 0, out[-300:])
        check("the CURRENT_ENGINE candidate is skipped by name",
              "CURRENT_ENGINE_DIRECT_PUBLISH_ONLY" in out
              and current.name in out, out[:400])
        check("it was not scored", "%s: editorial=" % current.name not in out)
        check("it stays in _drafts, untouched", current.is_file())
        check("it did not reach _posts", not (root / "_posts" / current.name).exists())
        check("a stale CURRENT_ENGINE draft is not archived either",
              old_current.is_file()
              and not (root / "_drafts" / "_archive" / old_current.name).exists())

        check("the legacy candidate WAS scored", "%s: editorial=" % legacy.name in out,
              out[:400])
        check("and the legacy candidate published",
              (root / "_posts" / legacy.name).is_file())
        check("the stale legacy draft was archived as before",
              (root / "_drafts" / "_archive" / stale_legacy.name).is_file())
    shutil.rmtree(root, ignore_errors=True)


# ── F + G. the mechanics, and exactly one art-direction call ────────────────────────
def test_direct_publication_uses_the_existing_mechanics():
    root = _repo()
    rid = "production-20260907T090000Z-dddd4444"
    with Env(root, [rid], ad_result={"ok": True, "brief": brief(3), "reason": ""}) as env:
        draft = _candidate(root, "a-full-publication", rid)
        rc = PB.publish_candidate(draft)
        dest = root / "_posts" / draft.name

        check("it published", rc == 0)
        check("the date was rewritten to today",
              ("date: %s" % datetime.now().strftime("%Y-%m-%d")) in dest.read_text())
        check("the art director was asked exactly once", len(env.ad_calls) == 1,
              "%d call(s)" % len(env.ad_calls))
        check("gen_images was called exactly once", len(env.image_calls) == 1)
        check("with the brief the art director returned",
              env.image_calls[0].get("brief") == brief(3), env.image_calls)
        check("the exact run was retained at the boundary",
              (root / ".store" / dest.stem / "PUBLICATION.json").is_file())
        man = json.loads((root / ".store" / dest.stem / "PUBLICATION.json").read_text())
        check("the bundle names the article's own run",
              man["provenance"]["engine_run"] == rid, man["provenance"]["engine_run"])
        check("the article was stamped with its audit pointer",
              PA.read_post(dest)[0].get("audit_bundle") == dest.stem)
        check("the destination was staged and committed",
              _git(root, "ls-files", "--error-unmatch", "--",
                   "_posts/%s" % dest.name).returncode == 0)
        check("the vanished untracked source was not handed to git",
              all(str(draft) not in c for c in env.calls if c[:2] == ["git", "add"]),
              env.calls)
        pushed = [c for c in env.calls if c[:2] == ["git", "push"]]
        pulled = [c for c in env.calls if c[:3] == ["git", "pull", "--rebase"]]
        check("it rebased then pushed, exactly as the selector does",
              len(pulled) == 1 and len(pushed) == 1, env.calls)
    shutil.rmtree(root, ignore_errors=True)


def test_zero_images_is_a_successful_publication():
    root = _repo()
    rid = "production-20260907T090000Z-eeee5555"
    with Env(root, [rid], ad_result={"ok": True, "brief": brief(0), "reason": ""}) as env:
        draft = _candidate(root, "an-article-that-wants-no-picture", rid)
        rc = PB.publish_candidate(draft)
        check("image_count 0 is a brief, not a failure", rc == 0)
        check("the art director was still asked once", len(env.ad_calls) == 1)
        check("and its zero-image brief was passed through, not discarded",
              env.image_calls and env.image_calls[0].get("brief") == brief(0),
              env.image_calls)
        check("the article published", (root / "_posts" / draft.name).is_file())
    shutil.rmtree(root, ignore_errors=True)


def test_the_call_site_is_where_it_says_it_is():
    src = (HERE / "new_engine_production.py").read_text()
    tree = ast.parse(src)
    run = next(n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef) and n.name == "run_scheduled")
    sites = [n for n in ast.walk(run) if isinstance(n, ast.Call)
             and getattr(n.func, "id", "") == "publish_if_eligible"]
    check("run_scheduled hands over exactly once", len(sites) == 1,
          "%d site(s)" % len(sites))
    check("and it does so after the candidate is persisted and CANDIDATE.json written",
          src.index("persist_candidate(") < src.index("CANDIDATE.json")
          < src.rindex("publish_if_eligible(orch"))
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "publish_if_eligible")
    calls = [n for n in ast.walk(fn) if isinstance(n, ast.Call)
             and getattr(n.func, "attr", "") == "publish_candidate"]
    check("publish_if_eligible makes at most one publication call and never retries",
          len(calls) == 1
          and not any(isinstance(n, (ast.For, ast.While)) for n in ast.walk(fn)))
    check("the stale 'ACCEPT != PUBLISH / selector owns publication' doctrine is gone",
          "the selector remains the publication owner" not in src)
    check("no scoring symbol is imported or named here",
          not any(w in src for w in ("composite_score", "draft_score", "topic_freshness",
                                     "persona_score", "AGE_WINDOW_DAYS")), src[:0])


def main():
    saved = (PB.REPO, PB.DRAFTS, PB.POSTS, PB.ARCHIVE, PB.subprocess)
    saved_env = dict(os.environ)
    try:
        for fn in (test_accept_and_eligible_publishes_that_exact_candidate,
                   test_ineligible_makes_no_publication_call,
                   test_a_publisher_failure_is_mechanical_not_editorial,
                   test_terminal_authorization_contract,
                   test_direct_path_reads_no_editorial_helper,
                   test_scoring_inputs_cannot_change_a_direct_publication,
                   test_legacy_pool_keeps_working_and_excludes_current_engine,
                   test_direct_publication_uses_the_existing_mechanics,
                   test_zero_images_is_a_successful_publication,
                   test_the_call_site_is_where_it_says_it_is):
            print("\n" + fn.__name__)
            fn()
    finally:
        PB.REPO, PB.DRAFTS, PB.POSTS, PB.ARCHIVE, PB.subprocess = saved
        os.environ.clear()
        os.environ.update(saved_env)

    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        return 1
    print("ALL CURRENT_ENGINE DIRECT PUBLICATION TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
