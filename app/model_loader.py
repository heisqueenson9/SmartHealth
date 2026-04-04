# =============================================================
# SmartHealth AI - Vercel Model Loader
# Author:      Enock Queenson Eduafo
# Student ID:  11014444
# Institution: University of Ghana (2026)
# =============================================================

import os
import joblib
import json

class ModelLoader:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelLoader, cls).__new__(cls)
            cls._instance.model = None
            cls._instance.scaler = None
            cls._instance.label_encoder = None
            cls._instance.summary = None
            cls._instance.features = []
            cls._instance.classes = []
            cls._instance.load_all()
        return cls._instance

    def load_all(self):
        """Load models and preprocessing tools once per runtime instance."""
        # Vercel's relative path for files is usually from the root
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        models_dir = os.path.join(base_dir, 'models')
        
        try:
            self.scaler = joblib.load(os.path.join(models_dir, 'scaler.pkl'))
            self.label_encoder = joblib.load(os.path.join(models_dir, 'label_encoder.pkl'))
            
            with open(os.path.join(models_dir, 'results_summary.json'), 'r') as f:
                self.summary = json.load(f)
                
            self.features = self.summary['features']
            self.classes = self.summary['classes']
            
            # Use Random Forest as default best model for deployment
            self.model = joblib.load(os.path.join(models_dir, 'random_forest.pkl'))
            print("Vercel Model Loader: Success")
            
        except Exception as e:
            print(f"Vercel Model Loader Error: {e}")
            raise e

# Global instance for app usage
loader = ModelLoader()
