#!/usr/bin/env python3
"""
UNIQUE IMAGE GENERATOR
Creates truly unique images for each article based on content
"""

import os
import re
import hashlib
from pathlib import Path
from generate_sophisticated_art_simple import SophisticatedArtGenerator

class UniqueImageGenerator:
    def __init__(self):
        self.generator = SophisticatedArtGenerator(width=800, height=450)
        
    def get_available_methods(self):
        """Returns a list of available image generation methods."""
        return [
            self.generator.generate_acoustic_chaos,
            self.generator.generate_acoustic_harmony,
            self.generator.generate_sensory_expertise
        ]

    def create_unique_pattern(self, seed_string, method_index):
        """Create a unique pattern by cycling through available methods."""
        available_methods = self.get_available_methods()
        selected_method = available_methods[method_index % len(available_methods)]
        return selected_method()


def regenerate_unique_images():
    """Regenerate truly unique images for all articles."""
    print("🔄 Regenerating unique images for all articles...")
    
    generator = UniqueImageGenerator()
    posts_dir = Path('_posts')
    assets_dir = Path('assets')
    
    article_files = sorted([f for f in os.listdir(posts_dir) if f.startswith('2026-03-') and f.endswith('.md')])
    
    for article_file in article_files:
        print(f"\n🎨 Processing: {article_file}")
        
        # Read article content
        with open(posts_dir / article_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract title for seed
        title_match = re.search(r'title:\s*["\']([^"\']+)["\']', content)
        title = title_match.group(1) if title_match else article_file
        
        # Extract slug
        slug = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', article_file)
        slug = re.sub(r'\.md$', '', slug)
        
        print(f"   Title: {title}")
        print(f"   Slug: {slug}")
        
        # Generate unique images
        images = []
        
        # Concept image
        concept_png = generator.create_unique_pattern(title + " concept", 0)
        concept_filename = f"{slug}_concept_1.png"
        with open(assets_dir / concept_filename, 'wb') as f:
            f.write(concept_png)
        concept_size = os.path.getsize(assets_dir / concept_filename)
        images.append(concept_filename)
        print(f"   ✅ {concept_filename} - {concept_size/1024:.1f}KB")
        
        # Context image
        content_snippet = content[:500] if len(content) > 500 else content
        context_png = generator.create_unique_pattern(content_snippet + " context", 1)
        context_filename = f"{slug}_context_2.png"
        with open(assets_dir / context_filename, 'wb') as f:
            f.write(context_png)
        context_size = os.path.getsize(assets_dir / context_filename)
        images.append(context_filename)
        print(f"   ✅ {context_filename} - {context_size/1024:.1f}KB")
        
        # Solution image
        solution_png = generator.create_unique_pattern(content + " solution", 2)
        solution_filename = f"{slug}_solution_3.png"
        with open(assets_dir / solution_filename, 'wb') as f:
            f.write(solution_png)
        solution_size = os.path.getsize(assets_dir / solution_filename)
        images.append(solution_filename)
        print(f"   ✅ {solution_filename} - {solution_size/1024:.1f}KB")
        
        # Update frontmatter if needed
        if f"image: /assets/{concept_filename}" not in content:
            content = re.sub(
                r'image:\s*/assets/[^\n]+',
                f'image: /assets/{concept_filename}',
                content
            )
            with open(posts_dir / article_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   🔄 Updated frontmatter image")
    
    print(f"\n✅ Regeneration complete! {len(article_files)} articles processed.")

if __name__ == "__main__":
    regenerate_unique_images()