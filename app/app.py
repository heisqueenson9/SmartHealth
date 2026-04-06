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

# Safe model loading — never crash the server if a model file is missing
MODELS = {}
MODEL_FILES = {
    'random_forest': 'models/random_forest_model.pkl',
    'svm': 'models/svm_model.pkl', 
    'decision_tree': 'models/decision_tree_model.pkl',
    'logistic_regression': 'models/logistic_regression_model.pkl'
}

def load_models():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for name, path in MODEL_FILES.items():
        full_path = os.path.join(base, path)
        try:
            MODELS[name] = joblib.load(full_path)
            print(f"[SmartHealth] Loaded: {name}")
        except Exception as e:
            print(f"[SmartHealth] WARNING: Could not load {name}: {e}")
            MODELS[name] = None

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

@app.route('/api/predict', methods=['POST'])
def api_predict():
    """Handles health biomarker data to generate clinical diagnostic predictions."""
    try:
        data = request.get_json(force=True)
        model_key = data.get('model', 'random_forest')
        features = data.get('features', [])
        
        if len(features) != 24:
            return jsonify({'error': 'Exactly 24 features required'}), 400
        
        model = MODELS.get(model_key)
        if model is None:
            return jsonify({'error': f'Model {model_key} not available'}), 503
        
        X = np.array(features, dtype=float).reshape(1, -1)
        prediction = model.predict(X)[0]
        probabilities = model.predict_proba(X)[0].tolist()
        confidence = round(max(probabilities) * 100, 1)
        
        CLASS_LABELS = [
            'Clinical Anemia',
            'Type 2 Diabetes',
            'Healthy Reference',
            'Heart Condition',
            'Thalassemia',
            'Thrombocytopenia'
        ]
        CLASS_DESCRIPTIONS = {
            'Clinical Anemia': 'Low hemoglobin and RBC markers indicate iron-deficient erythropoiesis or blood loss anemia.',
            'Type 2 Diabetes': 'Elevated glucose and HbA1c levels suggest chronic metabolic dysregulation consistent with Type 2 Diabetes.',
            'Healthy Reference': 'Biomarkers indicate physiological values within normal clinical ranges. No significant disease markers detected.',
            'Heart Condition': 'Elevated troponin and cardiovascular markers suggest potential ischemic or hypertensive cardiovascular stress.',
            'Thalassemia': 'Abnormal MCH and RBC structural markers indicate hereditary hemoglobin chain production disorder.',
            'Thrombocytopenia': 'Critically reduced platelet count indicates increased bleeding risk requiring urgent clinical review.'
        }
        CLASS_RECOMMENDATIONS = {
            'Clinical Anemia': ['Iron supplementation evaluation', 'Dietary iron increase (red meat, leafy greens)', 'Consult haematologist', 'Repeat CBC in 4-6 weeks'],
            'Type 2 Diabetes': ['Consult endocrinologist immediately', 'Monitor blood glucose daily', 'Reduce simple carbohydrate intake', 'Begin aerobic exercise program'],
            'Healthy Reference': ['Maintain current lifestyle', 'Annual blood panel recommended', 'Continue balanced nutrition'],
            'Heart Condition': ['Urgent cardiology referral', 'ECG and echocardiogram advised', 'Monitor blood pressure daily', 'Restrict sodium intake'],
            'Thalassemia': ['Genetic counselling recommended', 'Haematology specialist referral', 'Regular transfusion monitoring if severe', 'Family screening advised'],
            'Thrombocytopenia': ['Immediate haematology referral', 'Avoid NSAIDs and blood thinners', 'Monitor for bleeding symptoms', 'Bone marrow evaluation may be required']
        }
        
        label = CLASS_LABELS[int(prediction)] if int(prediction) < len(CLASS_LABELS) else 'Unknown'
        
        return jsonify({
            'prediction': label,
            'confidence': confidence,
            'probabilities': dict(zip(CLASS_LABELS, probabilities)),
            'description': CLASS_DESCRIPTIONS.get(label, ''),
            'recommendations': CLASS_RECOMMENDATIONS.get(label, []),
            'model_used': model_key
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port  = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
