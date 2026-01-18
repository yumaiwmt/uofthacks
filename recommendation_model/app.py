import os
import io
import json
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from PIL import Image
import torch
from torchvision import transforms

from amplitude import Amplitude

# Import your trained model
from complete_the_look import CompleteTheLook

# -------------------------------
# 1. Setup
# -------------------------------
AMPLITUDE_API_KEY = "7d38249e88f22878659b3850d77eadf8"
amp = Amplitude(AMPLITUDE_API_KEY)

device = "cuda" if torch.cuda.is_available() else "cpu"

# Initialize model
model = CompleteTheLook().to(device)
model.eval()  # inference mode

# Image transform
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# -------------------------------
# 2. Product embeddings database
# -------------------------------
# Replace with your real embeddings
product_db = {
    "SKU982": torch.randn(512),
    "SKU771": torch.randn(512),
    "SKU120": torch.randn(512)
}

# -------------------------------
# 3. Top-K recommendation function
# -------------------------------
def search_top_k(scene_img_tensor, product_db, k=3):
    scene_img_tensor = scene_img_tensor.unsqueeze(0).to(device)
    scores = {}
    for pid, prod_emb in product_db.items():
        prod_emb = prod_emb.to(device).unsqueeze(0)
        score = model(scene_img_tensor, prod_emb)
        scores[pid] = score.item()
    top_k = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
    return [{"product_id": pid, "score": s} for pid, s in top_k]

# -------------------------------
# 4. Send events to Amplitude
# -------------------------------
def send_to_amplitude(user_id, upload_image_id, recommendations):
    for rank, rec in enumerate(recommendations, 1):
        event = BaseEvent(
            user_id=user_id,
            event_type="Recommended Product Shown",
            event_properties={
                "upload_image_id": upload_image_id,
                "product_id": rec["product_id"],
                "score": rec["score"],
                "rank": rank
            }
        )
        amp.track(event)
    print(f"Sent {len(recommendations)} events to Amplitude for {upload_image_id}")

# -------------------------------
# 5. FastAPI app
# -------------------------------
app = FastAPI(title="Fashion Recommender API")

@app.post("/recommend/")
async def recommend(user_id: str, file: UploadFile = File(...), top_k: int = 3):
    # Read image bytes and convert to PIL
    image_bytes = await file.read()
    scene_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    scene_tensor = transform(scene_img)

    # Get top-K recommendations
    recommendations = search_top_k(scene_tensor, product_db, k=top_k)

    # Send to Amplitude
    send_to_amplitude(user_id, file.filename, recommendations)

    # Return recommendations as JSON
    return JSONResponse({"upload_image_id": file.filename, "recommendations": recommendations})