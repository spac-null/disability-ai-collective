#!/usr/bin/env python3
"""art_director.py -- one bounded, text-only editorial art-direction step.

WHAT IT REPLACES. gen_images.py generated a fixed three-image set -- setting_1 16:9,
moment_2 1:1, symbol_3 1:1 -- from the article title and a ~150-character excerpt, under a
per-persona style template chosen by a hash of the slug. That pipeline cannot see the
article. It produced three images for a 600-word piece and three for a 2,500-word one, in
the same persona look every time, with alt text of the literal form
"{title} -- editorial illustration".

WHAT THIS IS NOT. Not a vision system, not an image-acquisition step, not a new factual
gate, and not a layout engine. It reads text and returns a brief. Recraft still receives
TEXT ONLY; no source image reaches it, here or anywhere.

WHY IT CAN'T BLOCK A PUBLICATION. Art direction is a quality improvement on an image set,
and an article with no art direction is an article with the images it would have had
anyway. Every failure path returns None and the caller keeps the existing behaviour. This
is the opposite of the composition stages, where a provider failure must HOLD: there, a
missing answer would be silently substituted into an article's argument.

ONE MODEL CALL. On the Claude subscription transport, like every other editorial
reasoning call.
"""
import json
import re

SCHEMA_VERSION = 1

FUNCTIONS = ("ESTABLISH_PLACE", "SHOW_MECHANISM", "CLARIFY_SPATIAL_RELATION",
             "CONCEPTUAL_COVER", "BREATHING_ROOM", "DIAGRAM")

REGISTERS = ("SPATIAL_DIAGRAMMATIC", "MATERIAL_EDITORIAL",
             "ATMOSPHERIC_OBSERVATIONAL", "CONCEPTUAL_SYSTEMIC")

MAX_IMAGES = 3

# Aspect ratio follows the image's FUNCTION, not a fixed slot in a three-image set.
RATIO_BY_FUNCTION = {
    "ESTABLISH_PLACE": "16:9", "SHOW_MECHANISM": "1:1",
    "CLARIFY_SPATIAL_RELATION": "16:9", "CONCEPTUAL_COVER": "16:9",
    "BREATHING_ROOM": "1:1", "DIAGRAM": "16:9",
}

# ── the core prohibition ──────────────────────────────────────────────────────
# NEVER ILLUSTRATE DISABILITY. The publication's subject is the world it examines, and
# the stock iconography of disability illustrates a category instead: a pictogram stands
# for "this article is about disabled people" and tells a reader nothing about the
# building, study, rule or system the piece is actually reading. Worse, it is the visual
# form of the topic-not-lens failure the editorial doctrine spent its whole history
# retiring. These terms are refused in a returned brief, not merely discouraged in the
# prompt, because a prompt is advice and a validator is a contract.
FORBIDDEN_ICONOGRAPHY = (
    "wheelchair", "accessibility symbol", "accessible icon", "disabled symbol",
    "blue badge", "prosthetic", "prosthesis", "puzzle piece", "jigsaw",
    "generic ear", "cupped ear", "human ear floating", "brain diagram", "glowing brain",
    "silhouette overcoming", "overcoming silhouette", "triumphant silhouette",
    "inspirational figure", "ramp as metaphor", "metaphorical ramp",
    "white cane icon", "guide dog icon", "hearing aid icon", "sign language hands icon",
)

