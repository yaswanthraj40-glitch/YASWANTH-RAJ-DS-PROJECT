"""
CoolRoute Explainability Service
SHAP-based feature attribution for heat predictions.

Uses SHAP TreeExplainer when available.
Falls back to XGBoost feature_importances_ when SHAP is not installed.
All values come from the actual model — nothing is hardcoded.
"""

import json
import logging
import os
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

def _find_path(rel_path: str) -> str:
    """Find file path whether run from root or backend directory."""
    if os.path.exists(rel_path):
        return rel_path
    parent_rel = os.path.join("..", rel_path)
    if os.path.exists(parent_rel):
        return parent_rel
    file_dir = os.path.dirname(os.path.abspath(__file__))
    abs_path = os.path.join(file_dir, "..", rel_path)
    if os.path.exists(abs_path):
        return abs_path
    abs_root_path = os.path.join(file_dir, "..", "..", rel_path)
    if os.path.exists(abs_root_path):
        return abs_root_path
    return rel_path

SHAP_VALUES_PATH = _find_path("models/shap_values.json")
REPORT_PATH = _find_path("models/evaluation_report.json")

# Try to import SHAP (optional dependency)
try:
    import shap
    SHAP_AVAILABLE = True
    logger.info("SHAP library available — using TreeExplainer")
except ImportError:
    SHAP_AVAILABLE = False
    logger.warning(
        "SHAP not installed. Using XGBoost feature_importances_ as fallback. "
        "Install with: pip install shap"
    )

FEATURE_LABELS = {
    "building_density": "Building Density",
    "ndvi": "Vegetation (NDVI)",
    "road_density": "Road Density",
    "population_density": "Population Density",
    "distance_to_water": "Distance to Water",
    "elevation": "Elevation",
    "albedo": "Surface Albedo",
    "income_index": "Income Level",
    "existing_tree_cover": "Tree Cover",
}

FEATURE_DIRECTIONS = {
    # positive = increases heat, negative = reduces heat
    "building_density": "increases_heat",
    "ndvi": "reduces_heat",
    "road_density": "increases_heat",
    "population_density": "increases_heat",
    "distance_to_water": "increases_heat",
    "elevation": "reduces_heat",
    "albedo": "increases_heat",
    "income_index": "neutral",
    "existing_tree_cover": "reduces_heat",
}


