"""
CoolRoute Data Service
Centralized data ingestion pipeline:
  Raw Data → Validation → Cleaning → Coordinate Transform → Spatial Join
           → Feature Engineering → Grid Cells → ML Dataset

Attempts real OSM and population data first.
Falls back to clearly-labeled DEMO data when unavailable.
"""

import logging
import math
import os
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import numpy as np
import requests

logger = logging.getLogger(__name__)

# ── City configuration ────────────────────────────────────────────────────────
CITY_CONFIGS = {
    "chennai": {
        "bounds": [13.00, 80.20, 13.15, 80.35],  # [south, west, north, east]
        "center": [13.0827, 80.2707],
        "grid_spacing_deg": 0.005,  # ~500m grid
        "population_grid_km2_estimate": 25000,
    }
}

DEFAULT_CITY = "chennai"

# ── Data source metadata ──────────────────────────────────────────────────────
DATA_SOURCES = {
    "osm_buildings": {
        "name": "OpenStreetMap Buildings",
        "provider": "Overpass API",
        "url": "https://overpass-api.de/api/interpreter",
        "license": "ODbL",
        "key_required": False,
    },
    "osm_roads": {
        "name": "OpenStreetMap Roads",
        "provider": "Overpass API",
        "url": "https://overpass-api.de/api/interpreter",
        "license": "ODbL",
        "key_required": False,
    },
    "osm_water": {
        "name": "OpenStreetMap Water Bodies",
        "provider": "Overpass API",
        "url": "https://overpass-api.de/api/interpreter",
        "license": "ODbL",
        "key_required": False,
    },
    "weather": {
        "name": "Open-Meteo Weather API",
        "provider": "Open-Meteo",
        "url": "https://open-meteo.com",
        "license": "CC BY 4.0",
        "key_required": False,
    },
    "ndvi_lst": {
        "name": "NDVI / LST (Satellite)",
        "provider": "Google Earth Engine / Sentinel-2 / Landsat 9",
        "url": "https://earthengine.google.com",
        "license": "Varies",
        "key_required": True,
        "key_env": "GEE_PROJECT_ID",
    },
    "population": {
        "name": "Population Density",
        "provider": "WorldPop / Census of India",
        "url": "https://hub.worldpop.org",
        "license": "CC BY 4.0",
        "key_required": False,
    },
}


