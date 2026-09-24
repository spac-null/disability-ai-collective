"""Branch E: the frozen commitment-slice-repaired plan, plus exactly ONE prohibition.

Positive plan surgery (branch D) removed the unsupported bridge from every Architecture
surface and the Writer rebuilt it anyway, reaching across beats for a fact that sat ten lines
further down the same packet. This tests the one remaining plan-level lever that operates at
the scope the Writer actually reads: `prohibitions`, an EXISTING Architecture field the packet
renders verbatim in its RULES block.

Nothing else changes. The architecture is read from branch-D and one string is appended to one
list. Every static check below exists to prove that is the only delta.

Usage: packet_prohibition_experiment.py <out_dir>
"""
import copy, hashlib, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from new_engine_v1 import story as ST                        # noqa: E402
from new_engine_v1 import composition as CP                  # noqa: E402

E = pathlib.Path("/srv/data/cripminds-repair-compiler-2026-09-24")
D = E / "branch-D"
TERM = "cutoff wavelength"

# The one prohibition. Modelled on the plan's own canonical form -- an imperative naming the
# move, then a semicolon and the boundary, exactly like the existing
#   "Do not merge the unilluminated read-noise exposures with the roughly two-hour
#    dark-current exposures into one set; they are separate tests with separate purposes."
#
# It forbids the RELATION and nothing else: both concepts may still be named, the term may
# still be explained, F86 and F87 and the cadmium-fraction material are all still permitted.
# The boundary clause says the step is NOT ESTABLISHED, never that it is false -- the evidence
# is silent on it, and telling the Writer otherwise would be inventing a negative fact.
PROHIBITION = ("Do not state or imply that the bandgap energy sets, determines, controls or "
               "produces the cutoff wavelength; the cadmium fraction's relation to each is "
               "established separately, and the step between them is not.")

FORBIDDEN_TO_BAN = ["bandgap energy", "cutoff wavelength"]


def sha(x):
    return hashlib.sha256(x.encode("utf-8") if isinstance(x, str) else x).hexdigest()


def jsha(o):
    return sha(json.dumps(o, sort_keys=True, ensure_ascii=False))


