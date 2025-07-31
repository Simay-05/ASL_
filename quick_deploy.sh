#!/bin/bash

# 🚀 Quick Deploy Script for ASL Learning Assistant
# This script helps you deploy your app to GitHub and Streamlit Cloud

echo "🎯 ASL Learning Assistant - Quick Deploy Script"
echo "================================================"

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Please run this script from your ASLProject directory"
    exit 1
fi

echo "✅ Found app.py - we're in the right directory!"

# Ask for GitHub username
echo ""
echo "📝 Please enter your GitHub username:"
read github_username

# Ask for repository name
echo ""
echo "📝 Enter repository name (or press Enter for 'asl-learning-assistant'):"
read repo_name
repo_name=${repo_name:-asl-learning-assistant}

echo ""
echo "🚀 Starting deployment process..."

# Initialize git repository
echo "📁 Initializing git repository..."
git init

# Add all files
echo "📄 Adding files to git..."
git add .

# Create initial commit
echo "💾 Creating initial commit..."
git commit -m "Initial commit: ASL Learning Assistant with improved hand detection"

# Rename branch to main
echo "🌿 Setting up main branch..."
git branch -M main

# Add remote origin
echo "🔗 Adding GitHub remote..."
git remote add origin https://github.com/$github_username/$repo_name.git

# Push to GitHub
echo "⬆️ Pushing to GitHub..."
git push -u origin main

echo ""
echo "🎉 SUCCESS! Your code is now on GitHub!"
echo ""
echo "📋 Next Steps:"
echo "1. Go to: https://share.streamlit.io/"
echo "2. Sign in with your GitHub account"
echo "3. Click 'New app'"
echo "4. Select repository: $github_username/$repo_name"
echo "5. Set main file path: app.py"
echo "6. Click 'Deploy!'"
echo ""
echo "🌐 Your public URL will be: https://$repo_name.streamlit.app"
echo ""
echo "🎯 Share this URL with anyone - they can access your ASL Learning Assistant from anywhere!"
echo ""
echo "💡 Pro tip: The camera will work on Streamlit Cloud with proper permissions!" 