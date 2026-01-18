import torch
import torch.nn as nn
from torchvision import transforms as T
from PIL import Image
from pathlib import Path

# 1. Setup Device and Transforms
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
TRANSFORM = T.Compose([
    T.Resize((224, 224)),
    T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# 2. Re-initialize the Model Architecture
class CompleteTheLook(nn.Module):
    def __init__(self):
        super().__init__()
        # Use the same weights version as training
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
    # Load Model
    model = CompleteTheLook().to(DEVICE)
    model.load_state_dict(torch.load(model_path, map_location=DEVICE))
    model.eval()

    # Process Scene
    scene_img = TRANSFORM(Image.open(scene_image_path).convert("RGB")).unsqueeze(0).to(DEVICE)
    
    # Process and Rank Products
    results = []
    product_paths = list(Path(products_folder).glob("*.jpg"))
    
    print(f"Comparing scene to {len(product_paths)} products...")
    for p_path in product_paths:
        prod_img = TRANSFORM(Image.open(p_path).convert("RGB")).unsqueeze(0).to(DEVICE)
        score = model(scene_img, prod_img).item()
        results.append((p_path.name, score))

    # Sort by Score (Descending)
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]

# Run the test
if __name__ == "__main__":
    # Update these paths to your local files
    TOP_RECS = test_recommendation(
        model_path="fashion_recommender_v1.pth",  
        scene_image_path=r"testing images\alesia-kazantceva-dhD_FiNkuzw-unsplash.jpg", 
        products_folder="fashion_data/cached_images/products" 
    
    )
    print("\n--- Top Recommendations ---")
    for i, (name, score) in enumerate(TOP_RECS, 1):
        print(f"{i}. {name} (Score: {score:.4f})")