#!/bin/bash

# Deployment script for Vercel

echo "🚀 Preparing for Vercel deployment..."

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
    git branch -M main
fi

# Add all files
echo "Adding files to git..."
git add .

# Commit changes
echo "Committing changes..."
git commit -m "Deploy to Vercel: Sentiment Analysis System"

echo "✅ Ready for deployment!"
echo ""
echo "Next steps:"
echo "1. Push to GitHub: git remote add origin <your-repo-url> && git push -u origin main"
echo "2. Go to vercel.com and import your GitHub repository"
echo "3. Vercel will automatically detect the configuration and deploy"
echo ""
echo "Or use Vercel CLI:"
echo "1. npm install -g vercel"
echo "2. vercel login"
echo "3. vercel"
