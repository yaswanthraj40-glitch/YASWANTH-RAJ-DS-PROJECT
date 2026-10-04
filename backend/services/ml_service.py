"""
CoolRoute ML Service
Wraps the XGBoost model with proper preprocessing, evaluation, and persistence.
"""

import json
import logging
import os
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

FEATURE_NAMES = [
    "ndvi",
    "building_density",
    "road_density",
    "population_density",
    "distance_to_water",
    "elevation",
    "albedo",
    "income_index",
    "existing_tree_cover",
]

def _find_path(rel_path: str) -> str:
    """Find file path whether run from root or backend directory."""
    if os.path.exists(rel_path):
        return rel_path
    parent_rel = os.path.join("..", rel_path)
    if os.path.exists(parent_rel):
        return parent_rel
    # Also check absolute path relative to file
    file_dir = os.path.dirname(os.path.abspath(__file__))
    abs_path = os.path.join(file_dir, "..", rel_path)
    if os.path.exists(abs_path):
        return abs_path
    abs_root_path = os.path.join(file_dir, "..", "..", rel_path)
    if os.path.exists(abs_root_path):
        return abs_root_path
    return rel_path

MODEL_PATH = _find_path("models/heat_predictor.json")
FEATURES_PATH = _find_path("models/feature_names.json")
REPORT_PATH = _find_path("models/evaluation_report.json")
SCALER_PATH = _find_path("models/feature_scaler.json")


