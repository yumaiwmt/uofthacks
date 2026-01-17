#!/usr/bin/env python
# ===============================
# Product Recommendation Inference
# ===============================

import os
import sys
import json
import logging
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
import torchvision.transforms as T
from torchvision import models

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===============================
# Model Architecture (same as training)
# ===============================

class CNNEncoder(nn.Module):
    def __init__(self, embed_dim=512):
        super().__init__()
        resnet = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
        self.backbone = nn.Sequential(*list(resnet.children())[:-2])
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Linear(2048, embed_dim)

    def forward(self, x):
        spatial = self.backbone(x)
        pooled = self.pool(spatial).flatten(1)
        global_feat = self.fc(pooled)
        return spatial, global_feat


class LocalCompatibility(nn.Module):
    def __init__(self, embed_dim):
        super().__init__()
        self.linear = nn.Linear(embed_dim, embed_dim)

    def forward(self, spatial_feat, product_feat):
        B, C, H, W = spatial_feat.shape
        spatial_feat = spatial_feat.view(B, C, -1).permute(0, 2, 1)

        proj_prod = self.linear(product_feat).unsqueeze(1)
        scores = torch.sum(spatial_feat * proj_prod, dim=-1)
        attn = F.softmax(scores, dim=1)

        return torch.sum(attn.unsqueeze(-1) * spatial_feat, dim=1)


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
# Image Transforms
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
# Recommendation Function
# ===============================

def get_image_files(directory):
    """Get all image files from a directory"""
    if not os.path.exists(directory):
        logger.error(f"Directory not found: {directory}")
        return []
    
    image_files = []
    for f in os.listdir(directory):
        if f.lower().endswith(('.jpg', '.jpeg', '.png')):
            image_files.append(os.path.join(directory, f))
    
    return image_files


