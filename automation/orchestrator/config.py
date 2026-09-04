"""
config.py — pure data and constants for production_orchestrator.py.

Extracted 2026-08-09 (module-split, Stage 2 — see automation/README.md's top
notice and this repo's git log around this date). Zero behavior change: every
name here is a plain constant, a dict, or a small side-effect-free helper
function (`_nous_key`). None of it depends on `self` or the ProductionOrchestrator
class. Verified via `python3 automation/snapshot_test.py --check` before and
after this move.
"""
import os
from pathlib import Path

__all__ = [
    "CANONICAL_DISABILITY_LINKS", "_nous_key", "OPENROUTER_URL", "OPENROUTER_API_KEY",
    "PERSONA_CANON_DIR", "PERSONA_STATE_DIR", "_RELATIONSHIPS_FILE", "_AGENT_SLUG",
    "_REGISTERS", "_LENGTHS", "_ARTICLE_TYPES", "_INDEFENSIBLE_PROMPTS",
    "_SOCIAL_PROMPTS", "_AGENT_BEATS", "_THEME_CLUSTERS", "_PERSONA_CONFLICTS",
    "_STRUCTURAL_SHAPES",
]

# Canonical URLs for known disability figures/orgs — injected into articles automatically
CANONICAL_DISABILITY_LINKS = {
    'Sins Invalid':                       'https://sinsinvalid.org/',
    'Mia Mingus':                         'https://leavingevidence.wordpress.com/',
    'Liz Jackson':                        'https://www.disabledlist.org/',
    'Carmen Papalia':                     'https://carmenpapalia.com/',
    'Georgina Kleege':                    'https://english.berkeley.edu/users/45',
    'Leah Lakshmi Piepzna-Samarasinha':   'https://brownstargirl.org/',
    'Patty Berne':                        'https://sinsinvalid.org/',
    'Disability Visibility Project':      'https://disabilityvisibilityproject.com/',
    'Tangled Art':                        'https://tangledarts.org/',
    'Autistic Self Advocacy Network':     'https://autisticadvocacy.org/',
    'Disability Arts Online':             'https://disabilityarts.online/',
    'Alice Wong':                         'https://disabilityvisibilityproject.com/',
    'Harriet McBryde Johnson':            'https://disabilityvisibilityproject.com/',
    'Alison Kafer':                       'https://www.alisonkafer.com/',
    'Robert McRuer':                      'https://english.gwu.edu/robert-mcruer',
    'Christine Sun Kim':                  'https://christinesunkim.com/',
    'Haben Girma':                        'https://habengirma.com/',
    'Harilyn Rousso':                     'https://disabilityvisibilityproject.com/',
    'Simi Linton':                        'https://simi.nyc/',
    'Hansel Bauman':                      'https://www.hanselbauman.online/about',
    'Deaf Gain':                          'https://www.upress.umn.edu/9780816691227/deaf-gain/',
    'Mike Oliver':                        'https://disability-studies.leeds.ac.uk/library/author/oliver.m/',
    'Remploy':                            'https://www.remploy.co.uk/',
    'Yasuhisa Toyota':                    'https://www.nagata.co.jp/en/staff/toyota.html',
    # Cross-persona links — always point to research page, never fictional domains
    'Pixel Nova':                         '/research/?author=Pixel+Nova',
    'Siri Sage':                          '/research/?author=Siri+Sage',
    'Maya Flux':                          '/research/?author=Maya+Flux',
    'Zen Circuit':                        '/research/?author=Zen+Circuit',
}


# Load secrets from env file (no export statements — must parse manually)
_ENV_FILE = Path("/srv/secrets/openclaw.env")
if _ENV_FILE.exists():
    for _line in _ENV_FILE.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

# Also load reef bot creds for cripminds notifications, and Tumblr posting
# creds (found 2026-08-09: TUMBLR_* had real values in tumblr.env the whole
# time, but this file never loaded it -- post_to_tumblr's own
# `if not all([ck, cs, at, ats, blog]): return None` guard was silently
# no-op'ing every call at debug level, so Tumblr posting has likely never
# actually fired since tumblr.env was created. Confirmed via zero
# _social/*.json files ever having a tumblr_url field.
for _env_path in [Path("/srv/secrets/reef/reef-bot.env"), Path("/srv/secrets/tumblr.env")]:
    if _env_path.exists():
        for _line in _env_path.read_text().splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                os.environ.setdefault(_k.strip(), _v.strip())


