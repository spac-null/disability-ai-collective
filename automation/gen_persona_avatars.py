#!/usr/bin/env python3
"""
Generate persona avatar images for the 4 Crip Minds writers.

Saves to assets/{persona_slug}_avatar.jpg using the same Recraft V4.1
pipeline as article images (gen_images.py).

Usage:
    OPENROUTER_API_KEY=sk-... python3 automation/gen_persona_avatars.py
    OPENROUTER_API_KEY=sk-... python3 automation/gen_persona_avatars.py --force
"""

import argparse
import os
import pathlib
import sys
import time

REPO_ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from gen_images import call_openrouter, save_image

ASSETS_DIR = REPO_ROOT / "assets"
MODEL = "recraft/recraft-v4.1"

PERSONAS = [
    {
        "slug": "pixel_nova",
        "name": "Pixel Nova",
        "prompt": (
            "Two-colour screen print. Bold flat graphic, high contrast, no text. "
            "Visual information architecture — a wayfinding system seen from above, "
            "grid of paths that include some and exclude others. "
            "The map has a blind spot built in. "
            "References: Dutch graphic design, Werkplaats Typografie without the typography. "
            "Corita Kent energy — political and precise at once. "
            "Palette: deep purple and acid green on near-black. Square format."
        ),
    },
    {
        "slug": "siri_sage",
        "name": "Siri Sage",
        "prompt": (
            "Architectural cross-section rendered as confrontational print. "
            "The interior of a building shown as pure geometry — a lobby, a corridor, "
            "a threshold between public and private. No figures, no text. "
            "The space itself is the argument: who it welcomes, who it filters out. "
            "Gouache or risograph technique. Hard-edged planes, acoustic tension visible "
            "in the proportions. Palette: steel blue, warm ochre, deep shadow. Square format."
        ),
    },
    {
        "slug": "maya_flux",
        "name": "Maya Flux",
        "prompt": (
            "Screen-print protest graphic. A ramp — not an inspirational ramp, "
            "a ramp blocked by a sandwich board, a ramp that ends three centimetres "
            "above the street. Bold, flat, no text. "
            "The city seen from a wheelchair: pavement texture, curb height, "
            "the gap between policy and asphalt. "
            "Activist graphic energy. Palette: forest green, burnt orange, raw white. "
            "Square format, linocut texture."
        ),
    },
    {
        "slug": "zen_circuit",
        "name": "Zen Circuit",
        "prompt": (
            "Circuit diagram reimagined as a political document. No labels, no text. "
            "A network of connections — some nodes lit, some dark, "
            "the pattern of what gets called a disorder from outside "
            "and feels like a system from inside. "
            "Blueprint or technical illustration aesthetic charged with political tension. "
            "Cold palette: deep navy, copper trace, off-white on near-black. "
            "Precise, interconnected, deliberately beautiful. Square format."
        ),
    },
]


def main():
    parser = argparse.ArgumentParser(description="Generate persona avatar images")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument("--dry-run", action="store_true", help="Print prompts without calling API")
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key and not args.dry_run:
        print("Error: OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    for persona in PERSONAS:
        dest = ASSETS_DIR / f"{persona['slug']}_avatar.jpg"

        if dest.exists() and not args.force:
            print(f"  exists: {dest.name} (use --force to regenerate)")
            continue

        print(f"\n  {persona['name']}: {persona['slug']}_avatar.jpg")
        if args.dry_run:
            print(f"  PROMPT: {persona['prompt'][:120]}...")
            continue

        try:
            data = call_openrouter(persona["prompt"], "1:1", MODEL, api_key)
            save_image(data, dest)
            print(f"  saved: {dest.name} ({len(data)//1024}KB)")
        except Exception as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            sys.exit(1)

        time.sleep(2)

    if not args.dry_run:
        print("\nDone. Now update references in:")
        print("  about.html")
        print("  _layouts/post.html")
        print("  _layouts/debate.html")
        print("\nThen: git add assets/ about.html _layouts/ && git commit && git push")


if __name__ == "__main__":
    main()
