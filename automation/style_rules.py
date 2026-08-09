"""
style_rules.py — single source of truth for the Crip Minds writing-style rules.

Built 2026-08-09, migration Stage 2 (see .claude/bregman-anchor-corpus.md Section 5
and this repo's git log around this date for the incident and design discussion that
prompted it). Before this file existed, the same ~15 rules were hand-copied as raw
prompt text into at least 12 separate locations across automation/production_orchestrator.py
and two now-deleted legacy scripts (opus_rewrite.py, root production_orchestrator.py).
Confirmed drift found by direct comparison: a jargon wordlist that differed (5 vs 7 vs 8
terms across 3 copies, one term appearing in exactly one of them), a metaphor-for-mechanism
ban with no exception for quoted speech in any of 3 copies, a list-length cap contradicted
by real source material in all 4 copies, and a code comment that mislabeled which rule
number a shared deterministic check belonged to because two copies used different R-number
schemes for the same rule.

DESIGN:
Each Rule carries THREE text renderings because the same rule genuinely needs three
different voices, and trying to make one text serve all three is what caused the drift
in the first place:
  - imperative: second-person, for the writer's own generation prompt ("Never do X").
  - full:       third-person with worked examples and exceptions, for judge prompts
                (the pre-commit gate, the post-publish review) that need to explain a
                violation, not just avoid one.
  - terse:      one clause, for compact checklists and log lines.

`exemptions` is a single shared list — the carve-out that took three hand-edits to add
correctly (metaphor exempt inside a real attributed quote) is now one list entry that
every renderer includes automatically.

Rule numbering (R1, R2, ...) is NEVER stored here or anywhere else. It is assigned at
render time by render_gate()/render_review(), based on a stable sort over whichever
rules carry that stage's tag. Downstream code keys on rule.id (a stable slug), never on
a number — this is what makes the R14-means-something-different-in-two-functions class
of bug structurally impossible going forward.

USAGE:
    from style_rules import RULES, render_gate, render_review, render_writer_bullet

    gate_text, gate_map = render_gate()      # -> (prompt string, {"R7": "long-list", ...})
    verdict_rule_id = gate_map[verdict_rule_number]   # translate a parsed "R7" back to an id

    # Inside the writer's generation prompt, replace a hand-typed bullet with:
    prompt_piece = render_writer_bullet("crafted-rhetoric")
"""
from dataclasses import dataclass, field
from enum import Enum, auto


class Stage(Enum):
    GENERATE = auto()   # writer's own prompt — instruction only, no check
    REWRITE = auto()    # rewrite_with_opus's whole-document rewrite pass
    GATE = auto()       # _pre_commit_gate — BLOCKING, runs before the file is written
    REVIEW = auto()     # validate_article — ADVISORY, runs async after publish


class Severity(Enum):
    GENERATIVE = auto()  # instruction only, never checked
    ADVISORY = auto()    # checked, does not block on its own
    BLOCKING = auto()    # checked, can block promotion


@dataclass
class Example:
    bad: str
    good: str = ""


@dataclass
class Rule:
    id: str                       # stable slug — THE identity, never a number
    name: str                     # short caps name, e.g. "CRAFTED RHETORIC"
    terse: str                    # one clause, for compact checklists
    imperative: str               # second-person, for the writer prompt
    full: str                     # third-person, with exceptions, for judge prompts
    stages: set                   # subset of {Stage.GENERATE, .REWRITE, .GATE, .REVIEW}
    severity: Severity
    exemptions: list = field(default_factory=list)
    examples: list = field(default_factory=list)
    rationale: str = ""
    added: str = ""
    last_verified: str = ""


def _exemptions_text(rule):
    if not rule.exemptions:
        return ""
    return " EXEMPT: " + " Also exempt: ".join(rule.exemptions)


# ─────────────────────────────────────────────────────────────────────────────
# THE REGISTRY
#
# Scope: this covers the rules CONFIRMED to be duplicated with drift across
# multiple locations (per the 2026-08-09 audit). It deliberately does NOT
# attempt to migrate every rule in every prompt — most of the writer's
# generation prompt (persona voice, GROUNDING, NAMED VOICES, structural
# guidance like MICROSCOPE AND TELESCOPE) is unique prose that was never
# duplicated elsewhere, and moving it here would add indirection with no
# corresponding drift risk to fix. Add a rule here only when it needs to
# render identically in 2+ places.
# ─────────────────────────────────────────────────────────────────────────────

