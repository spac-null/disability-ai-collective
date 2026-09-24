"""Read branch E's output for the target relation, the explanation, and the legitimate facts.

Regex alone cannot decide whether a bridge was asserted -- branch D's "and with it the cutoff
wavelength" is a bridge that no keyword list written beforehand would have contained. So this
prints every sentence carrying either concept, in full, for reading, and uses patterns only to
flag candidates.

Usage: packet_prohibition_analysis.py <replay_dir>
"""
import json, pathlib, re, sys, hashlib

EXPL = "long-wavelength edge"
BRIDGE = [
    r"bandgap[^.]{0,80}\b(sets?|determin\w+|controls?|produces?|fixes?|governs?|dictat\w+|establish\w+|defines?|gives?)\b[^.]{0,60}cutoff",
    r"cutoff[^.]{0,80}\b(set|determined|controlled|produced|fixed|governed|established|defined|dictated)\s+by\b[^.]{0,60}bandgap",
    r"bandgap[^.]{0,40}\band with it\b",
    r"\band with it\b[^.]{0,40}cutoff",
    r"bandgap[^.]{0,60}(long-wavelength edge)",
    r"cutoff[^.]{0,60}\bfollows? from\b[^.]{0,40}bandgap",
    r"bandgap[^.]{0,40}(,|—|--)\s*(and\s+)?(so|thus|hence|therefore)[^.]{0,40}cutoff",
]


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def main(d):
    d = pathlib.Path(d)
    art = (d / "ARTICLE_FINAL.md")
    art = art.read_text() if art.exists() else ""
    draft = (d / "WRITER_DRAFT.md")
    draft = draft.read_text() if draft.exists() else ""
    pkt = (d / "WRITER_PACKET.txt")
    pkt = pkt.read_text() if pkt.exists() else ""
    pkg = (d / "EDITORIAL_PACKAGE.json")
    pkg = pkg.read_text() if pkg.exists() else ""
    res = json.loads((d / "COMPOSITION_RESULT.json").read_text()) if (d / "COMPOSITION_RESULT.json").exists() else {}

    print("RUN: %s" % d.name)
    print("  status=%s stage=%s calls=%s mode=%s" % (res.get("status"), res.get("failure_stage"),
                                                     res.get("model_calls_total"), res.get("compose_mode")))
    print("  reason: %s" % str(res.get("failure_reason"))[:150])
    print("  packet sha256 as run: %s" % hashlib.sha256(pkt.encode()).hexdigest())

    for label, text in (("WRITER DRAFT", draft), ("FINAL ARTICLE", art)):
        if not text:
            continue
        print("\n" + "=" * 96)
        print("%s -- every sentence naming either concept" % label)
        hits = [s for s in sentences(text) if re.search(r"bandgap|cutoff", s, re.I)]
        for s in hits:
            flags = [p for p in BRIDGE if re.search(p, s, re.I)]
            print("   %s %s" % ("!!" if flags else "  ", s))
        print("   -- pattern-flagged bridge candidates: %d" % sum(
            1 for s in hits if any(re.search(p, s, re.I) for p in BRIDGE)))
        print("   -- explanation present: %s" % (EXPL in text))
        print("   -- bandgap mentioned at all: %s   cutoff mentioned: %s"
              % (bool(re.search("bandgap", text, re.I)), bool(re.search("cutoff", text, re.I))))
        print("   -- cadmium fraction 0.445 present: %s" % ("0.445" in text))
        print("   -- WFI range 0.48/2.3 present: %s" % ("0.48" in text and "2.3" in text))

    print("\n" + "=" * 96)
    print("PACKAGE: bandgap=%s cutoff=%s" % (bool(re.search("bandgap", pkg, re.I)),
                                             bool(re.search("cutoff", pkg, re.I))))
    print("GATES REACHED: %s" % sorted(p.name for p in d.glob("*.json")))


if __name__ == "__main__":
    main(sys.argv[1])
