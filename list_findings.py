#!/usr/bin/env python3
"""
List all disability angles found in today's RSS crawl
"""

import json

def main():
    try:
        with open('rss_disability_findings.json', 'r') as f:
            data = json.load(f)
        
        print("📊 ALL DISABILITY ANGLES FOUND (March 13th)")
        print("=" * 80)
        print(f"Total Findings: {len(data)}")
        print()
        
        for i, item in enumerate(data, 1):
            print(f"{i}. {item['article_idea']}")
            print(f"   🔗 URL: {item['url'][:70]}...")
            print(f"   📰 Source: {item['domain']} - {item['title'][:50]}...")
            print(f"   🎯 Confidence: {item['confidence']:.2f}")
            
            # Show disability concepts found
            concepts = item.get('disability_concepts', {})
            concept_list = []
            for category, terms in concepts.items():
                if terms:
                    concept_list.append(f"{category}: {', '.join(terms[:3])}")
            
            if concept_list:
                print(f"   🧠 Disability Concepts: {'; '.join(concept_list)}")
            
            print()
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()