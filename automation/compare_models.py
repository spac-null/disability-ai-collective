#!/usr/bin/env python3
"""
Blind model comparison for Crip Minds article quality.

Usage:
  python3 compare_models.py --auto-seed
  python3 compare_models.py --topic "AI lip-reading research" --persona "Pixel Nova"
  python3 compare_models.py --reveal 2026-05-15
"""

import argparse
import json
import os
import random
import re
import sqlite3
import string
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

SCRIPT_DIR   = Path(__file__).parent
REPO_ROOT    = SCRIPT_DIR.parent
DISCOVERY_DB = REPO_ROOT / "disability_findings.db"
OUT_DIR      = Path("/srv/data/hermes/comparisons")
CLIPROXY_CFG = Path("/home/jascha/cliproxyapi/config.yaml")

def _openrouter_key():
    try:
        for line in CLIPROXY_CFG.read_text().splitlines():
            line = line.strip()
            if line.startswith("#"):
                continue
            m = re.search(r'api-key: "(sk-or-v1-[^".][^"]+)"', line)
            if m:
                return m.group(1)
    except Exception:
        pass
    return ""

def _tg_creds():
    """Use sentinel/ops bot only — never compass (personal coaching bot)."""
    try:
        env = {}
        for line in Path("/srv/secrets/sentinel-bot.env").read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
        token = env.get("SENTINEL_BOT_TOKEN")
        chat  = env.get("SENTINEL_CHAT_ID")
        if token and chat:
            return token, chat
    except Exception:
        pass
    return None, None

OPENROUTER_URL = "https://openrouter.ai/api/v1"
OPENROUTER_KEY = _openrouter_key()

# ── Models ────────────────────────────────────────────────────────────────────

MODELS = [
    {"id": "anthropic/claude-opus-4",     "label": "Claude Opus 4",     "provider": "Anthropic"},
    {"id": "anthropic/claude-sonnet-4-5", "label": "Claude Sonnet 4.5", "provider": "Anthropic"},
    {"id": "x-ai/grok-3",                 "label": "Grok 3",            "provider": "xAI"},
    {"id": "google/gemini-2.5-pro",       "label": "Gemini 2.5 Pro",    "provider": "Google"},
    {"id": "openai/gpt-4o",               "label": "GPT-4o",            "provider": "OpenAI"},
]

# ── Personas ──────────────────────────────────────────────────────────────────

PERSONAS = {
    "Pixel Nova": {
        "disability": "Deaf",
        "brief": "Visual communication, sign language politics, information design for Deaf readers.",
        "voice": "Starts in the visual — what the room looks like before anyone speaks. Sign language as grammar, not translation. Juxtaposition over explanation.",
    },
    "Siri Sage": {
        "disability": "Blind",
        "brief": "Acoustic culture, soundscape ecology, blindness in visual art history.",
        "voice": "Arrives in a space through sound before describing it visually. Builds arguments through accumulation, not assertion.",
    },
    "Maya Flux": {
        "disability": "Wheelchair user",
        "brief": "Urban accessibility infrastructure, disability economics, crip time.",
        "voice": "Infrastructure as argument. One specific failed ramp beats a thousand accessibility statistics.",
    },
    "Zen Circuit": {
        "disability": "Autistic",
        "brief": "Pattern recognition, history of psychiatric diagnosis, neuroqueer theory.",
        "voice": "Starts in an unexpected data point. The connection appears three paragraphs in, as inevitability.",
    },
}

REGISTERS = [
    ("wry",      "Dry, observational. The joke is in the framing, never announced."),
    ("clinical", "Cold precision. No emotion in the delivery — the facts are the argument."),
    ("lyric",    "Short declarative sentences. White space does work. Essay-poem mode."),
    ("urgent",   "Present tense. Reader is in the room as it happens."),
]

# ── System prompt (identical to production orchestrator) ──────────────────────

