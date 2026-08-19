#!/usr/bin/env python3
"""WG-6B LOCAL POST-PATCH CLOSURE CHECK. For every patched sentence, asks whether
an unsupported commitment of the SAME semantic class survives in the sentence AS
IT NOW READS. Deliberately does NOT show the pre-patch wording: the question is
about the resulting semantic commitment, not about whether old strings vanished.
BLIND to the gold ledger."""
import hashlib, json
from pathlib import Path

W = Path(__file__).resolve().parent            # closure/
B = W.parent                                    # WG-6B
I = B.parent / "WG-6A" / "inputs"
ART = {"form1-3": "form1-3-article.md", "r2": "form-1.3-r2-article.md", "r3": "form-1.3-r3-article.md"}

SYSTEM = """You are the closure-verification stage of a source-fidelity audit for a disability-led publication. A repair has just edited an article to remove content the SOURCE TEXT does not support. Your job is to decide whether each repair actually CLOSED the unsupported commitment it was meant to clear.

THE ONLY QUESTION IS SOURCE FIDELITY — never world truth. A statement can be true in reality and still UNSUPPORTED, because the supplied SOURCE TEXT does not establish it. Never use outside knowledge.

WHAT CLOSURE MEANS

You are given a sentence AS IT NOW READS after the repair, and the TARGET COMMITMENT the repair was supposed to eliminate.

Do NOT check whether particular words disappeared. You are not string-matching. Read the sentence as a reader would and decide what it now COMMITS TO.

The commitment is NOT closed if the sentence still asserts it in ANY form:
  * a shorter form of the same claim
  * a weaker synonym or paraphrase
  * an adjacent phrase that carries it independently
  * a grammatical remnant that still implies it
  * a presupposition the sentence now depends on

The commitment IS closed if, reading the sentence on its own, a reader is no longer told the target
factual content — even if the sentence still discusses the same subject in a way the source licenses.

RESIDUAL CLASSES — check each explicitly against the sentence as it now reads:
  HUMAN_STATE       does it still assert what a person knew, felt, intended, expected or brought?
  TEMPORAL          does it still assert a time, date, duration or interval the source does not give?
  SOURCE_META       does it still assert what the source says, does, or does not do, unproven?
  QUANTIFIER_SCOPE  does it assert of ALL what the source restricts to SOME (or the reverse)?
  CONCRETE_DETAIL   does it still assert a specific place, name, number or fact not in the source?
  QUALIFIER_LOSS    has a source qualifier been dropped, making the claim stronger than the source?

ALSO CHECK FOR NEW DAMAGE
  NEW_UNSUPPORTED   does the sentence now assert something unsupported that a repair could have
                    introduced (an invented substitute fact, a wrong name, a changed number)?
  HEDGE_ADDED       has a hedge been added to rescue a claim ("perhaps", "it seems", "arguably",
                    "on this reading")? That is not a repair.
  GRAMMAR_BROKEN    is the sentence now ungrammatical or incoherent?

Interpretation remains legitimate. A sentence that analyses, evaluates, compares or draws meaning from
source-grounded material asserts no new factual state and is NOT a residual. Do not report analysis as
a residual just because it is confident or unhedged.

VERDICT per item:
  CLOSED        the target commitment is gone in every form, and no new unsupported content appeared
  UNDER_CLEARED the target commitment, or a residual/weaker form of it, still survives
  OVER_EDITED   the target is gone but the repair also removed or altered source-supported content,
                or introduced new unsupported content

OUTPUT
Reply with JSON only, no markdown fences, no commentary:
{"checks":[{"PATCH_ID":"...","TARGET_COMMITMENT":"...","SENTENCE_NOW":"...","WHAT_IT_NOW_COMMITS_TO":"...","RESIDUAL_CLASSES_FOUND":["..."],"NEW_UNSUPPORTED":"YES|NO","HEDGE_ADDED":"YES|NO","GRAMMAR_BROKEN":"YES|NO","VERDICT":"CLOSED|UNDER_CLEARED|OVER_EDITED","REASON":"..."}]}

RESIDUAL_CLASSES_FOUND is [] when nothing survives. Process every PATCH_ID you are given, exactly once, in order."""

