import torch
from torchvision import transforms
from torch.utils.data import Dataset
from torchvision import datasets
from torchvision.transforms import ToTensor
import matplotlib.pyplot as plt
from torch.utils.data import DataLoader
import torchvision
from torch import nn
from torchsummary import summary
import torch.nn.functional as F
import torch.optim as optim
from torchvision import models
from torch.utils.data import DataLoader, random_split
import base64
import json
import requests


import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image 
from tqdm import tqdm
import random
import os
import cv2

OLLAMA_URL = "http://localhost:11434/api/generate"

class_names = [
    'A', 'B', 'Blank', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O',
    'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'
]

def compare_signs(correct_path: str, user_path: str, predicted_letter: str, probability: str, target_letter: str) -> str:
    def b64(p): 
        return base64.b64encode(open(p, "rb").read()).decode()

    payload = {
        "model": "llava",
        "stream": False,
        "system": (
            """
You will give feedback regarding letters depicted in American Sign Language. You will be given two images. One will be the correct depiction of a letter and the other will be the one done by the user. Give feedback to the user to help them reach the correct gesture by highlighting the difference between the hands in the images. Only use the given pictures for reference and do not refer to previous knowledge regarding American Sign Language."""
        ),
        "prompt": (
            f"""
The first given image is the correct depiction of the letter {target_letter} in american sign language and the second given image is a depiction of the letter {target_letter} in american sign language done by the user. The second image is a gesture done by the user that was recognized by a separate model as the letter '{predicted_letter}', the confidence of the model in this guess is {probability} out of 1. The second image may be correct or partially incorrect when compared to the correct image, please provide your feedback accordingly. Please provide textual feedback for the user who has done the hand gesture in the second image to help them reach the correct depiction of the letter {target_letter}."""
        ),
        "images": [b64(correct_path), b64(user_path)]
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=10)
        response.raise_for_status()
        return json.loads(response.text)["response"].strip()
    except requests.exceptions.ConnectionError:
        return f"AI feedback unavailable (Ollama not running). Your sign was recognized as '{predicted_letter}' with {float(probability)*100:.1f}% confidence. You were trying to sign '{target_letter}'. Please compare your hand position with the reference image."
    except requests.exceptions.Timeout:
        return f"AI feedback timeout. Your sign was recognized as '{predicted_letter}' with {float(probability)*100:.1f}% confidence. You were trying to sign '{target_letter}'. Please compare your hand position with the reference image."
    except Exception as e:
        return f"AI feedback error: {str(e)}. Your sign was recognized as '{predicted_letter}' with {float(probability)*100:.1f}% confidence. You were trying to sign '{target_letter}'. Please compare your hand position with the reference image."


def sharpen_image(img: Image.Image) -> Image.Image:
    img_np = np.array(img)

    # Eğer grayscale'se tek kanal olur; bunu OpenCV'nin beklediği formatta işle
    if len(img_np.shape) == 2:
        img_cv = img_np
    else:
        img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

    # Sharpening kernel
    kernel = np.array([[0, -1, 0],
                       [-1, 5,-1],
                       [0, -1, 0]])

    sharpened = cv2.filter2D(img_cv, -1, kernel)

    # Eğer tek kanallıysa, doğrudan geri döndür
    if len(sharpened.shape) == 2:
        return Image.fromarray(sharpened)
    else:
        sharpened_rgb = cv2.cvtColor(sharpened, cv2.COLOR_BGR2RGB)
        return Image.fromarray(sharpened_rgb)


transform = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.Resize((200, 200)),
    transforms.Lambda(lambda img: sharpen_image(img)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5], std=[0.5]),
])

os.environ['CUDA_LAUNCH_BLOCKING'] = '1'
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class SimpleCNN(nn.Module):
    def __init__(self, num_classes=27):
        super(SimpleCNN, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, 1)
        self.conv2 = nn.Conv2d(32, 64, 3, 1)
        self.conv3 = nn.Conv2d(64, 128, 3, 1)
        self.fc1 = nn.Linear(128 * 23 * 23, 512)
        self.fc2 = nn.Linear(512, num_classes)
        self.dropout = nn.Dropout(0.5)
        self.pool = nn.MaxPool2d(2, 2)
    
    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = self.pool(F.relu(self.conv3(x)))
        x = x.view(-1, 128 * 23 * 23)  # Flatten the tensor
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x


MyModel = SimpleCNN()  # Define your model
MyModel.load_state_dict(torch.load('ASL_Model.pth', map_location=torch.device('cpu')))
MyModel = MyModel.to(device)

def predict_and_feedback(model, image_path, transform, device, correct_path, user_path, target_letter):
    # Load the image
    image = Image.open(image_path).convert('RGB')
    
    # Preprocess the image
    image_tensor = transform(image).unsqueeze(0).to(device)
    
    # Set the model to evaluation mode
    model.eval()
    
    with torch.no_grad():
        # Make a prediction
        outputs = model(image_tensor)
        _, predicted = torch.max(outputs, 1)
        predicted_class = class_names[predicted.item()]
        probs = torch.softmax(outputs, dim=1)
        top_prob, pred = torch.max(probs, dim=1)
        
        # Get feedback from the AI model
        feedback_text = compare_signs(correct_path, user_path, predicted_class, str(top_prob.item()), target_letter)
        
        # Return prediction info and feedback
        return {
            'predicted_class': predicted_class,
            'confidence': top_prob.item(),
            'feedback': feedback_text
        }