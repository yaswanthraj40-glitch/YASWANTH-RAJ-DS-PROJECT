"""
Standalone Test Runner for CoolRoute Backend (Uses standard unittest)
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from services.ml_service import MLService
from services.optimization_service import OptimizationService
from services.weather_service import WeatherService
from services.satellite_service import SatelliteService
from services.data_service import DataService
from services.heat_service import HeatService
from services.explainability_service import ExplainabilityService
from services.impact_service import ImpactService

class TestCoolRouteCore(unittest.TestCase):
    def setUp(self):
        self.ml_svc = MLService()
        self.opt_svc = OptimizationService()
        self.sat_svc = SatelliteService()
        self.weather_svc = WeatherService()
        self.data_svc = DataService()
        self.explain_svc = ExplainabilityService(ml_service=self.ml_svc)
        self.impact_svc = ImpactService(ml_service=self.ml_svc)
        self.heat_svc = HeatService(
            data_service=self.data_svc,
            satellite_service=self.sat_svc,
            ml_service=self.ml_svc,
            explainability_service=self.explain_svc,
        )

    def test_ml_prediction(self):
        features = {
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
        res = self.ml_svc.predict(features)
        self.assertIn("predicted_lst_c", res)
        self.assertTrue(25.0 <= res["predicted_lst_c"] <= 60.0)

    def test_weather_service(self):
        current = self.weather_svc.get_current_weather()
        self.assertIn("air_temperature_c", current)
        self.assertIn("estimated_surface_temp_c", current)
        self.assertIn("source", current)

    def test_optimization_budget(self):
        zones = [
            {
                "grid_id": f"G{i}",
                "latitude": 13.08,
                "longitude": 80.27,
                "predicted_lst_c": 36.0 + i,
                "heat_risk": "HIGH",
                "building_density": 0.7,
                "road_density": 12.0,
                "population_density": 25000,
                "income_index": 3.0,
                "existing_tree_cover": 0.05,
                "area_km2": 0.25,
            }
            for i in range(10)
        ]
        budget = 50000.0
        res = self.opt_svc.optimize(budget=budget, max_trees=100, zones=zones)
        self.assertLessEqual(res["budget_used_inr"], budget + 1.0)
        self.assertTrue(len(res["planting_plan"]) > 0)
        self.assertIn("justification", res["planting_plan"][0])

    def test_shap_explainability(self):
        features = {
            "ndvi": 0.1,
            "building_density": 0.9,
            "road_density": 20.0,
            "population_density": 50000.0,
            "distance_to_water": 3000.0,
            "elevation": 10.0,
            "albedo": 0.35,
            "income_index": 2.0,
            "existing_tree_cover": 0.02,
        }
        res = self.explain_svc.explain_why_hot(features, 46.5)
        self.assertIn("top_heat_drivers", res)
        self.assertIn("human_explanation", res)

    def test_impact_simulation(self):
        zones = [
            {
                "grid_id": "G1",
                "latitude": 13.08,
                "longitude": 80.27,
                "predicted_lst_c": 46.0,
                "heat_risk": "EXTREME",
                "building_density": 0.8,
                "road_density": 15.0,
                "population_density": 35000,
                "income_index": 3.0,
                "existing_tree_cover": 0.05,
                "ndvi": 0.15,
                "albedo": 0.30,
                "area_km2": 0.25,
            }
        ]
        plan = [{"zone_id": "G1", "trees_recommended": 80, "species": "neem"}]
        sim = self.impact_svc.simulate(zones=zones, planting_plan=plan)
        self.assertTrue(sim["simulation_complete"])
        self.assertIn("summary", sim)
        self.assertIn("avg_cooling_c", sim["summary"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
