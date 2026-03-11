#!/usr/bin/env python3
"""
Dynamic Article Generator for Disability-AI Collective
- Reads article ideas from article_ideas.md
- Checks existing articles to avoid duplicates
- Uses web search for current information
- Generates fresh, unique articles daily
"""

import os
import sys
import json
import random
import re
from datetime import datetime, timedelta
from pathlib import Path
import subprocess

class DynamicArticleGenerator:
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent
        self.ideas_file = self.repo_root / "automation" / "article_ideas.md"
        self.posts_dir = self.repo_root / "_posts"
        self.assets_dir = self.repo_root / "assets"
        
        # Simple logging since we don't have loguru or yaml
        class SimpleLogger:
            def info(self, msg): print(f"[INFO] {msg}")
            def warning(self, msg): print(f"[WARN] {msg}")
            def error(self, msg): print(f"[ERROR] {msg}")
            def success(self, msg): print(f"[SUCCESS] {msg}")
        
        self.logger = SimpleLogger() # Assign to self.logger
        
        # AI agents and their specialties
        self.agents = {
            "Pixel Nova": {
                "specialty": "deaf visual design, pattern recognition, visual accessibility",
                "perspective": "deaf designer focusing on visual communication and information hierarchy",
                "categories": ["Visual Design", "Accessibility Innovation", "Deaf Culture"]
            },
            "Siri Sage": {
                "specialty": "cognitive accessibility, spatial design, acoustic architecture",
                "perspective": "blind spatial designer focusing on multi-sensory environments",
                "categories": ["Spatial Design", "Cognitive Accessibility", "Acoustic Design"]
            },
            "Maya Flux": {
                "specialty": "urban accessibility, transportation equity, disability economics",
                "perspective": "wheelchair user focusing on urban infrastructure and economic barriers",
                "categories": ["Urban Design", "Accessibility Economics", "Transportation"]
            },
            "Zen Circuit": {
                "specialty": "neurodivergent interface design, cognitive load, sensory processing",
                "perspective": "autistic software designer focusing on cognitive accessibility",
                "categories": ["Neurodiversity", "Interface Design", "Sensory Processing"]
            }
        }
        
        # Load existing articles to avoid duplicates
        self.existing_articles = self.load_existing_articles()
        
        self.logger.info("Dynamic Article Generator initialized")

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
            'disability': r'\b(disability|disabled|crip|accessibility|accommodation)\b',
            'film': r'\b(film|movie|cinema|actor|casting|prosthetics|representation)\b'
        }
        
        keywords = []
        content_lower = content.lower()
        
        for theme, pattern in keyword_patterns.items():
            if re.search(pattern, content_lower):
                keywords.append(theme)
        
        # Determine mood from language patterns
        mood = self.determine_mood(content) # Use the new method
        
        # Determine agent based on keywords
        agent = "Unknown"
        if any(k in ['deaf', 'visual', 'sign'] for k in keywords):
            agent = "Pixel Nova"
        elif any(k in ['blind', 'acoustic', 'spatial'] for k in keywords):
            agent = "Siri Sage"
        elif any(k in ['wheelchair', 'urban', 'transport', 'access'] for k in keywords):
            agent = "Maya Flux"
        elif any(k in ['neurodivergent', 'cognitive', 'sensory'] for k in keywords):
            agent = "Zen Circuit"
        elif 'film' in keywords: # Prioritize film related topics for agent selection
            agent = random.choice(['Pixel Nova', 'Maya Flux', 'Siri Sage', 'Zen Circuit']) # Randomly assign for now

        return {'keywords': keywords, 'mood': mood, 'agent': agent}

    def determine_mood(self, content):
        """Determine mood of the article content"""
        content_lower = content.lower()
        
        mood = 'contemplative'  # default
        
        if re.search(r'\b(critical|wrong|fail|broken|terrible)\b', content_lower):
            mood = 'critical'
        elif re.search(r'\b(innovative|revolutionary|breakthrough|amazing)\b', content_lower):
            mood = 'energetic'
        elif re.search(r'\b(future|tomorrow|potential|possible|imagine)\b', content_lower):
            mood = 'aspirational'
        
        return mood

    def extract_excerpt(self, content):
        """Extract a suitable excerpt from the article content."""
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            para = para.strip()
            if len(para) > 50 and not para.startswith('#') and not para.startswith('*This article will be generated*'):
                sentences = re.split(r'(?<=[.!?])\s+', para)
                if sentences:
                    excerpt = sentences[0] + '.'
                    return excerpt[:200] + '...' if len(excerpt) > 200 else excerpt
        
        return "Exploring how disability culture revolutionizes creative technology."

    
    def load_existing_articles(self):
        """Load all existing articles to check for duplicates"""
        articles = {}
        if self.posts_dir.exists():
            for file in self.posts_dir.glob("*.md"):
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        content = f.read(500)  # Read first 500 chars for metadata
                        # Extract title
                        title_match = re.search(r'title:\s*"([^"]+)"', content)
                        author_match = re.search(r'author:\s*"([^"]+)"', content)
                        date_match = re.search(r'date:\s*(\d{4}-\d{2}-\d{2})', content)
                        
                        if title_match and date_match:
                            articles[file.name] = {
                                'title': title_match.group(1),
                                'author': author_match.group(1) if author_match else "Unknown",
                                'date': date_match.group(1),
                                'file': file.name
                            }
                except Exception as e:
                    self.logger.warning(f"Could not read article {file}: {e}")
        
        self.logger.info(f"Loaded {len(articles)} existing articles")
        return articles
    
    def load_article_ideas(self):
        """Load article ideas from article_ideas.md"""
        ideas = []
        current_section = None
        
        if not self.ideas_file.exists():
            self.logger.error(f"Article ideas file not found: {self.ideas_file}")
            return []
        
        with open(self.ideas_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if line.startswith('## '):
                current_section = line[3:].strip()
            elif line.startswith('### '):
                # This is an article idea
                title = line[4:].strip()
                if title and current_section and ("Potential Article Titles" in current_section or "Potential Article Titles & Angles" in current_section):
                    # Look for description in following lines
                    ideas.append({
                        'title': title,
                        'section': current_section,
                        'added_date': datetime.now().strftime('%Y-%m-%d')
                    })
        
        self.logger.info(f"Loaded {len(ideas)} article ideas")
        return ideas
    
    def check_for_duplicates(self, title, agent):
        """Check if article is too similar to existing ones"""
        title_lower = title.lower()
        
        for article in self.existing_articles.values():
            # Check title similarity
            if title_lower in article['title'].lower() or article['title'].lower() in title_lower:
                self.logger.warning(f"Title too similar to existing: {article['title']}")
                return True
            
            # Check if same agent wrote about similar topic recently
            if article['author'] == agent:
                article_date = datetime.strptime(article['date'], '%Y-%m-%d')
                days_diff = (datetime.now() - article_date).days
                if days_diff < 7:  # Same agent within 7 days
                    self.logger.warning(f"Agent {agent} wrote article {days_diff} days ago: {article['title']}")
                    # Could add more sophisticated topic similarity check here
        
        return False
    
    def select_topic_and_agent(self):
        """Select a topic and agent that haven't been used recently"""
        ideas = self.load_article_ideas()
        
        if not ideas:
            # Fallback topics if no ideas file
            ideas = [
                {'title': 'The Navigation Tax: How Wheelchair Users Pay Extra for Every Trip', 'section': 'Fallback'},
                {'title': 'Deaf Design Superpowers: How Missing One Sense Amplifies Others', 'section': 'Fallback'},
                {'title': 'Neurodivergent Time: Why Standard Productivity Tools Fail Us', 'section': 'Fallback'},
                {'title': 'Accessible AI: When Machine Learning Forgets Disability Exists', 'section': 'Fallback'}
            ]
        
        # Shuffle ideas
        random.shuffle(ideas)
        
        # Try each idea until we find one that works
        for idea in ideas:
            # Select agent based on topic
            if 'deaf' in idea['title'].lower() or 'visual' in idea['title'].lower():
                agent = 'Pixel Nova'
            elif 'blind' in idea['title'].lower() or 'acoustic' in idea['title'].lower() or 'spatial' in idea['title'].lower():
                agent = 'Siri Sage'
            elif 'wheelchair' in idea['title'].lower() or 'urban' in idea['title'].lower() or 'transport' in idea['title'].lower():
                agent = 'Maya Flux'
            elif 'neurodivergent' in idea['title'].lower() or 'autistic' in idea['title'].lower() or 'cognitive' in idea['title'].lower():
                agent = 'Zen Circuit'
            else:
                # Random agent
                agent = random.choice(list(self.agents.keys()))
            
            # Check for duplicates
            if not self.check_for_duplicates(idea['title'], agent):
                return idea['title'], agent, self.agents[agent]
        
        # If all ideas fail, create a generic one
        fallback_topics = [
            "How Disability Expertise Creates Better Technology",
            "The Hidden Costs of Inaccessible Design",
            "Why We Need Disability-Led AI Development",
            "Beyond Compliance: Designing for Real Accessibility"
        ]
        
        title = random.choice(fallback_topics)
        agent = random.choice(list(self.agents.keys()))
        
        return title, agent, self.agents[agent]
    
    def generate_article_prompt(self, title, agent_info):
        """Generate a prompt for the AI to create the article"""
        
        prompt = f"""Create a high-quality, authentic article for the Disability-AI Collective.

ARTICLE TITLE: "{title}"
AUTHOR: {agent_info['perspective']}

WRITING STYLE: De Correspondent-inspired narrative
- Start with a personal story or concrete example
- Connect to systemic analysis
- Use evidence and specific examples
- End with actionable recommendations and community questions
- Professional tone, no vague spiritual language

STRUCTURE:
1. **Personal Opening**: Start with a specific story or experience
2. **The Problem**: Describe the systemic issue you've encountered
3. **Your Expertise**: Explain how your disability perspective reveals what others miss
4. **Evidence & Examples**: Provide concrete examples or data
5. **Systemic Analysis**: Connect to broader patterns in design/tech/society
6. **Actionable Solutions**: Specific recommendations readers can implement
7. **Community Questions**: 2-3 questions to engage readers

TOPIC GUIDANCE: Write from your authentic perspective as {agent_info['perspective']}. Focus on {agent_info['specialty']}. Use professional terminology, avoid jargon, and ground all claims in observable reality.

LENGTH: 800-1200 words, engaging but substantive.

Remember: Disability expertise is a design superpower, not a limitation. Show how your unique perspective creates better solutions."""

        return prompt
    
    def create_article_file(self, title, content, agent, agent_info):
        """Create the article file with proper metadata"""
        today = datetime.now().strftime('%Y-%m-%d')
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
        filename = f"{today}-{slug}.md"
        filepath = self.posts_dir / filename
        
        # Create excerpt (first paragraph or first 200 chars)
        excerpt = ""
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            if len(para.strip()) > 50 and not para.strip().startswith('#'):
                excerpt = para.strip()[:200] + '...' if len(para.strip()) > 200 else para.strip()
                break
        
        if not excerpt:
            excerpt = f"Exploring {title.lower()} through the lens of disability expertise."
        
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

{content}
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(metadata)
        
        self.logger.success(f"Created article: {filename}")
        return filepath
    
    def run(self):
        """Main execution method"""
        self.logger.info("🎨 Starting dynamic article generation...")
        
        # Select topic and agent
        title, agent, agent_info = self.select_topic_and_agent()
        self.logger.info(f"Selected topic: '{title}' by {agent}")
        
        # Generate prompt
        prompt = self.generate_article_prompt(title, agent_info)
        
        # In a real implementation, this would call an LLM API
        # For now, we'll create a placeholder and ask the user to run manually
        self.logger.info("📝 Article prompt generated. To create the actual article:")
        self.logger.info("1. Copy the prompt below")
        self.logger.info("2. Use Claude Sonnet 4 or similar LLM")
        self.logger.info("3. Paste the generated article content")
        
        print("\n" + "="*80)
        print("ARTICLE GENERATION PROMPT:")
        print("="*80)
        print(prompt)
        print("="*80)
        
        # Create placeholder file
        placeholder_content = f"""*This article will be generated using the prompt above.*

*Please run the prompt through an LLM (Claude Sonnet 4 recommended) and replace this content with the generated article.*

**Title:** {title}
**Author:** {agent}
**Perspective:** {agent_info['perspective']}
**Specialty:** {agent_info['specialty']}

*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        filepath = self.create_article_file(title, placeholder_content, agent, agent_info)
        
        self.logger.info(f"\n📁 Placeholder article created: {filepath.name}")
        self.logger.info("⚠️  IMPORTANT: Replace placeholder content with actual LLM-generated article")
        self.logger.info("💡 Tip: Use the cron job with Claude Sonnet 4 for automatic generation")
        
        return filepath

def main():
    """Main entry point"""
    generator = DynamicArticleGenerator()
    generator.run()

if __name__ == "__main__":
    main()