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
app = Flask(__name__, static_folder="../frontend", static_url_path="/")
CORS(app)

# MongoDB Atlas Connection
MONGO_URI = "mongodb+srv://root:root@cluster0.nokldp5.mongodb.net/?retryWrites=true&w=majority&tls=true"
client = MongoClient(MONGO_URI)
db = client["smart_parking"]
students_collection = db["students"]
parking_logs_collection = db["parking_logs"]

# Load YOLO model
model = YOLO("best.pt")

# Initialize PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, use_gpu=False)

# Parking slots (global state)
parklist = [0] * 10  # 0 = empty, 1 = occupied

# Initialize parklist from MongoDB logs on startup
def initialize_parklist():
    global parklist
    print("Initializing parklist from MongoDB logs...")
    for slot in range(10):
        # Find the most recent log for this slot
        latest_log = parking_logs_collection.find_one(
            {"slot": slot},
            sort=[("timestamp", -1)]
        )
        if latest_log and latest_log["action"] == "entry":
            # Check if there's an exit log after this entry
            latest_exit = parking_logs_collection.find_one(
                {"slot": slot, "action": "exit", "timestamp": {"$gt": latest_log["timestamp"]}},
                sort=[("timestamp", -1)]
            )
            if not latest_exit:
                parklist[slot] = 1
                print(f"Slot {slot} marked as occupied based on MongoDB log")
    print(f"Initialized parklist: {parklist}")

# Call initialization on startup
initialize_parklist()

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
    pattern = re.compile(r"[\W]")
    text = pattern.sub("", text)
    text = text.replace("???", "").replace("O", "0").replace("粤", "")
    return str(text)

# ----------- Routes -------------

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "parking.html")

@app.route("/student_portal")
def serve_student_portal():
    return send_from_directory(app.static_folder, "student_portal.html")

@app.route("/<path:path>")
def serve_static_file(path):
    return send_from_directory(app.static_folder, path)

@app.route("/get_parking_state", methods=["GET"])
def get_parking_state():
    try:
        parked_slots = []
        for slot in range(10):
            if parklist[slot] == 1:
                recent_entry = parking_logs_collection.find_one(
                    {"slot": slot, "action": "entry"},
                    sort=[("timestamp", -1)]
                )
                if recent_entry:
                    parked_slots.append({
                        "slot": slot,
                        "plate_number": recent_entry["plate_number"]
                    })
        return jsonify({
            "parklist": parklist,
            "parked_slots": parked_slots
        })
    except Exception as e:
        print(f"Error in get_parking_state: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/process_license_plate", methods=["POST"])
