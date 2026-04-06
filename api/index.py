import sys, os, joblib
from flask import jsonify

# Add project root to sys.path so we can import 'app'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app.app import app as application

# Set absolute paths for Vercel's serverless environment
application.static_folder   = os.path.join(BASE_DIR, 'static')
application.template_folder = os.path.join(BASE_DIR, 'app', 'templates')

# Pre-load models at startup for performance and verify they exist
application.MODELS = {}
MODEL_FILENAMES = {
    'random_forest':      'random_forest_model.pkl',
    'svm':                'svm_model.pkl',
    'decision_tree':      'decision_tree_model.pkl',
    'logistic_regression':'logistic_regression_model.pkl'
}

def bootstrap_models():
    """Robustly load ML binaries from the root /models directory."""
    for key, filename in MODEL_FILENAMES.items():
        path = os.path.join(BASE_DIR, 'models', filename)
        try:
            if os.path.exists(path):
                application.MODELS[key] = joblib.load(path)
                print(f"[SmartHealth] Successfully loaded {key} model.")
            else:
                print(f"[SmartHealth] ERROR: Model {filename} not found at {path}")
                application.MODELS[key] = None
        except Exception as e:
            print(f"[SmartHealth] CRITICAL failure loading {key}: {e}")
            application.MODELS[key] = None

# Run the model loader on startup
bootstrap_models()

# Export for Vercel
app = application