src = (I / "source-snapshot.txt").read_text(encoding="utf-8")
report = {r["tag"]: r for r in json.loads((B / "APPLICATION-REPORT.json").read_text())}
findings = json.loads((B / "REPAIR-INPUTS.json").read_text())

def sentence_after(old_sentence, all_patches):
    """The parent sentence as it now reads. Applies EVERY patch whose OLD_TEXT falls
    inside this sentence — two findings can share one parent sentence, and applying
    only one of them would not reproduce the article's actual text."""
    s = old_sentence
    for q in all_patches:
        if q["old"] in s:
            s = s.replace(q["old"], "" if q["op"].upper() == "DELETE" else q["new"])
    return s

for tag, af in ART.items():
    patched = (B / f"{tag}-patched.md").read_text(encoding="utf-8")
    sent = {f["FINDING_ID"]: f for f in findings[tag]}
    items = []
    for a in report[tag]["applied"]:
        f = sent[a["FINDING_ID"]]
        now = sentence_after(f["PARENT_SENTENCE"], report[tag]["applied"])
        assert now.strip() in patched, f"reconstructed sentence not in patched article: {tag} {a['PATCH_ID']}"
        items.append({"PATCH_ID": a["PATCH_ID"],
                      "TARGET_COMMITMENT": a["TARGET_COMMITMENT"] or f["ATOMIC_UNSUPPORTED_COMMITMENT"],
                      "FAILURE_CLASS_REPAIRED": f["FAILURE_CLASS"],
                      "SENTENCE_NOW": now.strip()})
    user = (f"SOURCE TEXT (the only evidence — nothing outside it counts):\n---\n{src}\n---\n\n"
            f"{len(items)} REPAIRED SENTENCES. For each, decide whether the target commitment is\n"
            f"CLOSED in the sentence AS IT NOW READS. You are NOT shown the pre-repair wording, by\n"
            f"design: judge the resulting semantic commitment, not whether strings disappeared.\n"
            f"---\n" + "\n".join(json.dumps(i, ensure_ascii=False) for i in items) + "\n---\n")
    rendered = "=== SYSTEM ===\n" + SYSTEM + "\n\n=== USER ===\n" + user
    sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
    (W / f"{tag}-closure-system.txt").write_text(SYSTEM, encoding="utf-8")
    (W / f"{tag}-closure-user.txt").write_text(user, encoding="utf-8")
    (W / f"{tag}-closure-prompt.txt").write_text(rendered, encoding="utf-8")
    (W / f"{tag}-closure-meta.json").write_text(json.dumps({
        "stage": "WG-6B LOCAL POST-PATCH CLOSURE CHECK", "tag": tag, "items": len(items),
        "system_sha256": sha(SYSTEM), "user_sha256": sha(user), "prompt_sha256": sha(rendered),
        "patched_article_sha256": hashlib.sha256(patched.encode()).hexdigest(),
        "source_sha256": hashlib.sha256(src.encode()).hexdigest(),
        "shows_pre_patch_wording": False,
        "model_identity": "claude-opus-5[1m] via local Claude subscription, fresh-context subagent",
        "execution_mode": "LOCAL_CLAUDE_SUBSCRIPTION", "blind_to_gold": True,
        "phase": "PRESERVED_PRE_EXECUTION"}, indent=2))
    print(f"{tag}: {len(items)} closure items  prompt_sha={sha(rendered)[:16]}")
    for i in items:
        print(f'   {i["PATCH_ID"]} [{i["FAILURE_CLASS_REPAIRED"]}] -> {i["SENTENCE_NOW"][:95]}')
