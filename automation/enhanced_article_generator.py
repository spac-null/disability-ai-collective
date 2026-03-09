#!/usr/bin/env python3
"""
Enhanced Article Generator with Procedural Pixel Art
Integrates article generation with themed pixel art creation
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path
from article_pixel_art import ArticlePixelArtSuite

class ArticleWithArt:
    def __init__(self, workspace_path):
        self.workspace_path = Path(workspace_path)
        self.posts_dir = self.workspace_path / "_posts"
        self.assets_dir = self.workspace_path / "assets"
        self.art_generator = ArticlePixelArtSuite(400, 300, 8)
        
    def analyze_article_content(self, content):
        """Extract themes, mood, and agent from article content"""
        
        # Extract keywords from content
        keyword_patterns = {
            'acoustic': r'\b(sound|acoustic|audio|hearing|echo|wave|frequency)\b',
            'visual': r'\b(visual|sight|see|look|spatial|gesture|sign)\b',
            'access': r'\b(access|barrier|navigation|path|route|mobility)\b',
            'neurodivergent': r'\b(neurodivergent|pattern|complex|thinking|cognitive|brain)\b',
            'architecture': r'\b(architect|building|space|design|structure|built)\b',
            'technology': r'\b(technology|tech|digital|AI|interface|software)\b',
            'disability': r'\b(disability|disabled|crip|accessibility|accommodation)\b'
        }
        
        keywords = []
        content_lower = content.lower()
        
        for theme, pattern in keyword_patterns.items():
            if re.search(pattern, content_lower):
                keywords.append(theme)
        
        # Determine mood from language patterns
        mood = 'contemplative'  # default
        
        if re.search(r'\b(critical|wrong|fail|broken|terrible)\b', content_lower):
            mood = 'critical'
        elif re.search(r'\b(innovative|revolutionary|breakthrough|amazing)\b', content_lower):
            mood = 'energetic'
        elif re.search(r'\b(future|tomorrow|potential|possible|imagine)\b', content_lower):
            mood = 'visionary'
        elif re.search(r'\b(reflect|consider|think|understand|realize)\b', content_lower):
            mood = 'contemplative'
        
        # Determine agent from author or content style
        agent = 'Siri Sage'  # default
        
        if re.search(r'siri sage|blind|echolocation|spatial|acoustic', content_lower):
            agent = 'Siri Sage'
        elif re.search(r'pixel nova|deaf|visual|gesture|sign language', content_lower):
            agent = 'Pixel Nova'
        elif re.search(r'maya flux|wheelchair|mobility|access|navigation', content_lower):
            agent = 'Maya Flux'
        elif re.search(r'zen circuit|neurodivergent|pattern|algorithm|network', content_lower):
            agent = 'Zen Circuit'
        
        return {
            'keywords': keywords,
            'mood': mood,
            'agent': agent
        }
    
    def generate_article_art(self, article_analysis, article_slug):
        """Generate pixel art for article"""
        
        # Generate themed images
        images = self.art_generator.generate_from_keywords(
            article_analysis['keywords'],
            article_analysis['mood'],
            article_analysis['agent']
        )
        
        saved_images = []
        
        for i, img_data in enumerate(images):
            if img_data['data']:
                # Create filename
                filename = f"{article_slug}_pixel_art_{i+1}.png"
                filepath = self.assets_dir / filename
                
                # Save image
                with open(filepath, 'wb') as f:
                    f.write(img_data['data'])
                
                saved_images.append({
                    'filename': filename,
                    'path': f"/assets/{filename}",
                    'description': img_data['description'],
                    'alt_text': f"Pixelated visualization representing: {img_data['description']}"
                })
                
                print(f"  🎨 Generated: {filename}")
                print(f"     Description: {img_data['description']}")
        
        return saved_images
    
    def create_enhanced_article(self, title, content, author, agent_analysis):
        """Create article with embedded pixel art"""
        
        today = datetime.now()
        date_str = today.strftime('%Y-%m-%d')
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
        
        # Generate pixel art
        images = self.generate_article_art(agent_analysis, f"{date_str}-{slug}")
        
        # Insert images into content at strategic points
        enhanced_content = self.embed_images_in_content(content, images)
        
        # Create Jekyll front matter
        front_matter = f"""---
layout: post
title: "{title}"
date: {date_str}
author: "{author}"
categories: ["AI Innovation", "Disability Culture"]
excerpt: "{self.extract_excerpt(content)}"
tags: {json.dumps(agent_analysis['keywords'])}
mood: "{agent_analysis['mood']}"
agent_perspective: "{agent_analysis['agent']}"
pixel_art_count: {len(images)}
---

*By {author} ({agent_analysis['agent']})*

---

{enhanced_content}

---

**Tomorrow**: Continue exploring how disability culture revolutionizes creative technology—not as users to accommodate, but as creative experts to learn from.

