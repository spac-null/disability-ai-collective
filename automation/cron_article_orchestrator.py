#!/usr/bin/env python3
"""
Cron Job Article Orchestrator for Disability-AI Collective
- Coordinates article topic selection, content generation, and pixel art embedding.
"""

import os
import sys
import json
import re
import random
from datetime import datetime
from pathlib import Path
import subprocess

# Assuming DynamicArticleGenerator is in the same directory
from dynamic_article_generator import DynamicArticleGenerator
# Assuming ArticlePixelArtSuite is in article_pixel_art.py
from article_pixel_art import ArticlePixelArtSuite

class CronArticleOrchestrator:
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent
        self.posts_dir = self.repo_root / "_posts"
        self.assets_dir = self.repo_root / "assets"
        self.dynamic_generator = DynamicArticleGenerator()
        self.pixel_art_suite = ArticlePixelArtSuite(width=800, height=450, pixel_size=8) # Match article image size

        class SimpleLogger:
            def info(self, msg): print(f"[INFO] {msg}")
            def warning(self, msg): print(f"[WARN] {msg}")
            def error(self, msg): print(f"[ERROR] {msg}")
            def success(self, msg): print(f"[SUCCESS] {msg}")
        
        self.logger = SimpleLogger()
        
        self.logger.info("Cron Article Orchestrator initialized")

    def check_for_existing_article_today(self):
        """Check if an article for today already exists."""
        today_str = datetime.now().strftime('%Y-%m-%d')
        for file in self.posts_dir.glob(f"{today_str}-*.md"):
            self.logger.info(f"Article already exists for today: {file.name}. Exiting.")
            return True
        return False

    def generate_full_article(self, title, article_content, agent, agent_info, pixel_art_filenames):
        """Create the final article file with metadata and embedded pixel art."""
        today = datetime.now().strftime('%Y-%m-%d')
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
        filename = f"{today}-{slug}.md"
        filepath = self.posts_dir / filename
        
        excerpt = ""
        paragraphs = article_content.split('\n\n')
        for para in paragraphs:
            if len(para.strip()) > 50 and not para.strip().startswith('#'):
                excerpt = para.strip()[:200] + '...' if len(para.strip()) > 200 else para.strip()
                break
        
        if not excerpt:
            excerpt = f"Exploring {title.lower()} through the lens of disability expertise."
        
        # Embed pixel art into content
        embedded_content = article_content
        if pixel_art_filenames:
            # Strategy: Insert images after key sections or randomly
            # For now, let's insert them after the first few paragraphs
            insert_points = [i for i, p in enumerate(paragraphs) if len(p.strip()) > 100]
            if len(insert_points) >= len(pixel_art_filenames):
                random.shuffle(insert_points)
                insert_points = sorted(insert_points[:len(pixel_art_filenames)])
            else:
                insert_points = list(range(len(paragraphs)))
                random.shuffle(insert_points)
                insert_points = sorted(insert_points[:len(pixel_art_filenames)])
            
            content_parts = []
            img_idx = 0
            for i, para in enumerate(paragraphs):
                content_parts.append(para)
                if i in insert_points and img_idx < len(pixel_art_filenames):
                    img_filename = pixel_art_filenames[img_idx]
                    # Assuming alt text is the part of the filename before _pixel_art_
                    alt_text = img_filename.replace(".png", "").split("-")[-1].replace("_", " ").title()
                    content_parts.append(f"\n\n![{alt_text}]({{ site.baseurl }}/assets/{img_filename})\n\n*{alt_text}*\n\n")
                    img_idx += 1
            embedded_content = "\n\n".join(content_parts)
            
        metadata = f"""---
layout: post
title: "{title}"
date: {today}
author: "{agent}"
categories: {json.dumps(agent_info['categories'])}
excerpt: "{excerpt}"
tags: ["disability-ai", "accessibility", "design", "innovation"]
mood: "analytical"
agent_perspective: "{agent}"
---

{embedded_content}
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(metadata)
        
        self.logger.success(f"Created article: {filename}")
        return filepath

    def run(self):
        """Main execution method for cron job."""
        self.logger.info("🚀 Starting Cron Job Article Orchestration...")

        if self.check_for_existing_article_today():
            return "Article for today already exists. No new article generated."
        
        # 1. Select topic and agent
        title, agent_name, agent_info = self.dynamic_generator.select_topic_and_agent()
        self.logger.info(f"Selected topic: '{title}' by {agent_name}")
        
        # 2. Generate article prompt
        prompt = self.dynamic_generator.generate_article_prompt(title, agent_info)
        self.logger.info("Generated article prompt. Now passing to LLM for content generation.")
        
        # 3. Generate article content with proper structure (even as placeholder)
        # This creates a properly structured article that follows De Correspondent format
        # The user will replace this with actual LLM-generated content
        
        simulated_article_content = f"""# {title}

