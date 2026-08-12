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
  .adm-nav { display: flex; flex-wrap: wrap; gap: 1.25rem; margin-bottom: 2rem; padding-bottom: 1rem;
    border-bottom: 2px solid var(--foundation-gray-300, #c4b5a0); }
  .adm-nav a { font-weight: 600; text-decoration: none; color: inherit; padding: 0.25rem 0; }
  .adm-nav a:hover, .adm-nav a:focus-visible { text-decoration: underline; }
  .adm-nav a[aria-current="page"] { border-bottom: 3px solid var(--brand-crip-blue, #3f5f89); }
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
  @media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
</style>
</head>
<body>
<main id="adm-app" class="adm-shell" aria-live="polite"></main>
<script nonce="${nonce}">
(function () {
  var app = document.getElementById("adm-app");
  var STATUS_LABEL = { draft: "Draft", review: "Review", frozen: "Frozen", published: "Active", completed: "Complete" };
  var DATASET_PURPOSE_LABEL = { pilot: "Pilot", development: "Development", blind_calibration: "Blind calibration", contested: "Contested" };
  var DISPOSITION_LABEL = { development_reference: "Development reference", contested: "Contested", hold_for_later: "Hold for later" };

  function el(tag, attrs, children) {
    var e = document.createElement(tag);
    for (var k in (attrs || {})) {
      if (k === "text") continue;
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

  function renderNav(hash) {
    app.innerHTML = "";
    var nav = el("nav", { class: "adm-nav", "aria-label": "Admin sections" });
    [["/dashboard", "Dashboard"], ["/rounds", "Rounds"], ["/calibration", "Calibration"], ["/reviewers", "Reviewers"], ["/import", "Import"]].forEach(function (pair) {
      var current = hash.indexOf(pair[0]) === 0;
      var a = el("a", { href: "#" + pair[0] }, [pair[1]]);
      if (current) a.setAttribute("aria-current", "page");
      nav.appendChild(a);
    });
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

      body.appendChild(el("p", { class: "adm-title" }, ["Current round"]));
      if (d.active_round) {
        body.appendChild(renderRoundCard(d.active_round, true));
      } else {
        body.appendChild(el("p", { class: "adm-muted" }, ["No round is currently active."]));
      }

      body.appendChild(el("p", { class: "adm-title", style: "margin-top:2rem;" }, ["Needs your attention"]));
      if (d.needs_attention.length === 0) {
        body.appendChild(el("p", { class: "adm-muted" }, ["Nothing waiting on you right now."]));
      } else {
        var ul = el("ul", {});
        d.needs_attention.forEach(function (n) {
          ul.appendChild(el("li", {}, [el("a", { href: "#/rounds/" + n.round_id }, [n.round_id]), " \\u2014 " + n.note]));
        });
        body.appendChild(ul);
      }

      body.appendChild(el("p", { class: "adm-title", style: "margin-top:2rem;" }, ["Rounds"]));
      body.appendChild(renderRoundsTable(d.rounds));

      var actions = el("div", { class: "adm-actions" });
      actions.appendChild(el("a", { class: "btn btn--primary", href: "#/rounds/new" }, ["New round"]));
      actions.appendChild(el("a", { class: "btn btn--outline", href: "#/import" }, ["Import draft"]));
      body.appendChild(actions);
    });
  });

  function renderRoundCard(r, showReviewers) {
    var card = el("div", { class: "adm-card" });
    var head = el("div", { class: "adm-row" });
    head.appendChild(el("h3", {}, [el("a", { href: "#/rounds/" + r.round_id }, [r.round_id])]));
    head.appendChild(statusBadge(r.status));
    card.appendChild(head);
    card.appendChild(el("p", { class: "adm-muted" }, [(DATASET_PURPOSE_LABEL[r.dataset_purpose] || r.dataset_purpose) + " \\u00b7 " + r.item_count + " questions"]));
    if (showReviewers && r.status === "completed") {
      var exportStatus = (r.export_status && r.export_status.status) || "not_ready";
      if (exportStatus === "ready") {
        card.appendChild(el("p", { style: "margin-top:0.5rem;" }, ["Research export ready."]));
        card.appendChild(el("a", {
          class: "btn btn--outline btn--sm",
          href: "/admin/api/rounds/" + encodeURIComponent(r.round_id) + "/export/download",
        }, ["Download research handoff"]));
      } else if (exportStatus === "failed") {
        card.appendChild(el("p", { class: "adm-err", style: "margin-top:0.5rem;" }, ["Export error \\u2014 see round page to retry."]));
      } else {
        card.appendChild(el("p", { class: "adm-muted", style: "margin-top:0.5rem;" }, ["Preparing the research export\\u2026"]));
      }
    } else if (showReviewers && r.reviewers) {
      r.reviewers.forEach(function (rv) {
        var row = el("div", { class: "adm-row", style: "margin-top:0.5rem;" });
        row.appendChild(el("span", { text: rv.reviewer_id }));
        row.appendChild(el("span", { class: "adm-muted", text: rv.answered + " / " + rv.assigned }));
        card.appendChild(row);
        var bar = el("div", { class: "adm-progress-bar", role: "progressbar", "aria-valuenow": String(rv.answered), "aria-valuemin": "0", "aria-valuemax": String(rv.assigned) });
        var pct = rv.assigned ? Math.round((rv.answered / rv.assigned) * 100) : 0;
        bar.appendChild(el("div", { class: "adm-progress-fill", style: "width:" + pct + "%;" }));
        card.appendChild(bar);
      });
    }
    return card;
  }

  function renderRoundsTable(rounds) {
    var wrap = el("div", { class: "adm-table-wrap" });
    var table = el("table", { class: "adm-table" });
    var thead = el("thead", {}, [el("tr", {}, [
      el("th", { text: "Round" }), el("th", { text: "Status" }), el("th", { text: "Purpose" }),
      el("th", { text: "Questions" }), el("th", { text: "Reviewers" }), el("th", { text: "Created" }),
    ])]);
    table.appendChild(thead);
    var tbody = el("tbody", {});
    rounds.forEach(function (r) {
      tbody.appendChild(el("tr", {}, [
        el("td", {}, [el("a", { href: "#/rounds/" + r.round_id }, [r.round_id])]),
        el("td", {}, [statusBadge(r.status)]),
        el("td", { text: DATASET_PURPOSE_LABEL[r.dataset_purpose] || r.dataset_purpose }),
        el("td", { text: String(r.item_count) }),
        el("td", { text: String(r.reviewer_count) }),
        el("td", { text: fmtDate(r.created_at) }),
      ]));
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    return wrap;
  }

  // ---- rounds list ----------------------------------------------------

  route(/^\\/rounds$/, function () {
    app.appendChild(el("h1", { class: "text-h2" }, ["Rounds"]));
    var actions = el("div", { class: "adm-actions" });
    actions.appendChild(el("a", { class: "btn btn--primary", href: "#/rounds/new" }, ["New round"]));
    app.appendChild(actions);
    var body = el("div", {}, ["Loading\\u2026"]);
    app.appendChild(body);
    api("/rounds").then(function (res) {
      body.innerHTML = "";
      if (!res.ok) { body.appendChild(el("p", { class: "adm-err" }, ["Couldn't load rounds."])); return; }
      body.appendChild(renderRoundsTable(res.body.rounds));
    });
  });

  // ---- reviewers ----------------------------------------------------

  route(/^\\/reviewers$/, function () {
    app.appendChild(el("h1", { class: "text-h2" }, ["Reviewers"]));
    var newForm = el("div", { class: "adm-card" });
    newForm.appendChild(el("h3", {}, ["Add a reviewer"]));
    var idField = el("input", { class: "adm-field", placeholder: "reviewer id (optional \\u2014 generated if left blank)" });
    newForm.appendChild(idField);
    var createdBox = el("div", {});
    newForm.appendChild(createdBox);
    var createBtn = el("button", { class: "btn btn--primary" }, ["Create reviewer"]);
    createBtn.addEventListener("click", function () {
      createBtn.disabled = true;
      api("/reviewers", { method: "POST", body: JSON.stringify({ reviewer_id: idField.value || undefined }) }).then(function (res) {
        createBtn.disabled = false;
        if (!res.ok) { createdBox.innerHTML = ""; createdBox.appendChild(el("p", { class: "adm-err" }, ["Couldn't create reviewer."])); return; }
        createdBox.innerHTML = "";
        createdBox.appendChild(el("p", {}, ["Created " + res.body.reviewer_id + ". Invitation link (copy it now \\u2014 shown once):"]));
        createdBox.appendChild(el("p", { class: "adm-note" }, ["https://lab.cripminds.com" + res.body.invite_url_path]));
        loadReviewers();
      });
    });
    newForm.appendChild(createBtn);
    app.appendChild(newForm);

    var body = el("div", {}, ["Loading\\u2026"]);
    app.appendChild(body);

    function loadReviewers() {
      api("/reviewers").then(function (res) {
        body.innerHTML = "";
        if (!res.ok) { body.appendChild(el("p", { class: "adm-err" }, ["Couldn't load reviewers."])); return; }
        var wrap = el("div", { class: "adm-table-wrap" });
        var table = el("table", { class: "adm-table" });
        table.appendChild(el("thead", {}, [el("tr", {}, [
          el("th", { text: "Reviewer" }), el("th", { text: "Status" }), el("th", { text: "Practice" }),
          el("th", { text: "Progress" }), el("th", { text: "Since" }), el("th", { text: "Action" }),
        ])]));
        var tbody = el("tbody", {});
        res.body.reviewers.forEach(function (rv) {
          var actionBtn = el("button", { class: "btn btn--outline btn--sm" }, [rv.revoked ? "Reactivate" : "Revoke"]);
          actionBtn.addEventListener("click", function () {
            actionBtn.disabled = true;
            api("/reviewers/" + encodeURIComponent(rv.reviewer_id) + "/" + (rv.revoked ? "reactivate" : "revoke"), { method: "POST" })
              .then(function () { loadReviewers(); });
          });
          tbody.appendChild(el("tr", {}, [
            el("td", { text: rv.reviewer_id }),
            el("td", { text: rv.revoked ? "Revoked" : "Active" }),
            el("td", { text: rv.practice_completed ? "Done" : "Not yet" }),
            el("td", { text: rv.total_answered + " / " + rv.total_assigned }),
            el("td", { text: fmtDate(rv.created_at) }),
            el("td", {}, [actionBtn]),
          ]));
        });
        table.appendChild(tbody);
        wrap.appendChild(table);
        body.appendChild(wrap);
      });
    }
    loadReviewers();
  });

  // ---- calibration ----------------------------------------------------

  var EVIDENCE_LABELS = {
    strong_reference: "Strong references", provisional_reference: "Provisional",
    contested: "Contested", needs_more_reviewers: "Needs more reviewers", insufficient_evidence: "Insufficient evidence",
  };

  route(/^\\/calibration$/, function () {
    app.appendChild(el("h1", { class: "text-h2" }, ["Calibration"]));
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
        card.appendChild(el("p", { class: "adm-title" }, ["Current"]));
        card.appendChild(el("h3", {}, [el("a", { href: "#/rounds/" + d.round_id }, [d.round_id])]));

        (d.reviewers || []).forEach(function (rv) {
          card.appendChild(el("p", {}, [rv.reviewer_id + " " + rv.answered + " / " + rv.assigned]));
        });

        card.appendChild(el("p", { class: "adm-label", style: "margin-top:1rem;" }, ["Workflow"]));
        card.appendChild(el("p", {}, [d.calibration_run ? (d.calibration_run.status + (d.calibration_run.current_step ? " (" + d.calibration_run.current_step + ")" : "")) : "Not started"]));

        if (d.evidence_summary) {
          card.appendChild(el("p", { class: "adm-label", style: "margin-top:1rem;" }, ["Evidence"]));
          Object.keys(EVIDENCE_LABELS).forEach(function (key) {
            card.appendChild(el("p", {}, [EVIDENCE_LABELS[key] + " \\u00a0\\u00a0 " + (d.evidence_summary[key] || 0)]));
          });
        }

        card.appendChild(el("p", { class: "adm-label", style: "margin-top:1rem;" }, ["Next action"]));
        card.appendChild(el("p", { style: "font-weight:600;" }, [d.next_action]));

        if (d.next_round_draft && d.next_round_draft.draft_round_id) {
          card.appendChild(el("p", {}, [el("a", { class: "btn btn--primary", href: "#/rounds/" + d.next_round_draft.draft_round_id }, ["Review next round"])]));
        }

        if (d.calibration_run && d.calibration_run.status === "failed") {
          card.appendChild(el("p", { class: "adm-err", style: "margin-top:0.5rem;" }, [d.calibration_run.error || "Calibration failed."]));
          var retryBtn = el("button", { class: "btn btn--outline" }, ["Retry"]);
          retryBtn.addEventListener("click", function () {
            retryBtn.disabled = true;
            api("/calibration/runs/" + encodeURIComponent(d.calibration_run.run_id) + "/retry", { method: "POST" }).then(function () { load(); });
          });
          card.appendChild(retryBtn);
        }

        body.appendChild(card);

        if (d.history && d.history.length) {
          body.appendChild(el("p", { class: "adm-title", style: "margin-top:1.5rem;" }, ["History"]));
          var list = el("ul", {});
          d.history.forEach(function (ev) {
            list.appendChild(el("li", {}, [fmtDate(ev.timestamp) + " \\u2014 " + ev.label]));
          });
          body.appendChild(list);
        }
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

  function renderReviewerPreview(items) {
    var wrap = el("div", {});
    items.forEach(function (item, i) {
      var block = el("div", { class: "adm-item-block" });
      block.appendChild(el("p", { class: "adm-label" }, ["Question " + (i + 1) + " \\u2014 Source"]));
      block.appendChild(el("p", { class: "rl-text" }, ["\\u201C" + item.source_snapshot + "\\u201D"]));
      block.appendChild(el("p", { class: "adm-label" }, ["The sentence"]));
      block.appendChild(el("p", { class: "rl-text" }, ["\\u201C" + item.candidate_sentence + "\\u201D"]));
      wrap.appendChild(block);
    });
    return wrap;
  }

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
    var idField = el("input", { class: "adm-field", placeholder: "RL-2026-002" });
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
      label.appendChild(document.createTextNode(" " + r.reviewer_id));
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
    body.appendChild(el("p", { class: "adm-muted" }, ["This is exactly what reviewers will see. Nothing is written to production until you publish."]));
    body.appendChild(el("p", {}, [
      el("strong", {}, ["Round: "]), round.round_id, " \\u00b7 ",
      DATASET_PURPOSE_LABEL[round.dataset_purpose] || round.dataset_purpose, " \\u00b7 ",
      round.reviewer_count + " reviewer(s), " + round.item_count + " question(s)",
    ]));
    body.appendChild(renderReviewerPreview(round.items));

    var actions = el("div", { class: "adm-actions" });
    var editBtn = el("a", { class: "btn btn--outline", href: "#/rounds/" + round.round_id + "?edit" }, ["Edit again"]);
    editBtn.addEventListener("click", function (e) {
      e.preventDefault();
      api("/rounds/" + encodeURIComponent(round.round_id), { method: "PUT", body: JSON.stringify({ status: "draft" }) }).then(function () { reload(); });
    });
    actions.appendChild(editBtn);

    var publishBtn = el("button", { class: "btn btn--primary" }, ["Freeze & Publish"]);
    var messageBox = el("div", {});
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
    body.appendChild(el("p", {}, [
      DATASET_PURPOSE_LABEL[round.dataset_purpose] || round.dataset_purpose, " \\u00b7 ",
      round.item_count + " question(s) \\u00b7 published " + fmtDate(round.published_at),
    ]));

    body.appendChild(el("p", { class: "adm-label" }, ["Reviewer progress"]));
    (round.reviewers || []).forEach(function (rv) {
      body.appendChild(el("p", {}, [rv.reviewer_id + ": " + rv.answered + " / " + rv.assigned]));
    });

    if (round.completion_state === "complete") {
      body.appendChild(renderExportPanel(round));
    }

    body.appendChild(el("p", { class: "adm-label" }, ["Research disposition"]));
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
    body.appendChild(dispSelect);

    body.appendChild(el("p", { class: "adm-label", style: "margin-top:1.5rem;" }, ["Questions (admin view)"]));
    (round.items || []).forEach(function (item, i) {
      var block = el("div", { class: "adm-item-block" });
      block.appendChild(el("p", { class: "adm-label" }, ["Source"]));
      block.appendChild(el("p", { class: "rl-text" }, [item.source_snapshot]));
      block.appendChild(el("p", { class: "adm-label" }, ["The sentence"]));
      block.appendChild(el("p", { class: "rl-text" }, [item.candidate_sentence]));
      if (item.internal_note) {
        block.appendChild(el("p", { class: "adm-label" }, ["Internal note"]));
        block.appendChild(el("p", { class: "adm-note adm-muted" }, [item.internal_note]));
      }
      if (item.provenance) {
        block.appendChild(el("p", { class: "adm-label" }, ["Provenance"]));
        block.appendChild(el("p", { class: "adm-muted" }, [item.provenance]));
      }
      body.appendChild(block);
    });

    if (round.publication_receipt) {
      body.appendChild(el("p", { class: "adm-label", style: "margin-top:1.5rem;" }, ["Publication receipt"]));
      body.appendChild(el("pre", { class: "adm-note", style: "font-size:0.8rem;overflow-x:auto;" }, [JSON.stringify(round.publication_receipt, null, 2)]));
    }
  }

  // ---- results ----------------------------------------------------

  route(/^\\/results\\/([^/]+)$/, function (roundId) {
    app.appendChild(el("h1", { class: "text-h2" }, ["Results \\u2014 " + roundId]));
    var body = el("div", {}, ["Loading\\u2026"]);
    app.appendChild(body);
    api("/results/" + encodeURIComponent(roundId)).then(function (res) {
      body.innerHTML = "";
      if (!res.ok) { body.appendChild(el("p", { class: "adm-err" }, ["Couldn't load results."])); return; }
      res.body.items.forEach(function (item, i) {
        var card = el("div", { class: "adm-card" });
        card.appendChild(el("div", { class: "adm-row" }, [
          el("h3", {}, ["Question " + (i + 1)]),
          el("span", { class: "adm-badge", text: item.agreement === "agreement" ? "Agreement" : item.agreement === "disagreement" ? "Disagreement" : "Single judgment" }),
        ]));
        card.appendChild(el("p", { class: "adm-label" }, ["Source"]));
        card.appendChild(el("p", { class: "rl-text" }, [item.source_snapshot]));
        card.appendChild(el("p", { class: "adm-label" }, ["The sentence"]));
        card.appendChild(el("p", { class: "rl-text" }, [item.candidate_sentence]));
        item.judgments.forEach(function (j) {
          var jBlock = el("div", { style: "margin-top:0.75rem;padding-top:0.75rem;border-top:1px solid var(--foundation-gray-300,#c4b5a0);" });
          jBlock.appendChild(el("p", {}, [el("strong", {}, [j.reviewer_id]), ": " + j.selected_public_response.replace(/_/g, " ")]));
          if (j.confidence) jBlock.appendChild(el("p", { class: "adm-muted" }, ["Confidence: " + j.confidence.replace(/_/g, " ")]));
          if (j.comment) jBlock.appendChild(el("p", {}, [j.comment]));
          card.appendChild(jBlock);
        });
        body.appendChild(card);
      });
      if (!res.body.items.length) body.appendChild(el("p", { class: "adm-muted" }, ["No responses yet."]));
    });
  });

  // ---- import ----------------------------------------------------

  route(/^\\/import$/, function () {
    app.appendChild(el("h1", { class: "text-h2" }, ["Import a round"]));
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
