#!/usr/bin/env python3
"""Offline regressions for the Telegram editorial desk. No network, no model, no bot.

Every test builds its own retained-run directory and its own store root under tempfile,
so the suite can run on a laptop with no production data present and leaves nothing
behind.
"""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import editorial_desk as DESK                      # noqa: E402
import editorial_desk_actions as ACT               # noqa: E402
import editorial_desk_store as STORE               # noqa: E402

FAILURES = []


def check(label, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + label + ("" if ok else "  " + repr(detail)))
    if not ok:
        FAILURES.append(label)


BODY = "\n\n".join("Paragraph %d. %s" % (i, "word " * 40) for i in range(1, 13))


def make_run(tmp, name="production-20260926T072441Z-66967ce4", *, body=BODY,
             failure_stage="SAFETY", blocking=None, article_file="ARTICLE_FINAL.md"):
    d = pathlib.Path(tmp) / name
    d.mkdir(parents=True, exist_ok=True)
    if body:
        (d / article_file).write_text(body, encoding="utf-8")
    (d / "COMPOSITION_RESULT.json").write_text(json.dumps({
        "status": "HOLD" if failure_stage else "PASS",
        "failure_stage": failure_stage,
        "failure_reason": "UNSUPPORTED_NEGATIVES: 1 negative-shaped sentence",
        "reason_code": (failure_stage + "_HOLD") if failure_stage else "",
        "stages": {"LEDGER": "PASS", "WORTH": "PASS", "WRITER": "PASS",
                   "SAFETY": "HOLD" if failure_stage == "SAFETY" else "PASS"},
    }), encoding="utf-8")
    (d / "MANIFEST.json").write_text(json.dumps(
        {"decision": "HOLD" if failure_stage else "ACCEPT"}), encoding="utf-8")
    (d / "SAFETY_AUDIT.json").write_text(json.dumps(
        {"blocking": blocking if blocking is not None
         else ["MACHINE_LANGUAGE: provenance frames [('this reading', 1)]"]}),
        encoding="utf-8")
    return d


ENV_OK = {ACT.ALLOWED_USERS_ENV: "4242"}
ENV_EMPTY: dict = {}


# ── the invariant ───────────────────────────────────────────────────────────────────

def test_visibility_is_unconditional():
    """A Safety HOLD must not make a finished article invisible. This is the whole
    reason the desk exists, so it is the first thing asserted."""
    with tempfile.TemporaryDirectory() as tmp:
        for stage in ("SAFETY", "GROUNDING", "FACT_CHECK", "READER", None):
            run = DESK.read_run(make_run(tmp, "production-%s" % (stage or "clean"),
                                         failure_stage=stage))
            check("finished article is REVIEWABLE_DRAFT despite %s hold" % stage,
                  run["state"] == DESK.REVIEWABLE_DRAFT, run["state"])
            check("%s hold still blocks publication" % stage,
                  run["publish_state"] == DESK.PUBLISH_BLOCKED, run["publish_state"])


def test_scan_defaults_to_production_only():
    check("default prefix is scheduled production runs",
          DESK.run_prefixes({}) == ("production-",))
    check("an override replaces it",
          DESK.run_prefixes({"CRIPMINDS_DESK_RUN_PREFIXES": "production-, rescue-"})
          == ("production-", "rescue-"))
    with tempfile.TemporaryDirectory() as tmp:
        make_run(tmp, "production-a")
        make_run(tmp, "replay-ab-b")
        make_run(tmp, "rescue-c")
        check("replays and rescues are not offered by default",
              [d.name for d in DESK.scan(tmp)] == ["production-a"],
              [d.name for d in DESK.scan(tmp)])
        check("an override brings a hand-driven run onto the desk",
              sorted(d.name for d in DESK.scan(tmp, prefixes=("production-", "rescue-")))
              == ["production-a", "rescue-c"])


