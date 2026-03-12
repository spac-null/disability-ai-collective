#!/usr/bin/env python3
"""
Disability-AI Collective Discovery Crawler

A sophisticated crawler that finds disability angles in NON-disability related content.
Finds subtle references to disability in general journalism, tech, business, design,
science, and culture content, then transforms them into article ideas.

Key Features:
1. Focus on non-disability content
2. Look for subtle disability references
3. Convert findings into article ideas
4. Ethical crawling with rate limiting
5. Structured data output (SQLite + JSON)
6. RSS feed reader for multiple sources
7. Content analyzer with keyword/pattern matching
8. Article idea generator with disability-AI angles
"""

import asyncio
import aiohttp
import sqlite3
import json
import re
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from urllib.parse import urlparse, urljoin
import feedparser
from bs4 import BeautifulSoup
import hashlib
from pathlib import Path
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ArticleFinding:
    """Represents a discovered article with disability angle potential"""
    id: str
    source_url: str
    source_name: str
    original_title: str
    original_summary: str
    publish_date: str
    discovered_at: str
    disability_keywords: List[str]
    disability_context: str
    article_title: str
    article_angle: str
    research_questions: List[str]
    assigned_agent: str
    confidence_score: float
    tags: List[str]
    raw_content_hash: str
    
    def to_dict(self):
        return asdict(self)

@dataclass
class SourceConfig:
    """Configuration for a content source"""
    name: str
    rss_url: str
    category: str
    rate_limit_seconds: int = 5
    enabled: bool = True
    keywords_boost: Dict[str, float] = None
    
    def __post_init__(self):
        if self.keywords_boost is None:
            self.keywords_boost = {}

# ============================================================================
# DISABILITY KEYWORDS AND PATTERNS
# ============================================================================

DISABILITY_KEYWORDS = {
    # Physical disabilities
    'wheelchair': 0.9,
    'prosthetic': 0.9,
    'crutch': 0.8,
    'walker': 0.8,
    'cane': 0.7,
    'mobility': 0.6,
    'accessible': 0.7,
    'accessibility': 0.8,
    
    # Sensory disabilities
    'deaf': 0.9,
    'hard of hearing': 0.8,
    'hearing loss': 0.8,
    'blind': 0.9,
    'visually impaired': 0.8,
    'low vision': 0.8,
    'sensory': 0.6,
    
    # Neurodiversity and cognitive disabilities
    'neurodiverse': 0.9,
    'neurodivergent': 0.9,
    'autistic': 0.8,
    'ADHD': 0.8,
    'dyslexia': 0.8,
    'cognitive': 0.7,
    'learning disability': 0.8,
    
    # Chronic conditions and invisible disabilities
    'chronic pain': 0.8,
    'fibromyalgia': 0.8,
    'MS': 0.8,
    'multiple sclerosis': 0.8,
    'arthritis': 0.7,
    'invisible disability': 0.9,
    
    # Social and systemic aspects
    'accommodation': 0.7,
    'inclusion': 0.7,
    'exclusion': 0.8,
    'marginalization': 0.8,
    'ableism': 0.9,
    'disability rights': 0.9,
    'ADA': 0.8,
    'universal design': 0.8,
    
    # Assistive technology
    'screen reader': 0.8,
    'voice control': 0.7,
    'caption': 0.8,
    'transcript': 0.7,
    'sign language': 0.8,
    'braille': 0.8,
    'assistive tech': 0.8,
}

DISABILITY_PATTERNS = [
    r'(struggle|difficulty|challenge|barrier).*(see|hear|move|walk|read|write|communicate)',
    r'(cannot|can\'t|unable to).*(see|hear|move|walk|read|write|communicate)',
    r'(exclude|exclusion).*(disability|disabled|wheelchair|deaf|blind)',
    r'(design|build|create).*(without|excluding).*(disability|accessibility)',
    r'(technology|app|website|product).*(not.*accessible|inaccessible)',
    r'(work|office|job).*(accommodation|disability|accessible)',
    r'(remote work|hybrid work).*(disability|inclusion|accessibility)',
]

# ============================================================================
# SOURCE CONFIGURATIONS
# ============================================================================

