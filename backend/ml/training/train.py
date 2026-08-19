"""
Smart Health Sync — ML Training Pipeline
Authors: Enock Queenson Eduafo & Christabel Araba Edumadze | University of Ghana 2026

Handles data loading, preprocessing, model selection, training, 
evaluation, and persistence of model artefacts with leakage prevention.
"""

import os
import json
import logging
import shutil
import warnings
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score)
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

# ── Config ───────────────────────────────────────────────────
warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("smarthealth.train")

# ── Paths ────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATASETS_DIR = BASE_DIR / "datasets"
MODELS_ROOT = BASE_DIR / "models"
REGISTRY_DIR = BASE_DIR / "backend" / "ml" / "registry" / "models"

for d in [MODELS_ROOT, REGISTRY_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Feature Set ──────────────────────────────────────────────
FEATURES = [
    'Glucose', 'Cholesterol', 'Hemoglobin', 'Platelets',
    'White Blood Cells', 'Red Blood Cells', 'Hematocrit',
    'Mean Corpuscular Volume', 'Mean Corpuscular Hemoglobin',
    'Mean Corpuscular Hemoglobin Concentration', 'Insulin', 'BMI',
    'Systolic Blood Pressure', 'Diastolic Blood Pressure', 'Triglycerides',
    'HbA1c', 'LDL Cholesterol', 'HDL Cholesterol', 'ALT', 'AST',
    'Heart Rate', 'Creatinine', 'Troponin', 'C-reactive Protein'
]

DISEASE_LABELS = {
    'Healthy': 'Healthy',
    'Diabetes': 'Diabetes',
    'Anemia': 'Anemia',
    'Thalasse': 'Thalassemia',
    'Thalassemia': 'Thalassemia',
    'Thromboc': 'Thrombocytopenia',
    'Thrombocytopenia': 'Thrombocytopenia',
    'Heart Di': 'Heart Disease',
    'Heart Disease': 'Heart Disease'
}

# ── Pipeline Class ───────────────────────────────────────────
class TrainingPipeline:
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.models = {
            'random_forest': RandomForestClassifier(n_estimators=200, max_depth=15, class_weight='balanced', random_state=42),
            'decision_tree': DecisionTreeClassifier(max_depth=12, class_weight='balanced', random_state=42),
            'svm': SVC(kernel='rbf', C=10, probability=True, class_weight='balanced', random_state=42),
            'logistic_regression': LogisticRegression(max_iter=2000, class_weight='balanced', random_state=42)
        }
        self.results = []
        self.train_count = 0
        self.test_count = 0

    def clean_and_standardize(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['Disease'] = df['Disease'].map(DISEASE_LABELS).fillna(df['Disease'])
        df = df.dropna().drop_duplicates().reset_index(drop=True)
        return df

    def load_data(self):
        logger.info("Loading train and test datasets independently...")
        data_source = DATA_DIR if (DATA_DIR / "train_data.csv").exists() else DATASETS_DIR
        train_df = pd.read_csv(data_source / "train_data.csv")
        test_df = pd.read_csv(data_source / "test_data.csv")
        
        train_df = self.clean_and_standardize(train_df)
        test_df = self.clean_and_standardize(test_df)
        
        # Verify Leakage & Overlap
        train_hashes = set(train_df[FEATURES].astype(str).agg("|".join, axis=1))
        test_hashes = set(test_df[FEATURES].astype(str).agg("|".join, axis=1))
        overlap = train_hashes.intersection(test_hashes)
        if overlap:
            logger.warning(f"Overlap detected: removing {len(overlap)} duplicate test rows to prevent leakage.")
            test_df = test_df[~test_df[FEATURES].astype(str).agg("|".join, axis=1).isin(overlap)].reset_index(drop=True)

        # Fit LabelEncoder on all unique classes
        all_classes = sorted(list(set(train_df['Disease'].unique()).union(set(test_df['Disease'].unique()))))
        self.label_encoder.fit(all_classes)

        self.train_count = len(train_df)
        self.test_count = len(test_df)
        logger.info(f"Independent datasets loaded: {self.train_count} train samples, {self.test_count} test samples across {len(all_classes)} classes.")

        X_train = train_df[FEATURES].values
        y_train = self.label_encoder.transform(train_df['Disease'].values)
        X_test = test_df[FEATURES].values
        y_test = self.label_encoder.transform(test_df['Disease'].values)

        return X_train, X_test, y_train, y_test

    def train_and_evaluate(self):
        X_train, X_test, y_train, y_test = self.load_data()
        
        logger.info("Scaling features with StandardScaler...")
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Save preprocessing tools
        self._persist_artefact(self.scaler, "scaler.pkl")
        self._persist_artefact(self.label_encoder, "label_encoder.pkl")

        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

        for name, model in self.models.items():
            logger.info(f"Training {name}...")
            model.fit(X_train_scaled, y_train)
            
            y_pred = model.predict(X_test_scaled)
            
            acc = accuracy_score(y_test, y_pred)
            prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
            rec = recall_score(y_test, y_pred, average='weighted', zero_division=0)
            f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=cv)
            
            logger.info(f"  {name} Result: Accuracy={acc:.4f}, F1={f1:.4f}, CV={cv_scores.mean():.4f}")
            
            self._persist_artefact(model, f"{name}.pkl")
            if name == "svm":
                self._persist_artefact(model, "support_vector_machine.pkl")
            
            self.results.append({
                'name': name.replace('_', ' ').title(),
                'key': name,
                'accuracy': round(float(acc), 4),
                'precision': round(float(prec), 4),
                'recall': round(float(rec), 4),
                'f1_score': round(float(f1), 4),
                'cv_mean': round(float(cv_scores.mean()), 4),
                'confusion_matrix': confusion_matrix(y_test, y_pred).tolist()
            })

        best_model_entry = max(self.results, key=lambda x: x['f1_score'])
        best_model_obj = self.models[best_model_entry['key']]
        self._persist_artefact(best_model_obj, "best_model.pkl")

    def _persist_artefact(self, obj, filename):
        for target_dir in [MODELS_ROOT, REGISTRY_DIR]:
            joblib.dump(obj, target_dir / filename)

    def save_summary(self):
        best_model = max(self.results, key=lambda x: x['f1_score'])
        logger.info(f"Best model: {best_model['name']} ({best_model['key']})")
        
        summary = {
            'metadata': {
                'trained_at': datetime.utcnow().isoformat(),
                'author': 'Enock Queenson Eduafo & Christabel Araba Edumadze',
                'features': FEATURES,
                'preprocessing': 'StandardScaler',
                'dataset_clean': True,
                'train_samples': self.train_count,
                'test_samples': self.test_count,
                'leakage_free': True
            },
            'best_model': best_model['name'],
            'best_model_key': best_model['key'],
            'models': self.results,
            'classes': list(self.label_encoder.classes_)
        }
        
        with open(MODELS_ROOT / "results_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        shutil.copy(MODELS_ROOT / "results_summary.json", REGISTRY_DIR / "results_summary.json")

        # Also write synchronized metadata.json
        metadata = {
            "model_version": "v2.0.0-clean",
            "best_model": best_model['name'],
            "best_model_key": best_model['key'],
            "accuracy": best_model['accuracy'],
            "f1_score": best_model['f1_score'],
            "train_samples": self.train_count,
            "test_samples": self.test_count,
            "classes": list(self.label_encoder.classes_),
            "features": FEATURES,
            "trained_at": datetime.utcnow().isoformat()
        }
        with open(MODELS_ROOT / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        shutil.copy(MODELS_ROOT / "metadata.json", REGISTRY_DIR / "metadata.json")

# ── Execute ──────────────────────────────────────────────────
if __name__ == "__main__":
    pipeline = TrainingPipeline()
    pipeline.train_and_evaluate()
    pipeline.save_summary()
    logger.info("Training pipeline completed successfully.")