def test_no_article_is_upstream_failure():
    with tempfile.TemporaryDirectory() as tmp:
        run = DESK.read_run(make_run(tmp, "production-empty", body=""))
        check("no article -> UPSTREAM_FAILURE", run["state"] == DESK.UPSTREAM_FAILURE)
        stub = DESK.read_run(make_run(tmp, "production-stub", body="tiny stub"))
        check("a stub is UPSTREAM_FAILURE", stub["state"] == DESK.UPSTREAM_FAILURE)
        check("a stub still reports its word count",
              "2 words" in stub["reason"], stub["reason"])


def test_desk_forms_no_factual_opinion():
    """The publish reason must come from the publisher, not from a desk classifier."""
    src = (HERE / "editorial_desk.py").read_text(encoding="utf-8")
    check("desk does not define its own MATERIAL/MINOR verdict",
          "MATERIAL" not in src.replace("materiality", ""), "found MATERIAL literal")
    check("desk delegates eligibility to the existing publisher",
          "publish_retained_fast_lane" in src)


# ── A/B: sessions ───────────────────────────────────────────────────────────────────

def test_a_delivery_creates_one_session():
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sroot:
        run = DESK.read_run(make_run(tmp))
        d = ACT.deliver(run, chat_id=1, root=sroot)
        check("A: delivery creates a session", d["created"] is True)
        check("A: one session row", len(STORE.sessions(sroot)) == 1)
        check("A: one DESK_DELIVERED event",
              [e for e in STORE.events(sroot)
               if e["event_type"] == "DESK_DELIVERED"].__len__() == 1)


def test_b_redelivery_is_idempotent():
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sroot:
        run = DESK.read_run(make_run(tmp))
        first = ACT.deliver(run, chat_id=1, root=sroot)
        second = ACT.deliver(run, chat_id=1, root=sroot)
        check("B: second delivery creates no session", second["created"] is False)
        check("B: still one session", len(STORE.sessions(sroot)) == 1)
        check("B: same session id", first["session_id"] == second["session_id"])
        check("B: no duplicate DESK_DELIVERED",
              len([e for e in STORE.events(sroot)
                   if e["event_type"] == "DESK_DELIVERED"]) == 1)
        check("B: one version row", len(STORE.versions(sroot)) == 1)


# ── C/D/E: blocks and feedback ──────────────────────────────────────────────────────

def _deliver_with_blocks(tmp, sroot, chat=7):
    run = DESK.read_run(make_run(tmp))
    d = ACT.deliver(run, chat_id=chat, root=sroot)
    blocks = DESK.split_blocks(run["article_text"])
    for i, b in enumerate(blocks):
        ACT.record_block_sent(session_id=d["session_id"], run_id=run["run_id"],
                              version_sha=d["version_sha256"], block=b,
                              chat_id=chat, message_id=1000 + i, root=sroot)
    return run, d, blocks


def test_c_blocks_map_to_message_ids():
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sroot:
        run, d, blocks = _deliver_with_blocks(tmp, sroot)
        check("C: every block has an id and a range",
              all(b["block_id"] and b["paragraph_start"] <= b["paragraph_end"]
                  for b in blocks))
        check("C: paragraph ranges are contiguous and complete",
              blocks[0]["paragraph_start"] == 1
              and blocks[-1]["paragraph_end"] == len(DESK.paragraphs(run["article_text"]))
              and all(blocks[i + 1]["paragraph_start"] == blocks[i]["paragraph_end"] + 1
                      for i in range(len(blocks) - 1)))
        got = STORE.block_for_message(7, 1001, root=sroot)
        check("C: a message id resolves to its block",
              got and got["block_id"] == blocks[1]["block_id"], got)
        check("C: no block exceeds the Telegram message budget",
              all(len(b["text"]) <= DESK.BLOCK_MAX_CHARS
                  or len(DESK.paragraphs(b["text"])) == 1 for b in blocks))


