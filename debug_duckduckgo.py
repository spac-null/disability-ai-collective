#!/usr/bin/env python3
"""
Debug script to understand DuckDuckGo HTTP 202 responses
"""

import urllib.request
import urllib.parse
import re
import time
import random

def test_duckduckgo_search():
    """Test basic DuckDuckGo search"""
    test_queries = [
        "site:wired.com technology",
        "site:techcrunch.com AI",
        "test search",
    ]
    
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    ]
    
    for query in test_queries:
        print(f"\n=== Testing query: '{query}' ===")
        
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://duckduckgo.com/html/?q={encoded_query}"
        
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        try:
            req = urllib.request.Request(search_url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=15) as response:
                print(f"Status: {response.status} {response.reason}")
                print(f"Headers: {dict(response.getheaders())}")
                
                # Read a small amount of content
                content = response.read(5000).decode('utf-8', errors='ignore')
                
                # Check for common patterns
                if '<title>' in content:
                    title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
                    if title_match:
                        print(f"Page title: {title_match.group(1).strip()}")
                
                # Check for result patterns
                if 'result__url' in content:
                    print("Found DuckDuckGo result patterns")
                elif 'no-results' in content.lower():
                    print("No results found")
                else:
                    print("Unknown page structure")
                
                # Save sample for analysis
                with open(f'debug_{query.replace(":", "_")}.html', 'w') as f:
                    f.write(content[:2000])
                
        except Exception as e:
            print(f"Error: {e}")
        
        # Delay between requests
        time.sleep(3)
    
    print("\n=== Testing complete ===")

def test_direct_website():
    """Test direct website access"""
    print("\n=== Testing direct website access ===")
    
    test_urls = [
        "https://www.wired.com/",
        "https://techcrunch.com/",
        "https://www.theverge.com/",
    ]
    
    for url in test_urls:
        print(f"\nTesting: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        try:
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                print(f"Status: {response.status} {response.reason}")
                
                if response.status == 200:
                    # Read just headers and first bit
                    content = response.read(1000).decode('utf-8', errors='ignore')
                    if '<title>' in content:
                        title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
                        if title_match:
                            print(f"Title: {title_match.group(1).strip()[:100]}...")
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(2)

def main():
    print("=== DuckDuckGo Debug Script ===")
    print("Testing network connectivity and DuckDuckGo responses...")
    
    # Test DuckDuckGo
    test_duckduckgo_search()
    
    # Test direct websites
    test_direct_website()
    
    print("\n=== Analysis ===")
    print("If HTTP 202 responses continue, DuckDuckGo may be blocking automated requests.")
    print("Possible solutions:")
    print("1. Use different user agents")
    print("2. Add delays between requests")
    print("3. Use alternative search methods")
    print("4. Check if network has restrictions")

if __name__ == "__main__":
    main()