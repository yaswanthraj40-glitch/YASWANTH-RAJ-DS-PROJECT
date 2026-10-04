# CoolRoute — Urban Heat Island Mitigation System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB.svg)](https://react.dev)
[![XGBoost](https://img.shields.io/badge/ML-XGBoost-EB5424.svg)](https://xgboost.readthedocs.io)
[![SHAP](https://img.shields.io/badge/Explainability-SHAP-00f0ff.svg)](https://shap.readthedocs.io)

An AI-driven decision-support platform designed for urban city planners and climate researchers to map urban heat islands (UHI), explain thermal severity drivers via SHAP, simulate diurnal heat trajectories, and generate equity-weighted tree planting optimization interventions with defensible cooling simulations.

---

## Table of Contents
1. [Problem Statement](#1-problem-statement)
2. [Solution Architecture](#2-solution-architecture)
3. [End-to-End System Pipeline](#3-end-to-end-system-pipeline)
4. [Data Sources & Data Ingestion Pipeline](#4-data-sources--data-ingestion-pipeline)
5. [ML Methodology & Feature Engineering](#5-ml-methodology--feature-engineering)
6. [XGBoost Heat Prediction Model](#6-xgboost-heat-prediction-model)
7. [Model Performance & Evaluation Metrics](#7-model-performance--evaluation-metrics)
8. [SHAP Explainability Engine](#8-shap-explainability-engine)
9. [3D Heat Mapping & Spatial Analysis](#9-3d-heat-mapping--spatial-analysis)
10. [Temporal & Diurnal Analysis](#10-temporal--diurnal-analysis)
11. [Tree Planting Optimization Algorithm](#11-tree-planting-optimization-algorithm)
12. [Equity & Socio-Demographic Strategy](#12-equity--socio-demographic-strategy)
13. [Before / After Intervention Simulation](#13-before--after-intervention-simulation)
14. [REST API Documentation](#14-rest-api-documentation)
15. [Installation & Setup Guide](#15-installation--setup-guide)
16. [Demo Mode & Data Provenance Policy](#16-demo-mode--data-provenance-policy)
17. [Known Limitations](#17-known-limitations)
18. [Future Roadmap](#18-future-roadmap)

---

## 1. Problem Statement
Rapid urbanization and replacement of natural vegetation with asphalt and dense concrete create **Urban Heat Islands (UHI)**, where surface temperatures in metropolitan zones are 3–10°C hotter than surrounding rural environs. High-density coastal and tropical cities (e.g., Chennai, India) face severe summer land surface temperatures (LST) exceeding 48°C, disproportionately harming vulnerable low-income wards with minimal green canopy coverage, triggering heat distress, elevated air-conditioning electricity demand, and public health crises.

---

## 2. Solution Architecture

CoolRoute unifies satellite remote sensing indices, OpenStreetMap spatial infrastructure, real-time Open-Meteo meteorological feeds, and socioeconomic data into an interactive 3D spatial decision-support platform:

```
              REAL-WORLD DATA SOURCES
   (Sentinel-2, Landsat, OpenStreetMap, Open-Meteo, WorldPop)
                         │
                         ▼
             DATA PROCESSING PIPELINE
   (Validation → Cleaning → Spatial Join → Feature Engineering)
                         │
                         ▼
             GRID CELLS (ML DATASET)
  (Lat, Lon, NDVI, Building Density, Road Density, Pop Density, Albedo)
                         │
                         ▼
            TRAINED XGBOOST REGRESSOR
          (Predicts Land Surface Temp)
                         │
                         ▼
            SHAP EXPLAINABILITY ENGINE
         ("Why is this specific area hot?")
                         │
                         ▼
             HOTSPOT SEVERITY CLASSIFIER
           (LOW, MODERATE, HIGH, EXTREME)
                         │
        ┌────────────────┴────────────────┐
        ▼                                 ▼
TEMPORAL ANALYSIS                 OPTIMIZATION ENGINE
(Hourly Diurnal Curve via      (Transparent Equity-Weighted
Open-Meteo Air Temp + UHI)     Multi-Objective Solver)
        │                                 │
        └────────────────┬────────────────┘
                         ▼
             BEFORE / AFTER SIMULATION
       (Updated NDVI & Tree Cover ML Inference)
                         │
                         ▼
            INTERACTIVE 3D DASHBOARD
           (Mapbox GL + Three.js + Recharts)
```

---

## 3. End-to-End System Pipeline

```
Raw Data Ingestion → Spatial Grid Partitioning → Feature Vector Assembly
  → Model Inference (LST) → SHAP Attribution → Hotspot Risk Tagging
  → Configurable Tree Optimization → Before/After Delta Simulation → 3D Visualization
```

---

## 4. Data Sources & Data Ingestion Pipeline

| Dataset | Provider | Spatial Resolution | License | Mode Status |
|---|---|---|---|---|
| **Air Temperature & Diurnal Weather** | Open-Meteo API | Point/Hourly | CC BY 4.0 | **REAL DATA (Live)** |
| **Building Footprints** | OpenStreetMap (Overpass API) | Vector Polygons | ODbL | **REAL / Fallback Demo** |
| **Road Network** | OpenStreetMap (Overpass API) | Vector Lines | ODbL | **REAL / Fallback Demo** |
| **Water Bodies** | OpenStreetMap (Overpass API) | Vector Polygons | ODbL | **REAL / Fallback Demo** |
| **NDVI Vegetation Index** | Sentinel-2 (GEE Connector) | 10m | Open Access | **DEMO MODE (Simulated)** |
| **Land Surface Temp (LST)** | Landsat 8/9 Thermal Band 10 | 30m / 100m | USGS Open | **DEMO MODE (Simulated)** |
| **Population Density** | WorldPop / Census of India | 100m Grid | CC BY 4.0 | **DEMO MODE (Model Estimate)** |

### Data Processing Steps:
1. **Validation & Filtering**: Bounding box spatial clipping for Chennai metropolitan region (`13.00°N–13.15°N, 80.20°E–80.35°E`).
2. **Coordinate Transformation**: Reprojection to EPSG:4326 grid cells (~500m × 500m).
3. **Spatial Aggregation**: Polygon-in-cell joins to compute building density (0–1) and road density (km/km²).
4. **Euclidean Distance Fields**: Minimum distance calculation from cell centroid to nearest water body.

---

## 5. ML Methodology & Feature Engineering

Each spatial grid cell is characterized by 9 features:
1. `ndvi`: Normalized Difference Vegetation Index ($-1.0$ to $+1.0$)
2. `building_density`: Built-up fraction within the cell ($0.0$ to $1.0$)
3. `road_density`: Total road length per square kilometer ($0$ to $25\text{ km/km}^2$)
4. `population_density`: Resident population exposure ($\text{people/km}^2$)
5. `distance_to_water`: Euclidean distance to nearest ocean/river/lake (meters)
6. `elevation`: Topographic height above sea level (meters)
7. `albedo`: Surface solar reflectance index ($0.10$ to $0.50$)
8. `income_index`: Socioeconomic level proxy ($1$ to $10$, lower = more vulnerable)
9. `existing_tree_cover`: Current canopy coverage percentage ($0.0$ to $0.50$)

**Target Variable**: `land_surface_temperature` (LST in °C).

---

## 6. XGBoost Heat Prediction Model

- **Algorithm**: Extreme Gradient Boosted Trees (`xgboost.XGBRegressor`)
- **Objective**: `reg:squarederror`
- **Hyperparameters**:
  - `n_estimators`: 500
  - `max_depth`: 8
  - `learning_rate`: 0.05
  - `subsample`: 0.8
  - `colsample_bytree`: 0.8
  - `reg_alpha`: 0.1, `reg_lambda`: 1.0
- **Storage Format**: Saved as UTF-8 human-readable JSON (`models/heat_predictor.json`).

---

## 7. Model Performance & Evaluation Metrics

> *Metrics computed on test split and 5-Fold Cross Validation:*

- **Mean Absolute Error (MAE)**: `0.929°C`
- **Root Mean Squared Error (RMSE)**: `1.183°C`
- **$R^2$ Score**: `0.948` (94.8% variance explained)
- **Mean Absolute Percentage Error (MAPE)**: `2.32%`
- **5-Fold Cross-Validation MAE**: `1.022°C ± 0.104°C`

*(Note: In demo mode, these metrics validate model convergence on synthetic morphology training datasets. When connected to GEE credentials, metrics reflect real satellite calibration).*

---

## 8. SHAP Explainability Engine

To eliminate "black box" ML behavior, CoolRoute integrates **SHAP (SHapley Additive exPlanations)** TreeExplainer. For any selected hotspot, the model returns exact percentage contributions:

```
Why is this zone hot? (e.g. Zone 23: 46.8°C)
├─ Building Density (+42.1%) ────── High thermal mass & heat retention
├─ Low NDVI / Lack of Trees (+31.4%) ── Reduced evapotranspiration cooling
├─ Road Density (+14.8%) ────────── High asphalt dark pavement absorption
└─ Low Surface Albedo (+8.2%) ───── High solar radiation absorption
```

---

## 9. 3D Heat Mapping & Spatial Analysis

- **Map Engine**: Mapbox GL JS with 3D polygon fill extrusions and building extrusions.
- **Categorical Risk Scale**:
  - `LOW (<38°C)`: 🟢 `#00ff88` (Green)
  - `MODERATE (38–42°C)`: 🟡 `#ffb703` (Yellow)
  - `HIGH (43–45°C)`: 🟠 `#ff006e` (Orange/Pink)
  - `EXTREME (>46°C)`: 🔴 `#ff0000` (Red)
- **Toggleable Visual Metrics**: Switch effortlessly between LST Heat, NDVI Vegetation, Population Density, and Tree Cover Deficit.

---

## 10. Temporal & Diurnal Analysis

Heat severity fluctuates significantly throughout the day:
- **Morning (06:00–10:00)**: ~28–33°C (baseline solar heating)
- **Noon (10:00–14:00)**: ~38–42°C (peak solar radiation)
- **Afternoon (14:00–18:00)**: ~41–47°C (peak urban heat island storage release)
- **Evening (18:00–22:00)**: ~33–36°C (slow radiative cooling)

CoolRoute pulls live hourly temperature from **Open-Meteo** and applies calibrated UHI offset models to provide hourly urban temperature curves.

---

## 11. Tree Planting Optimization Algorithm

### Objective Function:
$$\text{Priority Score} = w_1 \cdot \text{HeatSeverity} + w_2 \cdot \text{PopExposure} + w_3 \cdot \text{Vulnerability} + w_4 \cdot \text{TreeDeficit} + w_5 \cdot \text{CoolingPotential}$$

- **Configurable Constraints**:
  - Total Financial Budget (INR ₹)
  - Maximum plantable canopy space per zone
  - Minimum and maximum trees per neighborhood
- **Species Database**:
  - **Neem**: ₹500/tree, 0.08°C cooling/tree, fast growth, drought-tolerant.
  - **Peepal**: ₹600/tree, 0.10°C cooling/tree, medium growth, dense shade.
  - **Banyan**: ₹800/tree, 0.12°C cooling/tree, slow growth, maximum cooling.
  - **Gulmohar**: ₹350/tree, 0.06°C cooling/tree, fast growth, aesthetic shade.

---

## 12. Equity & Socio-Demographic Strategy

Conventional urban greening often favors affluent neighborhoods. CoolRoute enforces an **Equity Priority Slider**:
- Increasing equity weighting prioritizes zones with income index $< 4/10$ and temperature $> 43^\circ\text{C}$.
- Low-income neighborhoods receive up to **40% higher weight** in tree allocation.

---

## 13. Before / After Intervention Simulation

Rather than applying a hardcoded temperature subtraction, CoolRoute re-executes ML inference with post-intervention feature values ($\text{NDVI}_{\text{new}}$ and $\text{TreeCover}_{\text{new}}$):

$$\Delta \text{Canopy} = N_{\text{trees}} \times \text{CanopyArea}_{\text{species}}$$
$$\text{NDVI}_{\text{after}} = \text{NDVI}_{\text{before}} + \Delta \text{CanopyFraction} \times 0.5$$

- Displays side-by-side split screen on 3D building models.
- All values are explicitly labeled **ESTIMATED** with citations to urban forestry microclimate research (Bowler et al. 2010, Zupancic et al. 2015).

---

## 14. REST API Documentation

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/data/status` | Ingestion status & real vs demo mode indicator |
| `GET` | `/api/data/sources` | Metadata, spatial resolution, and citations |
| `GET` | `/api/heat-map` | GeoJSON FeatureCollection of 3D heat zones |
| `POST` | `/api/predict-heat` | XGBoost prediction + SHAP explanation |
| `GET` | `/api/heat/{lat}/{lng}` | Coordinate heat prediction & local SHAP |
| `GET` | `/api/heat/timeseries` | Diurnal temperature curve (Open-Meteo) |
| `GET` | `/api/model/metrics` | Actual MAE, RMSE, $R^2$, CV scores from trained model |
| `GET` | `/api/model/importance` | SHAP and gain-based feature importances |
| `GET` | `/api/model/explain/{zone_id}` | Per-zone "Why is this area hot?" attribution |
| `POST` | `/api/optimization` | Solves equity-weighted planting plan |
| `POST` | `/api/impact/simulation` | Re-runs ML inference for before/after delta |
| `GET` | `/api/ward-stats` | Aggregated zone statistics |
| `GET` | `/api/impact-summary` | City-wide population at risk & cooling benefits |

---

## 15. Installation & Setup Guide

### Prerequisites:
- Python 3.10+
- Node.js 18+ & npm

### Backend Setup:
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt

# Train model & compute SHAP values:
python model_train.py

# Start FastAPI server:
python main.py
```
*Backend runs on `http://localhost:8000`*

### Frontend Setup:
```bash
cd frontend
npm install
npm run dev
```
*Frontend runs on `http://localhost:5173`*

---

## 16. Demo Mode & Data Provenance Policy

CoolRoute operates under strict academic and hackathon integrity guidelines:
- **Real Data**: Open-Meteo live hourly air temperatures, Overpass API OpenStreetMap vectors.
- **Demo Mode**: When Google Earth Engine API credentials are not supplied, satellite NDVI and thermal LST are synthesized based on urban morphology patterns and labeled with `DEMO DATA — NOT REAL-TIME`.
- **Estimates**: Carbon sequestration, energy savings, and cooling degrees are tagged with `ESTIMATED` accompanied by scientific literature assumptions.

---

## 17. Known Limitations
1. **Thermal Satellite Latency**: Real-world Landsat 8/9 thermal passes have an 8-to-16-day revisit rate; real-time LST relies on weather interpolation between satellite overpasses.
2. **Canopy Growth Lag**: Real trees require 3–5 years to achieve full cooling canopy; models project maturity benefits.
3. **Mapbox Public Token**: Requires a user-provided Mapbox token for private custom styling in production (`VITE_MAPBOX_TOKEN`).

---

## 18. Future Roadmap
- Google Earth Engine automatic OAuth2 ingestion pipeline.
- High-resolution LiDAR tree canopy height dataset integration.
- Mobile thermal crowd-sourcing app for citizen science validation.
