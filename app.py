import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from flask import Flask, render_template, Response, jsonify, request
import cv2
import joblib
import numpy as np
import pandas as pd
import json
import mediapipe as mp
from sklearn.preprocessing import StandardScaler
from features import build_features
import onnxruntime as rt
import random
import base64
from io import BytesIO
from PIL import Image

app = Flask(__name__)

base_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(base_dir, 'models', 'rf_emotion.onnx')
scaler_path = os.path.join(base_dir, 'models', 'scaler.json')

# Load the model and scaler
try:
    sess = rt.InferenceSession(model_path)
    input_name = sess.get_inputs()[0].name
    label_name = sess.get_outputs()[0].name

    with open(scaler_path, 'r') as f:
        scaler_data = json.load(f)
    scaler = StandardScaler()
    scaler.mean_ = np.array(scaler_data['mean_'])
    scaler.scale_ = np.array(scaler_data['scale_'])
except FileNotFoundError:
    sess = None
    scaler = None

last_emotion = ""
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh()

# Emotion to song mapping (only working embed-safe YouTube IDs)
EMOTION_SONGS = {
    "happy": [
        "FJDfG7EzBeE",
        "kG1jb6zRn10"
    ],
    "sad": [
        "_l5El5n8qmg",
        "YMmzolJNjOM"
    ],
    "angry": [
        "kXYiU_JCYtU",  # Linkin Park - In The End
        "ScNNfyq3d_w",  # Disturbed - Down With The Sickness
        "hTWKbfoikeg"   # Nirvana - Smells Like Teen Spirit
    ],
    "surprise": [
        "rlMtaSs7wfs",
        "vjABLFK_wPY"
    ]
}

# Store the last played song for each emotion
last_played_song = {}

def predict_emotion(img):
    """Predict emotion from image"""
    global last_emotion
    if sess is None or scaler is None:
        last_emotion = "Model not found"
        return

    results = face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            h, w, c = img.shape
            features = build_features(face_landmarks.landmark, w, h)
            features = pd.DataFrame([features])
            features = scaler.transform(features)
            features = features.astype(np.float32)
            prediction = sess.run([label_name], {input_name: features})[0]
            last_emotion = str(prediction[0])

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/process_image", methods=['POST'])
def process_image():
    data = request.get_json()
    img_data = data['image'].split(',')[1]
    img = Image.open(BytesIO(base64.b64decode(img_data)))
    img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    predict_emotion(img)
    return jsonify({"emotion": last_emotion})

@app.route("/get_song/<emotion>")
def get_song(emotion):
    """Get a random song for the given emotion, avoiding immediate repetition"""
    emotion_lower = emotion.lower()
    
    # Default to happy if emotion not found
    if emotion_lower not in EMOTION_SONGS:
        emotion_lower = "happy"
    
    song_list = EMOTION_SONGS[emotion_lower]
    
    # Avoid repeating the last song if possible
    if len(song_list) > 1 and emotion_lower in last_played_song:
        last_song = last_played_song[emotion_lower]
        available_songs = [s for s in song_list if s != last_song]
        if available_songs:
            video_id = random.choice(available_songs)
        else:
            video_id = random.choice(song_list) # Fallback if all songs are the same
    else:
        video_id = random.choice(song_list)
    
    # Store the new song as the last played for this emotion
    last_played_song[emotion_lower] = video_id
    
    return jsonify({
        "video_id": video_id,
        "emotion": emotion
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)