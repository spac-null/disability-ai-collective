#!/usr/bin/env python3
"""
daily_run_report.py -- a compact, insight-dense Telegram report for each day's run.

WHY THIS EXISTS. cripminds-daily.sh alerts only when the orchestrator exits
non-zero, which by design happens for infra/contract failures and NOT for an
ordinary editorial HOLD (production_orchestrator.py says so in as many words: a
HOLD "correctly stays quiet"). That is right for alerting and wrong for
reporting: on 2026-09-14 the run held at SAFETY, behaved exactly as designed,
and told nobody. This reports every run, whatever it decided, and puts the day's
result in the context of the days around it -- one run's HOLD is a fact, four in
a row at the same stage is a signal.

TWO THINGS IT IS CAREFUL ABOUT

1. MANIFEST.json records the ENGINE's decision, which is not always the final
   one. The published SFMOMA essay names run production-20260913T083824Z-f83f4b8a,
   whose manifest says HOLD; that run then went through an owner-repair chain and
   ended at PUBLICATION_DECISION.json. So the final word is read from
   PUBLICATION_DECISION.json where it exists, and the manifest only otherwise.
2. "Days since published" is counted from _posts, not from engine decisions, for
   the same reason: what actually reached readers is the honest measure.

It is a READER. It runs after the pipeline, reads only retained evidence and the
repo, and can neither change a run nor delay one. Every internal failure is
swallowed and reported as text: a broken reporter must never look like a broken
pipeline, and must never break one.

No model calls. No publication. No database. No git writes. Nothing is written
anywhere except the message it sends and its own stdout.

Secrets come from the environment (REEF_BOT_TOKEN / REEF_CHAT_ID, as cron
sources /srv/secrets/reef/reef-bot.env). They are never printed, never logged,
and never placed in the message.

Usage:
  python3 automation/daily_run_report.py              # today, send
  python3 automation/daily_run_report.py --dry-run    # print only
  python3 automation/daily_run_report.py --date 2026-09-13
"""

import argparse
import collections
import datetime
import json
import os
import pathlib
import re
import sys
import urllib.parse
import urllib.request

EVIDENCE_ROOT = pathlib.Path(
    os.environ.get("NEW_ENGINE_EVIDENCE_ROOT", "/srv/data/cripminds-new-engine-v1"))
REPO = pathlib.Path(__file__).resolve().parent.parent
TIMEOUT = 15
TREND_DAYS = 7          # width of the outcome strip
RECURRENCE_RUNS = 20    # how far back "recurring stage" looks

GLYPH = {"PUBLISHED": "✅", "ACCEPT": "✅", "CLEARED": "☑️", "HOLD": "⏸",
         "FAIL": "⚠️", "NONE": "·"}


def _log(line):
    """One stamped line. The log is read months later by someone asking whether the
    report actually fired on a given morning; an unstamped line cannot answer that."""
    print("[%s] %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), line),
          flush=True)


def _load(d, name):
    """A missing or malformed artifact is a fact to report, never an exception."""
    try:
        return json.loads((d / name).read_text(encoding="utf-8"))
    except Exception:
        return {}


# ── outcomes ────────────────────────────────────────────────────────────────────────

_PUBLISHED_RUNS = None


def published_run_ids():
    """Run ids named by an actual post. The only unambiguous answer to "did this
    run reach readers": MANIFEST records the ENGINE's decision, and a run the
    engine held can still be owner-repaired and published without the manifest
    being rewritten (production-20260913T083824Z-f83f4b8a is exactly that)."""
    global _PUBLISHED_RUNS
    if _PUBLISHED_RUNS is None:
        ids = set()
        try:
            for f in (REPO / "_posts").glob("*.md"):
                m = re.search(r'^engine_run:\s*"?([^"\n]+)"?\s*$',
                              f.read_text(encoding="utf-8", errors="replace")[:4000], re.M)
                if m:
                    ids.add(m.group(1).strip())
        except Exception:
            pass
        _PUBLISHED_RUNS = ids
    return _PUBLISHED_RUNS