SOURCE_CONFIGS = [
    # Tech Journalism
    SourceConfig(
        name="TechCrunch",
        rss_url="https://techcrunch.com/feed/",
        category="tech",
        rate_limit_seconds=3,
        keywords_boost={'AI': 1.2, 'tech': 1.1, 'startup': 1.1}
    ),
    SourceConfig(
        name="Wired",
        rss_url="https://www.wired.com/feed/rss",
        category="tech",
        rate_limit_seconds=4
    ),
    SourceConfig(
        name="The Verge",
        rss_url="https://www.theverge.com/rss/index.xml",
        category="tech",
        rate_limit_seconds=3
    ),
    
    # Business/Economics
    SourceConfig(
        name="Bloomberg",
        rss_url="https://www.bloomberg.com/feeds/podcasts/etf-report.xml",
        category="business",
        rate_limit_seconds=5
    ),
    SourceConfig(
        name="Financial Times",
        rss_url="https://www.ft.com/?format=rss",
        category="business",
        rate_limit_seconds=6
    ),
    SourceConfig(
        name="Harvard Business Review",
        rss_url="https://hbr.org/feed",
        category="business",
        rate_limit_seconds=5
    ),
    
    # Design/Architecture
    SourceConfig(
        name="Dezeen",
        rss_url="https://www.dezeen.com/feed/",
        category="design",
        rate_limit_seconds=4,
        keywords_boost={'design': 1.2, 'architecture': 1.2}
    ),
    SourceConfig(
        name="ArchDaily",
        rss_url="https://www.archdaily.com/feed",
        category="design",
        rate_limit_seconds=4
    ),
    SourceConfig(
        name="Fast Company Design",
        rss_url="https://www.fastcompany.com/design/rss",
        category="design",
        rate_limit_seconds=4
    ),
    
    # Science/Health
    SourceConfig(
        name="Nature",
        rss_url="https://www.nature.com/nature.rss",
        category="science",
        rate_limit_seconds=6
    ),
    SourceConfig(
        name="New Scientist",
        rss_url="https://www.newscientist.com/feed/home",
        category="science",
        rate_limit_seconds=5
    ),
    
    # Culture/Entertainment
    SourceConfig(
        name="Variety",
        rss_url="https://variety.com/feed/",
        category="culture",
        rate_limit_seconds=4
    ),
    SourceConfig(
        name="Hollywood Reporter",
        rss_url="https://www.hollywoodreporter.com/feed/",
        category="culture",
        rate_limit_seconds=4
    ),
    SourceConfig(
        name="Pitchfork",
        rss_url="https://pitchfork.com/feed/feed-news/rss",
        category="culture",
        rate_limit_seconds=4
    ),
    
    # General News (non-disability sections)
    SourceConfig(
        name="New York Times Technology",
        rss_url="https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
        category="news",
        rate_limit_seconds=5
    ),
    SourceConfig(
        name="The Guardian Technology",
        rss_url="https://www.theguardian.com/technology/rss",
        category="news",
        rate_limit_seconds=5
    ),
    SourceConfig(
        name="BBC Technology",
        rss_url="http://feeds.bbci.co.uk/news/technology/rss.xml",
        category="news",
        rate_limit_seconds=5
    ),
]

# ============================================================================
# ARTICLE IDEA GENERATORS
# ============================================================================

