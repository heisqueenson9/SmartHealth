# =============================================================
# SmartHealth AI - Main Flask Application
# Author:      Enock Queenson Eduafo
# Student ID:  11014444
# Institution: University of Ghana
# Department:  Computer Science - Information Technology
# Supervisor:  Professor Solomon Mensah
# Year:        2026
# =============================================================

import os
import sys
import json
import numpy as np
import joblib
from flask import Flask, render_template, request, jsonify

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR   = os.path.join(BASE_DIR, 'models')
TEMPLATE_DIR = os.path.join(BASE_DIR, 'app', 'templates')
STATIC_DIR   = os.path.join(BASE_DIR, 'app', 'static')

app = Flask(
    __name__,
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR
)
app.jinja_env.globals['enumerate'] = enumerate

try:
    scaler        = joblib.load(os.path.join(MODELS_DIR, 'scaler.pkl'))
    label_encoder = joblib.load(os.path.join(MODELS_DIR, 'label_encoder.pkl'))
    with open(os.path.join(MODELS_DIR, 'results_summary.json')) as f:
        results_summary = json.load(f)
    MODELS = {
        'logistic_regression':    joblib.load(os.path.join(MODELS_DIR, 'logistic_regression.pkl')),
        'decision_tree':          joblib.load(os.path.join(MODELS_DIR, 'decision_tree.pkl')),
        'random_forest':          joblib.load(os.path.join(MODELS_DIR, 'random_forest.pkl')),
        'support_vector_machine': joblib.load(os.path.join(MODELS_DIR, 'support_vector_machine.pkl')),
    }
    print("All models loaded successfully.")
except Exception as e:
    print(f"ERROR loading models: {e}")
    print("Run: python src/train_models.py")
    sys.exit(1)

FEATURES = results_summary['features']
CLASSES  = results_summary['classes']

DISEASE_INFO = {
    'Healthy': {
        'color': '#C5E710',
        'description': 'No disease indicators detected. Continue maintaining a healthy lifestyle.',
        'recommendations': [
            'Regular check-ups every 12 months',
            'Maintain a balanced diet and regular exercise',
            'Monitor blood pressure and glucose levels annually'
        ]
    },
    'Diabetes': {
        'color': '#F4DF6B',
        'description': 'Indicators consistent with Diabetes Mellitus. Blood glucose regulation is impaired.',
        'recommendations': [
            'Consult an endocrinologist immediately',
            'Monitor blood glucose daily',
            'Follow a low-glycaemic diet plan',
            'Review insulin or medication regimen with your doctor'
        ]
    },
    'Anemia': {
        'color': '#8E9630',
        'description': 'Blood markers suggest reduced red blood cell count or haemoglobin levels.',
        'recommendations': [
            'Consult a haematologist',
            'Iron supplementation may be required',
            'Increase iron-rich foods in your diet',
            'Full blood count follow-up in 4 to 6 weeks'
        ]
    },
    'Heart Disease': {
        'color': '#e74c3c',
        'description': 'Cardiovascular risk markers are elevated. Indicators consistent with Heart Disease.',
        'recommendations': [
            'Seek immediate cardiology consultation',
            'ECG and stress test recommended',
            'Follow a low-sodium diet and avoid smoking',
            'Review cholesterol and blood pressure medication'
        ]
    },
    'Thalassemia': {
        'color': '#9b59b6',
        'description': 'Haemoglobin structure abnormalities detected consistent with Thalassemia.',
        'recommendations': [
            'Genetic counselling is recommended',
            'Regular haematology reviews required',
            'Monitor for iron overload if receiving transfusions',
            'Folic acid supplementation may be advised'
        ]
    },
    'Thrombocytopenia': {
        'color': '#e67e22',
        'description': 'Platelet count appears significantly reduced.',
        'recommendations': [
            'Immediate haematology referral required',
            'Avoid NSAIDs and blood thinners',
            'Monitor for unusual bruising or bleeding',
            'Bone marrow evaluation may be needed'
        ]
    },
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict')
def predict_page():
    return render_template('predict.html', features=FEATURES)

@app.route('/results')
def results_page():
    return render_template(
        'results.html',
        models=results_summary['models'],
        best_model=results_summary['best_model'],
        classes=CLASSES
    )

@app.route('/about')
def about_page():
    return render_template('about.html')

@app.route('/api/predict', methods=['POST'])
def api_predict():
    try:
        data      = request.get_json(force=True)
        model_key = data.get('model', results_summary['best_model_key'])
        values    = data.get('features', {})
        input_values = []
        for feat in FEATURES:
            val = values.get(feat)
            if val is None:
                return jsonify({'error': f'Missing feature: {feat}'}), 400
            input_values.append(float(val))
        X        = np.array(input_values).reshape(1, -1)
        X_scaled = scaler.transform(X)
        model    = MODELS.get(model_key, MODELS['random_forest'])
        pred_enc = model.predict(X_scaled)[0]
        pred_label = label_encoder.inverse_transform([pred_enc])[0]
        confidence = None
        all_probas = {}
        if hasattr(model, 'predict_proba'):
            proba_arr  = model.predict_proba(X_scaled)[0]
            confidence = float(np.max(proba_arr)) * 100
            all_probas = {
                label_encoder.inverse_transform([i])[0]: round(float(p) * 100, 2)
                for i, p in enumerate(proba_arr)
            }
        info = DISEASE_INFO.get(pred_label, {})
        return jsonify({
            'prediction':      pred_label,
            'confidence':      round(confidence, 2) if confidence else None,
            'probabilities':   all_probas,
            'model_used':      model_key,
            'color':           info.get('color', '#C5E710'),
            'description':     info.get('description', ''),
            'recommendations': info.get('recommendations', []),
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/models', methods=['GET'])
def api_models():
    return jsonify(results_summary)

if __name__ == '__main__':
    port  = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
