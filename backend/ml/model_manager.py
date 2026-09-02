"""
Smart Health Sync — Professional Model Manager
Authors: Enock Queenson Eduafo & Christabel Araba Edumadze | University of Ghana 2026

Handles model discovery, loading, validation, caching, and inference
with robust path resolution for local and cloud environments.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

import joblib
import numpy as np
from backend.ml.preprocessing.normalization import normalize_input

# ─── Logger ──────────────────────────────────────────────────
logger = logging.getLogger("smarthealth.ml")

# ─── Constants ───────────────────────────────────────────────
# Feature order MUST match train_models.py StandardScaler fit
FEATURE_ORDER = [
    "Glucose", "Cholesterol", "Hemoglobin", "Platelets",
    "White Blood Cells", "Red Blood Cells", "Hematocrit",
    "Mean Corpuscular Volume", "Mean Corpuscular Hemoglobin",
    "Mean Corpuscular Hemoglobin Concentration", "Insulin", "BMI",
    "Systolic Blood Pressure", "Diastolic Blood Pressure", "Triglycerides",
    "HbA1c", "LDL Cholesterol", "HDL Cholesterol", "ALT", "AST",
    "Heart Rate", "Creatinine", "Troponin", "C-reactive Protein",
]

CLASS_LABELS = [
    "Anemia", "Diabetes", "Healthy", "Heart Disease",
    "Thalassemia", "Thrombocytopenia",
]

CLASS_DESCRIPTIONS = {
    "Healthy":          "Physiological markers within established clinical baseline ranges.",
    "Diabetes":         "Glucose and HbA1c elevation suggests chronic metabolic dysregulation.",
    "Anemia":           "Red blood cell counts or haemoglobin concentration below physiological norms.",
    "Heart Disease":    "Cardiovascular enzyme and lipid markers indicate cardiac stress.",
    "Thalassemia":      "Hereditary blood disorder affecting haemoglobin production pathways.",
    "Thrombocytopenia": "Low platelet count indicating critical clotting risk factors.",
}

CLASS_RECOMMENDATIONS = {
    "Healthy":          ["Maintain your current healthy lifestyle and regular check-ups."],
    "Diabetes":         [
        "Consult an endocrinologist for HbA1c management.",
        "Monitor blood glucose levels regularly.",
        "Follow a low-glycaemic diet plan.",
    ],
    "Anemia":           [
        "Consult a haematologist for iron studies.",
        "Consider dietary iron supplementation.",
        "Follow up with full blood count in 4–6 weeks.",
    ],
    "Heart Disease":    [
        "Seek immediate cardiology review.",
        "Monitor lipid panel and troponin levels.",
        "Avoid high-sodium, high-fat diets.",
    ],
    "Thalassemia":      [
        "Genetic counselling is recommended.",
        "Regular haematology follow-up required.",
        "Avoid iron supplements without specialist advice.",
    ],
    "Thrombocytopenia": [
        "Urgent haematology consultation advised.",
        "Avoid aspirin and NSAIDs.",
        "Monitor for bleeding symptoms.",
    ],
}

GENERIC_RECOMMENDATIONS = [
    "Consult a licensed medical professional for formal clinical review.",
    "Ensure all biomarker inputs match your latest laboratory report.",
    "Do not modify any ongoing treatment based exclusively on algorithmic predictions.",
]


# ─── Path Resolution ─────────────────────────────────────────
def resolve_models_dir() -> Path:
    """
    Locate the /models directory across all common deployment environments.
    Supports: local dev, Render, Railway, Docker (/app), Vercel (/var/task).

    Preference order:
      1. MODEL_STORAGE_PATH env var
      2. Root-level /models (most common local + deployment layout)
      3. /app/models (Docker generic)
      4. /var/task/models (Vercel)
    """
    # 1. Environment variable override
    env_path = os.environ.get("MODEL_STORAGE_PATH", "")
    if env_path and Path(env_path).exists():
        logger.info(f"[ModelManager] Using MODEL_STORAGE_PATH: {env_path}")
        return Path(env_path)

    # 2. Walk up from this file to repo root, then check /models
    here = Path(__file__).resolve()
    candidate_roots = [
        here.parent.parent.parent,   # backend/ml/model_manager.py -> 3 levels up = repo root
        here.parent.parent,          # 2 levels up
        Path("/app"),                # Render / Railway / Docker
        Path("/var/task"),           # Vercel
        Path(os.getcwd()),           # Current working directory
    ]
    for root in candidate_roots:
        candidate = root / "models"
        if candidate.exists() and candidate.is_dir():
            # Prefer directories that actually contain .pkl files
            has_pkl = any(candidate.glob("*.pkl"))
            if has_pkl:
                logger.info(f"[ModelManager] Models directory (with .pkl): {candidate}")
                return candidate

    # 3. Fallback: return any existing models dir even without .pkl
    for root in candidate_roots:
        candidate = root / "models"
        if candidate.exists() and candidate.is_dir():
            logger.info(f"[ModelManager] Models directory (empty): {candidate}")
            return candidate

    # 4. Last resort: best guess
    fallback = here.parent.parent.parent / "models"
    logger.warning(f"[ModelManager] Could not locate models dir, defaulting to: {fallback}")
    return fallback


# ─── ModelManager ────────────────────────────────────────────
class ModelManager:
    """
    Singleton class managing model discovery, loading, validation, and inference.
    """

    def __init__(self):
        self.models_dir: Path = resolve_models_dir()
        self.scaler = None
        self.label_encoder = None
        self.summary: dict = {}

        self.features: list = FEATURE_ORDER
        self.classes: list = CLASS_LABELS

        self.loaded_models: Dict[str, Any] = {}
        self.missing_models: list = []
        self.corrupted_models: list = []

        self._classifier_files = {
            "random_forest":      "random_forest.pkl",
            "svm":                "svm.pkl",
            "decision_tree":      "decision_tree.pkl",
            "logistic_regression":"logistic_regression.pkl",
        }

        self.load_artifacts()

    def load_artifacts(self):
        """Discover and load scaler, label encoder, summary, and models."""
        logger.info(f"[ModelManager] Models directory (with .pkl): {self.models_dir}")
        logger.info("=" * 60)
        logger.info("[SmartHealth] Starting ML model validation …")

        self.loaded_models.clear()
        self.missing_models.clear()
        self.corrupted_models.clear()

        if not self.models_dir.exists():
            logger.error(f"[SmartHealth] Models directory does not exist: {self.models_dir}")
            return

        # Load scaler
        self._load_artefact("scaler", "scaler.pkl", "scaler")

        # Load label_encoder
        self._load_artefact("label_encoder", "label_encoder.pkl", "encoder")

        # Verify label_encoder classes
        if self.label_encoder is not None:
            actual_classes = set(self.label_encoder.classes_)
            expected_classes = {
                "Diabetes",
                "Anemia",
                "Thalassemia",
                "Heart Disease",
                "Thrombocytopenia",
                "Healthy"
            }
            if actual_classes != expected_classes:
                raise RuntimeError(
                    f"Invalid ML classes. Expected {sorted(expected_classes)}, got {sorted(actual_classes)}"
                )

        # Load summary
        self._load_summary()

        # Load available models
        for key, filename in self._classifier_files.items():
            self._load_model(key, filename)

        # Also attempt best_model.pkl as random_forest if present
        best_path = self.models_dir / "best_model.pkl"
        if best_path.exists() and "random_forest" not in self.loaded_models:
            self._load_model("random_forest", "best_model.pkl")

        # Summary log
        logger.info(f"[SmartHealth] ✓ Loaded models : {list(self.loaded_models.keys())}")
        logger.info(f"[SmartHealth] ✗ Missing models: {self.missing_models}")
        logger.info(f"[SmartHealth] ✗ Corrupt models: {self.corrupted_models}")
        logger.info("=" * 60)

    def _load_artefact(self, attr_name: str, filename: str, kind: str):
        path = self.models_dir / filename
        if not path.exists():
            logger.warning(f"[SmartHealth] Missing {kind}: {filename}")
            self.missing_models.append(filename)
            return
        try:
            obj = joblib.load(path)
            setattr(self, attr_name, obj)
            logger.info(f"[SmartHealth] Loaded {kind}: {filename}")
        except Exception as exc:
            logger.error(f"[SmartHealth] Corrupted {kind}: {filename} — {exc}", exc_info=True)
            self.corrupted_models.append(filename)

    def _load_summary(self):
        path = self.models_dir / "results_summary.json"
        if not path.exists():
            logger.warning("[SmartHealth] results_summary.json not found — using defaults.")
            return
        try:
            with open(path, "r", encoding="utf-8") as fh:
                self.summary = json.load(fh)
            if self.summary.get("features"):
                self.features = self.summary["features"]
            if self.summary.get("classes"):
                self.classes  = self.summary["classes"]
            logger.info("[SmartHealth] Loaded results_summary.json")
        except Exception as exc:
            logger.error(f"[SmartHealth] Failed to read results_summary.json: {exc}")
            self.corrupted_models.append("results_summary.json")

    def _load_model(self, key: str, filename: str):
        path = self.models_dir / filename
        if not path.exists():
            logger.warning(f"[SmartHealth] Missing model: {filename}")
            self.missing_models.append(filename)
            return
        try:
            model = joblib.load(path)
            self.loaded_models[key] = model
            logger.info(f"[SmartHealth] ✓ Loaded model: {key} ({filename})")
        except Exception as exc:
            logger.error(f"[SmartHealth] ✗ Corrupted model: {filename} — {exc}", exc_info=True)
            self.corrupted_models.append(filename)

    def get_model(self, key: str):
        key = self._normalise_key(key)
        if key in self.loaded_models:
            return self.loaded_models[key]
        filename = getattr(self, "_classifier_files", {}).get(key)
        if filename and (self.models_dir / filename).exists() and key not in self.corrupted_models:
            self._load_model(key, filename)
        return self.loaded_models.get(key)

    # ── Health Check ─────────────────────────────────────────
    def health_report(self) -> dict:
        return {
            "status":           "healthy" if self.loaded_models else "degraded",
            "models_directory": str(self.models_dir),
            "directory_exists": self.models_dir.exists(),
            "loaded_models":    list(self.loaded_models.keys()),
            "missing_models":   self.missing_models,
            "corrupted_models": self.corrupted_models,
            "scaler_loaded":    self.scaler is not None,
            "encoder_loaded":   self.label_encoder is not None,
            "feature_count":    len(self.features),
        }

    # ── Inference ────────────────────────────────────────────
    def predict(
        self,
        features_dict: dict,
        model_key: str = "random_forest",
        symptoms: list = None,
        preliminary_candidates: list = None
    ) -> dict:
        """
        Run inference on a raw clinical features dictionary.
        Clinical values are normalized via normalize_input ONCE before scaling.
        Integrates Two-Stage Clinical Evidence Fusion (Stage A Symptoms + Stage B Biomarkers).
        """
        model_key = self._normalise_key(model_key)
        model = self.get_model(model_key)
        fallback_used = False

        if model is None:
            for fallback in ["random_forest", "svm", "decision_tree", "logistic_regression"]:
                fallback_model = self.get_model(fallback)
                if fallback_model:
                    model = fallback_model
                    model_key = fallback
                    fallback_used = True
                    logger.warning(f"[SmartHealth] Fallback to model: {fallback}")
                    break

        if model is None:
            raise RuntimeError(
                "No diagnostic models are currently loaded. "
                f"Missing: {self.missing_models}, Corrupted: {self.corrupted_models}"
            )

        # Clinical reference normal midpoints for unselected/missing features so they remain neutral (z=0)
        DEFAULT_CLINICAL_NORMALS = {
            "Glucose": 90.0, "Cholesterol": 180.0, "Hemoglobin": 14.0, "Platelets": 250.0,
            "White Blood Cells": 6.5, "Red Blood Cells": 4.8, "Hematocrit": 42.0,
            "Mean Corpuscular Volume": 88.0, "Mean Corpuscular Hemoglobin": 30.0,
            "Mean Corpuscular Hemoglobin Concentration": 34.0, "Insulin": 10.0, "BMI": 23.5,
            "Systolic Blood Pressure": 120.0, "Diastolic Blood Pressure": 80.0, "Triglycerides": 120.0,
            "HbA1c": 5.4, "LDL Cholesterol": 95.0, "HDL Cholesterol": 55.0, "ALT": 25.0,
            "AST": 22.0, "Heart Rate": 72.0, "Creatinine": 0.9, "Troponin": 0.01,
            "C-reactive Protein": 3.0
        }

        feature_vector = []
        for f in self.features:
            if f in features_dict and features_dict[f] is not None and features_dict[f] != "":
                try:
                    val = float(features_dict[f])
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"Invalid numeric value for {f}: {features_dict[f]}") from exc
            else:
                val = float(DEFAULT_CLINICAL_NORMALS.get(f, 0.0))
            feature_vector.append(val)

        X_raw = np.array(feature_vector, dtype=np.float64).reshape(1, -1)

        # 3. Apply StandardScaler (fitted on raw clinical values during training)
        X = X_raw
        if self.scaler is not None:
            X = self.scaler.transform(X_raw)

        # 4. Predict & Decode Label
        if self.label_encoder is None:
            raise RuntimeError("Label encoder is required for safe six-class prediction.")

        pred_enc = model.predict(X)[0]
        pred_label = self.label_encoder.inverse_transform([pred_enc])[0]

        ALLOWED_CLASSES = {
            "Diabetes",
            "Anemia",
            "Thalassemia",
            "Heart Disease",
            "Thrombocytopenia",
            "Healthy"
        }
        if pred_label not in ALLOWED_CLASSES:
            raise RuntimeError(f"Model returned unsupported class: {pred_label}")

        # 5. Probabilities Map matching exact class labels
        raw_probabilities = {}
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X)[0]
            for model_class_index, probability in zip(model.classes_, proba):
                try:
                    label = self.label_encoder.inverse_transform([model_class_index])[0]
                except Exception:
                    label = str(model_class_index)
                raw_probabilities[label] = round(float(probability) * 100, 2)
        else:
            raw_probabilities = {c: (100.0 if c == pred_label else 0.0) for c in ALLOWED_CLASSES}

        # 6. Two-Stage Clinical Evidence Fusion Pipeline
        from backend.ml.clinical_fusion import fuse_clinical_evidence
        fusion_res = fuse_clinical_evidence(
            symptoms=symptoms or [],
            raw_features=features_dict,
            raw_probabilities=raw_probabilities,
            preliminary_candidates=preliminary_candidates or []
        )

        final_prediction = fusion_res["predictedDiagnosis"]
        final_confidence = fusion_res["confidence"]

        # 7. Feature Importances
        feature_importance = {}
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
            total_importance = float(np.sum(importances))
            if total_importance > 0:
                pairs = sorted(
                    zip(self.features, importances),
                    key=lambda x: x[1],
                    reverse=True,
                )[:5]
                feature_importance = {
                    name: round((float(imp) / total_importance) * 100, 1)
                    for name, imp in pairs
                }

        # 8. Generate clinical explanations using REAL raw clinical values
        explanations = self._generate_explanation(features_dict, final_prediction)

        return {
            "predictedDiagnosis":   final_prediction,
            "prediction":           final_prediction,
            "confidence":           round(final_confidence, 2),
            "symptomEvidence":      fusion_res["symptomEvidence"],
            "biomarkerEvidence":    fusion_res["biomarkerEvidence"],
            "combinedEvidence":     fusion_res["combinedEvidence"],
            "supportingSymptoms":   fusion_res["supportingSymptoms"],
            "supportingBiomarkers": fusion_res["supportingBiomarkers"],
            "conflictingEvidence":  fusion_res["conflictingEvidence"],
            "probabilities":        fusion_res["combinedEvidence"],
            "feature_importance":   feature_importance,
            "description":          CLASS_DESCRIPTIONS.get(final_prediction, "Diagnostic data under clinical review."),
            "explanations":         explanations,
            "recommendations":      (
                CLASS_RECOMMENDATIONS.get(final_prediction, []) + GENERIC_RECOMMENDATIONS
            ),
            "model_used":           model_key,
            "fallback_used":        fallback_used,
            "status":               "success",
        }

    def _generate_explanation(self, features: dict, prediction: str) -> list:
        """Generate human-readable explanations based on real clinical units."""
        explanations = []
        
        # 1. Diabetes
        if prediction == "Diabetes":
            glucose = float(features.get("Glucose", 0))
            hba1c = float(features.get("HbA1c", 0))
            insulin = float(features.get("Insulin", 0))
            
            if glucose > 126.0:
                explanations.append(f"Fasting glucose level ({glucose:.1f} mg/dL) is significantly elevated (> 126 mg/dL).")
            if hba1c > 6.5:
                explanations.append(f"HbA1c level ({hba1c:.1f}%) indicates long-term glycemic elevation (> 6.5%).")
            if insulin > 25.0:
                explanations.append(f"Insulin level ({insulin:.1f} uIU/mL) suggests metabolic resistance.")
            if not explanations:
                explanations.append("Glucose and HbA1c elevation indicates chronic metabolic dysregulation.")
                
        # 2. Anemia
        elif prediction == "Anemia":
            hemo = float(features.get("Hemoglobin", 0))
            rbc = float(features.get("Red Blood Cells", 0))
            hct = float(features.get("Hematocrit", 0))
            
            if hemo < 12.0 and hemo > 0:
                explanations.append(f"Hemoglobin concentration ({hemo:.1f} g/dL) is below physiological norms (< 12 g/dL).")
            if rbc < 4.1 and rbc > 0:
                explanations.append(f"Red blood cell count ({rbc:.2f} x10^6/uL) indicates reduced oxygen-carrying capacity.")
            if hct < 36.0 and hct > 0:
                explanations.append(f"Hematocrit ({hct:.1f}%) is reduced (< 36%).")
            if not explanations:
                explanations.append("Reduced red blood cell count and low haemoglobin concentration detected.")

        # 3. Heart Disease
        elif prediction == "Heart Disease":
            trop = float(features.get("Troponin", 0))
            ldl = float(features.get("LDL Cholesterol", 0))
            chol = float(features.get("Cholesterol", 0))
            crp = float(features.get("C-reactive Protein", 0))
            
            if trop > 0.04:
                explanations.append(f"Troponin level ({trop:.2f} ng/mL) is elevated, indicating cardiac muscle stress.")
            if ldl > 130.0 or chol > 200.0:
                explanations.append(f"Elevated lipid panel indicators (Cholesterol: {chol:.1f} mg/dL, LDL: {ldl:.1f} mg/dL) suggest cardiac risk.")
            if crp > 10.0:
                explanations.append(f"C-reactive protein ({crp:.1f} mg/L) indicates active vascular inflammation.")
            if not explanations:
                explanations.append("Elevated troponin and lipid indicators point to cardiovascular stress.")

        # 4. Thalassemia
        elif prediction == "Thalassemia":
            mcv = float(features.get("Mean Corpuscular Volume", 0))
            mch = float(features.get("Mean Corpuscular Hemoglobin", 0))
            mchc = float(features.get("Mean Corpuscular Hemoglobin Concentration", 0))
            
            if mcv < 80.0 and mcv > 0:
                explanations.append(f"Mean Corpuscular Volume (MCV) is low ({mcv:.1f} fL), indicating microcytosis (< 80 fL).")
            if mch < 27.0 and mch > 0:
                explanations.append(f"Mean Corpuscular Hemoglobin (MCH) is low ({mch:.1f} pg), matching hypochromic characteristics.")
            if mchc < 32.0 and mchc > 0:
                explanations.append(f"MCHC ({mchc:.1f} g/dL) is reduced (< 32 g/dL).")
            if not explanations:
                explanations.append("Abnormal hemoglobin production pathways and low MCV/MCH markers detected.")

        # 5. Thrombocytopenia
        elif prediction == "Thrombocytopenia":
            platelets = float(features.get("Platelets", 0))
            if platelets < 150.0 and platelets > 0:
                explanations.append(f"Platelet count ({platelets:.1f} x10^3/uL) is in the thrombocytopenia range (< 150 x10^3/uL).")
            else:
                explanations.append(f"Platelet indices ({platelets:.1f} x10^3/uL) indicate critical clotting risk factors.")

        # 6. Healthy
        else:
            explanations.append("All measured clinical biomarkers fall within normal physiological reference baselines.")
                
        return explanations

    # ── Helpers ──────────────────────────────────────────────
    @staticmethod
    def _normalise_key(raw: str) -> str:
        key_map = {
            "random_forest": "random_forest", "randomforest": "random_forest", "rf": "random_forest",
            "svm": "svm", "support_vector_machine": "svm", "svc": "svm",
            "decision_tree": "decision_tree", "decisiontree": "decision_tree", "dt": "decision_tree",
            "logistic_regression": "logistic_regression",
            "logisticregression": "logistic_regression", "lr": "logistic_regression",
        }
        return key_map.get(raw.lower().strip(), "random_forest")


# ── Global singleton ─────────────────────────────────────────
model_manager = ModelManager()
