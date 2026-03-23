from flask import Blueprint, request, jsonify
import cv2
import numpy as np
import base64
from tensorflow.keras.models import load_model
import os

detect_bp = Blueprint('detect', __name__)

# --- 1. Load the AI Model ---
try:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = os.path.join(BASE_DIR, "emotion_model.h5")
    model = load_model(model_path)
    print("✅ AI Model Loaded Successfully!")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    model = None

emotion_labels = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']

# --- 2. Initialize OpenCV Face Detector ---
# This is built right into OpenCV, no extra downloads needed!
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

@detect_bp.route('/analyze', strict_slashes=False, methods=['POST', 'OPTIONS'])
def detect_emotion():
    if model is None:
        return jsonify({"error": "AI Model not loaded on server."}), 500

    try:
        data = request.get_json()
        image_data = data.get('image')

        if not image_data:
            return jsonify({"error": "No image provided"}), 400

        # 3. Decode the Base64 image from React into an OpenCV Image
        encoded_data = image_data.split(',')[1] 
        nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({"error": "Could not decode image"}), 400

        # 4. Find the face using OpenCV
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # detectMultiScale finds faces and returns their coordinates
        faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        if len(faces) == 0:
            return jsonify({"error": "No face detected. Please ensure your face is clearly visible."}), 400

        # Get the coordinates of the first face detected: [x, y, width, height]
        x, y, bw, bh = faces[0]
        
        # Crop the face out of the frame
        face_roi = frame[y:y+bh, x:x+bw]

        if face_roi.size == 0:
            return jsonify({"error": "Invalid face crop"}), 400

        # 5. Preprocess for your specific emotion model (48x48 Grayscale)
        gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        resized_face = cv2.resize(gray_face, (48, 48))
        normalized_face = resized_face.astype('float32') / 255.0
        reshaped_face = np.reshape(normalized_face, (1, 48, 48, 1))

        # 6. Predict the Emotion!
        predictions = model.predict(reshaped_face)
        detected_emotion = emotion_labels[np.argmax(predictions)]

        return jsonify({"emotion": detected_emotion}), 200

    except Exception as e:
        print(f"Error in detection route: {e}")
        return jsonify({"error": "An internal server error occurred during detection."}), 500