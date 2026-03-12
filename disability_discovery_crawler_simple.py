#!/usr/bin/env python3
"""
Disability Discovery Crawler - Simplified Version (Standard Library Only)
Finds disability angles in non-disability journalism without external dependencies
"""

import json
import sqlite3
import re
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET

class SimplifiedDisabilityCrawler:
    """Crawls for disability angles in non-disability content using only stdlib"""
    
    def __init__(self, db_path="disability_findings.db"):
        self.db_path = db_path
        self.findings = []
        self.init_database()
        
        # Keywords that indicate disability-related content
        self.disability_keywords = {
            'prosthetic', 'wheelchair', 'deaf', 'blind', 'neurodiverse', 'autistic',
            'accessibility', 'inclusive', 'assistive', 'disability', 'accommodation',
            'sensory', 'cognitive', 'mobility', 'hearing', 'vision', 'marginalized',
            'barrier', 'disabled', 'ADL', 'neurodivergent', 'ADHD', 'dyslexia',
            'cp', 'cerebral palsy', 'MS', 'OCD', 'bipolar', 'depression',
            'anxiety', 'PTSD', 'chronic illness', 'chronic pain'
        }
        
        # Non-disability sources to check
        self.sources = {
            'tech': [
                'https://techcrunch.com/feed/',
                'https://www.theverge.com/rss/index.xml',
            ],
            'business': [
                'https://feeds.bloomberg.com/markets/news.rss',
                'https://feeds.ft.com/home/rss',
            ],
            'design': [
                'https://www.dezeen.com/feed/',
                'https://feeds.fastcompany.com/fastcompany',
            ],
            'science': [
                'https://feeds.nature.com/nature/rss/current',
                'https://www.newscientist.com/feed/science/',
            ],
            'culture': [
                'https://feeds.bloomberg.com/entertainment/news.rss',
                'https://www.hollywoodreporter.com/feed',
            ]
        }
    
    def init_database(self):
        """Initialize SQLite database for storing findings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS findings (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_name TEXT NOT NULL,
            original_topic TEXT NOT NULL,
            disability_angle TEXT NOT NULL,
            keywords TEXT NOT NULL,
            confidence REAL NOT NULL,
            discovered_date TEXT NOT NULL,
            article_idea TEXT NOT NULL,
            research_questions TEXT NOT NULL,
            suggested_agent TEXT NOT NULL,
            status TEXT DEFAULT 'pending'
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def fetch_rss_content(self, url: str, max_items: int = 5) -> List[Dict]:
        """Fetch and parse RSS feed content"""
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                content = response.read().decode('utf-8', errors='ignore')
                root = ET.fromstring(content)
                
                items = []
                for item in root.findall('.//item')[:max_items]:
                    title_elem = item.find('title')
                    description_elem = item.find('description')
                    link_elem = item.find('link')
                    
                    if title_elem is not None:
                        items.append({
                            'title': title_elem.text or '',
                            'description': description_elem.text if description_elem is not None else '',
                            'url': link_elem.text if link_elem is not None else url,
                            'source': url
                        })
                
                return items
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return []
    
    def analyze_content_for_disability_angle(self, title: str, description: str) -> Optional[Dict]:
        """Analyze article content for hidden disability angles"""
        combined_text = (title + ' ' + description).lower()
        
        # Look for disability keywords
        found_keywords = []
        keyword_positions = {}
        
        for keyword in self.disability_keywords:
            if keyword in combined_text:
                found_keywords.append(keyword)
                keyword_positions[keyword] = combined_text.find(keyword)
        
        if not found_keywords:
            return None
        
        # Calculate confidence based on keyword proximity and count
        confidence = min(1.0, len(found_keywords) / 5.0)
        
        # Generate article idea based on keywords and title
        article_idea = self._generate_article_idea(title, found_keywords)
        
        if article_idea:
            return {
                'keywords': found_keywords,
                'confidence': confidence,
                'article_idea': article_idea,
                'disability_angle': self._extract_angle(title, found_keywords)
            }
        
        return None
    
    def _extract_angle(self, title: str, keywords: List[str]) -> str:
        """Extract the disability angle from article title and keywords"""
        # Simple heuristic: combine title with disability keyword context
        primary_keyword = keywords[0] if keywords else 'disability'
        return f"How '{title}' affects or relates to {primary_keyword}"
    
    def _generate_article_idea(self, original_title: str, keywords: List[str]) -> Optional[str]:
        """Generate a disability-AI article idea from non-disability content"""
        # Templates for transforming non-disability topics into disability angles
        templates = [
            "The Hidden {keyword} Problem: Why '{title}' Matters for Disabled Communities",
            "Beyond {keyword}: How '{title}' Reveals Systemic Accessibility Gaps",
            "The {keyword} Paradox: What '{title}' Gets Wrong About Access",
            "Disability Expertise and '{title}': A Different Perspective",
            "The {keyword} Economy: Hidden Costs in '{title}'",
        ]
        
        if not keywords:
            return None
        
        primary_keyword = keywords[0].title()
        template = templates[len(keywords) % len(templates)]
        
        try:
            article_idea = template.format(keyword=primary_keyword, title=original_title[:50])
            return article_idea
        except:
            return None
    
    def crawl_category(self, category: str) -> List[Dict]:
        """Crawl all sources in a category"""
        results = []
        
        if category not in self.sources:
            print(f"Category '{category}' not found. Available: {list(self.sources.keys())}")
            return results
        
        print(f"\nCrawling {category.upper()} sources...")
        
        for source_url in self.sources[category]:
            print(f"  Fetching: {source_url[:50]}...")
            items = self.fetch_rss_content(source_url, max_items=10)
            
            for item in items:
                angle = self.analyze_content_for_disability_angle(
                    item['title'],
                    item['description']
                )
                
                if angle:
                    finding = {
                        'source': source_url,
                        'original_title': item['title'],
                        'original_url': item['url'],
                        'disability_angle': angle['disability_angle'],
                        'article_idea': angle['article_idea'],
                        'keywords': angle['keywords'],
                        'confidence': angle['confidence'],
                        'category': category,
                        'discovered': datetime.now().isoformat()
                    }
                    results.append(finding)
                    print(f"    ✓ Found angle: {angle['article_idea'][:60]}...")
        
        return results
    
    def save_findings(self, findings: List[Dict], output_format: str = 'json'):
        """Save findings to JSON and database"""
        # Save to JSON
        json_file = Path('disability_findings.json')
        with open(json_file, 'w') as f:
            json.dump(findings, f, indent=2)
        print(f"\n✓ Saved {len(findings)} findings to {json_file}")
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for finding in findings:
            try:
                cursor.execute('''
                INSERT OR REPLACE INTO findings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    finding.get('original_url', ''),
                    finding.get('original_title', ''),
                    finding.get('original_url', ''),
                    finding.get('source', ''),
                    finding.get('original_title', ''),
                    finding.get('disability_angle', ''),
                    ','.join(finding.get('keywords', [])),
                    finding.get('confidence', 0.5),
                    finding.get('discovered', datetime.now().isoformat()),
                    finding.get('article_idea', ''),
                    '',  # research questions
                    self._suggest_agent(finding),
                ))
            except Exception as e:
                print(f"Error saving finding: {e}")
        
        conn.commit()
        conn.close()
        print(f"✓ Saved findings to {self.db_path}")
    
    def _suggest_agent(self, finding: Dict) -> str:
        """Suggest which Disability-AI agent would be best for this article"""
        keywords = finding.get('keywords', [])
        
        if any(k in keywords for k in ['deaf', 'blind', 'sensory', 'visual', 'hearing']):
            return 'Pixel Nova or Siri Sage'
        elif any(k in keywords for k in ['neurodiverse', 'autistic', 'adhd', 'cognitive']):
            return 'Zen Circuit'
        elif any(k in keywords for k in ['accessibility', 'mobility', 'wheelchair', 'barrier']):
            return 'Maya Flux'
        else:
            return 'Any agent'
    
    def generate_report(self, findings: List[Dict]) -> str:
        """Generate a human-readable report of findings"""
        report = f"""# Disability Discovery Crawler Report