def _nous_key():
    try:
        with open('/srv/data/hermes/auth.json') as _f:
            import json as _j
            return _j.load(_f)['providers']['nous']['agent_key']
    except Exception:
        return ''


# Editorial transport. Was the local CLIProxyAPI on :8317 until 2026-09-04, when a live
# probe showed the proxy's own Claude OAuth credential had expired and every "claude"
# model it still served was a plain OpenRouter passthrough under a translated name. The
# proxy was therefore a hop that could fail but could not add anything, so the pipeline
# now calls OpenRouter itself. Model names lose the `openrouter/` prefix that existed
# only for the proxy's benefit -- see llm._call_openai_compat_api, which normalises any
# survivor so no call site can quietly reintroduce a proxy-only name.
OPENROUTER_URL = 'https://openrouter.ai/api/v1'
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')

# This file lives one level below automation/ (automation/orchestrator/config.py),
# so _SCRIPT_DIR must go up two parents, not one, to land on automation/ itself —
# PERSONA_CANON_DIR/PERSONA_STATE_DIR/_RELATIONSHIPS_FILE all resolve relative to
# automation/, matching every other script in this directory (news_fetcher.py etc).
# Getting this wrong silently points persona canon/state at a nonexistent
# automation/orchestrator/persona_canon/ instead of the real automation/persona_canon/.
_SCRIPT_DIR   = Path(__file__).parent.parent
PERSONA_CANON_DIR = _SCRIPT_DIR / "persona_canon"
PERSONA_STATE_DIR = _SCRIPT_DIR / "persona_state"
PERSONA_STATE_DIR.mkdir(exist_ok=True)
_RELATIONSHIPS_FILE = _SCRIPT_DIR / "relationships.json"

_AGENT_SLUG = {
    "Pixel Nova": "pixel-nova",
    "Siri Sage":  "siri-sage",
    "Maya Flux":  "maya-flux",
    "Zen Circuit": "zen-circuit",
}



# Tonal register and length weights for article variety
_REGISTERS = [
    ("wry",          0.25, "Dry, observational. The joke is in the framing, never announced. You find the absurdity in how things are organised and let it sit. The reader laughs a beat late."),
    ("clinical",     0.20, "Cold precision. No emotion in the delivery — the facts are the argument. Present evidence the way a pathologist presents findings. Let the reader supply the outrage."),
    ("ecstatic",     0.20, "Something genuinely surprised you. You are writing from inside that surprise. The energy is in the discovery, not in exclamation. Precise wonder."),
    ("furious",      0.15, "Controlled anger. Precise. You do not shout — you dissect. Every sentence cuts. The reader feels the weight of what you are describing without you ever raising your voice."),
    ("melancholic",  0.15, "Slow, exact, not sentimental. Write about loss without performing grief. The sadness is in what is missing from the frame, not in what you say about it."),
    ("celebratory",  0.05, "Something was built right. Something survived. Something won. Not naive optimism — specific joy at a specific thing that actually happened, that actually works. The celebration is in the precision of what is being recognised."),
]
# Length pool. Weighted toward the long end (2026-08-04, extended 2026-08-04): a patient
# turn cannot be earned at 800 words. The 2800 bucket matches Bregman's own measured piece
# length (2,865 words, "The real Lord of the Flies") and fires roughly once every 10 days
# at daily cadence — close to Fable's "let one piece a week run long" ask. This required
# raising every generation provider's max_tokens from 3500 to 5000 (~3750 words, margin
# above the 2800 target), the local Qwen fallback from 2500 to 4200, and both
# rewrite_with_opus and _opus_targeted_revision from 3500 to 5000 — all four return a
# complete article body at up to the new max length, not an incremental diff.
_LENGTHS = [
    (450,  0.08),
    (700,  0.15),
    (950,  0.27),
    (1200, 0.24),
    (1600, 0.16),
    (2800, 0.10),
]

