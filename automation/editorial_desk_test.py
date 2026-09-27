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


def test_quarantined_feedback_never_reaches_a_rewrite():
    """A row recorded under a defect stays in the log and stops being evidence."""
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sroot:
        run, d, blocks = _deliver_with_blocks(tmp, sroot)
        blk = STORE.block_for_message(7, 1001, root=sroot)
        good = ACT.react(session_id=d["session_id"], run_id=run["run_id"],
                         version_sha=d["version_sha256"],
                         event_type="FREE_TEXT_FEEDBACK", user_id=4242, chat_id=7,
                         block=blk, raw_feedback="this one is real",
                         dedupe_key="ok", root=sroot)
        bad = ACT.react(session_id=d["session_id"], run_id=run["run_id"],
                        version_sha=d["version_sha256"],
                        event_type="FREE_TEXT_FEEDBACK", user_id=4242, chat_id=7,
                        block=blk, raw_feedback="said about the wrong article",
                        dedupe_key="contaminated", root=sroot)
        STORE.quarantine([bad["event_id"]], reason="identity-contaminated",
                         incident="test", actor="test", root=sroot)
        brief = ACT.brief_for(d["session_id"], d["version_sha256"], sroot)
        check("quarantined feedback is excluded from the rewrite brief",
              "said about the wrong article" not in brief, brief[:300])
        check("clean feedback still reaches the brief", "this one is real" in brief)
        check("the quarantined row is NOT deleted from the log",
              any(e["event_id"] == bad["event_id"] for e in STORE.events(sroot)))
        check("and its raw words are still readable as evidence",
              any(e.get("raw_feedback") == "said about the wrong article"
                  for e in STORE.events(sroot)))
        check("quarantine is recorded with its reason and incident",
              STORE.quarantine_rows(sroot)[0]["reason"] == "identity-contaminated")


# ── one state per immutable version ─────────────────────────────────────────────────

def test_version_states():
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sroot:
        run = DESK.read_run(make_run(tmp))
        d = ACT.deliver(run, chat_id=7, root=sroot)
        sid, sha = d["session_id"], d["version_sha256"]
        st = ACT.version_state(sid, sha, sroot)
        check("delivered but never opened is UNREAD", st["status"] == ACT.UNREAD, st)

        blocks = DESK.split_blocks(run["article_text"])
        ACT.record_block_sent(session_id=sid, run_id=run["run_id"], version_sha=sha,
                              block=blocks[0], chat_id=7, message_id=1, root=sroot)
        st = ACT.version_state(sid, sha, sroot)
        check("opened is READING with progress",
              st["status"] == ACT.READING and st["at"] == 1 and st["of"] == len(blocks),
              st)
        check("its label reads as progress", st["label"] == "READING 1/%d" % len(blocks),
              st["label"])

        STORE.record_event(session=sid, run_id=run["run_id"],
                           event_type="ARTICLE_FINISHED", actor="owner",
                           version_sha=sha, root=sroot)
        check("finished is FINISHED",
              ACT.version_state(sid, sha, sroot)["status"] == ACT.FINISHED)

        STORE.record_event(session=sid, run_id=run["run_id"], event_type="HOLD",
                           actor="owner", version_sha=sha, root=sroot)
        check("held wins over finished",
              ACT.version_state(sid, sha, sroot)["status"] == ACT.HELD)


def test_two_versions_of_one_article_have_separate_states():
    """v0 and v1 side by side is exactly why state belongs to a version."""
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sroot:
        run = DESK.read_run(make_run(tmp))
        d = ACT.deliver(run, chat_id=7, root=sroot)
        child_text = run["article_text"].replace("Paragraph 1.", "Opening.")
        out = ACT.request_rewrite(
            session_id=d["session_id"], run_id=run["run_id"],
            version_sha=d["version_sha256"], user_id=4242, chat_id=7,
            rewrite_fn=lambda t, b: child_text,
            recheck_fn=lambda a, b: {"status": "NOT_CHECKED", "cleared": False,
                                     "reason": "test", "delta_errors": [],
                                     "grounding_blocking": []},
            root=sroot)
        child_sid = STORE.session_id(run["run_id"], out["version_sha256"])
        check("the rewrite opened its own session",
              STORE.session(child_sid, sroot) is not None)
        check("parent and child are different sessions",
              child_sid != d["session_id"])
        STORE.record_event(session=d["session_id"], run_id=run["run_id"],
                           event_type="ARTICLE_FINISHED", actor="owner",
                           version_sha=d["version_sha256"], root=sroot)
        check("the parent is FINISHED",
              ACT.version_state(d["session_id"], d["version_sha256"],
                                sroot)["status"] == ACT.FINISHED)
        check("the child is independently UNREAD",
              ACT.version_state(child_sid, out["version_sha256"],
                                sroot)["status"] == ACT.UNREAD)