def main(out_dir):
    out = pathlib.Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    base = json.loads((D / "ARCHITECTURE.json").read_text())
    led = json.loads((D / "LEDGER.json").read_text())
    if isinstance(led, dict) and "facts" in led:
        led = led["facts"]
    manifest = json.loads((D / "FINAL_EVIDENCE_MANIFEST.json").read_text())["facts"]

    arch = copy.deepcopy(base)
    arch["prohibitions"] = list(base.get("prohibitions") or []) + [PROHIBITION]

    checks, fail = [], False

    def chk(name, cond, note=""):
        nonlocal fail
        checks.append({"check": name, "pass": bool(cond), "note": note})
        if not cond:
            fail = True
        print("  %s  %-58s %s" % ("PASS" if cond else "FAIL", name, note))

    print("STATIC CHECKS (branch D -> branch E)\n")
    # 1
    chk("1 definition bridge still absent",
        "bandgap" not in arch["definitions"][TERM],
        repr(arch["definitions"][TERM])[:70] + "...")
    # 2
    EXPL = "the long-wavelength edge of what the detector material will register"
    chk("2 protected explanation byte-identical",
        EXPL in arch["definitions"][TERM] and arch["definitions"][TERM] == base["definitions"][TERM],
        "gloss sha %s" % sha(arch["definitions"][TERM])[:16])
    # 3
    b4 = next(b for b in arch["beats"] if b["beat_id"] == "B4")
    chk("3 F86 still at its MOVE location (B4)", "F86" in (b4.get("facts_allowed") or []),
        "B4 facts_allowed=%s" % b4["facts_allowed"])
    # 4
    b3, b3b = (next(b for b in a["beats"] if b["beat_id"] == "B3") for a in (arch, base))
    chk("4 B3 unchanged from its repaired form", b3 == b3b,
        "bandgap in B3 prose: %s" % ("bandgap" in b3["happens"]))
    # 5
    a2, b2 = copy.deepcopy(arch), copy.deepcopy(base)
    a2.pop("prohibitions"); b2.pop("prohibitions")
    chk("5 every other Architecture field byte-identical",
        json.dumps(a2, sort_keys=True) == json.dumps(b2, sort_keys=True),
        "sha %s" % jsha(a2)[:16])
    # 6
    added = [p for p in arch["prohibitions"] if p not in (base.get("prohibitions") or [])]
    chk("6 exactly one prohibition added",
        len(added) == 1 and len(arch["prohibitions"]) == len(base["prohibitions"]) + 1
        and arch["prohibitions"][:-1] == base["prohibitions"],
        "%d -> %d, appended" % (len(base["prohibitions"]), len(arch["prohibitions"])))
    # 9
    chk("9 definition_evidence untouched",
        arch.get("definition_evidence") == base.get("definition_evidence"),
        str(arch["definition_evidence"][TERM]))
    # 8
    ids = set(manifest.keys())
    verrs = (ST.validate_architecture(arch, ids, led)
             + ST.validate_definition_support(arch, led)
             + ST.validate_evidence_hierarchy(arch, ids))
    chk("8 current Architecture validators pass", not verrs, str(verrs[:2]) if verrs else "CLEAN")
    # 10 -- reusing the frozen detector result; the gloss is byte-identical to the one it saw
    rc = json.loads((E / "exp1" / "RECHECK.json").read_text())["A_bandgap"]
    prev = json.loads((E / "exp1" / "A_bandgap" / "REPAIRED_ARCHITECTURE.json").read_text())
    flagged = [c["commitment"] for r in rc["definitions"] if r["term"] == TERM
               for c in r["claims"] if c["status"] in ("NOT_ESTABLISHED", "CONTRADICTED")]
    chk("10 Claim Support Shadow clean (frozen, gloss byte-identical)",
        prev["definitions"][TERM] == arch["definitions"][TERM] and not flagged,
        "0 flagged; reused, no detector call")

    # 7 -- render the packet OFFLINE. writer_packet() takes no provider, so this is the exact
    #      prompt the Writer will be handed, provable before a single token is paid for.
    packet, rendered = CP.writer_packet(arch, led)
    chk("7 the prohibition reaches the Writer packet verbatim", PROHIBITION in rendered,
        "packet sha %s" % sha(rendered)[:16])

    print("\nPACKET INSPECTION")
    low = rendered.lower()
    pi = {}
    pi["bandgap available somewhere"] = "bandgap" in low
    pi["cutoff explanation available"] = EXPL.lower() in low
    pi["prohibition at packet scope (RULES)"] = PROHIBITION in rendered.split("RULES")[-1]
    # the relation must be nowhere POSITIVELY asserted
    import re
    assertions = re.findall(r"[^.\n]*bandgap[^.\n]*", rendered, flags=re.I)
    positive = [a.strip() for a in assertions if PROHIBITION[:40] not in a]
    pi["relation nowhere positively asserted"] = not any(
        re.search(r"bandgap[^.]{0,60}(sets|determines|controls|produces|gives|and with it)[^.]{0,40}cutoff", a, re.I)
        or re.search(r"cutoff[^.]{0,60}(set|determined|controlled|produced) by[^.]{0,40}bandgap", a, re.I)
        for a in positive)
    pi["prohibition scoped to relation, not concepts"] = all(
        not PROHIBITION.lower().startswith("do not mention") for _ in [0]) and all(
        c in rendered.lower() for c in FORBIDDEN_TO_BAN)
    for k, v in pi.items():
        print("  %s  %s" % ("PASS" if v else "FAIL", k))
        if not v:
            fail = True
    print("\n  every packet line mentioning bandgap:")
    for a in positive:
        print("     %s" % a[:150])

    (out / "ARCHITECTURE.json").write_text(json.dumps(arch, indent=2, ensure_ascii=False))
    (out / "WRITER_PACKET_FROZEN.txt").write_text(rendered)
    for f in ("RESEARCH_PACK.json", "FINAL_EVIDENCE_MANIFEST.json",
              "WORTH_AND_CANDIDATE.json", "LEDGER.json"):
        (out / f).write_text((D / f).read_text())
    rec = {"prohibition": PROHIBITION,
           "base_architecture_sha256": jsha(base),
           "e_architecture_sha256": jsha(arch),
           "frozen_packet_sha256": sha(rendered),
           "gloss_sha256": sha(arch["definitions"][TERM]),
           "checks": checks, "packet_inspection": pi,
           "model_calls_this_step": 0}
    (out / "STATIC.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False))
    print("\nfrozen packet sha256: %s" % sha(rendered))
    print("E architecture sha256: %s" % jsha(arch))
    print("\n%s" % ("STOP -- a static check failed" if fail else "ALL STATIC CHECKS PASS"))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/branch-E"))