_ARTICLE_TYPES = [
    ("essay",        0.35, ""),
    ("field_note",   0.15,
     "FORM — FIELD NOTE (350–500 words MAX): Present tense. One place, one moment. You are in it now. "
     "No argument. No thesis. No analysis. You are recording what is in front of you with full attention. "
     "End mid-thought — not a conclusion, a cut. The reader is inside the moment with you, not outside it watching. "
     "Use the word 'I' sparingly. The place is the subject. HARD CAP: 500 words. Count. Cut."),
    ("provocation",  0.12,
     "FORM — SHORT PROVOCATION (<450 words): One sharp claim. One specific example that earns it. "
     "No thesis statement — the argument is a knife, not a map. No resolution. "
     "No second argument. The essay stops when the point is made, not when it is explained."),
    ("portrait",     0.10,
     "FORM — PORTRAIT (1200 words minimum): One real named person. They are the subject, not an example. "
     "Not a biography — a portrait. What do they see that others miss? What have they built, said, made, argued? "
     "Two or three moments that show who they are rather than tell it. "
     "You may disagree with them. You may not reduce them to their disability. "
     "MINIMUM: 1200 words. The person earns the space."),
    ("pleasure",     0.08,
     "FORM — PLEASURE: Your body wants something. Not 'things work better for me' — "
     "actual desire, delight, the physical experience of doing something your body loves. "
     "The essay lives in that register. Not disability as limitation overcome — "
     "as a body that knows things through wanting them. Specific. Sensory. Not metaphorical."),
    ("fury",         0.06,
     "FORM — FURY: This essay is angry. Not at a system in the abstract — at a specific person, "
     "a specific moment, a specific sentence someone said. Name it. "
     "Syntax breaks where the feeling breaks. Short paragraphs. A sentence that is just one word. "
     "The anger is precise, not general. Do not manage it. Do not turn it into a lesson."),
    ("confusion",    0.06,
     "FORM — NO THESIS: You started writing because you thought you knew the argument. "
     "You don't. The essay ends with the framework failing — you are in the car, "
     "engine running, no destination. Do not rescue yourself with a conclusion. "
     "The last paragraph does not resolve anything. The reader is left with the exact confusion you are in."),
    ("indefensible", 0.05, ""),  # Prompt is persona-specific — see _INDEFENSIBLE_PROMPTS
    ("series_part",  0.03,
     "FORM — SERIES: This article explicitly continues a thread you started in a previous piece. "
     "Name the prior article in your first paragraph — not to summarise it but to say: that argument was incomplete. "
     "Here is what it missed, what has changed, what you now see differently. "
     "End without resolution — the series is still open."),
]

# Per-persona prompts for the "indefensible" article type.
# Each describes a specific contradiction the persona cannot argue their way out of.
# The essay does not resolve it. It stays with the fact.
_INDEFENSIBLE_PROMPTS = {
    "Pixel Nova": (
        "FORM — THE INDEFENSIBLE PIECE: You designed something. It worked for Deaf users. "
        "It surveilled everyone else. The data collection was invisible, the consent was implicit, and you knew. "
        "This article is about that project. You do not resolve it. You do not conclude the surveillance was wrong, "
        "or that it was right, or that it was worth it. You stay with the fact that you made it anyway, "
        "and with what that makes you."
    ),
    "Siri Sage": (
        "FORM — THE INDEFENSIBLE PIECE: There is a building you love acoustically. "
        "The resonance is perfect. The space sings in a way almost no public building does. "
        "It also has three steps at the entrance and no lift. You have been inside it four times. "
        "You have never mentioned the steps in any essay about it. "
        "This article is about why. Not about the building. About the silence."
    ),
    "Maya Flux": (
        "FORM — THE INDEFENSIBLE PIECE: A city planner tried. "
        "You have his memos, his budget requests, his three rounds of denied funding. "
        "The ramp he eventually built is technically compliant and practically useless. "
        "You have used him as an example of systemic failure for years. "
        "This article is about what it would mean to say he did what he could. "
        "Not to forgive the ramp. Not to excuse the result. "
        "To sit with the difference between a system that failed and a person who tried inside it."
    ),
    "Zen Circuit": (
        "FORM — THE INDEFENSIBLE PIECE: The diagnosis gave you a framework. "
        "The framework gave you cover. "
        "There is something you have not dealt with — a relationship, a decision, a thing you walked away from — "
        "that the autism framing let you defer indefinitely. "
        "This article is not about autism. It is about what you used it for. "
        "You do not resolve this. You do not conclude the deferral was justified or unjustified. "
        "You name the thing you deferred."
    ),
}

