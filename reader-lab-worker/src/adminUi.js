/**
 * Crip Minds Reader Lab — admin control plane (browser UI).
 *
 * Self-contained HTML/CSS/vanilla JS, same construction as the reviewer
 * app in index.js (no build step, no framework, one <script> block).
 * Talks only to /admin/api/* (see adminApi.js), which is gated by
 * Cloudflare Access — this file never handles ADMIN_TOKEN or any other
 * credential; the browser's own Access session is what authenticates it.
 *
 * Five screens, per the design doc — nothing more:
 *   Dashboard | Rounds (+ round detail/create/review/freeze/publish) |
 *   Results | Reviewers | Import
 */

export function renderAdminShell(nonce) {
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>Reader Lab — Admin</title>
<link rel="stylesheet" href="https://cripminds.com/assets/css/main-redesign.css">
<style nonce="${nonce}">
  body { background: var(--foundation-white, #fef9f2); color: var(--foundation-black, #0d0c0b); }
  .adm-shell { max-width: 920px; margin: 0 auto; padding: 2rem 1.25rem 5rem; }
  .adm-nav { display: flex; flex-wrap: wrap; align-items: flex-start; gap: 1.25rem; margin-bottom: 2rem; padding-bottom: 1rem;
    border-bottom: 2px solid var(--foundation-gray-300, #c4b5a0); }
  .adm-nav a { font-weight: 600; text-decoration: none; color: inherit; padding: 0.25rem 0; }
  .adm-nav a:hover, .adm-nav a:focus-visible { text-decoration: underline; }
  .adm-nav a[aria-current="page"] { border-bottom: 3px solid var(--brand-crip-blue, #3f5f89); }
  /* "Advanced" — a native <details> dropdown so routine operation never
     has to look at Research/Policy/Candidates/Import, but every one of
     those pages keeps its own working URL and is one click away. */
  .adm-nav-advanced { position: relative; }
  .adm-nav-advanced > summary { font-weight: 600; cursor: pointer; list-style: none; padding: 0.25rem 0;
    min-height: 44px; display: flex; align-items: center; opacity: 0.85; }
  .adm-nav-advanced > summary::-webkit-details-marker { display: none; }
  .adm-nav-advanced > summary::after { content: "\\25BE"; margin-left: 0.35rem; font-size: 0.7em; }
  .adm-nav-advanced[open] > summary::after { content: "\\25B4"; }
  .adm-nav-advanced-list { position: absolute; top: 100%; right: 0; margin-top: 0.4rem; background: var(--foundation-white, #fef9f2);
    border: 2px solid var(--foundation-gray-300, #c4b5a0); border-radius: 0.5rem; padding: 0.6rem 0.9rem;
    display: flex; flex-direction: column; gap: 0.6rem; z-index: 20; min-width: 11rem; white-space: nowrap; }
  .adm-nav-advanced-list a { padding: 0.15rem 0; }
  .adm-title { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em; opacity: 0.65; margin-bottom: 0.4rem; }
  .adm-card { border: 2px solid var(--foundation-gray-300, #c4b5a0); border-radius: 0.6rem; padding: 1.25rem 1.5rem;
    margin-bottom: 1.25rem; }
  .adm-row { display: flex; justify-content: space-between; align-items: center; gap: 1rem; flex-wrap: wrap; }
  .adm-badge { display: inline-block; padding: 0.15rem 0.6rem; border-radius: 999px; border: 2px solid currentColor;
    font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; }
  .adm-badge--draft { color: #7a6a4d; } .adm-badge--review { color: #8a6a1c; } .adm-badge--frozen { color: #3f5f89; }
  .adm-badge--published { color: #1c7a4d; } .adm-badge--completed { color: #1c7a4d; }
  table.adm-table { width: 100%; border-collapse: collapse; margin: 0.5rem 0 1.25rem; }
  .adm-table th, .adm-table td { text-align: left; padding: 0.6rem 0.75rem; border-bottom: 1px solid var(--foundation-gray-300, #c4b5a0); }
  .adm-table th { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.7; }
  .adm-table tr:hover td { background: var(--brand-crip-blue-50, #eef2f7); }
  .adm-table a { color: inherit; font-weight: 600; }
  .adm-table-wrap { overflow-x: auto; }
  .adm-label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; opacity: 0.6; margin: 1rem 0 0.35rem; }
  .adm-field { display: block; width: 100%; padding: 0.6rem 0.75rem; border: 2px solid var(--foundation-gray-300, #c4b5a0);
    border-radius: 0.4rem; font: inherit; margin-bottom: 0.5rem; box-sizing: border-box; }
  textarea.adm-field { min-height: 5rem; resize: vertical; }
  .adm-item-block { border: 1px dashed var(--foundation-gray-300, #c4b5a0); border-radius: 0.5rem; padding: 1rem;
    margin-bottom: 1rem; }
  .adm-actions { display: flex; gap: 0.75rem; flex-wrap: wrap; margin-top: 1rem; }
  .adm-progress-bar { height: 0.6rem; border-radius: 999px; background: var(--foundation-gray-300, #c4b5a0);
    overflow: hidden; width: 100%; max-width: 16rem; }
  .adm-progress-fill { height: 100%; background: var(--brand-crip-blue, #3f5f89); }
  .adm-warn { border-left: 4px solid #8a6a1c; padding: 0.5rem 0.9rem; margin-bottom: 0.5rem; background: rgba(138,106,28,0.08); }
  .adm-err { border-left: 4px solid #a3312a; padding: 0.5rem 0.9rem; margin-bottom: 0.5rem; background: rgba(163,49,42,0.08); }
  .adm-muted { opacity: 0.65; font-size: 0.9rem; }
  .adm-note { white-space: pre-wrap; }
  a.btn, button.btn { min-height: 44px; }

  /* Plain-language round summary card (Dashboard + Rounds) */
  .adm-round-card { border: 2px solid var(--foundation-gray-300, #c4b5a0); border-radius: 0.75rem;
    padding: 1.25rem 1.5rem; margin-bottom: 1rem; }
  .adm-round-card--action { border-color: var(--brand-crip-blue, #3f5f89); border-width: 3px; }
  .adm-round-id { font-size: 0.85rem; opacity: 0.6; margin-bottom: 0.15rem; }
  .adm-round-title { font-size: 1.3rem; font-weight: 700; margin-bottom: 0.15rem; }
  .adm-round-meta { font-size: 0.9rem; opacity: 0.75; margin-bottom: 0.6rem; }
  .adm-round-summary { margin: 0.5rem 0 0.9rem; line-height: 1.5; }
  .adm-status-pill { display: inline-block; padding: 0.2rem 0.7rem; border-radius: 999px; font-size: 0.8rem;
    font-weight: 700; margin-bottom: 0.5rem; border: 2px solid currentColor; }
  /* Two visually distinct shapes (not color alone): a filled dot prefix
     differs between "needs you" and "just informational" pills. */
  .adm-status-pill::before { content: "\\25CF "; }
  .adm-status-pill--attention { color: #a3312a; }
  .adm-status-pill--ready { color: #3f5f89; }
  .adm-status-pill--progress { color: #8a6a1c; }
  .adm-status-pill--done { color: #1c7a4d; }
  .adm-status-pill--neutral { color: #6b6258; }

  /* Native <details> for "Research details" / "Advanced" — keyboard and
     screen-reader accessible with zero extra JS/ARIA wiring. */
  details.adm-details { margin: 0.75rem 0; border: 1px solid var(--foundation-gray-300, #c4b5a0);
    border-radius: 0.5rem; padding: 0; }
  details.adm-details > summary { cursor: pointer; padding: 0.65rem 1rem; font-weight: 600; font-size: 0.9rem;
    list-style: none; min-height: 44px; display: flex; align-items: center; }
  details.adm-details > summary::-webkit-details-marker { display: none; }
  details.adm-details > summary::before { content: "\\25B8"; margin-right: 0.5rem; opacity: 0.6; }
  details.adm-details[open] > summary::before { content: "\\25BE"; }
  details.adm-details > .adm-details-body { padding: 0 1rem 1rem; font-size: 0.85rem; }
  details.adm-details table.adm-table { font-size: 0.85rem; }

  .adm-big-actions { display: flex; gap: 0.75rem; flex-wrap: wrap; margin-top: 1rem; }
  .adm-big-actions .btn { font-size: 1.05rem; padding: 0.8rem 1.5rem; }
  .adm-reviewer-answer { border-left: 4px solid var(--foundation-gray-300, #c4b5a0); padding: 0.5rem 0.9rem;
    margin-bottom: 0.5rem; }
  .adm-reviewer-answer--agree { border-left-color: #1c7a4d; }
  .adm-reviewer-answer--disagree { border-left-color: #8a6a1c; }

  /* "Preview as reviewer" — deliberately mirrors the real reviewer app's
     own look-and-feel (index.js's renderAppShell) so this is a faithful
     preview, not an admin-styled approximation. Read-only: choice
     "buttons" here are disabled, nothing here can record a response. */
  .adm-preview-banner { background: var(--brand-crip-blue-50, #eef2f7); border: 2px solid var(--brand-crip-blue, #3f5f89);
    border-radius: 0.5rem; padding: 0.85rem 1.1rem; margin-bottom: 1.5rem; font-weight: 600; }
  .adm-preview-frame { max-width: 640px; margin: 0 auto; padding: 1.5rem 1.25rem; border: 1px dashed var(--foundation-gray-300, #c4b5a0); border-radius: 0.75rem; }
  .adm-preview-progress { font-size: 0.85rem; opacity: 0.7; margin-bottom: 1.25rem; }
  .adm-preview-label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; opacity: 0.6; margin-bottom: 0.5rem; }
  .adm-preview-text { font-size: 1.1rem; line-height: 1.6; margin-bottom: 1.5rem; }
  .adm-preview-choice { display: block; width: 100%; text-align: left; padding: 0.9rem 1.1rem; margin-bottom: 0.6rem;
    border: 2px solid var(--foundation-gray-300, #c4b5a0); border-radius: 0.5rem; background: transparent; color: inherit;
    font: inherit; cursor: default; }
  .adm-preview-item + .adm-preview-item { margin-top: 2.5rem; padding-top: 2rem; border-top: 1px solid var(--foundation-gray-300, #c4b5a0); }

  @media (max-width: 30rem) {
    .adm-shell { padding: 1.25rem 0.9rem 4rem; }
    .adm-round-title { font-size: 1.1rem; }
    .adm-big-actions { flex-direction: column; }
    .adm-big-actions .btn { width: 100%; text-align: center; }
    table.adm-table, table.adm-table thead { display: none; }
  }
  @media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
</style>
</head>
<body>
<main id="adm-app" class="adm-shell" aria-live="polite"></main>
<script nonce="${nonce}">
(function () {
  var app = document.getElementById("adm-app");

  // ---- plain-language translations ---------------------------------
  // Canonical snake_case statuses stay exactly as the database/API use
  // them everywhere internally — these maps are presentation-only, used
  // at render time. Raw values remain visible under "Research details"/
  // "Advanced" on every screen that has one, never deleted.

  var STATUS_LABEL = { draft: "Draft", review: "Ready to send", frozen: "Ready to send", published: "In progress", completed: "Finished" };
  var STATUS_PILL_CLASS = { draft: "neutral", review: "ready", frozen: "ready", published: "progress", completed: "done" };
  var DATASET_PURPOSE_LABEL = { pilot: "Pilot", development: "Development", blind_calibration: "Blind calibration", contested: "Contested" };
  var DISPOSITION_LABEL = { development_reference: "Development reference", contested: "Contested", hold_for_later: "Hold for later" };

  var CALIBRATION_RUN_PLAIN = {
    queued: "Getting started",
    analysis_pending: "Looking at the answers",
    evidence_updated: "Analysis complete",
    next_round_pending: "Preparing the next round",
    needs_eligible_candidates: "No new research questions are available yet",
    waiting_for_human_approval: "Next round ready to send",
    next_round_shadow_recorded: "Next round ready to send",
    next_round_published_automatically: "Next round sent automatically",
    failed: "Something needs your attention",
  };

  var PUBLIC_RESPONSE_TEXT = {
    source_supports: "\\u201CThe source supports this.\\u201D",
    reading_of_source: "\\u201CThis is a reading of the source.\\u201D",
    adds_unestablished: "\\u201CThis adds something the source doesn't establish.\\u201D",
    not_sure: "\\u201CI'm not sure.\\u201D",
  };

  function plainRoundStatus(round) {
    // A completed round whose analysis is still waiting on a candidate
    // pool reuses "needs_eligible_candidates" language even though it's
    // a calibration_run concept, not round.status — Jascha shouldn't
    // need to know that distinction exists.
    if (round.status === "completed" && round.calibration_next_action_key === "needs_eligible_candidates") {
      return "No new research questions are available yet";
    }
    return STATUS_LABEL[round.status] || round.status;
  }

  function statusPill(round) {
    var cls = STATUS_PILL_CLASS[round.status] || "neutral";
    return el("span", { class: "adm-status-pill adm-status-pill--" + cls, text: plainRoundStatus(round) });
  }

  // details/summary wrapper — used everywhere a technical/raw block
  // should exist but stay out of the way by default.
  function researchDetails(titleText, bodyChildren) {
    var d = el("details", { class: "adm-details" });
    d.appendChild(el("summary", { text: titleText }));
    var bodyDiv = el("div", { class: "adm-details-body" });
    (bodyChildren || []).forEach(function (c) { if (c) bodyDiv.appendChild(c); });
    d.appendChild(bodyDiv);
    return d;
  }

  function kvTable(pairs) {
    var table = el("table", { class: "adm-table" });
    var tbody = el("tbody", {});
    pairs.forEach(function (pair) {
      if (pair[1] === undefined || pair[1] === null || pair[1] === "") return;
      tbody.appendChild(el("tr", {}, [el("td", { style: "font-weight:600;white-space:nowrap;" }, [pair[0]]), el("td", {}, [String(pair[1])])]));
    });
    table.appendChild(tbody);
    return table;
  }

  function el(tag, attrs, children) {
    var e = document.createElement(tag);
    for (var k in (attrs || {})) {
      if (k === "text") continue;
      if (k === "style") {
        // The CSP here has no 'unsafe-inline' on style-src (same nonce-
        // only policy as script-src) — setting the style ATTRIBUTE
        // directly is blocked outright. Setting individual CSSOM
        // properties via element.style.setProperty is not attribute-
        // level inline style and isn't restricted by style-src, so every
        // style:"prop:value;" call site below keeps working exactly as
        // written, with zero change needed at each call site.
        String(attrs[k]).split(";").forEach(function (decl) {
          var idx = decl.indexOf(":");
          if (idx < 0) return;
          var prop = decl.slice(0, idx).trim();
          var val = decl.slice(idx + 1).trim();
          if (prop && val) e.style.setProperty(prop, val);
        });
        continue;
      }
      e.setAttribute(k, attrs[k]);
    }
    if (attrs && attrs.text !== undefined) e.textContent = attrs.text;
    (children || []).forEach(function (c) {
      if (c === null || c === undefined) return;
      e.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    });
    return e;
  }

  function api(path, opts) {
    return fetch("/admin/api" + path, Object.assign({ credentials: "same-origin", headers: { "content-type": "application/json" } }, opts || {}))
      .then(function (r) { return r.json().then(function (body) { return { ok: r.ok, status: r.status, body: body }; }); });
  }

  function fmtDate(iso) {
    if (!iso) return "\\u2014";
    return iso.replace("T", " ").replace(/\\.\\d+Z$/, "Z").slice(0, 16);
  }

  function statusBadge(status) {
    return el("span", { class: "adm-badge adm-badge--" + status, text: STATUS_LABEL[status] || status });
  }

  function errorList(className, items) {
    if (!items || !items.length) return null;
    var wrap = el("div", {});
    items.forEach(function (msg) { wrap.appendChild(el("div", { class: className, text: msg })); });
    return wrap;
  }

  // ---- routing ----------------------------------------------------

  var routes = [];
  function route(pattern, handler) { routes.push({ pattern: pattern, handler: handler }); }

  function navigate() {
    var hash = location.hash.replace(/^#/, "") || "/dashboard";
    for (var i = 0; i < routes.length; i++) {
      var m = routes[i].pattern.exec(hash);
      if (m) { renderNav(hash); routes[i].handler.apply(null, m.slice(1)); return; }
    }
    renderNav(hash);
    app.appendChild(el("p", {}, ["Not found."]));
  }

  // Simple Mode (default) vs. Advanced Mode — the file's organizing
  // navigation principle. Routine operation (is anything waiting for me,
  // is a round in progress, did one finish, do I need a reviewer) lives
  // entirely in the three primary links; research/policy/provenance
  // internals live one click under "Advanced," never deleted, never
  // moved to a different URL. See .claude/reader-lab-v0-design-2026-08-12.md
  // for the standing convention this implements.
  var PRIMARY_NAV = [["/dashboard", "Home"], ["/rounds", "Rounds"], ["/reviewers", "Reviewers"]];
  var ADVANCED_NAV = [["/calibration", "Research results"], ["/policy", "Policy"], ["/candidates", "Candidates"], ["/import", "Import"]];

  function renderNav(hash) {
    app.innerHTML = "";
    var nav = el("nav", { class: "adm-nav", "aria-label": "Admin sections" });
    PRIMARY_NAV.forEach(function (pair) {
      var current = hash.indexOf(pair[0]) === 0;
      var a = el("a", { href: "#" + pair[0] }, [pair[1]]);
      if (current) a.setAttribute("aria-current", "page");
      nav.appendChild(a);
    });
    var advancedCurrent = ADVANCED_NAV.some(function (pair) { return hash.indexOf(pair[0]) === 0; });
    var advDetails = el("details", { class: "adm-nav-advanced" });
    if (advancedCurrent) advDetails.setAttribute("open", "open");
    advDetails.appendChild(el("summary", { text: "Advanced" }));
    var advList = el("div", { class: "adm-nav-advanced-list" });
    ADVANCED_NAV.forEach(function (pair) {
      var current = hash.indexOf(pair[0]) === 0;
      var a = el("a", { href: "#" + pair[0] }, [pair[1]]);
      if (current) a.setAttribute("aria-current", "page");
      advList.appendChild(a);
    });
    advDetails.appendChild(advList);
    nav.appendChild(advDetails);
    app.appendChild(nav);
  }

  window.addEventListener("hashchange", navigate);

  // ---- dashboard ----------------------------------------------------

  route(/^\\/dashboard$/, function () {
    app.appendChild(el("h1", { class: "text-h2" }, ["Reader Lab"]));
    var body = el("div", {}, ["Loading\\u2026"]);
    app.appendChild(body);
    api("/dashboard").then(function (res) {
      body.innerHTML = "";
      if (!res.ok) { body.appendChild(el("p", { class: "adm-err" }, ["Couldn't load the dashboard."])); return; }
      var d = res.body;

      // ---- What do I click next? -----------------------------------
      body.appendChild(el("p", { class: "adm-title" }, ["Action required"]));
      if (d.needs_attention.length === 0) {
        body.appendChild(el("p", { style: "font-weight:700;font-size:1.1rem;" }, ["No action required."]));
      } else {
        d.needs_attention.forEach(function (n) {
          var box = el("div", { class: "adm-round-card adm-round-card--action" });
          box.appendChild(el("p", { style: "font-weight:600;margin-bottom:0.5rem;" }, [n.note]));
          // The right next click depends on what's actually blocking —
          // "add a reviewer" is a different, more useful action than
          // "go look at the round" when the real problem is nobody else
          // is available to give a second opinion.
          var action =
            n.type === "additional_review_needs_human_action" ? { href: "#/reviewers", label: "Add reviewer" }
            : n.type === "additional_review_needs_policy_configuration" ? { href: "#/policy", label: "Open Policy" }
            : n.type === "calibration_failed" ? { href: "#/calibration", label: "Open Calibration" }
            : { href: "#/rounds/" + n.round_id, label: "Go to " + n.round_id };
          box.appendChild(el("a", { class: "btn btn--primary", href: action.href }, [action.label]));
          body.appendChild(box);
        });
      }

      // ---- What happened? (every round, plain language) -------------
      body.appendChild(el("p", { class: "adm-title", style: "margin-top:2rem;" }, ["Rounds"]));
      if (!d.rounds.length) {
        body.appendChild(el("p", { class: "adm-muted" }, ["No rounds yet."]));
      } else {
        d.rounds.forEach(function (r) { body.appendChild(renderRoundSummaryCard(r)); });
      }

      body.appendChild(el("p", { class: "adm-muted", style: "margin-top:1rem;" }, [
        "New rounds are prepared automatically from eligible research \\u2014 you review and send them from Rounds when they're ready."
      ]));

      // Optional governance and full automation/policy state are real,
      // useful facts — just never things Jascha has to act on to keep
      // Reader Lab running, so they live below the fold, collapsed.
      var advanced = [];
      if (d.optional_governance && d.optional_governance.length) {
        var ogList = el("ul", {});
        d.optional_governance.forEach(function (n) {
          ogList.appendChild(el("li", {}, [el("a", { href: "#/rounds/" + n.round_id }, [n.round_id]), " \\u2014 " + n.note]));
        });
        advanced.push(el("p", { class: "adm-muted" }, ["Optional research classification not set for these rounds \\u2014 never required:"]));
        advanced.push(ogList);
      }
      if (d.automation) {
        var AUTOMATION_ROW_LABEL = {
          round_construction: "Round construction", analysis: "Analysis",
          existing_reviewer_assignment: "Reviewer assignment", additional_review: "Additional review",
          publication: "Publication", candidate_experiments: "Candidate experiments",
          fine_tune_experiments: "Fine-tune experiments", production_promotion: "Production promotion",
        };
        var autoRows = [];
        Object.keys(AUTOMATION_ROW_LABEL).forEach(function (key) {
          if (d.automation[key] === undefined) return;
          autoRows.push([AUTOMATION_ROW_LABEL[key], d.automation[key]]);
        });
        advanced.push(el("p", { class: "adm-label" }, ["Automation state"]));
        advanced.push(kvTable(autoRows));
      }
      if (advanced.length) body.appendChild(researchDetails("Advanced", advanced));
    });
  });

  // ---- plain-language round summary (shared: Dashboard + Rounds) ----

  function roundHeadlineLines(r) {
    var lines = [];
    if (r.status === "draft" || r.status === "review") {
      lines.push("Still being written.");
    } else if (r.status === "frozen") {
      if (r.publication_decision) {
        lines.push(r.publication_decision.would_publish ? "Automatic checks passed." : "Automatic checks found a problem.");
      } else {
        lines.push("Ready for you to review.");
      }
    } else if (r.status === "published") {
      var waiting = (r.reviewers || []).filter(function (rv) { return rv.answered < rv.assigned; }).map(function (rv) { return rv.display_name || rv.reviewer_id; });
      lines.push(waiting.length ? "Waiting for " + waiting.join(" and ") + " to answer." : "Waiting for the round to finish.");
    } else if (r.status === "completed") {
      var calib = r.calibration;
      if (!calib || !calib.evidence_summary) {
        lines.push("Analysis is running\\u2026");
      } else {
        var ev = calib.evidence_summary;
        var agree = (ev.strong_reference || 0) + (ev.provisional_reference || 0);
        var needMore = (ev.contested || 0) + (ev.needs_more_reviewers || 0);
        lines.push("Analysis complete.");
        if (agree) lines.push(agree + " question" + (agree === 1 ? "" : "s") + " had clear agreement.");
        if (needMore) lines.push(needMore + " question" + (needMore === 1 ? " needs" : "s need") + " more opinions.");
      }
      if (calib && calib.next_round_draft) {
        if (calib.next_round_draft.status === "DRAFT_READY") lines.push("Next round ready to send.");
        else if (calib.next_round_draft.status === "NEEDS_ELIGIBLE_CANDIDATES") lines.push("No new research questions are available yet.");
      }
    }
    return lines;
  }

  function renderRoundSummaryCard(r) {
    var card = el("div", { class: "adm-round-card" });
    card.appendChild(el("p", { class: "adm-round-id" }, [r.round_id]));
    card.appendChild(statusPill(r));
    card.appendChild(el("p", { class: "adm-round-meta" }, [r.item_count + " question" + (r.item_count === 1 ? "" : "s") + " \\u00b7 " + r.reviewer_count + " reviewer" + (r.reviewer_count === 1 ? "" : "s")]));

    var summaryLines = roundHeadlineLines(r);
    if (summaryLines.length) {
      var summaryP = el("p", { class: "adm-round-summary" });
      summaryLines.forEach(function (line, i) { if (i > 0) summaryP.appendChild(el("br", {})); summaryP.appendChild(document.createTextNode(line)); });
      card.appendChild(summaryP);
    }

    var actions = el("div", { class: "adm-big-actions" });
    if (r.status === "draft" || r.status === "review") {
      actions.appendChild(el("a", { class: "btn btn--primary", href: "#/rounds/" + r.round_id }, ["Continue editing"]));
    } else if (r.status === "frozen") {
      actions.appendChild(el("a", { class: "btn btn--outline", href: "#/rounds/" + r.round_id + "/preview" }, ["Preview as reviewer"]));
      actions.appendChild(el("a", { class: "btn btn--primary", href: "#/rounds/" + r.round_id }, ["Review & publish"]));
    } else if (r.status === "published") {
      actions.appendChild(el("a", { class: "btn btn--outline", href: "#/rounds/" + r.round_id }, ["View progress"]));
    } else if (r.status === "completed") {
      actions.appendChild(el("a", { class: "btn btn--primary", href: "#/results/" + r.round_id }, ["View summary"]));
      actions.appendChild(el("a", { class: "btn btn--outline", href: "#/rounds/" + r.round_id }, ["Research details"]));
    }
    card.appendChild(actions);
    return card;
  }

  function renderRoundsTable(rounds) {
    var wrap = el("div", {});
    rounds.forEach(function (r) { wrap.appendChild(renderRoundSummaryCard(r)); });
    return wrap;
  }

  // ---- rounds list ----------------------------------------------------

  route(/^\\/rounds$/, function () {
    app.appendChild(el("h1", { class: "text-h2" }, ["Rounds"]));
    var body = el("div", {}, ["Loading\\u2026"]);
    app.appendChild(body);
    api("/rounds").then(function (res) {
      body.innerHTML = "";
      if (!res.ok) { body.appendChild(el("p", { class: "adm-err" }, ["Couldn't load rounds."])); return; }
      if (!res.body.rounds.length) {
        body.appendChild(el("p", { class: "adm-muted" }, ["No rounds yet. The system will prepare the next one automatically."]));
      } else {
        body.appendChild(renderRoundsTable(res.body.rounds));
      }
      body.appendChild(researchDetails("Advanced / Recovery", [
        el("p", { class: "adm-muted" }, [
          "New rounds are normally prepared automatically from eligible research. Use these only to build or recover a round by hand."
        ]),
        el("div", { class: "adm-actions" }, [
          el("a", { class: "btn btn--outline", href: "#/rounds/new" }, ["New round"]),
          el("a", { class: "btn btn--outline", href: "#/import" }, ["Import a round"]),
        ]),
      ]));
    });
  });

  // ---- reviewers ----------------------------------------------------

  route(/^\\/reviewers$/, function () {
    app.appendChild(el("h1", { class: "text-h2" }, ["Reviewers"]));

    var newForm = el("div", { class: "adm-card" });
    newForm.appendChild(el("h3", {}, ["Add a reviewer"]));
    var nameField = el("input", { class: "adm-field", placeholder: "Name (e.g. Maria)", "aria-label": "Reviewer's name" });
    newForm.appendChild(nameField);
    var noteField = el("input", { class: "adm-field", placeholder: "Optional note", "aria-label": "Optional note about this reviewer" });
    newForm.appendChild(noteField);
    var createdBox = el("div", {});
    var createBtn = el("button", { class: "btn btn--primary" }, ["Create invitation"]);
    createBtn.addEventListener("click", function () {
      createBtn.disabled = true;
      var chosenName = nameField.value.trim();
      api("/reviewers", { method: "POST", body: JSON.stringify({ display_name: chosenName || undefined, contact_channel: noteField.value.trim() || undefined }) }).then(function (res) {
        createBtn.disabled = false;
        createdBox.innerHTML = "";
        if (!res.ok) { createdBox.appendChild(el("p", { class: "adm-err" }, ["Couldn't create the invitation."])); return; }
        var link = "https://lab.cripminds.com" + res.body.invite_url_path;
        var card = el("div", { class: "adm-card" });
        card.appendChild(el("p", { style: "font-weight:700;font-size:1.05rem;" }, ["Invitation ready"]));
        card.appendChild(el("p", {}, ["Send this private link to " + (chosenName || "the new reviewer") + ":"]));
        card.appendChild(el("p", { class: "adm-note" }, [link]));
        var copyBtn = el("button", { class: "btn btn--outline btn--sm" }, ["Copy invitation link"]);
        copyBtn.addEventListener("click", function () {
          if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(link).then(function () {
              copyBtn.textContent = "Copied!";
              setTimeout(function () { copyBtn.textContent = "Copy invitation link"; }, 2000);
            });
          }
        });
        card.appendChild(copyBtn);
        card.appendChild(el("p", { class: "adm-muted", style: "margin-top:0.6rem;" }, [
          "When they open it, Reader Lab will guide them through a few practice questions first."
        ]));
        var doneBtn = el("button", { class: "btn btn--outline btn--sm", style: "margin-top:0.6rem;" }, ["Done"]);
        doneBtn.addEventListener("click", function () { createdBox.innerHTML = ""; });
        card.appendChild(el("div", {}, [doneBtn]));
        createdBox.appendChild(card);
        nameField.value = "";
        noteField.value = "";
        loadReviewers();
      });
    });
    newForm.appendChild(createBtn);
    newForm.appendChild(createdBox);
    app.appendChild(newForm);

    var body = el("div", {}, ["Loading\\u2026"]);
    app.appendChild(body);

    function renderReviewerCard(rv) {
      var card = el("div", { class: "adm-round-card" });
      card.appendChild(el("p", { class: "adm-round-title" }, [rv.display_name || rv.reviewer_id]));
      var statusBits = [rv.revoked ? "Revoked" : "Active", rv.practice_completed ? "Practice complete" : "Practice not started yet"];
      card.appendChild(el("p", { class: "adm-round-meta" }, [statusBits.join(" \\u00b7 ") + " \\u00b7 " + rv.total_answered + " question" + (rv.total_answered === 1 ? "" : "s") + " answered"]));
      card.appendChild(el("p", {}, [
        rv.revoked ? "Not available for new rounds."
          : rv.active_for_calibration ? "Available for future rounds."
          : "Paused \\u2014 won't be offered new rounds automatically.",
      ]));

      var actions = el("div", { class: "adm-actions" });
      var pauseBtn = el("button", { class: "btn btn--outline btn--sm" }, [rv.active_for_calibration ? "Pause future rounds" : "Resume future rounds"]);
      pauseBtn.addEventListener("click", function () {
        pauseBtn.disabled = true;
        api("/reviewers/" + encodeURIComponent(rv.reviewer_id) + "/eligibility", {
          method: "POST", body: JSON.stringify({ active_for_calibration: !rv.active_for_calibration }),
        }).then(function () { loadReviewers(); });
      });
      actions.appendChild(pauseBtn);
      var revokeBtn = el("button", { class: "btn btn--outline btn--sm" }, [rv.revoked ? "Reactivate" : "Revoke"]);
      revokeBtn.addEventListener("click", function () {
        revokeBtn.disabled = true;
        api("/reviewers/" + encodeURIComponent(rv.reviewer_id) + "/" + (rv.revoked ? "reactivate" : "revoke"), { method: "POST" })
          .then(function () { loadReviewers(); });
      });
      actions.appendChild(revokeBtn);
      card.appendChild(actions);

      card.appendChild(researchDetails("Details", [kvTable([
        ["Reviewer ID", rv.reviewer_id],
        ["Lifetime, all rounds", rv.total_answered + " / " + rv.total_assigned + " answered/assigned"],
        ["Since", fmtDate(rv.created_at)],
        ["Auto-assign new rounds", rv.active_for_calibration ? "On" : "Off"],
        ["Max items per round", rv.max_items_per_round || "unset"],
      ])]));
      return card;
    }

    function loadReviewers() {
      api("/reviewers").then(function (res) {
        body.innerHTML = "";
        if (!res.ok) { body.appendChild(el("p", { class: "adm-err" }, ["Couldn't load reviewers."])); return; }
        if (!res.body.reviewers.length) {
          body.appendChild(el("p", { class: "adm-muted" }, ["No reviewers yet. Invite someone when you're ready."]));
          return;
        }
        res.body.reviewers.forEach(function (rv) { body.appendChild(renderReviewerCard(rv)); });
      });
    }
    loadReviewers();
  });

  // ---- policy ----------------------------------------------------

  var POLICY_FIELD_LABEL = {
    round_publication_policy: "Round publication",
    existing_reviewer_assignment_policy: "Existing-reviewer assignment",
    additional_review_policy: "Additional review",
    additional_reviewers_per_contested_item: "Additional reviewers per contested item",
  };

  function plainPublicationPolicy(v) {
    if (v === "automatic_if_valid") return "Automatically publish new rounds when the automatic checks pass.";
    if (v === "shadow_automatic") return "Ask me before publishing (currently also recording what auto-publish would decide, for review).";
    return "Ask me before publishing.";
  }
  function plainAssignmentPolicy(v) {
    return v === "automatic_if_valid"
      ? "Automatically offer new rounds to already-approved reviewers."
      : "Ask me before assigning existing reviewers to a new round.";
  }
  function plainAdditionalReviewPolicy(v, count) {
    if (v === "disabled") return "Off \\u2014 reviewers who disagree won't automatically get another opinion.";
    if (v === "automatic_if_valid") {
      return count == null
        ? "Automatically ask for another opinion when reviewers disagree \\u2014 needs a reviewer count set below first."
        : "Automatically ask " + count + " additional approved reviewer" + (count === 1 ? "" : "s") + " when reviewers disagree.";
    }
    return "Ask me before requesting another opinion when reviewers disagree.";
  }

  route(/^\\/policy$/, function () {
    app.appendChild(el("h1", { class: "text-h2" }, ["Policy"]));
    var body = el("div", {}, ["Loading\\u2026"]);
    app.appendChild(body);

    function load() {
      api("/policy").then(function (res) {
        body.innerHTML = "";
        if (!res.ok) { body.appendChild(el("p", { class: "adm-err" }, ["Couldn't load policy."])); return; }
        var active = res.body.active;

        var plainCard = el("div", { class: "adm-card" });
        plainCard.appendChild(el("p", { class: "adm-title" }, ["Automation"]));
        plainCard.appendChild(el("p", { class: "adm-label" }, ["Publishing new rounds"]));
        plainCard.appendChild(el("p", { style: "font-weight:600;" }, [plainPublicationPolicy(active.round_publication_policy)]));
        plainCard.appendChild(el("p", { class: "adm-label", style: "margin-top:1rem;" }, ["Extra opinions"]));
        plainCard.appendChild(el("p", {}, [plainAdditionalReviewPolicy(active.additional_review_policy, active.additional_reviewers_per_contested_item)]));
        plainCard.appendChild(el("p", { class: "adm-label", style: "margin-top:1rem;" }, ["Assigning existing reviewers to new rounds"]));
        plainCard.appendChild(el("p", {}, [plainAssignmentPolicy(active.existing_reviewer_assignment_policy)]));
        plainCard.appendChild(el("p", { class: "adm-muted", style: "margin-top:1rem;" }, [
          "Candidate research experiments: " + (active.candidate_experiment_policy === "research_gated" ? "Not automatic yet" : active.candidate_experiment_policy) +
          " \\u00b7 Fine-tuning: " + (active.fine_tune_experiment_policy === "disabled" ? "Off" : active.fine_tune_experiment_policy) +
          " \\u00b7 Production changes: Always require your approval."
        ]));
        body.appendChild(plainCard);

        var card = el("div", { class: "adm-card" });
        card.appendChild(el("p", { class: "adm-title" }, ["Active \\u2014 policy-v" + active.policy_version]));
        card.appendChild(el("p", { class: "adm-muted" }, [
          "Every change here creates a NEW, versioned policy \\u2014 nothing is edited in place, and every past calibration run stays interpretable under whichever version actually governed it. Production promotion is always human-only; no policy setting can change that."
        ]));

        var roundPubSelect = el("select", { class: "adm-field" });
        ["human_approval", "shadow_automatic", "automatic_if_valid"].forEach(function (v) {
          var opt = el("option", { value: v, text: v });
          if (active.round_publication_policy === v) opt.setAttribute("selected", "selected");
          roundPubSelect.appendChild(opt);
        });
        card.appendChild(el("p", { class: "adm-label" }, [POLICY_FIELD_LABEL.round_publication_policy]));
        card.appendChild(roundPubSelect);

        var reviewerAssignSelect = el("select", { class: "adm-field" });
        ["manual", "automatic_if_valid"].forEach(function (v) {
          var opt = el("option", { value: v, text: v });
          if (active.existing_reviewer_assignment_policy === v) opt.setAttribute("selected", "selected");
          reviewerAssignSelect.appendChild(opt);
        });
        card.appendChild(el("p", { class: "adm-label" }, [POLICY_FIELD_LABEL.existing_reviewer_assignment_policy]));
        card.appendChild(reviewerAssignSelect);

        var addlReviewSelect = el("select", { class: "adm-field" });
        ["disabled", "manual", "automatic_if_valid"].forEach(function (v) {
          var opt = el("option", { value: v, text: v });
          if (active.additional_review_policy === v) opt.setAttribute("selected", "selected");
          addlReviewSelect.appendChild(opt);
        });
        card.appendChild(el("p", { class: "adm-label" }, [POLICY_FIELD_LABEL.additional_review_policy]));
        card.appendChild(addlReviewSelect);

        var countField = el("input", { class: "adm-field", type: "number", min: "1", placeholder: "e.g. 1 \\u2014 required before \\u201Cadditional review\\u201D can run automatically", "aria-label": POLICY_FIELD_LABEL.additional_reviewers_per_contested_item });
        if (active.additional_reviewers_per_contested_item != null) countField.value = String(active.additional_reviewers_per_contested_item);
        card.appendChild(el("p", { class: "adm-label" }, [POLICY_FIELD_LABEL.additional_reviewers_per_contested_item]));
        card.appendChild(countField);

        card.appendChild(el("p", { class: "adm-muted", style: "margin-top:0.5rem;" }, [
          "Candidate experiments: " + active.candidate_experiment_policy + " \\u00b7 Fine-tune experiments: " + active.fine_tune_experiment_policy +
          " \\u00b7 Production promotion: " + active.production_promotion_policy + " (fixed)"
        ]));

        var notesField = el("textarea", { class: "adm-field", placeholder: "Why this change (optional, kept with the version)", "aria-label": "Why this change (optional, kept with the version)" });
        card.appendChild(notesField);

        var messageBox = el("div", {});
        var saveBtn = el("button", { class: "btn btn--primary" }, ["Save as new policy version"]);
        saveBtn.addEventListener("click", function () {
          saveBtn.disabled = true;
          var countVal = countField.value === "" ? null : parseInt(countField.value, 10);
          api("/policy", { method: "POST", body: JSON.stringify({
            round_publication_policy: roundPubSelect.value,
            existing_reviewer_assignment_policy: reviewerAssignSelect.value,
            additional_review_policy: addlReviewSelect.value,
            additional_reviewers_per_contested_item: countVal,
            notes: notesField.value || null,
          }) }).then(function (res2) {
            saveBtn.disabled = false;
            messageBox.innerHTML = "";
            if (!res2.ok) { messageBox.appendChild(errorList("adm-err", res2.body.errors || [res2.body.error])); return; }
            load();
          });
        });
        card.appendChild(saveBtn);
        card.appendChild(messageBox);

        var advancedChildren = [card];
        if (res.body.history && res.body.history.length > 1) {
          advancedChildren.push(el("p", { class: "adm-title", style: "margin-top:1.5rem;" }, ["History"]));
          var list = el("ul", {});
          res.body.history.forEach(function (p) {
            list.appendChild(el("li", {}, [
              "policy-v" + p.policy_version + (p.is_active ? " (active)" : "") + " \\u2014 " + fmtDate(p.created_at) + (p.notes ? ": " + p.notes : ""),
            ]));
          });
          advancedChildren.push(list);
        }
        body.appendChild(researchDetails("Advanced policy settings", advancedChildren));
      });
    }
    load();
  });

  // ---- candidates ----------------------------------------------------
  // Visibility/debugging only, per the design doc's own instruction:
  // "normal operation should not require Jascha to manage rows
  // manually." The import fallback below exists for recovery/audit —
  // routine research -> Reader Lab movement goes through the automatic
  // runner path (prepare_calibration_candidates.py -> POST
  // /ops/calibration/candidates), never this screen.

  route(/^\\/candidates$/, function () {
    app.appendChild(el("h1", { class: "text-h2" }, ["Research candidates"]));
    app.appendChild(el("p", { class: "adm-muted" }, [
      "Research questions waiting to be used in a future round. Nothing here needs routine action \\u2014 new rounds are drafted from these automatically."
    ]));

    var body = el("div", {}, ["Loading\\u2026"]);
    app.appendChild(body);

    function load() {
      api("/candidates").then(function (res) {
        body.innerHTML = "";
        if (!res.ok) { body.appendChild(el("p", { class: "adm-err" }, ["Couldn't load candidates."])); return; }
        var candidates = res.body.candidates;
        var visible = candidates.filter(function (c) { return !c.held_out; });
        var assigned = visible.filter(function (c) { return c.already_live_item_id; }).length;
        var waiting = visible.length - assigned;

        if (!visible.length) {
          body.appendChild(el("p", { class: "adm-muted" }, ["No research questions waiting. Nothing you need to do \\u2014 new ones appear automatically as they become ready."]));
        } else {
          var summaryCard = el("div", { class: "adm-card" });
          summaryCard.appendChild(el("p", {}, ["Research questions available: " + visible.length]));
          summaryCard.appendChild(el("p", {}, ["Already assigned: " + assigned]));
          summaryCard.appendChild(el("p", {}, ["Waiting for future rounds: " + waiting]));
          body.appendChild(summaryCard);
        }

        var advancedChildren = [];
        if (candidates.length) {
          var wrap = el("div", { class: "adm-table-wrap" });
          var table = el("table", { class: "adm-table" });
          table.appendChild(el("thead", {}, [el("tr", {}, [
            el("th", { text: "Provenance" }), el("th", { text: "Purpose" }), el("th", { text: "Held out?" }),
            el("th", { text: "Eligible" }), el("th", { text: "Already live?" }), el("th", { text: "Assigned/Answered" }),
            el("th", { text: "Ingested via" }), el("th", { text: "Since" }),
          ])]));
          var tbody = el("tbody", {});
          candidates.forEach(function (c) {
            tbody.appendChild(el("tr", {}, [
              el("td", { class: "adm-muted", text: c.provenance }),
              el("td", { text: DATASET_PURPOSE_LABEL[c.dataset_purpose] || c.dataset_purpose }),
              el("td", { text: c.held_out ? "YES \\u2014 should never appear" : "No" }),
              el("td", { text: c.eligible_for_reader_lab ? "Yes" : "No" }),
              el("td", { class: "adm-muted", text: c.already_live_item_id || "\\u2014" }),
              el("td", { text: c.assigned_count + " / " + c.answered_count }),
              el("td", { text: c.ingested_via || "\\u2014" }),
              el("td", { text: fmtDate(c.created_at) }),
            ]));
          });
          table.appendChild(tbody);
          wrap.appendChild(table);
          advancedChildren.push(wrap);
        }

        var importCard = el("div", { class: "adm-card", style: "margin-top:1.5rem;" });
        importCard.appendChild(el("h3", {}, ["Import a candidate bundle (fallback)"]));
        importCard.appendChild(el("p", { class: "adm-muted" }, [
          "Paste a prepare-calibration-candidates-v1 bundle JSON. Goes through the exact same validation as the automatic runner path. Normally you don't need this \\u2014 it's for recovery only."
        ]));
        var textarea = el("textarea", { class: "adm-field", style: "min-height:10rem;font-family:monospace;font-size:0.85rem;" });
        importCard.appendChild(textarea);
        var resultBox = el("div", {});
        var importBtn = el("button", { class: "btn btn--primary" }, ["Import"]);
        importBtn.addEventListener("click", function () {
          var parsed;
          try { parsed = JSON.parse(textarea.value); } catch (e) {
            resultBox.innerHTML = ""; resultBox.appendChild(el("p", { class: "adm-err" }, ["That's not valid JSON."])); return;
          }
          importBtn.disabled = true;
          api("/candidates/import", { method: "POST", body: JSON.stringify({ bundle: parsed }) }).then(function (res2) {
            importBtn.disabled = false;
            resultBox.innerHTML = "";
            if (!res2.ok) { resultBox.appendChild(errorList("adm-err", res2.body.errors || [res2.body.error])); return; }
            resultBox.appendChild(el("pre", { class: "adm-note", style: "font-size:0.8rem;overflow-x:auto;" }, [JSON.stringify(res2.body, null, 2)]));
            load();
          });
        });
        importCard.appendChild(importBtn);
        importCard.appendChild(resultBox);
        advancedChildren.push(importCard);

        body.appendChild(researchDetails("Research details", advancedChildren));
      });
    }
    load();
  });

  // ---- calibration ----------------------------------------------------

  var EVIDENCE_LABELS = {
    strong_reference: "Strong references", provisional_reference: "Provisional",
    contested: "Contested", needs_more_reviewers: "Needs more reviewers", insufficient_evidence: "Insufficient evidence",
  };

  var ADDITIONAL_REVIEW_STATUS_LABEL = {
    DISABLED: "Disabled by policy", NONE_NEEDED: "No disagreement to follow up on",
    NEEDS_HUMAN_ACTION: "Needs your attention", NEEDS_POLICY_CONFIGURATION: "Needs policy configuration",
    DRAFTED: "Drafted automatically",
  };

  function renderAdditionalReviewPlan(plan) {
    var wrap = el("div", {});
    wrap.appendChild(el("p", { style: (plan.status === "NEEDS_HUMAN_ACTION" || plan.status === "NEEDS_POLICY_CONFIGURATION") ? "font-weight:600;color:#a3312a;" : "" }, [
      ADDITIONAL_REVIEW_STATUS_LABEL[plan.status] || plan.status,
    ]));
    if (plan.reason) wrap.appendChild(el("p", { class: "adm-muted" }, [plan.reason]));
    if (plan.status === "DRAFTED" && plan.draft_round_id) {
      wrap.appendChild(el("p", {}, [el("a", { class: "btn btn--outline btn--sm", href: "#/rounds/" + plan.draft_round_id }, ["Review " + plan.draft_round_id])]));
    }
    if (plan.flagged_items && plan.flagged_items.length) {
      wrap.appendChild(el("p", { class: "adm-muted" }, [
        plan.flagged_items.length + " item(s): " + plan.flagged_items.map(function (i) { return i.disposition; }).join(", "),
      ]));
    }
    return wrap;
  }

  function renderPublicationDecision(decision, label) {
    var wrap = el("div", { style: "margin-top:0.5rem;" });
    wrap.appendChild(el("p", { class: "adm-label" }, [label + " \\u2014 what the system would do"]));
    wrap.appendChild(el("p", { style: "font-weight:600;" }, [
      decision.action === "published_automatically" ? "Published automatically"
        : decision.would_publish ? "Would publish (shadow \\u2014 not acted on)"
        : "Would NOT publish \\u2014 " + (decision.reason || "validation failed"),
    ]));
    return wrap;
  }

  route(/^\\/calibration$/, function () {
    app.appendChild(el("h1", { class: "text-h2" }, ["Research results"]));
    app.appendChild(el("p", { class: "adm-muted" }, ["What reviewers told us, round by round \\u2014 plain results first, the full research/workflow detail collapsed below."]));
    var body = el("div", {}, ["Loading\\u2026"]);
    app.appendChild(body);

    function load() {
      api("/calibration/status").then(function (res) {
        body.innerHTML = "";
        if (!res.ok) { body.appendChild(el("p", { class: "adm-err" }, ["Couldn't load calibration status."])); return; }
        var d = res.body;

        if (!d.round_id) {
          body.appendChild(el("p", { class: "adm-muted" }, [d.next_action || "Nothing to show yet."]));
          return;
        }

        var card = el("div", { class: "adm-card" });
        card.appendChild(el("p", { class: "adm-round-id" }, [d.round_id]));

        var runFailed = d.calibration_run && d.calibration_run.status === "failed";
        if (runFailed) {
          card.appendChild(el("p", { style: "font-weight:700;color:#a3312a;" }, ["Something needs your attention."]));
          card.appendChild(el("p", { class: "adm-muted" }, [d.calibration_run.error || "The automatic analysis ran into a problem."]));
          var retryBtn = el("button", { class: "btn btn--primary" }, ["Try again"]);
          retryBtn.addEventListener("click", function () {
            retryBtn.disabled = true;
            api("/calibration/runs/" + encodeURIComponent(d.calibration_run.run_id) + "/retry", { method: "POST" }).then(function () { load(); });
          });
          card.appendChild(retryBtn);
        } else if (!d.evidence_summary) {
          card.appendChild(el("p", { style: "font-weight:600;" }, [d.calibration_run ? (CALIBRATION_RUN_PLAIN[d.calibration_run.status] || "Working on it\\u2026") : "Waiting for this round to finish."]));
        } else {
          var ev = d.evidence_summary;
          var agree = (ev.strong_reference || 0) + (ev.provisional_reference || 0);
          var needMore = (ev.contested || 0) + (ev.needs_more_reviewers || 0);
          card.appendChild(el("p", { class: "adm-label" }, ["Results from this round"]));
          if (agree) card.appendChild(el("p", {}, [agree + " question" + (agree === 1 ? "" : "s") + ": reviewers agreed clearly."]));
          if (needMore) card.appendChild(el("p", {}, [needMore + " question" + (needMore === 1 ? "" : "s") + ": reviewers disagreed and may benefit from another opinion."]));

          if (d.additional_review) {
            var plain = renderAdditionalReviewPlain(d.additional_review);
            if (plain) card.appendChild(plain);
          }

          if (d.next_round_draft) {
            card.appendChild(el("p", { class: "adm-label", style: "margin-top:1rem;" }, ["Next round"]));
            if (d.next_round_draft.status === "DRAFT_READY" && d.next_round_draft.draft_round_id) {
              card.appendChild(el("p", { style: "font-weight:600;" }, ["Next round ready to send."]));
              card.appendChild(el("a", { class: "btn btn--primary btn--sm", href: "#/rounds/" + d.next_round_draft.draft_round_id }, ["Review " + d.next_round_draft.draft_round_id]));
            } else {
              card.appendChild(el("p", {}, ["No new research questions are available yet."]));
            }
          }
        }
        body.appendChild(card);

        var advanced = [];
        advanced.push(kvTable([
          ["Round-scoped reviewer counts", (d.reviewers || []).map(function (rv) { return (rv.display_name || rv.reviewer_id) + ": " + rv.answered + "/" + rv.assigned; }).join(", ")],
          ["Workflow status (raw)", d.calibration_run ? d.calibration_run.status + (d.calibration_run.current_step ? " (" + d.calibration_run.current_step + ")" : "") : "not started"],
          ["Policy version", d.policy_version],
          ["Next action (internal)", d.next_action],
        ]));
        if (d.evidence_summary) {
          advanced.push(el("p", { class: "adm-label", style: "margin-top:0.75rem;" }, ["Raw evidence counts"]));
          advanced.push(kvTable(Object.keys(EVIDENCE_LABELS).map(function (key) { return [EVIDENCE_LABELS[key], d.evidence_summary[key] || 0]; })));
        }
        if (d.additional_review) {
          advanced.push(el("p", { class: "adm-label", style: "margin-top:0.75rem;" }, ["Additional review (raw)"]));
          advanced.push(renderAdditionalReviewPlan(d.additional_review));
        }
        if (d.additional_review_publication_decision) advanced.push(renderPublicationDecision(d.additional_review_publication_decision, "Additional review round"));
        if (d.next_round_publication_decision) advanced.push(renderPublicationDecision(d.next_round_publication_decision, "Next round"));
        if (d.history && d.history.length) {
          advanced.push(el("p", { class: "adm-label", style: "margin-top:0.75rem;" }, ["History"]));
          var list = el("ul", {});
          d.history.forEach(function (ev) { list.appendChild(el("li", {}, [fmtDate(ev.timestamp) + " \\u2014 " + ev.label])); });
          advanced.push(list);
        }
        body.appendChild(researchDetails("Research details", advanced));
      });
    }
    load();
  });

  // ---- round detail / editor ----------------------------------------------------

  function itemEditorBlock(item, index, onRemove) {
    var block = el("div", { class: "adm-item-block" });
    var head = el("div", { class: "adm-row" });
    head.appendChild(el("strong", { text: "Question " + (index + 1) }));
    var removeBtn = el("button", { class: "btn btn--outline btn--sm", type: "button" }, ["Remove"]);
    removeBtn.addEventListener("click", onRemove);
    head.appendChild(removeBtn);
    block.appendChild(head);

    block.appendChild(el("p", { class: "adm-label" }, ["Source"]));
    var source = el("textarea", { class: "adm-field" }, [item.source_snapshot || ""]);
    block.appendChild(source);

    block.appendChild(el("p", { class: "adm-label" }, ["The sentence"]));
    var candidate = el("textarea", { class: "adm-field" }, [item.candidate_sentence || ""]);
    block.appendChild(candidate);

    block.appendChild(el("p", { class: "adm-label" }, ["Internal note (admin-only, never shown to reviewers)"]));
    var note = el("textarea", { class: "adm-field" }, [item.internal_note || ""]);
    block.appendChild(note);

    block.appendChild(el("p", { class: "adm-label" }, ["Provenance"]));
    var provenance = el("input", { class: "adm-field" }, []);
    provenance.value = item.provenance || "";
    block.appendChild(provenance);

    block.dataset_get = function () {
      return { slot: index + 1, source_snapshot: source.value, candidate_sentence: candidate.value, internal_note: note.value || null, provenance: provenance.value || null };
    };
    return block;
  }

  function renderReviewerPreview(items, showInternal) {
    var wrap = el("div", {});
    items.forEach(function (item, i) {
      var block = el("div", { class: "adm-item-block" });
      block.appendChild(el("p", { class: "adm-label" }, ["Question " + (i + 1) + " \\u2014 Source"]));
      block.appendChild(el("p", { class: "rl-text" }, ["\\u201C" + item.source_snapshot + "\\u201D"]));
      block.appendChild(el("p", { class: "adm-label" }, ["The sentence"]));
      block.appendChild(el("p", { class: "rl-text" }, ["\\u201C" + item.candidate_sentence + "\\u201D"]));
      if (showInternal && item.internal_note) {
        block.appendChild(el("p", { class: "adm-label" }, ["Internal note (never shown to reviewers)"]));
        block.appendChild(el("p", { class: "adm-note adm-muted" }, [item.internal_note]));
      }
      if (showInternal && item.provenance) {
        block.appendChild(el("p", { class: "adm-label" }, ["Provenance"]));
        block.appendChild(el("p", { class: "adm-muted" }, [item.provenance]));
      }
      wrap.appendChild(block);
    });
    return wrap;
  }

  // "Preview as reviewer" — the primary way Jascha reviews a round
  // before publishing (## 10). Renders items exactly as a reviewer will
  // see them: no family labels, no B2/machine terminology, no research
  // rationale, no internal candidate IDs — only what the round detail
  // API already returns for reviewer-facing fields, same guarantee
  // publish.js's canonicalizeManifest already enforces server-side.
  route(/^\\/rounds\\/([^/]+)\\/preview$/, function (roundId) {
    app.appendChild(el("h1", { class: "text-h2" }, ["Preview \\u2014 " + roundId]));
    var body = el("div", {}, ["Loading\\u2026"]);
    app.appendChild(body);
    api("/rounds/" + encodeURIComponent(roundId)).then(function (res) {
      body.innerHTML = "";
      if (!res.ok) { body.appendChild(el("p", { class: "adm-err" }, ["Couldn't load this round."])); return; }
      var round = res.body;
      body.appendChild(el("div", { class: "adm-preview-banner" }, [
        "This is exactly what each reviewer will see" + (round.reviewer_count ? " (" + round.reviewer_count + " reviewer" + (round.reviewer_count === 1 ? "" : "s") + " assigned)" : "") + " \\u2014 nothing here can send an answer."
      ]));
      var frame = el("div", { class: "adm-preview-frame" });
      (round.items || []).forEach(function (item, i) {
        var block = el("div", { class: "adm-preview-item" });
        block.appendChild(el("p", { class: "adm-preview-progress" }, [(i + 1) + " of " + round.items.length]));
        block.appendChild(el("p", { class: "adm-preview-label" }, ["Source"]));
        block.appendChild(el("p", { class: "adm-preview-text" }, ["\\u201C" + item.source_snapshot + "\\u201D"]));
        block.appendChild(el("p", { class: "adm-preview-label" }, ["The sentence"]));
        block.appendChild(el("p", { class: "adm-preview-text" }, ["\\u201C" + item.candidate_sentence + "\\u201D"]));
        block.appendChild(el("p", { class: "adm-preview-label" }, ["Which feels most accurate?"]));
        [
          "The source supports this", "This is a reading of the source",
          "This adds something the source doesn't establish", "I'm not sure",
        ].forEach(function (choice) {
          block.appendChild(el("button", { class: "adm-preview-choice", type: "button", disabled: "disabled" }, [choice]));
        });
        frame.appendChild(block);
      });
      body.appendChild(frame);
      body.appendChild(el("div", { class: "adm-actions", style: "margin-top:1.5rem;" }, [
        el("a", { class: "btn btn--outline", href: "#/rounds/" + roundId }, ["Back to round"]),
      ]));
    });
  });

  route(/^\\/rounds\\/(new)$/, function (id) { renderRoundEditor(null); });
  route(/^\\/rounds\\/([^/]+)$/, function (id) { renderRoundEditor(id); });

  function renderRoundEditor(roundId) {
    app.appendChild(el("h1", { class: "text-h2" }, [roundId ? roundId : "New round"]));
    var body = el("div", {}, [roundId ? "Loading\\u2026" : ""]);
    app.appendChild(body);

    function loadAndRender() {
      var reviewersP = api("/reviewers");
      var roundP = roundId ? api("/rounds/" + encodeURIComponent(roundId)) : Promise.resolve({ ok: true, body: null });
      Promise.all([reviewersP, roundP]).then(function (results) {
        var reviewers = results[0].ok ? results[0].body.reviewers : [];
        var round = results[1].body;
        body.innerHTML = "";
        if (roundId && !results[1].ok) { body.appendChild(el("p", { class: "adm-err" }, ["Round not found."])); return; }
        renderEditorForRound(body, roundId, round, reviewers, loadAndRender);
      });
    }
    loadAndRender();
  }

  function renderEditorForRound(body, roundId, round, reviewers, reload) {
    var status = round ? round.status : "draft";
    body.appendChild(el("p", { class: "adm-title" }, ["Status"]));
    body.appendChild(statusBadge(status));

    if (status === "published" || status === "completed") {
      renderPublishedRoundView(body, round);
      return;
    }

    if (status === "frozen") {
      renderFrozenReviewView(body, round, reload);
      return;
    }

    // draft / review — full editor
    var idField = el("input", { class: "adm-field", placeholder: "RL-2026-002", "aria-label": "Round ID" });
    idField.value = (round && round.round_id) || roundId || "";
    if (roundId) idField.setAttribute("disabled", "disabled");
    body.appendChild(el("p", { class: "adm-label" }, ["Round ID"]));
    body.appendChild(idField);

    body.appendChild(el("p", { class: "adm-label" }, ["Dataset purpose"]));
    var purposeSelect = el("select", { class: "adm-field" });
    ["pilot", "development", "blind_calibration", "contested"].forEach(function (p) {
      var opt = el("option", { value: p, text: DATASET_PURPOSE_LABEL[p] });
      if (round && round.dataset_purpose === p) opt.setAttribute("selected", "selected");
      purposeSelect.appendChild(opt);
    });
    body.appendChild(purposeSelect);

    body.appendChild(el("p", { class: "adm-label" }, ["Task version"]));
    var versionField = el("input", { class: "adm-field" });
    versionField.value = (round && round.task_version) || "v0.1";
    body.appendChild(versionField);

    body.appendChild(el("p", { class: "adm-label" }, ["Research question (internal, optional)"]));
    var questionField = el("textarea", { class: "adm-field" }, [(round && round.research_question) || ""]);
    body.appendChild(questionField);

    body.appendChild(el("p", { class: "adm-label" }, ["Reviewers"]));
    var reviewerBoxes = [];
    var reviewerWrap = el("div", {});
    reviewers.filter(function (r) { return !r.revoked; }).forEach(function (r) {
      var label = el("label", { style: "display:block;margin-bottom:0.3rem;" });
      var cb = el("input", { type: "checkbox", value: r.reviewer_id });
      if (round && round.reviewers && round.reviewers.some(function (rr) { return rr.reviewer_id === r.reviewer_id; })) cb.checked = true;
      label.appendChild(cb);
      label.appendChild(document.createTextNode(" " + (r.display_name || r.reviewer_id)));
      reviewerBoxes.push(cb);
      reviewerWrap.appendChild(label);
    });
    body.appendChild(reviewerWrap);

    body.appendChild(el("p", { class: "adm-label", style: "margin-top:1.5rem;" }, ["Questions"]));
    var itemsWrap = el("div", {});
    var itemBlocks = [];
    var initialItems = (round && round.items && round.items.length ? round.items : [{}]);
    function addItemBlock(item) {
      var b = itemEditorBlock(item || {}, itemBlocks.length, function () {
        var i = itemBlocks.indexOf(b);
        itemBlocks.splice(i, 1);
        itemsWrap.removeChild(b);
      });
      itemBlocks.push(b);
      itemsWrap.appendChild(b);
    }
    initialItems.forEach(addItemBlock);
    body.appendChild(itemsWrap);
    var addItemBtn = el("button", { class: "btn btn--outline btn--sm", type: "button" }, ["Add question"]);
    addItemBtn.addEventListener("click", function () { addItemBlock({}); });
    body.appendChild(addItemBtn);

    function collectManifest() {
      return {
        round_id: idField.value,
        dataset_purpose: purposeSelect.value,
        task_version: versionField.value,
        research_question: questionField.value || null,
        reviewer_ids: reviewerBoxes.filter(function (c) { return c.checked; }).map(function (c) { return c.value; }),
        items: itemBlocks.map(function (b) { return b.dataset_get(); }),
      };
    }

    var messageBox = el("div", {});
    body.appendChild(messageBox);

    var actions = el("div", { class: "adm-actions" });
    var saveBtn = el("button", { class: "btn btn--outline" }, ["Save draft"]);
    saveBtn.addEventListener("click", function () {
      var manifest = collectManifest();
      if (!manifest.round_id) { messageBox.innerHTML = ""; messageBox.appendChild(el("p", { class: "adm-err" }, ["Round ID is required."])); return; }
      api("/rounds/" + encodeURIComponent(manifest.round_id), { method: "PUT", body: JSON.stringify(Object.assign({ status: "draft" }, manifest)) }).then(function (res) {
        messageBox.innerHTML = "";
        if (!res.ok) { messageBox.appendChild(errorList("adm-err", (res.body.errors || [res.body.error]))); return; }
        location.hash = "#/rounds/" + manifest.round_id;
      });
    });
    actions.appendChild(saveBtn);

    var freezeBtn = el("button", { class: "btn btn--primary" }, ["Review & freeze"]);
    freezeBtn.addEventListener("click", function () {
      var manifest = collectManifest();
      if (!manifest.round_id) { messageBox.innerHTML = ""; messageBox.appendChild(el("p", { class: "adm-err" }, ["Round ID is required."])); return; }
      api("/rounds/" + encodeURIComponent(manifest.round_id), { method: "PUT", body: JSON.stringify(Object.assign({ status: "draft" }, manifest)) }).then(function () {
        return api("/rounds/" + encodeURIComponent(manifest.round_id) + "/freeze", { method: "POST", body: JSON.stringify(manifest) });
      }).then(function (res) {
        messageBox.innerHTML = "";
        if (!res.ok) { messageBox.appendChild(errorList("adm-err", (res.body.errors || [res.body.error]))); messageBox.appendChild(errorList("adm-warn", res.body.warnings)); return; }
        location.hash = "#/rounds/" + manifest.round_id;
        location.reload ? null : reload();
      });
    });
    actions.appendChild(freezeBtn);
    body.appendChild(actions);
  }

  function renderFrozenReviewView(body, round, reload) {
    body.appendChild(el("p", { class: "adm-round-meta" }, [round.item_count + " question" + (round.item_count === 1 ? "" : "s") + " \\u00b7 " + round.reviewer_count + " reviewer" + (round.reviewer_count === 1 ? "" : "s")]));

    var checksLine = round.publication_decision
      ? (round.publication_decision.would_publish ? "Automatic checks passed." : "Automatic checks found a problem \\u2014 see Research details before publishing.")
      : "Nothing is sent to reviewers until you publish.";
    body.appendChild(el("p", { style: "font-weight:600;font-size:1.05rem;" }, [checksLine]));

    var messageBox = el("div", {});

    var actions = el("div", { class: "adm-big-actions" });
    actions.appendChild(el("a", { class: "btn btn--outline", href: "#/rounds/" + round.round_id + "/preview" }, ["Preview as reviewer"]));

    var publishBtn = el("button", { class: "btn btn--primary" }, ["Publish"]);
    if (round.publication_decision && !round.publication_decision.would_publish) publishBtn.disabled = true;
    publishBtn.addEventListener("click", function () {
      publishBtn.disabled = true;
      api("/rounds/" + encodeURIComponent(round.round_id) + "/publish", { method: "POST" }).then(function (res) {
        publishBtn.disabled = false;
        messageBox.innerHTML = "";
        if (!res.ok) { messageBox.appendChild(errorList("adm-err", (res.body.errors || [res.body.error]))); return; }
        reload();
      });
    });
    actions.appendChild(publishBtn);
    body.appendChild(actions);
    body.appendChild(messageBox);

    var editBtn = el("a", { class: "btn btn--outline btn--sm", href: "#/rounds/" + round.round_id + "?edit", style: "margin-top:0.75rem;display:inline-block;" }, ["Edit again"]);
    editBtn.addEventListener("click", function (e) {
      e.preventDefault();
      api("/rounds/" + encodeURIComponent(round.round_id), { method: "PUT", body: JSON.stringify({ status: "draft" }) }).then(function () { reload(); });
    });
    body.appendChild(editBtn);

    var detailsChildren = [];
    detailsChildren.push(kvTable([
      ["Raw status", round.status],
      ["Dataset purpose", DATASET_PURPOSE_LABEL[round.dataset_purpose] || round.dataset_purpose],
      ["Frozen at", fmtDate(round.frozen_at)],
      ["Manifest hash", round.manifest_sha256],
    ]));
    if (round.publication_decision) {
      detailsChildren.push(el("p", { class: "adm-label", style: "margin-top:1rem;" }, ["Automatic publication check"]));
      detailsChildren.push(kvTable([
        ["Would publish", String(round.publication_decision.would_publish)],
        ["Reason", round.publication_decision.reason],
        ["Policy version", round.publication_decision.policy_version],
        ["Decided at", fmtDate(round.publication_decision.decided_at)],
      ]));
    }
    detailsChildren.push(el("p", { class: "adm-label", style: "margin-top:1rem;" }, ["Questions (raw content + internal notes)"]));
    detailsChildren.push(renderReviewerPreview(round.items, true));
    body.appendChild(researchDetails("Research details", detailsChildren));
  }

  function renderExportPanel(round) {
    var panel = el("div", { class: "adm-card" });
    var status = (round.export_status && round.export_status.status) || "not_ready";

    var head = el("div", { class: "adm-row" });
    head.appendChild(el("strong", { text: "COMPLETE" }));
    panel.appendChild(head);
    panel.appendChild(el("p", {}, [el("a", { href: "#/results/" + round.round_id }, ["View results"])]));

    var body = el("div", { style: "margin-top:0.75rem;" });
    panel.appendChild(body);

    function renderReady() {
      body.innerHTML = "";
      body.appendChild(el("p", { text: "Research export ready." }));
      body.appendChild(el("a", {
        class: "btn btn--primary",
        href: "/admin/api/rounds/" + encodeURIComponent(round.round_id) + "/export/download",
      }, ["Download research handoff"]));
    }

    function renderError(detail) {
      body.innerHTML = "";
      body.appendChild(el("p", { class: "adm-err", text: "EXPORT ERROR \\u2014 " + (detail || "generation failed") }));
      var retryBtn = el("button", { class: "btn btn--outline" }, ["Retry export"]);
      retryBtn.addEventListener("click", function () {
        retryBtn.disabled = true;
        api("/rounds/" + encodeURIComponent(round.round_id) + "/export/retry", { method: "POST" }).then(function (res) {
          retryBtn.disabled = false;
          if (res.ok && res.body.status === "ready") renderReady();
          else renderError(res.body && (res.body.error || (res.body.error_detail)));
        });
      });
      body.appendChild(retryBtn);
    }

    function renderNotReady() {
      body.innerHTML = "";
      body.appendChild(el("p", { class: "adm-muted", text: "Preparing the research export\\u2026" }));
      var retryBtn = el("button", { class: "btn btn--outline" }, ["Retry available"]);
      retryBtn.addEventListener("click", function () {
        retryBtn.disabled = true;
        api("/rounds/" + encodeURIComponent(round.round_id) + "/export/retry", { method: "POST" }).then(function (res) {
          retryBtn.disabled = false;
          if (res.ok && res.body.status === "ready") renderReady();
          else renderError(res.body && (res.body.error || res.body.error_detail));
        });
      });
      body.appendChild(retryBtn);
    }

    if (status === "ready") renderReady();
    else if (status === "failed") renderError(round.export_status && round.export_status.error_detail);
    else renderNotReady();

    return panel;
  }

  function renderPublishedRoundView(body, round) {
    body.appendChild(el("p", { class: "adm-round-meta" }, [
      round.item_count + " question" + (round.item_count === 1 ? "" : "s") + " \\u00b7 published " + fmtDate(round.published_at),
    ]));

    if (round.status === "published") {
      body.appendChild(el("p", { class: "adm-label" }, ["Reviewer progress"]));
      (round.reviewers || []).forEach(function (rv) {
        var row = el("div", { class: "adm-row", style: "margin-top:0.5rem;" });
        row.appendChild(el("span", { text: rv.display_name || rv.reviewer_id }));
        row.appendChild(el("span", { class: "adm-muted", text: rv.answered + " / " + rv.assigned }));
        body.appendChild(row);
        var bar = el("div", { class: "adm-progress-bar" });
        var pct = rv.assigned ? Math.round((rv.answered / rv.assigned) * 100) : 0;
        bar.appendChild(el("div", { class: "adm-progress-fill", style: "width:" + pct + "%;" }));
        body.appendChild(bar);
      });
    }

    if (round.completion_state === "complete") {
      var calib = round.calibration;
      var evCard = el("div", { class: "adm-card" });
      evCard.appendChild(el("p", { style: "font-weight:700;font-size:1.1rem;margin-bottom:0.5rem;" }, ["Finished"]));
      if (!calib || !calib.evidence_summary) {
        evCard.appendChild(el("p", { class: "adm-muted" }, ["Analysis is running\\u2026 check back shortly."]));
      } else {
        var ev = calib.evidence_summary;
        var agree = (ev.strong_reference || 0) + (ev.provisional_reference || 0);
        var needMore = (ev.contested || 0) + (ev.needs_more_reviewers || 0);
        evCard.appendChild(el("p", {}, ["Results from this round:"]));
        if (agree) evCard.appendChild(el("p", {}, [agree + " question" + (agree === 1 ? "" : "s") + ": reviewers agreed clearly."]));
        if (needMore) evCard.appendChild(el("p", {}, [needMore + " question" + (needMore === 1 ? "" : "s") + ": reviewers disagreed and may benefit from another opinion."]));
        if (!agree && !needMore) evCard.appendChild(el("p", { class: "adm-muted" }, ["Nothing conclusive yet."]));

        if (calib.additional_review) {
          var arChildren = renderAdditionalReviewPlain(calib.additional_review);
          if (arChildren) evCard.appendChild(arChildren);
        }
      }
      evCard.appendChild(el("a", { class: "btn btn--primary", href: "#/results/" + round.round_id, style: "margin-top:0.75rem;" }, ["View summary"]));
      body.appendChild(evCard);
      body.appendChild(renderExportPanel(round));
    }

    var detailsChildren = [];

    // Optional research classification — deliberately looks completely
    // normal when unset; never a warning, never framed as a required
    // next step (## 4 of the handoff this implements).
    detailsChildren.push(el("p", { class: "adm-label" }, ["Optional research classification"]));
    detailsChildren.push(el("p", { class: "adm-muted" }, ["Optional: classify how this completed round should be used in future research. Leaving this unset is completely normal."]));
    var dispSelect = el("select", { class: "adm-field", style: "max-width:20rem;" });
    dispSelect.appendChild(el("option", { value: "", text: "\\u2014 not set \\u2014" }));
    Object.keys(DISPOSITION_LABEL).forEach(function (d) {
      var opt = el("option", { value: d, text: DISPOSITION_LABEL[d] });
      if (round.dataset_disposition === d) opt.setAttribute("selected", "selected");
      dispSelect.appendChild(opt);
    });
    dispSelect.addEventListener("change", function () {
      api("/rounds/" + encodeURIComponent(round.round_id) + "/disposition", { method: "POST", body: JSON.stringify({ disposition: dispSelect.value }) });
    });
    detailsChildren.push(dispSelect);

    if (round.completion_state === "complete" && round.calibration) {
      detailsChildren.push(el("p", { class: "adm-label", style: "margin-top:1.25rem;" }, ["Calibration workflow"]));
      var calib2 = round.calibration;
      detailsChildren.push(kvTable([
        ["Raw evidence counts", calib2.evidence_summary ? JSON.stringify(calib2.evidence_summary) : null],
        ["Workflow status", calib2.calibration_run ? calib2.calibration_run.status : null],
        ["Policy version", calib2.policy_version],
        ["Next action (internal)", calib2.next_action],
      ]));
      if (calib2.additional_review) {
        detailsChildren.push(el("p", { class: "adm-label", style: "margin-top:0.75rem;" }, ["Additional review (raw)"]));
        detailsChildren.push(renderAdditionalReviewPlan(calib2.additional_review));
      }
      detailsChildren.push(el("p", {}, [el("a", { href: "#/calibration" }, ["Open Calibration"])]));
    }

    detailsChildren.push(el("p", { class: "adm-label", style: "margin-top:1.25rem;" }, ["Questions (raw content + internal notes)"]));
    detailsChildren.push(renderReviewerPreview(round.items || [], true));

    if (round.publication_receipt) {
      detailsChildren.push(el("p", { class: "adm-label", style: "margin-top:1.25rem;" }, ["Publication receipt"]));
      detailsChildren.push(el("pre", { class: "adm-note", style: "font-size:0.8rem;overflow-x:auto;" }, [JSON.stringify(round.publication_receipt, null, 2)]));
    }

    body.appendChild(researchDetails("Research details", detailsChildren));
  }

  // Plain-language version of the additional-review outcome, for the
  // primary (non-Advanced) view. Returns null when there is nothing a
  // non-technical reader needs to see (no disagreement, or policy
  // deliberately disabled — neither is actionable).
  function renderAdditionalReviewPlain(plan) {
    if (plan.status === "NONE_NEEDED" || plan.status === "DISABLED") return null;
    var wrap = el("div", { style: "margin-top:0.75rem;" });
    var count = (plan.flagged_items || []).length;
    if (plan.status === "NEEDS_HUMAN_ACTION" || plan.status === "NEEDS_POLICY_CONFIGURATION") {
      wrap.appendChild(el("p", { style: "font-weight:600;" }, [
        count + " question" + (count === 1 ? "" : "s") + " would benefit from one more independent reviewer.",
      ]));
      wrap.appendChild(el("p", { class: "adm-muted" }, [
        plan.status === "NEEDS_POLICY_CONFIGURATION"
          ? "This isn't configured yet."
          : "There are currently no other approved reviewers available.",
      ]));
      wrap.appendChild(el("a", { class: "btn btn--outline btn--sm", href: "#/reviewers" }, ["Add reviewer"]));
    } else if (plan.status === "DRAFTED" && plan.draft_round_id) {
      wrap.appendChild(el("p", {}, ["An additional round was created automatically for " + count + " question" + (count === 1 ? "" : "s") + "."]));
      wrap.appendChild(el("a", { class: "btn btn--outline btn--sm", href: "#/rounds/" + plan.draft_round_id }, ["View " + plan.draft_round_id]));
    }
    return wrap;
  }

  // ---- results ----------------------------------------------------

  var ANALYSIS_FIELD_LABEL = {
    disposition: "Disposition", agreement_state: "Agreement state", reference_strength: "Reference strength",
    machine_comparison: "Machine comparison (role only, v1)", role_alignment: "Role alignment",
    support_alignment: "Support alignment", overall_relation: "Overall relation", notes: "Notes",
  };

  route(/^\\/results\\/([^/]+)$/, function (roundId) {
    app.appendChild(el("h1", { class: "text-h2" }, ["Results \\u2014 " + roundId]));
    var body = el("div", {}, ["Loading\\u2026"]);
    app.appendChild(body);
    api("/results/" + encodeURIComponent(roundId)).then(function (res) {
      body.innerHTML = "";
      if (!res.ok) { body.appendChild(el("p", { class: "adm-err" }, ["Couldn't load results."])); return; }
      if (!res.body.items.length) { body.appendChild(el("p", { class: "adm-muted" }, ["No responses yet."])); return; }

      res.body.items.forEach(function (item, i) {
        var card = el("div", { class: "adm-card" });
        card.appendChild(el("h3", {}, ["Question " + (i + 1)]));

        if (item.agreement === "agreement") {
          card.appendChild(el("p", { style: "font-weight:700;color:#1c7a4d;" }, ["Both reviewers agreed"]));
          card.appendChild(el("p", {}, ["Both answered: " + PUBLIC_RESPONSE_TEXT[item.judgments[0].selected_public_response]]));
        } else if (item.agreement === "disagreement") {
          card.appendChild(el("p", { style: "font-weight:700;color:#8a6a1c;" }, ["Reviewers disagreed"]));
          item.judgments.forEach(function (j) {
            var label = j.reviewer_display_name || j.reviewer_id;
            var ans = el("div", { class: "adm-reviewer-answer adm-reviewer-answer--disagree" });
            ans.appendChild(el("p", { style: "font-weight:600;margin-bottom:0.15rem;" }, [label + ":"]));
            ans.appendChild(el("p", {}, [PUBLIC_RESPONSE_TEXT[j.selected_public_response]]));
            card.appendChild(ans);
          });
          card.appendChild(el("p", { class: "adm-muted" }, ["This question may benefit from another opinion."]));
        } else {
          card.appendChild(el("p", { style: "font-weight:600;" }, ["One reviewer has answered so far"]));
          card.appendChild(el("p", {}, [PUBLIC_RESPONSE_TEXT[item.judgments[0].selected_public_response]]));
        }

        var hasComments = item.judgments.some(function (j) { return j.comment; });
        if (hasComments) {
          var commentsBody = [];
          item.judgments.forEach(function (j) {
            if (!j.comment) return;
            commentsBody.push(el("p", { style: "margin-top:0.5rem;" }, [
              el("strong", {}, [(j.reviewer_display_name || j.reviewer_id) + ": "]), j.comment,
            ]));
          });
          card.appendChild(researchDetails("Show comments", commentsBody));
        }

        var compareChildren = [];
        compareChildren.push(el("p", { class: "adm-label" }, ["Source (frozen excerpt)"]));
        compareChildren.push(el("p", { class: "rl-text" }, [item.source_snapshot]));
        compareChildren.push(el("p", { class: "adm-label" }, ["The sentence"]));
        compareChildren.push(el("p", { class: "rl-text" }, [item.candidate_sentence]));
        compareChildren.push(el("p", { class: "adm-label", style: "margin-top:0.75rem;" }, ["Each reviewer's raw judgment"]));
        compareChildren.push(kvTable(item.judgments.map(function (j) {
          return [(j.reviewer_display_name || j.reviewer_id) + " (" + j.reviewer_id + ")", j.internal_normalized_response + (j.confidence ? " \\u00b7 " + j.confidence : "")];
        })));
        if (item.analysis) {
          compareChildren.push(el("p", { class: "adm-label", style: "margin-top:0.75rem;" }, ["Automatic analysis (this round's calibration run)"]));
          compareChildren.push(kvTable(Object.keys(ANALYSIS_FIELD_LABEL).map(function (k) { return [ANALYSIS_FIELD_LABEL[k], item.analysis[k]]; })));
        } else {
          compareChildren.push(el("p", { class: "adm-muted", style: "margin-top:0.75rem;" }, ["Automatic analysis hasn't run for this item yet."]));
        }
        card.appendChild(researchDetails("Research comparison", compareChildren));

        body.appendChild(card);
      });
    });
  });

  // ---- import ----------------------------------------------------

  route(/^\\/import$/, function () {
    app.appendChild(el("h1", { class: "text-h2" }, ["Import a round (recovery tool)"]));
    app.appendChild(el("p", { class: "adm-warn" }, ["Normally you do not need this. New rounds are created automatically from eligible research \\u2014 use this only to recover or hand-build a round."]));
    app.appendChild(el("p", { class: "adm-muted" }, ["Paste a round manifest JSON (e.g. reader-lab/rounds/drafts/RL-2026-NNN.json). Nothing is written to production until you choose Save as draft or Freeze & Publish."]));
    var textarea = el("textarea", { class: "adm-field", style: "min-height:12rem;font-family:monospace;font-size:0.85rem;" });
    app.appendChild(textarea);

    var validateBtn = el("button", { class: "btn btn--outline" }, ["Preview"]);
    var resultBox = el("div", {});
    var lastParsed = null;

    function runValidate() {
      var parsed;
      try { parsed = JSON.parse(textarea.value); } catch (e) {
        resultBox.innerHTML = "";
        resultBox.appendChild(el("p", { class: "adm-err" }, ["That's not valid JSON."]));
        return;
      }
      lastParsed = parsed;
      api("/import", { method: "POST", body: JSON.stringify({ manifest: parsed, action: "validate" }) }).then(function (res) {
        resultBox.innerHTML = "";
        if (!res.ok) { resultBox.appendChild(el("p", { class: "adm-err" }, ["Couldn't validate."])); return; }
        var body = res.body;
        resultBox.appendChild(errorList("adm-err", body.errors));
        resultBox.appendChild(errorList("adm-warn", body.warnings));
        if (body.valid) {
          resultBox.appendChild(el("p", {}, ["Looks valid. Preview:"]));
          resultBox.appendChild(renderReviewerPreview(body.preview.items));
          var actions = el("div", { class: "adm-actions" });
          var draftBtn = el("button", { class: "btn btn--outline" }, ["Save as draft"]);
          draftBtn.addEventListener("click", function () {
            api("/import", { method: "POST", body: JSON.stringify({ manifest: lastParsed, action: "save_draft" }) }).then(function (res2) {
              if (res2.ok) location.hash = "#/rounds/" + res2.body.round_id;
            });
          });
          var publishBtn = el("button", { class: "btn btn--primary" }, ["Freeze & Publish"]);
          publishBtn.addEventListener("click", function () {
            api("/import", { method: "POST", body: JSON.stringify({ manifest: lastParsed, action: "freeze_and_publish" }) }).then(function (res2) {
              if (res2.ok) location.hash = "#/rounds/" + res2.body.round_id;
              else { resultBox.appendChild(errorList("adm-err", (res2.body.errors || [res2.body.error]))); }
            });
          });
          actions.appendChild(draftBtn);
          actions.appendChild(publishBtn);
          resultBox.appendChild(actions);
        }
      });
    }
    validateBtn.addEventListener("click", runValidate);
    app.appendChild(validateBtn);
    app.appendChild(resultBox);
  });

  navigate();
})();
</script>
</body>
</html>`;
}