# ── what a VISUAL observation may and may not license ─────────────────────────
# The sidecar is NON_CLAIM_BEARING by construction and stays that way here. Its object
# and material vocabulary is genuinely useful to an illustrator -- "corrugated roof",
# "timber post", "earthen wall" -- and it is the only place subject-specific visual
# character exists at all. What it may never do is become an assertion, so these shapes
# are stripped from any visual anchor before the brief is accepted.
_VISUAL_PROHIBITED = (
    (re.compile(r"\d"), "vision_read_number"),
    (re.compile(r"\b(?:metre|meter|metres|meters|cm|mm|inch|inches|foot|feet|"
                r"square|storey|storeys|stories|floor level|gradient|slope of)\b", re.I),
     "measurement_language"),
    (re.compile(r"\b(?:accessible|inaccessible|accessibility|step[- ]free|"
                r"wheelchair|ADA|compliance|compliant|code[- ]compliant)\b", re.I),
     "accessibility_claim"),
    (re.compile(r"\b(?:only|sole|exclusive)\s+(?:route|entrance|access|way in)\b", re.I),
     "route_exclusivity"),
    (re.compile(r"\b(?:no other|there is no|without any|lacks any|absence of)\b", re.I),
     "absence_of_alternatives"),
    (re.compile(r"\b(?:cannot|can't|unable to|is able to|can reach|could not reach)\b", re.I),
     "human_capability_claim"),
)

_VISUAL_FIELDS_ALLOWED = ("observable_facts", "spatial_relationships", "printed_labels")
_VISUAL_DIGEST_KEYS = ("objects_and_materials", "spatial_relationships", "printed_labels")


def visual_anchor_violation(text: str) -> str:
    """Why this line may not serve as a VISUAL anchor. '' when it may."""
    for rx, reason in _VISUAL_PROHIBITED:
        if rx.search(text or ""):
            return reason
    return ""


def visual_context_digest(sidecar: dict | None, max_lines: int = 24) -> dict:
    """The publishable-to-an-illustrator slice of a NON_CLAIM_BEARING sidecar.

    Three of the sidecar's fields are useful vocabulary; two are not. `not_established`
    and `questions_raised` are the observer's own hedges and open questions -- passing
    them to an art director invites it to illustrate an uncertainty as if it were a
    subject. `rejected` is guard-audit material and is never reused, which its own
    comment in visual_observe.py says explicitly.

    Every surviving line is re-guarded here rather than trusted. The sidecar's guards
    already ran, but this module must not depend on another module's invariant holding
    for a purpose it was not written for.
    """
    out = {"present": False, "objects_and_materials": [], "spatial_relationships": [],
           "printed_labels": [], "dropped": 0}
    if not isinstance(sidecar, dict):
        return out
    if sidecar.get("status") != "NON_CLAIM_BEARING":
        return out                      # not the object this function is contracted to read
    out["present"] = True
    for obs in (sidecar.get("observations") or []):
        for line in (obs.get("observable_facts") or []):
            if visual_anchor_violation(line):
                out["dropped"] += 1
            elif len(out["objects_and_materials"]) < max_lines:
                out["objects_and_materials"].append(line)
        for line in (obs.get("spatial_relationships") or []):
            if visual_anchor_violation(line):
                out["dropped"] += 1
            elif len(out["spatial_relationships"]) < max_lines:
                out["spatial_relationships"].append(line)
        for lab in (obs.get("printed_labels") or []):
            s = lab.get("label") if isinstance(lab, dict) else str(lab)
            if s and s not in out["printed_labels"] and len(out["printed_labels"]) < max_lines:
                out["printed_labels"].append(s)
    return out


