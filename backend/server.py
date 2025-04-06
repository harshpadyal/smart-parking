from flask import Flask, request, jsonify, send_from_directory
import os
import base64
import sqlite3
from datetime import datetime
import cv2
import numpy as np
import re
from ultralytics import YOLO
from paddleocr import PaddleOCR
from flask_cors import CORS

# Set environment variable to avoid KMP duplicate library issue
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Flask App
app = Flask(__name__, static_folder='../frontend', static_url_path='/')
CORS(app)  # Enable CORS for cross-origin requests

# Load YOLO model
model = YOLO('best.pt')  # Ensure 'best.pt' is in the backend directory

# Initialize PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, use_gpu=False)

# Path to SQLite DB
DB_PATH = 'parking.db'

# ----------- DB Setup -----------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS parking_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plate_number TEXT,
                    timestamp TEXT
                )''')
    conn.commit()
    conn.close()

# ----------- PaddleOCR Function -----------
def paddle_ocr(frame, x1, y1, x2, y2):
    """Extract license plate text using PaddleOCR"""
    frame = frame[y1:y2, x1:x2]
    result = ocr.ocr(frame, det=False, rec=True, cls=False)
    text = ""

    if result and result[0]:  # Check if result is not None or empty
        for r in result:
            scores = r[0][1]
            scores = 0 if np.isnan(scores) else int(scores * 100)

            if scores > 60:  # Confidence threshold
                text = r[0][0]

    # Clean the text
    pattern = re.compile(r'[\W]')  # Remove unwanted characters
    text = pattern.sub("", text)
    text = text.replace("???", "").replace("O", "0").replace("粤", "")

    return str(text)

# ----------- Routes -------------

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'parking.html')

@app.route('/<path:path>')
def serve_static_file(path):
    return send_from_directory(app.static_folder, path)

@app.route('/process_license_plate', methods=['POST'])
def process_plate():
    try:
        data = request.get_json()
        image_data = data.get('image')

        if not image_data:
            return jsonify({'error': 'No image provided'}), 400

        # Decode base64 image
        image_data = image_data.split(',')[1]  # Remove base64 header
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Run YOLO detection
        results = model(image, conf=0.45)[0]  # Confidence threshold from main.py
        if len(results.boxes) == 0:
            return jsonify({'error': 'No license plate detected'}), 404

        # Process the first detected box
        box = results.boxes[0].xyxy[0].cpu().numpy().astype(int)
        x1, y1, x2, y2 = box
        plate_crop = image[y1:y2, x1:x2]

        # Extract text with PaddleOCR
        plate_text = paddle_ocr(image, x1, y1, x2, y2)

        if not plate_text:
            return jsonify({'error': 'Could not read plate number'}), 422

        # Store in DB
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO parking_logs (plate_number, timestamp) VALUES (?, ?)", (plate_text, timestamp))
        conn.commit()
        conn.close()

        return jsonify({'plate_number': plate_text, 'timestamp': timestamp})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ----------- Main -------------
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)