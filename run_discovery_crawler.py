#!/usr/bin/env python3
"""
Disability Discovery Crawler - Smart Wrapper
Automatically chooses between mock and production based on network availability
"""

import sys
import os
from datetime import datetime

def test_network_connectivity():
    """Test if we can reach external RSS feeds"""
    test_urls = [
        'https://techcrunch.com/feed/',
        'https://feeds.bloomberg.com/markets/news.rss'
    ]
    
    try:
        import urllib.request
        import socket
        socket.setdefaulttimeout(5)
        
        # Try a simple HEAD request to Google to check general connectivity
        urllib.request.urlopen('https://www.google.com', timeout=5)
        print("✓ Network connectivity detected")
        return True
    except Exception as e:
        print(f"✗ No network connectivity: {e}")
        print("  Falling back to mock data")
        return False

def run_crawler():
    """Run the appropriate crawler based on network availability"""
    print(f"\n{'='*60}")
    print(f"Disability Discovery Crawler - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    has_network = test_network_connectivity()
    
    if has_network:
        print("\nRunning PRODUCTION crawler (real RSS feeds)...")
        try:
            # Try to import and run the production crawler
            from disability_discovery_crawler_simple import SimplifiedDisabilityCrawler
            crawler = SimplifiedDisabilityCrawler()
            findings = crawler.run_crawl()
            return len(findings)
        except Exception as e:
            print(f"✗ Production crawler failed: {e}")
            print("  Falling back to mock crawler...")
            has_network = False
    
    if not has_network:
        print("\nRunning MOCK crawler (simulated data)...")
        try:
            from disability_discovery_crawler_mock import MockDisabilityCrawler
            crawler = MockDisabilityCrawler()
            findings = crawler.run_crawl()
            
            # Also update the cron job that this was a mock run
            with open('crawler_last_run.txt', 'w') as f:
                f.write(f"MOCK_RUN|{datetime.now().isoformat()}|{len(findings)}")
            
            return len(findings)
        except Exception as e:
            print(f"✗ Mock crawler failed: {e}")
            return 0

def main():
    """Main entry point"""
    try:
        findings_count = run_crawler()
        
        print(f"\n{'='*60}")
        if findings_count > 0:
            print(f"✅ CRAWL COMPLETE: Found {findings_count} disability angles")
        else:
            print(f"⚠️  CRAWL COMPLETE: No findings (check network connectivity)")
        print(f"{'='*60}")
        
        # Exit with appropriate code
        sys.exit(0 if findings_count > 0 else 1)
        
    except KeyboardInterrupt:
        print("\n\nCrawler interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
