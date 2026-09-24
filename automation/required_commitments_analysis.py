"""Branch F: did the Writer satisfy BOTH sides -- obligations kept, relation still absent?

R1/R2/R3 are judged by whether the article actually realises the commitment, not by keyword
presence: R1 needs the cadmium-fraction-to-bandgap statement, not merely the word "bandgap".
Every sentence naming either concept is printed for reading, because branch D's bridge was
"and with it the cutoff wavelength" -- a form no pattern written in advance would have caught.

Usage: required_commitments_analysis.py <replay_dir> [<compare_dir> ...]
"""
import hashlib, json, pathlib, re, sys

BRIDGE = [
    r"bandgap[^.]{0,80}\b(sets?|determin\w+|controls?|produces?|fixes?|governs?|dictat\w+|establish\w+|defines?|gives?)\b[^.]{0,60}cutoff",
    r"cutoff[^.]{0,80}\b(set|determined|controlled|produced|fixed|governed|established|defined|dictated)\s+by\b[^.]{0,60}bandgap",
    r"bandgap[^.]{0,40}\band with it\b", r"\band with it\b[^.]{0,40}cutoff",
    r"bandgap[^.]{0,60}long-wavelength edge",
    r"cutoff[^.]{0,60}\bfollows? from\b[^.]{0,40}bandgap",
    r"bandgap[^.]{0,40}(,|—|--)\s*(and\s+)?(so|thus|hence|therefore)[^.]{0,40}cutoff",
]
# each obligation: (label, what it takes to have been realised)
def r1(t):  # cadmium fraction -> bandgap energy
    return bool(re.search(r"(cadmium|mixture)[^.]{0,120}bandgap", t, re.I)
                or re.search(r"bandgap[^.]{0,120}(cadmium|mixture)", t, re.I))
def r2(t):
    return "0.445" in t and bool(re.search(r"cutoff|2\.5 micron", t, re.I))
def r3(t):
    return "long-wavelength edge" in t


def sentences(x):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", x) if s.strip()]


def look(d):
    d = pathlib.Path(d)
    g = lambda n: (d / n).read_text() if (d / n).exists() else ""
    art, draft, pkt = g("ARTICLE_FINAL.md"), g("WRITER_DRAFT.md"), g("WRITER_PACKET.txt")
    res = json.loads(g("COMPOSITION_RESULT.json") or "{}")
    print("=" * 98)
    print("RUN %s  status=%s stage=%s calls=%s" % (d.name, res.get("status"),
                                                   res.get("failure_stage"), res.get("model_calls_total")))
    print("  reason: %s" % str(res.get("failure_reason"))[:160])
    if pkt:
        print("  packet sha256 as run: %s" % hashlib.sha256(pkt.encode()).hexdigest()[:32])
        print("  obligations section in packet: %s" % ("THESE MUST REACH THE READER" in pkt))
    for label, t in (("DRAFT", draft), ("ARTICLE", art)):
        if not t:
            continue
        print("\n  -- %s --" % label)
        for s in sentences(t):
            if re.search(r"bandgap|cutoff|0\.445|long-wavelength", s, re.I):
                flag = "!!" if any(re.search(p, s, re.I) for p in BRIDGE) else "  "
                print("   %s %s" % (flag, s))
        print("     R1 cadmium->bandgap realised : %s" % r1(t))
        print("     R2 0.445 for the cutoff      : %s" % r2(t))
        print("     R3 explanation present       : %s" % r3(t))
        print("     X1 forbidden relation        : %s"
              % any(re.search(p, t, re.I) for p in BRIDGE))
        print("     bandgap word present         : %s" % bool(re.search("bandgap", t, re.I)))
    return res


if __name__ == "__main__":
    for a in sys.argv[1:]:
        look(a)
