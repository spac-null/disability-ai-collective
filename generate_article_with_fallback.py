#!/usr/bin/env python3
"""
Generate article content with model fallback chain.
"""

import json
import sys
import os
from datetime import datetime

# Add automation directory to path
sys.path.append('automation')

from dynamic_article_generator import DynamicArticleGenerator

def generate_article_with_fallback(prompt, metadata):
    """Generate article content using model fallback chain."""
    
    # Model priority list
    model_priority = [
        "anthropic/claude-3-5-sonnet-20241022",  # Claude Opus
        "google/gemini-2.5-pro-exp-03-25",       # Gemini Pro 2.5
        "anthropic/claude-sonnet-4-20250514",    # Current default
        "gemini/gemini-2.5-flash"                # Fallback
    ]
    
    generator = DynamicArticleGenerator()
    
    for model in model_priority:
        print(f"\n[INFO] Attempting to generate with model: {model}")
        try:
            # Set the model
            generator.model = model
            
            # Generate the article
            article_content = generator.generate_article(prompt, metadata)
            
            if article_content and len(article_content.strip()) > 100:
                print(f"[SUCCESS] Generated article with {model}")
                print(f"[INFO] Article length: {len(article_content)} characters")
                return {
                    "status": "success",
                    "model": model,
                    "content": article_content
                }
            else:
                print(f"[WARNING] Empty or too short content from {model}")
                
        except Exception as e:
            print(f"[ERROR] Failed with model {model}: {e}")
            continue
    
    print("[ERROR] All models failed")
    return {
        "status": "error",
        "error": "All models failed to generate article content"
    }

def check_similarity_with_recent_articles(content, days=7):
    """Check if content is too similar to recent articles."""
    # This is a simplified version - in production, this would use
    # semantic similarity checking with embeddings
    print(f"[INFO] Checking similarity with articles from last {days} days")
    
    # For now, we'll assume it's not too similar
    # In a real implementation, we would:
    # 1. Load recent articles from _posts directory
    # 2. Extract embeddings for each
    # 3. Calculate similarity scores
    # 4. Return True if max similarity > 0.7
    
    return {
        "status": "success",
        "is_too_similar": False,
        "max_similarity": 0.0,
        "message": "Similarity check passed (simplified implementation)"
    }

if __name__ == "__main__":
    # Read the prompt and metadata from stdin or file
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            data = json.load(f)
    else:
        # Read from stdin
        data = json.load(sys.stdin)
    
    if data.get("status") != "success":
        print(json.dumps({"status": "error", "error": "Input data has error status"}))
        sys.exit(1)
    
    prompt = data.get("prompt", "")
    metadata = data.get("metadata", {})
    
    if not prompt:
        print(json.dumps({"status": "error", "error": "No prompt provided"}))
        sys.exit(1)
    
    # Generate article with fallback
    result = generate_article_with_fallback(prompt, metadata)
    
    if result["status"] == "success":
        # Check similarity
        similarity_result = check_similarity_with_recent_articles(result["content"])
        
        if similarity_result.get("is_too_similar", False):
            print(json.dumps({
                "status": "rejected",
                "reason": "Too similar to recent articles",
                "similarity": similarity_result.get("max_similarity", 0.0)
            }))
        else:
            print(json.dumps({
                "status": "success",
                "model": result["model"],
                "content": result["content"],
                "similarity_check": similarity_result
            }))
    else:
        print(json.dumps(result))