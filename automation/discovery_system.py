                elif source["type"] == "calendar":
                    for event in source.get("events", []):
                        items.append({
                            "title": f"Event: {event['name']}",
                            "description": event.get("relevance", "") + " " + event.get("notes", ""),
                            "link": "",
                            "published": event.get("date", ""),
                            "source": source["name"]
                        })
                
                # Process each item
                for item in items:
                    analysis = self.analyze_topic(item["title"], item.get("description", ""))
                    
                    # Only save if disability relevance > 0.2
                    if analysis["disability_relevance"] > 0.2:
                        topic_id = self.generate_topic_id(item["title"], item.get("link", ""))
                        
                        topic_data = {
                            "id": topic_id,
                            "title": item["title"],
                            "description": item.get("description", ""),
                            "source_url": item.get("link", ""),
                            "source_name": item.get("source", source["name"]),
                            "source_type": source["type"],
                            **analysis
                        }
                        
                        if self.save_topic(topic_data):
                            new_topics += 1
                            source_stats[category] += 1
        
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
            
            # Get agent's specialty
            cursor.execute("SELECT specialty, categories FROM agents WHERE name = ?", (agent_name,))
            agent_row = cursor.fetchone()
            
            if not agent_row:
                print(f"[ERROR] Agent {agent_name} not found")
                return None
            
            specialty = agent_row["specialty"].lower()
            categories = agent_row["categories"].lower()
            
            # Build query to find topics matching agent's specialty
            # This is simplified - in production, we'd use more sophisticated matching
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
                
                # Check for specialty keywords
                specialty_keywords = [
                    "deaf", "visual", "design", "pattern" if "pixel nova" in agent_name.lower() else "",
                    "blind", "acoustic", "spatial", "sound" if "siri sage" in agent_name.lower() else "",
                    "wheelchair", "urban", "transport", "economic" if "maya flux" in agent_name.lower() else "",
                    "neurodivergent", "cognitive", "sensory", "interface" if "zen circuit" in agent_name.lower() else ""
                ]
                
                for keyword in specialty_keywords:
                    if keyword and keyword in title_desc:
                        score += 0.2
                
                # Check themes against agent categories
                if topic.get("themes"):
                    themes = json.loads(topic["themes"])
                    for theme in themes:
                        if theme in categories:
                            score += 0.1
                
                scored_topics.append((score, topic))
            
            # Sort by score and return best
            scored_topics.sort(key=lambda x: x[0], reverse=True)
            
            if scored_topics and scored_topics[0][0] > 0.3:
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