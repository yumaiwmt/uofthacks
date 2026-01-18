import torch
import torch.nn as nn
from torchvision import transforms as T
from PIL import Image
from pathlib import Path
import os

# 1. Setup Device and Transforms
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
TRANSFORM = T.Compose([
    T.Resize((224, 224)),
    T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# 2. Model Architecture
class CompleteTheLook(nn.Module):
    def __init__(self):
        super().__init__()
        from torchvision.models import resnet50, ResNet50_Weights
        resnet = resnet50(weights=ResNet50_Weights.DEFAULT)
        self.encoder = nn.Sequential(*list(resnet.children())[:-1])
        self.fc = nn.Linear(2048, 512)

    def forward(self, scene, product):
        s_feat = self.fc(self.encoder(scene).flatten(1))
        p_feat = self.fc(self.encoder(product).flatten(1))
        return torch.sum(s_feat * p_feat, dim=1)

@torch.no_grad()
def test_recommendation(model_path, scene_image_path, products_folder, top_k=5):
    prod_path_obj = Path(products_folder)
    
    if not prod_path_obj.exists():
        print(f"❌ ERROR: The folder '{prod_path_obj}' does not exist.")
        print(f"Looked in: {prod_path_obj.absolute()}")
        return []

    valid_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    product_paths = [
        p for p in prod_path_obj.rglob('*') 
        if p.suffix.lower() in valid_extensions
    ]

    if not product_paths:
        print(f"❌ ERROR: No images found in '{prod_path_obj}'.")
        return []

    # Load Model
    model = CompleteTheLook().to(DEVICE)
    if not os.path.exists(model_path):
        print(f"❌ ERROR: Model file '{model_path}' not found.")
        return []
        
    try:
        model.load_state_dict(torch.load(model_path, map_location=DEVICE))
    except Exception as e:
        print(f"❌ ERROR loading model: {e}")
        return []
        
    model.eval()

    # Process Scene
    try:
        scene_img = TRANSFORM(Image.open(scene_image_path).convert("RGB")).unsqueeze(0).to(DEVICE)
    except Exception as e:
        print(f"❌ ERROR opening scene image: {e}")
        return []
    
    # Process and Rank Products
    results = []
    print(f"✅ Found {len(product_paths)} products. Starting inference...")
    
    for p_path in product_paths:
        try:
            prod_img = TRANSFORM(Image.open(p_path).convert("RGB")).unsqueeze(0).to(DEVICE)
            score = model(scene_img, prod_img).item()
            results.append((p_path.name, score))
        except Exception as e:
            continue 

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]

# ===============================
# MAIN EXECUTION (PORTABLE)
# ===============================
if __name__ == "__main__":
    # SCRIPT_DIR is: .../UofTHacks/recommendation_model
    SCRIPT_DIR = Path(__file__).resolve().parent
    
    # REPO_ROOT is: .../UofTHacks
    REPO_ROOT = SCRIPT_DIR.parent 
    
    # --- DYNAMIC RELATIVE PATHS ---
    
    # 1. Products are in the root UofTHacks/data_cache
    PRODUCTS_DIR = REPO_ROOT / "data_cache" / "products"
    
    # 2. Model file is in the root UofTHacks folder
    MODEL_FILE = REPO_ROOT / "fashion_recommender_v1.pth"
    
    # 3. Scene image (Update this if it's also in the root!)
    # If it's in UofTHacks/testing images:
    SCENE_IMG = REPO_ROOT / "testing images" / "alesia-kazantceva-dhD_FiNkuzw-unsplash.jpg"

    # Run the test
    TOP_RECS = test_recommendation(
        model_path=MODEL_FILE,  
        scene_image_path=SCENE_IMG, 
        products_folder=PRODUCTS_DIR 
    )

    # Print Results
    if TOP_RECS:
        print("\n--- Top Recommendations ---")
        for i, (name, score) in enumerate(TOP_RECS, 1):
            print(f"{i}. {name} (Score: {score:.4f})")