def final_outcome(run_dir):
    """The run's FINAL word, most authoritative source first."""
    if run_dir.name in published_run_ids():
        return "PUBLISHED", True
    pd = _load(run_dir, "PUBLICATION_DECISION.json")
    status = str(pd.get("publication_status") or "").upper()
    if status.startswith("PASS"):
        return "CLEARED", True
    if status:
        return status, True
    return str(_load(run_dir, "MANIFEST.json").get("decision") or "?").upper(), False


def runs_for(day):
    stamp = day.strftime("%Y%m%d")
    return sorted(p for p in EVIDENCE_ROOT.glob("production-%sT*" % stamp) if p.is_dir())


def all_runs():
    return sorted(p for p in EVIDENCE_ROOT.glob("production-*") if p.is_dir())


def total_cost(manifest):
    total = 0.0
    def walk(o):
        nonlocal total
        if isinstance(o, dict):
            v = o.get("subscription_cost_equivalent_usd")
            if isinstance(v, (int, float)):
                total += float(v)
            for x in o.values():
                walk(x)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(manifest.get("provider_identity") or {})
    return total


def headline(run_dir, comp):
    for name in ("ARTICLE_FINAL.md", "ARTICLE_COMPLETED.md", "article.md"):
        try:
            for line in (run_dir / name).read_text(encoding="utf-8").splitlines():
                if line.startswith("# "):
                    return line[2:].strip()
        except Exception:
            pass
    t = str((comp.get("package") or {}).get("title") or "").strip()
    if t:
        return t
    subj = str(comp.get("subject") or "").strip()
    if subj:
        return (subj[:90] + "\u2026") if len(subj) > 90 else subj
    return "(no article written)"


def hold_why(comp):
    """The reason in words a person reads, not the machine's bucket syntax.

    The raw string looks like:
      NEW_UNSUPPORTED_FACTS: the final prose carries factual surface the packet
      never granted -- numbers=[] entities=['Italian'] sensory=[]
    Empty buckets are noise; a populated one is the whole story. Anything this
    does not recognise is passed through trimmed rather than dropped, so a new
    failure shape is never silently rendered as nothing.
    """
    reason = str(comp.get("failure_reason") or "").strip()
    if not reason:
        return ""
    body = reason.split(":", 1)[1] if ":" in reason else reason
    NAME = {"entities": ("entity", "entities"), "numbers": ("number", "numbers"),
            "sensory": ("sensory detail", "sensory details"),
            "dates": ("date", "dates"), "quotes": ("quote", "quotes")}
    found = []
    for bucket, items in re.findall(r"(\w+)=\[([^\]]*)\]", body):
        vals = [v.strip().strip("'\"") for v in items.split(",") if v.strip()]
        if vals:
            one, many = NAME.get(bucket, (bucket, bucket))
            found.append("%s not granted by the packet: %s"
                         % (one if len(vals) == 1 else many,
                            ", ".join('"%s"' % v for v in vals[:4])))
    if found:
        return "; ".join(found)
    cleaned = re.sub(r"\w+=\[[^\]]*\]", "", body)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -\u2013\u2014")
    return (cleaned[:110] + "\u2026") if len(cleaned) > 110 else cleaned


# ── context that turns one data point into a signal ─────────────────────────────────

def outcome_strip(day, days=TREND_DAYS):
    """One glyph per day: the day's last run, oldest first."""
    out = []
    for i in range(days - 1, -1, -1):
        d = day - datetime.timedelta(days=i)
        rs = runs_for(d)
        if not rs:
            out.append(GLYPH["NONE"])
            continue
        o, _ = final_outcome(rs[-1])
        out.append(GLYPH.get(o, GLYPH["FAIL"] if o not in ("HOLD",) else GLYPH["HOLD"]))
    return "".join(out)


def recurring_stage(day, n=RECURRENCE_RUNS):
    """Is one stage doing most of the holding lately? Counted over runs, not days."""
    recent = [p for p in all_runs() if p.name[11:19] <= day.strftime("%Y%m%d")][-n:]
    stages = [(_load(p, "COMPOSITION_RESULT.json") or {}).get("failure_stage")
              for p in recent]
    stages = [s for s in stages if s]
    if not stages:
        return "", 0, 0
    stage, count = collections.Counter(stages).most_common(1)[0]
    return stage, count, len(recent)