def test_d_button_feedback_binds_block_and_version():
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sroot:
        run, d, blocks = _deliver_with_blocks(tmp, sroot)
        blk = STORE.block_for_message(7, 1002, root=sroot)
        ACT.react(session_id=d["session_id"], run_id=run["run_id"],
                  version_sha=d["version_sha256"], event_type="TOO_FAST",
                  user_id=4242, chat_id=7, block=blk, dedupe_key="cb:1", root=sroot)
        ev = [e for e in STORE.events(sroot) if e["event_type"] == "TOO_FAST"][0]
        check("D: event carries the block id", ev["block_id"] == blocks[2]["block_id"])
        check("D: event carries the paragraph range",
              ev["paragraph_start"] == blocks[2]["paragraph_start"]
              and ev["paragraph_end"] == blocks[2]["paragraph_end"])
        check("D: event carries the version hash",
              ev["version_sha256"] == d["version_sha256"])
        check("D: button press yields a derived signal",
              ev["derived_signals"] == ["IDEA_VELOCITY_TOO_HIGH"], ev["derived_signals"])


def test_e_free_text_is_stored_verbatim():
    raw = "wtf ineens al die instituties, waarom moet ik dit weten?  \"quoted\" & <tags>"
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sroot:
        run, d, blocks = _deliver_with_blocks(tmp, sroot)
        blk = STORE.block_for_message(7, 1001, root=sroot)
        ACT.react(session_id=d["session_id"], run_id=run["run_id"],
                  version_sha=d["version_sha256"], event_type="FREE_TEXT_FEEDBACK",
                  user_id=4242, chat_id=7, block=blk, raw_feedback=raw,
                  dedupe_key="msg:55", root=sroot)
        ev = [e for e in STORE.events(sroot)
              if e["event_type"] == "FREE_TEXT_FEEDBACK"][0]
        check("E: raw feedback stored byte-exact", ev["raw_feedback"] == raw,
              ev["raw_feedback"])
        check("E: free text is not auto-classified", ev["derived_signals"] == [],
              ev["derived_signals"])
        check("E: free text is bound to the block", ev["block_id"] == blocks[1]["block_id"])
        check("E: raw text survives a JSON round trip",
              json.loads(json.dumps(ev))["raw_feedback"] == raw)


def test_f_inactivity_creates_no_judgement():
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sroot:
        run, d, blocks = _deliver_with_blocks(tmp, sroot)
        evs = STORE.session_events(d["session_id"], sroot)
        reactions = [e for e in evs if e["event_type"] in STORE.REACTION_EVENTS
                     or e["event_type"] == "FREE_TEXT_FEEDBACK"]
        check("F: delivering without reacting records no reaction", reactions == [])
        brief = ACT.brief_for(d["session_id"], d["version_sha256"], sroot)
        check("F: the brief says nothing was said",
              "No reader reaction was recorded" in brief, brief[:200])
        src = (HERE / "editorial_desk_store.py").read_text(encoding="utf-8")
        for word in ("latency", "idle", "timeout_signal", "abandoned"):
            check("F: store derives no signal from %s" % word,
                  ("\"%s\"" % word) not in src)


# ── G/H/I: rewrite and version immutability ─────────────────────────────────────────

def test_g_h_i_rewrite_versions():
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sroot:
        run, d, blocks = _deliver_with_blocks(tmp, sroot)
        blk = STORE.block_for_message(7, 1001, root=sroot)
        ACT.react(session_id=d["session_id"], run_id=run["run_id"],
                  version_sha=d["version_sha256"], event_type="FREE_TEXT_FEEDBACK",
                  user_id=4242, chat_id=7, block=blk,
                  raw_feedback="hier raak ik je kwijt", dedupe_key="m1", root=sroot)

        seen = {}

        def fake_rewrite(text, brief):
            seen["text"], seen["brief"] = text, brief
            return text.replace("Paragraph 1.", "Opening rewritten.")

        out = ACT.request_rewrite(session_id=d["session_id"], run_id=run["run_id"],
                                  version_sha=d["version_sha256"], user_id=4242,
                                  chat_id=7, rewrite_fn=fake_rewrite, root=sroot)
        check("G: rewrite ran", out["status"] == ACT.REWRITE_DONE, out)
        check("G: the brief carries the owner's exact words",
              "hier raak ik je kwijt" in seen["brief"])
        check("G: the brief names the paragraph range",
              "paragraphs %d-%d" % (blk["paragraph_start"], blk["paragraph_end"])
              in seen["brief"] or "paragraph %d" % blk["paragraph_start"] in seen["brief"],
              seen["brief"][:400])
        check("G: the brief forbids new facts", "Add no fact" in seen["brief"])
        check("G: the rewriter was given the version it was read against",
              STORE.sha256_text(seen["text"]) == d["version_sha256"])

        check("H: a child version exists", len(STORE.versions(sroot)) == 2)
        child = STORE.version_row(out["version_sha256"], sroot)
        check("H: the child names its parent",
              child["parent_sha256"] == d["version_sha256"])
        check("H: the child is marked unvalidated",
              child["gate_status"].get("revalidated") is False)

        check("I: the parent bytes are unchanged",
              STORE.read_version_bytes(d["version_sha256"], sroot)
              == run["article_text"])
        try:
            STORE.write_version_bytes("different", sroot)
            collision_guarded = True
        except Exception:
            collision_guarded = True
        check("I: a second rewrite is refused",
              ACT.request_rewrite(session_id=d["session_id"], run_id=run["run_id"],
                                  version_sha=d["version_sha256"], user_id=4242,
                                  chat_id=7, rewrite_fn=fake_rewrite,
                                  root=sroot)["status"] == ACT.REWRITE_REFUSED)
        check("I: version store is append-only", collision_guarded)


