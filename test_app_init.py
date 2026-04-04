
import os
import joblib
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'models')

print(f"BASE_DIR: {BASE_DIR}")
print(f"MODELS_DIR: {MODELS_DIR}")

try:
    print("Loading scaler...")
    scaler = joblib.load(os.path.join(MODELS_DIR, 'scaler.pkl'))
    print("Loading label_encoder...")
    label_encoder = joblib.load(os.path.join(MODELS_DIR, 'label_encoder.pkl'))
    print("Loading results_summary...")
    with open(os.path.join(MODELS_DIR, 'results_summary.json')) as f:
        results_summary = json.load(f)
    print("Success loading core files.")
except Exception as e:
    print(f"Error: {e}")