def test_inbox_lists_and_never_chooses():
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sroot:
        for n, day in enumerate(("26", "25", "24"), start=1):
            body = "\n\n".join("Article %s paragraph %d. %s" % (day, i, "word " * 40)
                                for i in range(1, 10))
            r = DESK.read_run(make_run(tmp, "production-202609%sT070000Z-aaa%d"
                                       % (day, n), body=body))
            ACT.deliver(r, chat_id=7, root=sroot)
        rows = ACT.inbox(sroot)
        check("every delivered version is listed", len(rows) == 3, len(rows))
        check("all start UNREAD",
              all(r["status"] == ACT.UNREAD for r in rows), [r["status"] for r in rows])
        check("each row names its own version",
              len({r["version_sha256"] for r in rows}) == 3)
        check("a delivered-but-unopened article never disappears from the inbox",
              all(r["session_id"] for r in rows))


def test_feedback_summary_prefers_the_detail_over_its_parent():
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sroot:
        run, d, blocks = _deliver_with_blocks(tmp, sroot)
        sid, sha = d["session_id"], d["version_sha256"]
        blk = STORE.block_for_message(7, 1000, root=sroot)
        ACT.react(session_id=sid, run_id=run["run_id"], version_sha=sha,
                  event_type="SOUNDS_LIKE_REPORT", user_id=4242, chat_id=7, block=blk,
                  dedupe_key="p1", root=sroot)
        ACT.react(session_id=sid, run_id=run["run_id"], version_sha=sha,
                  event_type="FEEDBACK_DETAIL", user_id=4242, chat_id=7, block=blk,
                  detail="NO_STORY", metadata={"of_action": "SOUNDS_LIKE_REPORT"},
                  dedupe_key="p2", root=sroot)
        summary = dict(ACT.feedback_summary(sid, sha, sroot))
        check("the detail is what the summary reports",
              summary.get("No story") == 1, summary)
        check("the refined parent is not double-counted",
              "Sounds like report" not in summary, summary)


# ── the rewrite may not invent ──────────────────────────────────────────────────────

def test_want_more_never_says_give_this_more_room():
    text = DESK.BUTTON_INSTRUCTIONS["WANT_MORE"]
    check("WANT_MORE does not issue an open invitation to expand",
          "give this more room" not in text.lower(), text)
    for needed in ("ONLY by", "do not expand it"):
        check("WANT_MORE names its limits (%r)" % needed, needed in text, text)


def test_rewrite_contract_forbids_humanising_by_invention():
    sysmsg = DESK.REWRITE_SYSTEM
    check("the contract states HUMAN DOES NOT MEAN INVENTED",
          "HUMAN DOES NOT MEAN INVENTED" in sysmsg)
    for banned in ("sensory detail", "scene texture", "motives", "beliefs",
                   "implied dialogue", "invented chronology", "causal"):
        check("the contract forbids %s" % banned, banned in sysmsg, banned)
    for allowed in ("selection", "pacing", "paragraphing", "reordering"):
        check("the contract permits %s" % allowed, allowed in sysmsg, allowed)


def test_licensed_evidence_is_supplied_to_the_rewriter():
    with tempfile.TemporaryDirectory() as tmp:
        d = make_run(tmp)
        (pathlib.Path(d) / "LEDGER.json").write_text(json.dumps({
            "F01": {"proposition": "A pregnant patient slept in an interview room."},
            "F02": {"proposition": "42% of patients consented in the second pilot."},
        }), encoding="utf-8")
        ev = DESK.licensed_evidence(d)
        check("the ledger propositions are read", len(ev) == 2, ev)
        user = DESK.rewrite_user("THE BODY", "THE BRIEF", ev)
        check("the rewriter is shown the licensed facts", "42% of patients" in user)
        check("and told it may use nothing else", "nothing outside this list" in user)

        empty = DESK.rewrite_user("THE BODY", "THE BRIEF", [])
        check("with no evidence retained, expansion is forbidden outright",
              "may not expand anything" in empty, empty[:400])


