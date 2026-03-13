#!/usr/bin/env python3
"""
RSS Disability Crawler - Uses RSS feeds instead of search engines
Avoids DuckDuckGo blocking by accessing news sites directly via RSS
"""

import json
import sqlite3
import re
import urllib.request
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional
import html
import random
import time
import socket # Added for timeout handling

class RSSDisabilityCrawler:
    """
    RSS-based crawler for finding disability angles in quality journalism.
    Uses RSS feeds instead of search engines to avoid blocking.
    """
    
    def __init__(self):
        self.db_path = "disability_findings.db"  # Unified database
        self.findings = []
        self.visited_urls = set()
        self.init_database()
        
        # RSS FEEDS FOR QUALITY JOURNALISM
        self.rss_feeds = {
            'wired.com': [
                'https://www.wired.com/feed/',
                'https://www.wired.com/feed/category/ideas/latest/',
                'https://www.wired.com/feed/category/design/latest/',
                'https://www.wired.com/feed/category/business/latest/',
            ],
            'techcrunch.com': [
                'https://techcrunch.com/feed/',
                'https://techcrunch.com/category/artificial-intelligence/feed/',
                'https://techcrunch.com/category/startups/feed/',
                'https://techcrunch.com/category/security/feed/',
            ],
            'theverge.com': [
                'https://www.theverge.com/rss/index.xml',
                'https://www.theverge.com/tech/rss/index.xml',
                'https://www.theverge.com/design/rss/index.xml',
                'https://www.theverge.com/science/rss/index.xml',
            ],
            'fastcompany.com': [
                'https://www.fastcompany.com/feed',
                'https://www.fastcompany.com/work-life/feed',
                'https://www.fastcompany.com/innovation/feed',
            ],
            'bloomberg.com': [
                'https://www.bloomberg.com/feeds/podcasts/odd_lots.xml',  # Podcast feed
                'https://www.bloomberg.com/technology/rss/',
                'https://www.bloomberg.com/opinion/rss/',
            ],
            'nature.com': [
                'https://www.nature.com/nature.rss',
                'https://www.nature.com/articles.rss',
                'https://www.nature.com/news.rss',
            ],
            'theguardian.com': [
                'https://www.theguardian.com/technology/rss',
                'https://www.theguardian.com/science/rss',
                'https://www.theguardian.com/society/rss',
                'https://www.theguardian.com/culture/rss',
                'https://www.theguardian.com/education/rss',
            ],
            # DISABILITY ART & CULTURE SOURCES (PRIMARY FOCUS)
            'tangledarts.org': [
                'https://tangledarts.org/feed/',
            ],
            'sinsinvalid.org': [
                'https://sinsinvalid.org/feed/',
            ],
            'disabilityvisibilityproject.com': [
                'https://disabilityvisibilityproject.com/feed/',
            ],
            # Additional disability culture feeds
            'disabilityjustice.org': [
                'https://disabilityjustice.org/feed/',
            ],
            'cripstem.com': [
                'https://cripstem.com/feed/',
            ],
            'disabledwriters.com': [
                'https://disabledwriters.com/feed/',
            ],
            
            # MAINSTREAM ART & CULTURE SOURCES (SECONDARY)
            'hyperallergic.com': [
                'https://hyperallergic.com/feed/',
                'https://hyperallergic.com/category/art/feed/',
                'https://hyperallergic.com/category/culture/feed/',
            ],
            'artsy.net': [
                'https://www.artsy.net/rss/news',
                'https://www.artsy.net/rss/features',
            ],
            'artnews.com': [
                'https://www.artnews.com/feed/',
                'https://www.artnews.com/category/art-news/feed/',
            ],
            'artforum.com': [
                'https://www.artforum.com/feed/',
                'https://www.artforum.com/news/feed/',
            ],
            'dezeen.com': [
                'https://www.dezeen.com/feed/',
                'https://www.dezeen.com/architecture/feed/',
                'https://www.dezeen.com/design/feed/',
            ],
            'designboom.com': [
                'https://www.designboom.com/feed/',
                'https://www.designboom.com/architecture/feed/',
            ],
            'creativeboom.com': [
                'https://www.creativeboom.com/feed/',
                'https://www.creativeboom.com/illustration/feed/',
            ],
            # CULTURE & SOCIETY
            'nytimes.com': [
                'https://rss.nytimes.com/services/xml/rss/nyt/Arts.xml',
                'https://rss.nytimes.com/services/xml/rss/nyt/Design.xml',
                'https://rss.nytimes.com/services/xml/rss/nyt/Fashion.xml',
                'https://rss.nytimes.com/services/xml/rss/nyt/Theater.xml',
            ],
            'theguardian.com': [
                'https://www.theguardian.com/artanddesign/rss',
                'https://www.theguardian.com/culture/rss',
                'https://www.theguardian.com/stage/rss',
                'https://www.theguardian.com/film/rss',
                'https://www.theguardian.com/music/rss',
            ],
            'bbc.com': [
                'https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml',
                'https://feeds.bbci.co.uk/news/culture/rss.xml',
            ],
            # TECHNOLOGY FOR ART/CREATIVITY (secondary)
            'techcrunch.com': [
                'https://techcrunch.com/category/creativity/feed/',
            ],
            'wired.com': [
                'https://www.wired.com/feed/category/culture/latest/',
                'https://www.wired.com/feed/category/design/latest/',
            ],
        }
        
        # Disability concepts to look for in article bodies
        self.disability_concepts = {
            # Physical accessibility
            'physical': ['wheelchair', 'mobility', 'prosthetic', 'ramp', 'elevator', 'stairs', 'dance', 'movement', 'gesture'],
            
            # Sensory accessibility  
            'sensory': ['deaf', 'blind', 'hearing', 'vision', 'caption', 'audio', 'visual', 'tactile', 'haptic', 'texture', 'color', 'sound', 'music'],
            
            # Cognitive/neurodiversity
            'cognitive': ['neurodiverse', 'autistic', 'ADHD', 'dyslexia', 'cognitive', 'focus', 'pattern', 'rhythm', 'composition', 'improvisation'],
            
            # Communication
            'communication': ['speech', 'language', 'communication', 'interface', 'interaction', 'expression', 'narrative', 'storytelling', 'metaphor'],
            
            # Systemic barriers
            'systemic': ['barrier', 'access', 'inclusion', 'exclusion', 'marginalized', 'equity', 'representation', 'voice', 'agency', 'visibility'],
            
            # Design approaches
            'design': ['universal design', 'inclusive design', 'accessible', 'accommodation', 'aesthetic', 'form', 'function', 'beauty', 'ugliness'],
            
            # Art & Creativity
            'art': ['artist', 'painting', 'sculpture', 'performance', 'theater', 'film', 'photography', 'installation', 'exhibition', 'gallery', 'museum', 'curator'],
            
            # Cultural expression
            'culture': ['identity', 'community', 'tradition', 'innovation', 'subculture', 'mainstream', 'marginal', 'radical', 'conservative', 'progressive'],
        }
        
        # User agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        ]
    
    def init_database(self):
        """Initialize unified SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create unified findings table (same as in init_unified_database.py)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS findings (
            id TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            title TEXT NOT NULL,
            angle TEXT NOT NULL,
            confidence REAL NOT NULL,
            domain TEXT NOT NULL,
            source_type TEXT NOT NULL,  -- 'rss', 'web_crawl', 'api', 'manual'
            source_details TEXT NOT NULL,  -- JSON with source-specific info
            disability_concepts TEXT NOT NULL,  -- JSON array
            content_snippet TEXT NOT NULL,
            discovered_date TEXT NOT NULL,
            publish_date TEXT,
            status TEXT DEFAULT 'pending',
            processed_date TEXT,
            used_for_article BOOLEAN DEFAULT 0,
            article_id TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_random_user_agent(self):
        """Get random user agent"""
        return random.choice(self.user_agents)
    
    def fetch_rss_feed(self, rss_url: str) -> Optional[List[Dict]]:
        """Fetch and parse RSS feed"""
        print(f"  [RSS Fetch] Attempting to fetch: {rss_url}")
        
        try:
            headers = {
                'User-Agent': self.get_random_user_agent(),
                'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            }
            
            req = urllib.request.Request(rss_url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=15) as response:
                print(f"  [RSS Fetch] Received HTTP status: {response.status} for {rss_url}")
                if response.status == 200:
                    content = response.read().decode('utf-8', errors='ignore')
                    print(f"  [RSS Parse] Parsing content from: {rss_url}")
                    
                    # Parse RSS/Atom
                    articles = []
                    
                    try:
                        root = ET.fromstring(content)
                        
                        # Check if it's RSS
                        if root.tag == 'rss':
                            channel = root.find('channel')
                            if channel is not None:
                                for item in channel.findall('item'):
                                    article = self._parse_rss_item(item)
                                    if article:
                                        articles.append(article)
                        
                        # Check if it's Atom
                        elif '{http://www.w3.org/2005/Atom}' in root.tag:
                            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                                article = self._parse_atom_entry(entry)
                                if article:
                                    articles.append(article)
                        
                        print(f"  [RSS Parse] Found {len(articles)} articles from {rss_url}")
                        return articles
                        
                    except ET.ParseError as pe:
                        print(f"  [RSS Parse] XML ParseError for {rss_url}: {pe}. Trying regex fallback.")
                        return self._parse_rss_with_regex(content)
                    except Exception as e:
                        print(f"  [RSS Parse] Unexpected error during XML parsing for {rss_url}: {e}")
                        return []
                        
                else:
                    print(f"  [RSS Fetch] HTTP {response.status} for {rss_url}")
                    return []
                    
        except urllib.error.HTTPError as he:
            print(f"  [RSS Fetch] HTTP Error for {rss_url}: {he.code} {he.reason}")
            return []
        except urllib.error.URLError as ue:
            print(f"  [RSS Fetch] URL Error for {rss_url}: {ue.reason}")
            return []
        except socket.timeout:
            print(f"  [RSS Fetch] Timeout for {rss_url}")
            return []
        except Exception as e:
            print(f"  [RSS Fetch] General error for {rss_url}: {e}")
            return []
    
    def _parse_rss_item(self, item) -> Optional[Dict]:
        """Parse RSS item"""
        try:
            title_elem = item.find('title')
            link_elem = item.find('link')
            desc_elem = item.find('description')
            pubdate_elem = item.find('pubDate')
            
            if title_elem is not None and link_elem is not None:
                return {
                    'title': html.unescape(title_elem.text.strip() if title_elem.text else ''),
                    'url': link_elem.text.strip() if link_elem.text else '',
                    'description': html.unescape(desc_elem.text.strip() if desc_elem and desc_elem.text else ''),
                    'pub_date': pubdate_elem.text.strip() if pubdate_elem and pubdate_elem.text else '',
                }
        except:
            pass
        
        return None
    
    def _parse_atom_entry(self, entry) -> Optional[Dict]:
        """Parse Atom entry"""
        try:
            title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
            link_elem = entry.find('{http://www.w3.org/2005/Atom}link')
            summary_elem = entry.find('{http://www.w3.org/2005/Atom}summary')
            published_elem = entry.find('{http://www.w3.org/2005/Atom}published')
            
            if title_elem is not None:
                url = ''
                if link_elem is not None and 'href' in link_elem.attrib:
                    url = link_elem.attrib['href']
                
                return {
                    'title': html.unescape(title_elem.text.strip() if title_elem.text else ''),
                    'url': url,
                    'description': html.unescape(summary_elem.text.strip() if summary_elem and summary_elem.text else ''),
                    'pub_date': published_elem.text.strip() if published_elem and published_elem.text else '',
                }
        except:
            pass
        
        return None
    
    def _parse_rss_with_regex(self, content: str) -> List[Dict]:
        """Fallback: Parse RSS with regex"""
        articles = []
        
        # Simple regex for RSS items
        item_pattern = r'<item[^>]*>(.*?)</item>'
        items = re.findall(item_pattern, content, re.DOTALL)
        
        for item in items[:10]:  # Limit to 10 items
            try:
                # Extract title
                title_match = re.search(r'<title[^>]*>(.*?)</title>', item, re.DOTALL)
                title = html.unescape(title_match.group(1).strip()) if title_match else ''
                
                # Extract link
                link_match = re.search(r'<link[^>]*>(.*?)</link>', item, re.DOTALL)
                if not link_match:
                    link_match = re.search(r'<link[^>]*href="([^"]+)"', item)
                
                url = html.unescape(link_match.group(1).strip()) if link_match else ''
                
                # Extract description
                desc_match = re.search(r'<description[^>]*>(.*?)</description>', item, re.DOTALL)
                description = html.unescape(desc_match.group(1).strip()) if desc_match else ''
                
                if title and url:
                    articles.append({
                        'title': title,
                        'url': url,
                        'description': description,
                        'pub_date': '',
                    })
            except:
                continue
        
        return articles
    
    def fetch_webpage(self, url: str) -> Optional[str]:
        """Fetch webpage content"""
        try:
            headers = {
                'User-Agent': self.get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    content = response.read().decode('utf-8', errors='ignore')
                    return content
                else:
                    return None
                    
        except Exception as e:
            return None
    
    def extract_text_from_html(self, html_content: str) -> Dict[str, str]:
        """Extract text content from HTML"""
        if not html_content:
            return {'title': '', 'text': ''}
        
        # Extract title
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
        title = html.unescape(title_match.group(1).strip()) if title_match else ''
        
        # Remove scripts, styles
        cleaned = re.sub(r'<script[^>]*>.*?</script>', ' ', html_content, flags=re.DOTALL)
        cleaned = re.sub(r'<style[^>]*>.*?</style>', ' ', cleaned, flags=re.DOTALL)
        
        # Extract text from paragraphs and headings
        text_parts = []
        
        # Get headings (h1-h3)
        for tag in ['h1', 'h2', 'h3']:
            matches = re.findall(f'<{tag}[^>]*>(.*?)</{tag}>', cleaned, re.IGNORECASE | re.DOTALL)
            for match in matches:
                text = re.sub(r'<[^>]+>', ' ', match)
                text = html.unescape(text.strip())
                if text and len(text) > 10:
                    text_parts.append(text)
        
        # Get paragraphs
        p_matches = re.findall(r'<p[^>]*>(.*?)</p>', cleaned, re.IGNORECASE | re.DOTALL)
        for match in p_matches:
            text = re.sub(r'<[^>]+>', ' ', match)
            text = html.unescape(text.strip())
            if text and len(text) > 20:
                text_parts.append(text)
        
        full_text = ' '.join(text_parts)
        
        return {
            'title': title[:200] if title else '',
            'text': full_text[:4000] if full_text else ''
        }
    
    def analyze_for_disability_concepts(self, url: str, title: str, text: str, 
                                       domain: str, rss_feed: str) -> Optional[Dict]:
        """
        Analyze article for hidden disability concepts
        Returns None if no concepts found
        """
        if not text or len(text) < 200:
            return None
        
        text_lower = text.lower()
        title_lower = title.lower()
        
        # Look for disability concepts
        found_concepts = {}
        concept_contexts = {}
        
        for concept_type, keywords in self.disability_concepts.items():
            found_keywords = []
            
            for keyword in keywords:
                if keyword in text_lower:
                    found_keywords.append(keyword)
                    
                    # Find context around keyword
                    keyword_pos = text_lower.find(keyword)
                    if keyword_pos != -1:
                        start = max(0, keyword_pos - 100)
                        end = min(len(text_lower), keyword_pos + len(keyword) + 100)
                        context = text_lower[start:end].replace('\n', ' ').strip()
                        concept_contexts[f"{concept_type}:{keyword}"] = context
            
            if found_keywords:
                found_concepts[concept_type] = found_keywords
        
        if not found_concepts:
            return None
        
        # Direct disability keywords — must appear in title OR text (not just navigation)
        DIRECT_DISABILITY_KEYWORDS = [
            'deaf', 'blind', 'disability', 'disabled', 'wheelchair', 'prosthetic',
            'autistic', 'neurodivergent', 'accessibility', 'hearing loss',
            'visual impairment', 'mobility impairment', 'crip', 'sign language',
            'assistive tech', 'assistive technology', 'aac device', 'braille',
        ]

        # Check for at least 1 direct disability keyword in title or text
        has_direct_keyword = any(kw in title_lower or kw in text_lower for kw in DIRECT_DISABILITY_KEYWORDS)
        if not has_direct_keyword:
            return None

        # Boilerplate/navigation patterns — reject if keyword only appears in nav context
        NAV_PATTERNS = [
            r'(nav|navigation|menu|sidebar|footer|header|breadcrumb)[^.]{0,200}(deaf|blind|disability|disabled|wheelchair)',
            r'(deaf|blind|disability|disabled|wheelchair)[^.]{0,200}(nav|navigation|menu|sidebar|footer)',
        ]
        direct_in_body = False
        for kw in DIRECT_DISABILITY_KEYWORDS:
            if kw in title_lower:
                direct_in_body = True
                break
            if kw in text_lower:
                # Check it's not only in nav/boilerplate context
                kw_pos = text_lower.find(kw)
                context_window = text_lower[max(0, kw_pos - 150):min(len(text_lower), kw_pos + 150)]
                nav_words = ['navigation', 'sidebar', 'footer', 'menu', 'breadcrumb', 'related articles', 'see also']
                if not any(nw in context_window for nw in nav_words):
                    direct_in_body = True
                    break
        if not direct_in_body:
            return None

        # Calculate confidence
        concept_count = len(found_concepts)
        total_keywords = sum(len(keywords) for keywords in found_concepts.values())
        
        base_confidence = min(1.0, (concept_count * 0.2) + (total_keywords * 0.1))
        
        # Boost for concepts in title
        title_concepts = 0
        for concept_type, keywords in found_concepts.items():
            for keyword in keywords:
                if keyword in title_lower:
                    title_concepts += 1
        
        if title_concepts > 0:
            base_confidence *= 1.3
        
        # Boost if direct disability keyword in title
        if any(kw in title_lower for kw in DIRECT_DISABILITY_KEYWORDS):
            base_confidence = max(base_confidence, 0.7)
        
        # Generate article idea
        article_idea = self._generate_article_idea(title, found_concepts, domain)
        
        if article_idea and base_confidence > 0.6:
            return {
                'url': url,
                'title': title,
                'domain': domain,
                'rss_feed': rss_feed,
                'disability_concepts': found_concepts,
                'concept_contexts': concept_contexts,
                'confidence': min(1.0, base_confidence),
                'article_idea': article_idea,
                'content_snippet': text[:300] + '...' if len(text) > 300 else text,
                'publish_date': datetime.now().isoformat()
            }
        
        return None
    
    def _generate_article_idea(self, original_title: str, 
                              found_concepts: Dict[str, List[str]],
                              domain: str) -> Optional[str]:
        """Generate article idea based on found concepts"""
        if not found_concepts:
            return None
        
        # Clean title
        clean_title = re.sub(r' - [^-]+$', '', original_title)
        clean_title = re.sub(r' \| [^|]+$', '', clean_title)
        short_title = clean_title[:60] + '...' if len(clean_title) > 60 else clean_title
        
        primary_concept = list(found_concepts.keys())[0]
        primary_keyword = found_concepts[primary_concept][0].title()
        
        # Simple templates
        templates = [
            f"The {primary_keyword} Perspective on '{short_title}'",
            f"What '{short_title}' Misses About {primary_keyword}",
            f"Inclusive Analysis: The {primary_keyword} Dimension of '{short_title}'",
            f"Disability Insight: How '{short_title}' Affects {primary_keyword} Communities",
            f"Accessibility Critique: The {primary_keyword} Story Behind '{short_title}'",
        ]
        
        import random
        return random.choice(templates)
    
    def save_finding(self, finding: Dict):
        """Save finding to database and JSON"""
        # Generate ID
        import hashlib
        finding_id = hashlib.md5(finding['url'].encode()).hexdigest()
        
        # Check if already exists
        if finding_id in self.visited_urls:
            return False
        
        # Add to visited
        self.visited_urls.add(finding_id)
        
        # Add metadata
        finding['id'] = finding_id
        finding['discovered_date'] = datetime.now().isoformat()
        finding['status'] = 'pending'
        
        # Save to unified database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert to unified format
        # Extract angle from article_idea or generate from title
        angle = finding.get('article_idea', '')
        if not angle:
            angle = f"Disability perspective on: {finding['title'][:50]}..."
        
        # Convert disability concepts to JSON array
        disability_concepts_list = []
        for concept_type, keywords in finding.get('disability_concepts', {}).items():
            disability_concepts_list.extend(keywords)
        
        # Prepare source details JSON
        source_details = {
            'rss_feed': finding.get('rss_feed', ''),
            'concept_contexts': finding.get('concept_contexts', {})
        }
        
        cursor.execute('''
        INSERT OR REPLACE INTO findings 
        (id, url, title, angle, confidence, domain, source_type, 
         source_details, disability_concepts, content_snippet, 
         discovered_date, publish_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            finding['id'],
            finding['url'],
            finding['title'],
            angle,
            finding['confidence'],
            finding['domain'],
            'rss',  # source_type
            json.dumps(source_details),
            json.dumps(list(set(disability_concepts_list))),
            finding['content_snippet'],
            finding['discovered_date'],
            finding.get('publish_date', ''),
            finding['status']
        ))
        
        conn.commit()
        conn.close()
        
        # Add to findings list
        self.findings.append(finding)
        
        return True
    
    def run_rss_crawl(self, max_feeds: int = 3, max_articles_per_feed: int = 5):
        """Run RSS crawl across feeds"""
        print("=== RSS Disability Crawler ===")
        print(f"Starting crawl at {datetime.now().isoformat()}")
        print(f"Targeting {max_feeds} RSS feeds with {max_articles_per_feed} articles each")
        print()
        
        total_findings = 0
        
        # Process each domain
        for domain, feeds in self.rss_feeds.items():
            if len(feeds) == 0:
                continue
            
            print(f"Processing domain: {domain}")
            
            # Try each feed until we get articles
            for rss_feed in feeds[:2]:  # Try first 2 feeds
                print(f"[Crawler Run] Attempting to fetch RSS feed: {rss_feed}")
                articles = self.fetch_rss_feed(rss_feed)
                
                if not articles:
                    print(f"[Crawler Run] No articles from {rss_feed}, trying next feed.")
                    continue
                
                print(f"  Analyzing {len(articles)} articles from RSS feed {rss_feed}")
                
                # Process articles
                for article in articles[:max_articles_per_feed]:
                    url = article['url']
                    title = article['title']
                    
                    # Skip if no URL
                    if not url:
                        print(f"[Crawler Run] Skipping article with no URL: {title}")
                        continue
                    
                    # Fetch webpage
                    print(f"[Crawler Run] Attempting to fetch webpage: {url}")
                    html_content = self.fetch_webpage(url)
                    if not html_content:
                        print(f"[Crawler Run] No HTML content from {url}, skipping.")
                    
                    # Extract text
                    extracted = self.extract_text_from_html(html_content)
                    if not extracted['text']:
                        # Use description if no text extracted
                        extracted['text'] = article.get('description', '')
                    
                    if not extracted['text'] or len(extracted['text']) < 100:
                        continue
                    
                    # Use RSS title if no HTML title
                    if not extracted['title']:
                        extracted['title'] = title
                    
                    # Analyze for disability concepts
                    finding = self.analyze_for_disability_concepts(
                        url, extracted['title'], extracted['text'], 
                        domain, rss_feed
                    )
                    
                    if finding:
                        # Save finding
                        if self.save_finding(finding):
                            total_findings += 1
                            print(f"    ✓ Found disability angle: {finding['article_idea']}")
                            print(f"      Confidence: {finding['confidence']:.2f}")
                    
                    # Small delay between articles
                    time.sleep(1)
                
                # If we processed articles from this feed, move to next domain
                break
            
            print()
        
        # Save findings to JSON
        if self.findings:
            with open('rss_disability_findings.json', 'w') as f:
                json.dump(self.findings, f, indent=2)
            
            # Generate report
            self.generate_report()
        
        print(f"=== RSS Crawl Complete ===")
        print(f"Total findings: {total_findings}")
        print(f"Saved to: rss_disability_findings.json, rss_disability_findings.db")
        
        return total_findings
    
    def generate_report(self):
        """Generate human-readable report"""
        if not self.findings:
            return
        
        report_lines = [
            "# RSS Disability Crawler Report",
            f"Generated: {datetime.now().isoformat()}",
            f"Total Findings: {len(self.findings)}",
            "",
            "## Summary by Domain",
        ]
        
        # Group by domain
        domain_stats = {}
        for finding in self.findings:
            domain = finding['domain']
            if domain not in domain_stats:
                domain_stats[domain] = {
                    'count': 0,
                    'avg_confidence': 0,
                    'feeds': set()
                }
            
            stats = domain_stats[domain]
            stats['count'] += 1
            stats['avg_confidence'] += finding['confidence']
            stats['feeds'].add(finding['rss_feed'])
        
        # Calculate averages
        for domain in domain_stats:
            stats = domain_stats[domain]
            stats['avg_confidence'] /= stats['count']
            
            report_lines.append(f"### {domain}")
            report_lines.append(f"- Articles found: {stats['count']}")
            report_lines.append(f"- Average confidence: {stats['avg_confidence']:.2f}")
            report_lines.append(f"- RSS Feeds used: {', '.join(list(stats['feeds'])[:2])}")
            report_lines.append("")
        
        report_lines.append("## Detailed Findings")
        report_lines.append("")
        
        for i, finding in enumerate(self.findings, 1):
            report_lines.append(f"### Finding {i}: {finding['article_idea']}")
            report_lines.append(f"- **URL**: {finding['url']}")
            report_lines.append(f"- **Original Title**: {finding['title']}")
            report_lines.append(f"- **Domain**: {finding['domain']}")
            report_lines.append(f"- **RSS Feed**: {finding['rss_feed']}")
            report_lines.append(f"- **Confidence**: {finding['confidence']:.2f}")
            report_lines.append("")
            
            # Disability concepts found
            report_lines.append("**Disability Concepts Found:**")
            for concept_type, keywords in finding['disability_concepts'].items():
                report_lines.append(f"- {concept_type}: {', '.join(keywords)}")
            
            report_lines.append("")
            report_lines.append("**Content Snippet:**")
            report_lines.append(f"> {finding['content_snippet']}")
            report_lines.append("")
        
        # Write report
        with open('rss_disability_findings_report.md', 'w') as f:
            f.write('\n'.join(report_lines))
        
        print(f"Report generated: rss_disability_findings_report.md")


def main():
    """Main function"""
    print("Starting RSS Disability Crawler...")
    
    # Create crawler
    crawler = RSSDisabilityCrawler()
    
    # Run crawl
    findings = crawler.run_rss_crawl(max_feeds=3, max_articles_per_feed=3)
    
    if findings > 0:
        print(f"\nSuccessfully found {findings} disability angles via RSS feeds!")
        print("Check the generated files for details.")
    else:
        print("\nNo disability angles found via RSS.")
        print("This could mean:")
        print("1. Current articles don't contain disability concepts")
        print("2. RSS feeds might be blocked or have different formats")
        print("3. Network connectivity issues")
    
    return findings


if __name__ == "__main__":
    main()
