
import sys
import os
import json
import re
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)).replace('/automation', ''))
from generate_sophisticated_art_simple import SophisticatedArtGenerator

# Article metadata
article_slug = "accessibility-critique-the-access-story-behind-getting-here-on-the-go"
article_title = "Accessibility Critique: The Access Story Behind 'Getting here on the GO -'"
agent_name = "Pixel Nova"

# Image prompts (derived from QuickFix Orchestrator output)
image_prompt_hints = {
    "keywords": ["disability", "Visual Design", "accessibility"],
    "mood": "analytical",
    "style": "sophisticated pixel art, abstract representation"
}

pixel_art_generator = SophisticatedArtGenerator(width=800, height=450)

assets_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent / "assets"
assets_dir.mkdir(parents=True, exist_ok=True)

pixel_art_filenames = []

# Generate 3 images
for i in range(1, 4):
    # Dynamically adjust prompt for diversity
    prompt_suffix = f" depicting {article_title} from a {agent_name} perspective. Image {i} of 3."
    
    if i == 1:
        prompt = f"Visual chaos in transportation hubs from a deaf designer's perspective, {image_prompt_hints['style']}, {image_prompt_hints['mood']}." + prompt_suffix
        alt_text = "Visual chaos in transportation hubs from a deaf designer's perspective"
    elif i == 2:
        prompt = f"Information hierarchy failures showing how critical information gets lost in visual clutter, {image_prompt_hints['style']}, {image_prompt_hints['mood']}." + prompt_suffix
        alt_text = "Information hierarchy failures showing how critical information gets lost in visual clutter"
    else:
        prompt = f"Disability co-design process: Building accessibility into foundations from the beginning, {image_prompt_hints['style']}, {image_prompt_hints['mood']}." + prompt_suffix
        alt_text = "Disability co-design process: Building accessibility into foundations from the beginning"

    # Use generate_art directly from the instance
    image_data = pixel_art_generator.generate_art(prompt=prompt)
    
    img_filename = f"{article_slug}_pixel_art_{i}.png"
    img_path = assets_dir / img_filename
    
    # The generate_art method returns raw image data, not a path. Need to save it.
    # Assuming image_data is bytes
    if image_data and isinstance(image_data, bytes):
        with open(img_path, 'wb') as f:
            f.write(image_data)
        pixel_art_filenames.append(img_filename)
        print(f"Generated and saved image: {img_filename}")
    else:
        print(f"Failed to generate image {i} for {article_slug}.")

print(f"Generated images: {pixel_art_filenames}")
