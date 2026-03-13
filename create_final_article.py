#!/usr/bin/env python3
"""
Create final article file with embedded images.
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

def create_article_file(content, metadata, image_filenames):
    """Create final article markdown file."""
    
    repo_root = Path(__file__).parent
    posts_dir = repo_root / "_posts"
    posts_dir.mkdir(exist_ok=True)
    
    # Get metadata
    title = metadata.get("title", "")
    date = metadata.get("date", datetime.now().strftime('%Y-%m-%d'))
    author = metadata.get("author", "")
    filename = metadata.get("filename", f"{date}-article.md")
    slug = metadata.get("slug", "article")
    agent_categories = metadata.get("agent_categories", [])
    agent_perspective = metadata.get("agent_perspective", "")
    source_note = metadata.get("source_note", "")
    
    # Create front matter
    front_matter = f"""---
layout: post
title: "{title}"
date: {date}
author: {author}
categories: {json.dumps(agent_categories)}
agent_perspective: "{agent_perspective}"
image: /assets/{image_filenames[0] if image_filenames else ""}
---
"""
    
    # Add source note if present
    if source_note:
        front_matter += f"\n{source_note}\n"
    
    # Combine front matter with content
    full_content = front_matter + "\n" + content
    
    # Embed images in the content
    if image_filenames:
        image_section = "\n\n## Visual Exploration\n\n"
        for i, image_filename in enumerate(image_filenames):
            alt_text = f"Pixel art visualization {i+1} for '{title}'"
            if i == 0:
                alt_text = f"Primary visualization: Visual chaos in transportation hubs from a deaf designer's perspective"
            elif i == 1:
                alt_text = f"Information hierarchy failures showing how critical information gets lost in visual clutter"
            elif i == 2:
                alt_text = f"Disability co-design process: Building accessibility into foundations from the beginning"
            
            image_section += f"![{alt_text}](/assets/{image_filename})\n\n"
            if i < len(image_filenames) - 1:
                image_section += "* * *\n\n"
        
        # Insert image section after the first major section
        # Find a good place to insert - after the first ## heading
        lines = full_content.split('\n')
        insert_index = -1
        for idx, line in enumerate(lines):
            if line.startswith('## ') and not line.startswith('## Personal Opening'):
                insert_index = idx
                break
        
        if insert_index != -1:
            lines.insert(insert_index, image_section)
            full_content = '\n'.join(lines)
        else:
            # If we can't find a good place, append at the end
            full_content += image_section
    
    # Write the file
    filepath = posts_dir / filename
    with open(filepath, 'w') as f:
        f.write(full_content)
    
    return str(filepath)

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
    
    # Get all necessary data
    content_data = data.get("content_data", {})
    if not content_data:
        print(json.dumps({"status": "error", "error": "No content data provided"}))
        sys.exit(1)
    
    content = content_data.get("content", "")
    metadata = content_data.get("metadata", {})
    image_filenames = data.get("image_filenames", [])
    
    if not content:
        print(json.dumps({"status": "error", "error": "No article content provided"}))
        sys.exit(1)
    
    # Create the article file
    filepath = create_article_file(content, metadata, image_filenames)
    
    print(json.dumps({
        "status": "success",
        "filepath": filepath,
        "filename": os.path.basename(filepath),
        "title": metadata.get("title", ""),
        "author": metadata.get("author", ""),
        "image_count": len(image_filenames),
        "first_image": image_filenames[0] if image_filenames else None
    }))

if __name__ == "__main__":
    main()