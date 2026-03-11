#!/usr/bin/env python3
"""
Discovery System for Disability-AI Collective (Self-Contained Version)
- Focuses on core logic of topic management and agent assignment
- Simulates discovery using predefined data (no external dependencies)
- Updates topic database internally
"""

import os
import sys
import json
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class DiscoverySystem:
    def __init__(self, db_path: str = None):
        self.repo_root = Path(__file__).parent.parent
        self.db_path = db_path or (self.repo_root / "automation" / "topics.db")
        
        # Keywords to prioritize
        self.priority_keywords = [
            "disability", "accessibility", "inclusive", "assistive", "accommodation",
            "deaf", "blind", "wheelchair", "neurodivergent", "autistic", "disabled",
            "representation", "inclusion", "equity", "barrier", "universal design",
            "film", "movie", "oscar", "awards", "cinema", "actor", "casting", "prosthetics"
        ]
        
        # Initialize database
        self.init_database()
        
        print(f"[DISCOVERY] System initialized. DB at {self.db_path}")
    
    def init_database(self):
        """Initialize SQLite database for topic storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Topics table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS topics (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            source_url TEXT,
            source_name TEXT,
            source_type TEXT,
            discovered_date TEXT,
            relevance_score REAL DEFAULT 0.0,
            disability_relevance REAL DEFAULT 0.0,
            uniqueness_score REAL DEFAULT 0.0,
            freshness_score REAL DEFAULT 0.0,
            total_score REAL DEFAULT 0.0,
            themes TEXT,
            key_quotes TEXT,
            statistics TEXT,
            assigned_agent TEXT,
            publication_status TEXT DEFAULT 'discovered',
            published_date TEXT,
            published_article_id TEXT,
            overlap_warning TEXT,
            notes TEXT
        )
        ''')
        
        # Agents table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS agents (
            name TEXT PRIMARY KEY,
            specialty TEXT,
            perspective TEXT,
            categories TEXT,
            last_article_date TEXT,
            article_count INTEGER DEFAULT 0
        )
        ''')
        
        # Initialize agents if not exists
        agents = [
            ("Pixel Nova", "deaf visual design, pattern recognition, visual accessibility", 
             "deaf designer focusing on visual communication and information hierarchy", 
             "Visual Design,Accessibility Innovation,Deaf Culture,Entertainment,Design"),
            ("Siri Sage", "cognitive accessibility, spatial design, acoustic architecture", 
             "blind spatial designer focusing on multi-sensory environments", 
             "Spatial Design,Cognitive Accessibility,Acoustic Design,Entertainment,Design"),
            ("Maya Flux", "urban accessibility, transportation equity, disability economics", 
             "wheelchair user focusing on urban infrastructure and economic barriers", 
             "Urban Design,Accessibility Economics,Transportation,Entertainment,Policy"),
            ("Zen Circuit", "neurodivergent interface design, cognitive load, sensory processing", 
             "autistic software designer focusing on cognitive accessibility", 
             "Neurodiversity,Interface Design,Sensory Processing,Technology,Design")
        ]
        
        for agent in agents:
            cursor.execute('''
            INSERT OR IGNORE INTO agents (name, specialty, perspective, categories) 
            VALUES (?, ?, ?, ?)
            ''', agent)
        
        conn.commit()
        conn.close()
        print(f"[DATABASE] Initialized at {self.db_path}")
    
    def get_disability_events(self) -> List[Dict]:
        """Get upcoming disability-related events"""
        today = datetime.now().date()
        events = []
        
        # Major disability awareness days
        disability_days = [
            {"name": "International Day of Persons with Disabilities", "date": f"{today.year}-12-03"},
            {"name": "World Autism Awareness Day", "date": f"{today.year}-04-02"},
            {"name": "World Hearing Day", "date": f"{today.year}-03-03"},
            {"name": "World Sight Day", "date": f"{today.year}-10-10"},
            {"name": "International Day of Sign Languages", "date": f"{today.year}-09-23"},
        ]
        
        # Add Oscar awards if within 2 weeks
        oscar_date = self.find_oscar_date(today.year)
        if oscar_date:
            days_until = (oscar_date - today).days
            if -7 <= days_until <= 14:  # Week before to 2 weeks after
                events.append({
                    "title": "Event: Academy Awards (Oscars)",
                    "description": "Opportunity for articles on disability casting, representation, awards",
                    "link": "",
                    "published": oscar_date.isoformat(),
                    "source": "Calendar - Oscars",
                    "source_type": "event"
                })
        
        for day in disability_days:
            event_date = datetime.strptime(day["date"], '%Y-%m-%d').date()
            days_until_event = (event_date - today).days
            if 0 <= days_until_event <= 30: # Upcoming within a month
                 events.append({
                    "title": f"Event: {day['name']}",
                    "description": f"Global awareness for {day['name'].lower()}",
                    "link": "",
                    "published": event_date.isoformat(),
                    "source": "Calendar",
                    "source_type": "event"
                })
        
        return events
    
    def find_oscar_date(self, year: int) -> Optional[datetime.date]:
        """Find Oscar awards date for given year (mocked for self-contained version)"""
        # For demo: if today is March 11, 2026, Oscar was March 8, 2026
        if year == 2026: # Given current date context in prompt
            return datetime(2026, 3, 8).date()
        return None
    
    def fetch_mock_data(self) -> List[Dict]:
        """Simulate fetching diverse topics"""
        mock_topics = [
            {
                "title": "The Prosthetics Paradox: Why Casting Disabled Actors Beats Hollywood Makeup",
                "description": "Analysis of disability representation shift from 'cripping up' to authentic casting. Explores economic and artistic value of authenticity vs. expensive prosthetics, with case studies of recent films.",
                "source_url": "https://www.nrc.nl/nieuws/2026/03/10/de-beste-films-van-het-jaar-zitten-vol-met-amateurs-a4922648",
                "source_name": "NRC Article - Film",
                "source_type": "news",
                "published": "2026-03-10"
            },
            {
                "title": "Neurodivergent Time: Why Standard Productivity Tools Fail Us",
                "description": "Examining how traditional productivity tools are built for a neurotypical brain, and why they often create more barriers for neurodivergent individuals. Proposes new design principles for inclusive productivity.",
                "source_url": "",
                "source_name": "Internal Idea - Neurodiversity",
                "source_type": "research_idea",
                "published": "2026-03-05"
            },
            {
                "title": "AI for All: How Accessible Machine Learning Models Benefit Everyone",
                "description": "Exploring the concept of inclusive AI design, where models are trained with diverse datasets and evaluated for accessibility. Demonstrates how this approach leads to more robust and fair AI systems.",
                "source_url": "",
                "source_name": "Internal Idea - AI Accessibility",
                "source_type": "research_idea",
                "published": "2026-03-01"
            },
            {
                "title": "Urban Planning with a Cane and Wheelchair: Rethinking City Mobility",
                "description": "A critical look at how urban infrastructure often neglects the needs of disabled pedestrians and wheelchair users. Case studies of cities successfully implementing universal design principles for transportation and public spaces.",
                "source_url": "",
                "source_name": "Internal Idea - Urban Design",
                "source_type": "research_idea",
                "published": "2026-02-28"
            }
        ]
        return mock_topics + self.get_disability_events()
    
    def analyze_topic(self, title: str, description: str = "", published_date: str = None) -> Dict:
        """Analyze topic for relevance scores and themes"""
        text = f"{title} {description}".lower()
        
        # Calculate disability relevance
        disability_relevance = 0.0
        for keyword in self.priority_keywords:
            if keyword in text:
                disability_relevance += 0.1 # Simple count
        disability_relevance = min(disability_relevance, 1.0)  # Cap at 1.0
        
        # Calculate uniqueness (simplified - would need comparison with existing topics and articles)
        uniqueness_score = 0.8 # Assume high uniqueness for mock data
        
        # Calculate freshness
        freshness_score = 0.7 # Default
        if published_date:
            try:
                pub_dt = datetime.fromisoformat(published_date).date()
                days_since_pub = (datetime.now().date() - pub_dt).days
                if days_since_pub <= 7: # Very fresh
                    freshness_score = 1.0
                elif days_since_pub <= 30: # Moderately fresh
                    freshness_score = 0.8
                elif days_since_pub > 90: # Older
                    freshness_score = 0.3
                else:
                    freshness_score = 0.5
            except ValueError:
                pass # Use default if date parsing fails
        
        # Total score
        total_score = (disability_relevance * 0.5 + 
                      uniqueness_score * 0.3 + 
                      freshness_score * 0.2)
        
        # Extract themes
        themes = self.extract_themes(text)
        
        return {
            "disability_relevance": disability_relevance,
            "uniqueness_score": uniqueness_score,
            "freshness_score": freshness_score,
            "total_score": total_score,
            "themes": themes,
        }
    
    def extract_themes(self, text: str) -> List[str]:
        """Extract thematic categories from text"""
        themes = []
        
        theme_patterns = {
            "technology": r"\b(tech|digital|ai|machine learning|software|app|device)\b",
            "policy": r"\b(policy|law|regulation|legislation|government|compliance)\b",
            "education": r"\b(education|school|university|training|curriculum)\b",
            "employment": r"\b(employment|job|workplace|career|hiring)\b",
            "healthcare": r"\b(health|medical|therapy|treatment|hospital)\b",
            "transportation": r"\b(transport|transit|mobility|travel|commute)\b",
            "housing": r"\b(housing|home|accommodation|living|shelter)\b",
            "entertainment": r"\b(film|movie|tv|media|entertainment|game|oscar|awards|hollywood|casting|actor|representation)\b",
            "design": r"\b(design|architecture|urban|product|interface|visual|spatial|aesthetic)\b",
            "research": r"\b(research|study|data|analysis|finding|report)\b",
            "neurodiversity": r"\b(neurodivergent|autism|adhd|neurotypical|cognitive)\b"
        }
        
        for theme, pattern in theme_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                themes.append(theme)
        
        return themes
    
    def generate_topic_id(self, title: str, source_url: str) -> str:
        """Generate unique ID for topic using a simplified hash"""
        content = f"{title}{source_url}".encode('utf-8')
        # Use a simple string hash instead of hashlib for no external deps
        return str(abs(hash(content)))[:12]
    
    def save_topic(self, topic_data: Dict) -> bool:
        """Save discovered topic to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if topic already exists
            cursor.execute("SELECT id FROM topics WHERE id = ?", (topic_data["id"],))
            if cursor.fetchone():
                print(f"[SKIP] Topic already exists: {topic_data['title'][:50]}...")
                conn.close()
                return False
            
            # Insert new topic
            cursor.execute('''
            INSERT INTO topics (
                id, title, description, source_url, source_name, source_type,
                discovered_date, relevance_score, disability_relevance,
                uniqueness_score, freshness_score, total_score, themes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                topic_data["id"],
                topic_data["title"],
                topic_data.get("description", ""),
                topic_data.get("source_url", ""),
                topic_data.get("source_name", ""),
                topic_data.get("source_type", ""),
                datetime.now().isoformat(),
                topic_data.get("total_score", 0.0),
                topic_data.get("disability_relevance", 0.0),
                topic_data.get("uniqueness_score", 0.0),
                topic_data.get("freshness_score", 0.0),
                topic_data.get("total_score", 0.0),
                json.dumps(topic_data.get("themes", []))
            ))
            
            conn.commit()
            conn.close()
            
            print(f"[SAVED] New topic: {topic_data['title'][:60]}... (Score: {topic_data.get('total_score', 0):.2f})")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to save topic: {e}")
            return False
    
    def run_discovery(self) -> Dict:
        """Run full discovery process across all sources (simulated)"""
        print("[DISCOVERY] Starting simulated discovery run...")
        
        new_topics = 0
        source_stats = {"mock_data": 0, "calendar": 0}
        
        items = self.fetch_mock_data()
        
        for item in items:
            analysis = self.analyze_topic(item["title"], item.get("description", ""), item.get("published", None))
            
            if analysis["disability_relevance"] > 0.2:
                topic_id = self.generate_topic_id(item["title"], item.get("link", ""))
                
                topic_data = {
                    "id": topic_id,
                    "title": item["title"],
                    "description": item.get("description", ""),
                    "source_url": item.get("link", ""),
                    "source_name": item.get("source", "Mock Data"),
                    "source_type": item.get("source_type", "mock"),
                    "published_date": item.get("published", None),
                    **analysis
                }
                
                if self.save_topic(topic_data):
                    new_topics += 1
                    if topic_data["source_type"] == "event": # Check source_type, not source_name
                        source_stats["calendar"] += 1
                    else:
                        source_stats["mock_data"] += 1
        
        print(f"[DISCOVERY] Complete. Found {new_topics} new topics.")
        print(f"  Source breakdown: {source_stats}")
        
        return {
            "new_topics": new_topics,
            "source_stats": source_stats,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_top_topics(self, limit: int = 20, min_score: float = 0.5) -> List[Dict]:
        """Get top scoring topics from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM topics 
            WHERE total_score >= ? 
            AND publication_status = 'discovered'
            ORDER BY total_score DESC, discovered_date DESC
            LIMIT ?
            ''', (min_score, limit))
            
            rows = cursor.fetchall()
            topics = [dict(row) for row in rows]
            
            # Parse JSON fields
            for topic in topics:
                if topic.get("themes"):
                    topic["themes"] = json.loads(topic["themes"])
            
            conn.close()
            return topics
            
        except Exception as e:
            print(f"[ERROR] Failed to get topics: {e}")
            return []
    
    def assign_agent_to_topic(self, topic_id: str, agent_name: str) -> bool:
        """Assign an agent to a topic for article writing"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            UPDATE topics 
            SET assigned_agent = ?, publication_status = 'assigned'
            WHERE id = ?
            ''', (agent_name, topic_id))
            
            # Update agent's last article date
            cursor.execute('''
            UPDATE agents 
            SET last_article_date = ?
            WHERE name = ?
            ''', (datetime.now().isoformat(), agent_name))
            
            conn.commit()
            conn.close()
            
            print(f"[ASSIGNED] Topic {topic_id[:8]}... to {agent_name}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to assign agent: {e}")
            return False
    
    def get_agent_stats(self) -> Dict:
        """Get statistics for all agents"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT name, specialty, last_article_date, article_count,
                   julianday('now') - julianday(last_article_date) as days_since_last
            FROM agents
            ''')
            
            rows = cursor.fetchall()
            agents = {}
            
            for row in rows:
                agent_data = dict(row)
                # Convert days_since_last to float (or None if no last article)
                if agent_data["last_article_date"]:
                    agent_data["days_since_last"] = float(agent_data["days_since_last"]) if agent_data["days_since_last"] else None
                else:
                    agent_data["days_since_last"] = None
                agents[agent_data["name"]] = agent_data
            
            conn.close()
            return agents
            
        except Exception as e:
            print(f"[ERROR] Failed to get agent stats: {e}")
            return {}
    
    def select_best_topic_for_agent(self, agent_name: str) -> Optional[Dict]:
        """Select the best topic for a specific agent based on their specialty"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get agent's specialty and categories
            cursor.execute("SELECT specialty, categories FROM agents WHERE name = ?", (agent_name,))
            agent_row = cursor.fetchone()
            
            if not agent_row:
                print(f"[ERROR] Agent {agent_name} not found")
                return None
            
            specialty = agent_row["specialty"].lower()
            categories = agent_row["categories"].lower()
            agent_categories = [c.strip() for c in categories.split(',')]
            
            # Build query to find topics matching agent's specialty
            query = '''
            SELECT * FROM topics 
            WHERE publication_status = 'discovered'
            AND total_score >= 0.6
            ORDER BY total_score DESC
            LIMIT 20
            '''
            
            cursor.execute(query)
            rows = cursor.fetchall()
            topics = [dict(row) for row in rows]
            
            # Score each topic for this agent
            scored_topics = []
            for topic in topics:
                score = 0.0
                title_desc = f"{topic['title']} {topic.get('description', '')}".lower()
                topic_themes = json.loads(topic.get("themes", "[]"))
                
                # Match agent specialty keywords to topic text
                agent_keywords_map = {
                    "pixel nova": ["deaf", "visual", "design", "pattern", "representation", "film", "movie"],
                    "siri sage": ["blind", "acoustic", "spatial", "sound", "architecture", "sensory", "film", "movie"],
                    "maya flux": ["wheelchair", "urban", "transport", "economic", "policy", "representation", "film", "movie"],
                    "zen circuit": ["neurodivergent", "cognitive", "sensory", "interface", "technology", "ai", "productivity"]
                }
                
                agent_specific_keywords = agent_keywords_map.get(agent_name.lower(), [])
                for keyword in agent_specific_keywords:
                    if keyword in title_desc:
                        score += 0.2
                
                # Match topic themes against agent categories
                for theme in topic_themes:
                    if theme in agent_categories:
                        score += 0.15
                
                # Boost for events, especially Oscars if relevant to agent
                if topic.get("source_type") == "event" and "oscar" in topic["title"].lower():
                    if "entertainment" in agent_categories or "design" in agent_categories or "policy" in agent_categories: # all agents could have a take
                        score += 0.3 # Significant boost for timely event
                
                scored_topics.append((score, topic))
            
            # Sort by score and return best
            scored_topics.sort(key=lambda x: x[0], reverse=True)
            
            if scored_topics and scored_topics[0][0] > 0.3: # Lower threshold to make sure topics are found
                best_topic = scored_topics[0][1]
                if best_topic.get("themes"):
                    best_topic["themes"] = json.loads(best_topic["themes"])
                print(f"[SELECTED] Best topic for {agent_name}: {best_topic['title'][:50]}... (Score: {scored_topics[0][0]:.2f})")
                return best_topic
            
            print(f"[WARNING] No suitable topic found for {agent_name}")
            return None
            
        except Exception as e:
            print(f"[ERROR] Failed to select topic for agent: {e}")
            return None

def main():
    """Main function for testing discovery system"""
    print("=== Disability-AI Discovery System ===\n")
    
    # Initialize system
    discovery = DiscoverySystem()
    
    # Run discovery
    result = discovery.run_discovery()
    
    print(f"\nDiscovery Results:")
    print(f"  New topics found: {result['new_topics']}")
    print(f"  Source breakdown: {result['source_stats']}")
    
    # Get top topics
    print(f"\nTop Topics in Database:")
    top_topics = discovery.get_top_topics(limit=5)
    for i, topic in enumerate(top_topics, 1):
        print(f"  {i}. {topic['title'][:60]}...")
        print(f"     Score: {topic['total_score']:.2f}, Themes: {topic.get('themes', [])}")
        print(f"     Source: {topic['source_name']}")
        print()
    
    # Get agent statistics
    print(f"\nAgent Statistics:")
    agents = discovery.get_agent_stats()
    for name, stats in agents.items():
        days = stats.get('days_since_last', 'Never')
        print(f"  {name}: {stats['specialty'][:40]}...")
        print(f"     Last article: {days} days ago")
        print()
    
    # Test topic selection for each agent
    print(f"\nTopic Selection Test:")
    for agent_name in ["Pixel Nova", "Siri Sage", "Maya Flux", "Zen Circuit"]:
        topic = discovery.select_best_topic_for_agent(agent_name)
        if topic:
            print(f"  {agent_name}: {topic['title'][:50]}...")
        else:
            print(f"  {agent_name}: No suitable topic found")

if __name__ == "__main__":
    main()