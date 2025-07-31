#!/usr/bin/env python3
import cv2
import os
import sys

def test_camera():
    print("🔍 Testing camera access...")
    
    # Set environment variables for macOS camera permissions
    os.environ['OPENCV_AVFOUNDATION_SKIP_AUTH'] = '1'
    
    # Try to open camera
    print("📹 Attempting to open camera...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Failed to open camera!")
        print("\n🔧 To fix this:")
        print("1. Go to System Preferences → Security & Privacy → Privacy → Camera")
        print("2. Find 'Terminal' or 'Python' in the list")
        print("3. Check the box to allow camera access")
        print("4. Restart your terminal and try again")
        return False
    
    print("✅ Camera opened successfully!")
    
    # Try to read a frame
    print("📸 Testing frame capture...")
    ret, frame = cap.read()
    
    if not ret:
        print("❌ Failed to read frame from camera!")
        cap.release()
        return False
    
    print("✅ Frame captured successfully!")
    print(f"📐 Frame size: {frame.shape}")
    
    # Show the frame briefly
    print("🖼️  Displaying camera feed (press 'q' to quit)...")
    cv2.imshow('Camera Test - Press q to quit', frame)
    
    # Wait for key press
    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("✅ Camera test completed successfully!")
    return True

if __name__ == "__main__":
    print("🎥 ASL Camera Permission Test")
    print("=" * 40)
    
    success = test_camera()
    
    if success:
        print("\n🎉 Camera is working! You can now use the ASL app.")
    else:
        print("\n⚠️  Camera test failed. Please check permissions and try again.")
        print("\n💡 Alternative: You can still use the image upload feature in the app!") 