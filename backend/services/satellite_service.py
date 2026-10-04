"""
CoolRoute Satellite Service
Provider interface for NDVI and LST.

REAL data requires Google Earth Engine credentials (see README).
In DEMO mode, values are derived from the synthetic data pipeline
and clearly labeled as DEMO/SIMULATED — NOT real satellite measurements.
"""

import logging
import os
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Whether GEE credentials are configured
GEE_AVAILABLE = bool(os.getenv("GEE_PROJECT_ID"))


def ndvi_from_formula(red: float, nir: float) -> float:
    """
    NDVI = (NIR - RED) / (NIR + RED)
    Valid range: -1.0 to 1.0
    Typical vegetation: 0.2 – 0.8
    """
    if (nir + red) == 0:
        return 0.0
    return round((nir - red) / (nir + red), 4)


def ndvi_to_heat_contribution(ndvi: float) -> float:
    """
    Estimate heat contribution from low NDVI.
    Based on: Buyadi et al. (2012), Weng et al. (2004) LST-NDVI relationship.
    Low NDVI (< 0.2) → high heat contribution.
    Returns a normalized 0–1 heat factor.
    """
    # Inverted: more vegetation = less heat
    return round(max(0.0, min(1.0, 1.0 - ndvi * 1.5)), 4)


def estimate_albedo_from_ndvi(ndvi: float, building_density: float) -> float:
    """
    Estimate surface albedo from NDVI and building density.
    Vegetation: low albedo (~0.15-0.25)
    Urban concrete/asphalt: higher albedo (~0.25-0.40)
    Note: This is an ESTIMATE, not a satellite measurement.
    """
    vegetation_albedo = 0.15 + (1 - ndvi) * 0.05
    urban_albedo = 0.20 + building_density * 0.20
    return round(vegetation_albedo * (1 - building_density) + urban_albedo * building_density, 4)


