# TELEGRAM EDITORIAL DESK — handoff, 2026-09-29

**Read this before touching anything under `automation/editorial_desk*`.**
Deployed and live. `.claude/WORK.md` does not yet mention this subsystem; it was last
synced 2026-09-07 and is stale on everything after PR #94.

---

## 1. WHY IT EXISTS

Between 10 and 27 September, 235 production runs produced 13 ACCEPTs, the last on
4 September. The last article to reach readers went out on **3 September**. In the same
period roughly twenty finished articles of 400–1,100 words were written, held at a gate,
retained on disk, and **never read by a person**.

The pipeline was not failing to write. It was failing to show anyone what it wrote.

### The invariant, and it is absolute

> **IF a coherent retained article exists, it reaches the owner's desk.**

Status decides what may be DONE with an article. It never decides whether it may be SEEN.

The pipeline itself shows why that separation cannot be softened: a run dies at SAFETY
carrying a first-person passage with no cited basis (a real factual problem) *and*
`MACHINE_LANGUAGE: provenance frames ['this reading']` (a phrasing tic), and because
`materiality.py` recognises neither category it fails closed on both. A desk that
consulted its own classifier before delivering would rebuild that gate one layer up,
where it is harder to see. **Do not add a delivery gate.**

---

## 2. CURRENT STATE

| Fact | Value |
|---|---|
| Deployed SHA | `e788e5c` (= `origin/main`) |
| Service | `cripminds-desk-bot.service`, systemd **user** unit, `Linger=yes`, active |
| Bot | `@cripminds_bot` ("Cripminds Desk Editor"), its own token |
| Secrets | `/srv/secrets/cripminds/desk-bot.env` (mode 600, dir 700) |
| Store | `/srv/data/cripminds-editorial-desk/` — append-only JSONL |
| Evidence read from | `/srv/data/cripminds-new-engine-v1/<run>/` (read-only) |
| Delivery cron | `5 10 * * *` → `automation/editorial_desk_deliver.py` |
| Tests | 178 + 203 + 212 = **593 offline checks**, all green |
| Data | 25 sessions · 102 events · 26 versions · 1 quarantined |

Unit file lives in the repo at `automation/cripminds-desk-bot.service`, installed to
`~/.config/systemd/user/`. Passwordless sudo is not available on trident; a lingering
user unit starts at boot, which is the only property a system unit was wanted for.

---

## 3. FILES AND BOUNDARIES

```
editorial_desk.py          read-only reading of a retained run; blocks; edit brief;
                           the reader vocabulary; the rewrite contract
editorial_desk_store.py    append-only JSONL; versions by sha256; quarantine
editorial_desk_actions.py  state machine: state model, inbox, deliver, react,
                           rewrite, approve, publish
editorial_desk_recheck.py  post-rewrite gates. THE ONLY desk module allowed to import
                           new_engine_v1.composition, and only to CALL it
editorial_desk_bot.py      Telegram adapter, nothing else
editorial_desk_deliver.py  the 10:05 cron: today's article, by itself
editorial_desk_render.py   TOOL: render every route over real data, send nothing
editorial_desk_live_check.py TOOL: prove Telegram accepts real payloads, then delete
editorial_desk_test.py / _bot_test.py / _route_audit.py
```

**No pipeline file has ever been modified by this work.** Research, Ledger, Worth,
Architecture, Writer, Continuity, Prose Finish, materiality policy and the publisher are
untouched. `test_r_no_learned_production_change_exists` asserts the desk modules define
no production prompt and import no composition stage; `editorial_desk_recheck` is the
single named exception.

---

## 4. DOCTRINE — the rules that were paid for

**Identity is carried by the button and nothing else resolves it.** Every inline button
embeds the session id = `sha256(run_id, article bytes)`. A handler uses the session the
button names, verifies the stored bytes still hash to that version, and sends blocks
from those bytes only. It may never re-resolve from queue order, card position, latest
delivery, title, or any notion of "current". An unidentifiable card refuses and says so.

**Silence is not a signal.** Nothing records or infers anything from latency,
non-response, or a reading that stopped. Ageing a row out of the inbox is housekeeping,
never a judgement, and writes nothing.

**The click is the primary truth.** `raw_feedback` is stored exactly as typed and never
replaced. `derived_signals` sit beside it and are recomputable. Free text is deliberately
**not** keyword-classified — a rule built from the sample that suggested it has already
been falsified once in this project.

**HUMAN ≠ INVENTED.** Human prose comes from selection, pacing, paragraphing, reordering,
staying with licensed actions, moving licensed material. Never from sensory detail, scene
texture, duration, placement, motive, belief, implied dialogue, chronology, or a new
causal join.

**Two gates after any rewrite, both mandatory, in order.**
`A` `continuity.validate_semantic_delta` (deterministic, offline) — did editing ADD
factual surface? `B` `composition.ground_candidate` over the frozen evidence — are the
resulting claims SUPPORTED? B runs even when A is clean. Either failing blocks.

**Publication: four guards, all required.** Allowlisted presser · an explicit
`OWNER_APPROVED` decision for these exact bytes · the retained run still holds those
bytes · the existing publisher grants eligibility *at publication time*. No learned
profile may substitute for any of them.

---

## 5. INCIDENTS — do not reintroduce these

