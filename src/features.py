import numpy as np

# Define useful landmark groups (from Mediapipe indices)
LEFT_EYE = [33, 133]
RIGHT_EYE = [362, 263]
MOUTH = [13, 14, 61, 291]  # upper lip, lower lip, corners
BROWS = [65, 295]          # left brow top, right brow top

def euclidean(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

def build_features(landmarks, w, h):
    # Convert normalized coords → pixel coords
    pts = [(lm.x * w, lm.y * h) for lm in landmarks]

    feats = []

    # Eye distance (scale reference)
    eye_dist = euclidean(pts[LEFT_EYE[0]], pts[RIGHT_EYE[1]])

    # 1. Mouth features
    mouth_height = euclidean(pts[MOUTH[0]], pts[MOUTH[1]]) / eye_dist
    mouth_width = euclidean(pts[MOUTH[2]], pts[MOUTH[3]]) / eye_dist
    feats.extend([mouth_height, mouth_width])

    # 2. Brow features
    brow_height_left = euclidean(pts[BROWS[0]], pts[LEFT_EYE[0]]) / eye_dist
    brow_height_right = euclidean(pts[BROWS[1]], pts[RIGHT_EYE[1]]) / eye_dist
    feats.extend([brow_height_left, brow_height_right])

    # 3. Symmetry (left vs right eye + mouth corners)
    eye_symmetry = euclidean(pts[LEFT_EYE[1]], pts[RIGHT_EYE[0]]) / eye_dist
    mouth_symmetry = abs(pts[MOUTH[2]][1] - pts[MOUTH[3]][1]) / eye_dist
    feats.extend([eye_symmetry, mouth_symmetry])

    # 4. Extra ratios: mouth aspect ratio
    mar = mouth_height / (mouth_width + 1e-6)
    feats.append(mar)

    return np.array(feats)
