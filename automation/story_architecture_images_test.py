#!/usr/bin/env python3
"""story_architecture_images_test.py -- every engine's articles get illustrated.

Illustration lived inside the LEGACY composition path: orchestrator/generate.py called
generate_images(), orchestrator/publish.py called _insert_images_balanced(). Story
Architecture has neither call, so from the 2026-09-05 cutover every CURRENT_ENGINE article
published without illustrations and nothing reported it -- no gate checks for images, and a
provider route that is healthy but has no caller looks exactly like a working system.

Measured in the published record before the fix:

    2026-09-06  the-upper-room-at-wildsumaco                     figures=0   CURRENT_ENGINE
    2026-09-03  a-conservation-centre-built-around-a-blocked...  figures=0   CURRENT_ENGINE
    2026-09-01  roman-launches-with-its-data-pipeline-built-in   figures=0   CURRENT_ENGINE
    2026-08-08  jebel-irhoud-broke-the-single-dot-i-was-trusting figures=2   legacy

Three things to prove, and the third matters as much as the first: Story Architecture now
reaches the image path, legacy is untouched, and nothing generates twice.

Stdlib only, no network, no image generation.
"""
import ast
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

FAILURES = []
CHECKS = [0]
HERE = os.path.dirname(os.path.abspath(__file__))


def check(label, cond, detail=""):
    CHECKS[0] += 1
    print(("  PASS  %s" if cond else "  FAIL  %s") % label
          + (("" if cond else " -- " + detail) if detail else ""))
    if not cond:
        FAILURES.append(label)


def src(name):
    return open(os.path.join(HERE, name), encoding="utf-8").read()


PB = src("publish_best.py")
GI = src("gen_images.py")

print("test_1_story_architecture_articles_now_reach_the_image_path")
check("publish_best calls the shared entry point",
      "gen_images.illustrate_post(dest)" in PB)
check("it does so at the promotion boundary, right after the post is dated",
      PB.index("set_publish_date(dest, now)") < PB.index("gen_images.illustrate_post(dest)")
      < PB.index("archived = []"))
check("promotion is the boundary BOTH engines cross",
      "shutil.move(str(best_draft), str(dest))" in PB,
      "a Story Architecture draft becomes a post here, exactly as a legacy one does")
check("the generated assets are staged for the commit",
      'mutated += res["assets"]' in PB,
      "images that are not staged never reach the site")
check("gen_images exposes one entry point that both generates and places",
      "def illustrate_post(" in GI)

print("\ntest_2_legacy_behaviour_is_not_broken")
check("orchestrator/generate.py still generates images itself",
      "self.generate_images(" in src(os.path.join("orchestrator", "generate.py")))
check("orchestrator/publish.py still places them itself",
      "self._insert_images_balanced(" in src(os.path.join("orchestrator", "publish.py")))
check("the placement implementation is REUSED, not reimplemented",
      "from orchestrator.images import ImagesMixin" in GI
      and "_insert_images_balanced(" in GI)
check("no second placement algorithm was written",
      GI.count("def _insert_images_balanced") == 0,
      "it is imported; defining one here would be the duplicate")
check("house style and provider routing are untouched",
      'DEFAULT_MODEL = "recraft/recraft-v4.1"' in GI)
gi_tree = ast.parse(GI)
gen_calls = sum(1 for n in ast.walk(gi_tree)
                if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "process_post")
check("illustrate_post generates through process_post, unchanged", gen_calls >= 1)

print("\ntest_3_no_duplicate_image_generation")
check("an already-illustrated post is skipped before any generation",
      PB.index("gen_images.has_image_field(dest.read_text())")
      < PB.index("gen_images.illustrate_post(dest)"),
      "the guard must be checked first, or legacy articles regenerate")
check("the skip path says so rather than silently doing nothing",
      "already illustrated upstream" in PB)
check("gen_images itself skips an existing asset file",
      "if dest.exists() and not force:" in GI)
check("illustrate_post leaves an already-figured body alone",
      'if "article-figure" in body:' in GI)
check("...and reports the figures it found rather than re-placing them",
      'figures = body.count("article-figure")' in GI)

print("\ntest_an_unillustrated_publication_is_never_silent")
check("a failure is printed on the run's output", 'print("  images: FAILED' in PB)
check("...and on stderr", "PUBLISHING WITHOUT ILLUSTRATIONS" in PB and "file=sys.stderr" in PB)
check("...and recorded in the commit message",
      'msg_parts.append("published without illustrations' in PB)
check("the flag is declared before the block that sets it",
      PB.index("image_failure = None") < PB.index('image_failure = res["reason"]'),
      "an init after the assignment would reset it and lose the failure")
check("an image failure does not raise out of illustrate_post",
      'return {"ok": False' in GI,
      "the caller decides what a missing illustration means")
check("a missing key is reported, not crashed on",
      "OPENROUTER_API_KEY is not set" in GI)

print("\n" + "-" * 60)
if FAILURES:
    print("STORY ARCHITECTURE IMAGES: %d of %d CHECKS FAILED" % (len(FAILURES), CHECKS[0]))
    for f in FAILURES:
        print("  - %s" % f)
    sys.exit(1)
print("ALL %d STORY ARCHITECTURE IMAGE TESTS PASSED" % CHECKS[0])
