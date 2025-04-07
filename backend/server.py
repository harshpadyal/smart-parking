from flask import Flask, request, jsonify, send_from_directory
import os
import base64
import cv2
import numpy as np
import re
from ultralytics import YOLO
from paddleocr import PaddleOCR
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime

# Set environment variable to avoid KMP duplicate library issue
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Flask App
app = Flask(__name__, static_folder='../frontend', static_url_path='/')
CORS(app)

# MongoDB Atlas Connection
MONGO_URI = "mongodb+srv://root:root@cluster0.nff1ovs.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0" 
client = MongoClient(MONGO_URI)
db = client['smart_parking']
students_collection = db['students']
parking_logs_collection = db['parking_logs']

# Load YOLO model
model = YOLO('best.pt')

# Initialize PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, use_gpu=False)

# ----------- PaddleOCR Function -----------
def paddle_ocr(frame, x1, y1, x2, y2):
    frame = frame[y1:y2, x1:x2]
    result = ocr.ocr(frame, det=False, rec=True, cls=False)
    text = ""
    if result and result[0]:
        for r in result:
            scores = r[0][1]
            scores = 0 if np.isnan(scores) else int(scores * 100)
            if scores > 60:
                text = r[0][0]
    pattern = re.compile(r'[\W]')
    text = pattern.sub("", text)
    text = text.replace("???", "").replace("O", "0").replace("粤", "")
    return str(text)

# ----------- Routes -------------

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'parking.html')

@app.route('/student_portal')
def serve_student_portal():
    return send_from_directory(app.static_folder, 'student_portal.html')

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

        image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        results = model(image, conf=0.45)[0]
        if len(results.boxes) == 0:
            return jsonify({'error': 'No license plate detected'}), 404

        box = results.boxes[0].xyxy[0].cpu().numpy().astype(int)
        x1, y1, x2, y2 = box
        plate_text = paddle_ocr(image, x1, y1, x2, y2)

        if not plate_text:
            return jsonify({'error': 'Could not read plate number'}), 422

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        parking_logs_collection.insert_one({"plate_number": plate_text, "timestamp": timestamp})

        return jsonify({'plate_number': plate_text, 'timestamp': timestamp})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/register_student', methods=['POST'])
def register_student():
    try:
        data = request.get_json()
        name = data.get('name')
        batch = data.get('batch')
        branch = data.get('branch')
        email = data.get('email')
        license_plate = data.get('license_plate')

        if not all([name, batch, branch, email, license_plate]):
            return jsonify({'error': 'All fields are required'}), 400

        if not email.endswith('@ves.ac.in'):
            return jsonify({'error': 'Please use a valid VESIT email'}), 400

        if students_collection.find_one({"email": email}):
            return jsonify({'error': 'Email already registered'}), 409
        if students_collection.find_one({"license_plate": license_plate}):
            return jsonify({'error': 'License plate already registered'}), 409

        student_data = {
            "name": name,
            "batch": batch,
            "branch": branch,
            "email": email,
            "license_plate": license_plate,
            "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        students_collection.insert_one(student_data)

        return jsonify({'message': 'Student registered successfully', 'data': student_data}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/student_activity', methods=['POST'])
def student_activity():
    try:
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({'error': 'Email is required'}), 400

        student = students_collection.find_one({"email": email})
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        license_plate = student['license_plate']
        activities = list(parking_logs_collection.find({"plate_number": license_plate}).sort("timestamp", -1))

        return jsonify({'activities': [{'plate_number': act['plate_number'], 'timestamp': act['timestamp']} for act in activities]}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ----------- Main -------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)