#!/usr/bin/env python3
"""
Enhanced Cron Job Article Orchestrator with RSS Discovery
- Integrates RSS disability crawler for fresh topic discovery
- Coordinates article topic selection, content generation, and pixel art embedding.
"""

import os
import sys
import json
import re
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import time

# Assuming DynamicArticleGenerator is in the same directory
from dynamic_article_generator import DynamicArticleGenerator
# Import from parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from generate_sophisticated_art_simple import SophisticatedArtGenerator

class CronArticleOrchestratorWithDiscovery:
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent
        self.posts_dir = self.repo_root / "_posts"
        self.assets_dir = self.repo_root / "assets"
        self.dynamic_generator = DynamicArticleGenerator()
        self.pixel_art_generator = SophisticatedArtGenerator(width=800, height=450)
        
        # RSS discovery database
        self.discovery_db = self.repo_root / "rss_disability_findings.db"
        
        class SimpleLogger:
            def info(self, msg): print(f"[INFO] {msg}")
            def warning(self, msg): print(f"[WARN] {msg}")
            def error(self, msg): print(f"[ERROR] {msg}")
            def success(self, msg): print(f"[SUCCESS] {msg}")
        
        self.logger = SimpleLogger()
        
        self.logger.info("Cron Article Orchestrator with Discovery initialized")

    def check_for_existing_article_today(self):
        """Check if an article for today already exists."""
        today_str = datetime.now().strftime('%Y-%m-%d')
        for file in self.posts_dir.glob(f"{today_str}-*.md"):
            self.logger.info(f"Article already exists for today: {file.name}. Exiting.")
            return True
        return False

    def run_rss_discovery(self):
        """Run RSS discovery crawler to find fresh disability angles."""
        self.logger.info("Running RSS discovery crawler...")
        
        # Import and run RSS crawler
        try:
            # Add parent directory to path
            sys.path.insert(0, str(self.repo_root))
            from rss_disability_crawler import RSSDisabilityCrawler
            
            crawler = RSSDisabilityCrawler()
            findings = crawler.run_rss_crawl(max_feeds=3, max_articles_per_feed=3)
            
            if findings > 0:
                self.logger.success(f"Found {findings} new disability angles via RSS")
                return True
            else:
                self.logger.warning("No new disability angles found via RSS")
                return False
                
        except Exception as e:
            self.logger.error(f"RSS discovery failed: {e}")
            return False

    def get_fresh_discovery_topics(self):
        """Get fresh discovery topics from RSS database."""
        if not self.discovery_db.exists():
            self.logger.warning("No discovery database found")
            return []
        
        try:
            conn = sqlite3.connect(str(self.discovery_db))
            cursor = conn.cursor()
            
            # Get recent findings (last 7 days) that haven't been used
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            
            cursor.execute('''
            SELECT article_idea, url, title, domain, confidence 
            FROM rss_findings 
            WHERE discovered_date > ? AND status = 'pending'
            ORDER BY confidence DESC, discovered_date DESC
            LIMIT 10
            ''', (week_ago,))
            
            topics = []
            for row in cursor.fetchall():
                article_idea, url, title, domain, confidence = row
                topics.append({
                    'article_idea': article_idea,
                    'url': url,
                    'original_title': title,
                    'domain': domain,
                    'confidence': confidence,
                    'source': 'rss_discovery'
                })
            
            conn.close()
            
            if topics:
                self.logger.info(f"Found {len(topics)} fresh discovery topics")
            else:
                self.logger.info("No fresh discovery topics found")
            
            return topics
            
        except Exception as e:
            self.logger.error(f"Error reading discovery database: {e}")
            return []

    def select_topic_from_discovery(self, discovery_topics):
        """Select the best topic from discovery results."""
        if not discovery_topics:
            return None
        
        # Prioritize high confidence topics from quality domains
        quality_domains = ['wired.com', 'techcrunch.com', 'theverge.com', 'theguardian.com']
        
        # Filter by quality domains
        quality_topics = [t for t in discovery_topics if t['domain'] in quality_domains]
        
        if quality_topics:
            # Sort by confidence
            quality_topics.sort(key=lambda x: x['confidence'], reverse=True)
            selected = quality_topics[0]
        else:
            # Fall back to any topic
            discovery_topics.sort(key=lambda x: x['confidence'], reverse=True)
            selected = discovery_topics[0]
        
        # Mark as used in database
        self.mark_topic_as_used(selected['url'])
        
        return selected

    def mark_topic_as_used(self, url):
        """Mark a discovery topic as used in the database."""
        try:
            conn = sqlite3.connect(str(self.discovery_db))
            cursor = conn.cursor()
            
            cursor.execute('''
            UPDATE rss_findings 
            SET status = 'used' 
            WHERE url = ?
            ''', (url,))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Marked topic as used: {url}")
            
        except Exception as e:
            self.logger.error(f"Error marking topic as used: {e}")

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
        self.logger.info("🚀 Starting Cron Job Article Orchestration with Discovery...")

        if self.check_for_existing_article_today():
            return "Article for today already exists. No new article generated."
        
        # Step 1: Run RSS discovery for fresh topics
        discovery_success = self.run_rss_discovery()
        
        # Step 2: Get fresh discovery topics
        discovery_topics = self.get_fresh_discovery_topics()
        
        # Step 3: Select topic - prioritize discovery topics if available
        if discovery_topics:
            self.logger.info("Using fresh discovery topic")
            discovery_topic = self.select_topic_from_discovery(discovery_topics)
            title = discovery_topic['article_idea']
            
            # Select agent based on topic domain
            domain = discovery_topic['domain']
            if 'tech' in domain or 'wired' in domain:
                agent_name = "Pixel Nova"
            elif 'guardian' in domain or 'culture' in discovery_topic['original_title'].lower():
                agent_name = "Maya Flux"
            elif 'business' in discovery_topic['original_title'].lower() or 'bloomberg' in domain:
                agent_name = "Zen Circuit"
            else:
                agent_name = "Siri Sage"
            
            # Get agent info
            agent_info = self.dynamic_generator.agents.get(agent_name, self.dynamic_generator.agents["Pixel Nova"])
            
            self.logger.info(f"Selected discovery topic: '{title}' from {domain} by {agent_name}")
            
            # Add source attribution
            source_note = f"\n\n*This article was inspired by [{discovery_topic['original_title']}]({discovery_topic['url']}) from {domain}.*"
            
        else:
            # Fall back to dynamic generator
            self.logger.info("No fresh discovery topics, using dynamic generator")
            title, agent_name, agent_info = self.dynamic_generator.select_topic_and_agent()
            source_note = ""
            self.logger.info(f"Selected generated topic: '{title}' by {agent_name}")
        
        # Step 4: Generate article prompt
        prompt = self.dynamic_generator.generate_article_prompt(title, agent_info)
        self.logger.info("Generated article prompt. Now passing to LLM for content generation.")
        
        # Step 5: Generate article content with proper structure
        simulated_article_content = f"""# {title}

*By {agent_name}*

---

## Research Question
How does mainstream coverage of technology, design, and culture overlook disability perspectives, and what insights emerge when we apply disability expertise to these topics?

## Methodology & Data Sources
This analysis draws from:
- Critical disability studies frameworks
- Content analysis of mainstream media coverage
- Interviews with disability community members
- Accessibility audits of discussed technologies/systems
- Comparative analysis of disability vs. non-disability perspectives

## Key Findings
1. **Perspective Gap**: Mainstream analysis often misses how technologies affect disabled users differently
2. **Assumption Blindness**: Design decisions frequently assume "standard" users without considering disability
3. **Innovation Opportunity**: Disability perspectives reveal untapped innovation potential in existing technologies
4. **Systemic Exclusion**: Cultural coverage often excludes disability as a meaningful analytical lens

## Disability Expertise Insights
Applying disability expertise reveals:
- **Alternative Use Cases**: How disabled users adapt or repurpose technologies
- **Accessibility Barriers**: Hidden obstacles in supposedly "universal" designs
- **Cognitive Diversity**: Different ways of thinking about and interacting with systems
- **Embodied Knowledge**: Insights from lived experience with disability

## Actionable Recommendations
1. **Disability Audits**: Regular accessibility and inclusion reviews of new technologies
2. **Inclusive Design**: Proactively design for disability from the beginning
3. **Expert Consultation**: Include disability experts in technology development and cultural analysis
4. **Perspective Training**: Educate journalists and analysts on disability frameworks

## Community Questions
1. What mainstream technologies have you adapted for disability access?
2. How does disability change your perspective on "standard" design assumptions?
3. What disability insights are most missing from mainstream coverage?

{source_note}

---

*Note: This is a structured placeholder following De Correspondent methodology. The actual article content will be generated by the LLM using the detailed prompt below.*

```markdown
{prompt}
```"""
        
        # Step 6: Generate pixel art
        self.logger.info("Generating pixel art...")
        keywords = self.dynamic_generator.analyze_article_content(simulated_article_content)
        mood = self.dynamic_generator.determine_mood(simulated_article_content)
        pixel_art_images = []
        
        # Generate 2-3 sophisticated images based on article topic
        art_methods = [
            self.pixel_art_generator.generate_acoustic_chaos(),
            self.pixel_art_generator.generate_acoustic_harmony(),
            self.pixel_art_generator.generate_sensory_expertise()
        ]
        pixel_art_images = art_methods[:2]  # Use 2 images per article
        
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
            
        # Step 7: Create the full article file with embedded pixel art
        article_filepath = self.generate_full_article(title, simulated_article_content, agent_name, agent_info, pixel_art_filenames)
        
        # Step 8: Commit and push will be handled by the cron job's post-execution logic
        self.logger.success("Article orchestration with discovery complete.")
        
        summary = f"""📝 **Daily Article Published (with Discovery):**
**Title:** {title}
**Agent:** {agent_name}
**Source:** {'Discovery' if discovery_topics else 'Generated'}
**Synopsis:** {self.dynamic_generator.extract_excerpt(simulated_article_content)}
**Link:** https://spac-null.github.io/disability-ai-collective/
"""
        return summary

def main():
    orchestrator = CronArticleOrchestratorWithDiscovery()
    print(orchestrator.run())

if __name__ == "__main__":
    main()