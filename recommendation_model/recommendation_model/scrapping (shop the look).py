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

def cache_pinterest_images(json_folder, target_cache_dir, max_samples=100):
    """
    json_folder: The long path from kagglehub where fashion.json is.
    target_cache_dir: The short path where you want images stored.
    """
    json_folder = Path(json_folder)
    cache_root = Path(target_cache_dir)
    
    scenes_dir = cache_root / "scenes"
    products_dir = cache_root / "products"
    
    scenes_dir.mkdir(parents=True, exist_ok=True)
    products_dir.mkdir(parents=True, exist_ok=True)

    # Note: Kaggle datasets sometimes put the JSON in a subfolder
    ann_path = json_folder / "fashion.json"
    if not ann_path.exists():
        # Fallback search if JSON is nested
        potential_paths = list(json_folder.rglob("fashion.json"))
        if potential_paths:
            ann_path = potential_paths[0]
        else:
            raise FileNotFoundError(f"Could not find fashion.json in {json_folder}")

    count = 0
    logger.info(f"Starting download to short path: {cache_root.absolute()}")
    
    with open(ann_path, "r") as f:
        for line in f:
            if count >= max_samples: break
            entry = json.loads(line)
            s_sig, p_sig = entry["scene"], entry["product"]
            
            s_path = scenes_dir / f"{s_sig}.jpg"
            p_path = products_dir / f"{p_sig}.jpg"
            
            if not s_path.exists():
                img = download_image(signature_to_url(s_sig))
                if img: img.save(s_path)
            
            if not p_path.exists():
                img = download_image(signature_to_url(p_sig))
                if img: img.save(p_path)
                
            if s_path.exists() and p_path.exists():
                count += 1
                if count % 10 == 0: logger.info(f"Cached {count} pairs...")

    return cache_root

# ===============================
# 2. Dataset & Model
# ===============================

class ShopTheLookDataset(Dataset):
    def __init__(self, cache_root, transform=None):
        self.root = Path(cache_root)
        self.transform = transform
        self.scenes = list((self.root / "scenes").glob("*.jpg"))
        self.all_products = list((self.root / "products").glob("*.jpg"))

    def __len__(self):
        return len(self.scenes)

    def __getitem__(self, idx):
        s_path = self.scenes[idx]
        scene_img = Image.open(s_path).convert("RGB")
        
        # Simple random sampling for pos/neg for demonstration
        pos_img = Image.open(random.choice(self.all_products)).convert("RGB") 
        neg_img = Image.open(random.choice(self.all_products)).convert("RGB")

        if self.transform:
            scene_img = self.transform(scene_img)
            pos_img = self.transform(pos_img)
            neg_img = self.transform(neg_img)
            
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
        return torch.sum(s_feat * p_feat, dim=1)

# ===============================
# 3. Main Training Execution
# ===============================

def main():
    # 1. Download/Find dataset via kagglehub
    try:
        import kagglehub
        KAGGLE_PATH = kagglehub.dataset_download("pypiahmad/shop-the-look-dataset")
    except Exception as e:
        logger.error(f"Kagglehub error: {e}")
        return

    # 2. DEFINE SHORT PATH HERE
    # This creates a folder named 'data_cache' in your current project folder
    SHORT_CACHE_PATH = "./data_cache" 
    
    # 3. Scrape and Cache
    cache_dir = cache_pinterest_images(KAGGLE_PATH, SHORT_CACHE_PATH, max_samples=100)
    
    # 4. Training Setup
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    transform = T.Compose([
        T.Resize((224, 224)), 
        T.ToTensor(), 
        T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    dataset = ShopTheLookDataset(cache_dir, transform)
    if len(dataset) == 0:
        logger.error("No images found in cache. Check internet connection or JSON path.")
        return

    loader = DataLoader(dataset, batch_size=8, shuffle=True)
    
    model = CompleteTheLook().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    margin = 0.2

    # 5. Training Loop
    for epoch in range(10):
        model.train()
        epoch_loss = 0
        for scene, pos, neg in loader:
            scene, pos, neg = scene.to(device), pos.to(device), neg.to(device)
            
            pos_score = model(scene, pos)
            neg_score = model(scene, neg)
            
            loss = torch.mean(torch.clamp(margin - pos_score + neg_score, min=0))
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
            
        print(f"Epoch {epoch+1} | Loss: {epoch_loss/len(loader):.4f}")
    
    # 6. Save Weights
    model_path = "fashion_recommender_v1.pth"
    torch.save(model.state_dict(), model_path)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    main()