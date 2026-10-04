"""
CoolRoute Backend API v2.0
FastAPI server with comprehensive ML, SHAP, temporal, optimization, and impact endpoints.
"""

import os
import json
import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np

# ── Existing imports (preserved) ─────────────────────────────────────────────
from chatbot_backend import ChatbotEngine

# ── New service imports ───────────────────────────────────────────────────────
from services.data_service import DataService
from services.satellite_service import SatelliteService
from services.weather_service import WeatherService
from services.ml_service import MLService
from services.heat_service import HeatService
from services.explainability_service import ExplainabilityService
from services.optimization_service import OptimizationService, TREE_SPECIES
from services.impact_service import ImpactService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="CoolRoute API",
    version="2.0.0",
    description=(
        "Urban Heat Island Mitigation — AI-powered decision support platform.\n\n"
        "**Demo Mode**: All satellite NDVI/LST values are DEMO (synthetic). "
        "Weather data is REAL (Open-Meteo). ML predictions are REAL (trained model)."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Initialize Services ───────────────────────────────────────────────────────
logger.info("Initializing CoolRoute services...")

data_svc = DataService(city="chennai")
satellite_svc = SatelliteService()
weather_svc = WeatherService()
ml_svc = MLService()
explain_svc = ExplainabilityService(ml_service=ml_svc)
optimizer_svc = OptimizationService()
impact_svc = ImpactService(ml_service=ml_svc)

heat_svc = HeatService(
    data_service=data_svc,
    satellite_service=satellite_svc,
    ml_service=ml_svc,
    explainability_service=explain_svc,
)

chatbot = ChatbotEngine()

logger.info("All services initialized.")

# ── Pydantic Models ───────────────────────────────────────────────────────────

class HeatPredictionRequest(BaseModel):
    ndvi: float = 0.3
    building_density: float = 0.5
    road_density: float = 10.0
    population_density: float = 20000.0
    distance_to_water: float = 2000.0
    elevation: float = 12.0
    albedo: float = 0.25
    income_index: float = 5.0
    existing_tree_cover: float = 0.1

class OptimizationRequest(BaseModel):
    budget: float = 500000.0
    max_trees: int = 500
    equity_weight: float = 0.5
    priority_wards: Optional[List[str]] = None
    weights: Optional[Dict[str, float]] = None
    min_trees_per_zone: int = 5
    max_trees_per_zone: int = 200

class ImpactSimulationRequest(BaseModel):
    planting_plan: List[Dict]
    zone_ids: Optional[List[str]] = None


# ── Helper ────────────────────────────────────────────────────────────────────

def _numpy_safe(obj):
    """Deep JSON-safe conversion for numpy types."""
    if isinstance(obj, dict):
        return {str(k): _numpy_safe(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_numpy_safe(x) for x in obj]
    elif isinstance(obj, (np.floating, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.integer, np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, np.ndarray):
        return [_numpy_safe(x) for x in obj.tolist()]
    elif isinstance(obj, (bool, str, int, float)) or obj is None:
        return obj
    try:
        if hasattr(obj, 'item'):
            return _numpy_safe(obj.item())
    except Exception:
        pass
    return obj


# ═══════════════════════════════════════════════════════════════════════════════
# ROOT
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    return {
        "message": "CoolRoute API v2.0 is running!",
        "version": "2.0.0",
        "model_loaded": ml_svc.is_loaded,
        "demo_mode": satellite_svc.is_demo,
        "endpoints": [
            "GET /api/data/status",
            "GET /api/data/sources",
            "GET /api/heat-map",
            "POST /api/predict-heat",
            "GET /api/heat/{lat}/{lng}",
            "GET /api/heat/timeseries",
            "GET /api/model/metrics",
            "GET /api/model/importance",
            "GET /api/model/explain/{zone_id}",
            "GET /api/weather/current",
            "GET /api/weather/timeseries",
            "POST /api/optimization",
            "POST /api/impact/simulation",
            "GET /api/ward-stats",
            "GET /api/impact-summary",
        ],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STATUS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/data/status")
async def get_data_status():
    """
    Returns the status of all data sources.
    Clearly distinguishes REAL vs DEMO data.
    """
    return {
        "data": data_svc.get_status(),
        "satellite": satellite_svc.get_status(),
        "weather": weather_svc.get_status(),
        "ml_model": {
            "loaded": ml_svc.is_loaded,
            "is_demo": False,
            "note": "XGBoost model trained on DEMO/synthetic data",
        },
        "global_demo_mode": satellite_svc.is_demo,
        "demo_banner": (
            "⚠️ DEMO MODE ACTIVE — Satellite NDVI/LST values are SIMULATED. "
            "Weather data is REAL (Open-Meteo). ML predictions are REAL (trained model)."
        ) if satellite_svc.is_demo else "✅ Real satellite data active",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/data/sources")
async def get_data_sources():
    """Return metadata about all data sources used."""
    return {
        "sources": data_svc.get_sources_info(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# HEAT MAP
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/heat-map")
async def get_heat_map(refresh: bool = False):
    """
    Returns GeoJSON FeatureCollection with ML-predicted heat zones.
    All features labeled with data provenance (real vs demo).
    """
    try:
        grid = heat_svc.build_heat_grid(force_refresh=refresh)
        features = []
        for cell in grid:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [cell["coordinates"]],
                },
                "properties": {
                    "grid_id": cell.get("grid_id"),
                    "temperature": cell.get("predicted_lst_c"),
                    "ndvi": cell.get("ndvi"),
                    "lst_estimated_c": cell.get("lst_estimated_c"),
                    "building_density": cell.get("building_density"),
                    "road_density": cell.get("road_density"),
                    "population_density": cell.get("population_density"),
                    "existing_tree_cover": cell.get("existing_tree_cover"),
                    "heat_risk": cell.get("heat_risk"),
                    "heat_risk_color": cell.get("heat_risk_color"),
                    "income_index": cell.get("income_index"),
                    "data_is_demo": cell.get("data_is_demo", True),
                    "ndvi_is_demo": cell.get("ndvi_is_demo", True),
                    "model_is_demo": False,
                },
            })

        stats = heat_svc.get_summary_stats()

        return {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "total_cells": len(features),
                "city": "Chennai",
                "summary": stats,
                "is_demo": satellite_svc.is_demo,
                "demo_note": "DEMO: Satellite NDVI/LST are simulated. ML predictions are from trained model.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"Heat map error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# HEAT PREDICTION
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/predict-heat")
async def predict_heat(request: HeatPredictionRequest):
    """
    Predict LST for a single zone using the trained XGBoost model.
    Returns prediction + SHAP explanation.
    """
    features = request.model_dump() if hasattr(request, 'model_dump') else request.dict()
    prediction = ml_svc.predict(features)
    lst = float(prediction["predicted_lst_c"])

    # SHAP explanation
    explanation = explain_svc.explain_why_hot(features, lst)
    global_importance = explain_svc.get_global_importance()

    return _numpy_safe({
        "predicted_lst_c": lst,
        "heat_risk": explanation["heat_risk"],
        "heat_risk_color": explanation["heat_risk_color"],
        "model_used": prediction.get("model_used"),
        "confidence": prediction.get("confidence"),
        "explanation": explanation,
        "global_feature_importance": global_importance.get("feature_importances", [])[:5],
        "note": prediction.get("note"),
        "training_data_note": prediction.get("training_data_note"),
    })


@app.get("/api/heat/{lat}/{lng}")
async def get_heat_at_point(lat: float, lng: float):
    """
    Get heat prediction and full SHAP explanation for a specific coordinate.
    Finds nearest grid cell and predicts heat.
    """
    try:
        result = heat_svc.predict_point(lat, lng)
        return _numpy_safe(result)
    except Exception as e:
        logger.error(f"Point prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# TEMPORAL ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/heat/timeseries")
async def get_heat_timeseries(date: Optional[str] = None, lat: float = 13.0827, lng: float = 80.2707):
    """
    Returns hourly heat pattern (air temp + estimated surface temp).
    Source: Open-Meteo (real air temp) + UHI offset (ESTIMATED surface temp).
    """
    weather_svc_local = WeatherService(lat=lat, lon=lng)
    timeseries = weather_svc_local.get_hourly_timeseries(date=date)
    return {
        **timeseries,
        "location": {"lat": lat, "lng": lng},
        "interpretation": {
            "morning": "06:00-10:00 — typically 28-33°C LST",
            "noon": "10:00-14:00 — peak heat period",
            "afternoon": "14:00-18:00 — highest UHI effect",
            "evening": "18:00-22:00 — gradual cooling",
        },
    }


@app.get("/api/weather/current")
async def get_current_weather():
    """Current weather conditions from Open-Meteo (real data)."""
    return weather_svc.get_current_weather()


@app.get("/api/weather/timeseries")
async def get_weather_timeseries(date: Optional[str] = None):
    """Hourly weather time-series from Open-Meteo."""
    return weather_svc.get_hourly_timeseries(date=date)


@app.get("/api/weather/historical")
async def get_weather_historical():
    """Last 7 days historical weather from Open-Meteo archive."""
    return weather_svc.get_historical_weekly()


# ═══════════════════════════════════════════════════════════════════════════════
# MODEL METRICS & EXPLAINABILITY
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/model/metrics")
async def get_model_metrics():
    """
    Returns actual model evaluation metrics from training.
    All values computed from the trained model — NOT hardcoded.
    """
    return ml_svc.get_metrics()


@app.get("/api/model/importance")
async def get_model_importance():
    """Returns feature importances from the trained model."""
    global_imp = explain_svc.get_global_importance()
    return {
        **global_imp,
        "model_loaded": ml_svc.is_loaded,
    }


@app.get("/api/model/explain/{zone_id}")
async def explain_zone(zone_id: str):
    """
    Returns SHAP-based explanation for why a zone has high/low heat.
    Values come from actual model — nothing is hardcoded.
    """
    grid = heat_svc.build_heat_grid()
    zone = next((c for c in grid if c.get("grid_id") == zone_id), None)
    if zone is None:
        raise HTTPException(status_code=404, detail=f"Zone {zone_id} not found")

    lst = float(zone.get("predicted_lst_c", 35.0))
    explanation = explain_svc.explain_why_hot(zone, lst)
    return _numpy_safe({
        "zone_id": zone_id,
        "latitude": zone.get("latitude"),
        "longitude": zone.get("longitude"),
        "predicted_lst_c": lst,
        **explanation,
    })


# ═══════════════════════════════════════════════════════════════════════════════
# OPTIMIZATION
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/optimization")
async def run_optimization(request: OptimizationRequest):
    """
    Generate optimized tree planting plan.
    Priority = HeatSeverity × PopulationExposure × Vulnerability × TreeDeficit × CoolingPotential
    All values from ML predictions — not hardcoded.
    """
    try:
        zones = heat_svc.build_heat_grid()
        result = optimizer_svc.optimize(
            budget=request.budget,
            max_trees=request.max_trees,
            zones=zones,
            equity_weight=request.equity_weight,
            weights=request.weights,
            min_trees_per_zone=request.min_trees_per_zone,
            max_trees_per_zone=request.max_trees_per_zone,
        )
        return result
    except Exception as e:
        logger.error(f"Optimization error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# IMPACT SIMULATION
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/impact/simulation")
async def run_impact_simulation(request: ImpactSimulationRequest):
    """
    Before/After simulation based on a planting plan.
    LST change calculated by re-running ML model with updated NDVI/tree_cover.
    All values ESTIMATED — labeled and assumption-documented.
    """
    try:
        grid = heat_svc.build_heat_grid()

        # Filter to specified zones if provided
        if request.zone_ids:
            zones = [c for c in grid if c.get("grid_id") in request.zone_ids]
        else:
            # Use top zones from planting plan
            plan_ids = {p.get("zone_id") for p in request.planting_plan}
            zones = [c for c in grid if c.get("grid_id") in plan_ids]

        if not zones:
            zones = grid[:20]  # Fallback to first 20 cells

        result = impact_svc.simulate(
            zones=zones,
            planting_plan=request.planting_plan,
            tree_species_db=TREE_SPECIES,
        )
        return result
    except Exception as e:
        logger.error(f"Impact simulation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# WARD STATS (Preserved + Upgraded)
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/ward-stats")
async def get_ward_stats():
    """
    Ward-level statistics derived from ML-predicted heat grid.
    No longer uses hardcoded random zones.
    """
    grid = heat_svc.build_heat_grid()

    # Group by approximate ward area (5×5 cell blocks)
    wards = {}
    for cell in grid:
        # Create ward groupings from grid coordinates
        lat_group = round(cell["latitude"] * 20) / 20  # 0.05° blocks
        lon_group = round(cell["longitude"] * 20) / 20
        ward_key = f"W_{lat_group:.3f}_{lon_group:.3f}"

        if ward_key not in wards:
            wards[ward_key] = {
                "ward": ward_key,
                "cells": [],
                "avg_temp": 0,
                "population": 0,
                "income": 0,
                "tree_cover": 0,
                "heat_risk": "LOW",
            }
        wards[ward_key]["cells"].append(cell)

    result = []
    for wid, ward in wards.items():
        cells = ward["cells"]
        lsts = [c.get("predicted_lst_c", 35) for c in cells]
        avg_lst = sum(lsts) / len(lsts)
        avg_pop = sum(c.get("population_density", 0) for c in cells) / len(cells)
        avg_income = sum(c.get("income_index", 5) for c in cells) / len(cells)
        avg_tc = sum(c.get("existing_tree_cover", 0.1) for c in cells) / len(cells)
        risk_counts = {}
        for c in cells:
            r = c.get("heat_risk", "LOW")
            risk_counts[r] = risk_counts.get(r, 0) + 1
        dominant_risk = max(risk_counts, key=risk_counts.get)

        result.append({
            "ward": wid,
            "avg_temp": round(avg_lst, 1),
            "population": int(avg_pop),
            "income": round(avg_income, 1),
            "tree_cover": round(avg_tc * 100, 1),
            "heat_risk": dominant_risk,
            "zones": len(cells),
            "center": {
                "lat": cells[len(cells) // 2]["latitude"],
                "lng": cells[len(cells) // 2]["longitude"],
            },
        })

    result.sort(key=lambda x: x["avg_temp"], reverse=True)
    return result[:20]


@app.get("/api/impact-summary")
async def get_impact_summary():
    """
    High-level impact summary derived from grid stats.
    All values labeled ESTIMATED where applicable.
    """
    stats = heat_svc.get_summary_stats()
    metrics = ml_svc.get_metrics()

    return {
        "city": "Chennai",
        "total_grid_cells": stats.get("total_cells", 0),
        "hotspot_count": stats.get("hotspot_count", 0),
        "avg_lst_c": stats.get("avg_lst_c"),
        "max_lst_c": stats.get("max_lst_c"),
        "population_at_risk": stats.get("total_population_at_risk"),
        "is_demo": stats.get("is_demo", True),
        "model_metrics": metrics.get("metrics", {}),
        "demo_note": (
            "DEMO: Satellite data is synthetic. "
            "Weather and ML model predictions are real."
        ),
    }


@app.get("/api/model-info")
async def get_model_info():
    """Return model training information (preserved from v1.0)."""
    return ml_svc.get_metrics()


# ═══════════════════════════════════════════════════════════════════════════════
# WEBSOCKET CHATBOT (Preserved)
# ═══════════════════════════════════════════════════════════════════════════════

@app.websocket("/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            response = await chatbot.generate_response(message)
            for char in response:
                await websocket.send_text(char)
                await asyncio.sleep(0.01)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