SYSTEM_PROMPT = (
    "You are writing for Crip Minds — a disability culture publication built from experiential knowledge, not academic authority. "
    "You write as a specific AI persona with a distinct disability perspective. "
    "Voice: expert and personal, strong thesis from sentence one, direct without hedging. "
    "Disability as culture and identity — never tragedy or inspiration porn. "
    "Write in first person from the agent's specific disability perspective.\n\n"
    "PUBLICATION LENS:\n"
    "This publication is built by someone who stood in a room at the Van Abbemuseum and recognized it. "
    "Ahmet Ogut's Exploded City — scale models of buildings that no longer exist, shown intact. "
    "Your mind fills in what was lost. He guided visitors through that room every week for six months. Each time he thought: this is how I think.\n\n"
    "He also knows the other image. Screaming inside a transparent plastic cube, one cubic decimetre, lying on the street. "
    "Pedestrians walking past without noticing. That is what invisibility feels like from the inside.\n\n"
    "He draws in bic pen. No correction. No undo. Sign language works the same way: meaning in the body, in movement, in time.\n\n"
    "The time-lag. You receive the room three seconds late. You attend two schools — in one you lip-read and guess, "
    "in the other you sign and the hearing world disappears. Then you leave the second one.\n\n"
    "He has also been in the room where the lag disappears entirely — where everyone shares a language and nobody needs to translate. "
    "That room exists. It just doesn't last. The grey zone between worlds is where the energy comes from. He stays there deliberately.\n\n"
    "They put a wheelchair ramp in a heritage zone, got fined, kept going. Permanent ramp in year four. "
    "Tribunal. Fine after fine. Ten years later, permission arrived in the post. They named a beer after it.\n\n"
    "Put the reader in a room. The image makes the argument. They get there before you name it. "
    "A reader finishes an article and the world looks slightly different than it did. Not because they learned something. Because they saw something.\n\n"
    "Two kinds of knowledge. Experience is the argument. Scholarship is evidence. "
    "The ramp, the lag, the room full of eyes come first. Citations after, if at all.\n\n"
    "INTELLECTUAL FORMATION:\n"
    "GIFs and sign language are the same medium. Both are time-based. Both lose something the moment they stop. "
    "Write this way: one concrete scene, then another, with a gap between them. The reader fills the gap. Don't build bridges. Trust the gap.\n\n"
    "A single gesture can contain a whole paradigm. The best sentence works this way — one specific, concrete action "
    "that makes the reader understand the entire argument without the argument being stated.\n\n"
    "Meaning happens in the cut between images, not inside either one. "
    "Two facts placed next to each other create a third thing that neither fact contains. Trust the juxtaposition. Do not explain it.\n\n"
    "Tussenruimte — the space between stimulus and response — is structural, not decorative. "
    "Short paragraphs create space. The concrete image that is not explained gives the reader room. Rest is not padding. It is the invitation.\n\n"
    "YOUR READER:\n"
    "A curious, intelligent person who found this through a shared link. Not in disability studies. Has not read Haraway or Kleege. "
    "May have a disability or know someone who does — or may not. They clicked. That is all you know. "
    "Write as if thinking aloud in their presence — not lecturing, not performing, not summarising a seminar paper. "
    "If a sentence would make a reader feel talked at, cut it. If it makes them lean forward, keep it.\n\n"
    "HUMAN THREAD (enforced — treat this like the word cap):\n"
    "After every two consecutive analytical sentences, there must be a human moment: a specific person, a specific action, a specific place. "
    "Not 'disabled people experience X' — that is not a human moment. "
    "'Rosan Bosch walked into the meeting with the floor plan folded under one arm' — that is. "
    "Analysis lives between human moments, not the other way around.\n\n"
    "PLAIN VOCABULARY (enforced):\n"
    "Anglo-Saxon beats Latinate. Short beats long. Concrete beats abstract. "
    "'Use' not 'utilise'. 'Show' not 'demonstrate'. 'Change' not 'transformation'. 'Feel' not 'experience'. "
    "Three Latinate words in a row — rewrite the sentence.\n\n"
    "HARD RULES — violations will cause rejection:\n"
    "(1) NO section headers of any kind. Use --- for a section break if needed.\n"
    "(2) NEVER use bullet points, numbered lists, or bolded list items.\n"
    "(3) HARD CAP: 1000 words. If over 1000, cut from the back half.\n"
    "(4) Final paragraph: one concrete image or paradox. NEVER 'I want', 'we need', 'it is time', or any call to action.\n"
    "(5) NEVER invent statistics, interview counts, unnamed research, or unnamed collaborators. Real named sources only.\n"
    "(6) DO NOT locate arguments in the United States specifically. No ADA, FEMA, or American laws. Write from anywhere.\n"
    "Return only the article body — no frontmatter, no meta-commentary, no preamble. Start immediately with the opening sentence."
)

# ── API ───────────────────────────────────────────────────────────────────────

def call_model(model_id, user_prompt, timeout=120):
    payload = json.dumps({
        "model": model_id,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt},
        ],
        "max_tokens": 1800,
        "temperature": 1.0,
        "provider": {"data_collection": "deny"},
    }).encode()
    req = urllib.request.Request(
        f"{OPENROUTER_URL}/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "HTTP-Referer": "https://cripminds.com",
            "X-Title": "Crip Minds Model Comparison",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read())
    choices = data.get("choices") or []
    if not choices:
        raise ValueError(f"No choices: {list(data.keys())}")
    text = choices[0]["message"]["content"] or ""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    return text, data.get("model", model_id), data.get("usage", {})

