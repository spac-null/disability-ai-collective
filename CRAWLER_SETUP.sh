#!/bin/bash
# Setup guide for Disability Discovery Crawler

echo "================================"
echo "Disability Discovery Crawler Setup"
echo "================================"
echo ""
echo "✓ Simplified crawler created: disability_discovery_crawler_simple.py"
echo "✓ Uses Python standard library only (no external dependencies needed)"
echo "✓ Ready to run immediately"
echo ""

echo "USAGE:"
echo "  python3 disability_discovery_crawler_simple.py"
echo ""

echo "OUTPUT FILES:"
echo "  - disability_findings.json       (all findings as JSON)"
echo "  - disability_findings_report.md  (human-readable report)"
echo "  - disability_findings.db         (SQLite database)"
echo ""

echo "CONFIGURATION:"
echo "To modify sources, edit the 'self.sources' dictionary in the script:"
echo ""
echo "  self.sources = {"
echo "    'tech': [list of RSS feed URLs],"
echo "    'business': [list of RSS feed URLs],"
echo "    'design': [list of RSS feed URLs],"
echo "    'science': [list of RSS feed URLs],"
echo "    'culture': [list of RSS feed URLs],"
echo "  }"
echo ""

echo "KEYWORDS TO DETECT:"
echo "The crawler looks for these disability-related keywords in non-disability content:"
echo "  prosthetic, wheelchair, deaf, blind, neurodiverse, autistic,"
echo "  accessibility, inclusive, sensory, cognitive, mobility, etc."
echo ""

echo "NEXT STEPS:"
echo "1. Test the crawler: python3 disability_discovery_crawler_simple.py"
echo "2. Check outputs: cat disability_findings_report.md"
echo "3. Configure sources as needed"
echo "4. Schedule daily runs with cron"
echo ""

echo "To schedule daily crawls at 06:00 UTC, add to crontab:"
echo "  0 6 * * * cd /path/to/disability-ai-collective && python3 disability_discovery_crawler_simple.py"
echo ""

echo "Setup complete! ✓"
