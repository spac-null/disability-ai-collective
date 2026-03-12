#!/usr/bin/env python3
"""
Disability Web Crawler - Full Webpage & Search Engine Crawling
Finds disability angles in current journalism by crawling actual webpages
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

class DisabilityWebCrawler:
    """Crawls webpages to find disability angles in current journalism"""
    
    def __init__(self):
        self.db_path = "disability_web_findings.db"
        self.findings = []
        self.visited_urls = set()
        self.init_database()
        
        # Disability keywords to search for in webpage content
        self.disability_keywords = {
            'prosthetic', 'wheelchair', 'deaf', 'blind', 'neurodiverse', 'autistic',
            'accessibility', 'inclusive', 'assistive', 'disability', 'accommodation',
            'sensory', 'cognitive', 'mobility', 'hearing', 'vision', 'marginalized',
            'barrier', 'disabled', 'neurodivergent', 'ADHD', 'dyslexia',
            'chronic illness', 'chronic pain', 'mental health', 'inclusion',
            'universal design', 'adaptive technology', 'assistive device'
        }
        
        # User agents to rotate
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
        CREATE TABLE IF NOT EXISTS web_findings (
            id TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            title TEXT NOT NULL,
            domain TEXT NOT NULL,
            content_snippet TEXT NOT NULL,
            disability_keywords TEXT NOT NULL,
            keyword_contexts TEXT NOT NULL,
            confidence REAL NOT NULL,
            article_idea TEXT NOT NULL,
            discovered_date TEXT NOT NULL,
            word_count INTEGER NOT NULL,
            source_type TEXT NOT NULL,
            status TEXT DEFAULT 'pending'
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_random_user_agent(self):
        """Get random user agent"""
        return random.choice(self.user_agents)
    
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
        
        # Extract text from paragraphs
        text_parts = []
        p_matches = re.findall(r'<p[^>]*>(.*?)</p>', cleaned, re.IGNORECASE | re.DOTALL)
        
        for match in p_matches:
            text = re.sub(r'<[^>]+>', ' ', match)
            text = html.unescape(text.strip())
            if text and len(text) > 20:
                text_parts.append(text)
        
        full_text = ' '.join(text_parts)
        
        return {
            'title': title[:200],
            'text': full_text[:3000]  # Limit text length
        }
    
    def analyze_webpage_content(self, url: str, title: str, text: str) -> Optional[Dict]:
        """Analyze webpage content for disability angles"""
        if not text or len(text) < 100:
            return None
        
        text_lower = text.lower()
        title_lower = title.lower()
        
        # Find disability keywords
        found_keywords = []
        keyword_contexts = {}
        
        for keyword in self.disability_keywords:
            if keyword in text_lower or keyword in title_lower:
                found_keywords.append(keyword)
                
                # Find context
                keyword_pos = text_lower.find(keyword)
                if keyword_pos != -1:
                    start = max(0, keyword_pos - 80)
                    end = min(len(text_lower), keyword_pos + len(keyword) + 80)
                    context = text_lower[start:end].replace('\n', ' ').strip()
                    keyword_contexts[keyword] = context
        
        if not found_keywords:
            return None
        
        # Calculate confidence
        confidence = min(1.0, len(found_keywords) / 3.0)
        
        # Generate article idea
        article_idea = self._generate_article_idea(title, found_keywords)
        
        if article_idea and confidence > 0.3:
            # Extract domain from URL
            domain = urllib.parse.urlparse(url).netloc
            
            return {
                'url': url,
                'title': title,
                'domain': domain,
                'keywords': found_keywords,
                'keyword_contexts': keyword_contexts,
                'confidence': confidence,
                'article_idea': article_idea,
                'word_count': len(text.split()),
                'content_snippet': text[:200] + '...' if len(text) > 200 else text,
                'source_type': 'web_crawl'
            }
        
        return None
    
    def _generate_article_idea(self, original_title: str, keywords: List[str]) -> Optional[str]:
        """Generate article idea from webpage content"""
        templates = [
            "What '{title}' Reveals About Hidden {keyword} Barriers",
            "The {keyword} Perspective on '{title}': What Analysis Misses",
            "Disability Expertise Reads '{title}' Differently",
            "Beyond the Headline: {keyword} Implications of '{title}'",
        ]
        
        if not keywords:
            return None
        
        primary_keyword = keywords[0].title()
        template = templates[len(keywords) % len(templates)]
        
        try:
            # Clean title
            clean_title = re.sub(r' - [^-]+$', '', original_title)  # Remove site name
            clean_title = clean_title[:50] + '...' if len(clean_title) > 50 else clean_title
            
            article_idea = template.format(keyword=primary_keyword, title=clean_title)
            return article_idea
        except:
            return None
    
    def crawl_test_urls(self) -> List[Dict]:
        """Crawl test URLs to demonstrate webpage crawling"""
        print("Starting web crawl for disability angles...")
        
        # Test URLs that might contain disability-related content
        test_urls = [
            # Tech/Design URLs
            "https://www.w3.org/WAI/fundamentals/accessibility-intro/",
            "https://developer.mozilla.org/en-US/docs/Web/Accessibility",
            "https://www.smashingmagazine.com/category/accessibility/",
            # News/Articles
            "https://www.nytimes.com/section/technology",
            "https://www.theguardian.com/technology",
            # GitHub accessibility topics
            "https://github.com/topics/accessibility",
            "https://github.com/topics/assistive-technology",
        ]
        
        findings = []
        
        for i, url in enumerate(test_urls):
            print(f"\n[{i+1}/{len(test_urls)}] Crawling: {url[:60]}...")
            
            if url in self.visited_urls:
                continue
            
            content = self.fetch_webpage(url)
            if content:
                extracted = self.extract_text_from_html(content)
                print(f"  Title: {extracted['title'][:80]}...")
                print(f"  Text length: {len(extracted['text'])} chars")
                
                analysis = self.analyze_webpage_content(
                    url, 
                    extracted['title'], 
                    extracted['text']
                )
                
                if analysis:
                    findings.append(analysis)
                    print(f"  ✓ Found disability angle!")
                    print(f"     Idea: {analysis['article_idea']}")
                    print(f"     Keywords: {', '.join(analysis['keywords'])}")
                else:
                    print(f"  ✗ No disability angles found")
                
                self.visited_urls.add(url)
                
                # Delay
                time.sleep(1)
            else:
                print(f"  ✗ Failed to fetch (network issue)")
        
        return findings
    
    def save_findings(self, findings: List[Dict]):
        """Save findings to database and JSON"""
        if not findings:
            print("\nNo disability angles found in web crawl")
            return
        
        # Save to JSON
        json_file = Path('disability_web_findings.json')
        with open(json_file, 'w') as f:
            json.dump(findings, f, indent=2)
        print(f"\n✓ Saved {len(findings)} findings to {json_file}")
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        saved_count = 0
        for finding in findings:
            try:
                cursor.execute('''
                INSERT OR REPLACE INTO web_findings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    finding['url'],
                    finding['url'],
                    finding['title'],
                    finding['domain'],
                    finding['content_snippet'],
                    ','.join(finding['keywords']),
                    json.dumps(finding['keyword_contexts']),
                    finding['confidence'],
                    finding['article_idea'],
                    datetime.now().isoformat(),
                    finding['word_count'],
                    finding['source_type'],
                    'pending'
                ))
                saved_count += 1
            except Exception as e:
                print(f"Error saving finding: {e}")
        
        conn.commit()
        conn.close()
        print(f"✓ Saved {saved_count} findings to database {self.db_path}")
    
    def generate_report(self, findings: List[Dict]) -> str:
        """Generate human-readable report"""
        report = f"""# Disability Web Crawler Report