class ArticleIdeaGenerator:
    """Generates disability-AI article ideas from discovered content"""
    
    # Mapping of categories to potential article angles
    CATEGORY_ANGLES = {
        'tech': [
            "How {topic} Excludes {disability} Users",
            "The {disability} Perspective on {topic}",
            "{topic} Through a {disability} Lens",
            "Why {topic} Fails {disability} Communities",
            "Building {topic} That Includes {disability} Users",
        ],
        'business': [
            "The Business Case for {disability} Inclusion in {topic}",
            "How {topic} Impacts {disability} Employment",
            "{disability} Consumers and the {topic} Market",
            "The Economic Cost of Excluding {disability} from {topic}",
            "{topic}: Opportunity or Barrier for {disability} Workers?",
        ],
        'design': [
            "How {topic} Design Excludes {disability} People",
            "Inclusive Design Principles for {topic}",
            "The {disability} Experience of {topic} Spaces",
            "Redesigning {topic} for {disability} Accessibility",
            "{topic} as Sensory Exclusion: A {disability} Analysis",
        ],
        'science': [
            "The {disability} Implications of {topic} Research",
            "How {topic} Science Overlooks {disability}",
            "{disability} Perspectives on {topic} Discoveries",
            "The Ethics of {topic} for {disability} Communities",
            "{topic}: Scientific Progress or {disability} Exclusion?",
        ],
        'culture': [
            "How {topic} Represents (or Erases) {disability}",
            "The {disability} Subtext in {topic}",
            "{topic} Through a {disability} Cultural Lens",
            "Why {topic} Needs More {disability} Voices",
            "Deconstructing {topic}: A {disability} Critique",
        ],
        'news': [
            "The {disability} Angle on {topic}",
            "How {topic} Affects {disability} Communities",
            "The Untold {disability} Story of {topic}",
            "{topic}: What About {disability} People?",
            "Reading Between the Lines: {disability} in {topic}",
        ],
    }
    
    # Research questions by category
    RESEARCH_QUESTIONS = {
        'tech': [
            "How does this technology currently exclude people with this disability?",
            "What assistive technologies could make this more accessible?",
            "What are the specific barriers for people with this disability?",
            "How could AI be used to improve accessibility?",
            "What design changes would make this inclusive?",
        ],
        'business': [
            "What economic impact does this have on people with disabilities?",
            "How does this affect employment opportunities?",
            "What are the market opportunities in making this accessible?",
            "What legal/compliance issues exist?",
            "How does this intersect with disability rights legislation?",
        ],
        'design': [
            "What sensory or physical barriers exist in this design?",
            "How does this design prioritize certain abilities over others?",
            "What universal design principles could be applied?",
            "How does this design affect people with different disabilities?",
            "What would a truly inclusive version look like?",
        ],
        'science': [
            "How are people with disabilities represented in this research?",
            "What ethical considerations exist for disability communities?",
            "How might this discovery impact assistive technology?",
            "What accessibility implications does this research have?",
            "How could this research be made more inclusive?",
        ],
        'culture': [
            "How are people with disabilities represented in this cultural product?",
            "What stereotypes or tropes are present?",
            "How does this reflect societal attitudes toward disability?",
            "What disability perspectives are missing?",
            "How could this be more authentically inclusive?",
        ],
        'news': [
            "How are people with disabilities affected by this news?",
            "What disability perspectives are missing from coverage?",
            "How does this intersect with disability rights?",
            "What historical context exists for disability communities?",
            "What solutions would benefit people with disabilities?",
        ],
    }
    
    # Disability terms for substitution
    DISABILITY_TERMS = {
        'wheelchair': ['wheelchair users', 'mobility disabilities'],
        'prosthetic': ['limb difference', 'prosthetic users'],
        'deaf': ['Deaf community', 'hard of hearing'],
        'blind': ['blind community', 'visually impaired'],
        'neurodiverse': ['neurodivergent people', 'cognitive disabilities'],
        'sensory': ['sensory disabilities', 'sensory processing differences'],
    }
    
    @classmethod
    def generate_article_idea(
        cls, 
        original_title: str, 
        category: str, 
        disability_keywords: List[str],
        context: str
    ) -> Tuple[str, str, List[str]]:
        """Generate article title, angle, and research questions"""
        
        # Extract main topic from original title
        topic = cls._extract_topic(original_title)
        
        # Get primary disability keyword
        primary_disability = disability_keywords[0] if disability_keywords else "disability"
        disability_term = cls.DISABILITY_TERMS.get(primary_disability, [primary_disability])[0]
        
        # Select angle template
        angle_templates = cls.CATEGORY_ANGLES.get(category, cls.CATEGORY_ANGLES['news'])
        angle_template = random.choice(angle_templates)
        
        # Generate title and angle
        article_title = angle_template.format(topic=topic, disability=disability_term)
        article_angle = f"Exploring how {topic.lower()} intersects with {disability_term.lower()} experiences and accessibility"
        
        # Generate research questions
        base_questions = cls.RESEARCH_QUESTIONS.get(category, cls.RESEARCH_QUESTIONS['news'])
        research_questions = random.sample(base_questions, min(3, len(base_questions)))
        
        # Customize questions with specific context
        customized_questions = []
        for q in research_questions:
            customized = q.replace("this", topic.lower())
            if "disability" in q:
                customized = customized.replace("disability", disability_term.lower())
            customized_questions.append(customized)
        
        return article_title, article_angle, customized_questions
    
    @staticmethod
    def _extract_topic(title: str) -> str:
        """Extract main topic from article title"""
        # Remove common prefixes
        prefixes = ['The ', 'A ', 'An ', 'How ', 'Why ', 'What ', 'When ', 'Where ']
        for prefix in prefixes:
            if title.startswith(prefix):
                title = title[len(prefix):]
        
        # Extract first noun phrase (simplified)
        words = title.split()
        if len(words) > 5:
            return ' '.join(words[:4]) + '...'
        return title

