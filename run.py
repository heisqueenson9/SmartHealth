# =============================================================
# SmartHealth AI - Startup Script
# Author:      Enock Queenson Eduafo
# Student ID:  11014444
# Institution: University of Ghana
# Year:        2026
# Usage:       python run.py
# =============================================================

import os
import sys
import subprocess

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'models')

REQUIRED_MODELS = [
    'random_forest.pkl', 'support_vector_machine.pkl',
    'decision_tree.pkl', 'logistic_regression.pkl',
    'best_model.pkl', 'scaler.pkl',
    'label_encoder.pkl', 'results_summary.json'
]

def check_models():
    return [f for f in REQUIRED_MODELS
            if not os.path.exists(os.path.join(MODELS_DIR, f))]

def train():
    print("Training models. This takes 2 to 5 minutes...")
    result = subprocess.run(
        [sys.executable, os.path.join(BASE_DIR, 'src', 'train_models.py')],
        cwd=BASE_DIR
    )
    if result.returncode != 0:
        print("Training failed. Check that data/train_data.csv and data/test_data.csv exist.")
        sys.exit(1)

if __name__ == '__main__':
    print("=" * 55)
    print("  SmartHealth AI")
    print("  Enock Queenson Eduafo | 11014444")
    print("  University of Ghana | 2026")
    print("=" * 55)
    missing = check_models()
    if missing:
        print(f"Missing: {missing}")
        train()
    sys.path.insert(0, os.path.join(BASE_DIR, 'app'))
    print("\nStarting server at http://localhost:5000\n")
    from app import app
    app.run(debug=True, host='0.0.0.0', port=5000)