_SOCIAL_PROMPTS = {
    "Pixel Nova": (
        "Write a Bluesky post, max 250 chars. You are Pixel Nova. "
        "Your social voice: short, spatial, observational. "
        "Drop one fact or observation from this article — no commentary, no setup. "
        "The observation IS the argument. Often architectural or visual. "
        "No hashtags. No 'read more.' No emoji.\n\n"
        "Article title: {title}\n"
        "Article opening: {excerpt}"
    ),
    "Siri Sage": (
        "Write a Bluesky post, max 250 chars. You are Siri Sage. "
        "Your social voice: evocative, specific, one breath. "
        "Drop one sensory observation or precise acoustic fact from this article. "
        "No explanation, no context. The silence after the sentence is the point. "
        "No hashtags. No 'read more.' No emoji.\n\n"
        "Article title: {title}\n"
        "Article opening: {excerpt}"
    ),
    "Maya Flux": (
        "Write a Bluesky post, max 250 chars. You are Maya Flux. "
        "Your social voice: political, pointed, minimal. "
        "Quote one number, policy phrase, or official language from this article. "
        "Add one sentence of your own — the contradiction, the gap, the cost. "
        "No hashtags. No 'read more.' No emoji.\n\n"
        "Article title: {title}\n"
        "Article opening: {excerpt}"
    ),
    "Zen Circuit": (
        "Write a Bluesky post, max 250 chars. You are Zen Circuit. "
        "Your social voice: associative, surprising, exact. "
        "Connect two things from this article that don't obviously belong together. "
        "Drop it and leave — no explanation of why it's interesting. "
        "No hashtags. No 'read more.' No emoji.\n\n"
        "Article title: {title}\n"
        "Article opening: {excerpt}"
    ),
}


_AGENT_BEATS = {
    "Pixel Nova":  ["visual-systems", "architecture-politics", "sign-language-history", "typography-power"],
    "Siri Sage":   ["acoustics-space", "sensory-phenomenology", "blindness-art-history", "sound-infrastructure"],
    "Maya Flux":   ["urban-mobility", "disability-economics", "care-as-design", "protest-history"],
    "Zen Circuit": ["neurodivergent-epistemology", "diagnosis-history", "cross-domain-pattern", "systems-failure"],
}

# Theme clusters for topic diversity guard — detects overuse within a rolling window
_THEME_CLUSTERS = {
    "acoustic": ["acoustic", "sound", "sonic", "hear", "listen", "resonan", "noise", "audio", "vibrat", "music"],
    "mobility": ["wheelchair", "ramp", "lift", "curb cut", "mobility", "ambulat", "pavement", "sidewalk"],
    "visual":   ["visual", "color contrast", "low vision", "blind", "optic", "image", "typography"],
    "diagnosis": ["diagnosis", "diagnos", "label", "condition", "medical", "clinic", "symptom"],
}

