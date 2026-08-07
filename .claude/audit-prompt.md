  You are auditing the Crip Minds content pipeline after a major quality improvement session.

  CONTEXT:
  - Repo: /srv/data/openclaw/workspaces/ops/disability-ai-collective/ on trident
  - Memory: read /Users/stargatesgx/.claude/projects/-Users-stargatesgx-code-trident/memory/cripminds_orchestrator.md first
  - Today's date: check with `date`
  - Pipeline was audited and fixed across 5 rounds (2026-03-15). See git log for commits.
  - The article already published today is: 2026-03-15-the-map-is-not-the-territory...md

  TASK: Run a test article generation and compare output against previously published articles.

  ═══════════════════════════════════════════════
  STEP 1 — VERIFY PIPELINE IS INTACT
  ═══════════════════════════════════════════════

  Run syntax check on both files:
    python3 -m py_compile automation/production_orchestrator.py && echo OK
    python3 -m py_compile opus_rewrite.py && echo OK

  Check git log to confirm all 6 fix commits are present:
    git log --oneline | head -8

  ═══════════════════════════════════════════════
  STEP 2 — READ 3 PREVIOUSLY PUBLISHED ARTICLES
  ═══════════════════════════════════════════════

  Read these 3 articles in full from _posts/:
    1. 2026-03-15-the-map-is-not-the-territory-the-territory-is-not-accessible-either.md
    2. 2026-03-14-the-accessible-entrance-is-around-the-back-on-the-architecture-of-separate-and-u.md
    3. 2026-03-14-the-open-office-was-designed-to-break-my-brain.md

  For each, record:
    - Author (agent)
    - model_used field
    - Register/tone you detect
    - Word count (rough)
    - Opening line
    - Ending line (last sentence of body)
    - Does the ending follow the ENDING spec? (one sentence, concrete image, no CTA, no hope)
    - Quality score if you ran score_quality() on it (manually assess)
    - What beat/territory it covers

  ═══════════════════════════════════════════════
  STEP 3 — TEMPORARILY RENAME TODAY'S ARTICLE
  ═══════════════════════════════════════════════

  Today's article already exists so the orchestrator would skip.
  Temporarily rename it to bypass the duplicate check:

    cd /srv/data/openclaw/workspaces/ops/disability-ai-collective
    mv _posts/2026-03-15-the-map-is-not-the-territory*.md /tmp/todays_article_backup.md

  ═══════════════════════════════════════════════
  STEP 4 — RUN TEST GENERATION (DRY-RUN VARIANT)
  ═══════════════════════════════════════════════

  Run the orchestrator but capture output WITHOUT committing or posting to social media:

    set -a && . /srv/secrets/openclaw.env && set +a
    cd /srv/data/openclaw/workspaces/ops/disability-ai-collective
    python3 automation/production_orchestrator.py 2>&1 | tee /tmp/test_run.log

  After it runs:
    - Check /tmp/test_run.log for which provider was used, register chosen, length target
    - Find the new article: ls _posts/2026-03-15-*.md (there will be 2 now or the new one)
    - Read the new test article in full

  ═══════════════════════════════════════════════
  STEP 5 — COMPARE TEST ARTICLE VS PREVIOUS ARTICLES
  ═══════════════════════════════════════════════

  Compare the test article against the 3 baseline articles on these dimensions:

  STRUCTURAL:
    - Does it open with a concrete moment or sharp claim (not a question, not statistics)?
    - Does it end with one sentence (ENDING spec)?
    - Word count — is it within 800-2000 range? Does it match the logged target?
    - Are there any section headers? Are they statements (not questions)?
    - Any bullet points or numbered lists in the body?

  VOICE:
    - Is the agent's persona distinctive and consistent?
    - First-person throughout?
    - Does the disability perspective feel like expertise/lens (not tragedy)?
    - Register — does the tone match the logged register (wry/clinical/furious/melancholic/ecstatic)?

  QUALITY GATE:
    - Run score_quality() logic manually: what flags would it get? What score?
    - Would opus_rewrite.py trigger a rewrite on it?
    - Check model_used field — was it Opus or a fallback?

  IMPROVEMENTS (what the 9 quality changes were supposed to produce):
    - ENDING block: is the last paragraph exactly one sentence? concrete image?
    - REGISTER: is there a noticeable tonal identity compared to previous articles?
    - SOURCE MATERIAL: does it reference specific facts/names from the source article?
    - BEAT NUDGE: check automation.log — did a beat nudge fire?
    - THREAD: did a cross-article thread block appear in the prompt?
    - LINK POOL: were any pool links woven in? (pool may still be empty — note if so)

  REGRESSION CHECK:
    - Compared to the 3 baseline articles, is quality better, same, or worse?
    - What specifically is different?
    - What's still missing or weak?

  ═══════════════════════════════════════════════
  STEP 6 — CLEANUP
  ═══════════════════════════════════════════════

  IMPORTANT: Remove the test article and restore the real one.

    # Remove test article and its images
    ls _posts/2026-03-15-*.md   # identify which is the test one (different slug from the backup)
    rm _posts/<test-article-slug>.md

    # Remove test images if generated (check assets/ for today's date prefix)
    ls assets/<test-slug>*.jpg 2>/dev/null && rm assets/<test-slug>*.jpg

    # Remove review sidecar if created
    ls _reviews/<test-slug>*.md 2>/dev/null && rm _reviews/<test-slug>*.md

    # Restore the real article
    mv /tmp/todays_article_backup.md _posts/2026-03-15-the-map-is-not-the-territory-the-territory-is-not-accessible-either.md

    # Verify git status — should show only deletions of test files, real article restored
    git status

    # If git has staged the test article (from commit_to_git), reset:
    git reset HEAD _posts/<test-slug>.md 2>/dev/null || true
    git checkout -- _posts/2026-03-15-the-map-is-not-the-territory*.md 2>/dev/null || true

    # Final verify — _posts/ should have only real articles
    ls _posts/2026-03-15-*.md

  ═══════════════════════════════════════════════
  STEP 7 — WRITE COMPARISON REPORT
  ═══════════════════════════════════════════════

  Write a structured comparison covering:

  1. WHAT CHANGED (concrete, observable differences between test article and 3 baselines):
     - Opening structure
     - Ending structure
     - Register/tone distinctiveness
     - Source material integration
     - Agent voice fidelity

  2. WHAT'S WORKING from the 9 improvements

  3. WHAT'S NOT YET VISIBLE (pool links empty, beats table may be sparse, thread requires prior articles)

  4. REGRESSIONS OR NEW PROBLEMS introduced by any fix

  5. VERDICT: Is the pipeline producing meaningfully better articles than before?
     Give a 1-5 rating per dimension (opening / ending / voice / structure / uniqueness)
     and an overall score vs baseline.

  After writing the report: if significant issues found, open a new conversation with
  the specific fix to implement. Do not fix inline without user confirmation.

  ---
  That prompt covers the full test loop. Key design choices:
  - Renames today's article rather than patching the duplicate-check (cleaner, no code change)
  - Reads 3 baselines first so the comparison is grounded, not impressionistic
  - Structured dimensions so the comparison produces actionable data, not just "better/worse"
  - Cleanup is explicit — test article, images, sidecar, git state, all spelled out
  - Ends with a report, not a fix — you read the diff, then decide what to act on next