import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from flask import Flask, render_template, Response, jsonify
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

app = Flask(__name__)

# Load the model and scaler
try:
    sess = rt.InferenceSession("models/rf_emotion.onnx")
    input_name = sess.get_inputs()[0].name
    label_name = sess.get_outputs()[0].name

    try:
        scaler = joblib.load("models/scaler.joblib")
    except FileNotFoundError:
        with open("models/scaler.json", 'r') as f:
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

# Emotion to song mapping (you can expand this with more videos)
EMOTION_SONGS = {
    "happy": [
        "dQw4w9WgXcQ",  # Rick Astley - Never Gonna Give You Up
        "ZbZSe6N_BXs",  # Happy by Pharrell Williams
        "Y66j_BUCBMY"   # Happy songs
    ],
    "sad": [
        "4fndeDfaWCg",  # Somebody That I Used to Know
        "hLQl3WQQoQ0",  # Someone Like You - Adele
        "SlPhMPnQ58k"   # Sad songs
    ],
    "angry": [
        "WNIPqafd4As",  # Breaking Benjamin
        "04F4xlWSFh0",  # Rage Against The Machine
        "CSvFpBOe8eY"   # Angry music
    ],
    "surprised": [
        "kJQP7kiw5Fk",  # Despacito
        "fJ9rUzIMcZQ",  # Upbeat music
        "pRpeEdMmmQ0"   # Surprise songs
    ],
    "neutral": [
        "kXYiU_JCYtU",  # Relaxing music
        "jfKfPfyJRdk",  # Lofi hip hop
        "5qap5aO4i9A"   # Chill music
    ],
    "fear": [
        "sOnqjkJTMaA",  # Thriller - Michael Jackson
        "Zi_XLOBDo_Y",  # Scary music
        "hzPpWInAiOg"   # Horror themes
    ]
}

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

def gen_frames():
    cap = cv2.VideoCapture(0)
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            predict_emotion(frame)
            ret, buffer = cv2.imencode(".jpg", frame)
            frame = buffer.tobytes()
            yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/emotion")
def emotion():
    return jsonify({"emotion": last_emotion})

@app.route("/get_song/<emotion>")
def get_song(emotion):
    """Get a random song for the given emotion"""
    emotion_lower = emotion.lower()
    
    # Default to neutral if emotion not found
    if emotion_lower not in EMOTION_SONGS:
        emotion_lower = "neutral"
    
    # Pick a random song from the emotion category
    video_id = random.choice(EMOTION_SONGS[emotion_lower])
    
    return jsonify({
        "video_id": video_id,
        "emotion": emotion
    })

if __name__ == "__main__":
    app.run(debug=True)