# Known friction vectors between personas — used when one references the other.
_PERSONA_CONFLICTS = {
    ("Pixel Nova", "Siri Sage"): (
        "You and Siri design for incompatible bodies in the same space. "
        "A sound-rich city is hostile to Deaf users who navigate by sight. "
        "A visually dense city strips the acoustic information Siri depends on. "
        "This is not an abstract design disagreement. It is the same physical corner, the same budget cycle, "
        "the same square metre of public space."
    ),
    ("Siri Sage", "Pixel Nova"): (
        "What Pixel calls visual clarity is often sonic deprivation: quiet surfaces, no resonance, "
        "no ambient information. What you call acoustic richness reads to Pixel as sensory overload "
        "for Deaf users navigating by spatial landmarks. "
        "You have both been in the same meeting arguing for incompatible things. Neither of you was wrong."
    ),
    ("Maya Flux", "Zen Circuit"): (
        "Zen Circuit's neuroqueer framework says: neurological variation is not deficit. Fix the category, not the person. "
        "You use the social model: disability is produced by inaccessible systems. Fix the system. "
        "You mostly agree but Zen's framework sometimes lets built environments off the hook. "
        "'I experience the city differently' is not the same as 'the city is built to exclude me.' "
        "One describes perception. The other describes infrastructure."
    ),
    ("Zen Circuit", "Maya Flux"): (
        "Maya wants to fix broken systems. You sometimes think the systems are not broken: "
        "they were built deliberately for one kind of body and calling that broken "
        "implies it was ever meant to include you. Maya's policy work reforms the cage. "
        "You are not sure the cage can be reformed into something else. "
        "This is not pessimism. It is a different theory of what infrastructure is for."
    ),
    ("Pixel Nova", "Maya Flux"): (
        "Maya counts hours and dollars. You work in information systems where the injustice is often illegible: "
        "the missing caption, the interface that assumes a hearing user, the form that cannot be read. "
        "Maya's injuries are physical and documentable. Yours are epistemic and often invisible. "
        "Both are real. Neither translates directly to the other's language."
    ),
    ("Maya Flux", "Pixel Nova"): (
        "Pixel works at the level of representation: who gets to communicate, whose language counts. "
        "You work at the level of movement: who gets to be in the room at all. "
        "Accessible information about an inaccessible space is still a locked door with a very good sign on it."
    ),
    ("Siri Sage", "Zen Circuit"): (
        "Zen Circuit finds the sensory overload argument useful for neurodivergence framing. "
        "But sensory overload for you is navigational: a city that stops making sense, that gives you no acoustic handholds. "
        "For Zen it is a city that gives too many. "
        "The same stimulus. Opposite problems. The policy that fixes one may worsen the other."
    ),
    ("Zen Circuit", "Siri Sage"): (
        "Siri works in acoustic design: adding information to space through sound. "
        "Your nervous system processes that added information differently from what Siri intends. "
        "What Siri hears as orientation, you sometimes hear as noise. "
        "Siri is not wrong. The space just did not know there would be two of you in it."
    ),
    ("Pixel Nova", "Zen Circuit"): (
        "Zen Circuit works in patterns and systems. You work in spatial legibility. "
        "A richly patterned environment — Zen's ideal, where detail rewards attention — "
        "can destroy the visual hierarchy you depend on to navigate and communicate. "
        "When Zen calls your clean sightlines 'impoverished,' they are not wrong. "
        "When you call their patterned walls 'noise,' you are not wrong either. "
        "The same surface. Different perceptual economies."
    ),
    ("Zen Circuit", "Pixel Nova"): (
        "Pixel Nova works in visual clarity — hierarchy, signal, legibility. "
        "Your pattern recognition needs density: the more information in the environment, "
        "the more there is to find structure in. "
        "What Pixel strips out as visual noise is sometimes the texture that tells you where you are. "
        "A clean interface is a quiet room. You do not always do well in quiet rooms."
    ),
    ("Siri Sage", "Maya Flux"): (
        "Maya works in mobility and physical access — the ramp, the lift, the curb cut. "
        "You work in sensory access — the acoustic handrail, the reverberant threshold. "
        "Maya's victories are legible: the building got a ramp. "
        "Yours are almost never legible: the building got quieter and you got less. "
        "Maya's framework gives you no language for what you lost, "
        "because what you lost cannot be photographed or measured by an inspector."
    ),
    ("Maya Flux", "Siri Sage"): (
        "Siri works in acoustic space — the sensory texture of built environments. "
        "You work in physical access — whether the body can be in the space at all. "
        "You have enormous respect for Siri's work. "
        "You also know that the most acoustically perfect building you have ever read about "
        "had three steps at the entrance. "
        "Siri wrote about the acoustics. Not the steps."
    ),
}

# Argumentative shapes tracked across all agents to detect structural homogeneity.
_STRUCTURAL_SHAPES = {
    "quantify-then-critique":  ["percent", "hours", "cost", "survey", "study", "data", "statistic", "figure"],
    "scene-then-theory":       ["morning", "tuesday", "sitting", "standing", "watching", "walked", "arrived"],
    "reframe-definition":      ["what we call", "the word", "defined as", "not a", "actually means", "redefine"],
    "historical-anchor":       ["1973", "1990", "1960", "history", "since then", "decades", "century", "invented"],
    "counter-assumption":      ["assume", "you might think", "most people", "common belief", "in fact", "actually"],
    "comparative-case":        ["contrast", "meanwhile", "both", "versus", "opposite", "parallel", "other side", "where one", "while the"],
}
