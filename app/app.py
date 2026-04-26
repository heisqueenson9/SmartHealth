"""
Smart Health Sync — Flask Application Entry Point
Author: Enock Queenson Eduafo (11014444)
University of Ghana | Final Year Project 2026
Supervisor: Professor Solomon Mensah

This module initialises the Flask web application, loads pre-trained
machine learning models from the /models directory, exposes prediction
API routes, and serves the frontend HTML templates.
"""

import os, json, numpy as np
from flask import Flask, render_template, request, jsonify
import joblib

app = Flask(__name__, 
    template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
    static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'),
    static_url_path='/static'
)

MODELS = {}

def find_model_file(filename):
    """
    Try every possible path where the model file could be on Vercel.
    Vercel deploys to /var/task/ — models must be found relative to that.
    """
    search_bases = [
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__)),
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        '/var/task',
        '/var/task/models',
    ]
    
    search_paths = []
    for base in search_bases:
        search_paths.extend([
            os.path.join(base, filename),
            os.path.join(base, 'models', filename),
            os.path.join(base, 'app', 'models', filename),
        ])
    
    for path in search_paths:
        if os.path.exists(path):
            print(f'[SmartHealth] Found model at: {path}')
            return path
    
    return None

def load_models():
    """Initialises all models by searching through multiple potential locations."""
    model_files = {
        'random_forest':      'random_forest_model.pkl',
        'svm':                'svm_model.pkl',
        'decision_tree':      'decision_tree_model.pkl',
        'logistic_regression':'logistic_regression_model.pkl',
    }
    for key, filename in model_files.items():
        path = find_model_file(filename)
        if path:
            try:
                MODELS[key] = joblib.load(path)
                print(f'[SmartHealth] SUCCESS: loaded {key}')
            except Exception as e:
                print(f'[SmartHealth] LOAD ERROR for {key}: {e}')
                MODELS[key] = None
        else:
            MODELS[key] = None

load_models()

@app.route('/')
def index():
    """Renders the main landing page for Smart Health Sync."""
    return render_template('index.html')

@app.route('/predict')
def predict_page():
    """Renders the prediction page with the data input form."""
    return render_template('predict.html')

@app.route('/results')
def results_page():
    """Renders the model performance and evaluation metrics page."""
    return render_template('results.html')

@app.route('/about')
def about_page():
    """Renders the about page with project details and researcher info."""
    return render_template('about.html')

@app.route('/api/debug')
def debug():
    """Diagnostic route to verify environment and file mapping for Vercel deployment."""
    import os
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_dir = os.path.join(base, 'models')
    result = {
        'cwd': os.getcwd(),
        'base': base,
        'model_dir': model_dir,
        'model_dir_exists': os.path.exists(model_dir),
        'files_in_models': os.listdir(model_dir) if os.path.exists(model_dir) else 'FOLDER NOT FOUND',
        'models_loaded': {k: (v is not None) for k, v in MODELS.items()},
        '__file__': __file__
    }
    return jsonify(result)

@app.route('/api/static-test')
def static_test():
    """Diagnostic route to verify static file availability for Vercel serving."""
    import os
    static_dir = app.static_folder
    files = []
    for root, dirs, filenames in os.walk(static_dir):
        for f in filenames:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, static_dir)
            files.append(rel)
    return jsonify({
        'static_folder': static_dir,
        'static_folder_exists': os.path.exists(static_dir),
        'files': sorted(files)
    })

