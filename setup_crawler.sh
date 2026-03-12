#!/bin/bash
# Setup script for Disability Discovery Crawler

set -e  # Exit on error

echo "🚀 Setting up Disability Discovery Crawler"
echo "=========================================="

# Check Python version
echo "Checking Python version..."
python3 --version || { echo "Python 3 is required"; exit 1; }

# Create virtual environment
echo -e "\nCreating virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "Virtual environment created: .venv/"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo -e "\nActivating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo -e "\nUpgrading pip..."
pip install --upgrade pip

# Install dependencies
echo -e "\nInstalling dependencies..."
if [ -f "crawler_requirements.txt" ]; then
    pip install -r crawler_requirements.txt
else
    echo "Warning: crawler_requirements.txt not found"
    echo "Installing core dependencies..."
    pip install aiohttp feedparser beautifulsoup4 lxml aiosqlite python-dateutil
fi

# Create necessary directories
echo -e "\nCreating directories..."
mkdir -p logs
mkdir -p exports
mkdir -p backups

# Test imports
echo -e "\nTesting imports..."
python3 -c "
import aiohttp
import feedparser
import bs4
import aiosqlite
print('✅ All required modules imported successfully')
" || { echo "❌ Import test failed"; exit 1; }

# Run quick test
echo -e "\nRunning quick test..."
if [ -f "test_crawler.py" ]; then
    python3 test_crawler.py
    if [ $? -eq 0 ]; then
        echo "✅ Quick test passed"
    else
        echo "❌ Quick test failed"
        exit 1
    fi
else
    echo "⚠️  test_crawler.py not found, skipping test"
fi

# Create default config if it doesn't exist
if [ ! -f "config.yaml" ] && [ -f "crawler_config.yaml" ]; then
    echo -e "\nCreating config.yaml from template..."
    cp crawler_config.yaml config.yaml
    echo "Created config.yaml (edit to customize)"
fi

# Make scripts executable
echo -e "\nMaking scripts executable..."
chmod +x disability_discovery_crawler.py 2>/dev/null || true
chmod +x test_crawler.py 2>/dev/null || true

echo -e "\n🎉 Setup complete!"
echo -e "\nNext steps:"
echo "1. Review config.yaml (if created)"
echo "2. Run test: python3 test_crawler.py"
echo "3. Run crawler: python3 disability_discovery_crawler.py"
echo "4. Check output: disability_findings.json, disability_report.md"
echo -e "\nFor help: python3 disability_discovery_crawler.py --help"
echo -e "\nTo deactivate virtual environment: deactivate"

# Create a simple run script
cat > run_crawler.sh << 'EOF'
#!/bin/bash
# Simple wrapper to run the crawler

source .venv/bin/activate
python3 disability_discovery_crawler.py "$@"
EOF

chmod +x run_crawler.sh
echo -e "\nCreated run_crawler.sh wrapper script"

# Create a cron example
cat > cron_example.txt << 'EOF'
# Example crontab entries for scheduled crawling
# Run daily at 2 AM
0 2 * * * cd /path/to/disability-ai-collective && .venv/bin/python disability_discovery_crawler.py

# Run every 6 hours
0 */6 * * * cd /path/to/disability-ai-collective && .venv/bin/python disability_discovery_crawler.py

# Run weekdays at 8 AM
0 8 * * 1-5 cd /path/to/disability-ai-collective && .venv/bin/python disability_discovery_crawler.py
EOF

echo -e "\nCreated cron_example.txt with scheduling examples"

echo -e "\n✨ Ready to discover disability angles! ✨"