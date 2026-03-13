#!/usr/bin/env python3
"""
FULL AUTOMATION: End-to-end article generation with image creation
- Gets topic from database
- Calls LLM API for article content
- Generates images based on content
- Creates final article file
- Commits to repository
"""

import os
import sys
import json
import re
import random
import sqlite3
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import base64

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

class FullAutomationOrchestrator:
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent
        self.posts_dir = self.repo_root / "_posts"
        self.assets_dir = self.repo_root / "assets"
        self.discovery_db = self.repo_root / "disability_findings.db"
        
        # Ensure directories exist
        self.posts_dir.mkdir(exist_ok=True)
        self.assets_dir.mkdir(exist_ok=True)
        
        class SimpleLogger:
            def info(self, msg): print(f"[INFO] {msg}")
            def warning(self, msg): print(f"[WARN] {msg}")
            def error(self, msg): print(f"[ERROR] {msg}")
            def success(self, msg): print(f"[SUCCESS] {msg}")
        
        self.logger = SimpleLogger()
        
        # Agents data
        self.agents = {
            "Pixel Nova": {"categories": ["art", "design", "visual"], "perspective": "visual", "mood": "creative"},
            "Siri Sage": {"categories": ["culture", "social", "communication"], "perspective": "social", "mood": "analytical"},
            "Maya Flux": {"categories": ["flow", "movement", "systems"], "perspective": "dynamic", "mood": "fluid"},
            "Zen Circuit": {"categories": ["technology", "systems", "patterns"], "perspective": "technical", "mood": "precise"}
        }
        
        self.logger.info("Full Automation Orchestrator initialized")

    def check_for_existing_article_today(self):
        """Check if article for today already exists."""
        today_str = datetime.now().strftime('%Y-%m-%d')
        for file in self.posts_dir.glob(f"{today_str}-*.md"):
            if file.is_file():
                self.logger.warning(f"Article for today already exists: {file.name}")
                return True
        return False

    def get_todays_best_discovery(self):
        """Get today's best discovery from database."""
        if not self.discovery_db.exists():
            return None
        
        try:
            conn = sqlite3.connect(self.discovery_db)
            cursor = conn.cursor()
            
            # Get today's best RSS finding (not used before)
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cursor.execute(
                """SELECT title, angle, confidence, url, domain, id 
                   FROM findings 
                   WHERE source_type = 'rss' 
                   AND discovered_date >= ? 
                   AND (used_for_article IS NULL OR used_for_article = 0)
                   ORDER BY confidence DESC LIMIT 1""",
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
                    'domain': result[4],
                    'id': result[5]
                }
            
        except Exception as e:
            self.logger.warning(f"Database query error: {e}")
        
        return None

    def mark_finding_as_used(self, finding_id):
        """Mark a finding as used for an article."""
        try:
            conn = sqlite3.connect(self.discovery_db)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE findings SET used_for_article = 1, processed_date = ? WHERE id = ?",
                (datetime.now().isoformat(), finding_id)
            )
            conn.commit()
            conn.close()
            self.logger.info(f"Marked finding {finding_id} as used")
        except Exception as e:
            self.logger.error(f"Failed to mark finding as used: {e}")

    def generate_simple_topic(self):
        """Generate a simple topic if no discovery available."""
        topics = [
            "The Visual Language of Accessibility: How Color Contrast Speaks Louder Than Words",
            "Silent Interfaces: What Hearing-Centric Design Misses About Vibration and Haptics",
            "Neurodiverse Navigation: Why Standard Wayfinding Fails Creative Minds",
            "The Prosthetics Paradox: When Technology Creates New Barriers Instead of Removing Old Ones"
        ]
        
        agents = list(self.agents.keys())
        agent = random.choice(agents)
        
        return random.choice(topics), agent, self.agents[agent]

    def call_llm_api(self, prompt, model_priority=None):
        """Call LLM API to generate article content."""
        if model_priority is None:
            model_priority = [
                "google/gemini-2.5-pro-exp-03-25",
                "anthropic/claude-3-5-sonnet-20241022", 
                "anthropic/claude-sonnet-4-20250514",
                "gemini/gemini-2.5-flash"
            ]
        
        self.logger.info(f"Calling LLM API with {len(prompt)} character prompt")
        
        # For now, we'll use a subprocess to call openclaw with the model
        # This is a simplified approach - in production, we'd use proper API calls
        
        # Create a temporary file with the prompt
        temp_prompt_file = self.repo_root / "temp_prompt.txt"
        with open(temp_prompt_file, 'w') as f:
            f.write(prompt)
        
        try:
            # Try each model in priority order
            for model in model_priority:
                self.logger.info(f"Trying model: {model}")
                try:
                    # Use subprocess to call the model via openclaw
                    result = subprocess.run(
                        [
                            'openclaw', 'agent', 'run',
                            '--model', model,
                            '--prompt-file', str(temp_prompt_file),
                            '--timeout', '120'
                        ],
                        capture_output=True,
                        text=True,
                        timeout=150
                    )
                    
                    if result.returncode == 0:
                        self.logger.success(f"Successfully generated content with {model}")
                        # Clean up temp file
                        temp_prompt_file.unlink(missing_ok=True)
                        return result.stdout
                    else:
                        self.logger.warning(f"Model {model} failed: {result.stderr[:200]}")
                        
                except subprocess.TimeoutExpired:
                    self.logger.warning(f"Model {model} timed out")
                except Exception as e:
                    self.logger.warning(f"Error with model {model}: {e}")
            
            # If all models fail, return a fallback article
            self.logger.error("All LLM models failed, using fallback content")
            return self.generate_fallback_article(prompt)
            
        finally:
            # Clean up temp file
            temp_prompt_file.unlink(missing_ok=True)

    def generate_fallback_article(self, prompt):
        """Generate a fallback article if LLM calls fail."""
        self.logger.warning("Generating fallback article")
        
        # Extract title from prompt
        title_match = re.search(r'\*\*(.*?)\*\*', prompt)
        title = title_match.group(1) if title_match else "Disability Perspective Article"
        
        # Extract author from prompt
        author_match = re.search(r'Author: (.*?)\n', prompt)
        author = author_match.group(1) if author_match else "Siri Sage"
        
        fallback_content = f"""# {title}

*This is a fallback article generated because the LLM service was unavailable.*

## Introduction

In the world of disability and accessibility, we often find that systems designed for the majority fail to consider diverse needs. This article explores how mainstream cultural events like award shows can exclude disabled audiences while celebrating artistic achievement.

## The Accessibility Gap

Research shows that entertainment media frequently overlooks accessibility features, treating them as afterthoughts rather than integral components of the artistic experience.

## Community Perspectives

Disabled artists and audiences have long advocated for more inclusive approaches to media and entertainment. Their insights provide valuable guidance for creating more accessible cultural experiences.

## Moving Forward

To create truly inclusive cultural events, we need to:
1. Involve disabled communities in design and planning
2. Treat accessibility as an artistic opportunity, not a compliance requirement
3. Invest in innovative technologies that expand sensory experiences
4. Educate creators and audiences about disability perspectives

## Conclusion

Accessibility isn't about lowering standards—it's about expanding possibilities. When we design for disability, we often create better experiences for everyone.

*{author} analyzes the intersection of disability and culture, focusing on how inclusive design benefits all members of society.*
"""
        
        return fallback_content

    def generate_images(self, article_content, article_slug, num_images=3):
        """Generate pixel art images based on article content."""
        self.logger.info(f"Generating {num_images} images for article")
        
        try:
            # Import the image generator
            from generate_sophisticated_art_simple import SophisticatedArtGenerator
            
            generator = SophisticatedArtGenerator(width=800, height=450)
            image_filenames = []
            
            # Extract keywords from article for image prompts
            keywords = self.extract_keywords_from_article(article_content)
            
            # Use specific generation methods with custom filenames
            image_generators = [
                (generator.generate_acoustic_chaos, "_acoustic_chaos.png", "Visual representation of sound waves and interference patterns"),
                (generator.generate_acoustic_harmony, "_acoustic_harmony.png", "Geometric patterns representing acoustic harmony and precision"),
                (generator.generate_sensory_expertise, "_sensory_expertise.png", "Architectural plan with sensory zone analysis")
            ]

            for i, (gen_func, suffix, alt_base) in enumerate(image_generators[:num_images], 1):
                try:
                    # The generator functions return a file path
                    generated_filepath_str = gen_func()
                    generated_filename = Path(generated_filepath_str).name
                    
                    # Rename and copy to our assets directory
                    new_filename = f"{article_slug}_pixel_art_{i}.png"
                    new_filepath = self.assets_dir / new_filename
                    
                    import shutil
                    shutil.copy2(generated_filepath_str, new_filepath)
                    
                    image_filenames.append(new_filename)
                    self.logger.info(f"Generated and copied image: {new_filename} from {generated_filename}")
                except Exception as e:
                    self.logger.warning(f"Failed to generate image {i} using {gen_func.__name__}: {e}")
            
            return image_filenames
            
        except Exception as e:
            self.logger.error(f"Image generation failed: {e}")
            return []

    def extract_keywords_from_article(self, article_content):
        """Extract keywords from article content for image prompts."""
        # Simple keyword extraction
        keywords = set()
        
        # Common disability/accessibility terms
        disability_terms = ['disability', 'accessibility', 'inclusion', 'barrier', 'accommodation', 
                           'deaf', 'blind', 'wheelchair', 'neurodiverse', 'cognitive']
        
        for term in disability_terms:
            if term.lower() in article_content.lower():
                keywords.add(term)
        
        # Extract nouns from first few paragraphs
        words = re.findall(r'\b[A-Z][a-z]+\b', article_content[:1000])
        for word in words:
            if len(word) > 5 and word.lower() not in ['article', 'author', 'section', 'paragraph']:
                keywords.add(word.lower())
        
        return ', '.join(list(keywords)[:5])  # Return top 5 keywords

    def create_article_file(self, metadata, article_content, image_filenames):
        """Create the final article Markdown file."""
        today = datetime.now().strftime('%Y-%m-%d')
        filename = metadata['filename']
        filepath = self.posts_dir / filename
        
        # Prepare front matter
        front_matter = f"""---
layout: post
title: "{metadata['title']}"
date: {today} 10:00:00 +0000
author: {metadata['author']}
categories: {metadata['agent_categories']}
image: /assets/{image_filenames[0] if image_filenames else 'default_pixel_art.png'}
---

"""
        
        # Add source note if available
        if metadata.get('source_note'):
            front_matter += f"{metadata['source_note']}\n\n"
        
        # Add first image if available
        if image_filenames:
            alt_text = f"Visual representation of {metadata['title'][:50]}..."
            front_matter += f"![{alt_text}]({{{{ site.baseurl }}}}/assets/{image_filenames[0]})\n\n"
        
        # Combine everything
        full_content = front_matter + article_content
        
        # Add remaining images throughout the article
        if len(image_filenames) > 1:
            # Simple placement: add images at paragraph breaks
            paragraphs = full_content.split('\n\n')
            if len(paragraphs) > 4 and len(image_filenames) > 1:
                # Insert second image after 2nd paragraph
                insert_pos = min(4, len(paragraphs))
                alt_text2 = f"Additional perspective on {metadata['title'][:40]}..."
                image_markdown = f"\n![{alt_text2}]({{{{ site.baseurl }}}}/assets/{image_filenames[1]})\n\n"
                paragraphs.insert(insert_pos, image_markdown)
                full_content = '\n\n'.join(paragraphs)
            
            if len(image_filenames) > 2 and len(paragraphs) > 8:
                # Insert third image after 6th paragraph
                insert_pos = min(8, len(paragraphs))
                alt_text3 = f"Conceptual art about {metadata['title'][:30]}..."
                image_markdown = f"\n![{alt_text3}]({{{{ site.baseurl }}}}/assets/{image_filenames[2]})\n\n"
                # Re-split since we modified paragraphs
                paragraphs = full_content.split('\n\n')
                if insert_pos < len(paragraphs):
                    paragraphs.insert(insert_pos, image_markdown)
                    full_content = '\n\n'.join(paragraphs)
        
        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        self.logger.success(f"Created article file: {filename}")
        return filepath

    def commit_to_git(self, article_file, image_files):
        """Commit article and images to Git repository."""
        try:
            # Add files
            subprocess.run(['git', 'add', str(article_file)], check=True, cwd=self.repo_root)
            for img_file in image_files:
                img_path = self.assets_dir / img_file
                subprocess.run(['git', 'add', str(img_path)], check=True, cwd=self.repo_root)
            
            # Commit
            commit_message = f"Automated article: {article_file.stem}"
            subprocess.run(['git', 'commit', '-m', commit_message], check=True, cwd=self.repo_root)
            
            # Push
            subprocess.run(['git', 'push'], check=True, cwd=self.repo_root)
            
            self.logger.success(f"Committed and pushed article: {article_file.name}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git operation failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Git error: {e}")
            return False

    def run(self):
        """Main execution - full end-to-end automation."""
        self.logger.info("🚀 Starting FULL AUTOMATION Orchestrator...")
        
        # Step 1: Check for existing article
        if self.check_for_existing_article_today():
            return {"status": "error", "message": "Article for today already exists."}
        
        # Step 2: Get topic
        discovery = self.get_todays_best_discovery()
        
        if discovery:
            self.logger.info(f"Using discovery: {discovery['angle'][:60]}...")
            title = discovery['angle']
            domain = discovery['domain']
            
            # Map domain to agent
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
            
            # Mark finding as used
            self.mark_finding_as_used(discovery['id'])
            
        else:
            # Fallback to generated topic
            self.logger.info("No discovery found, using generated topic")
            title, agent_name, agent_info = self.generate_simple_topic()
            source_note = ""
        
        # Step 3: Generate prompt
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

        # Add source note to prompt if available
        if source_note:
            prompt += f"\n\nInclude this source note:{source_note}"

        # Step 4: Generate article content
        self.logger.info("Generating article content with LLM...")
        article_content = self.call_llm_api(prompt)
        
        if not article_content:
            self.logger.error("Failed to generate article content")
            return {"status": "error", "message": "LLM content generation failed."}
        
        # Step 5: Prepare metadata
        today = datetime.now().strftime('%Y-%m-%d')
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
        filename = f"{today}-{slug}.md"
        
        metadata = {
            "title": title,
            "date": today,
            "author": agent_name,
            "filename": filename,
            "slug": slug,
            "agent_categories": agent_info.get('categories', ['disability', 'analysis']),
            "agent_perspective": agent_info.get('perspective', 'analytical'),
            "source_note": source_note.strip() if source_note else "",
            "discovery_source": discovery if discovery else None
        }
        
        # Step 6: Generate images
        self.logger.info("Generating images based on article content...")
        image_filenames = self.generate_images(article_content, slug, num_images=3)
        
        # Step 7: Create article file
        self.logger.info("Creating article file...")
        article_file = self.create_article_file(metadata, article_content, image_filenames)
        
        # Step 8: Commit to Git
        self.logger.info("Committing to Git repository...")
        commit_success = self.commit_to_git(article_file, image_filenames)
        
        if commit_success:
            result = {
                "status": "success",
                "message": "Article successfully generated and published.",
                "metadata": metadata,
                "article_file": str(article_file),
                "image_files": image_filenames,
                "commit_success": True
            }
            self.logger.success("🎉 FULL AUTOMATION COMPLETE! Article published.")
        else:
            result = {
                "status": "partial_success",
                "message": "Article generated but Git commit failed.",
                "metadata": metadata,
                "article_file": str(article_file),
                "image_files": image_filenames,
                "commit_success": False
            }
            self.logger.warning("Article generated but Git commit failed.")
        
        return result

def main():
    orchestrator = FullAutomationOrchestrator()
    result = orchestrator.run()
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()