RULES = [
    Rule(
        id="jargon",
        name="JARGON",
        terse="institutional vocabulary banned: claimants, non-compliant, stakeholders, "
              "outcomes, intervention, change of circumstances, platform upgrades, "
              "priority locations",
        imperative=(
            "JARGON — BANNED: Strip institutional vocabulary. 'Claimants' → 'tenants' or "
            "'residents'. 'Non-compliant' → say what the barrier is. 'Change of "
            "circumstances' → 'situation had changed'. 'Platform upgrades' → 'rebuild the "
            "platform'. 'Stakeholders' → who they are. 'Outcomes' → what people got or did "
            "not get. 'Intervention' → what actually happened. 'Priority locations' → name "
            "the actual place. If the word appears in a government report, a council "
            "briefing, or an accessibility audit — replace it with what a person would say "
            "to another person."
        ),
        full=(
            "JARGON — flag any institutional vocabulary: claimants, non-compliant, "
            "stakeholders, outcomes, intervention, change of circumstances, platform "
            "upgrades, priority locations. These words belong in audit reports, not essays."
        ),
        stages={Stage.GENERATE, Stage.REWRITE, Stage.GATE, Stage.REVIEW},
        severity=Severity.BLOCKING,
        rationale="Union of 3 previously-drifted wordlists (5/7/8 terms); 'priority "
                  "locations' existed in exactly one of them before this fix.",
        added="2026-08-04", last_verified="2026-08-09",
    ),
    Rule(
        id="nominalization",
        name="NOMINALIZATION",
        terse="a verb rewritten as a noun so the actor disappears",
        imperative=(
            "NOMINALIZATION — BANNED: Actions stay as verbs. When a verb becomes a noun, "
            "the person doing it disappears. 'The redesign of the system' → 'they "
            "redesigned the system.' 'The implementation' → 'they built it.' 'The "
            "assessment of needs' → 'someone asked what you needed.' Scan for nouns ending "
            "in -tion, -ment, -ance, -ence, -al, -ure — these are often verbs in disguise. "
            "Free the verb. Name who does it."
        ),
        full=(
            "NOMINALIZATION — an actual verb rewritten as a noun so the actor disappears "
            "('the redesign of the interface' should be 'they redesigned the interface')."
        ),
        exemptions=[
            "an ordinary noun that merely ends in -tion/-ment/-ance/-ence but was never a "
            "verb in this sentence — 'access', 'government', 'moment', 'experience', "
            "'evidence', 'silence', 'distance', 'argument', 'environment' are just nouns, "
            "not violations. Test: could you name who did the verb? If there's no hidden "
            "actor to free, it isn't a nominalization."
        ],
        stages={Stage.GENERATE, Stage.REWRITE, Stage.GATE, Stage.REVIEW},
        severity=Severity.BLOCKING,
        added="2026-08-01", last_verified="2026-08-09",
    ),
    Rule(
        id="system-voice",
        name="SYSTEM VOICE",
        terse="passive/bureaucratic syntax that erases who did the thing",
        imperative=(
            "SYSTEM VOICE — BANNED: Never write in the syntax of the systems you are "
            "critiquing. Test every sentence: who is doing what to whom? If you cannot "
            "point to a human subject doing a concrete thing, rewrite. Passive voice "
            "erases the person causing harm. Stacked bureaucratic nouns erase the person "
            "experiencing it. 'The intervention was implemented' → 'The council installed "
            "a ramp.' 'Access needs were assessed' → 'A caseworker asked what you needed.' "
            "'Equipment requests were processed' → 'Someone reviewed your application for "
            "a grab rail.' If the sentence could appear in the audit report the article is "
            "criticising, it has failed."
        ),
        full=(
            "SYSTEM VOICE — passive construction that erases the actor. 'Stops were "
            "flagged as non-compliant' has no person. Flag it."
        ),
        stages={Stage.GENERATE, Stage.REWRITE, Stage.GATE, Stage.REVIEW},
        severity=Severity.BLOCKING,
        rationale="Was present in the writer prompt and the post-publish review but "
                  "ABSENT from the blocking pre-commit gate — a violation could ship live "
                  "with nothing stopping it. Moved to BLOCKING here.",
        added="2026-08-09", last_verified="2026-08-09",
    ),
    Rule(
        id="vague-we",
        name="VAGUE WE",
        terse="'we' with no named referent",
        imperative=(
            "VAGUE WE — BANNED: 'We' must always have a named referent. If 'we' means "
            "everyone, it usually means a specific group that benefits from not being "
            "named. Name them. 'We designed this system' → 'non-disabled designers built "
            "this system.' 'We don't talk about this' → 'the council never published "
            "this.' If you cannot say who we is, cut the word and make someone specific "
            "do the thing."
        ),
        full="VAGUE WE — every 'we' must name a clear referent. Flag 'we' that means everyone.",
        stages={Stage.GENERATE, Stage.REWRITE, Stage.GATE, Stage.REVIEW},
        severity=Severity.BLOCKING,
        added="2026-08-01", last_verified="2026-08-09",
    ),
    Rule(
        id="front-loaded-sentence",
        name="FRONT-LOADED SENTENCE",
        terse="long subordinate clause before the subject",
        imperative=(
            "FRONT-LOADED SENTENCES — BANNED: Subject comes first. Verb comes second. "
            "Never open with a long subordinate clause that makes the reader hold the "
            "setup in memory before the sentence resolves. 'What happens after the "
            "deadline has none of those qualities' → 'Once the deadline passes, none of "
            "that applies.' If the sentence does not name its subject in the first five "
            "words, rewrite it."
        ),
        full=(
            "FRONT-LOADED SENTENCE — long subordinate clause before the subject. Flag "
            "sentences opening with 'When considering...', 'What happens after...', "
            "'Given that...'."
        ),
        stages={Stage.GENERATE, Stage.REWRITE, Stage.GATE, Stage.REVIEW},
        severity=Severity.BLOCKING,
        added="2026-08-01", last_verified="2026-08-09",
    ),
    Rule(
        id="subject-verb-distance",
        name="SUBJECT-VERB DISTANCE",
        terse="a long appositive/relative clause buries the main verb far from its subject",
        imperative=(
            "Naming the subject early is not enough on its own: if a long appositive or "
            "relative clause — 'X as a/an Y that/which/who Z' — sits between that subject "
            "and its main verb, the reader still has to hold the subject in memory across "
            "the detour. 'The eye as an organ that some of us route the whole world "
            "through gets a footnote' names 'the eye' in word 2 but delays 'gets' by 12 "
            "words — split it: 'Some of us route the whole world through our eyes. That "
            "gets a footnote.' Keep subject and verb close together, always."
        ),
        full=(
            "SUBJECT-VERB DISTANCE — the subject is named early (so the front-loaded-"
            "sentence rule alone would pass it) but a long appositive or relative clause — "
            "'as a/an X that/which/who...', or a comma- or em-dash-set-off descriptor — "
            "sits between the subject and its main verb, forcing the reader to hold the "
            "subject in memory across the detour."
        ),
        exemptions=[
            "a short appositive (3-4 words) that barely delays the verb",
            "a relative clause that IS the sentence's last constituent with nothing "
            "waiting behind it",
        ],
        stages={Stage.GATE, Stage.REVIEW},
        severity=Severity.BLOCKING,
        added="2026-08-01", last_verified="2026-08-09",
    ),
    Rule(
        id="named-references",
        name="NAMED REFERENCES",
        terse="name + what they said/did + why it matters, all in one sentence",
        imperative=(
            "NAMED REFERENCES: Name + one sentence of context + move on. Never leave a "
            "name floating. Never spend a paragraph setting up who someone is before "
            "using their idea. If the reference needs more than one sentence to land, "
            "either the idea is not earning its place or the writing is carrying it wrong. "
            "The idea should do the work, not the biography."
        ),
        full=(
            "NAMED REFERENCES — name + what they said/did + why it matters here, all in "
            "one sentence. Flag floating names with only a year, or paragraph-long "
            "introductions of a person."
        ),
        stages={Stage.GENERATE, Stage.REWRITE, Stage.REVIEW},
        severity=Severity.ADVISORY,
        rationale="Kept ADVISORY, not promoted to BLOCKING: the only available fix "
                  "(adding context) requires material the surgical fixer isn't allowed to "
                  "invent. A blocking check with no permitted remedy just discards fixes.",
        added="2026-08-01", last_verified="2026-08-09",
    ),
    Rule(
        id="decoding-required",
        name="DECODING REQUIRED",
        terse="a sentence the reader must stop and re-read to parse at all",
        imperative=(
            "NO DECODING REQUIRED. If a sentence needs the reader to stop and work out "
            "what it means, rewrite it. Three patterns to cut: (1) buried qualifiers — "
            "'the thought being that X' → state X directly; (2) metaphors that need "
            "unpacking before they mean anything — break them into what they actually "
            "say; (3) abstract compression — 'something they have no box for' → "
            "'something they cannot name'. Test: read the sentence aloud. If you pause to "
            "process it, the reader will too."
        ),
        full=(
            "DECODING REQUIRED — flag sentences the reader must stop and re-read to parse "
            "at all: buried qualifiers ('the thought being that...'), genuinely opaque "
            "abstract compression ('something they have no box for' with no other "
            "context)."
        ),
        exemptions=[
            "a metaphor just because it is figurative — a metaphor that lands in one read "
            "and states the piece's own argument is doing its job, not failing this rule. "
            "The test is whether a reader stalls, not whether the sentence uses "
            "figurative language.",
        ],
        stages={Stage.REVIEW},
        severity=Severity.ADVISORY,
        added="2026-08-01", last_verified="2026-08-09",
    ),
    Rule(
        id="crafted-rhetoric",
        name="CRAFTED RHETORIC",
        terse="metaphor-for-mechanism, mirrored/cleft sentences, aphoristic closers, "
              "sustained wordplay, framework/object-as-agent",
        imperative=(
            "CRAFTED RHETORIC — BANNED. Checked directly against real Bregman prose: he "
            "essentially never reaches for these six moves, even when everything else "
            "about a sentence is plain. (1) METAPHOR FOR MECHANISM — a figurative image "
            "standing in for a plain fact ('it grabs the eye before the brain gets a "
            "vote') — state the mechanism directly: what does it actually do. (2) "
            "MIRRORED/CLEFT SENTENCE — a symmetrical construction built for cleverness "
            "rather than genuine correction: 'X is what... Y is what...', 'one wants X, "
            "the other wants Y', or the same grammatical frame reused identically for two "
            "different subjects in a row. Do NOT flag a genuine 'not X, but Y' correction "
            "that replaces a real misconception with the actual explanation once — that "
            "is the REDEFINE technique, protected elsewhere, and real Bregman prose uses "
            "it plainly ('the problem is not X, it is Y'). Only flag when the mirrored "
            "template repeats within one piece, or when both halves are built for "
            "symmetry rather than to state a correction. (3) APHORISTIC OR IRONIC CLOSER "
            "— ending a paragraph on a crafted twist or epigram. End on a plain fact, a "
            "real quote, or a concrete narrative beat instead. (4) SUSTAINED WORDPLAY — "
            "reusing one word for cleverness across consecutive sentences. Use a "
            "different, plainer word the second time. (5) NAMED ABSTRACT FRAMEWORK AS "
            "AGENT — treating a coined category or discipline as if it acts ('persuasion "
            "design wants...'). Name the concrete object instead — the banner, the "
            "leaflet, the shop, the person. (6) INANIMATE OBJECT AS DELIBERATE AGENT — "
            "giving a building, a drawing, a render, a document, or a physical material/"
            "surface (a fold, a fabric, the ground, a pleat) deliberate intent, memory, or "
            "care it cannot have ('a building has decided that its meaning is...', 'the "
            "drawings were dismantling my argument', 'the fold does not remember the "
            "hand', 'a promise the ground makes'). Buildings don't decide anything, "
            "drawings don't dismantle anything, and folds don't remember or promise "
            "anything — say who did: the architect decided, I concluded from the "
            "drawings, the person who folded it. If a draft sentence resolves through "
            "symmetry, a twist, a pun, or handing intent to a thing, rewrite it flat."
        ),
        full=(
            "CRAFTED RHETORIC — flag any of these literary devices, even when the "
            "sentence is otherwise grammatical and plain-worded (real Bregman prose, "
            "checked directly against his published work, essentially never does any of "
            "these): (a) METAPHOR FOR MECHANISM — a figurative image standing in for a "
            "plain mechanical fact ('it grabs the eye before the brain gets a vote', "
            "'the same banner turns into a magnet for the eye') — state the mechanism "
            "directly instead. (b) MIRRORED/CLEFT SENTENCE — a symmetrical construction "
            "built for cleverness rather than genuine correction. Do NOT flag a genuine "
            "'not X, but Y' correction (the REDEFINE technique, protected elsewhere) — "
            "only flag when the mirrored template repeats within one piece, or both "
            "halves are built for symmetry rather than to state a correction. (c) "
            "APHORISTIC OR IRONIC CLOSER — a paragraph or piece ending on a crafted twist "
            "or epigram rather than a plain fact, a quote, or a concrete narrative beat. "
            "(d) SUSTAINED WORDPLAY — punning or reusing one word for cleverness across "
            "consecutive sentences. (e) NAMED ABSTRACT FRAMEWORK AS AGENT — treating a "
            "coined category or discipline as if it acts, instead of naming the concrete "
            "object. (f) INANIMATE OBJECT AS DELIBERATE AGENT — giving a building, a "
            "drawing, a render, a document, or a physical material or surface deliberate "
            "intent, memory, or care it cannot have — say who actually did it."
        ),
        exemptions=[
            "a metaphor inside a real, attributed quote from a named source (real "
            "Bregman example: a biblical image inside a real person's own letter — "
            "'not one camel, but a whole herd of elephants went through the eye of the "
            "needle', quoted, not the narrator's own line). Authentic reported speech is "
            "not the same violation as the narrator reaching for an invented image in "
            "their own voice; only flag figurative language when it is the writer's own, "
            "unattributed description of a mechanism",
            "a plain, unadorned comparison stated once and dropped ('the room reads it "
            "like a spreadsheet') — only flag when the device is doing rhetorical work "
            "(symmetry, a twist, a pun, or false agency) rather than just naming a thing",
        ],
        stages={Stage.GENERATE, Stage.GATE, Stage.REVIEW},
        severity=Severity.BLOCKING,
        rationale="Live incident 2026-08-09: 'A ramp is a promise the ground makes' "
                  "shipped as a published article's opening sentence. The rule had "
                  "already fired correctly at the gate but was overridden by an "
                  "unrelated >=3-violations threshold (see opening-paragraph escalation, "
                  "fixed separately). Quote exemption added the same day after comparing "
                  "against real Bregman source text. Absent entirely from "
                  "rewrite_with_opus's 41-rule list before this fix — the only register "
                  "instruction a non-Opus draft ever received had no crafted-rhetoric ban "
                  "at all.",
        added="2026-08-04", last_verified="2026-08-09",
    ),
    Rule(
        id="long-list",
        name="LONG LIST",
        terse="4+ items in a list, unless it earns its length with a payoff right after",
        imperative=(
            "LISTS RUN TO THREE — with one earned exception. Four items in a list is one "
            "too many, UNLESS the list is deliberately piling up toward a single payoff "
            "or ironic reversal that lands in the sentence right after it (real Bregman "
            "example: nine named items — figures, movements, inventions — in one "
            "sentence, followed immediately by 'and income was still the same' for full "
            "weight). No payoff after it, no exception: cut to three."
        ),
        full=(
            "LONG LIST — 4 or more items in a list, UNLESS the list is deliberately "
            "piling up toward a single payoff/reversal in the sentence right after it "
            "(real Bregman example: nine named items in one sentence, immediately "
            "followed by an ironic 'and nothing had changed' punchline). A long list with "
            "no such payoff after it is still a violation."
        ),
        stages={Stage.GENERATE, Stage.REWRITE, Stage.GATE, Stage.REVIEW},
        severity=Severity.BLOCKING,
        rationale="Flat '4+ is always a violation' cap contradicted by real Bregman "
                  "practice (a real 9-item list building to a payoff). Confirmed the "
                  "opposite failure mode doesn't occur: the same book elsewhere keeps a "
                  "4-item list to exactly 4 with no payoff needed, i.e. short lists with "
                  "no reversal are also real and fine — only the flat cap was wrong.",
        added="2026-08-04", last_verified="2026-08-09",
    ),
    Rule(
        id="paragraph-length",
        name="PARAGRAPH LENGTH",
        terse="more than 5 sentences in one paragraph",
        imperative=(
            "PARAGRAPH LENGTH: Keep paragraphs short. Two to four sentences is the "
            "target. A one-sentence paragraph lands like a verdict — use it deliberately. "
            "If a paragraph exceeds five sentences, it is trying to do two things; break "
            "it."
        ),
        full="LONG PARAGRAPH — flag any paragraph exceeding 5 sentences.",
        stages={Stage.GENERATE, Stage.REWRITE, Stage.GATE, Stage.REVIEW},
        severity=Severity.BLOCKING,
        rationale="Countable — this can be a deterministic sentence-split check rather "
                  "than an LLM judgement; kept as an LLM rule here pending that "
                  "migration (tracked separately).",
        added="2026-08-01", last_verified="2026-08-09",
    ),
    Rule(
        id="section-breaks",
        name="SECTION BREAKS",
        terse="more than 3 '---' breaks in the body",
        imperative=(
            "SECTION BREAKS: Two --- breaks per article is the target. Three is the "
            "ceiling. Never more. Each break resets the reader with no handhold. Only use "
            "a break for a genuine scene change or time jump. Transitions between ideas "
            "happen inside the prose — a short sentence, a pivot word, a contrast. Not a "
            "line break."
        ),
        full="SECTION BREAKS — flag if more than 3 '---' breaks appear in the body.",
        stages={Stage.GENERATE, Stage.REWRITE, Stage.GATE, Stage.REVIEW},
        severity=Severity.BLOCKING,
        added="2026-08-01", last_verified="2026-08-09",
    ),
    Rule(
        id="meta-language-commentary",
        name="META-LANGUAGE COMMENTARY",
        terse="describing HOW something was worded as its own observation, instead of just saying it",
        imperative=(
            "NO META-LANGUAGE COMMENTARY: Do not analyze or comment on word choice or "
            "phrasing as its own observation, from outside the language rather than "
            "inside it. 'The word rolling appeared twice, both times as praise' is "
            "commentary ABOUT a word instead of just using the word. 'It sounds "
            "technical, but it does something simple' is commentary about how a fact "
            "will land instead of just stating the fact. State the actual thing "
            "plainly. If a specific word or phrase matters, use it directly in your "
            "own sentence rather than pointing at it and describing its usage from a "
            "distance."
        ),
        full=(
            "META-LANGUAGE COMMENTARY — the sentence describes or analyzes how "
            "something was phrased/worded (word frequency, word choice, tone-of-"
            "delivery) as its own observation, rather than the writer simply stating "
            "the underlying fact in their own words. Reads as clinical and "
            "distancing rather than direct."
        ),
        stages={Stage.GENERATE, Stage.REVIEW},
        severity=Severity.ADVISORY,
        rationale="Reader feedback 2026-08-09, live article: 'The word rolling "
                  "appeared twice, both times as praise' (analyzing a source's word "
                  "choice instead of just using the words) and, from the same "
                  "editing pass earlier the same day, 'It sounds technical, but it "
                  "does something simple' (commentary on how a fact would land "
                  "instead of just stating it). Not yet a rule verified against real "
                  "Bregman source text the way the other rules were — kept ADVISORY "
                  "pending that check, not promoted to BLOCKING on the strength of "
                  "two same-day examples alone.",
        added="2026-08-09", last_verified="2026-08-09",
    ),
    Rule(
        id="stacked-temporal-clauses",
        name="STACKED TEMPORAL CLAUSES",
        terse="'after I'd done X and before I'd done Y' nested clauses used just to gesture at timing",
        imperative=(
            "NO STACKED TEMPORAL CLAUSES: Do not anchor a scene in time by stacking "
            "two subordinate clauses ('after I'd checked my tire pressure and before "
            "I'd finished the plantains'). This nests grammar just to gesture at "
            "'morning, mid-routine' and forces the reader to hold two clauses in "
            "memory before the main clause resolves. If two concrete details both "
            "matter, state them as a flat parallel list instead ('tire pressure "
            "checked by hand, plantains half eaten') or just keep the one detail "
            "that carries the most weight and cut the other."
        ),
        full=(
            "STACKED TEMPORAL CLAUSES — a scene-setting sentence uses two nested "
            "subordinate clauses (typically 'after X and before Y') purely to "
            "indicate rough timing, rather than a flat list or a single clean "
            "clause. Hard to parse in one read even when each clause alone is "
            "simple."
        ),
        stages={Stage.GENERATE, Stage.REVIEW},
        severity=Severity.ADVISORY,
        rationale="Reader feedback 2026-08-09, live article: 'I read that on a "
                  "Tuesday morning in Flatbush, after I'd checked my tire pressure "
                  "by hand and before I'd finished the plantains' — 'I cant read "
                  "that normally'. Fixed to a flat parallel construction ('tire "
                  "pressure checked by hand, plantains half eaten'). Kept ADVISORY, "
                  "same reasoning as meta-language-commentary above — real feedback, "
                  "not yet cross-checked against a Bregman source corpus.",
        added="2026-08-09", last_verified="2026-08-09",
    ),
    Rule(
        id="ending-shape",
        name="ENDING",
        terse="no house ending shape; only CTAs/summaries/title-echoes/couplets are violations",
        imperative=(
            "ENDING — NO FIXED SHAPE: There is no house ending. Do not default to "
            "trailing off, and do not default to a single unresolved sentence. Pick the "
            "ending this particular piece has earned, from any of these: (a) HARD "
            "RESOLUTION — you commit, plainly, to what you now think; the landing is "
            "warm and confident and you say the thing. (b) A LIVE QUESTION — a position "
            "the reader can argue with, the door left open. (c) A QUOTE — give the last "
            "words to someone else and do not top them. (d) A FACT — end on the concrete "
            "detail, dated and placed, with no commentary attached. (e) THE CODA — fold "
            "back to the opening scene, later or elsewhere or in a different register, "
            "without stating what changed. Still banned in every variant: a call to "
            "action, a summary of what you just argued, a thesis restatement or title "
            "echo, and any sentence beginning 'We need' / 'This requires' / 'Join'."
        ),
        full=(
            "ENDING — there is no house ending shape. Five are all valid and none is "
            "preferred: (a) a hard resolution the writer commits to — a warm, confident "
            "landing is legitimate and must NOT be flagged for resolving; (b) a live "
            "question or arguable position; (c) the last words given to a quoted source; "
            "(d) a plain concrete fact, dated or placed, with no commentary; (e) a coda "
            "folding back to the opening scene. Flag ONLY: a call to action, a summary of "
            "the argument just made, a thesis restatement or title echo, any sentence "
            "beginning 'We need' / 'This requires' / 'Join' / 'I am developing', or a "
            "resolving image-couplet (two mirrored sentences of equal length that land a "
            "feeling, e.g. 'The campfire is warm. The path is cold.') — the couplet is a "
            "rhythm tic, not an ending shape, and is the only resolved close that is "
            "still a violation. Do not flag an ending merely because it resolves, "
            "concludes, or lands with confidence."
        ),
        stages={Stage.GENERATE, Stage.REWRITE, Stage.REVIEW},
        severity=Severity.ADVISORY,
        rationale="Absent from the blocking gate entirely before this fix — checked only "
                  "in the writer prompt and the async post-publish review. Two now-"
                  "deleted legacy scripts (opus_rewrite.py, root production_orchestrator."
                  "py) mandated the OPPOSITE doctrine (a single fixed one-sentence-image "
                  "ending, banning the 'warm resolution' shape this rule protects) — "
                  "confirmed dead (not invoked by any cron) before deletion, so no live "
                  "damage occurred, but it's why this rule's real-world consistency "
                  "matters. The deterministic core of this rule (CTA openers, title-echo "
                  "detection) is a candidate for promotion to BLOCKING as a regex check; "
                  "the judged remainder (couplet detection, 'did this piece earn its "
                  "ending') stays advisory.",
        added="2026-08-01", last_verified="2026-08-09",
    ),
]