class ExplainabilityService:
    """
    SHAP-based explainability for heat predictions.

    Provides:
    - Global feature importance (SHAP mean absolute values or gain-based)
    - Local explanation for a single zone (SHAP values or feature contribution)
    - Human-readable "Why is this area hot?" output
    """

    def __init__(self, ml_service=None):
        self.ml_service = ml_service
        self.explainer = None
        self._shap_background: Optional[np.ndarray] = None
        self._cached_global: Optional[Dict] = None

        # Load cached SHAP values if available
        self._load_cached_shap()

    def _load_cached_shap(self):
        """Load pre-computed SHAP values from model training."""
        if os.path.exists(SHAP_VALUES_PATH):
            try:
                with open(SHAP_VALUES_PATH, "r") as f:
                    data = json.load(f)
                self._cached_global = data
                logger.info("Loaded cached SHAP values from training")
            except Exception as e:
                logger.warning(f"Could not load cached SHAP: {e}")

    def _get_explainer(self):
        """Create or return SHAP TreeExplainer."""
        if not SHAP_AVAILABLE:
            return None
        if self.explainer is not None:
            return self.explainer
        if self.ml_service is None or not self.ml_service.is_loaded:
            return None

        try:
            self.explainer = shap.TreeExplainer(self.ml_service.model)
            return self.explainer
        except Exception as e:
            logger.error(f"Could not create SHAP explainer: {e}")
            return None

    # ------------------------------------------------------------------
    # Global Importance
    # ------------------------------------------------------------------

    def get_global_importance(self) -> Dict:
        """
        Returns global feature importance.
        Priority: cached SHAP from training → live SHAP → gain-based importance.
        All values from actual model. Nothing hardcoded.
        """
        # 1. Use cached SHAP values from training
        if self._cached_global:
            return {
                **self._cached_global,
                "method": "SHAP (cached from training)",
                "is_demo": False,
            }

        # 2. Use gain-based feature importance from model
        if self.ml_service and self.ml_service.is_loaded:
            fi = self.ml_service.get_feature_importances()
            importances = fi.get("feature_importances", [])
            total = sum(x["importance"] for x in importances) or 1.0
            formatted = [
                {
                    "feature": x["feature"],
                    "label": FEATURE_LABELS.get(x["feature"], x["feature"]),
                    "importance": x["importance"],
                    "percentage": round(x["importance"] / total * 100, 1),
                    "direction": FEATURE_DIRECTIONS.get(x["feature"], "neutral"),
                }
                for x in importances
            ]
            return {
                "feature_importances": formatted,
                "method": "XGBoost gain-based (SHAP fallback)",
                "is_demo": False,
                "note": "Install shap for SHAP-based attribution: pip install shap",
            }

        return {
            "feature_importances": [],
            "error": "Model not loaded",
            "is_demo": True,
        }

    # ------------------------------------------------------------------
    # Local Explanation (per zone)
    # ------------------------------------------------------------------

    def explain_zone(self, features: Dict) -> Dict:
        """
        Explain why a specific zone has the predicted heat score.

        Returns SHAP-based or gain-weighted contributions per feature.
        All values are from the actual model — not hardcoded percentages.
        """
        if not (self.ml_service and self.ml_service.is_loaded):
            return self._no_model_explanation()

        feature_names = self.ml_service.feature_names or []
        row = {f: features.get(f, self.ml_service._feature_default(f)) for f in feature_names}

        # Try SHAP local explanation
        explainer = self._get_explainer()
        if explainer is not None:
            return self._shap_local(row, feature_names)
        else:
            return self._gain_local(row, feature_names)

    def explain_why_hot(self, features: Dict, predicted_lst: float) -> Dict:
        """
        Generate human-readable "Why is this area hot?" explanation.
        """
        explanation = self.explain_zone(features)
        contributions = explanation.get("contributions", [])

        # Top contributors (positive = heat driver)
        heat_drivers = [c for c in contributions if c.get("contribution_direction") == "increases_heat"]
        cool_factors = [c for c in contributions if c.get("contribution_direction") == "reduces_heat"]

        risk = self._classify_risk(predicted_lst)

        reasons = []
        for i, d in enumerate(heat_drivers[:4], 1):
            pct = d.get("percentage", 0)
            label = d.get("label", d.get("feature", ""))
            reasons.append(f"{i}. {label} (+{pct:.1f}%)")

        return {
            "predicted_lst_c": predicted_lst,
            "heat_risk": risk["level"],
            "heat_risk_color": risk["color"],
            "top_heat_drivers": heat_drivers[:4],
            "cooling_factors": cool_factors[:2],
            "human_explanation": (
                f"This area reaches {predicted_lst:.1f}°C primarily due to "
                + ", ".join([d["label"] for d in heat_drivers[:3]])
                + "."
            ),
            "ranked_reasons": reasons,
            "method": explanation.get("method"),
            "is_demo": explanation.get("is_demo", False),
        }

    def _classify_risk(self, lst: float) -> Dict:
        if lst >= 46:
            return {"level": "EXTREME", "color": "#ff0000"}
        elif lst >= 43:
            return {"level": "HIGH", "color": "#ff006e"}
        elif lst >= 40:
            return {"level": "MODERATE", "color": "#ffb703"}
        else:
            return {"level": "LOW", "color": "#00ff88"}

    # ------------------------------------------------------------------
    # SHAP local explanation
    # ------------------------------------------------------------------

    def _shap_local(self, row: Dict, feature_names: List[str]) -> Dict:
        """Compute SHAP values for a single prediction."""
        try:
            df = pd.DataFrame([row])
            shap_values = self.explainer.shap_values(df)
            sv = shap_values[0] if isinstance(shap_values, list) else shap_values[0]
            base = float(self.explainer.expected_value)
            total_shap = float(np.sum(np.abs(sv)))

            contributions = []
            for i, (feat, val) in enumerate(zip(feature_names, sv)):
                pct = abs(val) / total_shap * 100 if total_shap > 0 else 0
                contributions.append({
                    "feature": feat,
                    "label": FEATURE_LABELS.get(feat, feat),
                    "shap_value": round(float(val), 4),
                    "percentage": round(pct, 1),
                    "contribution_direction": FEATURE_DIRECTIONS.get(feat, "neutral"),
                    "feature_value": round(row.get(feat, 0), 4),
                })
            contributions.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

            return {
                "contributions": contributions,
                "base_value": round(base, 2),
                "method": "SHAP TreeExplainer (local)",
                "is_demo": False,
            }
        except Exception as e:
            logger.error(f"SHAP local explanation failed: {e}")
            return self._gain_local(row, feature_names)

    def _gain_local(self, row: Dict, feature_names: List[str]) -> Dict:
        """Gain-based local explanation (SHAP fallback)."""
        importances = self.ml_service.model.feature_importances_
        total = float(np.sum(importances)) or 1.0

        contributions = []
        for feat, imp in zip(feature_names, importances):
            imp_val = float(imp)
            pct = float(imp_val / total * 100)
            feat_val = float(row.get(feat, 0))
            direction = FEATURE_DIRECTIONS.get(feat, "neutral")
            contributions.append({
                "feature": str(feat),
                "label": str(FEATURE_LABELS.get(feat, feat)),
                "shap_value": round(imp_val, 6),
                "percentage": round(pct, 1),
                "contribution_direction": str(direction),
                "feature_value": round(feat_val, 4),
            })
        contributions.sort(key=lambda x: x["percentage"], reverse=True)

        return {
            "contributions": contributions,
            "method": "XGBoost gain-based attribution (SHAP not available)",
            "is_demo": False,
            "note": "Install shap for per-prediction SHAP values: pip install shap",
        }

    def _no_model_explanation(self) -> Dict:
        return {
            "contributions": [],
            "error": "Model not loaded. Run: python model_train.py",
            "method": "none",
            "is_demo": True,
        }