def architecture_digest(arch: dict | None, article_text: str = "") -> dict:
    """Beat structure and spine only.

    WHITELIST, not a blacklist. The Architecture object also carries fact-permission
    internals, per-beat allowed fact ids, withholding instructions and -- depending on how
    it was assembled -- the Worth gate's lens reasoning. None of that belongs in an art
    brief: the art director is not deciding what may be claimed, and handing it the lens
    argument invites an illustration of the ARGUMENT rather than of the world.
    """
    if not isinstance(arch, dict):
        return {}

    def ok(text):
        """Structural guidance survives only if the settled article supports it."""
        return (not article_text) or text_supports(text, article_text)

    beats, dropped = [], []
    for b in (arch.get("beats") or [])[:12]:
        carrier = (b.get("concrete_carrier") or b.get("carrier") or "")[:200]
        bid = b.get("beat_id")
        if not ok(carrier):
            dropped.append(bid)
            continue
        # ORDER AND CARRIER ONLY when reconciling. `happens` and `concept` are the
        # architecture's own prose about what a beat argues, and that is precisely where a
        # superseded framing lives -- five of WildSumaco's seven beats carry the withdrawn
        # ADA material in those fields while their carriers do not. A carrier the final
        # prose fully supports is safe structural guidance; the argument around it is not.
        beat = {"beat_id": bid, "carrier": carrier}
        if not article_text:
            beat.update({"happens": (b.get("happens") or "")[:300],
                         "concept": (b.get("concept_introduced") or b.get("concept") or "")[:200]})
        beats.append(beat)
    out = {"article_type": arch.get("article_type"), "beats": beats}
    if dropped:
        out["beats_omitted_as_unsupported_by_the_settled_article"] = dropped
    for key, src in (("story_spine", arch.get("story_spine")),
                     ("opening", arch.get("opening_object_or_event") or arch.get("opening")),
                     ("turn", arch.get("turn")),
                     ("ending_move", arch.get("ending_move"))):
        v = (src or "")[:500]
        if v and ok(v):
            out[key] = v
    return out


# ── the settled article is authoritative ─────────────────────────────────────
# THE DRIFT THIS EXISTS TO STOP, measured on the WildSumaco retrospective. The run's
# ARCHITECTURE.json still carried the ADA-accessibility-field argument -- story_spine,
# crip_turn, ending_move and five of its seven beats mention it somewhere -- while the
# SETTLED article contains the strings "ADA" and "accessib" exactly zero times, because
# that claim was removed from the live piece after Grounding objected to the adjacency.
# Handed both, the art director spent one of only two image slots on the withdrawn
# argument. Nothing was factually wrong in its brief; it was illustrating an article that
# no longer exists.
#
# THE PRINCIPLE: the settled article is authoritative. Architecture is an ORDERING AID --
# beat order, relationships, possible placement, story movement -- and never a second
# factual or editorial source. It may not reintroduce a withdrawn claim, a superseded
# framing, abandoned factual material, or an old argument absent from the final prose.
#
# DETERMINISTIC, and deliberately not a model step or a factual gate. Nothing HOLDs here;
# unrecoverable material is simply not passed on, and an art director that never sees the
# stale beat cannot spend a slot on it.
_TOKEN_RE = re.compile(r"[A-Z]{2,}(?![a-z])|[A-Za-z]{5,}")
_STEM = 5

# FUNCTION WORDS ARE NOT SUBJECT CONTENT. Found on the WildSumaco re-run: the beat "the
# pavilion floor above the natural ground" -- one of the two beats genuinely worth
# illustrating -- was omitted because the settled article says the floor is lifted "clear
# of" the ground and never uses the word "above". A preposition's absence is a difference
# in phrasing, not a withdrawn claim, and treating it as drift threw away good structural
# guidance to catch nothing. Only these are exempted: every one is a preposition,
# conjunction or determiner that happens to survive the 5-letter filter. Subject nouns are
# never on this list, so "cabuya" -- a material the final prose does not name -- still
# correctly omits its beat.
_FUNCTION_WORDS = frozenset("""
above below under over between through without within against across around during
where which their there these those while would could should still being about after
before because however though since among toward towards until unless whether other
another every each both same than then when what whose whom that this with from into
onto upon also more most less least such very just only than
""".split())