RULES_BY_ID = {r.id: r for r in RULES}


def _for_stage(stage):
    return [r for r in RULES if stage in r.stages]


def render_writer_bullet(rule_id):
    """Return the imperative-voice text for one rule, for splicing into the writer's
    generation prompt at the specific point a hand-typed bullet used to sit."""
    rule = RULES_BY_ID[rule_id]
    return rule.imperative + _exemptions_text(rule) if not rule.exemptions or _already_in_imperative(rule) else rule.imperative


def _already_in_imperative(rule):
    # Most imperative texts already weave exemptions in as prose (see crafted-rhetoric's
    # inline "EXEMPT:" clause above) rather than appending them mechanically — this
    # avoids a robotic "EXEMPT: ..." tacked onto hand-crafted second-person text.
    return True


def render_rewrite():
    """Render the numbered-list rendering used by rewrite_with_opus's whole-document
    rewrite pass. Returns (prompt_text, id_by_number)."""
    rules = _for_stage(Stage.REWRITE)
    lines = []
    id_by_number = {}
    for i, rule in enumerate(rules, start=1):
        id_by_number[str(i)] = rule.id
        lines.append(f"{i}. {rule.name}. {rule.imperative}")
    return "\n".join(lines), id_by_number


def render_gate():
    """Render the R1..Rn checklist used by _pre_commit_gate's GATE_SYSTEM. Numbering is
    assigned here, at render time, from a stable sort — never hand-typed, never stored.
    Returns (prompt_text, id_by_rnumber) so callers can translate a parsed 'R7' back to
    a stable rule id."""
    rules = sorted(_for_stage(Stage.GATE), key=lambda r: r.id)
    lines = []
    id_by_rnumber = {}
    for i, rule in enumerate(rules, start=1):
        rn = f"R{i}"
        id_by_rnumber[rn] = rule.id
        exempt = _exemptions_text(rule)
        lines.append(f"{rn}  {rule.full}{exempt}")
    return "\n".join(lines), id_by_rnumber


