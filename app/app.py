"""
SmartHealth AI — Flask Application Entry Point
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
    template_folder='templates',
    static_folder='static',
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
    """Renders the main landing page for SmartHealth AI."""
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

@app.route('/api/predict', methods=['POST'])
def api_predict():
    """Handles health biomarker data to generate clinical diagnostic predictions with fallback support."""
    try:
        data = request.get_json(force=True)
        
        # Model key normalizer: ensures frontend keys match backend expectations
        MODEL_KEY_MAP = {
            'random_forest': 'random_forest', 'randomforest': 'random_forest', 'rf': 'random_forest',
            'svm': 'svm', 'support_vector_machine': 'svm', 'supportvectormachine': 'svm',
            'decision_tree': 'decision_tree', 'decisiontree': 'decision_tree', 'dt': 'decision_tree',
            'logistic_regression': 'logistic_regression', 'logisticregression': 'logistic_regression', 'lr': 'logistic_regression',
        }

        model_key_raw = data.get('model', 'random_forest').lower().strip()
        model_key = MODEL_KEY_MAP.get(model_key_raw, 'random_forest')
        
        # Smart Fallback logic: use any available model if specific one fails to load
        model = MODELS.get(model_key)
        fallback_used = False
        if model is None:
            for fallback_key in ['random_forest', 'decision_tree', 'logistic_regression', 'svm']:
                if MODELS.get(fallback_key) is not None:
                    model = MODELS[fallback_key]
                    model_key = fallback_key
                    fallback_used = True
                    break
        
        if model is None:
            return jsonify({
                'error': 'No ML models are currently available. Please check deployment configuration.',
                'models_status': {k: v is not None for k, v in MODELS.items()}
            }), 503
        
        features = data.get('features', [])
        if len(features) != 24:
            return jsonify({'error': f'Expected 24 features, got {len(features)}'}), 400
        
        X = np.array(features, dtype=float).reshape(1, -1)
        prediction = int(model.predict(X)[0])
        probabilities = model.predict_proba(X)[0].tolist()
        confidence = round(max(probabilities) * 100, 1)
        
        CLASS_LABELS = [
            'Healthy Reference', 'Type 2 Diabetes', 'Clinical Anemia',
            'Heart Condition', 'Thalassemia', 'Thrombocytopenia'
        ]
        CLASS_DESCRIPTIONS = {
            'Healthy Reference': 'Biomarkers indicate physiological values within normal clinical ranges. No significant disease markers detected.',
            'Type 2 Diabetes': 'Elevated glucose and HbA1c levels suggest chronic metabolic dysregulation consistent with Type 2 Diabetes.',
            'Clinical Anemia': 'Low hemoglobin and RBC markers indicate iron-deficient erythropoiesis or blood loss anemia.',
            'Heart Condition': 'Elevated troponin and cardiovascular markers suggest potential ischemic or hypertensive cardiovascular stress.',
            'Thalassemia': 'Abnormal MCH and RBC structural markers indicate hereditary hemoglobin chain production disorder.',
            'Thrombocytopenia': 'Critically reduced platelet count indicates increased bleeding risk requiring urgent clinical review.'
        }
        CLASS_RECOMMENDATIONS = {
            'Healthy Reference': ['Maintain current lifestyle', 'Annual blood panel recommended', 'Continue balanced nutrition'],
            'Type 2 Diabetes': ['Consult endocrinologist immediately', 'Monitor blood glucose daily', 'Reduce simple carbohydrate intake'],
            'Clinical Anemia': ['Iron supplementation evaluation', 'Dietary iron increase', 'Consult haematologist'],
            'Heart Condition': ['Urgent cardiology referral', 'ECG and echocardiogram advised', 'Monitor blood pressure daily'],
            'Thalassemia': ['Genetic counselling recommended', 'Haematology specialist referral', 'Family screening advised'],
            'Thrombocytopenia': ['Immediate haematology referral', 'Avoid NSAIDs', 'Monitor for bleeding symptoms']
        }
        
        label = CLASS_LABELS[prediction] if prediction < len(CLASS_LABELS) else 'Unknown'
        
        return jsonify({
            'prediction': label,
            'confidence': confidence,
            'probabilities': dict(zip(CLASS_LABELS, probabilities)),
            'description': CLASS_DESCRIPTIONS.get(label, ''),
            'recommendations': CLASS_RECOMMENDATIONS.get(label, []),
            'model_used': model_key,
            'fallback_used': fallback_used
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'trace': traceback.format_exc()
        }), 500

if __name__ == '__main__':
    port  = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
