"""Compact batch adjudication: claim vs complete frozen evidence, several cases at once."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cm_evidence as E

BASE = "/srv/data/cripminds-new-engine-v1/"

CASES = [
    ("601f5d23", "production-20260903T212459Z-601f5d23",
     "The event featured eight pavilions",
     ["eight pavilion", "pavilions", "Nature Weave"]),
    ("tdtalk-pred", "production-20260911T165715Z-17914595",
     "Word prediction is offered as choices so a sentence can be built in fewer selections",
     ["fewer selections", "offered as choices", "selectable", "fewer", "keystroke"]),
    ("asl-quote1", "fast-lane-v1-fresh-asl-whitehouse-20260912",
     "To the extent the defendants argue that they prefer to act free from association with accessibility for people with disabilities, their gripe is with Congress and the Rehabilitation Act itself",
     ["their gripe is with Congress", "gripe"]),
    ("asl-quote2", "fast-lane-v1-fresh-asl-whitehouse-20260912",
     "For the purposes of this action, the defendants concede that section 504(a) applies to them, and wanting to have an 'image' free from its requirements is not a sound basis for declining to provide reasonable accommodations.",
     ["concede that section 504", "sound basis", "image"]),
    ("asl-504", "fast-lane-v1-fresh-asl-whitehouse-20260912",
     "Section 504 prohibits discrimination against people with disabilities in programs conducted by the federal government",
     ["Section 504", "programs conducted by the federal", "cornerstone"]),
    ("imm-emilio", "fast-lane-v1-fresh-immigration-20260912",
     "One of them was Emilio, originally from Venezuela",
     ["Emilio", "Venezuela", "more than 100"]),
    ("tdsnap-hardware", "production-20260911T165715Z-17914595",
     "Tobii Dynavox will not offer technical support for hardware compatibility issues on non-approved hardware",
     ["non-licensed resellers", "will not offer technical support"]),
    ("sfmoma-reagan", "production-20260913T083824Z-f83f4b8a",
     "Creative Growth exists because of decisions made when Ronald Reagan was governor of California",
     ["Reagan", "governor", "trace to", "in response"]),
    ("sfmoma-born", "production-20260913T083824Z-f83f4b8a",
     "William Scott was born in the Alice Griffith public housing development in 1964 and grew up there",
     ["Alice Griffith", "where the artist was raised", "Born in San Francisco", "Hayward"]),
]

only = sys.argv[1] if len(sys.argv) > 1 else None

for cid, run_id, claim, greps in CASES:
    if only and only != cid:
        continue
    run = E.load_run(BASE + run_id)
    print("\n" + "=" * 78)
    print("CASE:", cid, "|", run_id)
    print("CLAIM:", claim)
    if not run["sources"]:
        print("  !! no complete frozen source text")
        continue
    joined = " \n".join(v["norm_text"] for v in run["sources"].values())
    low = joined.lower()
    for g in greps:
        gn = E.normalize(g)[0].lower()
        idxs = [m.start() for m in re.finditer(re.escape(gn), low)][:2]
        if not idxs:
            print("  GREP %-38r -> NOT FOUND" % g)
        for i in idxs:
            print("  GREP %-38r -> ...%s..." % (g, joined[max(0, i - 200):i + len(gn) + 200]))
