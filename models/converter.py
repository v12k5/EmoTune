import joblib
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

# Load the joblib bundle
bundle = joblib.load("rf_emotion.joblib")
model = bundle["model"]
scaler = bundle["scaler"]

# Define the input type
n_features = scaler.n_features_in_
initial_type = [("input", FloatTensorType([None, n_features]))]

# Convert to ONNX
onnx_model = convert_sklearn(model, initial_types=initial_type)

# Save the ONNX model
with open("rf_emotion_new.onnx", "wb") as f:
    f.write(onnx_model.SerializeToString())

print("Model converted and saved as rf_emotion_new.onnx")
