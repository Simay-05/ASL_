import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import cv2
import numpy as np
import os

class ASLInference:
    def __init__(self, model_path='best_asl_model_new.pth', num_classes=27):
        # Set device - prioritize MPS for Apple Silicon, then CUDA, then CPU
        if torch.backends.mps.is_available():
            self.device = torch.device('mps')
            print(f'Using device: MPS (Apple Silicon GPU)')
        elif torch.cuda.is_available():
            self.device = torch.device('cuda')
            print(f'Using device: CUDA')
        else:
            self.device = torch.device('cpu')
            print(f'Using device: CPU')
        self.num_classes = num_classes
        self.class_names = ['A', 'B', 'Blank', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
        
        # Load model
        self.model = self.create_model()
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()
        
        # Define transforms
        self.transform = transforms.Compose([
            transforms.Resize((448, 448)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    
    def create_model(self):
        """Create the same model architecture as used in training"""
        model = models.resnet18(pretrained=False)
        
        # Replace the final layer
        num_features = model.fc.in_features
        model.fc = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(num_features, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, self.num_classes)
        )
        
        return model.to(self.device)
    
    def predict_image(self, image_path):
        """Predict ASL letter from an image file"""
        # Load and preprocess image
        image = Image.open(image_path).convert('RGB')
        image_tensor = self.transform(image).unsqueeze(0).to(self.device)
        
        # Make prediction
        with torch.no_grad():
            outputs = self.model(image_tensor)
            probabilities = torch.softmax(outputs, dim=1)
            predicted_class = torch.argmax(outputs, dim=1).item()
            confidence = probabilities[0][predicted_class].item()
        
        return self.class_names[predicted_class], confidence
    
    def predict_from_cv2_image(self, cv2_image):
        """Predict ASL letter from OpenCV image"""
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(rgb_image)
        
        # Preprocess
        image_tensor = self.transform(pil_image).unsqueeze(0).to(self.device)
        
        # Make prediction
        with torch.no_grad():
            outputs = self.model(image_tensor)
            probabilities = torch.softmax(outputs, dim=1)
            predicted_class = torch.argmax(outputs, dim=1).item()
            confidence = probabilities[0][predicted_class].item()
        
        return self.class_names[predicted_class], confidence
    
    def preprocess_roi(self, roi):
        """Preprocess ROI for better prediction"""
        # Convert to RGB
        roi_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
        
        # Apply some preprocessing to improve robustness
        # 1. Enhance contrast
        lab = cv2.cvtColor(roi_rgb, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        lab = cv2.merge([l, a, b])
        roi_enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        
        # 2. Apply slight Gaussian blur to reduce noise
        roi_blurred = cv2.GaussianBlur(roi_enhanced, (3, 3), 0)
        
        return roi_blurred
    
    def real_time_prediction(self):
        """Real-time ASL letter recognition using webcam"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Error: Could not open camera")
            return
        
        # Set camera properties for better quality
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        print("Real-time ASL Letter Recognition")
        print("=" * 35)
        print("Controls:")
        print("- Press 'q' to quit")
        print("- Press 's' to save current frame")
        print("- Press 'r' to reset confidence threshold")
        print("- Press '1-9' to manually label (for testing)")
        print()
        
        confidence_threshold = 0.5
        frame_count = 0
        saved_frames = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame")
                break
            
            # Create a copy for display
            display_frame = frame.copy()
            
            # Define region of interest (ROI) for hand detection
            height, width = frame.shape[:2]
            roi_x = int(width * 0.2)
            roi_y = int(height * 0.2)
            roi_w = int(width * 0.6)
            roi_h = int(height * 0.6)
            
            # Draw ROI rectangle
            cv2.rectangle(display_frame, (roi_x, roi_y), (roi_x + roi_w, roi_y + roi_h), (0, 255, 0), 2)
            
            # Extract ROI
            roi = frame[roi_y:roi_y + roi_h, roi_x:roi_x + roi_w]
            
            if roi.size > 0:
                try:
                    # Preprocess ROI for better prediction
                    roi_processed = self.preprocess_roi(roi)
                    
                    # Make prediction
                    predicted_letter, confidence = self.predict_from_cv2_image(roi_processed)
                    
                    # Only show prediction if confidence is above threshold
                    if confidence > confidence_threshold:
                        # Display prediction with color coding
                        color = (0, 255, 0) if confidence > 0.8 else (0, 255, 255) if confidence > 0.6 else (0, 165, 255)
                        text = f"{predicted_letter} ({confidence:.2f})"
                        cv2.putText(display_frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                        
                        # Add confidence bar with color coding
                        bar_width = int(200 * confidence)
                        bar_color = (0, 255, 0) if confidence > 0.8 else (0, 255, 255) if confidence > 0.6 else (0, 165, 255)
                        cv2.rectangle(display_frame, (10, 50), (10 + bar_width, 70), bar_color, -1)
                        cv2.rectangle(display_frame, (10, 50), (210, 70), (255, 255, 255), 2)
                        
                        # Add threshold indicator
                        threshold_pos = int(200 * confidence_threshold)
                        cv2.line(display_frame, (10 + threshold_pos, 50), (10 + threshold_pos, 70), (255, 0, 0), 2)
                    else:
                        # Show low confidence message
                        cv2.putText(display_frame, f"Low confidence: {confidence:.2f}", (10, 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                    # Display frame info
                    cv2.putText(display_frame, f"Frame: {frame_count}", (10, height - 60), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.putText(display_frame, f"Saved: {saved_frames}", (10, height - 40), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.putText(display_frame, f"Threshold: {confidence_threshold:.1f}", (10, height - 20), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    
                except Exception as e:
                    print(f"Prediction error: {e}")
                    cv2.putText(display_frame, "Prediction Error", (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Display frame
            cv2.imshow('ASL Letter Recognition', display_frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('s'):
                # Save current frame
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"captured_frame_{timestamp}_{frame_count}.jpg"
                cv2.imwrite(filename, frame)
                print(f"Saved frame: {filename}")
                saved_frames += 1
            elif key == ord('r'):
                # Reset confidence threshold
                confidence_threshold = 0.5
                print("Reset confidence threshold to 0.5")
            elif key in [ord(str(i)) for i in range(1, 10)]:
                # Manual labeling for testing
                letter_map = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F', 7: 'G', 8: 'H', 9: 'I'}
                letter = letter_map[key - ord('0')]
                print(f"Manual label: {letter}")
            
            frame_count += 1
        
        cap.release()
        cv2.destroyAllWindows()
        print(f"\nSession ended. Total frames processed: {frame_count}")

def test_model_on_sample_images():
    """Test the model on a few sample images from the dataset"""
    inference = ASLInference()
    
    # Test on a few images from each class
    test_dir = 'asl_new/Test_Alphabet'
    
    for class_name in os.listdir(test_dir):
        class_dir = os.path.join(test_dir, class_name)
        if os.path.isdir(class_dir):
            # Get first image from each class
            images = [f for f in os.listdir(class_dir) if f.endswith('.png')]
            if images:
                test_image_path = os.path.join(class_dir, images[0])
                predicted_letter, confidence = inference.predict_image(test_image_path)
                
                print(f"Actual: {class_name}, Predicted: {predicted_letter}, Confidence: {confidence:.3f}")

def test_model_on_real_data(model_path='best_asl_model_new.pth'):
    """Test the trained model on real camera data"""
    inference = ASLInference(model_path)
    real_data_dir = 'real_camera_data'
    
    if not os.path.exists(real_data_dir):
        print("No real data found. Run collect_real_data.py first.")
        return
    
    print("Testing model on real camera data...")
    print("=" * 40)
    
    total_correct = 0
    total_images = 0
    results_by_lighting = {}
    
    for lighting_condition in os.listdir(real_data_dir):
        condition_dir = os.path.join(real_data_dir, lighting_condition)
        if os.path.isdir(condition_dir):
            print(f"\nLighting condition: {lighting_condition}")
            print("-" * 30)
            
            condition_correct = 0
            condition_total = 0
            
            for image_file in os.listdir(condition_dir):
                if image_file.endswith('.jpg'):
                    image_path = os.path.join(condition_dir, image_file)
                    
                    # Extract expected letter from filename if available
                    expected_letter = None
                    if '_' in image_file:
                        parts = image_file.split('_')
                        if len(parts) >= 3 and parts[1] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                            expected_letter = parts[1]
                    
                    # Make prediction
                    try:
                        predicted_letter, confidence = inference.predict_image(image_path)
                        
                        print(f"Image: {image_file}")
                        print(f"Predicted: {predicted_letter} (confidence: {confidence:.3f})")
                        
                        if expected_letter:
                            print(f"Expected: {expected_letter}")
                            if predicted_letter == expected_letter:
                                print("✓ CORRECT")
                                total_correct += 1
                                condition_correct += 1
                            else:
                                print("✗ INCORRECT")
                            total_images += 1
                            condition_total += 1
                        else:
                            print("No expected label provided")
                        
                        print()
                    except Exception as e:
                        print(f"Error processing {image_file}: {e}")
            
            # Store results for this lighting condition
            if condition_total > 0:
                condition_accuracy = condition_correct / condition_total
                results_by_lighting[lighting_condition] = condition_accuracy
                print(f"Accuracy for {lighting_condition}: {condition_accuracy:.3f} ({condition_correct}/{condition_total})")
    
    # Print overall results
    if total_images > 0:
        overall_accuracy = total_correct / total_images
        print(f"\nOverall accuracy on real data: {overall_accuracy:.3f} ({total_correct}/{total_images})")
        
        print("\nAccuracy by lighting condition:")
        for condition, accuracy in results_by_lighting.items():
            print(f"  {condition}: {accuracy:.3f}")

if __name__ == '__main__':
    import sys
    
    # Check if model exists
    if not os.path.exists('best_asl_model_new.pth'):
        print("Error: Model file 'best_asl_model_new.pth' not found. Please train the model first.")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            print("Testing model on real camera data...")
            test_model_on_real_data()
        elif sys.argv[1] == 'sample':
            print("Testing model on sample dataset images...")
            test_model_on_sample_images()
        else:
            print("Usage:")
            print("  python asl_inference.py          # Real-time recognition")
            print("  python asl_inference.py test     # Test on real camera data")
            print("  python asl_inference.py sample   # Test on sample dataset")
    else:
        print("Starting real-time ASL letter recognition...")
        inference = ASLInference()
        inference.real_time_prediction() 