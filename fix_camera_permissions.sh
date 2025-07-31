#!/bin/bash

echo "🔧 ASL Camera Permission Fix for macOS"
echo "======================================"
echo ""

echo "📋 This script will help you fix camera permissions for the ASL app."
echo ""

echo "🔍 Checking current camera permissions..."
if [ -d "/System/Library/Frameworks/AVFoundation.framework" ]; then
    echo "✅ AVFoundation framework found"
else
    echo "❌ AVFoundation framework not found"
fi

echo ""
echo "📝 Manual steps to fix camera permissions:"
echo "1. Open System Preferences"
echo "2. Go to Security & Privacy"
echo "3. Click on Privacy tab"
echo "4. Select Camera from the left sidebar"
echo "5. Look for 'Terminal' or 'Python' in the list"
echo "6. Check the box to allow camera access"
echo "7. If you don't see Terminal/Python, click the + button and add it"
echo ""

echo "🧪 Testing camera access..."
python3 camera_test.py

echo ""
echo "💡 If the camera test works, your ASL app should work too!"
echo "🚀 Run: streamlit run app.py to start the ASL Learning Assistant" 