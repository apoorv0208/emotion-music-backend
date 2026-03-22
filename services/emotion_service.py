import base64
import numpy as np
import cv2
from tensorflow.keras.models import load_model

# --- Load model once when server starts ---
model = load_model("emotion_model.h5")

emotion_labels = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']

# --- Load Haar Cascade (comes with OpenCV) ---
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def decode_base64_image(base64_string):
    header, encoded = base64_string.split(",", 1)
    image_bytes = base64.b64decode(encoded)
    np_array = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    return image


def preprocess_face(face_roi):
    if face_roi is None or face_roi.size == 0:
        return None

    gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (48, 48))
    normalized = resized.astype("float32") / 255.0
    reshaped = np.reshape(normalized, (1, 48, 48, 1))

    return reshaped


def detect_emotion_from_base64(base64_string):

    frame = decode_base64_image(base64_string)

    if frame is None:
        return "Invalid Image"

    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_frame = cv2.equalizeHist(gray_frame)

    faces = face_cascade.detectMultiScale(
        gray_frame,
        scaleFactor=1.1,
        minNeighbors=4,
        minSize=(30, 30)
    )

    if len(faces) == 0:
        print("⚠ No face detected — using full image")
        face_roi = frame
    else:
        faces = sorted(faces, key=lambda x: x[2] * x[3], reverse=True)
        x, y, w, h = faces[0]
        face_roi = frame[y:y+h, x:x+w]

    input_data = preprocess_face(face_roi)

    if input_data is None:
        return "Error"

    preds = model.predict(input_data, verbose=0)
    detected_emotion = emotion_labels[np.argmax(preds)]

    print(f"🧠 Detected Emotion: {detected_emotion}")

    return detected_emotion