@app.route('/api/predict', methods=['POST'])
def api_predict():
    """Handles health biomarker data to generate clinical diagnostic predictions via POST request."""
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({'error': 'Missing JSON body.', 'status': 'failed'}), 400
        
        # Model key normalizer: ensures frontend keys match backend expectations
        MODEL_KEY_MAP = {
            'random_forest': 'random_forest', 'randomforest': 'random_forest', 'rf': 'random_forest',
            'svm': 'svm', 'support_vector_machine': 'svm', 'supportvectormachine': 'svm',
            'decision_tree': 'decision_tree', 'decisiontree': 'decision_tree', 'dt': 'decision_tree',
            'logistic_regression': 'logistic_regression', 'logisticregression': 'logistic_regression', 'lr': 'logistic_regression',
        }

        model_key_raw = str(data.get('model', 'random_forest')).lower().strip()
        model_key = MODEL_KEY_MAP.get(model_key_raw, 'random_forest')
        
        # Fallback logic: check app context or global MODELS dictionary
        MODELS = getattr(app, 'MODELS', {})
        model = MODELS.get(model_key)
        
        fallback_used = False
        if model is None:
            # Emergency fallback: try and find any loaded model
            for alt_key in ['random_forest', 'decision_tree', 'logistic_regression', 'svm']:
                if MODELS.get(alt_key) is not None:
                    model = MODELS[alt_key]
                    model_key = alt_key
                    fallback_used = True
                    break
        
        if model is None:
            return jsonify({
                'error': 'Diagnostic models not available. Please verify model binaries in /models directory.',
                'status': 'failed',
                'models_status': {k: (v is not None) for k, v in MODELS.items()}
            }), 503
        
        features = data.get('features', [])
        if not isinstance(features, list) or len(features) != 24:
            return jsonify({'error': f'Expected 24 biomarker fields, received {len(features)}.', 'status': 'failed'}), 400
        
        # Standardised clinical biomarker processing
        X = np.array(features, dtype=float).reshape(1, -1)
        prediction = int(model.predict(X)[0])
        probabilities = model.predict_proba(X)[0].tolist()
        confidence = round(max(probabilities) * 100, 1)
        
        # CORRECT ALPHABETICAL ORDER from train_models.py (F1 Score Maximised)
        CLASS_LABELS = [
            'Clinical Anemia',    # 0
            'Type 2 Diabetes',    # 1
            'Healthy Reference',  # 2
            'Heart Condition',    # 3
            'Thalassemia',        # 4
            'Thrombocytopenia'    # 5
        ]
        
        CLASS_DESCRIPTIONS = {
            'Healthy Reference': 'Physiological markers within established clinical baseline ranges.',
            'Type 2 Diabetes': 'Glucose and HbA1c elevation suggests chronic metabolic dysregulation.',
            'Clinical Anemia': 'Red blood cell counts or hemoglobin concentration below physiological norms.',
            'Heart Condition': 'Cardiovascular enzyme and lipid markers indicate cardiac stress.',
            'Thalassemia': 'Hereditary blood disorder affecting hemoglobin production pathways.',
            'Thrombocytopenia': 'Low platelet count indicating critical clotting risk factors.'
        }
        
        label = CLASS_LABELS[prediction] if 0 <= prediction < len(CLASS_LABELS) else 'Unclassified'
        
        return jsonify({
            'prediction': label,
            'confidence': confidence,
            'probabilities': dict(zip(CLASS_LABELS, probabilities)),
            'description': CLASS_DESCRIPTIONS.get(label, 'Diagnostic data under clinical review.'),
            'recommendations': [
                "Consult a licensed medical professional for formal clinical review.",
                "Ensure all biomarker inputs match your latest laboratory report.",
                "Do not modify any ongoing treatment based exclusively on algorithmic predictions."
            ],
            'model_used': model_key,
            'fallback_used': fallback_used,
            'status': 'success'
        })
        
    except ValueError as ve:
        return jsonify({'error': f'Invalid numeric data: {str(ve)}', 'status': 'failed'}), 400
    except Exception as e:
        import traceback
        return jsonify({
            'error': 'Predictive engine encountered a runtime exception.',
            'status': 'failed',
            'detail': str(e),
            'trace': traceback.format_exc() if app.debug else None
        }), 500

if __name__ == '__main__':
    port  = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
