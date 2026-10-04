"""
Comprehensive Route Verification Script for CoolRoute API
Tests all 18 routes against the live running server or direct test client.
"""
import sys
import os
import json
import requests

BASE_URL = "http://localhost:8000"

def test_all_routes():
    print("=" * 70)
    print("[*] CoolRoute API Comprehensive Route Verification")
    print("=" * 70)

    results = []

    # 1. GET /
    try:
        r = requests.get(f"{BASE_URL}/", timeout=30)
        assert r.status_code == 200
        assert "version" in r.json()
        results.append(("GET /", "PASS", r.status_code, "Root endpoint active"))
    except Exception as e:
        results.append(("GET /", "FAIL", getattr(r, 'status_code', 'ERR'), str(e)))

    # 2. GET /api/data/status
    try:
        r = requests.get(f"{BASE_URL}/api/data/status", timeout=30)
        assert r.status_code == 200
        assert "global_demo_mode" in r.json()
        results.append(("GET /api/data/status", "PASS", r.status_code, "Data status & demo flag verified"))
    except Exception as e:
        results.append(("GET /api/data/status", "FAIL", getattr(r, 'status_code', 'ERR'), str(e)))

    # 3. GET /api/data/sources
    try:
        r = requests.get(f"{BASE_URL}/api/data/sources", timeout=30)
        assert r.status_code == 200
        assert "sources" in r.json()
        results.append(("GET /api/data/sources", "PASS", r.status_code, "Data sources metadata returned"))
    except Exception as e:
        results.append(("GET /api/data/sources", "FAIL", getattr(r, 'status_code', 'ERR'), str(e)))

    # 4. GET /api/heat-map
    try:
        r = requests.get(f"{BASE_URL}/api/heat-map", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data.get("type") == "FeatureCollection"
        assert len(data.get("features", [])) > 0
        results.append(("GET /api/heat-map", "PASS", r.status_code, f"{len(data['features'])} GeoJSON heat zones"))
    except Exception as e:
        results.append(("GET /api/heat-map", "FAIL", getattr(r, 'status_code', 'ERR'), str(e)))

    # 5. POST /api/predict-heat
    try:
        payload = {
            "ndvi": 0.15,
            "building_density": 0.85,
            "road_density": 18.0,
            "population_density": 45000,
            "distance_to_water": 2500,
            "elevation": 12.0,
            "albedo": 0.35,
            "income_index": 3.0,
            "existing_tree_cover": 0.05
        }
        r = requests.post(f"{BASE_URL}/api/predict-heat", json=payload, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "predicted_lst_c" in data
        assert "explanation" in data
        results.append(("POST /api/predict-heat", "PASS", r.status_code, f"Predicted LST: {data['predicted_lst_c']}°C with SHAP"))
    except Exception as e:
        results.append(("POST /api/predict-heat", "FAIL", getattr(r, 'status_code', 'ERR'), str(e)))

    # 6. GET /api/heat/{lat}/{lng}
    try:
        r = requests.get(f"{BASE_URL}/api/heat/13.0827/80.2707", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "predicted_lst_c" in data
        results.append(("GET /api/heat/{lat}/{lng}", "PASS", r.status_code, f"Point heat: {data['predicted_lst_c']}°C at (13.08, 80.27)"))
    except Exception as e:
        results.append(("GET /api/heat/{lat}/{lng}", "FAIL", getattr(r, 'status_code', 'ERR'), str(e)))

    # 7. GET /api/heat/timeseries
    try:
        r = requests.get(f"{BASE_URL}/api/heat/timeseries", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "timeseries" in data
        results.append(("GET /api/heat/timeseries", "PASS", r.status_code, f"{len(data['timeseries'])} hourly points"))
    except Exception as e:
        results.append(("GET /api/heat/timeseries", "FAIL", getattr(r, 'status_code', 'ERR'), str(e)))

    # 8. GET /api/weather/current
    try:
        r = requests.get(f"{BASE_URL}/api/weather/current", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "air_temperature_c" in data
        results.append(("GET /api/weather/current", "PASS", r.status_code, f"Air temp: {data['air_temperature_c']}°C ({data.get('source', '')})"))
    except Exception as e:
        results.append(("GET /api/weather/current", "FAIL", getattr(r, 'status_code', 'ERR'), str(e)))

    # 9. GET /api/weather/timeseries
    try:
        r = requests.get(f"{BASE_URL}/api/weather/timeseries", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "timeseries" in data
        results.append(("GET /api/weather/timeseries", "PASS", r.status_code, f"{len(data['timeseries'])} weather intervals"))
    except Exception as e:
        results.append(("GET /api/weather/timeseries", "FAIL", getattr(r, 'status_code', 'ERR'), str(e)))

    # 10. GET /api/weather/historical
    try:
        r = requests.get(f"{BASE_URL}/api/weather/historical", timeout=30)
        assert r.status_code == 200
        data = r.json()
        results.append(("GET /api/weather/historical", "PASS", r.status_code, f"{len(data.get('history', []))} days historical archive"))
    except Exception as e:
        results.append(("GET /api/weather/historical", "FAIL", getattr(r, 'status_code', 'ERR'), str(e)))

    # 11. GET /api/model/metrics
    try:
        r = requests.get(f"{BASE_URL}/api/model/metrics", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "metrics" in data
        results.append(("GET /api/model/metrics", "PASS", r.status_code, f"MAE: {data['metrics'].get('mae_celsius')}°C, R²: {data['metrics'].get('r2_score')}"))
    except Exception as e:
        results.append(("GET /api/model/metrics", "FAIL", getattr(r, 'status_code', 'ERR'), str(e)))

    # 12. GET /api/model/importance
    try:
        r = requests.get(f"{BASE_URL}/api/model/importance", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "feature_importances" in data
        results.append(("GET /api/model/importance", "PASS", r.status_code, f"{len(data['feature_importances'])} features ranked"))
    except Exception as e:
        results.append(("GET /api/model/importance", "FAIL", getattr(r, 'status_code', 'ERR'), str(e)))

    # 13. GET /api/model/explain/{zone_id}
    try:
        r = requests.get(f"{BASE_URL}/api/model/explain/G0_0", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "top_heat_drivers" in data or "human_explanation" in data
        results.append(("GET /api/model/explain/{zone_id}", "PASS", r.status_code, "SHAP zone attribution verified"))
    except Exception as e:
        results.append(("GET /api/model/explain/{zone_id}", "FAIL", getattr(r, 'status_code', 'ERR'), str(e)))

    # 14. POST /api/optimization
    try:
        opt_payload = {
            "budget": 500000,
            "max_trees": 500,
            "equity_weight": 0.75
        }
        r = requests.post(f"{BASE_URL}/api/optimization", json=opt_payload, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "planting_plan" in data
        assert "summary" in data
        results.append(("POST /api/optimization", "PASS", r.status_code, f"Allocated {data['total_trees']} trees across {data['zones_selected']} zones"))
    except Exception as e:
        results.append(("POST /api/optimization", "FAIL", getattr(r, 'status_code', 'ERR'), str(e)))

    # 15. POST /api/impact/simulation
    try:
        sim_payload = {
            "planting_plan": [
                {"zone_id": "G0_0", "trees_recommended": 50, "species": "neem"}
            ]
        }
        r = requests.post(f"{BASE_URL}/api/impact/simulation", json=sim_payload, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "summary" in data
        results.append(("POST /api/impact/simulation", "PASS", r.status_code, f"Simulation avg cooling: -{data['summary'].get('avg_cooling_c')}°C"))
    except Exception as e:
        results.append(("POST /api/impact/simulation", "FAIL", getattr(r, 'status_code', 'ERR'), str(e)))

    # 16. GET /api/ward-stats
    try:
        r = requests.get(f"{BASE_URL}/api/ward-stats", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        results.append(("GET /api/ward-stats", "PASS", r.status_code, f"{len(data)} ward aggregated entries"))
    except Exception as e:
        results.append(("GET /api/ward-stats", "FAIL", getattr(r, 'status_code', 'ERR'), str(e)))

    # 17. GET /api/impact-summary
    try:
        r = requests.get(f"{BASE_URL}/api/impact-summary", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "avg_lst_c" in data
        results.append(("GET /api/impact-summary", "PASS", r.status_code, f"City avg LST: {data['avg_lst_c']}°C, hotspots: {data['hotspot_count']}"))
    except Exception as e:
        results.append(("GET /api/impact-summary", "FAIL", getattr(r, 'status_code', 'ERR'), str(e)))

    # 18. GET /api/model-info
    try:
        r = requests.get(f"{BASE_URL}/api/model-info", timeout=10)
        assert r.status_code == 200
        results.append(("GET /api/model-info", "PASS", r.status_code, "Model info compatibility route active"))
    except Exception as e:
        results.append(("GET /api/model-info", "FAIL", getattr(r, 'status_code', 'ERR'), str(e)))

    print("\n" + "-" * 70)
    print(f"{'ROUTE':<35} | {'STATUS':<6} | {'CODE':<5} | {'DETAILS'}")
    print("-" * 70)
    for route, status, code, details in results:
        status_symbol = "[OK]" if status == "PASS" else "[FAIL]"
        print(f"{route:<35} | {status_symbol:<6} | {str(code):<5} | {details}")
    print("-" * 70)

    passed = sum(1 for r in results if r[1] == "PASS")
    total = len(results)
    print(f"\nSummary: {passed}/{total} Routes Tested and Verified Successfully!")
    if passed == total:
        print("[SUCCESS] ALL ROUTES WORK 100% PERFECTLY!")
    else:
        print("[WARNING] Some routes need rectification.")

if __name__ == "__main__":
    test_all_routes()