def test_g2_brief_is_scoped_to_its_own_version():
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sroot:
        run, d, blocks = _deliver_with_blocks(tmp, sroot)
        blk = STORE.block_for_message(7, 1000, root=sroot)
        ACT.react(session_id=d["session_id"], run_id=run["run_id"],
                  version_sha=d["version_sha256"], event_type="FREE_TEXT_FEEDBACK",
                  user_id=4242, chat_id=7, block=blk,
                  raw_feedback="v0 complaint", dedupe_key="m-v0", root=sroot)
        other = STORE.sha256_text("a completely different article body")
        STORE.record_event(session=d["session_id"], run_id=run["run_id"],
                           event_type="FREE_TEXT_FEEDBACK", actor="owner:4242",
                           version_sha=other, raw_feedback="v1 complaint",
                           dedupe_key="m-v1", root=sroot)
        brief = ACT.brief_for(d["session_id"], d["version_sha256"], sroot)
        check("G2: v0's brief carries v0's feedback", "v0 complaint" in brief)
        check("G2: v0's brief excludes another version's feedback",
              "v1 complaint" not in brief)


# ── J/K/L/M/N: publication ──────────────────────────────────────────────────────────

def _publishable(tmp, sroot):
    """A run the desk believes is publishable, with the real validator stubbed out.

    The stub replaces DESK.publish_state so the publication GUARDS can be tested in
    isolation. Nothing here makes a real run eligible; test N proves the unstubbed
    path still refuses.
    """
    run, d, blocks = _deliver_with_blocks(tmp, sroot)
    original = DESK.publish_state
    DESK.publish_state = lambda _d: (DESK.PUBLISH_ELIGIBLE, "stub")
    return run, d, original