def render_review():
    """Render the R1..Rn checklist used by validate_article's RULES_SYSTEM. Separate
    numbering pass from render_gate() by design (different rule subset can apply to
    each stage) but uses the SAME id_by_rnumber pattern, so a caller comparing gate vs.
    review verdicts compares by rule.id, never by a possibly-different R-number."""
    rules = sorted(_for_stage(Stage.REVIEW), key=lambda r: r.id)
    lines = []
    id_by_rnumber = {}
    for i, rule in enumerate(rules, start=1):
        rn = f"R{i}"
        id_by_rnumber[rn] = rule.id
        exempt = _exemptions_text(rule)
        lines.append(f"{rn}  {rule.full}{exempt}")
    return "\n".join(lines), id_by_rnumber


def render_docs():
    """Render a markdown table for public-facing docs (press/system-report). One-way
    export only — never round-tripped back into this file."""
    lines = ["| Rule | Stages | Severity | Summary |", "|---|---|---|---|"]
    for r in RULES:
        stages = ", ".join(sorted(s.name for s in r.stages))
        lines.append(f"| {r.name} | {stages} | {r.severity.name} | {r.terse} |")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--export" and len(sys.argv) > 2 and sys.argv[2] == "md":
        print(render_docs())
    else:
        gate_text, gate_map = render_gate()
        print("=== GATE ===")
        print(gate_text)
        print()
        print("=== GATE rule-number map ===")
        print(gate_map)
