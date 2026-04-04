import os
import joblib
import flask
import pandas
import numpy
import sklearn

print("All imports successful")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'models')

try:
    scaler = joblib.load(os.path.join(MODELS_DIR, 'scaler.pkl'))
    print("Scaler loaded")
    label_encoder = joblib.load(os.path.join(MODELS_DIR, 'label_encoder.pkl'))
    print("Label encoder loaded")
except Exception as e:
    print(f"Error loading models: {e}")