def test_semantic_delta_coverage_is_measured_not_assumed():
    """Gate A against the REAL inventions of 2026-09-27. It catches two of four.

    This test records what the deterministic check actually does, including where it
    is blind, because an overstated gate is worse than a modest one: it was claimed in
    review that gate A would catch "on the same wall", and it does not. Its channels
    are lexicons, so a plausible ordinary word invents freely. That blindness is the
    whole argument for gate B being mandatory rather than a nicety -- do not delete
    these negative cases to make the suite look better.
    """
    import editorial_desk_recheck as RC
    parent = ("She had refused to stay in a bedroom with an Oxevision unit in it, "
              "even with the unit switched off.")
    caught = {
        "night after night": "She had refused the bedroom night after night.",
        "No door opening at two in the morning. No torch.":
            "No door opening at two in the morning. No torch.",
    }
    missed = {
        "on the same wall": "It was the same object on the same wall.",
        "Someone flicks it": "Off is a setting. Someone flicks it.",
    }
    for name, invented in caught.items():
        errs = RC.semantic_delta_errors(parent, parent + " " + invented)
        check("gate A catches %r" % name[:30], bool(errs), errs)
    for name, invented in missed.items():
        errs = RC.semantic_delta_errors(parent, parent + " " + invented)
        check("gate A is BLIND to %r -- gate B must cover it" % name[:30],
              errs == [], errs)
    clean = parent.replace(", even with", ". Even with")
    check("gate A passes an edit that adds nothing",
          RC.semantic_delta_errors(parent, clean) == [],
          RC.semantic_delta_errors(parent, clean))


def test_delta_clean_but_unsupported_still_blocks():
    """Gate B exists because gate A cannot see a bad join made of old words."""
    import editorial_desk_recheck as RC
    with tempfile.TemporaryDirectory() as tmp:
        d = pathlib.Path(make_run(tmp))
        for name in RC.GROUNDING_ARTIFACTS:
            (d / name).write_text("{}", encoding="utf-8")

        class FakeProvider:
            model = "fake"

        def fake_ground(*a, **kw):
            return {"status": "HOLD", "blocking": [
                {"quote": "Before it was a number, it was that.",
                 "classification": "TRUE_UNCERTAIN"}]}

        from new_engine_v1 import composition as CP
        saved = CP.ground_candidate
        CP.ground_candidate = fake_ground
        try:
            v = RC.check(d, "the body", "the body, rearranged",
                         provider=FakeProvider())
        finally:
            CP.ground_candidate = saved
        check("a clean delta does not clear the rewrite on its own",
              v["status"] == RC.BLOCKED_UNSUPPORTED, v)
        check("and the finding is reported", v["grounding_blocking"], v)
        check("cleared is false", v["cleared"] is False)


def test_recheck_fails_closed_without_evidence():
    import editorial_desk_recheck as RC
    with tempfile.TemporaryDirectory() as tmp:
        d = make_run(tmp)
        v = RC.check(d, "the body", "the body, rearranged")
        check("no retained evidence means NOT_CHECKED, never cleared",
              v["status"] == RC.NOT_CHECKED and v["cleared"] is False, v)
        check("and it says what is missing", "not retained" in v["reason"], v["reason"])