Generated: {datetime.now().isoformat()}

## Summary
- Total findings: {len(findings)}
- Date range: Last crawl

## Findings by Category
"""
        
        categories = {}
        for finding in findings:
            cat = finding.get('category', 'unknown')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(finding)
        
        for category, items in categories.items():
            report += f"\n### {category.upper()} ({len(items)} findings)\n"
            for item in items:
                confidence = item.get('confidence', 0.5)
                confidence_stars = '★' * int(confidence * 5) + '☆' * (5 - int(confidence * 5))
                report += f"\n- **{item.get('article_idea', 'Unknown')}**\n"
                report += f"  - Original: {item.get('original_title', 'N/A')}\n"
                report += f"  - Angle: {item.get('disability_angle', 'N/A')}\n"
                report += f"  - Suggested agent: {self._suggest_agent(item)}\n"
                report += f"  - Confidence: {confidence_stars}\n"
        
        return report
    
    def run_crawl(self, categories: List[str] = None) -> List[Dict]:
        """Run the complete crawling process"""
        if categories is None:
            categories = list(self.sources.keys())
        
        print(f"Starting Disability Discovery Crawler...")
        print(f"Categories: {', '.join(categories)}\n")
        
        all_findings = []
        for category in categories:
            findings = self.crawl_category(category)
            all_findings.extend(findings)
        
        if all_findings:
            self.save_findings(all_findings)
            report = self.generate_report(all_findings)
            
            with open('disability_findings_report.md', 'w') as f:
                f.write(report)
            print(f"\n✓ Generated report: disability_findings_report.md")
        else:
            print("\nNo disability angles found in this crawl.")
        
        return all_findings

if __name__ == '__main__':
    crawler = SimplifiedDisabilityCrawler()
    
    # Run crawler on all categories
    findings = crawler.run_crawl()
    
    print(f"\n✓ Crawl complete. Found {len(findings)} disability angles in non-disability content.")
