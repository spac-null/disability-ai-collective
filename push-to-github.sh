#!/bin/bash
# Push script for Disability-AI Collective repository
# Run this from your local machine (not from the container)

echo "🚀 Pushing Disability-AI Collective to GitHub..."

# Check if we're in the right directory
if [ ! -f "_config.yml" ]; then
    echo "❌ Error: Not in the disability-ai-collective directory"
    echo "Please run: cd /path/to/disability-ai-collective"
    exit 1
fi

# Check git status
echo "📊 Git status:"
git status

# Add all changes
echo "➕ Adding changes..."
git add .

# Commit
echo "💾 Committing changes..."
git commit -m "Automated research update $(date +'%Y-%m-%d')"

# Push to GitHub
echo "📤 Pushing to GitHub..."
git push origin main

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed to GitHub!"
    echo "🌐 Your site will be available at: https://spac-null.github.io/disabilityAI/"
    echo ""
    echo "Next steps:"
    echo "1. Go to https://github.com/spac-null/disabilityAI/settings/pages"
    echo "2. Enable GitHub Pages"
    echo "3. Select 'Deploy from a branch'"
    echo "4. Choose 'main' branch and '/ (root)' folder"
    echo "5. Save - your site will be live in a few minutes!"
else
    echo "❌ Failed to push to GitHub"
    echo "You may need to:"
    echo "1. Set up SSH keys: https://docs.github.com/en/authentication/connecting-to-github-with-ssh"
    echo "2. Or use HTTPS with personal access token"
    exit 1
fi