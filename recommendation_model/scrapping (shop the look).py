# ===============================
# Complete the Look (CTL) – Full Implementation
# ===============================

import os
import json
import random
import logging
from PIL import Image

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

import torchvision.transforms as T
from torchvision import models

try:
    import kagglehub
except ImportError:
    print("Warning: kagglehub not installed. Install with: pip install kagglehub")
    kagglehub = None

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===============================
# 1. Download Dataset
# ===============================

DATASET_PATH = None

try:
    if kagglehub is not None:
        logger.info("Downloading Shop the Look dataset from Kaggle...")
        DATASET_PATH = kagglehub.dataset_download(
            "pypiahmad/shop-the-look-dataset"
        )
        logger.info(f"Dataset path: {DATASET_PATH}")
        
        # Debug: List contents of dataset directory
        logger.info(f"Contents of {DATASET_PATH}:")
        for root, dirs, files in os.walk(DATASET_PATH):
            level = root.replace(DATASET_PATH, '').count(os.sep)
            indent = ' ' * 2 * level
            logger.info(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 2 * (level + 1)
            for file in files[:10]:  # Limit to first 10 files per directory
                logger.info(f'{subindent}{file}')
    else:
        raise ImportError("kagglehub not available")
except Exception as e:
    logger.error(f"Failed to download dataset from Kaggle: {e}")
    logger.info("Ensure you have Kaggle API credentials set up at ~/.kaggle/kaggle.json")
    logger.info("Or manually download the dataset and set DATASET_PATH variable")
    DATASET_PATH = None


# ===============================
# 2. Dataset Validation & Preprocessing
# ===============================

def validate_and_clean_dataset(root, dataset_type='fashion'):
    """
    Validates dataset by checking if all referenced images exist.
    Removes entries with missing images to prevent recursion errors.
    
    Returns:
        cleaned_data: Dictionary with only valid scene-product pairs
        removed_count: Number of entries removed
    """
    logger.info("Starting dataset validation...")
    
    try:
        ann_path = os.path.join(root, f"{dataset_type}.json")
        if not os.path.exists(ann_path):
            json_files = [f for f in os.listdir(root) if f.endswith('.json') and 'cat' not in f]
            if json_files:
                ann_path = os.path.join(root, json_files[0])
        
        # Load raw data
        raw_data = {}
        with open(ann_path, "r") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    scene_id = entry.get("scene", "")
                    product_id = entry.get("product", "")
                    if scene_id not in raw_data:
                        raw_data[scene_id] = {"scene": scene_id + ".jpg", "products": []}
                    if product_id and product_id not in raw_data[scene_id]["products"]:
                        raw_data[scene_id]["products"].append(product_id)
        
        logger.info(f"Loaded {len(raw_data)} total scenes from annotation file")
        
        # Discover actual image directories
        scenes_dir = None
        products_dir = None
        
        for item in os.listdir(root):
            item_path = os.path.join(root, item)
            if os.path.isdir(item_path):
                item_lower = item.lower()
                if 'scene' in item_lower:
                    scenes_dir = item_path
                    logger.info(f"Found scenes directory: {item}")
                elif 'product' in item_lower:
                    products_dir = item_path
                    logger.info(f"Found products directory: {item}")
        
        # If directories not found by name, check subdirectories
        if not scenes_dir or not products_dir:
            images_path = os.path.join(root, "images")
            if os.path.exists(images_path):
                for item in os.listdir(images_path):
                    item_path = os.path.join(images_path, item)
                    if os.path.isdir(item_path):
                        item_lower = item.lower()
                        if 'scene' in item_lower and not scenes_dir:
                            scenes_dir = item_path
                        elif 'product' in item_lower and not products_dir:
                            products_dir = item_path
        
        if not scenes_dir or not products_dir:
            logger.warning(f"Could not find image directories. Scenes: {scenes_dir}, Products: {products_dir}")
            logger.warning("Skipping validation and using all scenes")
            return raw_data, 0
        
        # Validate images exist
        cleaned_data = {}
        removed_count = 0
        
        for scene_id, entry in raw_data.items():
            scene_path = os.path.join(scenes_dir, entry["scene"])
            
            # Check if scene image exists (try different extensions)
            scene_found = os.path.exists(scene_path)
            if not scene_found:
                # Try without extension and search for any match
                base_name = os.path.splitext(entry["scene"])[0]
                for ext in ['.jpg', '.jpeg', '.png', '.JPG']:
                    alt_path = os.path.join(scenes_dir, base_name + ext)
                    if os.path.exists(alt_path):
                        scene_found = True
                        break
            
            if not scene_found:
                removed_count += 1
                continue
            
            # Check if all product images exist
            valid_products = []
            for product_id in entry["products"]:
                product_path = os.path.join(products_dir, product_id + ".jpg")
                if os.path.exists(product_path):
                    valid_products.append(product_id)
                else:
                    # Try alternative extensions
                    for ext in ['.jpeg', '.png', '.JPG', '.JPEG']:
                        alt_path = os.path.join(products_dir, product_id + ext)
                        if os.path.exists(alt_path):
                            valid_products.append(product_id)
                            break
            
            # Keep scene only if it has at least 1 valid product
            if valid_products:
                cleaned_data[scene_id] = {
                    "scene": entry["scene"],
                    "products": valid_products
                }
            else:
                removed_count += 1
        
        logger.info(f"Validation complete: {len(cleaned_data)} valid scenes, {removed_count} removed")
        return cleaned_data, removed_count
    
    except Exception as e:
        logger.error(f"Error during dataset validation: {e}")
        logger.warning("Continuing without validation")
        return raw_data, 0


# ===============================
# 2. Dataset Loader
# ===============================

class ShopTheLookDataset(Dataset):
    def __init__(self, root, transform=None, dataset_type='fashion', validate=True):
        """
        dataset_type: 'fashion' or 'home'
        Loads JSONL format data (one JSON object per line)
        validate: If True, validates dataset and removes bad samples
        """
        self.root = root
        self.transform = transform
        self.dataset_type = dataset_type

        try:
            if validate:
                # Use preprocessed & validated data
                self.data, removed = validate_and_clean_dataset(root, dataset_type)
                logger.info(f"Using {len(self.data)} validated scenes for training")
            else:
                # Load raw data without validation (for inference)
                ann_path = os.path.join(root, f"{dataset_type}.json")
                if not os.path.exists(ann_path):
                    json_files = [f for f in os.listdir(root) if f.endswith('.json') and 'cat' not in f]
                    if json_files:
                        ann_path = os.path.join(root, json_files[0])
                        logger.info(f"Using {json_files[0]} instead of {dataset_type}.json")
                
                self.data = {}
                with open(ann_path, "r") as f:
                    for line in f:
                        if line.strip():
                            entry = json.loads(line)
                            scene_id = entry.get("scene", "")
                            product_id = entry.get("product", "")
                            if scene_id not in self.data:
                                self.data[scene_id] = {"scene": scene_id + ".jpg", "products": []}
                            if product_id and product_id not in self.data[scene_id]["products"]:
                                self.data[scene_id]["products"].append(product_id)
                
                logger.info(f"Loaded {len(self.data)} scenes from {os.path.basename(ann_path)}")
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            raise

        self.scene_ids = list(self.data.keys())

        self.all_products = set()
        for v in self.data.values():
            for p in v["products"]:
                self.all_products.add(p)
        self.all_products = list(self.all_products)
        
        logger.info(f"Found {len(self.all_products)} unique products")

    def __len__(self):
        return len(self.scene_ids)

    def __getitem__(self, idx):
        scene_id = self.scene_ids[idx]
        entry = self.data[scene_id]

        # Try up to 5 times to get a valid sample
        for attempt in range(5):
            try:
                # Handle both full paths (test images) and relative paths (Kaggle dataset)
                scene_path = entry["scene"]
                if not os.path.isabs(scene_path):
                    scene_path = os.path.join(self.root, "images/scenes", scene_path)
                
                scene_img = Image.open(scene_path).convert("RGB")

                pos_id = random.choice(entry["products"])
                neg_id = random.choice(
                    list(set(self.all_products) - set(entry["products"]))
                )

                # Handle both full paths and filenames
                if os.path.isabs(pos_id):
                    pos_path = pos_id
                    neg_path = neg_id
                else:
                    pos_path = os.path.join(self.root, "images/products", pos_id + ".jpg")
                    neg_path = os.path.join(self.root, "images/products", neg_id + ".jpg")

                pos_img = Image.open(pos_path).convert("RGB")
                neg_img = Image.open(neg_path).convert("RGB")

                if self.transform:
                    scene_img = self.transform(scene_img)
                    pos_img = self.transform(pos_img)
                    neg_img = self.transform(neg_img)

                return scene_img, pos_img, neg_img
            except Exception as e:
                logger.debug(f"Error loading item {idx}, attempt {attempt+1}/5: {e}")
                # Try a different sample
                idx = (idx + 1) % len(self)
                scene_id = self.scene_ids[idx]
                entry = self.data[scene_id]
        
        # If all retries failed, return a valid sample we know works
        logger.warning(f"Could not load item after 5 attempts, falling back to index 0")
        return self.__getitem__(0) if idx != 0 else self.__getitem__(1)


# ===============================
# 3. Image Transforms
# ===============================

transform = T.Compose([
    T.Resize((224, 224)),
    T.ToTensor(),
    T.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


# ===============================
# 4. Model Components
# ===============================

class CNNEncoder(nn.Module):
    def __init__(self, embed_dim=512):
        super().__init__()
        resnet = models.resnet50(pretrained=True)
        self.backbone = nn.Sequential(*list(resnet.children())[:-2])
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Linear(2048, embed_dim)

    def forward(self, x):
        spatial = self.backbone(x)
        pooled = self.pool(spatial).flatten(1)
        global_feat = self.fc(pooled)
        return spatial, global_feat


class LocalCompatibility(nn.Module):
    def __init__(self, embed_dim, spatial_dim=2048):
        super().__init__()
        # Project spatial features from 2048 (ResNet) to embed_dim
        self.spatial_proj = nn.Linear(spatial_dim, embed_dim)
        self.linear = nn.Linear(embed_dim, embed_dim)

    def forward(self, spatial_feat, product_feat):
        B, C, H, W = spatial_feat.shape
        # spatial_feat: (B, 2048, H, W)
        spatial_feat = spatial_feat.view(B, C, -1).permute(0, 2, 1)  # (B, H*W, 2048)
        
        # Project to embed_dim
        spatial_feat = self.spatial_proj(spatial_feat)  # (B, H*W, embed_dim)

        proj_prod = self.linear(product_feat).unsqueeze(1)  # (B, 1, embed_dim)
        scores = torch.sum(spatial_feat * proj_prod, dim=-1)  # (B, H*W)
        attn = F.softmax(scores, dim=1)  # (B, H*W)

        return torch.sum(attn.unsqueeze(-1) * spatial_feat, dim=1)  # (B, embed_dim)


class CompleteTheLook(nn.Module):
    def __init__(self, embed_dim=512, lambda_global=0.5):
        super().__init__()
        self.encoder = CNNEncoder(embed_dim)
        self.local = LocalCompatibility(embed_dim)

        self.scene_proj = nn.Linear(embed_dim, embed_dim)
        self.prod_proj = nn.Linear(embed_dim, embed_dim)

        self.lambda_global = lambda_global

    def forward(self, scene, product):
        scene_spatial, scene_global = self.encoder(scene)
        _, prod_global = self.encoder(product)

        g_scene = self.scene_proj(scene_global)
        g_prod = self.prod_proj(prod_global)
        global_score = torch.sum(g_scene * g_prod, dim=1)

        local_scene = self.local(scene_spatial, prod_global)
        local_score = torch.sum(local_scene * prod_global, dim=1)

        return (
            self.lambda_global * global_score +
            (1 - self.lambda_global) * local_score
        )


# ===============================
# 5. Ranking Loss
# ===============================

class RankingLoss(nn.Module):
    def __init__(self, margin=0.2):
        super().__init__()
        self.margin = margin

    def forward(self, pos, neg):
        return torch.mean(torch.clamp(self.margin - pos + neg, min=0))


# ===============================
# 7. Inference / Recommendation
# ===============================

def recommend_products(model, scene_image_path, product_images_dir, device, transform, top_k=5):
    """
    Given a scene image, recommend the top-k matching products.
    
    Args:
        model: Trained CompleteTheLook model
        scene_image_path: Path to the scene image (jpg)
        product_images_dir: Directory containing product images
        device: 'cuda' or 'cpu'
        transform: Image transforms
        top_k: Number of recommendations to return
    
    Returns:
        List of (product_id, score) tuples sorted by score (highest first)
    """
    model.eval()
    
    try:
        # Load and preprocess scene image
        scene_img = Image.open(scene_image_path).convert("RGB")
        scene_img = transform(scene_img).unsqueeze(0).to(device)  # Add batch dimension
        
        # Get all product IDs
        product_files = [f for f in os.listdir(product_images_dir) if f.endswith('.jpg')]
        product_ids = [f.replace('.jpg', '') for f in product_files]
        
        logger.info(f"Evaluating scene against {len(product_ids)} products...")
        
        scores = []
        with torch.no_grad():
            for product_id in product_ids:
                try:
                    product_path = os.path.join(product_images_dir, product_id + '.jpg')
                    product_img = Image.open(product_path).convert("RGB")
                    product_img = transform(product_img).unsqueeze(0).to(device)
                    
                    # Get compatibility score
                    score = model(scene_img, product_img)
                    scores.append((product_id, score.item()))
                except Exception as e:
                    logger.debug(f"Skipping product {product_id}: {e}")
                    continue
        
        # Sort by score (descending)
        scores.sort(key=lambda x: x[1], reverse=True)
        
        recommendations = scores[:top_k]
        logger.info(f"Top {top_k} recommendations:")
        for rank, (product_id, score) in enumerate(recommendations, 1):
            logger.info(f"  {rank}. {product_id}: {score:.4f}")
        
        return recommendations
    
    except Exception as e:
        logger.error(f"Error during recommendation: {e}")
        return []


# ===============================
# 6. Training Loop
# ===============================

def main():
    try:
        if DATASET_PATH is None:
            logger.error("Dataset path is not set. Cannot proceed with training.")
            logger.info("Please either:")
            logger.info("1. Set up Kaggle API credentials (~/.kaggle/kaggle.json)")
            logger.info("2. Or manually download and set DATASET_PATH")
            return
        
        # Create models directory for checkpoints
        models_dir = "./models"
        os.makedirs(models_dir, exist_ok=True)
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {device}")

        logger.info("Loading dataset...")
        # Use testing images as mock dataset
        dataset = ShopTheLookDataset(DATASET_PATH, transform, dataset_type='fashion')
        loader = DataLoader(dataset, batch_size=4, shuffle=True, num_workers=0)  # Reduced batch size for fewer images

        logger.info("Initializing model...")
        model = CompleteTheLook().to(device)
        criterion = RankingLoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)

        logger.info("Starting training...")
        best_loss = float('inf')
        
        for epoch in range(30):  # Train for 30 epochs for better convergence
            model.train()
            total_loss = 0
            batch_count = 0

            try:
                for batch_idx, (scene, pos, neg) in enumerate(loader):
                    scene, pos, neg = scene.to(device), pos.to(device), neg.to(device)

                    pos_score = model(scene, pos)
                    neg_score = model(scene, neg)

                    loss = criterion(pos_score, neg_score)

                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()

                    total_loss += loss.item()
                    batch_count += 1
                    
                    if batch_idx % 10 == 0:
                        logger.info(f"Epoch {epoch+1} | Batch {batch_idx} | Loss: {loss.item():.4f}")

                avg_loss = total_loss / batch_count if batch_count > 0 else 0
                logger.info(f"Epoch {epoch+1} Complete | Avg Loss: {avg_loss:.4f}")
                
                # Save checkpoint after each epoch
                checkpoint_path = os.path.join(models_dir, f"model_epoch_{epoch+1}.pth")
                torch.save(model.state_dict(), checkpoint_path)
                logger.info(f"Saved checkpoint: {checkpoint_path}")
                
                # Save best model
                if avg_loss < best_loss:
                    best_loss = avg_loss
                    best_model_path = os.path.join(models_dir, "model_best.pth")
                    torch.save(model.state_dict(), best_model_path)
                    logger.info(f"New best model saved: {best_model_path} (Loss: {best_loss:.4f})")
                
            except KeyboardInterrupt:
                logger.info("Training interrupted by user")
                logger.info(f"Last checkpoint saved at epoch {epoch+1}")
                break
            except Exception as e:
                logger.error(f"Error during epoch {epoch+1}: {e}")
                continue

        logger.info("Training complete.")
        logger.info(f"Models saved in '{models_dir}' directory")
        logger.info(f"Best model: {os.path.join(models_dir, 'model_best.pth')}")
        logger.info("Usage: python script.py --infer <scene.jpg> <products_dir> ./models/model_best.pth")
    except Exception as e:
        logger.error(f"Critical error in training: {e}", exc_info=True)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--infer":
        # Inference mode
        if len(sys.argv) < 4:
            print("Usage: python script.py --infer <scene_image.jpg> <products_dir> [model_path]")
            sys.exit(1)
        
        scene_image = sys.argv[2]
        products_dir = sys.argv[3]
        model_path = sys.argv[4] if len(sys.argv) > 4 else None
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Running inference on {device}")
        
        # Load model
        model = CompleteTheLook().to(device)
        if model_path:
            try:
                model.load_state_dict(torch.load(model_path))
                logger.info(f"Loaded model from {model_path}")
            except Exception as e:
                logger.warning(f"Could not load model: {e}")
        
        # Get recommendations
        recommendations = recommend_products(model, scene_image, products_dir, device, transform, top_k=10)
        
    else:
        # Training mode
        main()