def content_tokens(text: str) -> list:
    """Distinctive tokens: acronyms of 2+ capitals, and words of 5+ letters.

    Acronyms are picked up separately and on purpose. "ADA" is three characters and would
    fall straight through a 5-letter word filter, which is exactly how a withdrawn legal
    framework gets back into an article's illustrations.
    """
    out, seen = [], set()
    for t in _TOKEN_RE.findall(text or ""):
        acronym = t.isupper() and len(t) <= 5
        k = t if acronym else t.lower()
        if not acronym and k in _FUNCTION_WORDS:
            continue
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def text_supports(phrase: str, article_text: str) -> bool:
    """True when EVERY distinctive token of `phrase` is recoverable from the article.

    ALL, not most. A majority test is the wrong shape here: "the ADA accessibility field
    on the station's directory entry" shares field, station, directory and entry with the
    settled prose and would pass a half-overlap rule while smuggling back the one term the
    article withdrew. What makes a phrase safe as structural guidance is that nothing in it
    is foreign to the final prose.

    Stem-tolerant by prefix so ordinary inflection (wall/walls, record/recorded) is not
    read as drift. A phrase with no distinctive tokens at all is not evidence of anything
    and is not treated as supported.
    """
    toks = content_tokens(phrase)
    if not toks:
        return False
    hay = article_text or ""
    low = hay.lower()
    for t in toks:
        if t.isupper() and len(t) <= 5:
            if re.search(r"\b%s\b" % re.escape(t), hay):      # acronym: case-sensitive
                continue
            return False
        if t[:_STEM] in low:
            continue
        return False
    return True


def reconcile_brief(brief: dict, article_text: str) -> tuple:
    """Strip factual anchors the settled article does not support. Returns (brief, notes).

    A BACKSTOP, not the primary defence -- architecture_digest already withholds
    unrecoverable material, so a stripped anchor here means the art director reached past
    what it was given. An image left with no supported anchor is dropped and image_count
    follows, because an image with nothing behind it in the final prose is decoration and
    the whole point of the count decision is that a slot is never filled for its own sake.

    KNOWN AND ACCEPTED COST, measured on both retrospectives: an exact-token test cannot
    see a synonym, so it strips a legitimate PARAPHRASE. Two anchors of roughly eighteen
    went that way, and BOTH failed on an attribution verb while every substantive token
    matched:

      "... stone sourced nearby"            vs an article saying "harvested or purchased
                                               nearby"
      "a sponsorship certificate NAMING a   vs an article that has the certificate, the
       job, a salary ... and forty hours"      salary, the hours -- but not "naming"

    The tempting fix is to exempt verbs the way _FUNCTION_WORDS exempts prepositions. It
    is NOT taken here, and the reason is that a verb is where a claim lives: recruited,
    classified, withdrew, refused. Exempting the category to catch two participles would
    open the hole this function exists to close. The other alternative is semantic
    matching, which this design deliberately does not add.

    So it degrades gracefully instead: an image is dropped only when ALL of its anchors
    fail, so a stripped paraphrase costs an anchor and not an image -- 0 images dropped
    across both runs. IF THIS EVER STARTS DROPPING IMAGES, that is the signal to revisit
    it, and the fix then is a per-anchor tolerance measured against real briefs, not a
    blanket verb exemption.
    """
    notes = {"anchors_dropped": [], "images_dropped": 0}
    if not isinstance(brief, dict) or not article_text:
        return brief, notes
    kept = []
    for im in (brief.get("images") or []):
        if not isinstance(im, dict):
            continue
        good = [a for a in (im.get("factual_anchors") or [])
                if text_supports(str(a), article_text)]
        for a in (im.get("factual_anchors") or []):
            if a not in good:
                notes["anchors_dropped"].append(str(a)[:120])
        if not good:
            notes["images_dropped"] += 1
            continue
        im = dict(im, factual_anchors=good)
        kept.append(im)
    brief = dict(brief, images=kept, image_count=len(kept))
    return brief, notes