# ============================================================================
# CONTENT ANALYZER
# ============================================================================

class ContentAnalyzer:
    """Analyzes content for disability references and generates findings"""
    
    def __init__(self):
        self.keywords = DISABILITY_KEYWORDS
        self.patterns = [re.compile(p, re.IGNORECASE) for p in DISABILITY_PATTERNS]
    
    def analyze_content(self, title: str, summary: str, full_text: str = "") -> Dict:
        """
        Analyze content for disability references
        Returns dict with keywords, context, and confidence score
        """
        text_to_analyze = f"{title} {summary} {full_text}".lower()
        
        # Find keywords
        found_keywords = []
        keyword_scores = []
        
        for keyword, base_score in self.keywords.items():
            if keyword.lower() in text_to_analyze:
                found_keywords.append(keyword)
                # Calculate score based on frequency and position
                frequency = text_to_analyze.count(keyword.lower())
                position_score = 1.0
                if keyword.lower() in title.lower():
                    position_score = 1.5
                elif keyword.lower() in summary.lower():
                    position_score = 1.2
                
                score = base_score * position_score * min(2.0, 1 + (frequency * 0.1))
                keyword_scores.append(score)
        
        # Check patterns
        pattern_matches = []
        for pattern in self.patterns:
            if pattern.search(text_to_analyze):
                pattern_matches.append(pattern.pattern)
        
        # Calculate confidence score
        confidence = 0.0
        if found_keywords:
            confidence = sum(keyword_scores) / len(keyword_scores)
            if pattern_matches:
                confidence *= 1.3  # Boost for pattern matches
        
        # Generate context
        context = self._generate_context(found_keywords, pattern_matches, text_to_analyze)
        
        return {
            'keywords': found_keywords,
            'pattern_matches': pattern_matches,
            'confidence': min(1.0, confidence),  # Cap at 1.0
            'context': context,
        }
    
    def _generate_context(self, keywords: List[str], patterns: List[str], text: str) -> str:
        """Generate human-readable context about the disability references"""
        if not keywords and not patterns:
            return "No direct disability references found"
        
        context_parts = []
        
        if keywords:
            if len(keywords) == 1:
                context_parts.append(f"Contains reference to '{keywords[0]}'")
            else:
                keyword_str = "', '".join(keywords[:-1]) + f"', and '{keywords[-1]}'"
                context_parts.append(f"Contains references to {keyword_str}")
        
        if patterns:
            pattern_desc = {
                r'struggle.*see': "mentions visual challenges",
                r'struggle.*hear': "mentions hearing challenges",
                r'cannot.*see': "describes visual limitations",
                r'cannot.*hear': "describes hearing limitations",
                r'exclude.*disability': "discusses exclusion of disabled people",
                r'design.*excluding': "describes exclusionary design",
                r'not.*accessible': "mentions accessibility barriers",
                r'work.*accommodation': "discusses workplace accommodations",
            }
            
            for pattern in patterns:
                for p, desc in pattern_desc.items():
                    if p in pattern:
                        context_parts.append(desc)
                        break
        
        return "; ".join(context_parts)

# ============================================================================
# RSS FEED READER
# ============================================================================

