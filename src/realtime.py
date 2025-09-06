import cv2
import mediapipe as mp
import joblib
from features import build_features

MODEL_PATH = "models/rf_emotion.joblib"

# Load trained model + scaler
bundle = joblib.load(MODEL_PATH)
model = bundle["model"]
scaler = bundle["scaler"]

mp_face_mesh = mp.solutions.face_mesh


def main():
    cap = cv2.VideoCapture(0)  # 0 = default webcam
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return

    with mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as face_mesh:

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            h, w, _ = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb)

            if results.multi_face_landmarks:
                # Extract features
                landmarks = results.multi_face_landmarks[0].landmark
                feats = build_features(landmarks, w, h)

                # Normalize using scaler
                feats_scaled = scaler.transform([feats])

                # Predict
                pred = model.predict(feats_scaled)[0]

                # Draw label
                cv2.putText(frame, f"Emotion: {pred}", (30, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

            cv2.imshow("Real-time Emotion Recognition", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()