#!/usr/bin/env python3
import sqlite3
import json
from datetime import datetime
from pathlib import Path

def generate_statistics():
    db_path = Path("disability_findings.db")
    if not db_path.exists():
        print("Database not found")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Basic statistics
    cursor.execute("SELECT COUNT(*) FROM findings")
    total_findings = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT domain) FROM findings")
    unique_domains = cursor.fetchone()[0]
    
    cursor.execute("SELECT MIN(discovered_date), MAX(discovered_date) FROM findings")
    first_last = cursor.fetchone()
    first_discovery = first_last[0]
    last_discovery = first_last[1]
    
    cursor.execute("SELECT COUNT(*) FROM findings WHERE used_for_article = 1")
    used_findings = cursor.fetchone()[0]
    
    # Category distribution
    cursor.execute("""
        SELECT disability_concepts, COUNT(*) as count 
        FROM findings 
        WHERE disability_concepts IS NOT NULL AND disability_concepts != ''
        GROUP BY disability_concepts 
        ORDER BY count DESC
        LIMIT 10
    """)
    top_categories = cursor.fetchall()
    
    # Recent findings
    cursor.execute("""
        SELECT title, domain, discovered_date
        FROM findings
        ORDER BY discovered_date DESC
        LIMIT 5
    """)
    recent_findings = cursor.fetchall()
    
    conn.close()
    
    # Generate report
    stats = {
        "timestamp": datetime.now().isoformat(),
        "total_findings": total_findings,
        "unique_domains": unique_domains,
        "used_findings": used_findings,
        "unused_findings": total_findings - used_findings,
        "first_discovery": first_discovery,
        "last_discovery": last_discovery,
        "top_categories": [{"disability_concepts": cat, "count": cnt} for cat, cnt in top_categories],
        "recent_findings": [{"title": title, "domain": domain, "discovered_date": discovered} for title, domain, discovered in recent_findings]
    }
    
    # Save to file
    stats_file = Path("statistics_report.json")
    with open(stats_file, "w") as f:
        json.dump(stats, f, indent=2)
    
    print(f"Statistics report saved to {stats_file}")
    
    # Print summary
    print("\n📊 Disability-AI Collective Statistics")
    print("=" * 40)
    print(f"Total findings in database: {total_findings}")
    print(f"Unique domains: {unique_domains}")
    print(f"Findings used for articles: {used_findings}")
    print(f"Findings available: {total_findings - used_findings}")
    print(f"First discovery: {first_discovery}")
    print(f"Last discovery: {last_discovery}")
    
    print("\n📈 Top Disability Concepts:")
    for cat, cnt in top_categories:
        print(f"  {cat}: {cnt}")
    
    print("\n📰 Recent Findings:")
    for title, domain, discovered in recent_findings:
        print(f"  {title[:50]}... ({domain})")

if __name__ == "__main__":
    generate_statistics()