"""
CoolRoute XGBoost Heat Prediction Model
Trains, evaluates, and saves model in human-readable JSON format.

IMPORTANT: This model is trained on SYNTHETIC/DEMO data generated from
urban morphology patterns. Metrics reflect model fit to synthetic data,
NOT real satellite LST measurements. Configure GEE_PROJECT_ID for real data.
"""

import os
import json
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

# Optional SHAP
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("   ℹ️  SHAP not installed. Install with: pip install shap")

# Feature names (human-readable)
FEATURE_NAMES = [
    'ndvi',                    # Normalized Difference Vegetation Index
    'building_density',        # Building coverage ratio (0-1)
    'road_density',           # Road length per km²
    'population_density',     # People per km²
    'distance_to_water',      # Meters to nearest water body
    'elevation',              # Meters above sea level
    'albedo',                 # Surface reflectivity (0-1)
    'income_index',           # Socio-economic level (1-10)
    'existing_tree_cover'     # Tree canopy percentage (0-1)
]

def load_data(data_path='data/chennai_features.csv'):
    """Load training data"""
    print("📂 Loading training data...")

    if not os.path.exists(data_path):
        print(f"   ⚠️ {data_path} not found. Generating synthetic data...")
        from data_downloader import generate_synthetic_city_data
        df = generate_synthetic_city_data(save=True)
    else:
        df = pd.read_csv(data_path)
        print(f"   ✓ Loaded {len(df)} records from {data_path}")

    return df

