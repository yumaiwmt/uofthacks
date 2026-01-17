# UofTHacks

A collection of machine learning and web scraping projects for outfit styling and product recommendation systems.

## Projects

### 1. Scraping Pipeline
An image scraping pipeline for collecting styled outfit images using both Redis and local memory storage.

**Features:**
- Downloads images from URLs
- Stores images in both Redis (for fast access) and local filesystem
- Uses PIL for image processing
- Supports batch image scraping

**Tech Stack:** Python, Redis, Pillow, Requests

**Setup:**
```bash
cd scraping_pipeline
pip install -r requirements.txt
```

**Usage:**
```python
from image_scraper import ImageScraper

scraper = ImageScraper()
urls = ['https://example.com/image1.jpg', 'https://example.com/image2.jpg']
scraper.scrape_images(urls)
```

---

### 2. Complete the Look (CTL) - Shop the Look Recommendation
A deep learning model that recommends complementary products for outfit scenes.

**Features:**
- Downloads the Shop the Look dataset from Kaggle
- Uses ResNet-50 CNN encoder for image embeddings
- Combines global and local compatibility scoring
- Trains using triplet ranking loss

**Tech Stack:** PyTorch, torchvision, Kaggle Hub, PIL

**Setup:**
```bash
pip install torch torchvision kagglehub pillow
```

**Usage:**
```bash
python "scrapping (shop the look).py"
```

The model learns to match products with outfit scenes by training on positive (matching) and negative (non-matching) product pairs.

---

## Installation

1. Clone the repository
2. Install dependencies for each project (see sections above)
3. Set up Redis (if using the scraping pipeline)

## Requirements

- Python 3.8+
- PyTorch (for CTL model)
- Redis (for scraping pipeline)
- CUDA (optional, for GPU acceleration)

## Future Enhancements

- Web interface for product recommendations
- Real-time image scraping from fashion websites
- Model fine-tuning with custom datasets
- API endpoint for recommendation service