def month_cost(day):
    total = 0.0
    pref = day.strftime("%Y%m")
    for p in all_runs():
        if p.name[11:17] == pref and p.name[11:19] <= day.strftime("%Y%m%d"):
            total += total_cost(_load(p, "MANIFEST.json"))
    return total


def last_published(day):
    """(days_ago, title) from _posts -- what actually reached readers."""
    best = None
    try:
        for p in (REPO / "_posts").glob("*.md"):
            m = re.match(r"(\d{4})-(\d{2})-(\d{2})-", p.name)
            if not m:
                continue
            d = datetime.date(*(int(x) for x in m.groups()))
            if d > day:
                continue
            head = p.read_text(encoding="utf-8", errors="replace")[:2000]
            if "withdrawn: true" in head:
                continue
            t = re.search(r'^title:\s*"?(.+?)"?\s*$', head, re.M)
            if best is None or d > best[0]:
                best = (d, t.group(1) if t else p.stem)
    except Exception:
        return None
    if not best:
        return None
    return (day - best[0]).days, best[1]


def corpus_counts():
    """Current vs earlier, using the site's own epoch predicate (_data/backlist.yml)."""
    try:
        y = (REPO / "_data" / "backlist.yml").read_text(encoding="utf-8")
        cutoff = (re.search(r"^legacy_through:\s*(\S+)", y, re.M) or [None, "9999-99-99"])[1]
        byline = (re.search(r'^editor_byline:\s*"(.*?)"', y, re.M) or [None, ""])[1]
        pre = set(re.findall(r"^\s+-\s+(\S+)\s*$",
                             y.split("pre_epoch:", 1)[1], re.M)) if "pre_epoch:" in y else set()
        cur = arch = 0
        for p in (REPO / "_posts").glob("*.md"):
            t = p.read_text(encoding="utf-8", errors="replace")
            fm = t.split("---", 2)[1] if t.startswith("---") else ""
            if re.search(r"^withdrawn:\s*true", fm, re.M):
                continue
            slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", p.stem)
            date = p.stem[:10]
            author = (re.search(r'^author:\s*"?(.*?)"?\s*$', fm, re.M) or [None, ""])[1]
            if author == byline:
                continue                      # editor's notes are not essays
            is_cur = (slug not in pre) and (
                'engine_generation: "CURRENT_ENGINE"' in fm
                or 'editorial_engine: "NEW_ENGINE_V1"' in fm
                or date > cutoff)
            cur += 1 if is_cur else 0
            arch += 0 if is_cur else 1
        return cur, arch
    except Exception:
        return None, None



# ── reading a failure that produced no run directory ────────────────────────────────

LOG = REPO / "automation.log"

# A typed failure is worth translating into the sentence that says what to DO. The
# generic "article generation failed — check automation.log" is true and useless: it
# cannot be acted on from a phone, and on 2026-09-15 it hid a one-command fix for
# nine hours. Anything not listed here is reported verbatim rather than flattened.
FAILURE_HELP = {
    "CLAUDE_SUBSCRIPTION_AUTH_FAILURE":
        ("The Claude CLI is signed out on Trident.",
         "Fix: ssh trident, then: claude auth login\n"
         "(must be the claude.ai subscription login, not --console)"),
    "CLAUDE_SUBSCRIPTION_LIMIT":
        ("The Claude subscription hit its usage limit.",
         "No action: it resets on its own. Tomorrow's 09:00 run should proceed."),
}