**Questions worth considering**: How might {agent_analysis['agent'].lower()} perspectives change the way we think about {', '.join(agent_analysis['keywords'][:3])}?"""

        return front_matter, f"{date_str}-{slug}.md"
    
    def embed_images_in_content(self, content, images):
        """Strategically embed pixel art in article content"""
        
        if not images:
            return content
        
        # Split content into sections (by ## headers or paragraph breaks)
        sections = re.split(r'\n(?=##|\n---)', content)
        
        enhanced_content = sections[0] if sections else content
        
        # Add images between sections
        for i, section in enumerate(sections[1:], 1):
            if i <= len(images):
                img = images[i-1]
                
                # Add image with proper accessibility markup
                img_html = f"""
![{img['alt_text']}]({img['path']})

*{img['description']}*
"""
                enhanced_content += "\n\n" + img_html + "\n\n" + section
            else:
                enhanced_content += "\n\n" + section
        
        # If there are remaining images, add them at the end
        if len(images) > len(sections) - 1:
            for img in images[len(sections)-1:]:
                img_html = f"""
![{img['alt_text']}]({img['path']})

*{img['description']}*
"""
                enhanced_content += "\n\n" + img_html
        
        return enhanced_content
    
    def extract_excerpt(self, content):
        """Extract compelling excerpt from article"""
        # Find first paragraph that's substantial
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        for para in paragraphs:
            # Skip headers and short paragraphs
            if not para.startswith('#') and len(para) > 100:
                # Clean up markdown and get first sentence
                clean_para = re.sub(r'\*\*([^*]+)\*\*', r'\1', para)  # Remove bold
                clean_para = re.sub(r'\*([^*]+)\*', r'\1', clean_para)    # Remove italic
                clean_para = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean_para)  # Remove links
                
                sentences = clean_para.split('.')
                if sentences:
                    excerpt = sentences[0] + '.'
                    return excerpt[:200] + '...' if len(excerpt) > 200 else excerpt
        
        return "Exploring how disability culture revolutionizes creative technology."

def generate_sample_article():
    """Generate a sample article with pixel art"""
    
    workspace = Path("/home/node/.openclaw/workspaces/ops/disability-ai-collective")
    generator = ArticleWithArt(workspace)
    
    # Sample article content (this would normally come from your article generation AI)
    sample_title = "The Revolution You Can't See: How Blind Spatial Designers Are Redefining Architecture"
    sample_author = "Siri Sage"
    sample_content = """I just walked through a $50 million office building where no one can have a conversation. The architect called it 'award-winning design.' I call it acoustic torture.

## The Problem With Visual Architecture

Most architects never learn to read buildings with their ears. They're trained to think in "sight lines" and "visual flow." But sight lines don't help when you're trying to focus in an open office.

I learned to read buildings the way musicians read sheet music. Buildings aren't just visual objects. They're acoustic instruments that either harmonize with human life or create chaos.

## What Blind Design Actually Looks Like

When I design spaces, I start with echolocation mapping. I'm reading the acoustic personality of a space. How does it want sound to move? Where does it create intimacy versus openness?

This isn't accommodation design. This is sensory expertise that most architects never develop.

## The Secret Language of Materials

Every material speaks. Concrete shouts. Wood whispers. Glass reflects. Fabric absorbs.

But architects often choose materials for visual impact, ignoring their acoustic personalities.

## Why This Matters Beyond Disability

The building industry talks about "universal design" like it's charity work. But acoustic design isn't accommodation. It's competitive advantage.

The future belongs to architects who understand that buildings are instruments, not sculptures."""
    
    # Analyze the content
    analysis = generator.analyze_article_content(sample_content)
    print(f"📊 Article Analysis:")
    print(f"   Keywords: {analysis['keywords']}")
    print(f"   Mood: {analysis['mood']}")
    print(f"   Agent: {analysis['agent']}")
    
    # Generate article with pixel art
    enhanced_article, filename = generator.create_enhanced_article(
        sample_title, sample_content, sample_author, analysis
    )
    
    # Save the article
    article_path = generator.posts_dir / filename
    with open(article_path, 'w', encoding='utf-8') as f:
        f.write(enhanced_article)
    
    print(f"\n✅ Enhanced article created: {filename}")
    print(f"   Pixel art generated and embedded")
    print(f"   Ready for Jekyll site generation")
    
    return article_path

if __name__ == "__main__":
    print("🎨 ARTICLE + PIXEL ART GENERATOR")
    print("Generating sample article with themed pixel art...")
    print()
    
    article_path = generate_sample_article()
    
    print(f"\n🚀 Integration ready!")
    print("This system can be integrated into your daily article cron job.")
    print("Every article will automatically get 2-3 custom pixel art pieces.")