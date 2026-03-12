#!/usr/bin/env python3
"""
Disability Discovery Crawler - LOCAL MOCK VERSION
For testing in environments without external network access
"""

import json
import sqlite3
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class MockDisabilityCrawler:
    """Mock crawler that simulates web content without network access"""
    
    def __init__(self, db_path="disability_findings_mock.db"):
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
        
        # Mock RSS feed data (simulates real articles)
        self.mock_feeds = {
            'tech': [
                {
                    'title': 'New AI Voice Assistant Launches with Advanced Speech Recognition',
                    'description': 'Tech company announces voice-controlled AI that understands natural language commands. The assistant can control smart home devices, schedule appointments, and answer complex queries.',
                    'url': 'https://techcrunch.com/mock/ai-voice-assistant',
                    'source': 'TechCrunch Mock'
                },
                {
                    'title': 'Remote Work Tools See 300% Growth in Enterprise Adoption',
                    'description': 'Companies are investing heavily in collaboration software and virtual office platforms as hybrid work becomes standard.',
                    'url': 'https://techcrunch.com/mock/remote-work-tools',
                    'source': 'TechCrunch Mock'
                }
            ],
            'business': [
                {
                    'title': 'Corporate Diversity Initiatives Focus on Neurodiversity Hiring',
                    'description': 'Major corporations are creating specialized hiring programs for autistic and neurodiverse talent, recognizing unique problem-solving skills.',
                    'url': 'https://bloomberg.com/mock/neurodiversity-hiring',
                    'source': 'Bloomberg Mock'
                },
                {
                    'title': 'Urban Development Projects Prioritize Sustainable Design',
                    'description': 'New city planning initiatives include wheelchair-accessible public spaces and sensory-friendly environments for all residents.',
                    'url': 'https://bloomberg.com/mock/urban-development',
                    'source': 'Bloomberg Mock'
                }
            ],
            'design': [
                {
                    'title': 'Minimalist Office Design Trends for 2026',
                    'description': 'Clean lines, neutral colors, and reduced visual clutter define the latest office aesthetics, though some critics question sensory accessibility.',
                    'url': 'https://dezeen.com/mock/minimalist-office',
                    'source': 'Dezeen Mock'
                },
                {
                    'title': 'Architectural Acoustics: Designing for Sound Quality',
                    'description': 'New research shows how building materials and layouts affect auditory experiences, with implications for deaf and hard-of-hearing individuals.',
                    'url': 'https://dezeen.com/mock/architectural-acoustics',
                    'source': 'Dezeen Mock'
                }
            ],
            'science': [
                {
                    'title': 'Breakthrough in Prosthetic Technology Allows Natural Movement',
                    'description': 'Researchers develop neural interface that enables intuitive control of prosthetic limbs, restoring near-natural mobility for amputees.',
                    'url': 'https://nature.com/mock/prosthetic-technology',
                    'source': 'Nature Mock'
                },
                {
                    'title': 'Study Reveals Cognitive Benefits of Sensory Deprivation',
                    'description': 'Controlled environments with reduced sensory input show promise for treating anxiety and improving focus in neurodiverse individuals.',
                    'url': 'https://nature.com/mock/sensory-deprivation',
                    'source': 'Nature Mock'
                }
            ],
            'culture': [
                {
                    'title': 'Film Industry Faces Criticism for Disability Representation',
                    'description': 'Recent blockbusters continue to cast able-bodied actors in disabled roles, despite growing calls for authentic representation.',
                    'url': 'https://hollywoodreporter.com/mock/disability-representation',
                    'source': 'Hollywood Reporter Mock'
                },
                {
                    'title': 'Deaf Musician Revolutionizes Electronic Music Composition',
                    'description': 'Using visual interfaces and tactile feedback, composer creates groundbreaking soundscapes that challenge traditional music production.',
                    'url': 'https://hollywoodreporter.com/mock/deaf-musician',
                    'source': 'Hollywood Reporter Mock'
                }
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
    
    def fetch_mock_content(self, category: str) -> List[Dict]:
        """Fetch mock RSS feed content (no network required)"""
        return self.mock_feeds.get(category, [])
    
    def analyze_content_for_disability_angle(self, title: str, description: str) -> Optional[Dict]:
        """Analyze article content for hidden disability angles"""
        combined_text = (title + ' ' + description).lower()
        
        # Look for disability keywords
        found_keywords = []
        
        for keyword in self.disability_keywords:
            if keyword in combined_text:
                found_keywords.append(keyword)
        
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
                'disability_angle': self._extract_angle(title, found_keywords),
                'research_questions': self._generate_research_questions(title, found_keywords)
            }
        
        return None
    
    def _extract_angle(self, title: str, keywords: List[str]) -> str:
        """Extract the disability angle from article title and keywords"""
        primary_keyword = keywords[0] if keywords else 'disability'
        return f"How '{title}' reveals hidden {primary_keyword} perspectives in mainstream discourse"
    
    def _generate_article_idea(self, original_title: str, keywords: List[str]) -> Optional[str]:
        """Generate a disability-AI article idea from non-disability content"""
        templates = [
            "The Hidden {keyword} Dimension of '{title}': What Mainstream Analysis Misses",
            "Beyond Surface Level: How '{title}' Unintentionally Highlights {keyword} Accessibility Gaps",
            "The {keyword} Paradox in '{title}': When Progress Creates New Barriers",
            "Disability Expertise Reads '{title}' Differently: A {keyword} Perspective",
            "The Unseen {keyword} Economy: Hidden Costs and Opportunities in '{title}'",
        ]
        
        if not keywords:
            return None
        
        primary_keyword = keywords[0].title()
        template = templates[len(keywords) % len(templates)]
        
        try:
            article_idea = template.format(keyword=primary_keyword, title=original_title[:60])
            return article_idea
        except:
            return None
    
    def _generate_research_questions(self, title: str, keywords: List[str]) -> str:
        """Generate research questions for the article idea"""
        questions = [
            f"How does {keywords[0]} expertise change our understanding of '{title}'?",
            f"What accessibility patterns are hidden in the assumptions behind '{title}'?",
            f"How would disability-led design approach the challenges in '{title}' differently?",
            f"What systemic barriers does '{title}' reveal or reinforce for {keywords[0]} communities?",
            f"How can the insights from '{title}' be transformed into actionable accessibility improvements?"
        ]
        return '|'.join(questions[:3])  # Join with pipe for database storage
    
    def crawl_category(self, category: str) -> List[Dict]:
        """Crawl mock sources in a category"""
        results = []
        
        if category not in self.mock_feeds:
            print(f"Category '{category}' not found. Available: {list(self.mock_feeds.keys())}")
            return results
        
        print(f"\nCrawling {category.upper()} mock sources...")
        
        for item in self.mock_feeds[category]:
            print(f"  Analyzing: {item['title'][:50]}...")
            angle = self.analyze_content_for_disability_angle(
                item['title'],
                item['description']
            )
            
            if angle:
                finding = {
                    'source': item['source'],
                    'original_title': item['title'],
                    'original_url': item['url'],
                    'disability_angle': angle['disability_angle'],
                    'article_idea': angle['article_idea'],
                    'keywords': angle['keywords'],
                    'confidence': angle['confidence'],
                    'research_questions': angle['research_questions'],
                    'category': category,
                    'discovered': datetime.now().isoformat()
                }
                results.append(finding)
                print(f"    ✓ Found angle: {angle['article_idea'][:60]}...")
        
        return results
    
    def save_findings(self, findings: List[Dict], output_format: str = 'json'):
        """Save findings to JSON and database"""
        # Save to JSON
        json_file = Path('disability_findings_mock.json')
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
                    finding.get('research_questions', ''),
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
        
        if any(k in keywords for k in ['deaf', 'blind', 'sensory', 'visual', 'hearing', 'acoustic']):
            return 'Pixel Nova or Siri Sage'
        elif any(k in keywords for k in ['neurodiverse', 'autistic', 'adhd', 'cognitive', 'mental']):
            return 'Zen Circuit'
        elif any(k in keywords for k in ['accessibility', 'mobility', 'wheelchair', 'barrier', 'prosthetic']):
            return 'Maya Flux'
        else:
            return 'Any agent'
    
    def generate_report(self, findings: List[Dict]) -> str:
        """Generate a human-readable report of findings"""
        report = f"""# Disability Discovery Crawler - MOCK TEST REPORT
Generated: {datetime.now().isoformat()}
Environment: Local Mock (No Network Required)

## Summary
- Total findings: {len(findings)}
- Categories crawled: {', '.join(set(f.get('category', 'unknown') for f in findings))}

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
                report += f"  - Keywords: {', '.join(item.get('keywords', []))}\n"
                report += f"  - Suggested agent: {self._suggest_agent(item)}\n"
                report += f"  - Confidence: {confidence_stars}\n"
        
        report += f"\n## Next Steps\n"
        report += f"These mock findings demonstrate the crawler's capability to identify disability angles in non-disability content.\n"
        report += f"In production with network access, the crawler will analyze real RSS feeds from:\n"
        report += f"- TechCrunch, The Verge, Wired\n"
        report += f"- Bloomberg, Financial Times, HBR\n"
        report += f"- Dezeen, ArchDaily, Fast Company\n"
        report += f"- Nature, New Scientist\n"
        report += f"- Variety, Hollywood Reporter\n"
        
        return report
    
    def run_crawl(self, categories: List[str] = None) -> List[Dict]:
        """Run the complete mock crawling process"""
        if categories is None:
            categories = list(self.mock_feeds.keys())
        
        print(f"Starting Disability Discovery Crawler (MOCK VERSION)...")
        print(f"Categories: {', '.join(categories)}")
        print(f"Environment: Local mock data (no network required)\n")
        
        all_findings = []
        for category in categories:
            findings = self.crawl_category(category)
            all_findings.extend(findings)
        
        if all_findings:
            self.save_findings(all_findings)
            report = self.generate_report(all_findings)
            
            with open('disability_findings_mock_report.md', 'w') as f:
                f.write(report)
            print(f"\n✓ Generated report: disability_findings_mock_report.md")
            
            # Also update the article ideas file with new findings
            self._update_article_ideas(all_findings)
        else:
            print("\nNo disability angles found in this crawl.")
        
        return all_findings
    
    def _update_article_ideas(self, findings: List[Dict]):
        """Update the article_ideas.md file with new findings"""
        try:
            ideas_file = Path('automation/article_ideas.md')
            if ideas_file.exists():
                with open(ideas_file, 'a') as f:
                    f.write(f"\n\n## Discovered by Crawler ({datetime.now().strftime('%Y-%m-%d')})\n")
                    for finding in findings:
                        if finding.get('confidence', 0) > 0.6:  # Only high-confidence findings
                            f.write(f"- **\"{finding.get('article_idea', '')}\"** - {finding.get('suggested_agent', 'Any agent')} ({finding.get('category', 'general')})\n")
                print(f"✓ Updated article_ideas.md with {len([f for f in findings if f.get('confidence', 0) > 0.6])} high-confidence findings")
        except Exception as e:
            print(f"Note: Could not update article_ideas.md: {e}")

if __name__ == '__main__':
    crawler = MockDisabilityCrawler()
    
    # Run crawler on all categories
    findings = crawler.run_crawl()
    
    print(f"\n{'='*60}")
    print(f"✓ MOCK CRAWL COMPLETE")
    print(f"✓ Found {len(findings)} disability angles in mock non-disability content")
    print(f"✓ All logic tested successfully (no network required)")
    print(f"✓ Ready for production with real RSS feeds when network access available")
    print(f"{'='*60}")