ART_DIRECTOR_SYSTEM = (
    "You are the art director for Crip Minds. You read a finished article and decide what, "
    "if anything, should be illustrated. You return JSON only.\n"
    "\n"
    "FIRST DECIDE HOW MANY IMAGES THIS ARTICLE WANTS: 0, 1, 2 or 3. ZERO IS A REAL ANSWER "
    "AND OFTEN THE RIGHT ONE. Do not assume a hero plus a detail plus an abstract. A short "
    "argumentative piece may want one image or none; a spatial piece may want two that do "
    "different work. Decide from the article, then justify the number in one clause. Never "
    "propose an image whose only purpose is to fill a slot.\n"
    "\n"
    "NEVER ILLUSTRATE DISABILITY. Illustrate the world the article is examining. Do not "
    "reach for a wheelchair pictogram, an accessibility symbol, a floating ear, a glowing "
    "brain, a prosthetic, a puzzle piece, a ramp used as metaphor, or a silhouette "
    "overcoming anything. Those illustrate a CATEGORY and tell a reader nothing about this "
    "subject. The single exception: such an object or person may appear when it is "
    "genuinely part of this article's evidence and the image actually needs it.\n"
    "\n"
    "VISUAL GRAMMAR -- FOUR REGISTERS, NOT ONE HOUSE STYLE. Crip Minds must not look like "
    "one repeated AI illustration. Choose the register the article earns:\n"
    "  SPATIAL_DIAGRAMMATIC        architecture, routes, mechanisms, interfaces, systems, "
    "spatial relationships\n"
    "  MATERIAL_EDITORIAL         objects, documents, materials, institutions, concrete "
    "fragments\n"
    "  ATMOSPHERIC_OBSERVATIONAL  place, weather, sound, scale, sensory environment\n"
    "  CONCEPTUAL_SYSTEMIC        classification, AI, measurement, bureaucracy, abstract "
    "systems\n"
    "Different images in one article may use different registers.\n"
    "\n"
    "SHARED PRINCIPLES, ACROSS ALL REGISTERS: tactile rather than glossy. Strong, simple "
    "composition. Concrete subject elements over generic symbolism. Evidence-aware "
    "abstraction. Limited visual clutter. Strange only when the subject itself is strange. "
    "AND NEVER MORE CERTAIN THAN THE ARTICLE -- if the piece leaves something unresolved, "
    "the image does not resolve it.\n"
    "\n"
    "The persona informs TONE. It does not dictate a medium, a palette or a fixed look, and "
    "you may not name or imitate a living artist, studio or photographer.\n"
    "\n"
    "THE SETTLED ARTICLE IS AUTHORITATIVE. The architecture you are shown is an ORDERING "
    "AID -- beat order, relationships, possible placement, story movement -- and never a "
    "second factual or editorial source. IF THE ARCHITECTURE AND THE SETTLED ARTICLE "
    "DIVERGE, FOLLOW THE SETTLED ARTICLE. Do not resurrect material absent from the final "
    "prose: an argument the piece once made and no longer makes, a claim that was "
    "withdrawn, a superseded framing, or abandoned factual material. If you cannot find "
    "something in the article in front of you, it is not in the article.\n"
    "\n"
    "FACTUAL ANCHORS come from the settled article -- things the piece itself establishes, "
    "recoverable from its prose. VISUAL ANCHORS are optional and come only from the "
    "non-claim-bearing visual context, when it is supplied: object and material vocabulary, "
    "broad spatial relationships, printed labels, subject-specific visual character. A "
    "visual anchor may NEVER assert a dimension, a numeric level, an exact count, "
    "accessibility, legal compliance, that a route is the only one, that no alternative "
    "exists, or what a person can or cannot do. If you catch yourself writing any of those, "
    "it is not an anchor.\n"
    "\n"
    "PEOPLE: NONE by default. Include a person only when the article itself carries a "
    "supported human subject and the image genuinely needs them.\n"
    "\n"
    "COMPOSITION NOTES are plain visual direction. You have not seen any photograph, so do "
    "not write 'recreate', 'same angle as', 'as in the photo', or refer to a source image's "
    "framing in any way.\n"
    "\n"
    "ALT TEXT is real descriptive alt text for the image you are commissioning -- what a "
    "reader who cannot see it would need. Never '<title> -- editorial illustration'.\n"
    "\n"
    "PLACEMENT is editorial, not arithmetic: HERO, or AFTER_BEAT:<beat_id> naming a beat "
    "from the architecture, or END. Do not use paragraph percentages."
)

