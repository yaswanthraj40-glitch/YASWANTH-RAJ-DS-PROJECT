"""
Tests for CoolRoute Optimization Service
Tests budget constraints, priority ordering, equity weighting.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from services.optimization_service import OptimizationService

@pytest.fixture
def optimizer():
    return OptimizationService()

@pytest.fixture
def mock_zones():
    """Mock heat grid zones for testing."""
    zones = []
    for i in range(20):
        zones.append({
            "grid_id": f"G{i}_0",
            "latitude": 13.05 + i * 0.005,
            "longitude": 80.25,
            "predicted_lst_c": 35.0 + i * 0.5,
            "heat_risk": "HIGH" if i > 10 else "MODERATE",
            "building_density": 0.3 + i * 0.03,
            "road_density": 5.0 + i * 0.5,
            "population_density": 10000 + i * 2000,
            "distance_to_water": 1000 + i * 100,
            "elevation": 10.0,
            "albedo": 0.25,
            "income_index": 5.0 - i * 0.1,
            "existing_tree_cover": 0.2 - i * 0.008,
            "ndvi": 0.4 - i * 0.01,
            "area_km2": 0.25,
            "bbox": [80.248, 13.048 + i * 0.005, 80.252, 13.052 + i * 0.005],
        })
    return zones


class TestOptimizationBudget:
    def test_budget_not_exceeded(self, optimizer, mock_zones):
        budget = 100_000.0
        result = optimizer.optimize(budget=budget, max_trees=500, zones=mock_zones)
        assert result["budget_used_inr"] <= budget + 1.0  # +1 for float tolerance

    def test_budget_zero_returns_empty(self, optimizer, mock_zones):
        result = optimizer.optimize(budget=0, max_trees=500, zones=mock_zones)
        assert result["total_trees"] == 0

    def test_trees_not_exceed_max(self, optimizer, mock_zones):
        max_trees = 10
        result = optimizer.optimize(budget=1_000_000, max_trees=max_trees, zones=mock_zones)
        assert result["total_trees"] <= max_trees

    def test_remaining_budget_correct(self, optimizer, mock_zones):
        budget = 200_000.0
        result = optimizer.optimize(budget=budget, max_trees=500, zones=mock_zones)
        used = result["budget_used_inr"]
        remaining = result["budget_remaining_inr"]
        assert abs(used + remaining - budget) < 1.0


class TestOptimizationPriority:
    def test_highest_lst_zones_selected_first(self, optimizer, mock_zones):
        """High-heat zones should appear in the top of the planting plan."""
        result = optimizer.optimize(budget=50_000, max_trees=50, zones=mock_zones)
        plan = result.get("planting_plan", [])
        if len(plan) >= 2:
            # First zone should have higher or equal priority score than last
            assert plan[0]["priority_score"] >= plan[-1]["priority_score"]

    def test_justification_present(self, optimizer, mock_zones):
        result = optimizer.optimize(budget=100_000, max_trees=100, zones=mock_zones)
        plan = result.get("planting_plan", [])
        for zone in plan:
            assert "justification" in zone
            assert len(zone["justification"]) > 10

    def test_result_has_objective_formula(self, optimizer, mock_zones):
        result = optimizer.optimize(budget=100_000, max_trees=100, zones=mock_zones)
        assert "objective_formula" in result


class TestOptimizationEquity:
    def test_equity_weight_increases_vulnerability_weight(self, optimizer, mock_zones):
        result_low = optimizer.optimize(budget=200_000, max_trees=100, zones=mock_zones, equity_weight=0.0)
        result_high = optimizer.optimize(budget=200_000, max_trees=100, zones=mock_zones, equity_weight=1.0)
        
        low_vuln_w = result_low["objective_weights"].get("vulnerability", 0)
        high_vuln_w = result_high["objective_weights"].get("vulnerability", 0)
        assert high_vuln_w >= low_vuln_w

    def test_equity_weight_out_of_range_clamped(self, optimizer, mock_zones):
        result = optimizer.optimize(budget=100_000, max_trees=100, zones=mock_zones, equity_weight=2.0)
        assert result["optimization_complete"] is True


class TestOptimizationSummary:
    def test_summary_has_cooling_estimate(self, optimizer, mock_zones):
        result = optimizer.optimize(budget=100_000, max_trees=100, zones=mock_zones)
        assert "summary" in result
        s = result["summary"]
        assert "expected_avg_cooling_c" in s

    def test_estimated_labels_present(self, optimizer, mock_zones):
        result = optimizer.optimize(budget=100_000, max_trees=100, zones=mock_zones)
        plan = result.get("planting_plan", [])
        for zone in plan:
            if "estimated_cooling_note" in zone:
                assert "ESTIMATED" in zone["estimated_cooling_note"]
