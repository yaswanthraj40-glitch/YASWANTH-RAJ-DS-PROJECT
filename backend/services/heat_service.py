"""
CoolRoute Heat Service
Orchestrates data → features → ML prediction → risk classification → hotspots.
"""

import logging
import math
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Heat risk thresholds (°C LST)
HEAT_THRESHOLDS = {
    "EXTREME": 46.0,
    "HIGH": 43.0,
    "MODERATE": 40.0,
    "LOW": 0.0,
}

HEAT_COLORS = {
    "EXTREME": "#ff0000",
    "HIGH": "#ff006e",
    "MODERATE": "#ffb703",
    "LOW": "#00ff88",
}


def classify_heat_risk(lst: float) -> Dict:
    """Classify heat risk from LST (°C)."""
    if lst >= HEAT_THRESHOLDS["EXTREME"]:
        level = "EXTREME"
    elif lst >= HEAT_THRESHOLDS["HIGH"]:
        level = "HIGH"
    elif lst >= HEAT_THRESHOLDS["MODERATE"]:
        level = "MODERATE"
    else:
        level = "LOW"
    return {
        "level": level,
        "color": HEAT_COLORS[level],
        "threshold": HEAT_THRESHOLDS[level],
    }


class HeatService:
    """
    Orchestrates the full heat analysis pipeline.
    
    Integrates:
    - DataService (grid + features)
    - SatelliteService (NDVI + LST)
    - MLService (XGBoost prediction)
    - ExplainabilityService (SHAP)
    """

    def __init__(self, data_service, satellite_service, ml_service, explainability_service):
        self.data = data_service
        self.satellite = satellite_service
        self.ml = ml_service
        self.explain = explainability_service
        self._heat_grid_cache: Optional[List[Dict]] = None

    def build_heat_grid(self, force_refresh: bool = False) -> List[Dict]:
        """
        Build complete heat grid with ML predictions.
        Returns: list of grid cells with all features + predicted LST + risk.
        """
        if self._heat_grid_cache and not force_refresh:
            return self._heat_grid_cache

        # Step 1: Get base grid with OSM features
        cells = self.data.build_grid()

        # Step 2: Add satellite-derived NDVI
        cells = self.satellite.get_ndvi_for_grid(cells)

        # Step 3: Add satellite-derived LST estimates
        cells = self.satellite.get_lst_for_grid(cells)

        # Step 4: ML prediction for all cells
        cells = self.ml.predict_batch(cells)

        # Step 5: Add risk classification + coordinates for map
        result = []
        for cell in cells:
            lst = cell.get("predicted_lst_c") or cell.get("lst_estimated_c", 35.0)
            risk = classify_heat_risk(lst)

            # Build polygon coordinates for Mapbox (GeoJSON)
            lat = cell["latitude"]
            lon = cell["longitude"]
            bbox = cell.get("bbox", [lon - 0.0025, lat - 0.0025, lon + 0.0025, lat + 0.0025])
            w, s, e, n = bbox
            coordinates = [[w, s], [e, s], [e, n], [w, n], [w, s]]

            result.append({
                **cell,
                "heat_risk": risk["level"],
                "heat_risk_color": risk["color"],
                "coordinates": coordinates,
                "center": [lon, lat],
                # Label data provenance clearly
                "data_is_demo": cell.get("osm_is_demo", True),
                "ndvi_is_demo": cell.get("ndvi_is_demo", True),
                "lst_is_demo": cell.get("lst_is_demo", True),
                "ml_is_demo": False,  # ML prediction is real (from trained model)
            })

        self._heat_grid_cache = result
        return result

    def get_hotspots(self, threshold: str = "HIGH") -> List[Dict]:
        """
        Return zones above a heat risk threshold, sorted by LST descending.
        threshold: 'LOW' | 'MODERATE' | 'HIGH' | 'EXTREME'
        """
        grid = self.build_heat_grid()
        levels = list(HEAT_THRESHOLDS.keys())
        threshold_idx = levels.index(threshold) if threshold in levels else 1
        valid_levels = levels[:threshold_idx + 1]

        hotspots = [c for c in grid if c.get("heat_risk") in valid_levels]
        hotspots.sort(key=lambda x: x.get("predicted_lst_c", 0), reverse=True)
        return hotspots

    def predict_point(self, lat: float, lon: float, features: Optional[Dict] = None) -> Dict:
        """
        Predict heat for a specific coordinate.
        If features not provided, uses nearest grid cell's features.
        """
        grid = self.build_heat_grid()
        
        # Find nearest cell
        nearest = min(
            grid,
            key=lambda c: (c["latitude"] - lat) ** 2 + (c["longitude"] - lon) ** 2,
        )
        
        if features is None:
            features = nearest

        prediction = self.ml.predict(features)
        lst = prediction["predicted_lst_c"]
        risk = classify_heat_risk(lst)
        explanation = self.explain.explain_why_hot(features, lst)

        return {
            "latitude": lat,
            "longitude": lon,
            "nearest_grid_id": nearest.get("grid_id"),
            "predicted_lst_c": lst,
            "heat_risk": risk["level"],
            "heat_risk_color": risk["color"],
            "features_used": {
                k: features.get(k) for k in self.ml.feature_names or []
            },
            "explanation": explanation,
            "model_used": prediction.get("model_used"),
            "data_is_demo": nearest.get("data_is_demo", True),
        }

    def get_summary_stats(self) -> Dict:
        """Compute summary statistics for the heat grid."""
        grid = self.build_heat_grid()
        lsts = [c.get("predicted_lst_c", 0) for c in grid if c.get("predicted_lst_c")]
        if not lsts:
            return {"error": "No predictions available"}

        import numpy as np
        risk_counts = {}
        for c in grid:
            r = c.get("heat_risk", "UNKNOWN")
            risk_counts[r] = risk_counts.get(r, 0) + 1

        return {
            "total_cells": len(grid),
            "avg_lst_c": round(float(np.mean(lsts)), 2),
            "max_lst_c": round(float(np.max(lsts)), 2),
            "min_lst_c": round(float(np.min(lsts)), 2),
            "risk_distribution": risk_counts,
            "hotspot_count": risk_counts.get("HIGH", 0) + risk_counts.get("EXTREME", 0),
            "total_population_at_risk": sum(
                c.get("population_density", 0) * c.get("area_km2", 0.25)
                for c in grid
                if c.get("heat_risk") in ("HIGH", "EXTREME")
            ),
            "city": self.data.city,
            "is_demo": all(c.get("data_is_demo", True) for c in grid[:5]),
        }
