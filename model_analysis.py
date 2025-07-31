import torch
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image
import numpy as np
import cv2
import os

# Import the model and transforms from feedback.py
import feedback

def analyze_model_prediction(image_path, target_letter):
    """Analyze what the model is actually seeing and predicting"""
    
    print(f"\n🔍 Analyzing model prediction for target letter: {target_letter}")
    print(f"📸 Image path: {image_path}")
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return
    
    # Load and preprocess image
    try:
        image = Image.open(image_path).convert('RGB')
        print(f"✅ Image loaded successfully: {image.size}")
        
        # Apply the same transform as the model
        image_tensor = feedback.transform(image).unsqueeze(0).to(feedback.device)
        print(f"✅ Image transformed: {image_tensor.shape}")
        
        # Get model prediction
        feedback.MyModel.eval()
        with torch.no_grad():
            outputs = feedback.MyModel(image_tensor)
            probabilities = torch.softmax(outputs, dim=1)
            
            # Get top 5 predictions
            top5_prob, top5_indices = torch.topk(probabilities, 5)
            
            print(f"\n📊 Model Predictions (Top 5):")
            for i in range(5):
                predicted_class = feedback.class_names[top5_indices[0][i].item()]
                confidence = top5_prob[0][i].item() * 100
                print(f"  {i+1}. {predicted_class}: {confidence:.2f}%")
            
            # Get the top prediction
            predicted_class = feedback.class_names[top5_indices[0][0].item()]
            confidence = top5_prob[0][0].item() * 100
            
            print(f"\n🎯 Top Prediction: {predicted_class} ({confidence:.2f}%)")
            print(f"🎯 Target Letter: {target_letter}")
            
            # Check if prediction matches target
            if predicted_class == target_letter:
                print("✅ CORRECT PREDICTION!")
            else:
                print("❌ WRONG PREDICTION!")
                
            return predicted_class, confidence
            
    except Exception as e:
        print(f"❌ Error analyzing image: {e}")
        return None, None

def compare_with_reference(user_image_path, target_letter):
    """Compare user image with reference image"""
    
    reference_path = f"correct_images/correct_image_{target_letter}.png"
    
    print(f"\n🔄 Comparing user image with reference:")
    print(f"👤 User image: {user_image_path}")
    print(f"📖 Reference image: {reference_path}")
    
    # Check if reference exists
    if not os.path.exists(reference_path):
        print(f"❌ Reference image not found: {reference_path}")
        return
    
    # Analyze both images
    print(f"\n📊 Analyzing user image:")
    user_pred, user_conf = analyze_model_prediction(user_image_path, target_letter)
    
    print(f"\n📊 Analyzing reference image:")
    ref_pred, ref_conf = analyze_model_prediction(reference_path, target_letter)
    
    # Summary
    print(f"\n📋 SUMMARY:")
    print(f"🎯 Target Letter: {target_letter}")
    print(f"👤 User Image Prediction: {user_pred} ({user_conf:.2f}%)")
    print(f"📖 Reference Image Prediction: {ref_pred} ({ref_conf:.2f}%)")
    
    if user_pred == ref_pred:
        print("✅ Both images predicted the same!")
    else:
        print("❌ Different predictions - this might indicate an issue")

def main():
    """Main analysis function"""
    
    print("🔍 ASL Model Analysis Tool")
    print("=" * 50)
    
    # Check if user image exists
    user_image_path = "correct_images/user_image.jpg"
    if not os.path.exists(user_image_path):
        print(f"❌ No user image found at {user_image_path}")
        print("💡 Please capture an image first using the app")
        return
    
    # Test with different target letters
    test_letters = ['I', 'D', 'C', 'A']
    
    for letter in test_letters:
        print(f"\n{'='*60}")
        print(f"🧪 Testing with target letter: {letter}")
        print(f"{'='*60}")
        
        analyze_model_prediction(user_image_path, letter)
        compare_with_reference(user_image_path, letter)

if __name__ == "__main__":
    main() 