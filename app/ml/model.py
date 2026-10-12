"""
Model Loader and Inference Engine
Loads MobileNetV2 PyTorch weights and provides top-3 disease predictions
"""

import json
from pathlib import Path
from PIL import Image

import torch
import torch.nn as nn
from torchvision import models, transforms

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
WEIGHTS_PATH = BASE_DIR / "weights" / "crop_mobilenetv2_best.pth"
SCRIPTED_PATH = BASE_DIR / "weights" / "crop_mobilenetv2_scripted.pt"
CLASS_NAMES_PATH = BASE_DIR / "training" / "class_names.json"

# Default classes if JSON is not yet generated
DEFAULT_CLASSES = [
    "Onion___Downy_Mildew",
    "Onion___Healthy",
    "Onion___Purple_Blotch",
    "Pomegranate___Anthracnose",
    "Pomegranate___Bacterial_Blight",
    "Pomegranate___Cercospora_Leaf_Spot",
    "Pomegranate___Healthy",
    "Tomato___Early_blight",
    "Tomato___Healthy",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Yellow_Leaf_Curl_Virus"
]

# Device: CPU for local lightweight inference, CUDA if GPU available
DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# ImageNet normalization transform
TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

class CropModelEngine:
    def __init__(self):
        self.device = DEVICE
        self.class_names = self._load_class_names()
        self.model = self._load_model()
        print(f"[*] ML Engine ready on device: {self.device} with {len(self.class_names)} classes.")

    def _load_class_names(self):
        if CLASS_NAMES_PATH.exists():
            try:
                with open(CLASS_NAMES_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return DEFAULT_CLASSES

    def _load_model(self):
        num_classes = len(self.class_names)
        
        # 1. First preference: TorchScript model (fastest inference, zero code dependency)
        if SCRIPTED_PATH.exists():
            try:
                print(f"[*] Loading TorchScript model from {SCRIPTED_PATH}")
                model = torch.jit.load(str(SCRIPTED_PATH), map_location=self.device)
                model.eval()
                return model
            except Exception as e:
                print(f"[!] Could not load TorchScript: {e}")

        # 2. Second preference: PyTorch weights (.pth)
        # Reconstruct MobileNetV2 architecture
        weights = models.MobileNet_V2_Weights.DEFAULT
        model = models.mobilenet_v2(weights=weights)
        in_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(in_features, num_classes)
        )

        if WEIGHTS_PATH.exists():
            try:
                print(f"[*] Loading trained weights from {WEIGHTS_PATH}")
                checkpoint = torch.load(str(WEIGHTS_PATH), map_location=self.device)
                model.load_state_dict(checkpoint)
                print("[*] Successfully loaded custom fine-tuned weights!")
            except Exception as e:
                print(f"[!] Warning loading weights: {e}. Using initialized architecture.")
        else:
            print("[*] No custom weights found yet. Initialized with pretrained MobileNetV2 features.")

        model.to(self.device)
        model.eval()
        return model

    def predict(self, pil_image: Image.Image, top_k: int = 3) -> list[dict]:
        """
        Runs inference on a PIL image.
        Returns top-k predictions with class_name and confidence score.
        """
        # Ensure 3-channel RGB
        rgb_image = pil_image.convert("RGB")
        tensor = TRANSFORM(rgb_image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            outputs = self.model(tensor)
            # Softmax converts raw logits to percentage probabilities (0.0 to 1.0)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]
            
            top_prob, top_indices = torch.topk(probabilities, k=min(top_k, len(self.class_names)))

        results = []
        for rank, (prob, idx) in enumerate(zip(top_prob, top_indices), start=1):
            class_name = self.class_names[idx.item()]
            crop_name = class_name.split("___")[0]
            is_healthy = "healthy" in class_name.lower()
            confidence = float(prob.item())

            results.append({
                "rank": rank,
                "class_name": class_name,
                "crop_name": crop_name,
                "confidence": confidence,
                "confidence_percentage": f"{confidence * 100:.1f}%",
                "is_healthy": is_healthy
            })

        return results

# Singleton instance
model_engine = CropModelEngine()
