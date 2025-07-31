import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import cv2
import numpy as np
import os
import requests
import json

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

# Initialize the improved ASL inference system
try:
    asl_inference = ASLInference('best_asl_model_new.pth')
    print("✅ Improved ASL model loaded successfully!")
except Exception as e:
    print(f"❌ Error loading improved model: {e}")
    asl_inference = None

def compare_signs(correct_path: str, user_path: str, predicted_letter: str, target_letter: str) -> str:
    """Compare user sign with correct reference using Ollama LLaVA (optional)"""
    try:
        # Try to get AI feedback from Ollama
        prompt = f"""
        You are an ASL (American Sign Language) expert. Compare these two hand signs:
        
        Reference image: {correct_path} (shows correct sign for letter '{target_letter}')
        User image: {user_path} (user's attempt, AI predicted '{predicted_letter}')
        
        Analyze the user's hand position compared to the reference and provide specific feedback:
        1. Is the sign correct? (Yes/No/Close)
        2. What specific adjustments are needed?
        3. Tips for improvement
        
        Be encouraging and helpful. Keep response under 100 words.
        """
        
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'llava',
                'prompt': prompt,
                'stream': False
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', 'AI feedback unavailable.')
        else:
            return f"AI feedback unavailable. Your sign was recognized as '{predicted_letter}'. Please compare your hand position with the reference image."
            
    except requests.exceptions.ConnectionError:
        return f"AI feedback unavailable (Ollama not running). Your sign was recognized as '{predicted_letter}'. Please compare your hand position with the reference image."
    except requests.exceptions.Timeout:
        return f"AI feedback unavailable (timeout). Your sign was recognized as '{predicted_letter}'. Please compare your hand position with the reference image."
    except Exception as e:
        return f"AI feedback unavailable. Your sign was recognized as '{predicted_letter}'. Please compare your hand position with the reference image."

def predict_and_feedback(image_path, target_letter):
    """Predict ASL letter and provide feedback using the improved model"""
    if asl_inference is None:
        return {
            'predicted_class': 'Error',
            'feedback': 'Model not loaded properly.',
            'success': False
        }
    
    try:
        # Make prediction using the improved model
        predicted_letter, confidence = asl_inference.predict_image(image_path)
        
        # Generate feedback
        correct_path = f"correct_images/correct_image_{target_letter}.png"
        
        if predicted_letter == target_letter:
            feedback = f"🎉 Perfect! You signed '{target_letter}' correctly!"
        elif predicted_letter == 'Blank':
            feedback = "🔍 No clear hand sign detected. Please ensure your hand is clearly visible and well-lit."
        else:
            # Try to get AI feedback, fallback to basic feedback
            try:
                ai_feedback = compare_signs(correct_path, image_path, predicted_letter, target_letter)
                feedback = ai_feedback
            except:
                feedback = f"📝 Close! You signed '{predicted_letter}' instead of '{target_letter}'. Please compare your hand position with the reference image."
        
        return {
            'predicted_class': predicted_letter,
            'feedback': feedback,
            'success': True
        }
        
    except Exception as e:
        return {
            'predicted_class': 'Error',
            'feedback': f'Error processing image: {str(e)}',
            'success': False
        }

def predict_from_cv2_image(cv2_image):
    """Predict ASL letter from OpenCV image using the improved model"""
    if asl_inference is None:
        return 'Error', 0.0
    
    try:
        # Preprocess the image for better prediction
        processed_image = asl_inference.preprocess_roi(cv2_image)
        
        # Make prediction
        predicted_letter, confidence = asl_inference.predict_from_cv2_image(processed_image)
        
        return predicted_letter, confidence
        
    except Exception as e:
        print(f"Prediction error: {e}")
        return 'Error', 0.0 