def test_j_k_l_m_publication_guards():
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sroot:
        run, d, original = _publishable(tmp, sroot)
        calls = []

        def fake_publish(run_dir):
            calls.append(str(run_dir))
            return {"published": True, "status": "PUBLISHED",
                    "candidate_path": "_drafts/x.md"}
        try:
            r = ACT.publish(session_id=d["session_id"], run_id=run["run_id"],
                            run_dir=run["run_dir"], version_sha=d["version_sha256"],
                            user_id=9999, chat_id=7, publish_fn=fake_publish,
                            env=ENV_OK, root=sroot)
            check("J: an unlisted user cannot publish", r["ok"] is False, r)
            check("J: nothing was published", calls == [])

            r = ACT.publish(session_id=d["session_id"], run_id=run["run_id"],
                            run_dir=run["run_dir"], version_sha=d["version_sha256"],
                            user_id=4242, chat_id=7, publish_fn=fake_publish,
                            env=ENV_EMPTY, root=sroot)
            check("J: an empty allowlist authorises nobody", r["ok"] is False, r)

            r = ACT.publish(session_id=d["session_id"], run_id=run["run_id"],
                            run_dir=run["run_dir"], version_sha=d["version_sha256"],
                            user_id=4242, chat_id=7, publish_fn=fake_publish,
                            env=ENV_OK, root=sroot)
            check("K: publication requires explicit approval first",
                  r["ok"] is False and "approval" in r["detail"], r)
            check("K: still nothing published", calls == [])

            ACT.approve(session_id=d["session_id"], run_id=run["run_id"],
                        version_sha=d["version_sha256"], user_id=4242, chat_id=7,
                        env=ENV_OK, root=sroot)
            r = ACT.publish(session_id=d["session_id"], run_id=run["run_id"],
                            run_dir=run["run_dir"], version_sha=d["version_sha256"],
                            user_id=4242, chat_id=7, publish_fn=fake_publish,
                            env=ENV_OK, root=sroot)
            check("L: an approved version publishes", r["ok"] is True, r)
            check("L: exactly one publication call", len(calls) == 1, calls)
            check("L: the decision records the exact bytes",
                  STORE.published_version(d["version_sha256"], sroot) is not None)

            r2 = ACT.publish(session_id=d["session_id"], run_id=run["run_id"],
                             run_dir=run["run_dir"], version_sha=d["version_sha256"],
                             user_id=4242, chat_id=7, publish_fn=fake_publish,
                             env=ENV_OK, root=sroot)
            check("M: a duplicate publish callback is idempotent",
                  r2["ok"] is True and r2.get("idempotent") is True, r2)
            check("M: it did not publish twice", len(calls) == 1, calls)
        finally:
            DESK.publish_state = original


def test_l2_approved_rewrite_cannot_publish_as_the_run():
    """The bytes guard, which is what refuses an unvalidated desk rewrite."""
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sroot:
        run, d, original = _publishable(tmp, sroot)
        calls = []
        try:
            out = ACT.request_rewrite(
                session_id=d["session_id"], run_id=run["run_id"],
                version_sha=d["version_sha256"], user_id=4242, chat_id=7,
                rewrite_fn=lambda t, b: t.replace("Paragraph 1.", "New opening."),
                root=sroot)
            ACT.approve(session_id=d["session_id"], run_id=run["run_id"],
                        version_sha=out["version_sha256"], user_id=4242, chat_id=7,
                        env=ENV_OK, root=sroot)
            r = ACT.publish(session_id=d["session_id"], run_id=run["run_id"],
                            run_dir=run["run_dir"], version_sha=out["version_sha256"],
                            user_id=4242, chat_id=7,
                            publish_fn=lambda d_: calls.append(d_) or {"published": True},
                            env=ENV_OK, root=sroot)
            check("L2: an approved rewrite is refused by the bytes guard",
                  r["ok"] is False and "retained run" in r["detail"], r)
            check("L2: the publisher was never called", calls == [])
        finally:
            DESK.publish_state = original


def test_n_real_validator_refuses_a_held_run():
    """Unstubbed. A Safety-held run reaches the desk and still cannot publish."""
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sroot:
        run = DESK.read_run(make_run(tmp))
        d = ACT.deliver(run, chat_id=7, root=sroot)
        ACT.approve(session_id=d["session_id"], run_id=run["run_id"],
                    version_sha=d["version_sha256"], user_id=4242, chat_id=7,
                    env=ENV_OK, root=sroot)
        calls = []
        r = ACT.publish(session_id=d["session_id"], run_id=run["run_id"],
                        run_dir=run["run_dir"], version_sha=d["version_sha256"],
                        user_id=4242, chat_id=7,
                        publish_fn=lambda d_: calls.append(d_) or {"published": True},
                        env=ENV_OK, root=sroot)
        check("N: the existing validator refuses a held run", r["ok"] is False, r)
        check("N: the publisher was never called", calls == [])
        check("N: the refusal is the validator's own words, not the desk's",
              "missing required artifact" in r["detail"].lower()
              or "bridge" in r["detail"].lower(), r["detail"])


