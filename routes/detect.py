import os
# 🚨 STRICT TENSORFLOW MEMORY LIMITS (Must be at the very top)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' # Block TF warnings from eating memory
os.environ['CUDA_VISIBLE_DEVICES'] = '-1' # Force CPU only

import tensorflow as tf
# Force TensorFlow to only use 1 thread so it doesn't freeze the server
tf.config.threading.set_inter_op_parallelism_threads(1)
tf.config.threading.set_intra_op_parallelism_threads(1)

from flask import Blueprint, request, jsonify
import cv2
import numpy as np
import base64
from tensorflow.keras.models import load_model
import gc # Garbage collector to free RAM

detect_bp = Blueprint('detect', __name__)

# --- Load the AI Model ---
try:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = os.path.join(BASE_DIR, "emotion_model.h5")
    # compile=False is crucial. It saves ~100MB of RAM because we only need to predict, not train.
    model = load_model(model_path, compile=False) 
    print("✅ AI Model Loaded Successfully!")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    model = None

emotion_labels = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

@detect_bp.route('/analyze', methods=['POST', 'OPTIONS'])
def detect_emotion():
    # 1. Handle CORS Preflight Instantly
    if request.method == 'OPTIONS':
        res = jsonify({"status": "CORS OK"})
        res.headers.add('Access-Control-Allow-Origin', '*')
        res.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        res.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return res, 200

    if model is None:
        return jsonify({"error": "AI Model not loaded."}), 500

    try:
        data = request.get_json()
        image_data = data.get('image')

        if not image_data:
            return jsonify({"error": "No image provided"}), 400

        # 2. Decode Image
        encoded_data = image_data.split(',')[1] 
        nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # 3. Find Face
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        if len(faces) == 0:
            return jsonify({"error": "No face detected. Please ensure your face is clearly visible."}), 400

        x, y, bw, bh = faces[0]
        face_roi = frame[y:y+bh, x:x+bw]

        # 4. Preprocess
        gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        resized_face = cv2.resize(gray_face, (48, 48))
        normalized_face = resized_face.astype('float32') / 255.0
        reshaped_face = np.reshape(normalized_face, (1, 48, 48, 1))

        # 5. Predict (verbose=0 saves memory)
        # 5. Predict (LIGHTWEIGHT SINGLE-IMAGE INFERENCE)
        predictions = model(reshaped_face, training=False)
        detected_emotion = emotion_labels[np.argmax(predictions[0])]

        # 6. FORCE MEMORY CLEANUP (Prevents the server from dying on the next picture)
        del nparr, frame, gray_frame, faces, face_roi, gray_face, resized_face, normalized_face, reshaped_face, predictions
        gc.collect()

        return jsonify({"emotion": detected_emotion}), 200

    except Exception as e:
        print(f"Error in detection route: {e}")
        return jsonify({"error": "An internal server error occurred during detection."}), 500