def last_failure_from_log(day):
    """The orchestrator failure recorded for `day`, if there is one.

    A provider failure on the first model call leaves no run directory at all, so the
    evidence root cannot answer "what went wrong" -- only the log can.

    Anchored on the wrapper's own "ERROR: orchestrator failed" line for `day`, and then
    the run_status block immediately BEFORE it, so a later successful run on the same
    day cannot be mistaken for the failure and an in-flight run is never read as one.
    Returns (status, stage, detail, reason_code) or None.
    """
    try:
        text = LOG.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None
    marks = [m.end() for m in re.finditer(
        re.escape(day.strftime("[%Y-%m-%d")) + r"[^\]]*\] ERROR: orchestrator failed", text)]
    if not marks:
        return None
    head = text[:marks[-1]]
    blocks = list(re.finditer(r'"run_status":\s*\{(.*?)\}', head, re.S))
    if not blocks:
        return None
    blk = blocks[-1].group(1)
    get = lambda k: (re.search(r'"%s":\s*"([^"]*)"' % k, blk) or [None, ""])[1]
    reasons = re.findall(r'"reason_code":\s*"([^"]+)"', head)
    return get("status"), get("stage"), get("detail"), (reasons[-1] if reasons else "")


def failure_lines(day):
    """Explanatory lines for a failure with no run directory, most useful first."""
    f = last_failure_from_log(day)
    if not f:
        return ["No production run directory for today, and no orchestrator failure "
                "recorded in automation.log. The 09:00 job may not have started."]
    status, stage, detail, reason = f
    out = []
    key = next((k for k in FAILURE_HELP if k in (detail or "") or k in (reason or "")), None)
    if key:
        what, how = FAILURE_HELP[key]
        out.append(what)
        out.append(how)
    else:
        out.append(detail or reason or "unknown failure")
    tail = "%s%s" % (status or "FAILURE", " at %s" % stage if stage else "")
    out.append("(%s)" % tail)
    return out


# ── the message ─────────────────────────────────────────────────────────────────────

def build_message(day):
    d = day.strftime("%a %-d %b")
    rs = runs_for(day)

    if not rs:
        strip = outcome_strip(day)
        lp = last_published(day)
        extra = "\nLast published: %d days ago" % lp[0] if lp else ""
        why = failure_lines(day)
        title = "⚠️ FAILED" if last_failure_from_log(day) else "⚠️ NO RUN"
        return ("\U0001f4d5 Crip Minds — daily run\n%s · %s\n\n%s\n\n"
                "Nothing was written: no run directory, no draft, no post.\n\n"
                "Last %d days: %s%s"
                % (d, title, "\n".join(why), TREND_DAYS, strip, extra))

    run_dir = rs[-1]
    manifest = _load(run_dir, "MANIFEST.json")
    comp = _load(run_dir, "COMPOSITION_RESULT.json")

    if not manifest:
        return ("\U0001f4d5 Crip Minds — daily run\n%s · ⏳ INCOMPLETE\n\n"
                "%s exists but has written no MANIFEST.json. Still running, or it "
                "stopped mid-flight." % (d, run_dir.name))

    outcome, owner_path = final_outcome(run_dir)
    glyph = GLYPH.get(outcome, GLYPH["FAIL"])
    stage = comp.get("failure_stage") or ""
    head = "%s · %s %s%s" % (d, glyph, outcome,
                                  " at %s" % stage if outcome == "HOLD" and stage else "")

    L = ["\U0001f4d5 Crip Minds — daily run", head, "",
         '"%s"' % headline(run_dir, comp)]

    meta = [x for x in ("%s words" % comp["words"] if comp.get("words") else "",
                        comp.get("compose_mode") or "",
                        ("%dm%02ds" % (int(comp["runtime_seconds"]) // 60,
                                       int(comp["runtime_seconds"]) % 60))
                        if isinstance(comp.get("runtime_seconds"), (int, float)) else "") if x]
    if meta:
        L.append(" · ".join(meta))
    L.append("")

    if outcome == "HOLD":
        why = hold_why(comp)
        if why:
            L.append("Why: %s" % why)
        stages = comp.get("stages") or {}
        ran = {k: v for k, v in stages.items() if v != "NOT_RUN"}
        passed = sum(1 for v in ran.values() if v == "PASS")
        repairs = sum((comp.get("repairs_by_stage") or {}).values())
        if ran:
            L.append("Cleared %d of %d stages%s." %
                     (passed, len(ran),
                      ", %d self-repair%s held" % (repairs, "" if repairs == 1 else "s")
                      if repairs else ""))
    elif outcome in ("PUBLISHED", "ACCEPT", "CLEARED"):
        L.append({"PUBLISHED": "Published — it reached readers.",
                   "CLEARED": "Cleared for publication.",
                   "ACCEPT": "Accepted by the engine."}[outcome])
        if owner_path:
            L.append("(owner-repaired before publication)")
    else:
        for r in (manifest.get("reasons") or [])[:2]:
            L.append("  " + str(r)[:150])

    rstat = manifest.get("run_status") or {}
    if isinstance(rstat, dict) and rstat.get("status"):
        L.append("⚠️ Run status: %s at %s" % (rstat.get("status"), rstat.get("stage")))

    # ── context ──
    L.append("")
    L.append("Last %d days: %s" % (TREND_DAYS, outcome_strip(day)))

    lp = last_published(day)
    if lp:
        days_ago, title = lp
        when = "today" if days_ago == 0 else ("yesterday" if days_ago == 1
                                              else "%d days ago" % days_ago)
        L.append("Last published: %s — %s" % (when, title[:44]))

    st, n, of = recurring_stage(day)
    if st and n >= 3:
        L.append("Recurring: %s held %d of last %d runs" % (st, n, of))

    today_cost = total_cost(manifest)
    mc = month_cost(day)
    bits = []
    if comp.get("model_calls_total"):
        bits.append("%s calls" % comp["model_calls_total"])
    if today_cost:
        bits.append("~$%.2f today" % today_cost)
    if mc:
        bits.append("~$%.0f this month" % mc)
    if bits:
        L.append(" · ".join(bits))

    cur, arch = corpus_counts()
    if cur is not None:
        L.append("Corpus: %d current · %d earlier" % (cur, arch))

    return "\n".join(L)


