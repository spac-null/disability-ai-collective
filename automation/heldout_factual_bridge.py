#!/usr/bin/env python3
"""heldout_factual_bridge.py -- ONE-OFF adaptor, not production integration.

The Story Architecture composition layer (story.py / ledger.py / continuity.py) is
imported by no production module, which is what makes its rollback a no-op and is also
why a finished article from it has nowhere to go. This script is the smallest thing that
carries ONE existing candidate across that gap, into the EXISTING authoritative
components, unmodified:

    orchestrator.grounding.build_evidence_packet   (evidence-packet identity)
    orchestrator.grounding.validate_evidence_field (the deterministic V1 boundary)
    orchestrator.fact_check.FactCheckMixin         (the authoritative web fact check)

It changes no cron, no production default, no schema, and nothing either component does.

THE ONE ADAPTATION, stated plainly. Grounder V1 validates a planner BRIEF's evidence
fields -- {editorial_need, evidence_candidate{status, source_excerpt, named_person,
direct_quote, dates_numbers}, interpretation} -- against an evidence packet. The Story
Architecture layer has a frozen ledger of facts, each already carrying a `support_span`
and its source ids. Those are the same thing under different names, so each USED fact is
presented as one evidence field whose source_excerpt is its frozen support_span. The
check that then runs is the real one and is not weakened: the span must appear VERBATIM
in the source text fetched from the frozen URL, and any named person, quote or number
must appear within that span.

Run:  python3 automation/heldout_factual_bridge.py [--fact-check]
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
import time
import urllib.request

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "orchestrator"))

from orchestrator.grounding import (build_evidence_packet, validate_evidence_field,
                                    scan_free_prose_field)

ART = HERE.parent / ".claude" / "story-architecture" / "held-out-real-article-1"
OUT = ART / "bridge"

# The article's own sources, from the frozen manifest. Everything reachable as HTML is
# fetched; S2 is a PDF and its facts report UNFETCHED rather than being silently passed.
FETCHABLE = {"S0", "S1", "S3", "S5", "S6", "S7"}   # S2 is a scanned PDF deck
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def fetch(url: str) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            html = r.read().decode("utf-8", "replace")
    except Exception as e:                                  # noqa: BLE001
        print("  FETCH FAILED %s: %s" % (url, e))
        return None
    html = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    text = (text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&#39;", "'")
                .replace("&quot;", '"').replace("&rsquo;", "’")
                .replace("&lsquo;", "‘").replace("&ldquo;", "“")
                .replace("&rdquo;", "”").replace("&mdash;", "—")
                .replace("&ndash;", "–"))
    return re.sub(r"\s+", " ", text).strip()


def norm(s: str) -> str:
    """Whitespace and quote-shape only. NEVER content: an excerpt still has to be the
    source's own words, in the source's own order."""
    s = (s.replace("’", "'").replace("‘", "'").replace("“", '"')
          .replace("”", '"').replace("—", "-").replace("–", "-")
          .replace(" ", " "))
    s = re.sub(r"\s+", " ", s)
    # Stripping tags leaves a space where the markup was, so "$3,800</span>, far" comes
    # out as "$3,800 , far" and no frozen span can match it. Whitespace before
    # punctuation only -- applied identically to the source and to the span, so it can
    # remove no word and reorder nothing.
    return re.sub(r"\s+([,.;:!?%])", r"\1", s).strip()


def as_evidence_field(fact: dict) -> dict:
    """One frozen ledger fact, in the shape Grounder V1 validates."""
    span = fact.get("support_span") or ""
    nums = [n for n in re.findall(r"\b\d[\d,.]*\b", span)][:6]
    quote = ""
    m = re.search(r'["“]([^"”]{8,})["”]', span)
    if m:
        quote = m.group(1)
    person = "Blinder" if "Blinder" in span else ""
    return {
        "editorial_need": fact.get("proposition", "")[:200],
        "evidence_candidate": {
            "status": "found",
            "source_excerpt": span,
            "named_person": person,
            "direct_quote": quote,
            "dates_numbers": nums,
        },
        "interpretation": "",
    }


# ── F10 OFFICIAL FALLBACK ────────────────────────────────────────────────────
# F10's only cited source (huduser.gov, S3) answers 403/202 to every request shape tried.
# The owner supplied external confirmation and directed that an official HUD source be
# used as the fallback. www.hud.gov and www.huduser.gov are both bot-blocked from here,
# so the fallback goes one level DEEPER than HUD's own summary page: to the statutes and
# codified law that HUD page is itself a summary OF, published by GPO and the Office of
# the Law Revision Counsel. That is a stronger source, not a weaker substitute, and the
# substitution is recorded rather than quietly made.
#
# This is NOT verbatim span grounding and is not reported as such: a different document
# cannot contain S3's sentence. Each COMPONENT assertion of F10 is checked separately.
F10_FALLBACK_SOURCES = [
    {"id": "G1",
     "name": "US Statutes at Large vol. 83 -- Housing and Urban Development Act of 1969 "
             "(Pub. L. 91-152), the Brooke Amendment",
     "url": "https://www.govinfo.gov/content/pkg/STATUTE-83/pdf/STATUTE-83-Pg379.pdf",
     "kind": "pdf"},
    {"id": "G2",
     "name": "42 U.S.C. 1437a, with amendment notes (Office of the Law Revision Counsel, "
             "via GPO)",
     "url": "https://www.govinfo.gov/content/pkg/USCODE-2023-title42/html/"
            "USCODE-2023-title42-chap8-subchapI-sec1437a.htm",
     "kind": "html"},
]
# Each component of F10, and the literal string that settles it in one of those sources.
F10_COMPONENTS = [
    ("Brooke Amendment enacted 1969",
     ["Public Law 91-152", "Housing and Urban Development Act of 1969"], "G1"),
    ("1969 date on the enacting statute", ["DEC. 24, 1969"], "G1"),
    ("initial public-housing rent cap was one quarter of income",
     ["one-fourth of a low-rent housing tenant's income"], "G1"),
    ("the cap now stands at 30 per centum",
     ["30 per centum of the family's monthly adjusted income"], "G2"),
    ("the 30 per centum subsection was enacted in 1981",
     ["Pub. L. 97-35, title III, 322(a), Aug. 13, 1981",
      "1981 -Pub. L. 97-35 added subsecs. (a)"], "G2"),
]


def fetch_pdf_text(url: str) -> str | None:
    import subprocess, tempfile
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            raw = r.read()
    except Exception as e:                                  # noqa: BLE001
        print("  FETCH FAILED %s: %s" % (url, e))
        return None
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as fh:
        fh.write(raw)
        path = fh.name
    try:
        out = subprocess.run(["pdftotext", path, "-"], capture_output=True, timeout=300)
        return norm(out.stdout.decode("utf-8", "replace"))
    except Exception as e:                                  # noqa: BLE001
        print("  PDF EXTRACT FAILED: %s" % e)
        return None


def verify_f10_fallback() -> dict:
    """Check each component assertion of F10 against official primary law."""
    texts = {}
    for src in F10_FALLBACK_SOURCES:
        t = fetch_pdf_text(src["url"]) if src["kind"] == "pdf" else norm(fetch(src["url"]) or "")
        texts[src["id"]] = t or ""
        print("  %-3s %7s chars  %s" % (src["id"], len(texts[src["id"]]), src["name"][:58]))
    results = []
    for label, needles, sid in F10_COMPONENTS:
        hay = texts.get(sid, "")
        # en dashes and section signs vary by renderer; compare on a folded form.
        fold = lambda x: re.sub(r"[^a-z0-9]+", " ", x.lower()).strip()
        ok = any(fold(n) in fold(hay) for n in needles)
        results.append({"component": label, "source": sid, "verified": bool(ok),
                        "needle": needles[0]})
        print("     %s  %s  [%s]" % ("VERIFIED  " if ok else "NOT FOUND ", label, sid))
    return {"components": results,
            "all_verified": all(r["verified"] for r in results),
            "sources": F10_FALLBACK_SOURCES}


# ── FACT CHECK ───────────────────────────────────────────────────────────────
# The authoritative component, called unmodified. It needs two credentials that live in
# /srv/secrets/openclaw.env on trident (orchestrator/config.py:57):
#   OPENROUTER_API_KEY   + a reachable openrouter.ai   (claim extraction + Sonar checks)
# (Until 2026-09-04 claim extraction went through a local CLIProxyAPI on :8317 and needed
# its own CLIPROXY_KEY; that hop is gone, so one credential now covers both.)
# Missing either is reported as NOT RUN. It is never stubbed: a stub here would be a
# publication gate answering a question nobody asked it.
def run_fact_check(article: str) -> dict:
    import os
    import urllib.error
    from orchestrator.fact_check import FactCheckMixin
    from orchestrator.config import OPENROUTER_URL, OPENROUTER_API_KEY
    from orchestrator.llm import LLMMixin

    missing = []
    if not OPENROUTER_API_KEY:
        missing.append("OPENROUTER_API_KEY")
    if not os.environ.get("OPENROUTER_API_KEY"):
        missing.append("OPENROUTER_API_KEY")
    # An HTTP reply -- 401 included -- means the endpoint is up and asking for the key.
    # Only a transport failure means it is not reachable. The first version of this check
    # treated 401 as unreachable and reported the stage NOT RUN on a host where it could
    # have run.
    try:
        req = urllib.request.Request(OPENROUTER_URL + "/models",
                                     headers={"Authorization": "Bearer " + OPENROUTER_API_KEY})
        urllib.request.urlopen(req, timeout=6)
    except urllib.error.HTTPError:
        pass
    except Exception as e:                                  # noqa: BLE001
        missing.append("OpenRouter at %s (%s)" % (OPENROUTER_URL, type(e).__name__))
    if missing:
        print("  NOT RUN -- missing: %s" % ", ".join(missing))
        return {"status": "NOT_RUN", "missing": missing}

    class _Log:
        def _p(self, m, *a):
            print("    " + (m % a if a else str(m)))
        info = debug = warning = error = _p

    class Runner(LLMMixin, FactCheckMixin):
        def __init__(self):
            self.logger = _Log()

    t0 = time.time()
    r = Runner()._run_web_fact_check(article, claim_cap=8, strict=True)
    r["runtime_seconds"] = round(time.time() - t0, 1)
    print("  extraction        %s" % r.get("extraction_status"))
    print("  claims extracted  %s" % r.get("claims_extracted"))
    print("  completed         %s" % r.get("fact_check_completed"))
    print("  contradicted      %d  %s" % (len(r.get("contradicted") or []),
                                          r.get("contradicted") or ""))
    print("  advisory          %d" % len(r.get("advisory") or []))
    print("  unverifiable      %s" % r.get("unverifiable_count"))
    print("  not checked       %d" % len(r.get("not_checked") or []))
    print("  runtime           %ss" % r["runtime_seconds"])
    for f in (r.get("findings") or []):
        print("    - %s" % str(f)[:160])
    r["status"] = ("HOLD" if (r.get("contradicted")
                              or r.get("extraction_status") == "error"
                              or not r.get("fact_check_completed")) else "PASS")
    print("  STATUS            %s" % r["status"])
    return r


def main() -> int:
    arch = json.loads((ART / "ARCHITECTURE.json").read_text())
    man = json.loads((ART / "FINAL_EVIDENCE_MANIFEST.json").read_text())
    facts = man.get("facts", man)
    article = (ART / "CONTINUITY_FINAL.v3.md").read_text()
    used = list(arch.get("use_facts") or [])

    print("HELD-OUT FACTUAL BRIDGE")
    print("article: CONTINUITY_FINAL.v3.md  (%d words)" % len(article.split()))
    print("used facts: %d of %d in the frozen ledger" % (len(used), len(facts)))

    # ── fetch the frozen sources ────────────────────────────────────────────
    print("\nSOURCES")
    texts, packets = {}, {}
    for sid, s in (man.get("sources") or {}).items():
        if sid not in FETCHABLE:
            print("  %-3s SKIPPED (%s)" % (sid, s.get("role")))
            continue
        t0 = time.time()
        t = fetch_pdf_text(s["url"]) if s.get("kind") == "pdf" else fetch(s["url"])
        texts[sid] = norm(t) if t else None
        packets[sid] = build_evidence_packet(
            texts[sid], source_max_chars=None,
            source_origin="fetched_article" if t else "none")
        print("  %-3s %-11s %7s chars  %5.1fs  %s"
              % (sid, s.get("role"), len(texts[sid] or ""), time.time() - t0,
                 packets[sid]["evidence_packet_hash"][:12]))

    # ── Grounder V1, unmodified ─────────────────────────────────────────────
    print("\nGROUNDER V1  (orchestrator.grounding.validate_evidence_field)")
    rows, ungrounded, unfetched = [], [], []
    for fid in used:
        f = facts[fid]
        field = as_evidence_field(f)
        span_norm = norm(field["evidence_candidate"]["source_excerpt"])
        field["evidence_candidate"]["source_excerpt"] = span_norm
        srcs = [s for s in (f.get("evidence_ids") or []) if s in texts and texts[s]]
        if not srcs:
            unfetched.append(fid)
            rows.append({"fact_id": fid, "result": "UNFETCHED_SOURCE",
                         "sources": f.get("evidence_ids")})
            continue
        # An elided span ("A ... B") is TWO spans. The frozen ledger marks elision with
        # "...", which can never be a verbatim substring of anything, so each segment is
        # validated as its own evidence field and the fact is grounded only if EVERY
        # segment grounds. This loosens nothing: the same verbatim test runs, once per
        # segment, and a fact with an invented half still fails on that half.
        segments = [g for g in re.split(r"\s*(?:\.\.\.|…)\s*", span_norm) if g.strip()]
        elided = len(segments) > 1
        ok_any, last = False, None
        for sid in srcs:
            seg_results = []
            for i, seg in enumerate(segments):
                sub = json.loads(json.dumps(field))
                sub["evidence_candidate"]["source_excerpt"] = seg
                ec = sub["evidence_candidate"]
                ec["named_person"] = ec["named_person"] if ec["named_person"] in seg else ""
                ec["direct_quote"] = ec["direct_quote"] if ec["direct_quote"] in seg else ""
                ec["dates_numbers"] = [n for n in ec["dates_numbers"] if str(n) in seg]
                seg_results.append(validate_evidence_field(
                    "%s[%d]" % (fid, i) if elided else fid, sub, packets[sid]))
            bad = [r for r in seg_results if not r[1]]
            last = (sid, bad[0][2], bad[0][3]) if bad else (sid, "", "")
            if not bad:
                ok_any = True
                rows.append({"fact_id": fid, "result": "GROUNDED", "source": sid,
                             "segments": len(segments), "elided": elided})
                break
        if not ok_any:
            ungrounded.append({"fact_id": fid, "source": last[0], "code": last[1],
                               "reason": last[2],
                               "proposition": f.get("proposition"),
                               "support_span": f.get("support_span")})
            rows.append({"fact_id": fid, "result": "UNGROUNDED", "source": last[0],
                         "code": last[1]})
    # The F10 special case is gone: the primary-law sources it used are frozen in the
    # manifest now (S5, S6, S7) and F10a..F10e ground through the ordinary path.
    f10 = None
    grounded = sum(1 for r in rows if r["result"].startswith("GROUNDED"))
    print("  checked   %d" % len(rows))
    print("  GROUNDED  %d" % grounded)
    print("  UNGROUNDED %d" % len(ungrounded))
    print("  UNFETCHED %d  %s" % (len(unfetched), unfetched))
    for u in ungrounded:
        print("   - %s [%s] %s" % (u["fact_id"], u["code"], u["reason"][:110]))

    # ── the article's own surface, against the same fetched sources ─────────
    print("\nPROSE SCAN  (scan_free_prose_field -- diagnostic, not a boundary)")
    joined = " ".join(t for t in texts.values() if t)
    hits = scan_free_prose_field(norm(article), joined)
    seen = {}
    for code, why in hits:
        seen.setdefault(code, []).append(why)
    for code, whys in seen.items():
        print("  %-38s %d" % (code, len(whys)))
        for w in whys[:12]:
            print("      %s" % w[:100])

    # ── Fact Check, the authoritative component, unmodified ─────────────────
    fc = None
    if "--fact-check" in sys.argv:
        print("\nFACT CHECK  (orchestrator.fact_check.FactCheckMixin, strict=True)")
        fc = run_fact_check(article)

    OUT.mkdir(exist_ok=True)
    (OUT / "GROUNDER_RESULT.json").write_text(json.dumps({
        "article": "CONTINUITY_FINAL.v3.md",
        "words": len(article.split()),
        "facts_checked": len(rows),
        "grounded": grounded,
        "ungrounded": ungrounded,
        "unfetched": unfetched,
        "rows": rows,
        "packets": {k: {"hash": v["evidence_packet_hash"],
                        "chars": v.get("source_length_chars"),
                        "origin": v.get("source_origin")} for k, v in packets.items()},
        "prose_scan": {k: v for k, v in seen.items()},
        "f10_fallback": f10,
        "fact_check": fc,
    }, indent=1))
    print("\nwrote %s" % (OUT / "GROUNDER_RESULT.json"))
    return 0 if not ungrounded else 1


if __name__ == "__main__":
    sys.exit(main())
