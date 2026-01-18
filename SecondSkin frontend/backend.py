from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'image_sorter'))  # Add path to image_sorter.py
from image_sorter import sort_image, gather_images
from pathlib import Path

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Paths (adjust if needed)
IMAGE_FOLDER = os.path.join(os.path.dirname(__file__), 'src', 'testing images')
KEEP_DIR = os.path.join(os.path.dirname(__file__), '..', 'keep')
DISCARD_DIR = os.path.join(os.path.dirname(__file__), '..', 'discard')
LOG_PATH = os.path.join(IMAGE_FOLDER, '.image_sort_log.csv')

@app.route('/images', methods=['GET'])
def get_images():
    """Return list of image filenames."""
    imgs = gather_images(Path(IMAGE_FOLDER))
    return jsonify([img.name for img in imgs])

@app.route('/image/<filename>', methods=['GET'])
def get_image(filename):
    """Serve an image file."""
    return send_from_directory(IMAGE_FOLDER, filename)

@app.route('/decide/<filename>/<decision>', methods=['POST'])
def decide(filename, decision):
    """Handle swipe decision: 'yes' for keep, 'no' for discard."""
    image_path = os.path.join(IMAGE_FOLDER, filename)
    if decision not in ['yes', 'no']:
        return jsonify({'error': 'Invalid decision'}), 400
    try:
        sort_image(image_path, decision, KEEP_DIR, DISCARD_DIR, LOG_PATH)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)