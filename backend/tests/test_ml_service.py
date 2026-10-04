"""
Tests for CoolRoute ML Service
Tests actual model behavior — not hardcoded values.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from services.ml_service import MLService

@pytest.fixture
def ml_svc():
    return MLService()

@pytest.fixture
def sample_features():
    return {
        "ndvi": 0.15,
        "building_density": 0.85,
        "road_density": 18.5,
        "population_density": 45000.0,
        "distance_to_water": 2500.0,
        "elevation": 12.0,
        "albedo": 0.35,
        "income_index": 3.0,
        "existing_tree_cover": 0.05,
    }

@pytest.fixture
def green_features():
    return {
        "ndvi": 0.65,
        "building_density": 0.10,
        "road_density": 2.0,
        "population_density": 2000.0,
        "distance_to_water": 300.0,
        "elevation": 20.0,
        "albedo": 0.15,
        "income_index": 8.0,
        "existing_tree_cover": 0.40,
    }


class TestMLServicePrediction:
    def test_predict_returns_dict(self, ml_svc, sample_features):
        result = ml_svc.predict(sample_features)
        assert isinstance(result, dict)

    def test_predict_has_lst(self, ml_svc, sample_features):
        result = ml_svc.predict(sample_features)
        assert "predicted_lst_c" in result
        lst = result["predicted_lst_c"]
        assert isinstance(lst, float)

    def test_lst_in_realistic_range(self, ml_svc, sample_features):
        result = ml_svc.predict(sample_features)
        lst = result["predicted_lst_c"]
        # Realistic Chennai range 28-52°C
        assert 25.0 <= lst <= 60.0, f"LST out of realistic range: {lst}"

    def test_urban_hotter_than_green(self, ml_svc, sample_features, green_features):
        """Urban high-density zone should predict higher LST than green low-density."""
        urban_result = ml_svc.predict(sample_features)
        green_result = ml_svc.predict(green_features)
        urban_lst = urban_result["predicted_lst_c"]
        green_lst = green_result["predicted_lst_c"]
        assert urban_lst > green_lst, (
            f"Urban ({urban_lst}°C) should be hotter than green ({green_lst}°C)"
        )

    def test_model_used_field_present(self, ml_svc, sample_features):
        result = ml_svc.predict(sample_features)
        assert "model_used" in result

    def test_predict_handles_missing_features(self, ml_svc):
        """Should not crash with partial features."""
        result = ml_svc.predict({"ndvi": 0.3})
        assert "predicted_lst_c" in result

    def test_predict_batch(self, ml_svc, sample_features, green_features):
        results = ml_svc.predict_batch([sample_features, green_features])
        assert len(results) == 2
        for r in results:
            assert "predicted_lst_c" in r

    def test_batch_empty(self, ml_svc):
        results = ml_svc.predict_batch([])
        assert results == []


class TestMLServiceMetrics:
    def test_get_metrics_returns_dict(self, ml_svc):
        metrics = ml_svc.get_metrics()
        assert isinstance(metrics, dict)

    def test_metrics_has_mae_rmse_r2(self, ml_svc):
        metrics = ml_svc.get_metrics()
        if metrics.get("model_loaded"):
            m = metrics.get("metrics", {})
            assert "mae_celsius" in m
            assert "rmse_celsius" in m
            assert "r2_score" in m

    def test_mae_is_positive(self, ml_svc):
        metrics = ml_svc.get_metrics()
        if metrics.get("model_loaded"):
            mae = metrics["metrics"].get("mae_celsius")
            if mae is not None:
                assert mae > 0

    def test_r2_in_range(self, ml_svc):
        metrics = ml_svc.get_metrics()
        if metrics.get("model_loaded"):
            r2 = metrics["metrics"].get("r2_score")
            if r2 is not None:
                assert -1.0 <= r2 <= 1.0


class TestMLServiceFeatureImportance:
    def test_importance_returns_list(self, ml_svc):
        fi = ml_svc.get_feature_importances()
        if "feature_importances" in fi:
            assert isinstance(fi["feature_importances"], list)

    def test_importance_values_sum_to_one(self, ml_svc):
        fi = ml_svc.get_feature_importances()
        if "feature_importances" in fi:
            total = sum(x["importance"] for x in fi["feature_importances"])
            assert abs(total - 1.0) < 0.01, f"Importances sum to {total}, not 1.0"
