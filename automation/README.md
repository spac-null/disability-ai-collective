# Automation System - Disability-AI Collective

## Overview

This automation system powers the daily research and development cycles for the Disability-AI Collective. It runs twice daily to discover cutting-edge developments at the intersection of disability culture and artificial intelligence.

## Daily Schedule

- **Morning (8:00 UTC)**: Research discovery cycle
- **Evening (20:00 UTC)**: Development and accessibility audit cycle

## Scripts

### `research_bot.py`
Main research automation script (requires external dependencies).

### `test_research_bot.py`
Simplified research bot for testing without external dependencies.

### `daily_automation.py`
Orchestrates the daily cycles and handles git operations.

### `simple_check.py`
Basic accessibility compliance checker.

## Directory Structure

```
automation/
├── research_bot.py          # Main research automation
├── test_research_bot.py     # Simplified test version
├── daily_automation.py      # Daily orchestration
└── requirements.txt         # Python dependencies

accessibility/
├── wcag_check.py           # Full accessibility checker
└── simple_check.py         # Basic accessibility checker
```

## How It Works

1. **Morning Cycle**:
   - Discovers new disability-AI developments
   - Creates research logs in `_research/`
   - Generates blog posts in `_posts/`
   - Commits changes to git

2. **Evening Cycle**:
   - Runs accessibility audits
   - Updates website statistics
   - Generates weekly summaries
   - Commits changes to git

## Setting Up Cron Jobs

To run this automation system on a schedule:

```bash
# Morning research (8:00 UTC)
0 8 * * * cd /path/to/disability-ai-collective && python3 automation/daily_automation.py morning

# Evening development (20:00 UTC)  
0 20 * * * cd /path/to/disability-ai-collective && python3 automation/daily_automation.py evening
```

## GitHub Pages Integration

Once the repository is pushed to GitHub, enable GitHub Pages in repository settings:
1. Go to Settings → Pages
2. Select "Deploy from a branch"
3. Choose "main" branch and "/ (root)" folder
4. Save - site will be available at `https://disability-ai-collective.github.io`

## Accessibility Commitment

All automation maintains WCAG 2.1 AA compliance:
- Screen reader optimized content
- Proper heading structure
- Alt text for all images
- High contrast design
- Keyboard navigation support

## Testing

Test the system manually:

```bash
# Test morning cycle
python3 automation/daily_automation.py morning

# Test evening cycle  
python3 automation/daily_automation.py evening

# Test full cycle
python3 automation/daily_automation.py full
```

## Next Steps

1. **Configure GitHub repository** and enable GitHub Pages
2. **Set up cron jobs** for daily automation
3. **Enhance research capabilities** with web scraping
4. **Add social media integration** for content sharing
5. **Implement community engagement** features

## Contributing

This automation system is open to contributions from the disability community and accessibility advocates. See our main [CONTRIBUTING.md](../docs/CONTRIBUTING.md) for details.