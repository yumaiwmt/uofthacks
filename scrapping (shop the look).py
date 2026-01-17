# ===============================
# Complete the Look (CTL) – Full Implementation
# ===============================

import os
import json
import random
from PIL import Image

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

import torchvision.transforms as T
from torchvision import models

import kagglehub


# ===============================
# 1. Download Dataset
# ===============================

DATASET_PATH = kagglehub.dataset_download(
    "pypiahmad/shop-the-look-dataset"
)

print("Dataset path:", DATASET_PATH)


# ===============================
# 2. Dataset Loader
# ===============================

class ShopTheLookDataset(Dataset):
    def __init__(self, root, transform=None):
        self.root = root
        self.transform = transform

        ann_path = os.path.join(root, "annotations.json")
        with open(ann_path, "r") as f:
            self.data = json.load(f)

        self.scene_ids = list(self.data.keys())

        self.all_products = set()
        for v in self.data.values():
            for p in v["products"]:
                self.all_products.add(p)
        self.all_products = list(self.all_products)

    def __len__(self):
        return len(self.scene_ids)

    def __getitem__(self, idx):
        scene_id = self.scene_ids[idx]
        entry = self.data[scene_id]

        scene_img = Image.open(
            os.path.join(self.root, "images/scenes", entry["scene"])
        ).convert("RGB")

        pos_id = random.choice(entry["products"])
        neg_id = random.choice(
            list(set(self.all_products) - set(entry["products"]))
        )

        pos_img = Image.open(
            os.path.join(self.root, "images/products", pos_id)
        ).convert("RGB")

        neg_img = Image.open(
            os.path.join(self.root, "images/products", neg_id)
        ).convert("RGB")

        if self.transform:
            scene_img = self.transform(scene_img)
            pos_img = self.transform(pos_img)
            neg_img = self.transform(neg_img)

        return scene_img, pos_img, neg_img


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
# 5. Ranking Loss
# ===============================

class RankingLoss(nn.Module):
    def __init__(self, margin=0.2):
        super().__init__()
        self.margin = margin

    def forward(self, pos, neg):
        return torch.mean(torch.clamp(self.margin - pos + neg, min=0))


# ===============================
# 6. Training Loop
# ===============================

def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("Using device:", device)

    dataset = ShopTheLookDataset(DATASET_PATH, transform)
    loader = DataLoader(dataset, batch_size=8, shuffle=True, num_workers=2)

    model = CompleteTheLook().to(device)
    criterion = RankingLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)

    for epoch in range(5):
        model.train()
        total_loss = 0

        for scene, pos, neg in loader:
            scene, pos, neg = scene.to(device), pos.to(device), neg.to(device)

            pos_score = model(scene, pos)
            neg_score = model(scene, neg)

            loss = criterion(pos_score, neg_score)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        print(f"Epoch {epoch+1} | Loss: {total_loss / len(loader):.4f}")

    print("Training complete.")


if __name__ == "__main__":
    main()