def process_plate():
    global parklist
    try:
        data = request.get_json()
        print("Received data:", data)
        image_data = data.get("image")
        slot = data.get("slot")

        # Validate inputs
        if not image_data:
            return jsonify({"error": "No image provided"}), 400
        if slot is None or not isinstance(slot, int) or slot < 0 or slot >= len(parklist):
            return jsonify({"error": "Invalid slot number"}), 400
        if parklist[slot] == 1:
            return jsonify({"error": "Slot already occupied"}), 400

        # Decode base64 image
        print("Raw image_data (first 50 chars):", image_data[:50])
        if "," in image_data:
            image_data = image_data.split(",")[1]
        print("Base64 part (first 50 chars):", image_data[:50])

        try:
            image_bytes = base64.b64decode(image_data)
        except base64.binascii.Error as e:
            return jsonify({"error": f"Invalid base64 data: {str(e)}"}), 400

        print("Decoded bytes length:", len(image_bytes))
        if len(image_bytes) == 0:
            return jsonify({"error": "Empty image data after decoding"}), 400

        nparr = np.frombuffer(image_bytes, np.uint8)
        print("NumPy array length:", len(nparr))
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return jsonify({"error": "Failed to decode image into a valid format"}), 400
        print("Image decoded, shape:", image.shape)

        # YOLO detection
        print("Running YOLO...")
        results = model(image, conf=0.45)[0]
        if len(results.boxes) == 0:
            return jsonify({"error": "No license plate detected"}), 404

        box = results.boxes[0].xyxy[0].cpu().numpy().astype(int)
        x1, y1, x2, y2 = box
        print(f"Detected box: {x1},{y1},{x2},{y2}")
        plate_text = paddle_ocr(image, x1, y1, x2, y2)
        print(f"Extracted plate text: {plate_text}")

        if not plate_text:
            return jsonify({"error": "Could not read plate number"}), 422

        # Check if license plate is registered
        print("Checking students collection...")
        student = students_collection.find_one({"license_plate": plate_text})
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not student:
            return jsonify({"error": "Not registered license plate", "plate_number": plate_text}), 403

        # Park the vehicle
        parklist[slot] = 1
        print(f"Parking vehicle at slot {slot}, Updated parklist: {parklist}")
        parking_logs_collection.insert_one({
            "plate_number": plate_text,
            "slot": slot,
            "timestamp": timestamp,
            "action": "entry"
        })

        return jsonify({
            "plate_number": plate_text,
            "timestamp": timestamp,
            "slot": slot
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/exit_vehicle", methods=["POST"])
def exit_vehicle():
    global parklist
    try:
        data = request.get_json()
        slot = data.get("slot")
        print(f"Exit request received for slot: {slot}")

        # Validate inputs
        if slot is None or not isinstance(slot, int) or slot < 0 or slot >= len(parklist):
            print(f"Invalid slot number: {slot}")
            return jsonify({"error": "Invalid slot number"}), 400
        if parklist[slot] == 0:
            print(f"Slot {slot} is already empty")
            return jsonify({"error": "Slot is already empty"}), 400

        # Find the most recent entry log for this slot
        recent_entry = parking_logs_collection.find_one(
            {"slot": slot, "action": "entry"},
            sort=[("timestamp", -1)]
        )
        if not recent_entry:
            print(f"No entry log found for slot {slot}")
            return jsonify({"error": "No entry log found for this slot"}), 404

        plate_number = recent_entry["plate_number"]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Log the exit
        parklist[slot] = 0
        print(f"Logging exit for plate {plate_number} at slot {slot}")
        parking_logs_collection.insert_one({
            "plate_number": plate_number,
            "slot": slot,
            "timestamp": timestamp,
            "action": "exit"
        })
        print(f"Exit logged successfully, Updated parklist: {parklist}")

        return jsonify({
            "plate_number": plate_number,
            "timestamp": timestamp,
            "slot": slot,
            "message": "Exit logged successfully"
        })

    except Exception as e:
        print(f"Error in exit_vehicle: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/register_student", methods=["POST"])
def register_student():
    try:
        data = request.get_json()
        name = data.get("name")
        batch = data.get("batch")
        branch = data.get("branch")
        email = data.get("email")
        license_plate = data.get("license_plate")

        if not all([name, batch, branch, email, license_plate]):
            return jsonify({"error": "All fields are required"}), 400

        if not email.endswith("@ves.ac.in"):
            return jsonify({"error": "Please use a valid VESIT email"}), 400

        if students_collection.find_one({"email": email}):
            return jsonify({"error": "Email already registered"}), 409
        if students_collection.find_one({"license_plate": license_plate}):
            return jsonify({"error": "License plate already registered"}), 409

        student_data = {
            "name": name,
            "batch": batch,
            "branch": branch,
            "email": email,
            "license_plate": license_plate,
            "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        students_collection.insert_one(student_data)

        return jsonify({"message": "Student registered successfully", "data": student_data}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/student_activity", methods=["POST"])
def student_activity():
    try:
        data = request.get_json()
        email = data.get("email")

        if not email:
            return jsonify({"error": "Email is required"}), 400

        student = students_collection.find_one({"email": email})
        if not student:
            return jsonify({"error": "Student not found"}), 404

        license_plate = student["license_plate"]
        activities = list(parking_logs_collection.find({"plate_number": license_plate}).sort("timestamp", -1))

        return jsonify({"activities": [{"plate_number": act["plate_number"], "slot": act["slot"], "timestamp": act["timestamp"], "action": act["action"]} for act in activities]}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------- Main -------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)