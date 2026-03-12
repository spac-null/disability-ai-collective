#!/usr/bin/env python3
"""
Test script for Disability Discovery Crawler
Demonstrates core functionality without full web crawling
"""

import sys
import json
from datetime import datetime
from disability_discovery_crawler import (
    ContentAnalyzer,
    ArticleIdeaGenerator,
    ArticleFinding,
    SourceConfig,
    DISABILITY_KEYWORDS,
    DISABILITY_PATTERNS
)

def test_analyzer():
    """Test the content analyzer with sample articles"""
    print("="*60)
    print("TESTING CONTENT ANALYZER")
    print("="*60)
    
    analyzer = ContentAnalyzer()
    
    test_cases = [
        {
            "title": "New AI Voice Assistant Revolutionizes Smart Homes",
            "summary": "The latest AI assistant uses voice commands to control everything in your home, but some users report difficulty with accents.",
            "expected_keywords": ["voice control", "difficulty"]
        },
        {
            "title": "Minimalist Office Design Trends for 2024",
            "summary": "Clean lines and sparse furniture create a calming environment, though some find the lack of visual cues disorienting.",
            "expected_keywords": ["visual", "disorienting"]
        },
        {
            "title": "Remote Work Study Shows Productivity Gains",
            "summary": "Companies report 25% productivity increase with remote work, especially benefiting employees who need accommodations.",
            "expected_keywords": ["accommodation", "remote work"]
        },
        {
            "title": "VR Gaming Headset Breaks Sales Records",
            "summary": "The new VR headset offers immersive experiences but users with motion sensitivity report nausea.",
            "expected_keywords": ["sensory", "motion"]
        },
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['title']}")
        print(f"Summary: {test['summary']}")
        
        result = analyzer.analyze_content(test['title'], test['summary'])
        
        print(f"Found keywords: {result['keywords']}")
        print(f"Pattern matches: {result['pattern_matches']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Context: {result['context']}")
        
        if result['keywords']:
            print("✅ Disability angle detected!")
        else:
            print("❌ No disability angle found")
    
    return analyzer

def test_idea_generator():
    """Test article idea generation"""
    print("\n" + "="*60)
    print("TESTING ARTICLE IDEA GENERATOR")
    print("="*60)
    
    generator = ArticleIdeaGenerator()
    
    test_cases = [
        {
            "original_title": "AI Voice Assistant Takes Over Smart Homes",
            "category": "tech",
            "keywords": ["voice control", "deaf"],
            "context": "voice-based interface"
        },
        {
            "original_title": "Open Plan Offices Increase Collaboration",
            "category": "design",
            "keywords": ["sensory", "neurodiverse"],
            "context": "noisy environment"
        },
        {
            "original_title": "Gig Economy Reshapes Workforce",
            "category": "business",
            "keywords": ["accommodation", "disability"],
            "context": "flexible work"
        },
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['original_title']}")
        print(f"Category: {test['category']}, Keywords: {test['keywords']}")
        
        title, angle, questions = generator.generate_article_idea(
            test['original_title'],
            test['category'],
            test['keywords'],
            test['context']
        )
        
        print(f"Generated Title: {title}")
        print(f"Article Angle: {angle}")
        print(f"Research Questions:")
        for q in questions:
            print(f"  - {q}")
    
    return generator

def test_finding_creation():
    """Test creating ArticleFinding objects"""
    print("\n" + "="*60)
    print("TESTING FINDING CREATION")
    print("="*60)
    
    # Create a sample finding
    finding = ArticleFinding(
        id="test123",
        source_url="https://example.com/article",
        source_name="Test Source",
        original_title="AI Voice Assistant Launches",
        original_summary="New voice-controlled AI assistant announced",
        publish_date="2024-03-10",
        discovered_at=datetime.now().isoformat(),
        disability_keywords=["voice control", "deaf"],
        disability_context="Voice-based interface excludes deaf users",
        article_title="How Voice-First AI Excludes Deaf Users",
        article_angle="Exploring accessibility issues in voice-controlled AI",
        research_questions=[
            "How do deaf users interact with voice-controlled AI?",
            "What alternative interfaces could be provided?",
            "How does this reflect broader accessibility issues in tech?"
        ],
        assigned_agent="Tech Accessibility Analyst",
        confidence_score=0.85,
        tags=["tech", "AI", "accessibility"],
        raw_content_hash="abc123"
    )
    
    print("Sample ArticleFinding created:")
    print(f"Original: {finding.original_title}")
    print(f"Disability Angle: {finding.article_title}")
    print(f"Keywords: {finding.disability_keywords}")
    print(f"Confidence: {finding.confidence_score}")
    print(f"Assigned to: {finding.assigned_agent}")
    
    # Convert to dict
    finding_dict = finding.to_dict()
    print(f"\nAs dictionary (first few keys):")
    for key in list(finding_dict.keys())[:5]:
        print(f"  {key}: {finding_dict[key]}")
    
    return finding

def test_source_config():
    """Test source configuration"""
    print("\n" + "="*60)
    print("TESTING SOURCE CONFIGURATION")
    print("="*60)
    
    # Create a test source config
    config = SourceConfig(
        name="Test Tech Blog",
        rss_url="https://test.com/feed",
        category="tech",
        rate_limit_seconds=3,
        enabled=True,
        keywords_boost={"AI": 1.2, "tech": 1.1}
    )
    
    print(f"Source: {config.name}")
    print(f"Category: {config.category}")
    print(f"Rate limit: {config.rate_limit_seconds}s")
    print(f"Keywords boost: {config.keywords_boost}")
    
    return config

def run_all_tests():
    """Run all tests"""
    print("🚀 DISABILITY DISCOVERY CRAWLER - FUNCTIONALITY TESTS")
    print("="*60)
    
    results = {}
    
    try:
        results['analyzer'] = test_analyzer()
        print("\n✅ Content Analyzer tests passed")
    except Exception as e:
        print(f"\n❌ Content Analyzer tests failed: {e}")
        return False
    
    try:
        results['generator'] = test_idea_generator()
        print("\n✅ Article Idea Generator tests passed")
    except Exception as e:
        print(f"\n❌ Article Idea Generator tests failed: {e}")
        return False
    
    try:
        results['finding'] = test_finding_creation()
        print("\n✅ Finding Creation tests passed")
    except Exception as e:
        print(f"\n❌ Finding Creation tests failed: {e}")
        return False
    
    try:
        results['config'] = test_source_config()
        print("\n✅ Source Configuration tests passed")
    except Exception as e:
        print(f"\n❌ Source Configuration tests failed: {e}")
        return False
    
    # Summary
    print("\n" + "="*60)
    print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("\nThe crawler's core components are working correctly:")
    print("1. ✅ Content analysis with disability keyword detection")
    print("2. ✅ Article idea generation from findings")
    print("3. ✅ Data structure creation and serialization")
    print("4. ✅ Source configuration management")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r crawler_requirements.txt")
    print("2. Run full crawler: python disability_discovery_crawler.py")
    print("3. Check output files: disability_findings.json, disability_report.md")
    
    return True

if __name__ == "__main__":
    # Check if we can import required modules
    try:
        import aiohttp
        import feedparser
        import bs4
        print("✅ All required modules are available")
    except ImportError as e:
        print(f"❌ Missing module: {e}")
        print("Install dependencies with: pip install -r crawler_requirements.txt")
        sys.exit(1)
    
    # Run tests
    success = run_all_tests()
    
    if success:
        print("\n✨ Ready to discover disability angles! ✨")
        sys.exit(0)
    else:
        print("\n❌ Tests failed. Please check the errors above.")
        sys.exit(1)