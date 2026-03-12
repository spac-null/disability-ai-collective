# Disability-AI Discovery Crawler

A sophisticated Python crawler that finds disability angles in **NON-disability related content**. This tool scans general journalism, tech news, business articles, design publications, and more to discover subtle disability references that could become compelling article ideas for the Disability-AI Collective.

## 🎯 Goal

Find disability angles where they're **NOT** the main topic. The magic is discovering disability perspectives in content that wasn't written about disability.

## ✨ Key Features

1. **Focus on non-disability content** - Crawls general publications, not disability-specific sources
2. **Sophisticated keyword/pattern matching** - Finds subtle disability references
3. **Article idea generation** - Transforms findings into research-ready article concepts
4. **Ethical crawling** - Respects robots.txt, implements rate limiting
5. **Structured output** - SQLite database + JSON export + Markdown reports
6. **Multi-source support** - 15+ pre-configured RSS feeds
7. **Concurrent processing** - Efficient async architecture

## 📊 Example Transformations

| Original Article | Disability Angle |
|-----------------|------------------|
| "New AI Assistant Launches" (TechCrunch) | "How Voice-First AI Excludes Deaf Users" |
| "Future of Remote Work" (Bloomberg) | "Remote Work Finally Includes Disabled Employees — Will It Last?" |
| "Minimalist Office Design" (Dezeen) | "Minimalism as Sensory Exclusion" |
| "VR Gaming Revolution" (The Verge) | "Virtual Reality's Accessibility Problem" |
| "AI in Healthcare" (Nature) | "When Medical AI Overlooks Disability" |

## 🗂️ Sources Crawled

### Tech Journalism
- TechCrunch
- Wired
- The Verge

### Business/Economics
- Bloomberg
- Financial Times
- Harvard Business Review

### Design/Architecture
- Dezeen
- ArchDaily
- Fast Company Design

### Science/Health
- Nature
- New Scientist

### Culture/Entertainment
- Variety
- Hollywood Reporter
- Pitchfork

### General News
- New York Times Technology
- The Guardian Technology
- BBC Technology

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/disability-ai-collective/discovery-crawler.git
cd discovery-crawler

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r crawler_requirements.txt
```

## 🚀 Quick Start

```bash
# Run the crawler (all sources)
python disability_discovery_crawler.py

# Run with specific sources
python disability_discovery_crawler.py --sources TechCrunch Wired

# Run specific categories
python disability_discovery_crawler.py --categories tech design

# Verbose output
python disability_discovery_crawler.py --verbose

# Skip database (testing)
python disability_discovery_crawler.py --skip-db

# See example/demo
python disability_discovery_crawler.py --example
```

## 📁 Output Files

The crawler generates three types of output:

1. **SQLite Database** (`disability_findings.db`)
   - Persistent storage of all findings
   - Enables historical analysis and deduplication
   - Query with: `sqlite3 disability_findings.db`

2. **JSON Export** (`disability_findings.json`)
   - Structured data for integration with other tools
   - Includes all metadata and analysis results

3. **Markdown Report** (`disability_report.md`)
   - Human-readable summary of findings
   - Includes statistics and top discoveries
   - Ready for sharing or publishing

## 🧠 How It Works

### 1. RSS Feed Reading
- Fetches latest articles from configured RSS feeds
- Respects rate limits (3-6 seconds between requests)
- Handles parsing errors gracefully

### 2. Content Analysis
- Scans titles, summaries, and full content
- Uses comprehensive disability keyword dictionary
- Applies regex patterns for contextual matching
- Calculates confidence scores (0.0-1.0)

### 3. Article Idea Generation
- Extracts main topic from original article
- Maps disability keywords to appropriate terminology
- Generates compelling article titles and angles
- Creates research questions for further investigation

### 4. Assignment & Tagging
- Assigns findings to appropriate Disability-AI agents
- Tags articles with categories and keywords
- Enables filtering and organization

## 🔧 Configuration

### Customizing Sources
Edit the `SOURCE_CONFIGS` list in `disability_discovery_crawler.py`:

```python
SOURCE_CONFIGS = [
    SourceConfig(
        name="Your Source",
        rss_url="https://example.com/feed",
        category="your_category",
        rate_limit_seconds=5,
        keywords_boost={'your': 1.2, 'keywords': 1.1}
    ),
    # Add more sources...
]
```

### Adding Disability Keywords
Extend the `DISABILITY_KEYWORDS` dictionary:

```python
DISABILITY_KEYWORDS = {
    'your_keyword': 0.8,  # Confidence score (0.0-1.0)
    # Add more keywords...
}
```

### Custom Patterns
Add regex patterns to `DISABILITY_PATTERNS`:

```python
DISABILITY_PATTERNS = [
    r'your pattern here',
    # Add more patterns...
]
```

## 📈 Monitoring & Statistics

The crawler tracks:
- Source fetch success/error rates
- Confidence score distribution
- Keyword frequency
- Processing time
- Duplicate detection rate

View statistics in the generated report or query the database:

```sql
-- Top sources by findings
SELECT source_name, COUNT(*) as count 
FROM findings 
GROUP BY source_name 
ORDER BY count DESC;