# ── sending ─────────────────────────────────────────────────────────────────────────

def send(text):
    token = os.environ.get("REEF_BOT_TOKEN", "")
    chat = os.environ.get("REEF_CHAT_ID", "")
    if not token or not chat:
        _log("NOT SENT: REEF_BOT_TOKEN/REEF_CHAT_ID missing from environment")
        return False
    data = urllib.parse.urlencode(
        {"chat_id": chat, "text": text, "disable_web_page_preview": "true"}).encode()
    try:
        req = urllib.request.Request(
            "https://api.telegram.org/bot%s/sendMessage" % token, data=data)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            ok = json.loads(r.read().decode("utf-8", "replace")).get("ok")
            _log("sent" if ok else "telegram returned ok=false")
            return bool(ok)
    except Exception as e:
        # Never echo the URL: it carries the token.
        _log("NOT SENT: telegram request failed (%s)" % type(e).__name__)
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="print the message, send nothing")
    ap.add_argument("--date", help="YYYY-MM-DD (default: today)")
    ap.add_argument("--alert-failure", action="store_true",
                    help="send the immediate failure alert (called by cripminds-daily.sh "
                         "when the orchestrator exits non-zero)")
    a = ap.parse_args()
    day = (datetime.datetime.strptime(a.date, "%Y-%m-%d").date()
           if a.date else datetime.date.today())
    if a.alert_failure:
        msg = ("\U0001f4d5 Crip Minds — run failed\n%s\n\n%s"
               % (datetime.datetime.now().strftime("%a %-d %b %H:%M"),
                  "\n".join(failure_lines(day))))
        if not a.dry_run:
            _log("--- failure alert ---")
        print(msg, flush=True)
        if not a.dry_run:
            send(msg)
        return 0
    try:
        msg = build_message(day)
    except Exception as e:
        msg = ("\U0001f4d5 Crip Minds — daily run\n%s\n\nREPORTER ERROR: %s: %s\n"
               "The run itself is unaffected; only this report failed."
               % (day.strftime("%a %-d %b"), type(e).__name__, str(e)[:200]))
    if a.dry_run:
        print(msg)
    else:
        _log("--- daily run report ---")
        print(msg, flush=True)
    if a.dry_run:
        print("\n[dry run — nothing sent]")
        return 0
    send(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