class DataService:
    """
    Centralized data service that orchestrates OSM, population, and feature data.

    Usage:
        svc = DataService(city="chennai")
        grid = svc.build_grid()  # Returns list of grid cells with all features
        status = svc.get_status()  # Returns per-source status
    """

    def __init__(self, city: str = DEFAULT_CITY):
        self.city = city
        self.config = CITY_CONFIGS.get(city, CITY_CONFIGS[DEFAULT_CITY])
        self.bounds = self.config["bounds"]
        self.source_status: Dict[str, Dict] = {}
        self._grid_cache: Optional[List[Dict]] = None
        self._cache_time: Optional[float] = None
        self._cache_ttl = 3600  # 1 hour

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_grid(self, force_refresh: bool = False) -> List[Dict]:
        """
        Build the full grid of cells for the city.
        Returns: list of grid cells, each with all features and metadata.
        """
        now = time.time()
        if (
            self._grid_cache is not None
            and self._cache_time is not None
            and (now - self._cache_time) < self._cache_ttl
            and not force_refresh
        ):
            return self._grid_cache

        logger.info(f"Building data grid for {self.city}...")

        # Step 1: Create spatial grid
        cells = self._create_grid()
        logger.info(f"  Created {len(cells)} grid cells")

        # Step 2: Try to get OSM data
        osm_data = self._fetch_osm_data()

        # Step 3: Compute features per cell
        cells = self._compute_features(cells, osm_data)

        # Step 4: Add metadata
        processed_at = datetime.now(timezone.utc).isoformat()
        for cell in cells:
            cell["processed_at"] = processed_at
            cell["city"] = self.city

        self._grid_cache = cells
        self._cache_time = now
        logger.info(f"  Grid ready: {len(cells)} cells")
        return cells

    def get_status(self) -> Dict:
        """Return the status of all data sources."""
        return {
            "city": self.city,
            "grid_cells": len(self._grid_cache) if self._grid_cache else 0,
            "sources": self.source_status,
            "data_sources_info": DATA_SOURCES,
            "has_real_data": any(
                not v.get("is_demo", True) for v in self.source_status.values()
            ),
            "demo_mode_active": all(
                v.get("is_demo", True) for v in self.source_status.values()
            ),
        }

    def get_sources_info(self) -> List[Dict]:
        """Return metadata about all data sources used."""
        result = []
        for key, info in DATA_SOURCES.items():
            status = self.source_status.get(key, {})
            result.append({
                **info,
                "status": status.get("status", "not_queried"),
                "is_demo": status.get("is_demo", True),
                "records": status.get("records", 0),
                "acquisition_date": status.get("acquisition_date"),
                "spatial_resolution": status.get("spatial_resolution"),
            })
        return result

    # ------------------------------------------------------------------
    # Grid creation
    # ------------------------------------------------------------------

    def _create_grid(self) -> List[Dict]:
        """Create a spatial grid of cells over the city bounds."""
        south, west, north, east = self.bounds
        spacing = self.config["grid_spacing_deg"]

        cells = []
        lat = south
        row = 0
        while lat < north:
            lon = west
            col = 0
            while lon < east:
                cell_id = f"G{row}_{col}"
                center_lat = round(lat + spacing / 2, 6)
                center_lon = round(lon + spacing / 2, 6)
                cells.append({
                    "grid_id": cell_id,
                    "latitude": center_lat,
                    "longitude": center_lon,
                    "bbox": [lon, lat, lon + spacing, lat + spacing],
                    "area_km2": round(
                        spacing * 111 * spacing * 111 * math.cos(math.radians(center_lat)), 3
                    ),
                })
                lon = round(lon + spacing, 6)
                col += 1
            lat = round(lat + spacing, 6)
            row += 1

        return cells

    # ------------------------------------------------------------------
    # OSM data ingestion
    # ------------------------------------------------------------------

    def _fetch_osm_data(self) -> Dict:
        """Attempt to fetch OSM buildings, roads, and water via Overpass."""
        south, west, north, east = self.bounds
        bbox = f"{south},{west},{north},{east}"
        overpass_url = "https://overpass-api.de/api/interpreter"

        queries = {
            "buildings": f"""
                [out:json][timeout:60];
                way["building"]({bbox});
                out center;
            """,
            "roads": f"""
                [out:json][timeout:60];
                way["highway"]({bbox});
                out center;
            """,
            "water": f"""
                [out:json][timeout:60];
                (
                  way["natural"="water"]({bbox});
                  way["waterway"]({bbox});
                );
                out center;
            """,
        }

        osm = {}
        for name, query in queries.items():
            try:
                resp = requests.post(
                    overpass_url,
                    data={"data": query},
                    timeout=60,
                    headers={"User-Agent": "CoolRoute-UHI-Research/1.0"},
                )
                resp.raise_for_status()
                data = resp.json()
                elements = data.get("elements", [])
                osm[name] = elements
                self.source_status[f"osm_{name}"] = {
                    "status": "ok",
                    "is_demo": False,
                    "records": len(elements),
                    "acquisition_date": datetime.now(timezone.utc).date().isoformat(),
                    "spatial_resolution": "vector",
                    "source": "OpenStreetMap via Overpass API",
                }
                logger.info(f"  OSM {name}: {len(elements)} elements")
            except Exception as e:
                logger.warning(f"  OSM {name} fetch failed: {e}. Using demo.")
                osm[name] = []
                self.source_status[f"osm_{name}"] = {
                    "status": "demo",
                    "is_demo": True,
                    "records": 0,
                    "error": str(e),
                }

        return osm

    # ------------------------------------------------------------------
    # Feature engineering
    # ------------------------------------------------------------------

    def _compute_features(self, cells: List[Dict], osm_data: Dict) -> List[Dict]:
        """
        Compute all features per grid cell.
        Uses OSM data when available; synthetic estimates when not.
        """
        buildings = osm_data.get("buildings", [])
        roads = osm_data.get("roads", [])
        water = osm_data.get("water", [])

        has_real_osm = bool(buildings or roads)

        # Pre-compute water centroids for distance calculations
        water_points = []
        for w in water:
            c = w.get("center", {})
            if c:
                water_points.append((c.get("lat", 0), c.get("lon", 0)))

        result = []
        center_lat, center_lon = self.config["center"]

        for cell in cells:
            lat, lon = cell["latitude"], cell["longitude"]
            bbox = cell["bbox"]

            # Distance from city center (normalized)
            center_dist = math.sqrt((lat - center_lat) ** 2 + (lon - center_lon) ** 2)
            center_norm = min(1.0, center_dist / 0.1)  # 0=center, 1=periphery

            if has_real_osm:
                bd = self._building_density_from_osm(bbox, buildings)
                rd = self._road_density_from_osm(bbox, roads)
                dw = self._distance_to_water(lat, lon, water_points)
                osm_is_demo = False
            else:
                # Synthetic estimate: dense center, sparse periphery
                bd = max(0.02, min(0.95, 0.9 - center_norm * 0.7 + self._cell_noise(lat, lon, "bd") * 0.1))
                rd = max(0.0, min(25.0, bd * 14.0 + self._cell_noise(lat, lon, "rd") * 2.0))
                dw = max(100.0, self._cell_noise(lat, lon, "dw") * 2000 + 1000)
                osm_is_demo = True

            # Population: WorldPop-inspired estimate (higher density near center)
            pop_base = self.config["population_grid_km2_estimate"]
            pop = max(500, min(65000, pop_base * (1 - center_norm * 0.6) + self._cell_noise(lat, lon, "pop") * 5000))

            # Income: inverse correlation with building density (simplified proxy)
            income = max(1.0, min(10.0, 10.0 - bd * 6.0 + self._cell_noise(lat, lon, "inc") * 1.5))

            # Elevation: Chennai is flat coastal, ~5–30m
            elevation = max(2.0, min(40.0, 12.0 + self._cell_noise(lat, lon, "elev") * 8.0))

            # Tree cover: inverse of building density
            tree_cover = max(0.01, min(0.45, 0.35 - bd * 0.28 + self._cell_noise(lat, lon, "tc") * 0.04))

            features = {
                **cell,
                "building_density": round(bd, 4),
                "road_density": round(rd, 2),
                "population_density": int(pop),
                "distance_to_water": round(dw, 1),
                "elevation": round(elevation, 1),
                "income_index": round(income, 1),
                "existing_tree_cover": round(tree_cover, 4),
                # NDVI and albedo will be added by satellite service
                "ndvi": None,
                "albedo": None,
                "lst_estimated_c": None,
                "osm_is_demo": osm_is_demo,
                "population_is_demo": True,  # WorldPop integration stub
                "data_sources": {
                    "buildings": "OSM (real)" if not osm_is_demo else "DEMO",
                    "roads": "OSM (real)" if not osm_is_demo else "DEMO",
                    "water": "OSM (real)" if not osm_is_demo else "DEMO",
                    "population": "DEMO (WorldPop model estimate)",
                    "ndvi": "DEMO (pending satellite)",
                    "lst": "DEMO (pending satellite)",
                },
            }
            result.append(features)

        return result

    def _building_density_from_osm(self, bbox: List[float], buildings: List[Dict]) -> float:
        """Estimate building density from OSM building centroids in bbox."""
        w, s, e, n = bbox[0], bbox[1], bbox[2], bbox[3]
        count = 0
        for b in buildings:
            c = b.get("center", {})
            lat, lon = c.get("lat"), c.get("lon")
            if lat and lon and s <= lat <= n and w <= lon <= e:
                count += 1
        # Normalize: assume max 50 buildings per ~500m cell = density 1.0
        return round(min(1.0, count / 50.0), 4)

    def _road_density_from_osm(self, bbox: List[float], roads: List[Dict]) -> float:
        """Estimate road density (km/km²) from OSM road centroids in bbox."""
        w, s, e, n = bbox[0], bbox[1], bbox[2], bbox[3]
        count = 0
        for r in roads:
            c = r.get("center", {})
            lat, lon = c.get("lat"), c.get("lon")
            if lat and lon and s <= lat <= n and w <= lon <= e:
                count += 1
        # Rough estimate: 1 road segment ≈ 0.2 km/km²
        return round(min(25.0, count * 0.2), 2)

    def _distance_to_water(self, lat: float, lon: float, water_points: List[Tuple]) -> float:
        """Euclidean distance to nearest water point (meters)."""
        if not water_points:
            return 3000.0
        min_dist = min(
            math.sqrt((lat - wp[0]) ** 2 + (lon - wp[1]) ** 2) for wp in water_points
        )
        # Convert degrees to approximate meters (at equator ~111km/deg)
        return round(min_dist * 111000, 1)

    def _cell_noise(self, lat: float, lon: float, key: str) -> float:
        """Deterministic pseudo-noise for a cell (reproducible)."""
        seed = int(abs(lat * 1000 + lon * 100)) % 2**31
        rng = np.random.default_rng(seed + hash(key) % 2**31)
        return float(rng.normal(0, 1))