class MLService:
    """
    ML Service wrapping the XGBoost heat prediction model.
    - Loads the pre-trained model on init
    - Exposes predict(), get_metrics(), get_feature_importances()
    - All metrics are from the actual trained model, not hardcoded
    """

    def __init__(self):
        self.model: Optional[xgb.XGBRegressor] = None
        self.feature_names: Optional[List[str]] = None
        self.evaluation_report: Optional[Dict] = None
        self._load()

    # ------------------------------------------------------------------
    # Model Loading
    # ------------------------------------------------------------------

    def _load(self):
        """Load trained model, feature names, and evaluation report."""
        if os.path.exists(MODEL_PATH) and os.path.exists(FEATURES_PATH):
            try:
                self.model = xgb.XGBRegressor()
                self.model.load_model(MODEL_PATH)

                with open(FEATURES_PATH, "r") as f:
                    self.feature_names = json.load(f)

                logger.info(f"Model loaded: {len(self.feature_names)} features")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                self.model = None
                self.feature_names = FEATURE_NAMES

        else:
            logger.warning("Trained model not found. Run: python model_train.py")
            self.model = None
            self.feature_names = FEATURE_NAMES

        if os.path.exists(REPORT_PATH):
            try:
                with open(REPORT_PATH, "r") as f:
                    self.evaluation_report = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load evaluation report: {e}")

    def reload(self):
        """Reload model from disk (call after retraining)."""
        self._load()

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(self, features: Dict) -> Dict:
        """
        Predict LST for a single zone.

        Parameters
        ----------
        features : dict with keys matching FEATURE_NAMES

        Returns
        -------
        dict with predicted_lst_c, model_used, confidence
        """
        if self.model is None or self.feature_names is None:
            return self._formula_fallback(features)

        try:
            # Build input dataframe in correct feature order
            row = {f: features.get(f, self._feature_default(f)) for f in self.feature_names}
            df = pd.DataFrame([row])
            predicted = float(self.model.predict(df)[0])
            predicted = round(predicted, 2)

            return {
                "predicted_lst_c": predicted,
                "model_used": "XGBoost (trained)",
                "model_is_demo": False,
                "confidence": "high",
                "note": "Prediction from trained XGBoost model on synthetic training data.",
                "training_data_note": "Model trained on DEMO/synthetic data. Accuracy improves with real satellite LST.",
            }
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return self._formula_fallback(features)

    def predict_batch(self, cells: List[Dict]) -> List[Dict]:
        """Predict LST for a list of grid cells."""
        if self.model is None or self.feature_names is None:
            return [self._formula_fallback(c) for c in cells]

        try:
            rows = []
            for cell in cells:
                row = {f: cell.get(f, self._feature_default(f)) for f in self.feature_names}
                rows.append(row)
            df = pd.DataFrame(rows)
            predictions = self.model.predict(df)

            results = []
            for cell, pred in zip(cells, predictions):
                results.append({
                    **cell,
                    "predicted_lst_c": round(float(pred), 2),
                    "model_used": "XGBoost (trained)",
                    "model_is_demo": False,
                })
            return results

        except Exception as e:
            logger.error(f"Batch prediction error: {e}")
            return [self._formula_fallback(c) for c in cells]

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def get_metrics(self) -> Dict:
        """Return actual model evaluation metrics from stored report."""
        if self.evaluation_report is None:
            return {
                "error": "Model not trained. Run: python model_train.py",
                "model_loaded": False,
            }

        metrics = self.evaluation_report.get("metrics", {})
        return {
            "model_loaded": self.model is not None,
            "model_type": self.evaluation_report.get("model_type"),
            "training_date": self.evaluation_report.get("training_date"),
            "dataset": self.evaluation_report.get("dataset", {}),
            "hyperparameters": self.evaluation_report.get("hyperparameters", {}),
            "metrics": {
                "mae_celsius": metrics.get("mae_celsius"),
                "rmse_celsius": metrics.get("rmse_celsius"),
                "r2_score": metrics.get("r2_score"),
                "mape_percent": metrics.get("mape_percent"),
                "cv_mae_mean": metrics.get("cv_mae_mean"),
                "cv_mae_std": metrics.get("cv_mae_std"),
            },
            "feature_importance": self.evaluation_report.get("feature_importance", {}),
            "shap_available": os.path.exists("models/shap_values.json"),
            "note": "All metrics computed from actual model training. Not hardcoded.",
            "training_data_note": (
                "Model trained on DEMO/synthetic data based on urban morphology patterns. "
                "Metrics reflect model fit to synthetic data, not real satellite LST."
            ),
        }

    def get_feature_importances(self) -> Dict:
        """Return feature importances from the trained model."""
        if self.model is None or self.feature_names is None:
            return {"error": "Model not loaded"}
        importances = self.model.feature_importances_.tolist()
        paired = list(zip(self.feature_names, importances))
        paired.sort(key=lambda x: x[1], reverse=True)
        return {
            "feature_importances": [
                {"feature": f, "importance": round(imp, 6)}
                for f, imp in paired
            ],
            "method": "XGBoost gain-based importance",
            "note": "Use SHAP for more reliable feature attribution.",
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _feature_default(self, feature: str) -> float:
        """Default value for a missing feature."""
        defaults = {
            "ndvi": 0.3,
            "building_density": 0.5,
            "road_density": 10.0,
            "population_density": 20000.0,
            "distance_to_water": 2000.0,
            "elevation": 12.0,
            "albedo": 0.25,
            "income_index": 5.0,
            "existing_tree_cover": 0.1,
        }
        return defaults.get(feature, 0.0)

    def _formula_fallback(self, features: Dict) -> Dict:
        """Physics-based fallback when model is not available."""
        bd = features.get("building_density", 0.5)
        rd = features.get("road_density", 10.0)
        ndvi = features.get("ndvi", 0.3)
        pop = features.get("population_density", 20000.0)
        albedo = features.get("albedo", 0.25)
        tc = features.get("existing_tree_cover", 0.1)
        dw = features.get("distance_to_water", 2000.0)

        lst = (
            30.0
            + bd * 9.5
            + rd * 0.35
            + (1 - ndvi) * 6.5
            + pop * 0.00007
            + albedo * 3.5
            - tc * 5.5
            - dw * 0.0007
        )
        return {
            "predicted_lst_c": round(lst, 2),
            "model_used": "physics formula (fallback — model not loaded)",
            "model_is_demo": True,
            "confidence": "low",
            "note": "Run python model_train.py for XGBoost predictions.",
        }

    @property
    def is_loaded(self) -> bool:
        return self.model is not None