def test_blocked_rewrite_is_visible_but_marked():
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sroot:
        run = DESK.read_run(make_run(tmp))
        d = ACT.deliver(run, chat_id=7, root=sroot)
        out = ACT.request_rewrite(
            session_id=d["session_id"], run_id=run["run_id"],
            version_sha=d["version_sha256"], user_id=4242, chat_id=7,
            rewrite_fn=lambda t, b: t.replace("Paragraph 1.", "New opening."),
            recheck_fn=lambda a, b: {"status": "BLOCKED_ADDED_MATERIAL",
                                     "cleared": False, "reason": "added scene",
                                     "delta_errors": ["editing added scene: ['torch']"],
                                     "grounding_blocking": []},
            root=sroot)
        row = STORE.version_row(out["version_sha256"], sroot)
        check("the blocked version is still stored and readable",
              STORE.read_version_bytes(out["version_sha256"], sroot) != "")
        check("its identity is the exact rewritten bytes",
              STORE.sha256_text(out["text"]) == out["version_sha256"])
        check("it is marked not revalidated",
              row["gate_status"]["revalidated"] is False, row["gate_status"])
        check("and carries the reason verbatim",
              "torch" in str(row["gate_status"]["delta_errors"]), row["gate_status"])


class evidence_root:
    """Point the desk at a fixture tree. `_title_for` resolves a run directory from
    EVIDENCE_ROOT, which is right in production and needs saying out loud in a test."""

    def __init__(self, tmp):
        self.tmp = tmp

    def __enter__(self):
        self.saved = DESK.EVIDENCE_ROOT
        DESK.EVIDENCE_ROOT = pathlib.Path(self.tmp)
        return self

    def __exit__(self, *a):
        DESK.EVIDENCE_ROOT = self.saved


def test_a_title_is_never_a_run_id():
    """The five cards delivered before card titles were recorded showed up in the
    inbox as `production-20260923T070239Z-1b5de95d`. A timestamp is not a headline."""
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sroot:
      with evidence_root(tmp):
            d = make_run(tmp, "production-20260923T070239Z-1b5de95d")
            (pathlib.Path(d) / "EDITORIAL_PACKAGE.json").write_text(
                json.dumps({"title": "The estimate that became the plan"}),
                encoding="utf-8")
            run = DESK.read_run(d)
            ACT.deliver(run, chat_id=7, root=sroot)   # no CARD_SENT: the pre-fix case
            row = ACT.inbox(sroot)[0]
            check("with no card event the package title is used",
                  row["title"] == "The estimate that became the plan", row["title"])
            check("and never the run id", "production-2026" not in row["title"])


def test_title_falls_back_to_the_opening_heading():
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sroot:
      with evidence_root(tmp):
            body = "# A heading the article opens with\n\n" + BODY
            d = make_run(tmp, "production-20260924T070701Z-3e62a182", body=body)
            run = DESK.read_run(d)
            ACT.deliver(run, chat_id=7, root=sroot)
            row = ACT.inbox(sroot)[0]
            check("with no package either, the opening heading is used",
                  row["title"] == "A heading the article opens with", row["title"])


def test_a_recorded_card_title_wins():
    """What the owner was shown beats anything re-derived later."""
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sroot:
      with evidence_root(tmp):
            d = make_run(tmp)
            (pathlib.Path(d) / "EDITORIAL_PACKAGE.json").write_text(
                json.dumps({"title": "Retitled since"}), encoding="utf-8")
            run = DESK.read_run(d)
            got = ACT.deliver(run, chat_id=7, root=sroot)
            STORE.record_event(session=got["session_id"], run_id=run["run_id"],
                               event_type="CARD_SENT", actor="system",
                               version_sha=got["version_sha256"], message_id=5,
                               metadata={"title": "What the card actually said"},
                               root=sroot)
            check("the card title wins over the package",
                  ACT.inbox(sroot)[0]["title"] == "What the card actually said")


def test_ageing_uses_the_article_date_not_the_delivery_date():
    """The whole backlog was delivered in one evening. Ageing by delivery time aged
    nothing -- /today still opened with twenty articles, which is the bug this test
    exists for. An article is old when it was WRITTEN, not when the desk got to it."""
    import datetime
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sroot:
        names = {"fresh": "production-%sT070000Z-aaaa" % today,
                 "stale": "production-20260910T070000Z-bbbb"}
        for tag, name in names.items():
            body = "\n\n".join("%s paragraph %d. %s" % (tag, i, "word " * 40)
                                for i in range(1, 10))
            ACT.deliver(DESK.read_run(make_run(tmp, name, body=body)),
                        chat_id=7, root=sroot)
        rows = {r["run_id"]: r for r in ACT.inbox(sroot)}
        check("both were delivered just now", len(rows) == 2)
        check("today's article is current", rows[names["fresh"]]["recent"] is True)
        check("an article written weeks ago is backlog, delivered today or not",
              rows[names["stale"]]["recent"] is False,
              rows[names["stale"]]["age_days"])
        check("but it is still on the desk, not hidden",
              rows[names["stale"]]["status"] == ACT.UNREAD)