class RSSFeedReader:
    """Reads and parses RSS feeds from configured sources"""
    
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.user_agent = "DisabilityAIDiscoveryCrawler/1.0 (+https://disability-ai-collective.org)"
    
    async def fetch_feed(self, feed_url: str) -> List[Dict]:
        """Fetch and parse RSS feed"""
        try:
            headers = {'User-Agent': self.user_agent}
            async with self.session.get(feed_url, headers=headers, timeout=30) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch {feed_url}: HTTP {response.status}")
                    return []
                
                content = await response.text()
                feed = feedparser.parse(content)
                
                if feed.bozo:
                    logger.warning(f"Feed parsing error for {feed_url}: {feed.bozo_exception}")
                
                articles = []
                for entry in feed.entries[:20]:  # Limit to 20 most recent
                    article = {
                        'title': entry.get('title', ''),
                        'summary': entry.get('summary', ''),
                        'link': entry.get('link', ''),
                        'published': entry.get('published', ''),
                        'published_parsed': entry.get('published_parsed'),
                        'author': entry.get('author', ''),
                        'categories': [cat for cat in entry.get('tags', []) if hasattr(cat, 'term')],
                    }
                    articles.append(article)
                
                logger.info(f"Fetched {len(articles)} articles from {feed_url}")
                return articles
                
        except Exception as e:
            logger.error(f"Error fetching feed {feed_url}: {e}")
            return []
    
    async def fetch_article_content(self, url: str) -> str:
        """Fetch full article content from URL"""
        try:
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            async with self.session.get(url, headers=headers, timeout=30) as response:
                if response.status != 200:
                    return ""
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                
                # Try to find main content
                main_content = soup.find('article') or soup.find('main') or soup.find('div', class_=re.compile(r'content|article|post'))
                
                if main_content:
                    text = main_content.get_text(separator=' ', strip=True)
                else:
                    text = soup.get_text(separator=' ', strip=True)
                
                # Clean up text
                text = re.sub(r'\s+', ' ', text)
                return text[:5000]  # Limit length
                
        except Exception as e:
            logger.error(f"Error fetching article content {url}: {e}")
            return ""

# ============================================================================
# DATABASE MANAGER
# ============================================================================

