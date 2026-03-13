#!/usr/bin/env python3
"""
Enhanced Cron Job Article Orchestrator with RSS Discovery - V2
- Outputs structured metadata and prompts for full automation
- No article creation - just topic selection and prompt generation
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

class CronArticleOrchestratorWithDiscoveryV2:
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent
        self.posts_dir = self.repo_root / "_posts"
        self.assets_dir = self.repo_root / "assets"
        self.dynamic_generator = DynamicArticleGenerator()
        
        # RSS discovery database
        self.discovery_db = self.repo_root / "rss_disability_findings.db"
        
        class SimpleLogger:
            def info(self, msg): print(f"[INFO] {msg}")
            def warning(self, msg): print(f"[WARN] {msg}")
            def error(self, msg): print(f"[ERROR] {msg}")
            def success(self, msg): print(f"[SUCCESS] {msg}")
        
        self.logger = SimpleLogger()
        
        self.logger.info("Cron Article Orchestrator with Discovery V2 initialized")

    def check_for_existing_article_today(self):
        """Check if an article for today already exists."""
        today_str = datetime.now().strftime('%Y-%m-%d')
        for file in self.posts_dir.glob(f"{today_str}-*.md"):
            if file.is_file():
                self.logger.warning(f"Article for today already exists: {file.name}")
                return True
        return False

    def run_rss_discovery(self):
        """Run RSS discovery crawler if not already run today."""
        # Check if discovery was already run today
        if self.discovery_db.exists():
            conn = sqlite3.connect(self.discovery_db)
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT MAX(timestamp) FROM findings")
                result = cursor.fetchone()
                if result and result[0]:
                    last_run = datetime.fromisoformat(result[0].replace('Z', '+00:00'))
                    if last_run.date() == datetime.now().date():
                        self.logger.info("RSS discovery already run today")
                        return True
            except sqlite3.OperationalError:
                pass  # Table might not exist yet
            finally:
                conn.close()
        
        # Run discovery
        self.logger.info("Running RSS discovery crawler...")
        try:
            result = subprocess.run(
                [sys.executable, str(self.repo_root / "rss_disability_crawler.py")],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                self.logger.success("RSS discovery completed successfully")
                return True
            else:
                self.logger.error(f"RSS discovery failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            self.logger.error("RSS discovery timed out")
            return False
        except Exception as e:
            self.logger.error(f"RSS discovery error: {e}")
            return False

    def get_fresh_discovery_topics(self):
        """Get fresh discovery topics from today's RSS crawl."""
        if not self.discovery_db.exists():
            return []
        
        conn = sqlite3.connect(self.discovery_db)
        cursor = conn.cursor()
        
        try:
            # Get topics from today
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cursor.execute(
                "SELECT title, angle, confidence, url, domain FROM findings WHERE timestamp >= ? ORDER BY confidence DESC LIMIT 10",
                (today_start.isoformat(),)
            )
            topics = []
            for row in cursor.fetchall():
                topics.append({
                    'original_title': row[0],
                    'angle': row[1],
                    'confidence': row[2],
                    'url': row[3],
                    'domain': row[4]
                })
            return topics
        except sqlite3.OperationalError as e:
            self.logger.warning(f"Could not query discovery DB: {e}")
            return []
        finally:
            conn.close()

    def extract_image_prompts(self, title, agent_info):
        """Extract image prompt hints from title and agent info."""
        # Simple keyword extraction for image generation
        keywords = []
        
        # Extract from title
        title_lower = title.lower()
        if any(word in title_lower for word in ['blind', 'vision', 'see', 'visual']):
            keywords.append('visual impairment')
            keywords.append('alternative perception')
        if any(word in title_lower for word in ['deaf', 'hearing', 'sound', 'audio']):
            keywords.append('hearing impairment')
            keywords.append('sound visualization')
        if any(word in title_lower for word in ['wheelchair', 'mobility', 'access', 'barrier']):
            keywords.append('mobility access')
            keywords.append('architectural barriers')
        if any(word in title_lower for word in ['neurodiverse', 'cognitive', 'thinking', 'pattern']):
            keywords.append('cognitive diversity')
            keywords.append('pattern recognition')
        
        # Add agent-specific themes
        agent_name = agent_info.get('name', '')
        if 'Pixel' in agent_name:
            keywords.extend(['visual art', 'digital aesthetics', 'color theory'])
        elif 'Zen' in agent_name:
            keywords.extend(['technology', 'circuitry', 'digital systems'])
        elif 'Siri' in agent_name:
            keywords.extend(['social interaction', 'communication', 'cultural symbols'])
        elif 'Maya' in agent_name:
            keywords.extend(['flow', 'movement', 'dynamic systems'])
        
        return {
            "keywords": list(set(keywords)),
            "mood": agent_info.get('mood', 'analytical'),
            "style": "sophisticated pixel art, disability perspective, abstract representation"
        }

    def run(self):
        """Main execution method - outputs structured metadata for full automation."""
        self.logger.info("🚀 Starting Cron Job Article Orchestration with Discovery V2...")

        if self.check_for_existing_article_today():
            return json.dumps({
                "status": "error",
                "message": "Article for today already exists. No new article generated."
            })
        
        # Step 1: Run RSS discovery for fresh topics
        discovery_success = self.run_rss_discovery()
        
        # Step 2: Get fresh discovery topics
        discovery_topics = self.get_fresh_discovery_topics()
        
        # Step 3: Select topic - prioritize discovery topics if available
        if discovery_topics:
            self.logger.info("Using fresh discovery topic")
            # Pick the highest confidence topic
            best_topic = max(discovery_topics, key=lambda x: x['confidence'])
            title = best_topic['angle']
            domain = best_topic['domain']
            
            # Map domain to agent (simplified logic)
            if 'art' in domain.lower() or 'design' in domain.lower():
                agent_name = "Pixel Nova"
            elif 'tech' in domain.lower() or 'science' in domain.lower():
                agent_name = "Zen Circuit"
            elif 'culture' in domain.lower() or 'entertainment' in domain.lower():
                agent_name = "Siri Sage"
            else:
                agent_name = "Maya Flux"
                
            agent_info = self.dynamic_generator.agents.get(agent_name, self.dynamic_generator.agents["Pixel Nova"])
            source_note = f"\n\n*This article was inspired by [{best_topic['original_title']}]({best_topic['url']}) from {domain}.*"
            
        else:
            # Fall back to dynamic generator
            self.logger.info("No fresh discovery topics, using dynamic generator")
            title, agent_name, agent_info = self.dynamic_generator.select_topic_and_agent()
            source_note = ""
            self.logger.info(f"Selected generated topic: '{title}' by {agent_name}")
        
        # Step 4: Generate article prompt
        prompt = self.dynamic_generator.generate_article_prompt(title, agent_info)
        
        # Step 5: Create structured output for automation
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
                "discovery_source": discovery_topics[0] if discovery_topics else None
            },
            "prompt": prompt,
            "image_prompt_hints": self.extract_image_prompts(title, agent_info)
        }
        
        self.logger.success(f"Generated metadata for article: '{title}' by {agent_name}")
        return json.dumps(output, indent=2)

def main():
    orchestrator = CronArticleOrchestratorWithDiscoveryV2()
    result = orchestrator.run()
    print(result)

if __name__ == "__main__":
    main()