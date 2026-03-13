#!/usr/bin/env python3
"""
Smart Disability Search Crawler - Intelligent Search Strategy
Uses domain-specific knowledge to find hidden disability angles in quality journalism
"""

import json
import sqlite3
import re
import urllib.request
import urllib.error
import urllib.parse
import socket
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import html
import random

class SmartDisabilitySearch:
    """
    Intelligent search strategy for finding disability angles in quality journalism.
    
    Key insights:
    1. Don't search for disability terms directly (that finds disability-focused content)
    2. Search for mainstream topics that likely contain disability angles
    3. Use specific, high-quality source domains
    4. Look for disability concepts in article bodies, not titles
    """
    
    def __init__(self):
        self.db_path = "smart_disability_findings.db"
        self.findings = []
        self.visited_urls = set()
        self.init_database()
        
        # DOMAIN-SPECIFIC SEARCH STRATEGIES
        # Each domain has specific search patterns that work best
        
        self.domain_strategies = {
            # Tech journalism - look for accessibility angles in tech news
            'techcrunch.com': {
                'search_patterns': [
                    'site:techcrunch.com "AI" "voice"',
                    'site:techcrunch.com "interface" "design"',
                    'site:techcrunch.com "startup" "health"',
                    'site:techcrunch.com "app" "communication"',
                ],
                'quality_score': 0.9,
                'description': 'Tech journalism with potential accessibility angles'
            },
            
            'wired.com': {
                'search_patterns': [
                    'site:wired.com "design" "future"',
                    'site:wired.com "technology" "human"',
                    'site:wired.com "innovation" "inclusion"',
                    'site:wired.com "interface" "experience"',
                ],
                'quality_score': 0.95,
                'description': 'High-quality tech/culture journalism'
            },
            
            'theverge.com': {
                'search_patterns': [
                    'site:theverge.com "design" "review"',
                    'site:theverge.com "interface" "usability"',
                    'site:theverge.com "app" "access"',
                ],
                'quality_score': 0.85,
                'description': 'Tech reviews with design focus'
            },
            
            # Design/Architecture - look for universal design angles
            'dezeen.com': {
                'search_patterns': [
                    'site:dezeen.com "architecture" "public"',
                    'site:dezeen.com "design" "space"',
                    'site:dezeen.com "urban" "planning"',
                ],
                'quality_score': 0.9,
                'description': 'Architecture/design journalism'
            },
            
            'archdaily.com': {
                'search_patterns': [
                    'site:archdaily.com "building" "access"',
                    'site:archdaily.com "design" "public"',
                    'site:archdaily.com "urban" "mobility"',
                ],
                'quality_score': 0.85,
                'description': 'Architecture projects and theory'
            },
            
            # Business/Workplace - look for neurodiversity/accessibility angles
            'bloomberg.com': {
                'search_patterns': [
                    'site:bloomberg.com "workplace" "future"',
                    'site:bloomberg.com "hiring" "diversity"',
                    'site:bloomberg.com "office" "design"',
                ],
                'quality_score': 0.9,
                'description': 'Business journalism with workplace focus'
            },
            
            'fastcompany.com': {
                'search_patterns': [
                    'site:fastcompany.com "work" "innovation"',
                    'site:fastcompany.com "design" "business"',
                    'site:fastcompany.com "future" "workplace"',
                ],
                'quality_score': 0.8,
                'description': 'Business innovation journalism'
            },
            
            # Science/Health - look for assistive tech angles
            'nature.com': {
                'search_patterns': [
                    'site:nature.com "technology" "health"',
                    'site:nature.com "device" "medical"',
                    'site:nature.com "innovation" "therapy"',
                ],
                'quality_score': 0.95,
                'description': 'Scientific research with tech applications'
            },
            
            'sciencedaily.com': {
                'search_patterns': [
                    'site:sciencedaily.com "new" "device"',
                    'site:sciencedaily.com "technology" "help"',
                    'site:sciencedaily.com "innovation" "medical"',
                ],
                'quality_score': 0.8,
                'description': 'Science news with tech focus'
            },
            
            # Culture/Entertainment - look for representation angles
            'variety.com': {
                'search_patterns': [
                    'site:variety.com "casting" "representation"',
                    'site:variety.com "film" "inclusion"',
                    'site:variety.com "entertainment" "diversity"',
                ],
                'quality_score': 0.85,
                'description': 'Entertainment industry journalism'
            },
            
            'theguardian.com': {
                'search_patterns': [
                    'site:theguardian.com "culture" "technology"',
                    'site:theguardian.com "society" "future"',
                    'site:theguardian.com "life" "digital"',
                ],
                'quality_score': 0.9,
                'description': 'Quality journalism across topics'
            },
        }
        
        # Disability concepts to look for in article bodies
        # These are NOT search terms - they're what we analyze FOR
        self.disability_concepts = {
            # Physical accessibility
            'physical': ['wheelchair', 'mobility', 'prosthetic', 'ramp', 'elevator', 'stairs'],
            
            # Sensory accessibility  
            'sensory': ['deaf', 'blind', 'hearing', 'vision', 'caption', 'audio', 'visual'],
            
            # Cognitive/neurodiversity
            'cognitive': ['neurodiverse', 'autistic', 'ADHD', 'dyslexia', 'cognitive', 'focus'],
            
            # Communication
            'communication': ['speech', 'language', 'communication', 'interface', 'interaction'],
            
            # Systemic barriers
            'systemic': ['barrier', 'access', 'inclusion', 'exclusion', 'marginalized', 'equity'],
            
            # Design approaches
            'design': ['universal design', 'inclusive design', 'accessible', 'accommodation'],
        }
        
        # User agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        ]
    
    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS smart_findings (
            id TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            title TEXT NOT NULL,
            domain TEXT NOT NULL,
            domain_strategy TEXT NOT NULL,
            search_pattern TEXT NOT NULL,
            disability_concepts TEXT NOT NULL,
            concept_contexts TEXT NOT NULL,
            confidence REAL NOT NULL,
            article_idea TEXT NOT NULL,
            discovered_date TEXT NOT NULL,
            content_snippet TEXT NOT NULL,
            quality_score REAL NOT NULL,
            status TEXT DEFAULT 'pending'
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_random_user_agent(self):
        """Get random user agent"""
        return random.choice(self.user_agents)
    
    def smart_search_duckduckgo(self, domain: str, search_pattern: str) -> List[str]:
        """
        Perform intelligent DuckDuckGo search for a specific domain and pattern
        """
        print(f"  Smart search: {domain} - '{search_pattern}'")
        
        try:
            # URL encode the search pattern
            encoded_query = urllib.parse.quote(search_pattern)
            search_url = f"https://duckduckgo.com/html/?q={encoded_query}"
            
            headers = {
                'User-Agent': self.get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            req = urllib.request.Request(search_url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status == 200:
                    content = response.read().decode('utf-8', errors='ignore')
                    
                    # Extract result links
                    urls = []
                    
                    # DuckDuckGo result pattern
                    result_pattern = r'class="result__url"[^>]*>.*?href="([^"]+)"'
                    matches = re.findall(result_pattern, content, re.DOTALL)
                    
                    for match in matches[:5]:  # Limit to 5 results
                        url = match.strip()
                        if url.startswith('//'):
                            url = 'https:' + url
                        
                        # Filter for our target domain
                        if domain in url:
                            # Filter out non-article URLs
                            if not any(ext in url.lower() for ext in ['.pdf', '.jpg', '.png', '.zip', '.mp4']):
                                urls.append(url)
                    
                    print(f"    Found {len(urls)} articles from {domain}")
                    return urls
                else:
                    print(f"    HTTP {response.status}")
                    return []
                    
        except Exception as e:
            print(f"    Search error: {e}")
            return []
    
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
            'title': title[:200],
            'text': full_text[:4000]  # More text for better analysis
        }
    
    def analyze_for_disability_concepts(self, url: str, title: str, text: str, 
                                       domain: str, search_pattern: str) -> Optional[Dict]:
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
        
        # Calculate confidence based on:
        # 1. Number of concept types found
        # 2. Number of keywords per concept
        # 3. Whether concepts are in title
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
        
        # Generate intelligent article idea
        article_idea = self._generate_smart_article_idea(
            title, found_concepts, domain, search_pattern
        )
        
        if article_idea and base_confidence > 0.4:
            quality_score = self.domain_strategies.get(domain, {}).get('quality_score', 0.5)
            
            return {
                'url': url,
                'title': title,
                'domain': domain,
                'domain_strategy': self.domain_strategies.get(domain, {}).get('description', 'unknown'),
                'search_pattern': search_pattern,
                'disability_concepts': found_concepts,
                'concept_contexts': concept_contexts,
                'confidence': min(1.0, base_confidence),
                'article_idea': article_idea,
                'content_snippet': text[:300] + '...' if len(text) > 300 else text,
                'quality_score': quality_score
            }
        
        return None
    
    def _generate_smart_article_idea(self, original_title: str, 
                                    found_concepts: Dict[str, List[str]],
                                    domain: str, search_pattern: str) -> Optional[str]:
        """
        Generate intelligent article idea based on found concepts and context
        """
        # Clean title
        clean_title = re.sub(r' - [^-]+$', '', original_title)
        clean_title = re.sub(r' \| [^|]+$', '', clean_title)
        short_title = clean_title[:60] + '...' if len(clean_title) > 60 else clean_title
        
        # Determine primary concept type
        if not found_concepts:
            return None
        
        primary_concept = list(found_concepts.keys())[0]
        primary_keyword = found_concepts[primary_concept][0].title()
        
        # Domain-specific templates
        domain_templates = {
            'techcrunch.com': [
                f"How '{short_title}' Reveals Unseen {primary_keyword} Barriers in Tech",
                f"The {primary_keyword} Blind Spot in Tech Innovation: What '{short_title}' Misses",
                f"Disability Expertise Reads '{short_title}' Differently: A {primary_keyword} Tech Critique",
            ],
            'wired.com': [
                f"The {primary_keyword} Dimension of '{short_title}': What Tech Culture Overlooks",
                f"Beyond the Interface: How '{short_title}' Affects {primary_keyword} Communities",
                f"Disability Futures: What '{short_title}' Gets Wrong About {primary_keyword}",
            ],
            'theverge.com': [
                f"The {primary_keyword} Review: What '{short_title}' Misses About Usability",
                f"Accessibility Audit: How '{short_title}' Fails {primary_keyword} Users",
                f"Designing for Difference: The {primary_keyword} Perspective on '{short_title}'",
            ],
            'dezeen.com': [
                f"Architecture's {primary_keyword} Problem: What '{short_title}' Doesn't Show",
                f"The Space Between: How '{short_title}' Excludes {primary_keyword} Bodies",
                f"Universal Design Failure: The {primary_keyword} Critique of '{short_title}'",
            ],
            'archdaily.com': [
                f"Building Barriers: The {primary_keyword} Reality Behind '{short_title}'",
                f"Architecture's Accessibility Gap: The {primary_keyword} Story Missing from '{short_title}'",
                f"Designing for All: What '{short_title}' Forgets About {primary_keyword}",
            ],
            'bloomberg.com': [
                f"The {primary_keyword} Cost: What '{short_title}' Misses About Workplace Inclusion",
                f"Business Blind Spot: How '{short_title}' Ignores {primary_keyword} Economics",
                f"Corporate Accessibility: The {primary_keyword} Perspective on '{short_title}'",
            ],
            'fastcompany.com': [
                f"Innovation's {primary_keyword} Problem: What '{short_title}' Gets Wrong",
                f"Designing for Diversity: The {primary_keyword} Critique of '{short_title}'",
                f"Future of Work: What '{short_title}' Forgets About {primary_keyword}",
            ],
            'nature.com': [
                f"Science's {primary_keyword} Gap: What '{short_title}' Overlooks",
                f"Research Accessibility: The {primary_keyword} Dimension of '{short_title}'",
                f"Inclusive Science: What '{short_title}' Misses About {primary_keyword}",
            ],
            'sciencedaily.com': [
                f"Technology's {primary_keyword} Blind Spot: What '{short_title}' Ignores",
                f"Assistive Innovation: The {primary_keyword} Story Behind '{short_title}'",
                f"Science for All: What '{short_title}' Forgets About {primary_keyword}",
            ],
            'variety.com': [
                f"Representation's {primary_keyword} Problem: What '{short_title}' Misses",
                f"Inclusive Entertainment: The {primary_keyword} Critique of '{short_title}'",
                f"Hollywood's Blind Spot: What '{short_title}' Forgets About {primary_keyword}",
            ],
            'theguardian.com': [
                f"Society's {primary_keyword} Gap: What '{short_title}' Overlooks",
                f"Inclusive Futures: The {primary_keyword} Perspective on '{short_title}'",
                f"Cultural Accessibility: What '{short_title}' Misses About {primary_keyword}",
            ],
        }
        
        # Get template for domain or use default
        templates = domain_templates.get(domain, [
            f"The {primary_keyword} Perspective on '{short_title}'",
            f"What '{short_title}' Misses About {primary_keyword}",
            f"Inclusive Analysis: The {primary_keyword} Dimension of '{short_title}'",
        ])
        
        # Return random template
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
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO smart_findings 
        (id, url, title, domain, domain_strategy, search_pattern, disability_concepts, 
         concept_contexts, confidence, article_idea, discovered_date, content_snippet, 
         quality_score, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            finding['id'],
            finding['url'],
            finding['title'],
            finding['domain'],
            finding['domain_strategy'],
            finding['search_pattern'],
            json.dumps(finding['disability_concepts']),
            json.dumps(finding['concept_contexts']),
            finding['confidence'],
            finding['article_idea'],
            finding['discovered_date'],
            finding['content_snippet'],
            finding['quality_score'],
            finding['status']
        ))
        
        conn.commit()
        conn.close()
        
        # Add to findings list
        self.findings.append(finding)
        
        return True
    
    def run_smart_search(self, max_domains: int = 3, max_searches_per_domain: int = 2):
        """Run intelligent search across domains"""
        print("=== Smart Disability Search Crawler ===")
        print(f"Starting search at {datetime.now().isoformat()}")
        print(f"Targeting {max_domains} domains with {max_searches_per_domain} searches each")
        print()
        
        # Select random domains
        domains = list(self.domain_strategies.keys())
        random.shuffle(domains)
        selected_domains = domains[:max_domains]
        
        total_findings = 0
        
        for domain in selected_domains:
            print(f"Searching domain: {domain}")
            print(f"  Strategy: {self.domain_strategies[domain]['description']}")
            
            # Get search patterns for this domain
            search_patterns = self.domain_strategies[domain]['search_patterns']
            selected_patterns = search_patterns[:max_searches_per_domain]
            
            for search_pattern in selected_patterns:
                # Perform search
                urls = self.smart_search_duckduckgo(domain, search_pattern)
                
                for url in urls:
                    # Fetch webpage
                    html_content = self.fetch_webpage(url)
                    if not html_content:
                        continue
                    
                    # Extract text
                    extracted = self.extract_text_from_html(html_content)
                    if not extracted['text']:
                        continue
                    
                    # Analyze for disability concepts
                    finding = self.analyze_for_disability_concepts(
                        url, extracted['title'], extracted['text'], 
                        domain, search_pattern
                    )
                    
                    if finding:
                        # Save finding
                        if self.save_finding(finding):
                            total_findings += 1
                            print(f"    ✓ Found disability angle: {finding['article_idea']}")
                            print(f"      Confidence: {finding['confidence']:.2f}, Quality: {finding['quality_score']:.2f}")
                
                # Small delay between searches
                time.sleep(2)
            
            print()
        
        # Save findings to JSON
        if self.findings:
            with open('smart_disability_findings.json', 'w') as f:
                json.dump(self.findings, f, indent=2)
            
            # Generate report
            self.generate_report()
        
        print(f"=== Search Complete ===")
        print(f"Total findings: {total_findings}")
        print(f"Saved to: smart_disability_findings.json, smart_disability_findings.db")
        
        return total_findings
    
    def generate_report(self):
        """Generate human-readable report"""
        if not self.findings:
            return
        
        report_lines = [
            "# Smart Disability Search Report",
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
                    'avg_quality': 0,
                    'strategies': set()
                }
            
            stats = domain_stats[domain]
            stats['count'] += 1
            stats['avg_confidence'] += finding['confidence']
            stats['avg_quality'] += finding['quality_score']
            stats['strategies'].add(finding['domain_strategy'])
        
        # Calculate averages
        for domain in domain_stats:
            stats = domain_stats[domain]
            stats['avg_confidence'] /= stats['count']
            stats['avg_quality'] /= stats['count']
            
            report_lines.append(f"### {domain}")
            report_lines.append(f"- Articles found: {stats['count']}")
            report_lines.append(f"- Average confidence: {stats['avg_confidence']:.2f}")
            report_lines.append(f"- Average quality score: {stats['avg_quality']:.2f}")
            report_lines.append(f"- Strategy: {', '.join(stats['strategies'])}")
            report_lines.append("")
        
        report_lines.append("## Detailed Findings")
        report_lines.append("")
        
        for i, finding in enumerate(self.findings, 1):
            report_lines.append(f"### Finding {i}: {finding['article_idea']}")
            report_lines.append(f"- **URL**: {finding['url']}")
            report_lines.append(f"- **Original Title**: {finding['title']}")
            report_lines.append(f"- **Domain**: {finding['domain']}")
            report_lines.append(f"- **Search Pattern**: {finding['search_pattern']}")
            report_lines.append(f"- **Confidence**: {finding['confidence']:.2f}")
            report_lines.append(f"- **Quality Score**: {finding['quality_score']:.2f}")
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
        with open('smart_disability_findings_report.md', 'w') as f:
            f.write('\n'.join(report_lines))
        
        print(f"Report generated: smart_disability_findings_report.md")


def main():
    """Main function"""
    print("Starting Smart Disability Search Crawler...")
    
    # Create crawler
    crawler = SmartDisabilitySearch()
    
    # Run search
    findings = crawler.run_smart_search(max_domains=3, max_searches_per_domain=2)
    
    if findings > 0:
        print(f"\nSuccessfully found {findings} disability angles in quality journalism!")
        print("Check the generated files for details.")
    else:
        print("\nNo disability angles found. Try adjusting search patterns or domains.")
    
    return findings


if __name__ == "__main__":
    main()