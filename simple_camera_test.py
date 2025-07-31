#!/usr/bin/env python3
import cv2
import os
import numpy as np
from PIL import Image

def test_camera_simple():
    """Simple camera test without cv2.imshow"""
    print("🔍 Testing camera access...")
    
    # Set environment variables for macOS
    os.environ['OPENCV_AVFOUNDATION_SKIP_AUTH'] = '1'
    
    try:
        # Try to open camera
        print("📹 Attempting to open camera...")
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Failed to open camera!")
            return False, "Camera not accessible"
        
        # Set camera properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        print("✅ Camera opened successfully!")
        
        # Try to read a frame
        print("📸 Testing frame capture...")
        ret, frame = cap.read()
        
        if not ret:
            print("❌ Failed to read frame from camera!")
            cap.release()
            return False, "Failed to read frame"
        
        print("✅ Frame captured successfully!")
        print(f"📐 Frame size: {frame.shape}")
        
        # Test hand detection
        print("🤚 Testing hand detection...")
        try:
            from hand_recognition_3 import HandTrackingDynamic
            detector = HandTrackingDynamic()
            
            # Process frame
            frame = detector.findFingers(frame, draw=False)
            lmsList, bbox = detector.findPosition(frame, draw=True)
            
            if lmsList:
                print("✅ Hand detected successfully!")
                print(f"📏 Hand landmarks: {len(lmsList)} points")
            else:
                print("⚠️ No hand detected in frame (this is normal)")
            
        except Exception as e:
            print(f"⚠️ Hand detection test failed: {e}")
        
        # Save a test image
        test_image_path = "camera_test_image.jpg"
        cv2.imwrite(test_image_path, frame)
        print(f"💾 Test image saved: {test_image_path}")
        
        cap.release()
        print("✅ Camera test completed successfully!")
        return True, "Camera working perfectly"
        
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        return False, str(e)

if __name__ == "__main__":
    print("🎥 ASL Camera Test (Simplified)")
    print("=" * 40)
    
    success, message = test_camera_simple()
    
    if success:
        print(f"\n🎉 {message}")
        print("You can now use the ASL app with camera!")
    else:
        print(f"\n⚠️ {message}")
        print("\n💡 Try these solutions:")
        print("1. Check System Preferences → Security & Privacy → Camera")
        print("2. Make sure Terminal/Python has camera access")
        print("3. Use the image upload option in the app") 