ART_DIRECTOR_SCHEMA = (
    "Reply with ONE JSON object:\n"
    '{"image_count": 0,\n'
    ' "count_reasoning": "one clause: why this many",\n'
    ' "images": [\n'
    '   {"function": "ESTABLISH_PLACE|SHOW_MECHANISM|CLARIFY_SPATIAL_RELATION|'
    'CONCEPTUAL_COVER|BREATHING_ROOM|DIAGRAM",\n'
    '    "register": "SPATIAL_DIAGRAMMATIC|MATERIAL_EDITORIAL|'
    'ATMOSPHERIC_OBSERVATIONAL|CONCEPTUAL_SYSTEMIC",\n'
    '    "editorial_purpose": "one sentence: what the reader should see differently",\n'
    '    "factual_anchors": ["things the article establishes"],\n'
    '    "visual_anchors": ["optional, from the visual context only"],\n'
    '    "must_not_invent": ["explicit list"],\n'
    '    "people": "NONE",\n'
    '    "composition_note": "plain visual direction",\n'
    '    "alt_text": "real descriptive alt text",\n'
    '    "placement": "HERO|AFTER_BEAT:<beat_id>|END"}\n'
    " ]}\n"
    'If the article wants no image, reply {"image_count": 0, "count_reasoning": "...", '
    '"images": []} and nothing else.\n'
    "No prose outside the JSON."
)


def build_user_prompt(article_text: str, title: str = "", dek: str = "",
                      arch: dict | None = None, persona: str = "",
                      visual_sidecar: dict | None = None,
                      beat_ids: list | None = None) -> str:
    """Assemble the art director's only input.

    Deliberately absent, and each for its own reason: raw source images (Recraft and this
    step are both text-only), research source bodies (the article is the settled account;
    the sources are where an unsettled claim would come back in), internal provenance,
    factual gaps, and the Worth gate's reasoning.
    """
    ad = architecture_digest(arch, article_text or "")
    vd = visual_context_digest(visual_sidecar)
    parts = ["TITLE", "  " + (title or "(none)").strip(), ""]
    if dek:
        parts += ["DEK", "  " + dek.strip(), ""]
    parts += ["PERSONA (tone only, never a fixed medium or palette)",
              "  " + (persona or "(none)"), ""]
    if ad:
        parts += ["STORY ARCHITECTURE -- ORDERING AID ONLY, NOT A FACTUAL SOURCE",
                  json.dumps(ad, indent=1, ensure_ascii=False), ""]
        ids = [b["beat_id"] for b in ad.get("beats") or [] if b.get("beat_id")]
        if ids:
            parts += ["BEAT IDS AVAILABLE FOR AFTER_BEAT PLACEMENT", "  " + ", ".join(ids), ""]
    if vd["present"]:
        parts += ["NON_CLAIM_BEARING VISUAL CONTEXT -- vocabulary only, never an assertion",
                  json.dumps({k: vd[k] for k in _VISUAL_DIGEST_KEYS},
                             indent=1, ensure_ascii=False), ""]
    else:
        parts += ["NON_CLAIM_BEARING VISUAL CONTEXT", "  (none supplied)", ""]
    parts += ["THE SETTLED ARTICLE", "<<<ARTICLE", (article_text or "").strip(), "ARTICLE>>>",
              "", ART_DIRECTOR_SCHEMA]
    return "\n".join(parts)


