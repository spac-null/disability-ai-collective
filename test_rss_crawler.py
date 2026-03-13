
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rss_disability_crawler import RSSDisabilityCrawler

class TestCrawler(RSSDisabilityCrawler):
    def fetch_rss_feed(self, rss_url: str): # Override with shorter timeout and more prints
        print(f"[TEST] Fetching RSS: {rss_url}")
        try:
            return super().fetch_rss_feed(rss_url)
        except Exception as e:
            print(f"[TEST] fetch_rss_feed failed for {rss_url}: {e}")
            raise

    def fetch_webpage(self, url: str): # Override with shorter timeout and more prints
        print(f"[TEST] Fetching Webpage: {url}")
        try:
            return super().fetch_webpage(url)
        except Exception as e:
            print(f"[TEST] fetch_webpage failed for {url}: {e}")
            raise

def main():
    print("[TEST] Initializing TestCrawler...")
    crawler = TestCrawler()
    print("[TEST] Initialized. Running crawl...")
    crawler.run_rss_crawl(max_feeds=1, max_articles_per_feed=1) # Limit for testing
    print("[TEST] Crawl finished.")

if __name__ == "__main__":
    main()