def score_products_for_image(model, image_path, product_images_dir, device):
    """Score all products for a single image. Returns dict of product_id -> score"""
    try:
        # Load and preprocess image
        img = Image.open(image_path).convert("RGB")
        img = transform(img).unsqueeze(0).to(device)
        
        # Get all product IDs
        product_files = [f for f in os.listdir(product_images_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        scores = {}
        
        with torch.no_grad():
            for product_file in product_files:
                try:
                    product_id = product_file.rsplit('.', 1)[0]
                    product_path = os.path.join(product_images_dir, product_file)
                    
                    product_img = Image.open(product_path).convert("RGB")
                    product_img = transform(product_img).unsqueeze(0).to(device)
                    
                    # Get compatibility score
                    score = model(img, product_img)
                    scores[product_id] = score.item()
                
                except Exception as e:
                    logger.debug(f"Skipping product {product_file}: {e}")
                    continue
        
        return scores
    
    except Exception as e:
        logger.error(f"Error scoring products for {image_path}: {e}")
        return {}


def recommend_from_preferences(model, liked_folder, disliked_folder, product_images_dir, device, top_k=10):
    """
    Recommend products based on liked and disliked outfit folders.
    
    Args:
        model: Trained CompleteTheLook model
        liked_folder: Folder with liked outfit images
        disliked_folder: Folder with disliked outfit images
        product_images_dir: Directory containing product images
        device: 'cuda' or 'cpu'
        top_k: Number of recommendations to return
    
    Returns:
        Dict with recommendations and metadata
    """
    model.eval()
    
    # Get image files
    liked_images = get_image_files(liked_folder)
    disliked_images = get_image_files(disliked_folder)
    
    if not liked_images:
        logger.error(f"No images found in liked folder: {liked_folder}")
        return {}
    
    logger.info(f"Found {len(liked_images)} liked images and {len(disliked_images)} disliked images")
    
    # Score products for liked images
    logger.info("Scoring liked outfits...")
    liked_scores = {}
    for i, image_path in enumerate(liked_images):
        logger.info(f"  Processing liked image {i+1}/{len(liked_images)}: {os.path.basename(image_path)}")
        scores = score_products_for_image(model, image_path, product_images_dir, device)
        
        # Aggregate scores
        for product_id, score in scores.items():
            if product_id not in liked_scores:
                liked_scores[product_id] = []
            liked_scores[product_id].append(score)
    
    # Score products for disliked images
    logger.info("Scoring disliked outfits...")
    disliked_scores = {}
    for i, image_path in enumerate(disliked_images):
        logger.info(f"  Processing disliked image {i+1}/{len(disliked_images)}: {os.path.basename(image_path)}")
        scores = score_products_for_image(model, image_path, product_images_dir, device)
        
        # Aggregate scores
        for product_id, score in scores.items():
            if product_id not in disliked_scores:
                disliked_scores[product_id] = []
            disliked_scores[product_id].append(score)
    
    # Calculate final recommendation scores
    # Higher score for products that match liked outfits
    # Lower score for products that match disliked outfits
    recommendations = {}
    
    for product_id in liked_scores:
        avg_liked = sum(liked_scores[product_id]) / len(liked_scores[product_id])
        avg_disliked = sum(disliked_scores.get(product_id, [0])) / max(len(disliked_scores.get(product_id, [0])), 1)
        
        # Final score: higher match with liked - lower match with disliked
        final_score = avg_liked - (0.5 * avg_disliked)
        recommendations[product_id] = {
            "score": float(final_score),
            "liked_avg": float(avg_liked),
            "disliked_avg": float(avg_disliked)
        }
    
    # Sort by score
    sorted_recs = sorted(recommendations.items(), key=lambda x: x[1]["score"], reverse=True)
    top_recommendations = sorted_recs[:top_k]
    
    result = {
        "status": "success",
        "metadata": {
            "liked_images": len(liked_images),
            "disliked_images": len(disliked_images),
            "total_products_scored": len(recommendations),
            "top_k": top_k,
            "timestamp": str(__import__('datetime').datetime.now())
        },
        "recommendations": [
            {
                "rank": rank,
                "product_id": product_id,
                "score": rec["score"],
                "liked_avg_score": rec["liked_avg"],
                "disliked_avg_score": rec["disliked_avg"]
            }
            for rank, (product_id, rec) in enumerate(top_recommendations, 1)
        ]
    }
    
    logger.info(f"\n{'='*80}")
    logger.info(f"TOP {len(top_recommendations)} PRODUCT RECOMMENDATIONS")
    logger.info(f"{'='*80}")
    for rec in result["recommendations"]:
        logger.info(f"  {rec['rank']}. {rec['product_id']:<30} | Score: {rec['score']:>8.4f} | Liked: {rec['liked_avg_score']:>6.4f} | Disliked: {rec['disliked_avg_score']:>6.4f}")
    logger.info(f"{'='*80}\n")
    
    return result


def recommend_products(model, scene_image_path, product_images_dir, device, top_k=10):
    """
    Given a scene image, recommend the top-k matching products.
    
    Args:
        model: Trained CompleteTheLook model
        scene_image_path: Path to the scene image (jpg)
        product_images_dir: Directory containing product images
        device: 'cuda' or 'cpu'
        top_k: Number of recommendations to return
    
    Returns:
        List of (product_id, score) tuples sorted by score (highest first)
    """
    model.eval()
    
    try:
        # Load and preprocess scene image
        if not os.path.exists(scene_image_path):
            logger.error(f"Scene image not found: {scene_image_path}")
            return []
        
        logger.info(f"Loading scene image: {scene_image_path}")
        scene_img = Image.open(scene_image_path).convert("RGB")
        scene_img = transform(scene_img).unsqueeze(0).to(device)  # Add batch dimension
        
        # Get all product IDs
        if not os.path.exists(product_images_dir):
            logger.error(f"Products directory not found: {product_images_dir}")
            return []
        
        product_files = [f for f in os.listdir(product_images_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        product_ids = [f.rsplit('.', 1)[0] for f in product_files]
        
        if not product_ids:
            logger.error(f"No product images found in {product_images_dir}")
            return []
        
        logger.info(f"Evaluating scene against {len(product_ids)} products...")
        
        scores = []
        with torch.no_grad():
            for i, product_id in enumerate(product_ids):
                try:
                    # Find the actual file (handles different extensions)
                    product_file = next(f for f in product_files if f.rsplit('.', 1)[0] == product_id)
                    product_path = os.path.join(product_images_dir, product_file)
                    
                    product_img = Image.open(product_path).convert("RGB")
                    product_img = transform(product_img).unsqueeze(0).to(device)
                    
                    # Get compatibility score
                    score = model(scene_img, product_img)
                    scores.append((product_id, score.item()))
                    
                    if (i + 1) % 50 == 0:
                        logger.info(f"  Processed {i + 1}/{len(product_ids)} products...")
                
                except Exception as e:
                    logger.debug(f"Skipping product {product_id}: {e}")
                    continue
        
        if not scores:
            logger.error("No products could be evaluated")
            return []
        
        # Sort by score (descending)
        scores.sort(key=lambda x: x[1], reverse=True)
        
        recommendations = scores[:top_k]
        
        logger.info(f"\n{'='*60}")
        logger.info(f"TOP {min(top_k, len(recommendations))} PRODUCT RECOMMENDATIONS")
        logger.info(f"{'='*60}")
        for rank, (product_id, score) in enumerate(recommendations, 1):
            logger.info(f"  {rank}. {product_id:<30} | Score: {score:.4f}")
        logger.info(f"{'='*60}\n")
        
        return recommendations
    
    except Exception as e:
        logger.error(f"Error during recommendation: {e}", exc_info=True)
        return []


# ===============================
# Main
# ===============================

def main():
    if len(sys.argv) < 2:
        print("\n" + "="*80)
        print("Product Recommendation System")
        print("="*80)
        print("\nUsage:")
        print("  Option 1 - Single image:")
        print("    python recommend.py <scene_image> <products_dir> [model_path] [top_k]")
        print("\n  Option 2 - Liked/Disliked folders:")
        print("    python recommend.py --preferences <liked_folder> <disliked_folder> <products_dir> [model_path] [top_k]")
        print("\nArgs:")
        print("  scene_image   : Path to outfit image (jpg, jpeg, png)")
        print("  liked_folder  : Folder with liked outfit images")
        print("  disliked_folder : Folder with disliked outfit images")
        print("  products_dir  : Directory containing product images")
        print("  model_path    : Path to trained model (optional, default: model.pth)")
        print("  top_k         : Number of recommendations (optional, default: 10)")
        print("\nExamples:")
        print("  Single image:")
        print("    python recommend.py outfit.jpg ./products model.pth 10")
        print("\n  Preferences-based:")
        print("    python recommend.py --preferences ./liked ./disliked ./products model.pth 10")
        print("="*80 + "\n")
        sys.exit(1)
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")
    
    # Load model
    logger.info("Initializing model...")
    model = CompleteTheLook().to(device)
    
    # Determine mode and parse arguments
    if sys.argv[1] == "--preferences":
        # Preferences mode
        if len(sys.argv) < 5:
            logger.error("Missing arguments for preferences mode")
            sys.exit(1)
        
        liked_folder = sys.argv[2]
        disliked_folder = sys.argv[3]
        products_dir = sys.argv[4]
        model_path = sys.argv[5] if len(sys.argv) > 5 else "model.pth"
        top_k = int(sys.argv[6]) if len(sys.argv) > 6 else 10
        output_json = sys.argv[7] if len(sys.argv) > 7 else "recommendations.json"
        
        # Load model weights
        if os.path.exists(model_path):
            try:
                model.load_state_dict(torch.load(model_path, map_location=device))
                logger.info(f"Loaded trained model from {model_path}")
            except Exception as e:
                logger.warning(f"Could not load model weights: {e}")
        else:
            logger.warning(f"Model file not found: {model_path}")
        
        # Get recommendations based on preferences
        result = recommend_from_preferences(model, liked_folder, disliked_folder, products_dir, device, top_k)
        
        # Save to JSON
        if result:
            with open(output_json, 'w') as f:
                json.dump(result, f, indent=2)
            logger.info(f"Recommendations saved to {output_json}")
            print(f"\n✓ Recommendations saved to {output_json}")
        else:
            logger.error("Failed to generate recommendations")
            sys.exit(1)
    
    else:
        # Single image mode
        scene_image = sys.argv[1]
        products_dir = sys.argv[2]
        model_path = sys.argv[3] if len(sys.argv) > 3 else "model.pth"
        top_k = int(sys.argv[4]) if len(sys.argv) > 4 else 10
        
        # Load model weights
        if os.path.exists(model_path):
            try:
                model.load_state_dict(torch.load(model_path, map_location=device))
                logger.info(f"Loaded trained model from {model_path}")
            except Exception as e:
                logger.warning(f"Could not load model weights: {e}")
        else:
            logger.warning(f"Model file not found: {model_path}")
        
        # Get recommendations for single image
        recommendations = recommend_products(model, scene_image, products_dir, device, top_k)
        
        if recommendations:
            print("\n✓ Recommendations generated successfully!")
        else:
            print("\n✗ Failed to generate recommendations")
            sys.exit(1)


if __name__ == "__main__":
    main()