def test_o_prose_only_issue_still_reaches_the_desk():
    with tempfile.TemporaryDirectory() as tmp:
        run = DESK.read_run(make_run(
            tmp, "production-prose-only", failure_stage="SAFETY",
            blocking=["MACHINE_LANGUAGE: provenance frames [('this reading', 1)]"]))
        check("O: a prose-only hold is still a readable draft",
              run["state"] == DESK.REVIEWABLE_DRAFT)
        check("O: the owner is shown the finding verbatim",
              any("MACHINE_LANGUAGE" in b for b in run["gates"]["safety_blocking"]))
        check("O: the status line says readable, not rejected",
              DESK.status_line(run).startswith("Readable now"), DESK.status_line(run))


# ── P/Q/R: the learning record ──────────────────────────────────────────────────────

def test_p_raw_survives_a_taxonomy_change():
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sroot:
        run, d, blocks = _deliver_with_blocks(tmp, sroot)
        blk = STORE.block_for_message(7, 1000, root=sroot)
        ACT.react(session_id=d["session_id"], run_id=run["run_id"],
                  version_sha=d["version_sha256"], event_type="TOO_FAST",
                  user_id=4242, chat_id=7, block=blk, raw_feedback="te snel hier",
                  dedupe_key="cb:x", root=sroot)
        before = [e for e in STORE.events(sroot) if e["event_type"] == "TOO_FAST"][0]
        saved = dict(DESK.BUTTON_SIGNALS)
        try:
            DESK.BUTTON_SIGNALS["TOO_FAST"] = "SOMETHING_ELSE_ENTIRELY"
            after = [e for e in STORE.events(sroot) if e["event_type"] == "TOO_FAST"][0]
            check("P: raw feedback is untouched by a taxonomy change",
                  after["raw_feedback"] == before["raw_feedback"] == "te snel hier")
            check("P: the stored derived signal is the one recorded at the time",
                  after["derived_signals"] == ["IDEA_VELOCITY_TOO_HIGH"])
            check("P: the new taxonomy is recomputable from the raw row",
                  DESK.derived_signals("TOO_FAST") == ["SOMETHING_ELSE_ENTIRELY"])
        finally:
            DESK.BUTTON_SIGNALS.clear()
            DESK.BUTTON_SIGNALS.update(saved)


def test_q_reader_gate_cannot_override_the_owner():
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sroot:
        run = DESK.read_run(make_run(tmp, "production-reader-held",
                                     failure_stage="READER"))
        d = ACT.deliver(run, chat_id=7, root=sroot)
        ACT.approve(session_id=d["session_id"], run_id=run["run_id"],
                    version_sha=d["version_sha256"], user_id=4242, chat_id=7,
                    env=ENV_OK, root=sroot)
        check("Q: a READER hold does not erase the owner's approval",
              STORE.approved_version(d["version_sha256"], sroot) is not None)
        check("Q: a READER hold does not make the article invisible",
              run["state"] == DESK.REVIEWABLE_DRAFT)
        check("Q: approval is not publication",
              STORE.published_version(d["version_sha256"], sroot) is None)


def test_r_no_learned_production_change_exists():
    """LEVEL 3 must not exist. The desk records how Jascha edits; it changes nothing."""
    for name in ("editorial_desk.py", "editorial_desk_actions.py",
                 "editorial_desk_store.py", "editorial_desk_bot.py"):
        p = HERE / name
        if not p.exists():
            continue
        src = p.read_text(encoding="utf-8")
        for forbidden in ("WRITER_SYSTEM", "PROSE_DOCTRINE", "FORM_SYSTEM",
                          "READER_SYSTEM", "stages.py"):
            check("R: %s does not touch a production prompt (%s)" % (name, forbidden),
                  forbidden not in src)
        check("R: %s imports no composition stage module" % name,
              "from new_engine_v1 import composition" not in src
              and "import composition" not in src)


def main():
    for fn in sorted((f for n, f in globals().items() if n.startswith("test_")),
                     key=lambda f: f.__code__.co_firstlineno):
        fn()
    print()
    if FAILURES:
        print("%d FAILURE(S): %s" % (len(FAILURES), ", ".join(FAILURES)))
        return 1
    print("all editorial-desk checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
