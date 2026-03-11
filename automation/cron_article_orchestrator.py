#!/usr/bin/env python3
"""
Cron Job Article Orchestrator for Disability-AI Collective
- Coordinates article topic selection, content generation, and pixel art embedding.
"""

import os
import sys
import json
import re
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
        self.pixel_art_suite = ArticlePixelArtSuite(width=800, height=450, scale=8) # Match article image size

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
        
        # 3. Call LLM to generate article content (this part is critical and needs to be done by the cron job's LLM itself)
        # For now, I will return the prompt so the cron job can use it.
        # The actual LLM call and content writing needs to be part of the agentTurn message
        # Or, if this script is executed directly by the agentTurn, the agentTurn will pass the LLM response back here.
        
        # For demonstration, let's simulate LLM generation here (in a real scenario, this would be an LLM API call)
        # This simulation will be replaced by the actual agentTurn message in the cron job
        simulated_article_content = f"""# {title}

*By {agent_name}*

---

This is a placeholder for the article content that would be generated by the LLM based on the following prompt:

---

```markdown
{prompt}
```

---

*Please replace this placeholder with the actual LLM-generated article content.*"""
        
        # 4. Generate pixel art
        self.logger.info("Generating pixel art...")
        keywords = self.dynamic_generator.analyze_article_content(simulated_article_content) # Re-analyze for keywords
        mood = self.dynamic_generator.determine_mood(simulated_article_content)
        pixel_art_images = self.pixel_art_suite.generate_from_keywords(keywords, mood, agent_name)
        
        pixel_art_filenames = []
        for idx, (img, art_info) in enumerate(pixel_art_images.items()):
            # Save pixel art to assets directory
            img_name = f"{datetime.now().strftime('%Y-%m-%d')}-{re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')}_pixel_art_{idx+1}.png"
            img.save(self.assets_dir / img_name)
            pixel_art_filenames.append(img_name)
            self.logger.success(f"Saved pixel art: {img_name}")
            
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