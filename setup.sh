#!/bin/bash
# One-command setup for Disability-AI Collective
# Run this after extracting the tarball on your local machine

echo "🚀 Setting up Disability-AI Collective..."

# Check if we're in the right directory
if [ ! -f "_config.yml" ]; then
    echo "❌ Error: Please run this script from the disability-ai-collective directory"
    echo "Extract the tarball first: tar -xzf disability-ai-collective.tar.gz"
    exit 1
fi

# Initialize git if not already
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
    git branch -M main
fi

# Check remote
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
if [ -z "$REMOTE_URL" ]; then
    echo "🔗 Setting up GitHub remote..."
    echo "Choose connection method:"
    echo "1) SSH (git@github.com:spac-null/disabilityAI.git) - Recommended if you have SSH keys"
    echo "2) HTTPS (https://github.com/spac-null/disabilityAI.git) - Will prompt for credentials"
    read -p "Enter choice (1 or 2): " choice
    
    case $choice in
        1)
            git remote add origin git@github.com:spac-null/disabilityAI.git
            echo "✅ Set remote to SSH"
            ;;
        2)
            git remote add origin https://github.com/spac-null/disabilityAI.git
            echo "✅ Set remote to HTTPS"
            ;;
        *)
            echo "❌ Invalid choice"
            exit 1
            ;;
    esac
else
    echo "✅ Remote already configured: $REMOTE_URL"
fi

# Add all files
echo "➕ Adding all files to git..."
git add .

# Commit
echo "💾 Creating commit..."
git commit -m "Initial commit: Complete Disability-AI Collective platform
- Accessibility-first Jekyll website
- Enhanced research bot with web scraping
- Daily automation scripts (morning/evening cycles)
- WCAG 2.1 AA compliance checker
- GitHub Actions auto-deployment
- OpenClaw cron job integration
- Test content and research logs"

# Push
echo "📤 Pushing to GitHub..."
echo "Note: You may be prompted for GitHub credentials or SSH passphrase"
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 SUCCESS! Your Disability-AI Collective is now on GitHub!"
    echo ""
    echo "📝 Next steps:"
    echo "1. Enable GitHub Pages:"
    echo "   Go to: https://github.com/spac-null/disabilityAI/settings/pages"
    echo "   Select: Deploy from branch → main → / (root)"
    echo "   Click Save"
    echo ""
    echo "2. Your site will be live at:"
    echo "   https://spac-null.github.io/disabilityAI/"
    echo ""
    echo "3. Automation starts immediately:"
    echo "   - 8:00 UTC daily: Morning research cycle"
    echo "   - 20:00 UTC daily: Evening development cycle"
    echo ""
    echo "4. Check the cron jobs in OpenClaw:"
    echo "   Use: /cron list"
    echo ""
    echo "🏁 Setup complete! Your automated research platform is ready."
else
    echo ""
    echo "❌ Push failed. Common solutions:"
    echo ""
    echo "A) If using SSH:"
    echo "   1. Check SSH keys: ssh -T git@github.com"
    echo "   2. Generate new key: ssh-keygen -t ed25519"
    echo "   3. Add to GitHub: https://github.com/settings/keys"
    echo ""
    echo "B) If using HTTPS:"
    echo "   1. Use personal access token as password"
    echo "   2. Or switch to SSH method"
    echo ""
    echo "C) Try manual push:"
    echo "   git push -u origin main --force"
    echo ""
    exit 1
fi