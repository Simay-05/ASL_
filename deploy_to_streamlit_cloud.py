# 🚀 Streamlit Cloud Deployment Guide
# This will make your ASL Learning Assistant accessible to anyone worldwide!

"""
STEP 1: Create a GitHub Repository
1. Go to https://github.com
2. Create a new repository named "asl-learning-assistant"
3. Upload all your project files to this repository

STEP 2: Deploy to Streamlit Cloud
1. Go to https://share.streamlit.io/
2. Sign in with your GitHub account
3. Click "New app"
4. Select your repository: "asl-learning-assistant"
5. Set the main file path: "app.py"
6. Click "Deploy!"

STEP 3: Share Your Public URL
Once deployed, you'll get a public URL like:
https://your-app-name.streamlit.app

This URL will be accessible to anyone worldwide!
"""

# Required files for deployment:
REQUIRED_FILES = [
    "app.py",
    "feedback.py", 
    "hand_recognition_3.py",
    "improved_hand_detection.py",
    "model_analysis.py",
    "ASL_Model.pth",
    "requirements.txt",
    "correct_images/",
    "American Sign Language Learning Assistant.png"
]

# Important: Make sure all files are in your GitHub repository
# The camera will work on Streamlit Cloud with proper permissions 