def validate_brief(brief: dict, beat_ids: list | None = None) -> list:
    """Contract errors in a returned brief. [] means usable."""
    errs = []
    if not isinstance(brief, dict):
        return ["the brief is not a JSON object"]
    count = brief.get("image_count")
    if not isinstance(count, int) or not (0 <= count <= MAX_IMAGES):
        return ["image_count must be an integer 0..%d, got %r" % (MAX_IMAGES, count)]
    images = brief.get("images")
    if not isinstance(images, list):
        return ["images must be a list"]
    if len(images) != count:
        errs.append("image_count is %d but %d image brief(s) were returned"
                    % (count, len(images)))
    known = set(beat_ids or [])
    for i, im in enumerate(images, 1):
        if not isinstance(im, dict):
            errs.append("image %d is not an object" % i)
            continue
        tag = "image %d" % i
        if im.get("function") not in FUNCTIONS:
            errs.append("%s: function %r is not one of %s" % (tag, im.get("function"), ", ".join(FUNCTIONS)))
        if im.get("register") not in REGISTERS:
            errs.append("%s: register %r is not one of %s" % (tag, im.get("register"), ", ".join(REGISTERS)))
        for f in ("editorial_purpose", "composition_note", "alt_text"):
            if not str(im.get(f) or "").strip():
                errs.append("%s: %s is empty" % (tag, f))
        if not (im.get("factual_anchors") or []):
            errs.append("%s: no factual_anchors -- an image with no anchor in the article "
                        "is decoration" % tag)
        # Generic alt text is the failure this step exists to end.
        alt = str(im.get("alt_text") or "")
        if re.search(r"(?:editorial|conceptual|detail)\s+(?:illustration|image)\s*$", alt, re.I) \
           or alt.strip().startswith(("—", "-")):
            errs.append("%s: alt_text is a template, not a description: %r" % (tag, alt[:80]))
        # Composition may not reference a source photograph it never saw.
        if re.search(r"\b(?:recreate|same angle|as in the (?:photo|photograph|image)|"
                     r"match the (?:photo|framing)|source photo)\b",
                     str(im.get("composition_note") or ""), re.I):
            errs.append("%s: composition_note refers to a source photograph" % tag)
        # The core rule, enforced rather than requested.
        blob = " ".join(str(im.get(k) or "") for k in
                        ("editorial_purpose", "composition_note", "alt_text")) \
               + " " + " ".join(str(x) for x in (im.get("factual_anchors") or [])
                                + (im.get("visual_anchors") or []))
        for term in FORBIDDEN_ICONOGRAPHY:
            if term in blob.lower():
                errs.append("%s: forbidden disability iconography %r -- illustrate the "
                            "world, not the category" % (tag, term))
                break
        for a in (im.get("visual_anchors") or []):
            why = visual_anchor_violation(str(a))
            if why:
                errs.append("%s: visual anchor asserts what a visual observation cannot "
                            "(%s): %r" % (tag, why, str(a)[:70]))
        pl = str(im.get("placement") or "")
        if pl.startswith("AFTER_BEAT:"):
            bid = pl.split(":", 1)[1].strip()
            if known and bid not in known:
                errs.append("%s: placement names beat %r which is not in the architecture"
                            % (tag, bid))
        elif pl not in ("HERO", "END", "BREATHING", "END / BREATHING"):
            errs.append("%s: placement %r is not HERO, AFTER_BEAT:<beat_id> or END"
                        % (tag, pl))
        if re.search(r"\d+\s*%", pl):
            errs.append("%s: placement is a paragraph percentage" % tag)
    return errs


def art_direct(provider, article_text: str, title: str = "", dek: str = "",
               arch: dict | None = None, persona: str = "",
               visual_sidecar: dict | None = None, max_tokens: int = 3_000) -> dict:
    """ONE model call. Returns {"ok", "brief", "reason", "identity"}; never raises.

    A failure here is not an editorial failure. The caller falls back to the existing
    image path, and an article ships with the images it would have had before this module
    existed. That is why nothing in this function propagates an exception.
    """
    ad = architecture_digest(arch, article_text or "")
    beat_ids = [b["beat_id"] for b in (ad.get("beats") or []) if b.get("beat_id")]
    out = {"ok": False, "brief": None, "reason": "", "identity": {},
           "beats_omitted": ad.get("beats_omitted_as_unsupported_by_the_settled_article", []),
           "reconciled": {}}
    try:
        user = build_user_prompt(article_text, title, dek, arch, persona,
                                 visual_sidecar, beat_ids)
        comp = provider.complete(system=ART_DIRECTOR_SYSTEM, user=user,
                                 max_tokens=max_tokens, temperature=0)
        text = getattr(comp, "text", comp if isinstance(comp, str) else "")
        out["identity"] = getattr(comp, "identity", lambda: {})() \
            if callable(getattr(comp, "identity", None)) else {}
        brief = _parse_json_object(text)
    except Exception as e:                                             # noqa: BLE001
        out["reason"] = "%s: %s" % (type(e).__name__, str(e)[:200])
        return out
    brief, notes = reconcile_brief(brief, article_text or "")
    out["reconciled"] = notes
    errs = validate_brief(brief, beat_ids)
    if errs:
        out["reason"] = "brief rejected: " + "; ".join(errs[:4])
        out["brief"] = brief
        return out
    brief["schema_version"] = SCHEMA_VERSION
    brief["visual_context_used"] = visual_context_digest(visual_sidecar)["present"]
    out.update({"ok": True, "brief": brief})
    return out


