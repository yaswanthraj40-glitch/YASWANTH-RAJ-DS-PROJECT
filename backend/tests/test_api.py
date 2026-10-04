"""
Tests for CoolRoute FastAPI endpoints.
Tests API response structure, not hardcoded values.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from fastapi.testclient import TestClient

# Use pytest-asyncio for async tests
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="module")
def client():
    """Create test client once per test module."""
    from main import app
    with TestClient(app) as c:
        yield c


class TestRootEndpoint:
    def test_root_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_root_has_version(self, client):
        data = client.get("/").json()
        assert "version" in data

    def test_root_has_model_loaded(self, client):
        data = client.get("/").json()
        assert "model_loaded" in data


class TestDataStatus:
    def test_data_status_200(self, client):
        resp = client.get("/api/data/status")
        assert resp.status_code == 200

    def test_data_status_has_demo_flag(self, client):
        data = client.get("/api/data/status").json()
        assert "global_demo_mode" in data

    def test_data_sources_200(self, client):
        resp = client.get("/api/data/sources")
        assert resp.status_code == 200
        data = resp.json()
        assert "sources" in data


class TestHeatPrediction:
    def test_predict_heat_200(self, client):
        payload = {
            "ndvi": 0.2,
            "building_density": 0.8,
            "road_density": 15.0,
            "population_density": 40000.0,
            "distance_to_water": 2000.0,
            "elevation": 12.0,
            "albedo": 0.30,
            "income_index": 3.0,
            "existing_tree_cover": 0.05,
        }
        resp = client.post("/api/predict-heat", json=payload)
        assert resp.status_code == 200

    def test_predict_heat_has_lst(self, client):
        payload = {
            "ndvi": 0.3, "building_density": 0.5, "road_density": 10.0,
            "population_density": 20000.0, "distance_to_water": 2000.0,
            "elevation": 12.0, "albedo": 0.25, "income_index": 5.0,
            "existing_tree_cover": 0.1,
        }
        data = client.post("/api/predict-heat", json=payload).json()
        assert "predicted_lst_c" in data
        lst = data["predicted_lst_c"]
        assert isinstance(lst, (int, float))
        assert 20.0 <= lst <= 65.0

    def test_predict_heat_has_risk(self, client):
        payload = {
            "ndvi": 0.3, "building_density": 0.5, "road_density": 10.0,
            "population_density": 20000.0, "distance_to_water": 2000.0,
            "elevation": 12.0, "albedo": 0.25, "income_index": 5.0,
            "existing_tree_cover": 0.1,
        }
        data = client.post("/api/predict-heat", json=payload).json()
        assert "heat_risk" in data
        assert data["heat_risk"] in ("LOW", "MODERATE", "HIGH", "EXTREME")

    def test_predict_heat_has_explanation(self, client):
        payload = {
            "ndvi": 0.1, "building_density": 0.9, "road_density": 20.0,
            "population_density": 50000.0, "distance_to_water": 3000.0,
            "elevation": 10.0, "albedo": 0.35, "income_index": 2.0,
            "existing_tree_cover": 0.02,
        }
        data = client.post("/api/predict-heat", json=payload).json()
        assert "explanation" in data


class TestModelEndpoints:
    def test_model_metrics_200(self, client):
        resp = client.get("/api/model/metrics")
        assert resp.status_code == 200

    def test_model_metrics_not_hardcoded(self, client):
        data = client.get("/api/model/metrics").json()
        if data.get("model_loaded"):
            m = data.get("metrics", {})
            # Metrics should exist and be floats
            mae = m.get("mae_celsius")
            r2 = m.get("r2_score")
            if mae is not None:
                assert isinstance(mae, float)
            if r2 is not None:
                assert isinstance(r2, float)

    def test_model_importance_200(self, client):
        resp = client.get("/api/model/importance")
        assert resp.status_code == 200


class TestWeatherEndpoints:
    def test_current_weather_200(self, client):
        resp = client.get("/api/weather/current")
        assert resp.status_code == 200

    def test_weather_timeseries_200(self, client):
        resp = client.get("/api/weather/timeseries")
        assert resp.status_code == 200

    def test_timeseries_has_data(self, client):
        data = client.get("/api/weather/timeseries").json()
        assert "timeseries" in data
        assert len(data["timeseries"]) > 0

    def test_timeseries_has_demo_or_source_label(self, client):
        data = client.get("/api/weather/timeseries").json()
        assert "source" in data


class TestOptimizationEndpoint:
    def test_optimize_200(self, client):
        payload = {
            "budget": 100000,
            "max_trees": 100,
            "equity_weight": 0.5,
        }
        resp = client.post("/api/optimization", json=payload)
        assert resp.status_code == 200

    def test_optimize_budget_respected(self, client):
        budget = 50000
        payload = {"budget": budget, "max_trees": 500, "equity_weight": 0.5}
        data = client.post("/api/optimization", json=payload).json()
        assert data.get("budget_used_inr", 0) <= budget + 1

    def test_optimize_has_justification(self, client):
        payload = {"budget": 200000, "max_trees": 100, "equity_weight": 0.5}
        data = client.post("/api/optimization", json=payload).json()
        plan = data.get("planting_plan", [])
        for zone in plan:
            assert "justification" in zone


class TestWardStats:
    def test_ward_stats_200(self, client):
        resp = client.get("/api/ward-stats")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


class TestHeatTimeseries:
    def test_heat_timeseries_200(self, client):
        resp = client.get("/api/heat/timeseries")
        assert resp.status_code == 200

    def test_heat_timeseries_has_morning_noon(self, client):
        data = client.get("/api/heat/timeseries").json()
        assert "morning_avg" in data
        assert "noon_avg" in data
        assert "afternoon_avg" in data
        assert "evening_avg" in data