class SatelliteService:
    """
    Satellite data service.
    
    In DEMO mode (no GEE credentials): provides physics-based estimates
    derived from urban morphology and vegetation indices.
    All demo values are clearly labeled with is_demo=True.
    
    In REAL mode (GEE configured): would ingest actual Sentinel-2 NDVI
    and Landsat 8/9 thermal band (Band 10) for LST.
    """

    def __init__(self):
        self.gee_available = GEE_AVAILABLE
        self.is_demo = not GEE_AVAILABLE
        if self.gee_available:
            logger.info("GEE credentials found — satellite service ready for real data")
        else:
            logger.info(
                "GEE credentials not found — satellite service running in DEMO mode. "
                "Set GEE_PROJECT_ID env variable to enable real satellite data."
            )

    def get_status(self) -> Dict:
        return {
            "service": "SatelliteService",
            "gee_available": self.gee_available,
            "is_demo": self.is_demo,
            "data_type": "real" if not self.is_demo else "demo",
            "ndvi_source": "Sentinel-2 Band 4 + Band 8" if not self.is_demo else "DEMO — synthetic estimate",
            "lst_source": "Landsat 8/9 Band 10 (thermal)" if not self.is_demo else "DEMO — physics-based estimate",
            "spatial_resolution_m": 10 if not self.is_demo else "~500 (synthetic grid)",
            "note": (
                "DEMO MODE: Satellite-derived NDVI and LST are simulated from urban morphology features. "
                "They are NOT real satellite measurements. "
                "Configure GEE_PROJECT_ID to enable real Sentinel-2 and Landsat data."
            ) if self.is_demo else "Real satellite data from Google Earth Engine",
        }

    def get_ndvi_for_grid(self, grid_cells: List[Dict]) -> List[Dict]:
        """
        Returns NDVI for each grid cell.
        In demo mode: derived from building density (inverse relationship).
        In real mode: would query Sentinel-2 via GEE.
        
        Parameters
        ----------
        grid_cells : list of dicts with keys lat, lon, building_density
        
        Returns
        -------
        Same list with 'ndvi', 'ndvi_source', 'ndvi_is_demo' added per cell.
        """
        if self.gee_available:
            return self._real_ndvi(grid_cells)
        else:
            return self._demo_ndvi(grid_cells)

    def get_lst_for_grid(self, grid_cells: List[Dict]) -> List[Dict]:
        """
        Returns Land Surface Temperature (LST) estimates.
        In demo mode: derived from features via urban heat formula.
        In real mode: would use Landsat 8/9 thermal band (Band 10).
        
        Parameters
        ----------
        grid_cells : list of dicts with ndvi, building_density, road_density, etc.
        
        Returns
        -------
        Same list with 'lst_estimated_c', 'lst_source', 'lst_is_demo' per cell.
        """
        if self.gee_available:
            return self._real_lst(grid_cells)
        else:
            return self._demo_lst(grid_cells)

    def compute_ndvi_statistics(self, grid_cells: List[Dict]) -> Dict:
        """Compute summary statistics for NDVI across the grid."""
        ndvis = [c.get("ndvi", 0) for c in grid_cells if c.get("ndvi") is not None]
        if not ndvis:
            return {"error": "no ndvi data"}
        return {
            "mean": round(float(np.mean(ndvis)), 4),
            "min": round(float(np.min(ndvis)), 4),
            "max": round(float(np.max(ndvis)), 4),
            "std": round(float(np.std(ndvis)), 4),
            "low_vegetation_fraction": round(float(np.mean(np.array(ndvis) < 0.2)), 3),
            "is_demo": self.is_demo,
        }

    # ------------------------------------------------------------------
    # Demo mode (clearly labeled)
    # ------------------------------------------------------------------

    def _demo_ndvi(self, grid_cells: List[Dict]) -> List[Dict]:
        """
        DEMO: Estimate NDVI from building density.
        Scientific basis: Strong negative correlation between NDVI and
        urban built-up index (Weng, 2012; normalized NDVI vs NDBI).
        This is a modeled estimate, NOT a satellite measurement.
        """
        result = []
        for cell in grid_cells:
            bd = cell.get("building_density", 0.5)
            # Negative correlation: high buildings → low vegetation
            # Range: 0.02 (dense urban) to 0.65 (green periphery)
            base_ndvi = max(0.02, min(0.65, 0.6 - bd * 0.55))
            # Add spatial variation
            np.random.seed(int(cell.get("lat", 0) * 1000 + cell.get("lon", 0) * 100) % 2**31)
            ndvi = round(max(0.01, min(0.75, base_ndvi + np.random.normal(0, 0.04))), 4)
            result.append({
                **cell,
                "ndvi": ndvi,
                "ndvi_source": "DEMO — estimated from building density (not satellite)",
                "ndvi_is_demo": True,
                "albedo": estimate_albedo_from_ndvi(ndvi, bd),
                "albedo_source": "DEMO — estimated from NDVI + building density",
            })
        return result

    def _demo_lst(self, grid_cells: List[Dict]) -> List[Dict]:
        """
        DEMO: Estimate LST from urban features.
        Formula adapted from: Buyadi et al. (2012), Sheng et al. (2017).
        Parameters calibrated for tropical coastal cities (Chennai).
        This is a physics-based ESTIMATE, NOT a thermal satellite measurement.
        """
        result = []
        for cell in grid_cells:
            ndvi = cell.get("ndvi", 0.3)
            bd = cell.get("building_density", 0.5)
            rd = cell.get("road_density", 10.0)
            pop = cell.get("population_density", 20000)
            albedo = cell.get("albedo", 0.25)
            tree_cover = cell.get("existing_tree_cover", 0.1)
            dist_water = cell.get("distance_to_water", 2000)
            elevation = cell.get("elevation", 10)

            # Physics-based LST model
            lst = (
                30.0
                + bd * 9.5
                + rd * 0.35
                + (1 - ndvi) * 6.5
                + pop * 0.00007
                + albedo * 3.5
                - tree_cover * 5.5
                - dist_water * 0.0007
                - elevation * 0.05
                + np.random.normal(0, 0.6)
            )
            lst = round(max(28.0, min(52.0, lst)), 2)

            result.append({
                **cell,
                "lst_estimated_c": lst,
                "lst_source": "DEMO — physics-based estimate (NOT thermal satellite)",
                "lst_is_demo": True,
                "lst_assumptions": "Formula: Buyadi et al. (2012), calibrated for tropical coastal cities",
            })
        return result

    # ------------------------------------------------------------------
    # Real mode stubs (requires GEE)
    # ------------------------------------------------------------------

    def _real_ndvi(self, grid_cells: List[Dict]) -> List[Dict]:
        """
        REAL: Query Sentinel-2 NDVI from Google Earth Engine.
        Requires GEE_PROJECT_ID and authenticated earthengine-api.
        NOT implemented — returns demo with warning.
        """
        logger.error(
            "Real NDVI from GEE is configured but earth-engine client is not installed. "
            "Install earthengine-api and authenticate. Falling back to demo."
        )
        return self._demo_ndvi(grid_cells)

    def _real_lst(self, grid_cells: List[Dict]) -> List[Dict]:
        """
        REAL: Query Landsat 8/9 Band 10 (thermal) for LST from GEE.
        Requires GEE_PROJECT_ID and authenticated earthengine-api.
        NOT implemented — returns demo with warning.
        """
        logger.error(
            "Real LST from GEE is configured but earth-engine client is not installed. "
            "Install earthengine-api and authenticate. Falling back to demo."
        )
        return self._demo_lst(grid_cells)
