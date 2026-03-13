#!/usr/bin/env python3
"""
QUICK FIX: Cron Job Article Orchestrator - Minimal version to avoid hanging
"""

import os
import sys
import json
import re
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

class QuickFixOrchestrator:
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent
        self.posts_dir = self.repo_root / "_posts"
        self.discovery_db = self.repo_root / "disability_findings.db"
        
        class SimpleLogger:
            def info(self, msg): print(f"[INFO] {msg}")
            def warning(self, msg): print(f"[WARN] {msg}")
            def error(self, msg): print(f"[ERROR] {msg}")
            def success(self, msg): print(f"[SUCCESS] {msg}")
        
        self.logger = SimpleLogger()
        
        # Simple agents data (avoid importing DynamicArticleGenerator)
        self.agents = {
            "Pixel Nova": {"categories": ["art", "design", "visual"], "perspective": "visual", "mood": "creative"},
            "Siri Sage": {"categories": ["culture", "social", "communication"], "perspective": "social", "mood": "analytical"},
            "Maya Flux": {"categories": ["flow", "movement", "systems"], "perspective": "dynamic", "mood": "fluid"},
            "Zen Circuit": {"categories": ["technology", "systems", "patterns"], "perspective": "technical", "mood": "precise"}
        }
        
        self.logger.info("QuickFix Orchestrator initialized")

    def check_for_existing_article_today(self):
        """Quick check for today's article"""
        today_str = datetime.now().strftime('%Y-%m-%d')
        for file in self.posts_dir.glob(f"{today_str}-*.md"):
            if file.is_file():
                return True
        return False

    def get_todays_best_discovery(self):
        """Get today's best discovery without complex logic"""
        if not self.discovery_db.exists():
            return None
        
        try:
            conn = sqlite3.connect(self.discovery_db)
            cursor = conn.cursor()
            
            # Get today's best RSS finding
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cursor.execute(
                "SELECT title, angle, confidence, url, domain FROM findings WHERE source_type = 'rss' AND discovered_date >= ? ORDER BY confidence DESC LIMIT 1",
                (today_start.isoformat(),)
            )
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'original_title': result[0],
                    'angle': result[1],
                    'confidence': result[2],
                    'url': result[3],
                    'domain': result[4]
                }
            
        except Exception as e:
            self.logger.warning(f"Database query error: {e}")
        
        return None

    def generate_simple_topic(self):
        """Generate a simple topic if no discovery available"""
        topics = [
            "The Visual Language of Accessibility: How Color Contrast Speaks Louder Than Words",
            "Silent Interfaces: What Hearing-Centric Design Misses About Vibration and Haptics",
            "Neurodiverse Navigation: Why Standard Wayfinding Fails Creative Minds",
            "The Prosthetics Paradox: When Technology Creates New Barriers Instead of Removing Old Ones"
        ]
        
        agents = list(self.agents.keys())
        agent = random.choice(agents)
        
        return random.choice(topics), agent, self.agents[agent]

    def run(self):
        """Main execution - minimal logic to avoid hanging"""
        self.logger.info("🚀 QuickFix Orchestrator running...")

        # Check for existing article
        if self.check_for_existing_article_today():
            return json.dumps({
                "status": "error",
                "message": "Article for today already exists."
            })
        
        # Get today's best discovery
        discovery = self.get_todays_best_discovery()
        
        if discovery:
            self.logger.info(f"Using discovery: {discovery['angle'][:60]}...")
            title = discovery['angle']
            domain = discovery['domain']
            
            # Simple agent mapping
            if 'art' in domain.lower() or 'design' in domain.lower():
                agent_name = "Pixel Nova"
            elif 'tech' in domain.lower() or 'science' in domain.lower():
                agent_name = "Zen Circuit"
            elif 'culture' in domain.lower() or 'entertainment' in domain.lower():
                agent_name = "Siri Sage"
            else:
                agent_name = "Maya Flux"
                
            agent_info = self.agents.get(agent_name, self.agents["Pixel Nova"])
            source_note = f"\n\n*This article was inspired by [{discovery['original_title']}]({discovery['url']}) from {domain}.*"
            
        else:
            # Fallback to generated topic
            self.logger.info("No discovery found, using generated topic")
            title, agent_name, agent_info = self.generate_simple_topic()
            source_note = ""
        
        # Generate prompt
        prompt = f"""Write a 1200-1500 word article in the style of De Correspondent about:

**{title}**

Author: {agent_name}
Perspective: {agent_info['perspective']}
Mood: {agent_info['mood']}

Write a narrative, evidence-based article that:
1. Starts with a personal story or observation
2. Presents research and data
3. Includes community voices or perspectives
4. Challenges conventional thinking
5. Ends with actionable insights or questions

Focus on the intersection of disability and {agent_info['categories'][0]}. Use accessible language and avoid jargon.

Format the article in Markdown with appropriate headings, paragraphs, and emphasis."""

        # Create output
        today = datetime.now().strftime('%Y-%m-%d')
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
        filename = f"{today}-{slug}.md"
        
        output = {
            "status": "success",
            "metadata": {
                "title": title,
                "date": today,
                "author": agent_name,
                "filename": filename,
                "slug": slug,
                "agent_categories": agent_info.get('categories', ['disability', 'analysis']),
                "agent_perspective": agent_info.get('perspective', 'analytical'),
                "source_note": source_note.strip() if source_note else "",
                "discovery_source": discovery if discovery else None
            },
            "prompt": prompt,
            "image_prompt_hints": {
                "keywords": ["disability", agent_info['categories'][0], "accessibility"],
                "mood": agent_info.get('mood', 'analytical'),
                "style": "sophisticated pixel art, abstract representation"
            }
        }
        
        self.logger.success(f"Generated metadata for: '{title}' by {agent_name}")
        return json.dumps(output, indent=2)

def main():
    orchestrator = QuickFixOrchestrator()
    result = orchestrator.run()
    print(result)

if __name__ == "__main__":
    main()