def train_and_evaluate(data_path='data/chennai_features.csv', test_size=0.2):
    """
    Train XGBoost model with full evaluation
    Saves model as human-readable JSON (not binary!)
    """
    print("=" * 70)
    print("🤖 CoolRoute Model Training Pipeline")
    print("=" * 70)

    # 1. Load data
    df = load_data(data_path)

    # 2. Prepare features and target
    X = df[FEATURE_NAMES]
    y = df['land_surface_temperature']

    print(f"\n📊 Dataset:")
    print(f"   • Total samples: {len(df)}")
    print(f"   • Features: {len(FEATURE_NAMES)}")
    print(f"   • Target: land_surface_temperature")
    print(f"   • Temp range: {y.min():.1f}°C - {y.max():.1f}°C")
    print(f"   • Temp mean: {y.mean():.1f}°C ± {y.std():.1f}°C")

    # 3. Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, shuffle=True
    )

    print(f"\n✂️ Train/Test Split:")
    print(f"   • Training: {len(X_train)} samples ({(1-test_size)*100:.0f}%)")
    print(f"   • Testing: {len(X_test)} samples ({test_size*100:.0f}%)")

    # 4. Train model
    print("\n🔧 Training XGBoost Regressor...")
    print("   • Algorithm: Gradient Boosted Trees")
    print("   • Estimators: 500")
    print("   • Max Depth: 8")
    print("   • Learning Rate: 0.05")

    model = xgb.XGBRegressor(
        n_estimators=500,
        max_depth=8,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=-1,  # Use all CPU cores
        objective='reg:squarederror'
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False
    )

    print("   ✓ Training complete!")

    # 5. Evaluate on test set
    print("\n📈 Test Set Evaluation:")
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    # Mean Absolute Percentage Error
    mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100

    print(f"   • Mean Absolute Error (MAE): {mae:.3f}°C")
    print(f"   • Root Mean Square Error (RMSE): {rmse:.3f}°C")
    print(f"   • R² Score: {r2:.4f} ({r2*100:.1f}% variance explained)")
    print(f"   • Mean Absolute % Error (MAPE): {mape:.2f}%")

    # 6. Cross-validation
    print("\n🔄 5-Fold Cross-Validation:")
    kfold = KFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X, y, cv=kfold, scoring='neg_mean_absolute_error')
    cv_mae = -cv_scores  # Convert back to positive

    print(f"   • CV MAE: {cv_mae.mean():.3f}°C ± {cv_mae.std():.3f}°C")
    print(f"   • Fold scores: {[f"{s:.3f}°C" for s in cv_mae]}")

    # 7. Feature Importance
    print("\n🔥 Feature Importance (Gain-based):")
    importance = model.feature_importances_
    feature_importance = list(zip(FEATURE_NAMES, importance))
    feature_importance.sort(key=lambda x: x[1], reverse=True)

    for feat, imp in feature_importance:
        bar = "█" * int(imp * 50)
        print(f"   • {feat:25s}: {imp:.4f} {bar}")

    # 8. Save model as HUMAN-READABLE JSON (not binary!)
    os.makedirs('models', exist_ok=True)

    # Save as JSON (text format - you can open and read it!)
    json_path = 'models/heat_predictor.json'
    model.save_model(json_path)
    print(f"\n💾 Model saved as JSON (human-readable):")
    print(f"   • Path: {json_path}")

    # Verify it's readable
    with open(json_path, 'r') as f:
        model_json = json.load(f)
    print(f"   • File size: {os.path.getsize(json_path):,} bytes")
    print(f"   • Trees in model: {len(model_json.get('learner', {}).get('gradient_booster', {}).get('model', {}).get('trees', []))}")
    print(f"   • Format: UTF-8 JSON text (open in any text editor!)")

    # Also save feature names for later use
    with open('models/feature_names.json', 'w') as f:
        json.dump(FEATURE_NAMES, f, indent=2)

    # Save evaluation report
    report = {
        "model_type": "XGBoost Regressor",
        "training_date": pd.Timestamp.now().isoformat(),
        "dataset": {
            "total_samples": int(len(df)),
            "train_samples": int(len(X_train)),
            "test_samples": int(len(X_test)),
            "features": FEATURE_NAMES
        },
        "hyperparameters": {
            "n_estimators": 500,
            "max_depth": 8,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8
        },
        "metrics": {
            "mae_celsius": round(mae, 4),
            "rmse_celsius": round(rmse, 4),
            "r2_score": round(r2, 4),
            "mape_percent": round(mape, 2),
            "cv_mae_mean": round(cv_mae.mean(), 4),
            "cv_mae_std": round(cv_mae.std(), 4)
        },
        "feature_importance": {
            feat: round(imp, 4) for feat, imp in feature_importance
        }
    }

    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            import numpy as np
            if isinstance(obj, (np.floating, np.float32, np.float64)):
                return float(obj)
            if isinstance(obj, (np.integer,)):
                return int(obj)
            return super().default(obj)

    report["training_data_note"] = (
        "DEMO/SYNTHETIC: Model trained on synthetic data based on urban morphology patterns. "
        "Metrics reflect fit to synthetic data, NOT real satellite LST. "
        "Configure GEE_PROJECT_ID env variable to enable real Sentinel-2/Landsat data."
    )

    with open('models/evaluation_report.json', 'w') as f:
        json.dump(report, f, indent=2, cls=NumpyEncoder)

    print(f"\n📄 Evaluation report saved: models/evaluation_report.json")

    # 10. SHAP Explainability
    if SHAP_AVAILABLE:
        print("\n🔍 Computing SHAP feature attributions...")
        try:
            explainer = shap.TreeExplainer(model)
            # Use a sample of training data as background
            sample_size = min(100, len(X_train))
            X_sample = X_train.sample(sample_size, random_state=42)
            shap_values = explainer.shap_values(X_sample)
            
            # Global SHAP importance (mean absolute SHAP value per feature)
            mean_abs_shap = np.abs(shap_values).mean(axis=0)
            total = float(mean_abs_shap.sum()) or 1.0
            shap_importances = [
                {
                    "feature": feat,
                    "label": feat.replace('_', ' ').title(),
                    "shap_importance": round(float(v), 6),
                    "percentage": round(float(v) / total * 100, 1),
                    "direction": (
                        "reduces_heat" if feat in ("ndvi", "existing_tree_cover", "elevation")
                        else "increases_heat"
                    ),
                }
                for feat, v in sorted(
                    zip(FEATURE_NAMES, mean_abs_shap),
                    key=lambda x: x[1], reverse=True
                )
            ]

            shap_report = {
                "feature_importances": shap_importances,
                "method": "SHAP TreeExplainer (mean absolute SHAP values)",
                "background_samples": sample_size,
                "base_value": round(float(explainer.expected_value), 4),
                "is_demo": False,
                "computed_at": pd.Timestamp.now().isoformat(),
            }
            with open('models/shap_values.json', 'w') as f:
                json.dump(shap_report, f, indent=2)
            print("   ✓ SHAP values saved: models/shap_values.json")
            print("   SHAP Global Feature Importance:")
            for item in shap_importances:
                bar = '█' * int(item['percentage'] / 2)
                print(f"   • {item['feature']:25s}: {item['percentage']:5.1f}% {bar}")
        except Exception as e:
            print(f"   ⚠️ SHAP computation failed: {e}")
    else:
        print("\n   ℹ️ SHAP not available — skipping SHAP computation")

    # 9. Generate prediction vs actual plot
    print("\n📊 Generating accuracy visualization...")
    plt.figure(figsize=(12, 5))

    # Plot 1: Predicted vs Actual
    plt.subplot(1, 2, 1)
    plt.scatter(y_test, y_pred, alpha=0.5, c='#00f0ff', s=20)
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2, label='Perfect Prediction')
    plt.xlabel('Actual Temperature (°C)', fontsize=12)
    plt.ylabel('Predicted Temperature (°C)', fontsize=12)
    plt.title(f'Predicted vs Actual\nMAE = {mae:.3f}°C, R² = {r2:.3f}', fontsize=14)
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Plot 2: Feature Importance
    plt.subplot(1, 2, 2)
    feats = [f[0] for f in feature_importance]
    imps = [f[1] for f in feature_importance]
    colors = ['#ff006e', '#ffb703', '#00f0ff', '#00ff88', '#a855f7', '#f472b6', '#60a5fa', '#fbbf24', '#34d399']
    plt.barh(feats, imps, color=colors[:len(feats)])
    plt.xlabel('Importance Score', fontsize=12)
    plt.title('Feature Importance (XGBoost)', fontsize=14)
    plt.gca().invert_yaxis()
    plt.grid(True, alpha=0.3, axis='x')

    plt.tight_layout()
    plt.savefig('models/accuracy_plot.png', dpi=150, bbox_inches='tight')
    print("   ✓ Saved: models/accuracy_plot.png")
    plt.close()

    # 10. Sample predictions
    print("\n🎯 Sample Predictions:")
    sample_indices = np.random.choice(len(X_test), 5, replace=False)
    for idx in sample_indices:
        actual = y_test.iloc[idx]
        predicted = y_pred[idx]
        error = abs(actual - predicted)
        print(f"   • Actual: {actual:.2f}°C | Predicted: {predicted:.2f}°C | Error: {error:.2f}°C")

    print("\n" + "=" * 70)
    print("✅ Model Training Complete!")
    print("=" * 70)
    print("\n📁 Output Files:")
    print("   • models/heat_predictor.json — Model (human-readable JSON)")
    print("   • models/feature_names.json — Feature list")
    print("   • models/evaluation_report.json — Full metrics report")
    print("   • models/accuracy_plot.png — Visualization")

    return model, report

def load_model(model_path='models/heat_predictor.json'):
    """Load trained model from JSON"""
    model = xgb.XGBRegressor()
    model.load_model(model_path)

    with open('models/feature_names.json', 'r') as f:
        features = json.load(f)

    return model, features

def predict_single(model, features_dict):
    """Make a single prediction"""
    df = pd.DataFrame([features_dict])
    prediction = model.predict(df)[0]
    return prediction

if __name__ == "__main__":
    model, report = train_and_evaluate()

    # Demo: Load and predict
    print("\n🧪 Testing model reload and prediction...")
    loaded_model, feature_names = load_model()

    sample_input = {
        'ndvi': 0.15,
        'building_density': 0.85,
        'road_density': 18.5,
        'population_density': 45000,
        'distance_to_water': 2500,
        'elevation': 12.0,
        'albedo': 0.35,
        'income_index': 3.0,
        'existing_tree_cover': 0.05
    }

    pred = predict_single(loaded_model, sample_input)
    print(f"\n📍 Sample Input (High-density urban zone):")
    for k, v in sample_input.items():
        print(f"   • {k}: {v}")
    print(f"\n🔮 Predicted Temperature: {pred:.2f}°C")
