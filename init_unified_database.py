#!/usr/bin/env python3
"""
Initialize unified disability findings database.
Supports multiple source types: rss, web_crawl, api, etc.
"""

import sqlite3
import json
from datetime import datetime

def init_unified_database():
    """Create unified database with findings table"""
    db_path = "disability_findings.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create unified findings table
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
    
    print(f"Unified database initialized: {db_path}")
    print("Table 'findings' created with columns:")
    print("  - id: Unique identifier")
    print("  - url: Source URL")
    print("  - title: Original title")
    print("  - angle: Disability angle/title")
    print("  - confidence: 0.0-1.0 confidence score")
    print("  - domain: Source domain")
    print("  - source_type: 'rss', 'web_crawl', 'api', 'manual'")
    print("  - source_details: JSON with source-specific info")
    print("  - disability_concepts: JSON array of concepts found")
    print("  - content_snippet: Text snippet")
    print("  - discovered_date: When found")
    print("  - publish_date: Original publish date")
    print("  - status: 'pending', 'processed', 'rejected'")
    print("  - processed_date: When processed")
    print("  - used_for_article: Boolean if used")
    print("  - article_id: Link to generated article")
    
    return db_path

def migrate_existing_rss_data():
    """Migrate existing RSS data to unified database"""
    old_db = "rss_disability_findings.db"
    new_db = "disability_findings.db"
    
    try:
        # Connect to old database
        old_conn = sqlite3.connect(old_db)
        old_cursor = old_conn.cursor()
        
        # Connect to new database (re-establish connection to pick up new table schema)
        new_conn = sqlite3.connect(new_db)
        new_cursor = new_conn.cursor()
        
        # Check if old table exists
        old_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rss_findings'")
        if not old_cursor.fetchone():
            print(f"No existing RSS data found in {old_db}")
            return
        
        # Read old data
        old_cursor.execute("SELECT id, url, title, domain, rss_feed, disability_concepts, concept_contexts, confidence, article_idea, discovered_date, content_snippet, publish_date, status FROM rss_findings")
        rows = old_cursor.fetchall()
        
        migrated_count = 0
        
        for row in rows:
            (old_id, old_url, old_title, old_domain, old_rss_feed, old_disability_concepts_json, 
             old_concept_contexts_json, old_confidence, old_article_idea, old_discovered_date, 
             old_content_snippet, old_publish_date, old_status) = row
            
            try:
                # Extract angle from article_idea, or use a default
                angle = old_article_idea if old_article_idea else f"Disability perspective on: {old_title[:50]}..."
                
                # Parse disability concepts JSON and convert to a simplified JSON array of keywords
                disability_concepts_list = []
                try:
                    concepts_dict = json.loads(old_disability_concepts_json)
                    for concept_type, keywords in concepts_dict.items():
                        disability_concepts_list.extend(keywords)
                except:
                    pass
                disability_concepts_json_new = json.dumps(list(set(disability_concepts_list)))
                
                # Prepare source details JSON
                source_details_json = json.dumps({
                    'rss_feed': old_rss_feed,
                    'original_table': 'rss_findings'
                })
                
                # Insert into unified database
                new_cursor.execute('''
                INSERT OR REPLACE INTO findings 
                (id, url, title, angle, confidence, domain, source_type, 
                 source_details, disability_concepts, content_snippet, 
                 discovered_date, publish_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    old_id,
                    old_url,
                    old_title,
                    angle,
                    old_confidence,
                    old_domain,
                    'rss',
                    source_details_json,
                    disability_concepts_json_new,
                    old_content_snippet,
                    old_discovered_date,
                    old_publish_date,
                    old_status
                ))
                
                migrated_count += 1
                
            except Exception as e:
                print(f"Error migrating row {old_id}: {e}")
        
        new_conn.commit()
        
        print(f"Migrated {migrated_count} RSS findings to unified database")
        
    except sqlite3.Error as e:
        print(f"Database migration error: {e}")
    finally:
        if 'old_conn' in locals():
            old_conn.close()
        if 'new_conn' in locals():
            new_conn.close()

if __name__ == "__main__":
    print("=== Initializing Unified Disability Findings Database ===")
    db_path = init_unified_database()
    print("\n=== Migrating Existing RSS Data ===")
    migrate_existing_rss_data()
    print("\n=== Database Setup Complete ===")
    print(f"Unified database: {db_path}")
    print("Ready for RSS, web crawling, and other sources!")