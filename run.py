# =============================================================
# SmartHealth AI - Application Startup Script
# Author:      Enock Queenson Eduafo
# Student ID:  11014444
# Institution: University of Ghana
# Department:  Computer Science - Information Technology
# Supervisor:  Professor Solomon Mensah
# Year:        2026
# =============================================================
#
# Run this file from the SmartHealth-AI root folder:
#     python run.py
# =============================================================

import os
import sys
import json
import subprocess

# Add the project root to Python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)


MODELS_DIR = os.path.join(BASE_DIR, 'models')

def check_models():
    required = [
        'random_forest.pkl',
        'support_vector_machine.pkl',
        'decision_tree.pkl',
        'logistic_regression.pkl',
        'best_model.pkl',
        'scaler.pkl',
        'label_encoder.pkl',
        'results_summary.json'
    ]
    missing = [f for f in required if not os.path.exists(os.path.join(MODELS_DIR, f))]
    return missing

def train_models():
    print("\nModels not found. Running training script...\n")
    src_path = os.path.join(BASE_DIR, 'src', 'train_models.py')
    result = subprocess.run(
        [sys.executable, src_path],
        cwd=BASE_DIR,
        capture_output=False
    )
    if result.returncode != 0:
        print("\nERROR: Training script failed.")
        print("Make sure data/train_data.csv and data/test_data.csv exist.")
        sys.exit(1)

if __name__ == '__main__':
    print("=" * 55)
    print("  SmartHealth AI")
    print("  Enock Queenson Eduafo | ID: 11014444")
    print("  University of Ghana | 2026")
    print("=" * 55)

    # Auto-train if models are missing
    missing = check_models()
    if missing:
        print(f"\nMissing model files: {missing}")
        train_models()
        missing = check_models()
        if missing:
            print(f"Still missing after training: {missing}")
            sys.exit(1)

    print("\nAll models loaded. Starting Flask server...\n")
    print("  Open your browser at: http://localhost:5000\n")

    # Import and run the app
    from app.app import app
    # Set host and port for compatibility
    app.run(debug=False, host='0.0.0.0', port=5000)
