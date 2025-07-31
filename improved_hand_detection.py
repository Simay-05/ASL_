import cv2
import numpy as np
from PIL import Image
import os

def improved_hand_crop(image_path, output_path="correct_images/user_image.jpg"):
    """
    Improved hand detection and cropping that ensures the AI model gets a proper hand image
    """
    
    # Read the image
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Could not read image: {image_path}")
        return False
    
    print(f"📸 Original image size: {image.shape}")
    
    # Convert to RGB for MediaPipe
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Initialize MediaPipe Hands
    import mediapipe as mp
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=True,
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    
    # Process the image
    results = hands.process(rgb_image)
    
    if results.multi_hand_landmarks:
        print("✅ Hand detected!")
        
        # Get the first hand landmarks
        hand_landmarks = results.multi_hand_landmarks[0]
        
        # Get image dimensions
        h, w, _ = image.shape
        
        # Extract landmark coordinates
        x_coords = [int(lm.x * w) for lm in hand_landmarks.landmark]
        y_coords = [int(lm.y * h) for lm in hand_landmarks.landmark]
        
        # Calculate bounding box with padding
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)
        
        # Add padding (50% of hand size)
        hand_width = x_max - x_min
        hand_height = y_max - y_min
        padding_x = int(hand_width * 0.5)
        padding_y = int(hand_height * 0.5)
        
        # Ensure crop region is within image bounds
        x1 = max(0, x_min - padding_x)
        y1 = max(0, y_min - padding_y)
        x2 = min(w, x_max + padding_x)
        y2 = min(h, y_max + padding_y)
        
        print(f"🔍 Hand bounding box: ({x1}, {y1}) to ({x2}, {y2})")
        print(f"📏 Crop size: {x2-x1} x {y2-y1}")
        
        # Crop the hand region
        hand_crop = image[y1:y2, x1:x2]
        
        # Ensure minimum size (at least 100x100)
        if hand_crop.shape[0] < 100 or hand_crop.shape[1] < 100:
            print("⚠️ Crop too small, using center crop instead")
            return center_crop_fallback(image, output_path)
        
        # Save the cropped image
        cv2.imwrite(output_path, hand_crop)
        print(f"✅ Hand crop saved: {hand_crop.shape}")
        
        # Draw bounding box on original image for debugging
        debug_image = image.copy()
        cv2.rectangle(debug_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.imwrite("debug_hand_detection.jpg", debug_image)
        print("🔍 Debug image saved: debug_hand_detection.jpg")
        
        return True
        
    else:
        print("❌ No hand detected, trying fallback methods...")
        return fallback_cropping(image, output_path)

def center_crop_fallback(image, output_path):
    """Fallback: center crop if hand detection fails"""
    
    h, w = image.shape[:2]
    
    # Calculate center crop (square)
    size = min(h, w)
    y1 = (h - size) // 2
    y2 = y1 + size
    x1 = (w - size) // 2
    x2 = x1 + size
    
    center_crop = image[y1:y2, x1:x2]
    cv2.imwrite(output_path, center_crop)
    
    print(f"✅ Center crop saved: {center_crop.shape}")
    return True

def fallback_cropping(image, output_path):
    """Multiple fallback methods for hand cropping"""
    
    h, w = image.shape[:2]
    print(f"🔄 Trying fallback cropping methods...")
    
    # Method 1: Center square crop
    print("📐 Method 1: Center square crop")
    size = min(h, w)
    y1 = (h - size) // 2
    y2 = y1 + size
    x1 = (w - size) // 2
    x2 = x1 + size
    
    crop1 = image[y1:y2, x1:x2]
    cv2.imwrite("temp_crop1.jpg", crop1)
    
    # Method 2: Full image (resized to square)
    print("📐 Method 2: Full image resized to square")
    crop2 = cv2.resize(image, (512, 512))
    cv2.imwrite("temp_crop2.jpg", crop2)
    
    # Method 3: Top-left quadrant
    print("📐 Method 3: Top-left quadrant")
    crop3 = image[0:h//2, 0:w//2]
    cv2.imwrite("temp_crop3.jpg", crop3)
    
    # Method 4: Center region (75% of image)
    print("📐 Method 4: Center region (75%)")
    y1 = int(h * 0.125)
    y2 = int(h * 0.875)
    x1 = int(w * 0.125)
    x2 = int(w * 0.875)
    crop4 = image[y1:y2, x1:x2]
    cv2.imwrite("temp_crop4.jpg", crop4)
    
    print("✅ Created 4 different crop options:")
    print("  - temp_crop1.jpg: Center square")
    print("  - temp_crop2.jpg: Full image resized")
    print("  - temp_crop3.jpg: Top-left quadrant")
    print("  - temp_crop4.jpg: Center region")
    
    # Use center square as default
    cv2.imwrite(output_path, crop1)
    print(f"✅ Using center square crop: {crop1.shape}")
    
    return True

def test_crops_with_model():
    """Test all crop options with the AI model"""
    
    import feedback
    
    crop_files = [
        "temp_crop1.jpg",
        "temp_crop2.jpg", 
        "temp_crop3.jpg",
        "temp_crop4.jpg"
    ]
    
    print("\n🧪 Testing all crop options with AI model:")
    print("=" * 60)
    
    for i, crop_file in enumerate(crop_files, 1):
        if os.path.exists(crop_file):
            print(f"\n📸 Testing {crop_file}:")
            
            # Load and analyze with model
            image = Image.open(crop_file).convert('RGB')
            image_tensor = feedback.transform(image).unsqueeze(0).to(feedback.device)
            
            feedback.MyModel.eval()
            with torch.no_grad():
                outputs = feedback.MyModel(image_tensor)
                probabilities = torch.softmax(outputs, dim=1)
                
                # Get top 3 predictions
                top3_prob, top3_indices = torch.topk(probabilities, 3)
                
                print(f"  Top 3 predictions:")
                for j in range(3):
                    predicted_class = feedback.class_names[top3_indices[0][j].item()]
                    confidence = top3_prob[0][j].item() * 100
                    print(f"    {j+1}. {predicted_class}: {confidence:.2f}%")
                
                # Check if it's not Blank
                top_pred = feedback.class_names[top3_indices[0][0].item()]
                if top_pred != 'Blank':
                    print(f"  ✅ Good crop! Detected: {top_pred}")
                else:
                    print(f"  ❌ Still detecting Blank")

def main():
    """Main function to improve hand detection"""
    
    print("🔧 Improved Hand Detection System")
    print("=" * 50)
    
    # Check if user image exists
    user_image_path = "correct_images/user_image.jpg"
    if not os.path.exists(user_image_path):
        print(f"❌ No user image found at {user_image_path}")
        print("💡 Please capture an image first using the app")
        return
    
    # Try improved hand detection
    success = improved_hand_crop(user_image_path)
    
    if success:
        print("\n✅ Hand detection completed!")
        print("🧪 Testing crops with AI model...")
        test_crops_with_model()
    else:
        print("\n❌ Hand detection failed!")

if __name__ == "__main__":
    main() 