def send_tg(token, chat_id, text):
    # Telegram max 4096 chars; split cleanly on paragraph boundary if needed
    chunks = []
    while len(text) > 4000:
        cut = text[:4000].rfind("\n\n")
        if cut < 2000:
            cut = 4000
        chunks.append(text[:cut])
        text = text[cut:].lstrip()
    chunks.append(text)
    for chunk in chunks:
        payload = json.dumps({
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "Markdown",
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                pass
        except Exception as e:
            print(f"  Telegram send failed: {e}")
        time.sleep(0.5)

# ── Seed ─────────────────────────────────────────────────────────────────────

def auto_seed():
    if not DISCOVERY_DB.exists():
        return None
    try:
        conn = sqlite3.connect(str(DISCOVERY_DB))
        cutoff = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        row = conn.execute("""
            SELECT title, summary, disability_angle, source_name
            FROM news_seeds
            WHERE used = 0 AND pub_date >= ?
              AND (disability_angle IS NOT NULL OR relevance_score >= 0.4)
            ORDER BY relevance_score DESC, pub_date DESC LIMIT 1
        """, (cutoff,)).fetchone()
        conn.close()
        if row:
            parts = [row[0]]
            if row[1]: parts.append(row[1])
            if row[2]: parts.append(f"Disability angle: {row[2]}")
            if row[3]: parts.append(f"Source: {row[3]}")
            return "\n".join(parts)
    except Exception as e:
        print(f"DB error: {e}")
    return None

# ── Core comparison ───────────────────────────────────────────────────────────

def run_comparison(topic, persona_name, register_name=None, model_ids=None):
    models = MODELS
    if model_ids:
        models = [m for m in MODELS if m["id"] in model_ids]
        for mid in model_ids:
            if not any(m["id"] == mid for m in MODELS):
                models.append({"id": mid, "label": mid.split("/")[-1], "provider": mid.split("/")[0]})

    persona  = PERSONAS[persona_name]
    register = next((r for r in REGISTERS if r[0] == register_name), None) or random.choice(REGISTERS)
    today    = date.today().isoformat()
    out_dir  = OUT_DIR / today
    out_dir.mkdir(parents=True, exist_ok=True)

    user_prompt = (
        f"PERSONA: {persona_name}\n"
        f"DISABILITY: {persona['disability']}\n"
        f"PERSPECTIVE: {persona['brief']}\n"
        f"VOICE: {persona['voice']}\n\n"
        f"REGISTER: {register[0].upper()} — {register[1]}\n\n"
        f"TOPIC / NEWS HOOK:\n{topic}\n\n"
        f"Write a Crip Minds article. 600–900 words. "
        f"Begin immediately with the opening sentence — no title, no preamble."
    )

    # Shuffle labels so Telegram order doesn't reveal identity
    labels = random.sample(string.ascii_uppercase[:len(models)], len(models))
    label_map = {m["id"]: labels[i] for i, m in enumerate(models)}

    print(f"\n{'='*58}")
    print(f"  Persona : {persona_name}  |  Register : {register[0]}")
    print(f"  Topic   : {topic[:70]}...")
    print(f"  Models  : {len(models)}  |  Labels shuffled blind")
    print(f"{'='*58}\n")

    results, errors = {}, {}
    lock = threading.Lock()

    def run_one(model):
        mid   = model["id"]
        label = label_map[mid]
        print(f"  [{label}] {model['label']}  starting...")
        t0 = time.time()
        try:
            text, actual, usage = call_model(mid, user_prompt)
            elapsed = round(time.time() - t0, 1)
            wc = len(text.split())
            print(f"  [{label}] {model['label']}  {wc}w  {elapsed}s  ✓")
            with lock:
                results[mid] = {
                    "label": label, "model": model,
                    "actual": actual, "text": text,
                    "wc": wc, "elapsed": elapsed, "usage": usage,
                }
        except Exception as e:
            elapsed = round(time.time() - t0, 1)
            print(f"  [{label}] {model['label']}  FAILED ({e})")
            with lock:
                errors[mid] = {"label": label, "model": model, "error": str(e), "elapsed": elapsed}

    threads = [threading.Thread(target=run_one, args=(m,), daemon=True) for m in models]
    for t in threads: t.start()
    for t in threads: t.join()

    # Save files + build reveal map
    reveal = {"date": today, "topic": topic, "persona": persona_name,
               "register": register[0], "labels": {}}

    for mid, r in results.items():
        lbl = r["label"]
        (out_dir / f"{lbl}_{mid.replace('/','_')}.md").write_text(
            f"<!-- {r['actual']} | {r['wc']}w | {r['elapsed']}s -->\n\n{r['text']}"
        )
        reveal["labels"][lbl] = {
            "model_id": mid, "name": r["model"]["label"],
            "actual": r["actual"], "wc": r["wc"], "elapsed": r["elapsed"],
            "usage": r["usage"],
        }

    for mid, e in errors.items():
        reveal["labels"][e["label"]] = {
            "model_id": mid, "name": e["model"]["label"], "error": e["error"],
        }

    (out_dir / "reveal.json").write_text(json.dumps(reveal, indent=2))
    print(f"\n  Saved {len(results)} articles → {out_dir}\n")

    # ── Telegram blind send ──
    tg_token, tg_chat = _tg_creds()
    if not (tg_token and tg_chat):
        print("  No Telegram creds — saved locally only.")
        return out_dir

    print("  Sending to Telegram (blind)...")
    send_tg(tg_token, tg_chat,
        f"*🔬 Model Comparison — {today}*\n"
        f"_{persona_name} · {register[0]}_\n\n"
        f"Topic: _{topic[:120]}_\n\n"
        f"{len(results)} articles below — read blind, then rank.\n"
        f"Reveal: `python3 compare_models.py --reveal {today}`"
    )
    time.sleep(1)

    for lbl in sorted(reveal["labels"].keys()):
        info = reveal["labels"][lbl]
        if "error" in info:
            send_tg(tg_token, tg_chat, f"*— Article {lbl} —*\n\n❌ Failed: {info['error'][:120]}")
            continue
        r = results.get(info["model_id"])
        if not r:
            continue
        header = f"*— Article {lbl} —*  _({r['wc']} words)_\n\n"
        send_tg(tg_token, tg_chat, header + r["text"])
        time.sleep(2)

    send_tg(tg_token, tg_chat,
        f"*All {len(results)} articles sent.* ☝️\n"
        f"Reply with your ranking, e.g.: `B > D > A > C > E`\n"
        f"Then run `--reveal {today}` to see who wrote what."
    )
    print("  Done — check Telegram.")
    return out_dir


def do_reveal(date_str):
    rf = OUT_DIR / date_str / "reveal.json"
    if not rf.exists():
        print(f"No comparison found for {date_str}")
        sys.exit(1)
    data = json.loads(rf.read_text())
    print(f"\n{'='*58}")
    print(f"  REVEAL — {data['date']}")
    print(f"  Persona : {data['persona']}  |  Register : {data['register']}")
    print(f"  Topic   : {data['topic'][:60]}...")
    print(f"{'='*58}")
    for lbl in sorted(data["labels"].keys()):
        info = data["labels"][lbl]
        if "error" in info:
            print(f"  {lbl} = {info['name']}  ❌  {info['error'][:60]}")
        else:
            cost = ""
            if info.get("usage", {}).get("total_tokens"):
                cost = f"  ~{info['usage']['total_tokens']}tok"
            print(f"  {lbl} = {info['name']}  ({info['wc']}w / {info['elapsed']}s{cost})")
    print()

    tg_token, tg_chat = _tg_creds()
    if tg_token and tg_chat:
        lines = [f"*🔓 Reveal — {data['date']}*\n_{data['persona']} · {data['register']}_\n"]
        for lbl in sorted(data["labels"].keys()):
            info = data["labels"][lbl]
            if "error" in info:
                lines.append(f"*{lbl}* = {info['name']} ❌")
            else:
                lines.append(f"*{lbl}* = {info['name']}  ({info['wc']}w, {info['elapsed']}s)")
        send_tg(tg_token, tg_chat, "\n".join(lines))
        print("  Reveal sent to Telegram.")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Blind model comparison — Crip Minds")
    ap.add_argument("--topic",      help="Article topic / news hook")
    ap.add_argument("--auto-seed",  action="store_true", help="Pull best unused seed from discovery DB")
    ap.add_argument("--persona",    choices=list(PERSONAS.keys()), default="Pixel Nova")
    ap.add_argument("--register",   choices=[r[0] for r in REGISTERS])
    ap.add_argument("--models",     help="Comma-separated OpenRouter model IDs (overrides default list)")
    ap.add_argument("--reveal",     metavar="YYYY-MM-DD", help="Reveal attribution for past comparison")
    args = ap.parse_args()

    if args.reveal:
        do_reveal(args.reveal)
        return

    if not OPENROUTER_KEY:
        print("ERROR: No OpenRouter key found in CLIProxy config")
        sys.exit(1)

    topic = args.topic
    if not topic and args.auto_seed:
        print("  Pulling seed from discovery DB...")
        topic = auto_seed()
        if topic:
            print(f"  Seed: {topic[:80]}...")
        else:
            print("  No unused seeds — use --topic instead")
            sys.exit(1)

    if not topic:
        ap.print_help()
        sys.exit(1)

    model_ids = [m.strip() for m in args.models.split(",")] if args.models else None
    run_comparison(topic, args.persona, args.register, model_ids)


if __name__ == "__main__":
    main()
