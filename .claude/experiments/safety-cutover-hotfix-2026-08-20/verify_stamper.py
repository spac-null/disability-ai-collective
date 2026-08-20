#!/usr/bin/env python3
"""
Operational verification of _maybe_stamp_publication_safety_version.

It has never fired in production (0/165 articles carry the stamp), so before it is
relied upon its behaviour is verified deterministically against temp fixtures.
No article created, no model call, no network, no production file touched.
"""
import pathlib, re, sys, tempfile
REPO = pathlib.Path(__file__).resolve().parents[3]   # -> repo root
assert (REPO / 'automation').is_dir(), 'repo root resolution failed: %s' % REPO
sys.path.insert(0, str(REPO / 'automation'))
from orchestrator.generate import GenerateMixin

FAIL = []
def check(n, c, d=""):
    print(("  PASS  " if c else "  FAIL  ") + n + ("" if c else "  " + str(d)))
    if not c: FAIL.append(n)

class Stub(GenerateMixin):
    PUBLICATION_SAFETY_CONTRACT_VERSION = 1

FM = ('---\nlayout: post\ntitle: "T"\nauthor: "Maya Flux"\ndate: 2026-08-16\n'
      'fact_check_status: {fc}\npublish_attempts: 1\n---\n\nBody text.\n')

def mk(d, fc, extra=""):
    p = pathlib.Path(d) / "a.md"
    t = FM.format(fc=fc)
    if extra: t = t.replace("---\n\nBody", extra + "---\n\nBody")
    p.write_text(t); return p

s = Stub()
print("stamper predicate: should_block falsy AND fact_check_status=='verified' AND no existing stamp\n")

with tempfile.TemporaryDirectory() as d:
    # 1. pass condition writes the version exactly once
    p = mk(d, "verified"); before = p.read_text()
    s._maybe_stamp_publication_safety_version(p, False)
    t = p.read_text()
    check("pass condition stamps the version", "publication_safety_version: 1" in t)
    check("stamped exactly once", t.count("publication_safety_version:") == 1)
    check("stamp is inside front matter", t.index("publication_safety_version") < t.index("\n---\n\nBody"))

    # unrelated front matter unchanged
    for field in ['layout: post', 'title: "T"', 'author: "Maya Flux"', 'date: 2026-08-16',
                  'fact_check_status: verified', 'publish_attempts: 1']:
        check("unrelated front matter preserved: %s" % field.split(':')[0], field in t)
    check("body unchanged", t.endswith("Body text.\n"))
    check("only one line added", len(t.splitlines()) == len(before.splitlines()) + 1)

    # 2. idempotent
    s._maybe_stamp_publication_safety_version(p, False)
    check("repeat invocation is idempotent", p.read_text() == t)

with tempfile.TemporaryDirectory() as d:
    # 3. fail: should_block true
    p = mk(d, "verified"); b = p.read_text()
    s._maybe_stamp_publication_safety_version(p, True)
    check("should_block=True writes nothing", p.read_text() == b)

with tempfile.TemporaryDirectory() as d:
    # 4. fail: fact_check not verified
    for fc in ("blocked", "unverified", "VERIFIED", ""):
        p = mk(d, fc); b = p.read_text()
        s._maybe_stamp_publication_safety_version(p, False)
        check("fact_check_status=%r writes nothing" % fc, p.read_text() == b)

with tempfile.TemporaryDirectory() as d:
    # 5. missing fact_check_status entirely
    p = pathlib.Path(d) / "b.md"
    p.write_text('---\ntitle: "T"\n---\n\nBody\n'); b = p.read_text()
    s._maybe_stamp_publication_safety_version(p, False)
    check("missing fact_check_status writes nothing", p.read_text() == b)

with tempfile.TemporaryDirectory() as d:
    # 6. existing stamp never overwritten
    p = mk(d, "verified", extra="publication_safety_version: 99\n")
    s._maybe_stamp_publication_safety_version(p, False)
    check("existing stamp not overwritten", "publication_safety_version: 99" in p.read_text())
    check("no duplicate stamp added", p.read_text().count("publication_safety_version:") == 1)

# 7. selector sees a correctly stamped candidate as eligible
import publish_best as PB
with tempfile.TemporaryDirectory() as d:
    p = mk(d, "verified")
    s._maybe_stamp_publication_safety_version(p, False)
    fm = PB.parse_frontmatter(p.read_text())
    check("selector: _ordinary_eligibility_ok on stamped draft", PB._ordinary_eligibility_ok(fm))
    check("selector: _current_safety_contract_ok on stamped draft", PB._current_safety_contract_ok(fm))
    p2 = mk(d, "verified")   # unstamped
    fm2 = PB.parse_frontmatter(p2.read_text())
    check("selector: unstamped draft correctly INELIGIBLE", not PB._current_safety_contract_ok(fm2))

print()
print("FAILED: %d" % len(FAIL) if FAIL else "ALL STAMPER VERIFICATION CHECKS PASSED")
sys.exit(1 if FAIL else 0)