class DatabaseManager:
    """Manages SQLite database for storing findings"""
    
    def __init__(self, db_path: str = "disability_findings.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create findings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS findings (
                    id TEXT PRIMARY KEY,
                    source_url TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    original_title TEXT NOT NULL,
                    original_summary TEXT,
                    publish_date TEXT,
                    discovered_at TEXT NOT NULL,
                    disability_keywords TEXT,
                    disability_context TEXT,
                    article_title TEXT NOT NULL,
                    article_angle TEXT,
                    research_questions TEXT,
                    assigned_agent TEXT,
                    confidence_score REAL,
                    tags TEXT,
                    raw_content_hash TEXT UNIQUE,
                    processed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create sources table for tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sources (
                    name TEXT PRIMARY KEY,
                    last_fetched TIMESTAMP,
                    fetch_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0
                )
            ''')
            
            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_findings_confidence 
                ON findings(confidence_score DESC)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_findings_discovered 
                ON findings(discovered_at DESC)
            ''')
            
            conn.commit()
    
    def save_finding(self, finding: ArticleFinding) -> bool:
        """Save a finding to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR IGNORE INTO findings (
                        id, source_url, source_name, original_title, original_summary,
                        publish_date, discovered_at, disability_keywords, disability_context,
                        article_title, article_angle, research_questions, assigned_agent,
                        confidence_score, tags, raw_content_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    finding.id,
                    finding.source_url,
                    finding.source_name,
                    finding.original_title,
                    finding.original_summary,
                    finding.publish_date,
                    finding.discovered_at,
                    json.dumps(finding.disability_keywords),
                    finding.disability_context,
                    finding.article_title,
                    finding.article_angle,
                    json.dumps(finding.research_questions),
                    finding.assigned_agent,
                    finding.confidence_score,
                    json.dumps(finding.tags),
                    finding.raw_content_hash,
                ))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error saving finding to database: {e}")
            return False
    
    def get_recent_findings(self, limit: int = 50) -> List[Dict]:
        """Get recent findings from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM findings 
                    ORDER BY discovered_at DESC 
                    LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting findings from database: {e}")
            return []
    
    def update_source_stats(self, source_name: str, success: bool = True):
        """Update source statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                now = datetime.now().isoformat()
                
                if success:
                    cursor.execute('''
                        INSERT INTO sources (name, last_fetched, fetch_count, success_count)
                        VALUES (?, ?, 1, 1)
                        ON CONFLICT(name) DO UPDATE SET
                            last_fetched = ?,
                            fetch_count = fetch_count + 1,
                            success_count = success_count + 1
                    ''', (source_name, now, now))
                else:
                    cursor.execute('''
                        INSERT INTO sources (name, last_fetched, fetch_count, error_count)
                        VALUES (?, ?, 1, 1)
                        ON CONFLICT(name) DO UPDATE SET
                            last_fetched = ?,
                            fetch_count = fetch_count + 1,
                            error_count = error_count + 1
                    ''', (source_name, now, now))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error updating source stats: {e}")

# ============================================================================
# MAIN CRAWLER CLASS
# ============================================================================

class DisabilityDiscoveryCrawler:
    """Main crawler orchestrator"""
    
    def __init__(self, configs: List[SourceConfig] = None):
        self.configs = configs or SOURCE_CONFIGS
        self.analyzer = ContentAnalyzer()
        self.db = DatabaseManager()
        self.idea_generator = ArticleIdeaGenerator()
        
        # Agents for assignment
        self.agents = [
            "Tech Accessibility Analyst",
            "Inclusive Design Researcher", 
            "Disability Policy Expert",
            "Assistive Technology Specialist",
            "Neurodiversity Advocate",
            "Universal Design Consultant",
            "Disability Culture Critic",
            "Accessibility Engineer",
        ]
    
    async def crawl_source(self, config: SourceConfig) -> List[ArticleFinding]:
        """Crawl a single source"""
        logger.info(f"Starting crawl for {config.name}")
        
        findings = []
        
        async with aiohttp.ClientSession() as session:
            reader = RSSFeedReader(session)
            
            # Fetch feed
            articles = await reader.fetch_feed(config.rss_url)
            
            for article in articles:
                try:
                    # Skip if no title
                    if not article['title'] or not article['link']:
                        continue
                    
                    # Fetch full content for better analysis
                    full_content = await reader.fetch_article_content(article['link'])
                    
                    # Analyze for disability references
                    analysis = self.analyzer.analyze_content(
                        article['title'],
                        article['summary'],
                        full_content
                    )
                    
                    # Skip if no disability references or low confidence
                    if not analysis['keywords'] and not analysis['pattern_matches']:
                        continue
                    
                    if analysis['confidence'] < 0.3:  # Minimum confidence threshold
                        continue
                    
                    # Generate article idea
                    article_title, article_angle, research_questions = \
                        self.idea_generator.generate_article_idea(
                            article['title'],
                            config.category,
                            analysis['keywords'],
                            analysis['context']
                        )
                    
                    # Create finding
                    finding = ArticleFinding(
                        id=self._generate_id(article['link']),
                        source_url=article['link'],
                        source_name=config.name,
                        original_title=article['title'][:500],
                        original_summary=article['summary'][:1000] if article['summary'] else "",
                        publish_date=article['published'] or "",
                        discovered_at=datetime.now().isoformat(),
                        disability_keywords=analysis['keywords'],
                        disability_context=analysis['context'],
                        article_title=article_title,
                        article_angle=article_angle,
                        research_questions=research_questions,
                        assigned_agent=random.choice(self.agents),
                        confidence_score=analysis['confidence'],
                        tags=[config.category] + analysis['keywords'][:3],
                        raw_content_hash=self._hash_content(article['title'] + article['summary']),
                    )
                    
                    # Save to database
                    if self.db.save_finding(finding):
                        findings.append(finding)
                        logger.info(f"Found disability angle in {config.name}: {article['title'][:50]}...")
                    
                    # Respect rate limiting between articles
                    await asyncio.sleep(config.rate_limit_seconds / 2)
                    
                except Exception as e:
                    logger.error(f"Error processing article from {config.name}: {e}")
                    continue
            
            # Update source stats
            self.db.update_source_stats(config.name, success=True)
            
            logger.info(f"Completed crawl for {config.name}: found {len(findings)} disability angles")
            return findings
    
    async def crawl_all_sources(self, max_concurrent: int = 3) -> List[ArticleFinding]:
        """Crawl all configured sources with concurrency control"""
        all_findings = []
        
        # Group sources by rate limit for better scheduling
        sources_by_rate = {}
        for config in self.configs:
            if config.enabled:
                rate = config.rate_limit_seconds
                sources_by_rate.setdefault(rate, []).append(config)
        
        # Process sources with similar rate limits together
        for rate, configs in sources_by_rate.items():
            logger.info(f"Processing {len(configs)} sources with rate limit {rate}s")
            
            # Process in batches
            for i in range(0, len(configs), max_concurrent):
                batch = configs[i:i + max_concurrent]
                tasks = [self.crawl_source(config) for config in batch]
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"Error in batch crawl: {result}")
                    elif isinstance(result, list):
                        all_findings.extend(result)
                
                # Wait between batches
                if i + max_concurrent < len(configs):
                    await asyncio.sleep(rate * 2)
        
        return all_findings
    
    def export_findings_json(self, findings: List[ArticleFinding], output_path: str = "findings.json"):
        """Export findings to JSON file"""
        try:
            data = {
                'export_date': datetime.now().isoformat(),
                'total_findings': len(findings),
                'findings': [finding.to_dict() for finding in findings]
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(findings)} findings to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting findings to JSON: {e}")
            return False
    
    def generate_report(self, findings: List[ArticleFinding]) -> str:
        """Generate a human-readable report"""
        if not findings:
            return "No disability angles found in this crawl."
        
        report = []
        report.append(f"# Disability-AI Discovery Crawler Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Findings: {len(findings)}")
        report.append("")
        
        # Group by source
        by_source = {}
        for finding in findings:
            by_source.setdefault(finding.source_name, []).append(finding)
        
        for source_name, source_findings in by_source.items():
            report.append(f"## {source_name} ({len(source_findings)} findings)")
            
            for finding in source_findings[:5]:  # Show top 5 per source
                report.append(f"### {finding.article_title}")
                report.append(f"**Original:** {finding.original_title[:100]}...")
                report.append(f"**Disability Angle:** {finding.article_angle}")
                report.append(f"**Keywords:** {', '.join(finding.disability_keywords[:3])}")
                report.append(f"**Assigned to:** {finding.assigned_agent}")
                report.append(f"**Confidence:** {finding.confidence_score:.2f}")
                report.append("")
        
        # Statistics
        report.append("## Statistics")
        
        # Top keywords
        all_keywords = []
        for finding in findings:
            all_keywords.extend(finding.disability_keywords)
        
        from collections import Counter
        keyword_counts = Counter(all_keywords)
        top_keywords = keyword_counts.most_common(10)
        
        report.append("### Top Disability Keywords")
        for keyword, count in top_keywords:
            report.append(f"- {keyword}: {count} articles")
        
        # Confidence distribution
        conf_scores = [f.confidence_score for f in findings]
        avg_confidence = sum(conf_scores) / len(conf_scores) if conf_scores else 0
        
        report.append(f"\n### Confidence Scores")
        report.append(f"- Average: {avg_confidence:.2f}")
        report.append(f"- High confidence (≥0.7): {sum(1 for s in conf_scores if s >= 0.7)}")
        report.append(f"- Medium confidence (0.4-0.69): {sum(1 for s in conf_scores if 0.4 <= s < 0.7)}")
        report.append(f"- Low confidence (0.3-0.39): {sum(1 for s in conf_scores if 0.3 <= s < 0.4)}")
        
        return "\n".join(report)
    
    @staticmethod
    def _generate_id(url: str) -> str:
        """Generate unique ID from URL"""
        return hashlib.md5(url.encode()).hexdigest()[:12]
    
    @staticmethod
    def _hash_content(content: str) -> str:
        """Generate hash for content deduplication"""
        return hashlib.sha256(content.encode()).hexdigest()

# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Disability-AI Discovery Crawler - Find disability angles in non-disability content"
    )
    parser.add_argument(
        '--sources', 
        nargs='+',
        help='Specific sources to crawl (by name)'
    )
    parser.add_argument(
        '--categories',
        nargs='+',
        choices=['tech', 'business', 'design', 'science', 'culture', 'news'],
        help='Categories to crawl'
    )
    parser.add_argument(
        '--max-concurrent',
        type=int,
        default=3,
        help='Maximum concurrent sources to crawl (default: 3)'
    )
    parser.add_argument(
        '--output-json',
        default='disability_findings.json',
        help='Output JSON file path (default: disability_findings.json)'
    )
    parser.add_argument(
        '--output-report',
        default='disability_report.md',
        help='Output report file path (default: disability_report.md)'
    )
    parser.add_argument(
        '--skip-db',
        action='store_true',
        help='Skip database storage (for testing)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting Disability-AI Discovery Crawler")
    logger.info(f"Python {sys.version}")
    
    # Filter sources if specified
    configs = SOURCE_CONFIGS
    
    if args.sources:
        configs = [c for c in configs if c.name in args.sources]
        logger.info(f"Filtered to {len(configs)} sources: {args.sources}")
    
    if args.categories:
        configs = [c for c in configs if c.category in args.categories]
        logger.info(f"Filtered to {len(configs)} categories: {args.categories}")
    
    if not configs:
        logger.error("No sources to crawl after filtering!")
        return
    
    # Create crawler
    crawler = DisabilityDiscoveryCrawler(configs)
    
    # Run crawl
    logger.info(f"Crawling {len(configs)} sources with max {args.max_concurrent} concurrent")
    
    start_time = time.time()
    findings = await crawler.crawl_all_sources(max_concurrent=args.max_concurrent)
    elapsed_time = time.time() - start_time
    
    logger.info(f"Crawl completed in {elapsed_time:.1f} seconds")
    logger.info(f"Found {len(findings)} disability angles")
    
    if not findings:
        logger.info("No disability angles found. Try different sources or categories.")
        return
    
    # Export findings
    if not args.skip_db:
        logger.info(f"Findings saved to database: disability_findings.db")
    
    # Export JSON
    if crawler.export_findings_json(findings, args.output_json):
        logger.info(f"Exported findings to {args.output_json}")
    
    # Generate and save report
    report = crawler.generate_report(findings)
    with open(args.output_report, 'w', encoding='utf-8') as f:
        f.write(report)
    logger.info(f"Generated report: {args.output_report}")
    
    # Print summary
    print("\n" + "="*60)
    print("DISABILITY-AI DISCOVERY CRAWLER - RESULTS SUMMARY")
    print("="*60)
    print(f"Sources crawled: {len(configs)}")
    print(f"Disability angles found: {len(findings)}")
    print(f"Time elapsed: {elapsed_time:.1f} seconds")
    print(f"Output files:")
    print(f"  - JSON findings: {args.output_json}")
    print(f"  - Markdown report: {args.output_report}")
    print(f"  - SQLite database: disability_findings.db")
    print("="*60)
    
    # Show top findings
    if findings:
        print("\nTOP 5 DISABILITY ANGLES FOUND:")
        print("-" * 40)
        
        sorted_findings = sorted(findings, key=lambda x: x.confidence_score, reverse=True)
        for i, finding in enumerate(sorted_findings[:5], 1):
            print(f"{i}. {finding.article_title}")
            print(f"   Source: {finding.source_name}")
            print(f"   Confidence: {finding.confidence_score:.2f}")
            print(f"   Keywords: {', '.join(finding.disability_keywords[:3])}")
            print()

# ============================================================================
# EXAMPLE USAGE AND DEMO
# ============================================================================

def run_example():
    """Run a quick example/demo of the crawler"""
    print("="*60)
    print("DISABILITY-AI DISCOVERY CRAWLER - DEMO")
    print("="*60)
    print("\nThis crawler finds disability angles in non-disability content.")
    print("\nExample transformations:")
    print("  TechCrunch: 'New AI Assistant Launches' →")
    print("    'How Voice-First AI Excludes Deaf Users'")
    print("  Bloomberg: 'Future of Remote Work' →")
    print("    'Remote Work Finally Includes Disabled Employees — Will It Last?'")
    print("  Dezeen: 'Minimalist Office Design' →")
    print("    'Minimalism as Sensory Exclusion'")
    print("\nTo run the full crawler:")
    print("  python disability_discovery_crawler.py")
    print("\nFor specific sources:")
    print("  python disability_discovery_crawler.py --sources TechCrunch Wired")
    print("\nFor specific categories:")
    print("  python disability_discovery_crawler.py --categories tech design")
    print("\nFor verbose output:")
    print("  python disability_discovery_crawler.py --verbose")
    print("="*60)

# ============================================================================
# CONFIGURATION AND SETUP
# ============================================================================

def check_dependencies():
    """Check if required dependencies are installed"""
    required = ['aiohttp', 'feedparser', 'beautifulsoup4']
    missing = []
    
    for package in required:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print("Missing dependencies. Install with:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    return True

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Check for help or example
    if len(sys.argv) == 1:
        run_example()
        sys.exit(0)
    
    if '--help' in sys.argv or '-h' in sys.argv:
        # Let argparse handle it
        pass
    elif '--example' in sys.argv:
        run_example()
        sys.exit(0)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Run main async function
    asyncio.run(main())