-- Average confidence by category
SELECT tags->>'$[0]' as category, AVG(confidence_score) as avg_confidence
FROM findings 
GROUP BY category 
ORDER BY avg_confidence DESC;
```

## 🤝 Ethical Considerations

This crawler follows ethical web scraping practices:

- **Respects robots.txt** - Checks before crawling
- **Rate limiting** - Configurable delays between requests
- **User-Agent identification** - Clearly identifies as research tool
- **Content minimization** - Only fetches necessary data
- **Attribution** - Always credits original sources
- **Non-commercial** - Research and analysis only

## 🧪 Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=. tests/

# Specific test file
pytest tests/test_analyzer.py -v
```

## 📚 API Reference

### Main Classes

#### `DisabilityDiscoveryCrawler`
Main orchestrator class.

```python
crawler = DisabilityDiscoveryCrawler(configs)
findings = await crawler.crawl_all_sources(max_concurrent=3)
```

#### `ContentAnalyzer`
Analyzes text for disability references.

```python
analyzer = ContentAnalyzer()
result = analyzer.analyze_content(title, summary, full_text)
```

#### `ArticleIdeaGenerator`
Generates article ideas from findings.

```python
generator = ArticleIdeaGenerator()
title, angle, questions = generator.generate_article_idea(
    original_title, category, keywords, context
)
```

#### `DatabaseManager`
Manages SQLite storage.

```python
db = DatabaseManager("findings.db")
db.save_finding(finding)
recent = db.get_recent_findings(limit=50)
```

## 🚨 Troubleshooting

### Common Issues

1. **"Module not found" errors**
   ```bash
   pip install -r crawler_requirements.txt
   ```

2. **Rate limiting from sources**
   - Increase `rate_limit_seconds` in source config
   - Reduce `max_concurrent` parameter

3. **Database locked errors**
   - Ensure only one instance is running
   - Check file permissions

4. **RSS parsing errors**
   - Source may have changed feed format
   - Check feed URL is still valid

### Debug Mode

```bash
python disability_discovery_crawler.py --verbose
```

## 📄 License

MIT License - See LICENSE file for details.

## 🙏 Acknowledgments

- Disability-AI Collective for the vision
- All content sources for making RSS feeds available
- Open source community for the tools that make this possible

## 🤔 FAQ

**Q: Is this legal?**
A: Yes, the crawler follows ethical web scraping practices, respects robots.txt, and only accesses publicly available RSS feeds.

**Q: How often should I run it?**
A: Daily or weekly, depending on your needs. The database prevents duplicates.

**Q: Can I add my own sources?**
A: Yes! Edit the `SOURCE_CONFIGS` list in the script.

**Q: What if a source blocks me?**
A: The crawler includes rate limiting and respects robots.txt. If blocked, increase delays or remove the source.

**Q: How accurate is the analysis?**
A: Confidence scores help filter results. Review generated ideas before publishing.

---

**Happy discovering!** 🎯

*Find the disability angles hiding in plain sight.*