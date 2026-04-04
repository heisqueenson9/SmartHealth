# =============================================================
# SmartHealth AI - Flask Blueprints / Routes
# Author:      Enock Queenson Eduafo
# Student ID:  11014444
# Institution: University of Ghana (2026)
# =============================================================

from flask import Blueprint, request, jsonify
from .model_loader import loader
import numpy as np

# Create blueprint for API routes
api_bp = Blueprint('api', __name__)

@api_bp.route('/')
def metadata():
    """Root metadata about the project."""
    return jsonify({
        "status": "online",
        "project": "SmartHealth AI Serverless API",
        "developer": {
            "name": "Enock Queenson Eduafo",
            "student_id": "11014444",
            "institution": "University of Ghana",
            "year": "2026"
        },
        "description": "Vercel optimized serverless machine learning inference for health biomarkers.",
        "endpoints": {
            "/": "GET (This document)",
            "/predict": "POST (Inference endpoint)"
        },
        "supported_conditions": loader.classes
    })

@api_bp.route('/predict', methods=['POST'])
def predict():
    """Diagnostic inference endpoint with validation and exception handling."""
    try:
        # Load raw JSON from request
        data = request.get_json(force=True)
        
        # 1. Check for blank or malformed input
        if not data or 'features' not in data:
            return jsonify({
                "error": "Missing input data. Provide a 'features' dictionary.",
                "example": { "features": { "Glucose": 0.5, "Cholesterol": 0.5, "..." : "..." } }
            }), 400
            
        features_dict = data.get('features', {})
        
        # 2. Input Validation (Ensure all 24 features are present)
        input_values = []
        missing_features = []
        
        for feat in loader.features:
            val = features_dict.get(feat)
            if val is None:
                missing_features.append(feat)
            else:
                try:
                    input_values.append(float(val))
                except (ValueError, TypeError):
                    return jsonify({"error": f"Invalid numeric value for feature: {feat}"}), 400
                    
        if missing_features:
            return jsonify({
                "error": "Missing biomarker inputs.",
                "missing": missing_features,
                "count": len(missing_features)
            }), 400
            
        # 3. Model Inference Pipeline
        X = np.array(input_values).reshape(1, -1)
        X_scaled = loader.scaler.transform(X)
        
        # Performance inference
        pred_enc = loader.model.predict(X_scaled)[0]
        pred_label = loader.label_encoder.inverse_transform([pred_enc])[0]
        
        # Confidence calculation (if applicable for the model)
        confidence = None
        probabilities = {}
        
        if hasattr(loader.model, 'predict_proba'):
            proba_arr = loader.model.predict_proba(X_scaled)[0]
            confidence = float(np.max(proba_arr)) * 100
            
            # Map probabilities to class names
            for i, p in enumerate(proba_arr):
                lbl = loader.label_encoder.inverse_transform([i])[0]
                probabilities[lbl] = round(float(p) * 100, 2)
                
        # 4. Result Return
        return jsonify({
            "result": {
                "prediction": pred_label,
                "confidence": round(confidence, 2) if confidence is not None else "N/A",
                "probabilities": probabilities
            },
            "meta": {
                "model": "Random Forest (Ensemble)",
                "feature_count": len(input_values)
            }
        })
        
    except Exception as e:
        # Global exception handling for runtime stability
        return jsonify({
            "error": "Internal server error occurred during inference.",
            "details": str(e)
        }), 500
