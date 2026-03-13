#!/usr/bin/env python3
"""
Extract image prompts from article content.
"""

import json
import re
import sys

def extract_image_prompts_from_content(content, title, metadata):
    """Extract image prompts from article content."""
    
    # Analyze content for themes
    content_lower = content.lower()
    
    # Keywords to look for
    theme_keywords = {
        'visual': ['visual', 'see', 'look', 'sight', 'color', 'font', 'typography', 'design', 'pattern'],
        'accessibility': ['access', 'barrier', 'navigation', 'wayfinding', 'inclusive', 'universal'],
        'transportation': ['station', 'transport', 'metro', 'underground', 'train', 'transit'],
        'architecture': ['architecture', 'building', 'space', 'design', 'structure'],
        'disability': ['disability', 'disabled', 'deaf', 'hearing', 'neurodivergent', 'cognitive'],
        'information': ['information', 'hierarchy', 'cognitive load', 'data', 'pattern']
    }
    
    # Find which themes are present
    themes = []
    for theme, keywords in theme_keywords.items():
        if any(keyword in content_lower for keyword in keywords):
            themes.append(theme)
    
    # Default to some themes if none found
    if not themes:
        themes = ['visual', 'accessibility', 'architecture']
    
    # Extract specific imagery from content
    imagery = []
    
    # Look for concrete visual descriptions
    visual_patterns = [
        r'flickering departure boards',
        r'color-coded lines',
        r'visual chaos',
        r'wayfinding signs',
        r'visual pattern recognition',
        r'information hierarchy',
        r'sensory soup',
        r'visual breathing room'
    ]
    
    for pattern in visual_patterns:
        if re.search(pattern, content_lower):
            imagery.append(pattern)
    
    # Create image prompts
    image_prompts = []
    
    # Prompt 1: Abstract representation of visual chaos in transportation
    if 'visual' in themes and 'transportation' in themes:
        image_prompts.append(
            "Sophisticated pixel art showing abstract visual chaos in a transportation hub: "
            "flickering departure boards with inconsistent typography, overlapping wayfinding signs, "
            "confusing color-coded lines. Disability perspective: showing how visual clutter creates "
            "barriers for deaf and neurodivergent people. Style: analytical, detailed, 8-bit pixel art "
            "with thoughtful composition."
        )
    
    # Prompt 2: Information hierarchy concept
    if 'information' in themes and 'visual' in themes:
        image_prompts.append(
            "Sophisticated pixel art visualizing information hierarchy failures: "
            "important information (emergency exits) given equal visual weight to trivial details, "
            "cognitive load mismatches, temporal inconsistencies. Disability perspective: "
            "deaf designer's view of how information flows (or doesn't flow) through space. "
            "Style: conceptual, diagrammatic, clean pixel art with clear visual storytelling."
        )
    
    # Prompt 3: Accessibility as co-design process
    if 'accessibility' in themes and 'disability' in themes:
        image_prompts.append(
            "Sophisticated pixel art showing disability co-design process: "
            "disabled consultants working alongside architects and designers from the beginning, "
            "not as afterthought. Visual metaphor of building accessibility into foundations. "
            "Disability perspective: expertise hierarchy being dismantled. "
            "Style: collaborative, hopeful, detailed pixel art with warm colors."
        )
    
    # If we don't have enough prompts, create generic ones
    while len(image_prompts) < 3:
        image_prompts.append(
            f"Sophisticated pixel art about {', '.join(themes[:2])} from disability perspective: "
            f"{metadata.get('agent_perspective', 'deaf designer')} viewpoint. "
            f"Style: analytical, detailed, 8-bit pixel art with disability justice themes."
        )
    
    return image_prompts[:3]  # Return max 3 prompts

def main():
    # Read input
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)
    
    if data.get("status") != "success":
        print(json.dumps({"status": "error", "error": "Input data has error status"}))
        sys.exit(1)
    
    content = data.get("content", "")
    metadata = data.get("metadata", {})
    
    if not content:
        print(json.dumps({"status": "error", "error": "No content provided"}))
        sys.exit(1)
    
    # Extract image prompts
    title = metadata.get("title", "")
    image_prompts = extract_image_prompts_from_content(content, title, metadata)
    
    print(json.dumps({
        "status": "success",
        "image_prompts": image_prompts,
        "metadata": metadata,
        "content_preview": content[:200] + "..." if len(content) > 200 else content
    }))

if __name__ == "__main__":
    main()