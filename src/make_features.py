# src/make_features.py
import os
import cv2
import mediapipe as mp
import pandas as pd
from tqdm import tqdm
from features import build_features

DATA_DIR = "dataset"
OUTPUT_CSV = "features123.csv"

mp_face_mesh = mp.solutions.face_mesh

def process_image(image_path, label):
    """Extract engineered features from image"""
    img = cv2.imread(image_path)
    if img is None:
        return None
    
    h, w, _ = img.shape
    with mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        min_detection_confidence=0.5
    ) as face_mesh:
        results = face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        if not results.multi_face_landmarks:
            return None
        landmarks = results.multi_face_landmarks[0].landmark
        return build_features(landmarks, w, h)

def main():
    rows = []
    labels = []
    for label in os.listdir(DATA_DIR):
        folder = os.path.join(DATA_DIR, label)
        if not os.path.isdir(folder):
            continue
        print(f"Processing {label}...")
        for file in tqdm(os.listdir(folder)):
            if not file.lower().endswith(('.jpg','.jpeg','.png')):
                continue
            path = os.path.join(folder, file)
            feats = process_image(path, label)
            if feats is not None:
                rows.append(feats)
                labels.append(label)

    # save features
    df = pd.DataFrame(rows)
    df["label"] = labels
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved {len(df)} samples to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
