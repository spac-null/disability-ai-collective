#!/usr/bin/env python3
"""
Disability Discovery Crawler - REAL DATA VERSION (Simplified)
Uses only accessible data sources (no mock data)
"""

import json
import sqlite3
import re
import urllib.request
import urllib.error
import socket
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET

class RealDataDisabilityCrawler:
    """Crawler that uses only accessible real data sources"""
    
    def __init__(self):
        self.db_path = "disability_findings_real.db"
        self.findings = []
        self.init_database()
        
        # Test which sources are actually accessible
        self.test_sources()
    
    def test_sources(self):
        """Test which data sources are accessible"""
        print("Testing accessible data sources...")
        
        test_urls = [
            ("GitHub Trending", "https://github.com/trending"),
            ("Hacker News API", "https://hacker-news.firebaseio.com/v0/topstories.json"),
            ("Wikipedia API", "https://en.wikipedia.org/w/api.php?action=feedrecentchanges&format=rss"),
        ]
        
        self.accessible_sources = []
        
        for name, url in test_urls:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        print(f"  ✅ {name} is accessible")
                        self.accessible_sources.append((name, url))
                    else:
                        print(f"  ❌ {name}: HTTP {response.status}")
            except Exception as e:
                print(f"  ❌ {name}: {str(e)[:50]}")
        
        print(f"\nFound {len(self.accessible_sources)} accessible data sources")
    
    def init_database(self):
        """Initialize SQLite database"""
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
    
    def fetch_github_trending(self):
        """Fetch GitHub trending repositories"""
        print("\nFetching GitHub Trending...")
        
        try:
            req = urllib.request.Request(
                "https://github.com/trending",
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8', errors='ignore')
                
                # Extract repository information
                items = []
                
                # Look for repository cards
                repo_pattern = r'<article[^>]*>.*?<h2[^>]*>.*?<a[^>]*href="([^"]+)".*?>([^<]+)</a>'
                matches = re.findall(repo_pattern, content, re.DOTALL)
                
                for match in matches[:10]:  # First 10 repos
                    repo_url = f"https://github.com{match[0]}"
                    repo_name = match[1].strip()
                    
                    items.append({
                        'title': f"GitHub Trending: {repo_name}",
                        'description': f"Popular repository on GitHub: {repo_name}",
                        'url': repo_url,
                        'source': 'GitHub Trending'
                    })
                
                print(f"  Found {len(items)} trending repositories")
                return items
                
        except Exception as e:
            print(f"  Error fetching GitHub Trending: {e}")
            return []
    
    def fetch_hacker_news(self):
        """Fetch Hacker News top stories"""
        print("\nFetching Hacker News...")
        
        try:
            # Get top story IDs
            req = urllib.request.Request(
                "https://hacker-news.firebaseio.com/v0/topstories.json",
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                story_ids = json.loads(response.read().decode())[:5]  # First 5 stories
            
            items = []
            for story_id in story_ids:
                try:
                    story_req = urllib.request.Request(
                        f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
                        headers={'User-Agent': 'Mozilla/5.0'}
                    )
                    
                    with urllib.request.urlopen(story_req, timeout=10) as story_response:
                        story_data = json.loads(story_response.read().decode())
                        
                        if 'title' in story_data:
                            items.append({
                                'title': f"HN: {story_data['title']}",
                                'description': story_data.get('text', '')[:200] if 'text' in story_data else '',
                                'url': story_data.get('url', f'https://news.ycombinator.com/item?id={story_id}'),
                                'source': 'Hacker News'
                            })
                
                except Exception as e:
                    continue
            
            print(f"  Found {len(items)} Hacker News stories")
            return items
            
        except Exception as e:
            print(f"  Error fetching Hacker News: {e}")
            return []
    
    def analyze_for_disability_angles(self, items):
        """Analyze items for disability angles"""
        disability_keywords = {
            'prosthetic', 'wheelchair', 'deaf', 'blind', 'neurodiverse', 'autistic',
            'accessibility', 'inclusive', 'assistive', 'disability', 'accommodation',
            'sensory', 'cognitive', 'mobility', 'hearing', 'vision', 'marginalized',
            'barrier', 'disabled', 'ADL', 'neurodivergent', 'ADHD', 'dyslexia'
        }
        
        findings = []
        
        for item in items:
            text = (item['title'] + ' ' + item['description']).lower()
            
            found_keywords = []
            for keyword in disability_keywords:
                if keyword in text:
                    found_keywords.append(keyword)
            
            if found_keywords:
                confidence = min(1.0, len(found_keywords) / 3.0)
                
                # Generate article idea
                primary_keyword = found_keywords[0].title()
                templates = [
                    f"The {primary_keyword} Angle: What '{item['title'][:40]}' Reveals About Tech Accessibility",
                    f"Beyond the Code: How '{item['title'][:40]}' Affects {primary_keyword} Communities",
                    f"Disability Expertise Reads '{item['title'][:40]}' Differently",
                ]
                
                article_idea = templates[len(found_keywords) % len(templates)]
                
                findings.append({
                    'original_title': item['title'],
                    'original_url': item['url'],
                    'source': item['source'],
                    'keywords': found_keywords,
                    'confidence': confidence,
                    'article_idea': article_idea,
                    'disability_angle': f"How {primary_keyword} perspectives intersect with '{item['title'][:30]}'",
                    'discovered': datetime.now().isoformat()
                })
        
        return findings
    
    def save_findings(self, findings):
        """Save findings to database and JSON"""
        if not findings:
            print("\nNo disability angles found in current data")
            return
        
        # Save to JSON
        with open('disability_findings_real.json', 'w') as f:
            json.dump(findings, f, indent=2)
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for finding in findings:
            cursor.execute('''
            INSERT OR REPLACE INTO findings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                finding['original_url'],
                finding['original_title'],
                finding['original_url'],
                finding['source'],
                finding['original_title'],
                finding['disability_angle'],
                ','.join(finding['keywords']),
                finding['confidence'],
                finding['discovered'],
                finding['article_idea'],
                '',
                self.suggest_agent(finding)
            ))
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Saved {len(findings)} real disability angles to:")
        print(f"   - disability_findings_real.json")
        print(f"   - {self.db_path}")
    
    def suggest_agent(self, finding):
        """Suggest which agent should write about this"""
        keywords = finding['keywords']
        
        if any(k in keywords for k in ['deaf', 'blind', 'sensory', 'visual', 'hearing']):
            return 'Pixel Nova or Siri Sage'
        elif any(k in keywords for k in ['neurodiverse', 'autistic', 'adhd', 'cognitive']):
            return 'Zen Circuit'
        elif any(k in keywords for k in ['accessibility', 'mobility', 'wheelchair', 'barrier']):
            return 'Maya Flux'
        else:
            return 'Any agent'
    
    def run(self):
        """Run the real data crawler"""
        print("=" * 60)
        print("REAL DATA DISABILITY DISCOVERY CRAWLER")
        print("=" * 60)
        
        all_items = []
        
        # Fetch from accessible sources
        github_items = self.fetch_github_trending()
        hn_items = self.fetch_hacker_news()
        
        all_items.extend(github_items)
        all_items.extend(hn_items)
        
        if not all_items:
            print("\n❌ No data could be fetched from accessible sources")
            return []
        
        print(f"\nTotal items fetched: {len(all_items)}")
        
        # Analyze for disability angles
        findings = self.analyze_for_disability_angles(all_items)
        
        # Save results
        self.save_findings(findings)
        
        return findings

if __name__ == '__main__':
    crawler = RealDataDisabilityCrawler()
    findings = crawler.run()
    
    if findings:
        print("\n" + "=" * 60)
        print(f"🎯 CRAWL COMPLETE: Found {len(findings)} REAL disability angles")
        print("=" * 60)
        
        for i, finding in enumerate(findings[:3], 1):
            print(f"\n{i}. {finding['article_idea']}")
            print(f"   Source: {finding['source']}")
            print(f"   Keywords: {', '.join(finding['keywords'])}")
            print(f"   Confidence: {finding['confidence']:.2f}")
    else:
        print("\n❌ No disability angles found in current real data")
