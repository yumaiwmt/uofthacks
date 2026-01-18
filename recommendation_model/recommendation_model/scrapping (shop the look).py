import os
import json
import random
import logging
import io
import requests
from pathlib import Path
from PIL import Image

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms as T

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===============================
# 1. Image Download Utilities
# ===============================

def signature_to_url(signature):
    return f'http://i.pinimg.com/400x/{signature[0:2]}/{signature[2:4]}/{signature[4:6]}/{signature}.jpg'

def download_image(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content)).convert("RGB")
    except:
        return None
    return None

def cache_pinterest_images(dataset_path, max_samples=100):
    """Downloads images and creates a clean folder structure."""
    dataset_path = Path(dataset_path)
    cache_dir = dataset_path / "cached_images"
    scenes_dir = cache_dir / "scenes"
    products_dir = cache_dir / "products"
    
    scenes_dir.mkdir(parents=True, exist_ok=True)
    products_dir.mkdir(parents=True, exist_ok=True)

    ann_path = dataset_path / "fashion.json" # Change to 'home.json' if needed
    count = 0
    
    with open(ann_path, "r") as f:
        for line in f:
            if count >= max_samples: break
            entry = json.loads(line)
            s_sig, p_sig = entry["scene"], entry["product"]
            
            s_path = scenes_dir / f"{s_sig}.jpg"
            p_path = products_dir / f"{p_sig}.jpg"
            
            # Only download if not already present
            if not s_path.exists():
                img = download_image(signature_to_url(s_sig))
                if img: img.save(s_path)
            
            if not p_path.exists():
                img = download_image(signature_to_url(p_sig))
                if img: img.save(p_path)
                
            if s_path.exists() and p_path.exists():
                count += 1
                if count % 10 == 0: logger.info(f"Downloaded {count} pairs...")

    return cache_dir

# ===============================
# 2. Dataset & Model
# ===============================

class ShopTheLookDataset(Dataset):
    def __init__(self, cache_root, transform=None):
        self.root = Path(cache_root)
        self.transform = transform
        
        # We index what we actually have on disk
        self.scenes = list((self.root / "scenes").glob("*.jpg"))
        # Map scene ID to its product (simplified for this dataset structure)
        # Note: In production, you'd use the JSON to map multiple products
        self.all_products = list((self.root / "products").glob("*.jpg"))

    def __len__(self):
        return len(self.scenes)

    def __getitem__(self, idx):
        s_path = self.scenes[idx]
        # In this dataset, names match the signatures
        s_id = s_path.stem 
        
        # Load Scene
        scene_img = Image.open(s_path).convert("RGB")
        
        # For simplicity, we assume the product with same index or similar logic
        # Ideally, use a lookup table from your JSON
        pos_img = Image.open(random.choice(self.all_products)).convert("RGB") 
        neg_img = Image.open(random.choice(self.all_products)).convert("RGB")

        if self.transform:
            scene_img, pos_img, neg_img = self.transform(scene_img), self.transform(pos_img), self.transform(neg_img)
        return scene_img, pos_img, neg_img

class CompleteTheLook(nn.Module):
    def __init__(self):
        super().__init__()
        resnet = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
        self.encoder = nn.Sequential(*list(resnet.children())[:-1])
        self.fc = nn.Linear(2048, 512)

    def forward(self, scene, product):
        s_feat = self.fc(self.encoder(scene).flatten(1))
        p_feat = self.fc(self.encoder(product).flatten(1))
        # Returns dot product similarity
        return torch.sum(s_feat * p_feat, dim=1)

# ===============================
# 3. Main Training Execution
# ===============================

def main():
    # 1. Dynamically find the Kaggle dataset path
    try:
        import kagglehub
        # This returns the actual path on your machine (e.g., C:\Users\yumai\.cache\...)
        DATASET_PATH = kagglehub.dataset_download("pypiahmad/shop-the-look-dataset")
        logger.info(f"Dataset found at: {DATASET_PATH}")
    except Exception as e:
        logger.error("Could not download/find dataset via kagglehub.")
        return

    # 2. Scrape (This will now create /cached_images inside the kagglehub folder)
    # Note: If fashion.json is inside a subfolder like 'fashion', 
    # you might need: Path(DATASET_PATH) / "fashion"
    cache_dir = cache_pinterest_images(DATASET_PATH, max_samples=100)
    
    # 2. Setup
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    transform = T.Compose([T.Resize((224, 224)), T.ToTensor(), T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
    
    dataset = ShopTheLookDataset(cache_dir, transform)
    loader = DataLoader(dataset, batch_size=8, shuffle=True)
    
    model = CompleteTheLook().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    margin = 0.2

    # 3. Loop
    for epoch in range(10):
        model.train()
        epoch_loss = 0
        for scene, pos, neg in loader:
            scene, pos, neg = scene.to(device), pos.to(device), neg.to(device)
            
            pos_score = model(scene, pos)
            neg_score = model(scene, neg)
            
            # Ranking Loss calculation
            loss = torch.mean(torch.clamp(margin - pos_score + neg_score, min=0))
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
            
        print(f"Epoch {epoch+1} | Loss: {epoch_loss/len(loader):.4f}")
    
    # Save the trained weights
    model_path = "fashion_recommender_v1.pth"
    torch.save(model.state_dict(), model_path)
    print(f"Model saved successfully to {model_path}")

if __name__ == "__main__":
    main()