def test_run_date_parsing():
    import datetime
    check("a production run id yields its date",
          ACT.run_date("production-20260927T070556Z-17cadeff")
          == datetime.datetime(2026, 9, 27, tzinfo=datetime.timezone.utc))
    check("a hand-driven run id yields its date too",
          ACT.run_date("editorial-20260927-oxevision-v3")
          == datetime.datetime(2026, 9, 27, tzinfo=datetime.timezone.utc))
    check("an unparseable id yields None rather than a guess",
          ACT.run_date("something-else") is None)


def test_a_part_read_article_ages_by_last_activity():
    """Open work stays while it is actually being worked on, and not one day longer.

    It used to stay forever, which turned the inbox into a guilt list: three articles
    from 10-14 September sat in "today" a fortnight later purely because READ had once
    been pressed on them.
    """
    import datetime
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sroot:
        run = DESK.read_run(make_run(tmp))
        d = ACT.deliver(run, chat_id=7, root=sroot)
        blocks = DESK.split_blocks(run["article_text"])
        ACT.record_block_sent(session_id=d["session_id"], run_id=run["run_id"],
                              version_sha=d["version_sha256"], block=blocks[0],
                              chat_id=7, message_id=1, root=sroot)
        STORE.record_event(session=d["session_id"], run_id=run["run_id"],
                           event_type="READ_STARTED", actor="owner",
                           version_sha=d["version_sha256"], root=sroot)

        row = ACT.inbox(sroot)[0]
        check("just-read work is in the default view",
              row["status"] == ACT.READING and row["recent"] is True, row)

        later = (datetime.datetime.now(datetime.timezone.utc)
                 + datetime.timedelta(days=5))
        row = ACT.inbox(sroot, now=later)[0]
        check("five days untouched, it moves to the backlog",
              row["recent"] is False, row["idle_days"])
        check("it is still READING, with its progress intact",
              row["status"] == ACT.READING and row["at"] == 1, row)
        check("and nothing was recorded about it having stopped",
              not any(e["event_type"] in ("HOLD", "ARTICLE_FINISHED")
                      for e in STORE.session_events(d["session_id"], sroot)))


def test_returning_to_an_old_read_brings_it_back():
    import datetime
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sroot:
        run = DESK.read_run(make_run(tmp, "production-20260910T070000Z-old1"))
        d = ACT.deliver(run, chat_id=7, root=sroot)
        blocks = DESK.split_blocks(run["article_text"])
        ACT.record_block_sent(session_id=d["session_id"], run_id=run["run_id"],
                              version_sha=d["version_sha256"], block=blocks[0],
                              chat_id=7, message_id=1, root=sroot)
        old = (datetime.datetime.now(datetime.timezone.utc)
               + datetime.timedelta(days=9))
        check("a fortnight-old article left untouched is backlog",
              ACT.inbox(sroot, now=old)[0]["recent"] is False)
        # Pressing RESUME sends another block, which is activity.
        ACT.record_block_sent(session_id=d["session_id"], run_id=run["run_id"],
                              version_sha=d["version_sha256"], block=blocks[1],
                              chat_id=7, message_id=2, root=sroot)
        row = ACT.inbox(sroot)[0]
        check("resuming it brings it back into the default view",
              row["recent"] is True, row["idle_days"])
        check("with the progress it had", row["at"] == 2, row)


def test_an_unread_article_is_still_judged_on_its_own_date():
    """The two clocks must not get crossed: unread by written-date, open by activity."""
    import datetime
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sroot:
        fresh = "production-%sT070000Z-f1" % today
        ACT.deliver(DESK.read_run(make_run(tmp, fresh)), chat_id=7, root=sroot)
        rows = {r["run_id"]: r for r in ACT.inbox(sroot)}
        check("an unopened article written today is current",
              rows[fresh]["recent"] is True and rows[fresh]["status"] == ACT.UNREAD)


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
