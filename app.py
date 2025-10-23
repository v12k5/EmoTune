import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from flask import Flask, render_template, jsonify, request
import cv2
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
from googleapiclient.discovery import build

YOUTUBE_API_KEY = "AIzaSyBcnfrMBbkBHRKyaq27QYws7AojYruevJ4"  # USE YOUR ACTUAL API KEY

app = Flask(__name__)

base_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(base_dir, 'models', 'rf_emotion.onnx')
scaler_path = os.path.join(base_dir, 'models', 'scaler.json')

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

EMOTION_SONGS = {
    "happy": ["FJDfG7EzBeE", "kG1jb6zRn10"],
    "sad": ["_l5El5n8qmg", "YMmzolJNjOM"],
    "angry": ["kXYiU_JCYtU", "ScNNfyq3d_w", "hTWKbfoikeg"],
    "surprise": ["rlMtaSs7wfs", "vjABLFK_wPY"]
}

last_played_song = {}

def youtube_search_by_emotion(emotion, language="telugu", max_results=1):
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        query = f"best {emotion} songs {language}"
        search_response = youtube.search().list(
            q=query,
            part='id,snippet',
            maxResults=max_results,
            type='video',
            videoEmbeddable='true'
        ).execute()
        video_ids = [
            item['id']['videoId']
            for item in search_response.get('items', [])
            if 'videoId' in item['id']
        ]
        return video_ids
    except Exception as e:
        print("YouTube Search error:", e)
        return []

def predict_emotion(img):
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
    emotion_lower = emotion.lower()
    user_language = request.args.get("lang", "telugu")
    video_ids = youtube_search_by_emotion(emotion_lower, language=user_language, max_results=1)
    if not video_ids:
        video_ids = EMOTION_SONGS.get(emotion_lower, EMOTION_SONGS["happy"])
    video_id = video_ids[0] if video_ids else None
    last_played_song[emotion_lower] = video_id
    return jsonify({
        "video_id": video_id,
        "emotion": emotion
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