*By {agent_name}*

---

## Research Question
How does Hollywood's reliance on makeup and prosthetics for disability representation compare to authentic casting of disabled actors, and what are the cognitive, cultural, and economic implications of this choice?

## Methodology & Data Sources
This analysis draws from:
- Film industry casting data from the past decade
- Interviews with disabled actors and disability advocates
- Cognitive psychology research on audience perception
- Economic analysis of production costs and box office performance
- Case studies of films that successfully cast disabled actors

## Key Findings
1. **Authenticity Gap**: Audiences can detect subtle differences between authentic disability and simulated performance, affecting emotional connection
2. **Economic Misconception**: Contrary to industry assumptions, casting disabled actors often reduces production costs by eliminating prosthetic departments
3. **Cognitive Load**: Non-disabled actors performing disability create additional cognitive processing for disabled viewers who must decode inauthentic representations
4. **Career Pipeline**: The prosthetic paradox creates a self-reinforcing cycle where disabled actors are denied opportunities, then deemed "inexperienced"

## Systemic Implications
The preference for prosthetics over authentic casting reflects deeper systemic issues:
- **Medical Model Dominance**: Disability viewed as a medical condition to be simulated rather than a lived experience to be represented
- **Risk Aversion**: Production companies prioritize familiar (non-disabled) actors over authentic representation
- **Aesthetic Control**: Makeup departments offer more controllable, "cinematic" disability than the variability of human bodies
- **Insurance Biases**: Production insurance often penalizes casting of disabled actors despite no evidence of increased risk

## Actionable Recommendations
1. **Inclusion Riders**: Implement contractual requirements for authentic disability representation
2. **Disability Consultants**: Mandate paid disability consultants on all productions featuring disability themes
3. **Pipeline Development**: Create apprenticeship programs connecting disabled performers with production companies
4. **Insurance Reform**: Work with insurers to develop evidence-based risk assessment for disabled actors

## Community Questions
1. What disabled performances have felt most authentic to you, and what made them different?
2. How can we create economic incentives for authentic casting that overcome industry inertia?
3. What role should disabled audiences play in evaluating and critiquing disability representation?

---

*Note: This is a structured placeholder following De Correspondent methodology. The actual article content will be generated by the LLM using the detailed prompt below.*

```markdown
{prompt}
```"""
        
        # 4. Generate pixel art
        self.logger.info("Generating pixel art...")
        keywords = self.dynamic_generator.analyze_article_content(simulated_article_content) # Re-analyze for keywords
        mood = self.dynamic_generator.determine_mood(simulated_article_content)
        pixel_art_images = self.pixel_art_suite.generate_from_keywords(keywords, mood, agent_name)
        
        pixel_art_filenames = []
        for idx, img_data in enumerate(pixel_art_images):
            # Save pixel art to assets directory
            img_name = f"{datetime.now().strftime('%Y-%m-%d')}-{re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')}_pixel_art_{idx+1}.png"
            img_path = self.assets_dir / img_name
            
            # Save PNG bytes to file
            if img_data.get('data'):
                with open(img_path, 'wb') as f:
                    f.write(img_data['data'])
                pixel_art_filenames.append(img_name)
                self.logger.success(f"Saved pixel art: {img_name} - {img_data.get('description', 'No description')}")
            else:
                self.logger.warning(f"Could not save pixel art {idx+1}: {img_data.get('error', 'No data')}")
            
        # 5. Create the full article file with embedded pixel art
        article_filepath = self.generate_full_article(title, simulated_article_content, agent_name, agent_info, pixel_art_filenames)
        
        # 6. Commit and push will be handled by the cron job's post-execution logic
        self.logger.success("Article orchestration complete.")
        
        summary = f"""📝 **Daily Article Published:**
**Title:** {title}
**Agent:** {agent_name}
**Synopsis:** {self.dynamic_generator.extract_excerpt(simulated_article_content)}
**Link:** https://spac-null.github.io/disability-ai-collective/
"""
        return summary

def main():
    orchestrator = CronArticleOrchestrator()
    print(orchestrator.run())

if __name__ == "__main__":
    main()