Generated: {datetime.now().isoformat()}

## Summary
- Total findings: {len(findings)}
- URLs crawled: {len(self.visited_urls)}
- Average confidence: {sum(f['confidence'] for f in findings) / len(findings) if findings else 0:.2f}

## Findings
"""
        
        for i, finding in enumerate(findings, 1):
            confidence_stars = '★' * int(finding['confidence'] * 5) + '☆' * (5 - int(finding['confidence'] * 5))
            
            report += f"\n### {i}. {finding['article_idea']}\n"
            report += f"- **URL**: {finding['url']}\n"
            report += f"- **Source**: {finding['domain']}\n"
            report += f"- **Keywords**: {', '.join(finding['keywords'])}\n"
            report += f"- **Confidence**: {confidence_stars} ({finding['confidence']:.2f})\n"
            report += f"- **Snippet**: {finding['content_snippet'][:150]}...\n"
        
        return report
    
    def run(self):
        """Run the web crawler"""
        print("=" * 60)
        print("DISABILITY WEB CRAWLER - Full Webpage Analysis")
        print("=" * 60)
        
        findings = self.crawl_test_urls()
        
        if findings:
            self.save_findings(findings)
            
            # Generate report
            report = self.generate_report(findings)
            with open('disability_web_findings_report.md', 'w') as f:
                f.write(report)
            print(f"\n✓ Generated report: disability_web_findings_report.md")
            
            # Update article ideas
            self._update_article_ideas(findings)
        else:
            print("\n❌ No disability angles found in current web crawl")
        
        return findings
    
    def _update_article_ideas(self, findings: List[Dict]):
        """Update article_ideas.md with web crawl findings"""
        try:
            ideas_file = Path('automation/article_ideas.md')
            if ideas_file.exists():
                with open(ideas_file, 'a') as f:
                    f.write(f"\n\n## Discovered by Web Crawler ({datetime.now().strftime('%Y-%m-%d')})\n")
                    for finding in findings:
                        if finding['confidence'] > 0.5:
                            f.write(f"- **\"{finding['article_idea']}\"** (confidence: {finding['confidence']:.2f})\n")
                print(f"✓ Updated article_ideas.md with {len([f for f in findings if f['confidence'] > 0.5])} high-confidence findings")
        except Exception as e:
            print(f"Note: Could not update article_ideas.md: {e}")

if __name__ == '__main__':
    crawler = DisabilityWebCrawler()
    findings = crawler.run()
    
    if findings:
        print("\n" + "=" * 60)
        print(f"✅ WEB CRAWL COMPLETE: Found {len(findings)} disability angles")
        print("=" * 60)
    else:
        print("\n❌ No disability angles found in web pages")
