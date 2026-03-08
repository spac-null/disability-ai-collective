# 🚀 Disability-AI Collective - GitHub Setup Guide

## Your Repository
- **URL**: `git@github.com:spac-null/disabilityAI.git`
- **SSH**: Requires SSH key authentication
- **Status**: Empty repository (ready for your code)

## Quick Setup Instructions

### Option A: If you have SSH keys set up on your local machine
```bash
# 1. Clone the empty repository
git clone git@github.com:spac-null/disabilityAI.git
cd disabilityAI

# 2. Copy the project files (from the tarball I created)
# Extract disability-ai-collective.tar.gz and copy contents

# 3. Push everything
git add .
git commit -m "Initial commit: Complete Disability-AI Collective platform"
git push -u origin main
```

### Option B: Using HTTPS (if SSH doesn't work)
```bash
# 1. Clone via HTTPS
git clone https://github.com/spac-null/disabilityAI.git
cd disabilityAI

# 2. Copy project files

# 3. Push (may prompt for GitHub credentials)
git add .
git commit -m "Initial commit"
git push origin main
```

### Option C: GitHub Web Interface
1. Go to https://github.com/spac-null/disabilityAI
2. Click "Add file" → "Upload files"
3. Upload all files from the `disability-ai-collective` folder
4. Commit with message "Initial commit"

## What's in the Project?
✅ **Complete Jekyll website** with accessibility-first design  
✅ **Enhanced research bot** with web scraping capabilities  
✅ **Daily automation scripts** for morning/evening cycles  
✅ **Accessibility checker** (WCAG 2.1 AA compliance)  
✅ **GitHub Actions workflow** for automatic deployment  
✅ **Cron job configuration** for OpenClaw automation  
✅ **Test content** already generated (research logs, blog posts)  

## After Pushing: Enable GitHub Pages
1. Go to: https://github.com/spac-null/disabilityAI/settings/pages
2. Under "Build and deployment", select:
   - **Source**: Deploy from a branch
   - **Branch**: `main`
   - **Folder**: `/ (root)`
3. Click **Save**
4. Your site will be live at: **https://spac-null.github.io/disabilityAI/**

## Automation Will Start Immediately
Once deployed, the cron jobs I set up will:
- **8:00 UTC daily**: Run morning research cycle
- **20:00 UTC daily**: Run evening development cycle
- All findings will be automatically committed and pushed

## Need Help?
If you have issues with SSH keys:
1. Check: `ssh -T git@github.com` (should say "Hi spac-null!")
2. Generate new SSH key: `ssh-keygen -t ed25519 -C "your-email@example.com"`
3. Add to GitHub: https://github.com/settings/keys

## Project Structure Summary
```
disability-ai-collective/
├── _config.yml          # Jekyll configuration
├── index.html           # Homepage
├── _layouts/            # Website templates
├── _posts/              # Blog posts (already has test content)
├── _research/           # Research logs (already has content)
├── automation/          # Research bots and scripts
├── accessibility/       # WCAG compliance tools
├── .github/workflows/   # Auto-deployment to GitHub Pages
└── push-to-github.sh    # Helper script
```

## Next Steps After Deployment
1. **Custom domain** (optional): Buy disabilityAI.com or similar
2. **Social media**: Set up Twitter/Mastodon for announcements
3. **Newsletter**: Collect emails for research updates
4. **Community**: Invite disability community contributors

Your automated disability-AI research platform is ready to go live! 🎉