def _parse_json_object(text: str) -> dict:
    t = (text or "").strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t, flags=re.S)
    i, j = t.find("{"), t.rfind("}")
    if i < 0 or j <= i:
        raise ValueError("no JSON object in the reply")
    return json.loads(t[i:j + 1])


# ── brief -> Recraft text prompt ──────────────────────────────────────────────
_REGISTER_DIRECTION = {
    "SPATIAL_DIAGRAMMATIC": (
        "Measured, constructed image with the clarity of a drawing rather than a "
        "photograph. Legible spatial logic, clean linework, flat planes, restrained "
        "palette. No text or labels."),
    "MATERIAL_EDITORIAL": (
        "Object-led editorial image. Real materials and surfaces, tactile rather than "
        "glossy, close and deliberate. Plain ground, strong single subject. No text."),
    "ATMOSPHERIC_OBSERVATIONAL": (
        "Atmosphere and scale carry the image. Light, air, distance and weather do the "
        "work; muted tonal range, generous negative space, no dramatisation. No text."),
    "CONCEPTUAL_SYSTEMIC": (
        "Abstract, systemic image built from ordered form -- grids, fields, sorting, "
        "repetition with a break in it. Cool and precise, never whimsical. No figures, "
        "no text."),
}


def build_image_prompt(image: dict, persona: str = "") -> str:
    """The text brief Recraft receives. Text only, always -- no image is ever sent."""
    p = [_REGISTER_DIRECTION.get(image.get("register"), _REGISTER_DIRECTION["MATERIAL_EDITORIAL"])]
    p.append("This image exists to %s." % str(image.get("editorial_purpose") or "").rstrip("."))
    anchors = [str(a) for a in (image.get("factual_anchors") or [])][:6]
    if anchors:
        p.append("Show, concretely: " + "; ".join(anchors) + ".")
    van = [str(a) for a in (image.get("visual_anchors") or [])
           if not visual_anchor_violation(str(a))][:6]
    if van:
        p.append("Material and spatial character: " + "; ".join(van) + ".")
    note = str(image.get("composition_note") or "").strip()
    if note:
        p.append("Composition: " + note.rstrip(".") + ".")
    people = str(image.get("people") or "NONE").strip().upper()
    p.append("No people in frame." if people in ("", "NONE") else "People: " + str(image.get("people")))
    mni = [str(m) for m in (image.get("must_not_invent") or [])][:8]
    if mni:
        p.append("Do not include or imply: " + "; ".join(mni) + ".")
    p.append("Tactile rather than glossy. Strong simple composition, limited clutter. "
             "No lettering, captions or watermarks anywhere in the image. "
             "No named artist's style.")
    if persona:
        p.append("Editorial tone (not a medium or palette): %s." % persona)
    return " ".join(p)


def ratio_for(image: dict) -> str:
    return RATIO_BY_FUNCTION.get(image.get("function"), "16:9")


def asset_suffix(index: int, image: dict) -> str:
    """Stable, descriptive filename part. Not the old fixed setting/moment/symbol slots."""
    return "%d_%s" % (index, str(image.get("function") or "image").lower())
