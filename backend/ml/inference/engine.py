"""Inference Engine wrapper for Smart Health Sync."""
from ..model_manager import model_manager

class InferenceEngine:
    """Compatibility wrapper around shared ModelManager."""
    def predict(self, features: dict, model_key: str = "random_forest") -> dict:
        return model_manager.predict(features, model_key)

engine = InferenceEngine()
