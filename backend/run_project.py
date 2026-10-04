#!/usr/bin/env python3
"""
CoolRoute Project Runner
One command to download data, train model, and start everything!
"""

import os
import sys
import subprocess
import time

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   🌡️  CoolRoute — Urban Heat Island Mitigation System              ║
║                                                                      ║
║   Data Science Final Year Project                                    ║
║   3D Visualization • ML Prediction • Equity Optimization • AI Chat   ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

def run_step(step_num, title, command, cwd=None):
    """Run a step with nice formatting"""
    print(f"\n{'='*70}")
    print(f"STEP {step_num}: {title}")
    print('='*70)

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=False,
            text=True
        )
        if result.returncode == 0:
            print(f"\n✅ Step {step_num} completed successfully!")
            return True
        else:
            print(f"\n❌ Step {step_num} failed with code {result.returncode}")
            return False
    except Exception as e:
        print(f"\n❌ Step {step_num} error: {e}")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    print("🔍 Checking Python dependencies...")

    required = ['fastapi', 'uvicorn', 'xgboost', 'sklearn', 'pandas', 'numpy', 'requests']
    missing = []

    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"   ⚠️ Missing packages: {', '.join(missing)}")
        print("   📦 Installing from requirements.txt...")
        subprocess.run("pip install -r requirements.txt", shell=True)
    else:
        print("   ✓ All dependencies installed!")

def main():
    print_banner()

    # Get project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)

    print("📁 Project directory:", project_root)

    # Step 0: Check dependencies
    check_dependencies()

    # Step 1: Create directories
    print("\n📂 Creating project directories...")
    os.makedirs('data', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    print("   ✓ data/")
    print("   ✓ models/")

    # Step 2: Download datasets
    print("\n📡 Step 1: Downloading datasets...")
    from data_downloader import download_all_datasets
    download_all_datasets(city="Chennai")

    # Step 3: Train model
    print("\n🤖 Step 2: Training XGBoost model...")
    from model_train import train_and_evaluate
    model, report = train_and_evaluate()

    # Step 4: Show results
    print("\n" + "="*70)
    print("📊 MODEL TRAINING RESULTS")
    print("="*70)
    metrics = report['metrics']
    print(f"   Mean Absolute Error:     {metrics['mae_celsius']:.3f}°C")
    print(f"   Root Mean Square Error:  {metrics['rmse_celsius']:.3f}°C")
    print(f"   R² Score:                {metrics['r2_score']:.4f}")
    print(f"   Cross-Validation MAE:    {metrics['cv_mae_mean']:.3f}°C")
    print(f"   Mean Absolute % Error:   {metrics['mape_percent']:.2f}%")

    print("\n📁 Generated files:")
    for f in ['models/heat_predictor.json', 'models/evaluation_report.json', 
              'models/accuracy_plot.png', 'data/chennai_features.csv']:
        if os.path.exists(f):
            size = os.path.getsize(f)
            print(f"   ✓ {f} ({size:,} bytes)")

    # Step 5: Start backend server
    print("\n" + "="*70)
    print("🚀 Step 3: Starting Backend Server")
    print("="*70)
    print("   API will be available at: http://localhost:8000")
    print("   API docs at: http://localhost:8000/docs")
    print("   Press Ctrl+C to stop")
    print("="*70 + "\n")

    time.sleep(2)

    # Start the server
    subprocess.run("python main.py", shell=True)

if __name__ == "__main__":
    main()
