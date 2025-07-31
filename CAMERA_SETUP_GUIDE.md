# 🎥 ASL Learning Assistant - Camera Setup Guide

## 🚀 Quick Start

Your ASL Learning Assistant is now running! 

**Access it at:** [http://localhost:8501](http://localhost:8501)

## 📸 Camera Setup

### ✅ Camera Test (Recommended First Step)
Run this to test if your camera works:
```bash
python3 camera_test.py
```

### 🔧 Fix Camera Permissions (if needed)
Run this helper script:
```bash
./fix_camera_permissions.sh
```

### 📋 Manual Camera Permission Setup
If the camera doesn't work, follow these steps:

1. **Open System Preferences**
2. **Go to Security & Privacy**
3. **Click Privacy tab**
4. **Select Camera from left sidebar**
5. **Look for 'Terminal' or 'Python' in the list**
6. **Check the box to allow camera access**
7. **If not found, click + and add Terminal/Python**
8. **Restart your terminal**

## 🎯 How to Use the App

### Step 1: Start Page
- See your ASL Learning Assistant logo
- Pick your avatar (emoji)
- Click "Start Learning"

### Step 2: Letter Selection
- Choose any letter from A-Z
- All letters are clickable buttons

### Step 3: Practice Mode
You have **TWO options**:

#### Option A: Camera Capture (Recommended)
- Click "Open Camera and Capture Sign"
- Camera window will open
- Show your hand sign
- Press 'c' to capture
- Press 'ESC' to cancel

#### Option B: Image Upload (Fallback)
- Upload a photo of your hand sign
- Works perfectly if camera has issues

### Step 4: Get Feedback
- See prediction and confidence score
- Get AI-powered feedback
- Compare with correct reference image

## 🔧 Troubleshooting

### Camera Not Working?
1. Run `python3 camera_test.py` to test
2. Check System Preferences → Security & Privacy → Camera
3. Make sure Terminal/Python has camera access
4. Try the image upload option instead

### App Not Loading?
1. Make sure you're in the right directory: `/Users/sim/Desktop/ASLProject`
2. Run `streamlit run app.py`
3. Check the terminal for any error messages

### Model Loading Issues?
The app automatically handles CPU/GPU compatibility.

## 🎉 Features

- ✅ Beautiful interface with your logo
- ✅ Avatar selection
- ✅ Letter picker (A-Z)
- ✅ **Two input methods** (camera + upload)
- ✅ AI model with real-time feedback
- ✅ Image comparison
- ✅ Error handling and user guidance

## 💡 Tips

- **Camera window might appear on a different monitor** - check all your screens
- **Image upload works perfectly** - use it if camera has issues
- **Press 'c' to capture** when your hand sign is ready
- **Press 'ESC' to cancel** camera capture

## 🆘 Need Help?

If you're still having issues:
1. Run `python3 camera_test.py` to test camera
2. Check camera permissions in System Preferences
3. Try the image upload option
4. The app will show helpful error messages

---

**Enjoy practicing your ASL signs! 🤟** 