| Date | What happened | Guard now in place |
|---|---|---|
| 09-26 | Five cards delivered; **every READ opened card five.** The handler resolved the right session from the button then discarded it for "most recently delivered" | `test_multi_card_identity` + a proof the fixture reproduces the incident using the removed resolver |
| 09-26 | A redelivered callback advanced the reader a block | reaction dedupe returns before advancing |
| 09-26 | `reply_to_message_id` held the block's own id — a tautology that could never evidence anything | now holds what Telegram reported, or None |
| 09-27 | `/today` said "Nothing new" while an unread article sat on the desk | one state model per version; `/today` is an inbox that chooses nothing |
| 09-27 | The rewriter invented "night after night", "No torch", "Someone flicks it" — all in paragraphs where WANT_MORE was pressed. The instruction said *"give this more room"* with no licensed material supplied | WANT_MORE names its permitted sources or forbids expansion; the rewriter receives the Ledger |
| 09-27 | One `/start` produced two identical inboxes | update-id dedupe + per-update logging |
| 09-28 | Owner pressed `Why now?` three times in 22s — the toast is invisible | a press ticks its own button via `editMessageReplyMarkup` |

**Measured, not assumed:** gate A catches `night after night` (TEMPORAL) and the
`No door / No torch` pair (NEGATION) and is **blind** to `on the same wall` and
`Someone flicks it`. Its channels are lexicons. It would also pass
`Before it was a number, it was that` — no new entity, number or scene, and the
woman→42% join quietly rebuilt. That is why gate B is mandatory. The test asserts the
blind spots on purpose; **do not delete the negative cases to make the suite look
better.**

---

## 6. OPEN — decided by the owner, not yet answered

1. **Subject drift.** There is **no** mental-health exclusion anywhere. The only
   exclusion in the commissioning path is
   `knowledge_first.ACCESS_ORIGIN_QUESTION_IDS = {PR004-04, PR004-06}`, about
   access-deficit framing. Roughly a quarter of the last fortnight's commissions are
   psychiatric (ME/CFS, Molaison, Oxevision, Prinzhorn); 27 and 28 Sep were both, which
   reads as policy. The 48 approved questions live in `.claude/perspective-research/`;
   the *subject* is proposed by a model in `knowledge_first.propose_stories`, so drift
   happens there, not in the library. Two options offered, neither chosen: mark the
   psychiatry-pulling question ids the way access-origin ones are marked, or add subject
   domain to `commissioning_diversity` (which today balances only geography/language).
   **Do not add a runtime keyword ban on story text.**

2. **Publish is decorative.** `publish_retained_fast_lane` is Fast-Lane-shaped: it wants
   `WRITER_OUTPUT.article_text == article.md` plus `CLAIM_MAP_VALIDATION`,
   `GROUNDING_AUDIT`, `READER_AUDIT`. On story-architecture runs `WRITER_OUTPUT`'s
   `article_text` is **empty** and three of those artifacts never exist — verified on
   today's run, the last ACCEPT (09-04) and 09-03. So PUBLISH can never fire, and its
   refusal text is plumbing (`missing required artifact: article.md`) rather than an
   editorial judgement. The end screen now omits Publish instead of showing the reason,
   but the underlying gap is untouched.

3. **Legacy `Continue` buttons** on cards already in the chat still record but no longer
   advance. Owner's call: refuse them as stale, or restore navigation. Recommendation was
   refuse — restoring navigation to a feedback button rebuilds the conflation just removed.

4. **The 2026-09-27 Oxevision rescue is unfinished.** `rescue-20260927T070556Z-17cadeff`
   holds the join-removed body but **HELD at SAFETY** on
   `CONTINUITY_ADDED_MATERIAL: 1 EXCLUSIVITY relation` — the word "only" in
   "only 42% consented", which already appears in the article and in the BBC source. The
   post-editor authority rule fired on a restatement of the Writer's own licensed phrase.
   No second repair was attempted, per instruction.

---

## 7. HOW TO WORK ON IT

```bash
# all three suites — run ALL of them before pushing (this was violated once)
python3 automation/editorial_desk_test.py
python3 automation/editorial_desk_bot_test.py
python3 automation/editorial_desk_route_audit.py

# see what Telegram would actually receive, over real data, sending nothing
python3 automation/editorial_desk_render.py [--route today]

# prove Telegram accepts the real payloads, then delete them again
python3 automation/editorial_desk_live_check.py

# deploy
git push origin HEAD:main
ssh jascha@trident 'cd /srv/data/hermes/workspace/disability-ai-collective \
  && git pull --ff-only origin main \
  && systemctl --user restart cripminds-desk-bot.service'
```

**The render harness is the tool that matters.** Every defect this subsystem has had was
visible only in the rendering — a run id where a headline belongs, an inbox opening with
twenty rows, publisher plumbing in front of a reader, `Noted.` after every press, a
1,716-character block. The unit tests asserted the behaviour and missed the output.

Two lessons worth keeping: a fix that ships green can still not fix the thing (ageing by
delivery time aged nothing, because the whole backlog was delivered in one evening), and
checking the live desk is what caught it both times.

---

## 8. WHAT THE READER ACTUALLY SAID SO FAR

Across four articles read on 26–28 September: `No story ×3`, `List of facts ×2`,
`Source summary ×1`, `Want more ×2`, `I am lost ×2`, `Why now? ×4`, `Strong ×1`, plus
three free-text lines, verbatim in `EVENTS.jsonl`:

> "throwed me into rabbithole, overflood woth details. no story is guiding me, its almost
> like describing. nothing more"
> "no story is guiding me, what is this about. why should i read? what is about?"
> "too dense, and to guide"

**The collection layer works. The thing that converts that into prose is the weak link.**
That is the useful frontier, not more buttons.

---

*Desk built 2026-09-26 → 29. Owner: Jascha. The system learns from his decisions; it does
not replace them.*
