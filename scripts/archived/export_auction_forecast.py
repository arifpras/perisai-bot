#!/usr/bin/env python3
"""
Export auction forecasts using weighted ensemble predictions
Generated from 5 ML models with R² scores: RF(0.7753), AdaBoost(0.7697), GB(0.7626), LR(0.7588), SW(0.7588)
Deep Learning (R²=-1.27) excluded for poor performance
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, AdaBoostRegressor
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# MODEL CONFIGURATION
# ============================================================================
# R² scores from final notebook evaluation (Cell 55)
# Note: Linear Regression excluded (similar to Stepwise Regression which includes feature selection)
R2_SCORES = {
    'Random Forest': 0.7753,
    'AdaBoost': 0.7697,
    'Gradient Boosting': 0.7626,
    'Stepwise Regression': 0.7588,
}

# Filter: exclude models with R² < 0.5 (quality threshold)
# Deep Learning had R² = -1.2717 (predicts worse than mean), so it's excluded
VIABLE_MODELS = {m: r for m, r in R2_SCORES.items() if r >= 0.5}

# Calculate weights (normalized R² scores)
TOTAL_R2 = sum(VIABLE_MODELS.values())
WEIGHTS = {m: r / TOTAL_R2 for m, r in VIABLE_MODELS.items()}

print("="*70)
print("WEIGHTED ENSEMBLE CONFIGURATION")
print("="*70)
print(f"✓ Using {len(VIABLE_MODELS)} viable models (excluding Deep Learning: R²=-1.27 and Linear Regression: duplicate with Stepwise)")
print(f"\nModel weights (R² normalized):")
for model, w in sorted(WEIGHTS.items(), key=lambda x: x[1], reverse=True):
    r2 = VIABLE_MODELS[model]
    print(f"  {model:25s} | R²={r2:.4f} | Weight={w:.4f}")

# ============================================================================
# TRAIN MODELS AND GENERATE PREDICTIONS
# ============================================================================
print("\n" + "="*70)
print("TRAINING MODELS")
print("="*70)

# Load training and prediction data
df_train = pd.read_excel('database/20251207_db01.xlsx', sheet_name='train_sbn')
df_predict = pd.read_excel('database/20251207_db01.xlsx', sheet_name='predict_sbn')

# Features used in notebook (Stepwise selection result)
FEATURES = ['number_series', 'dpk_bio_log', 'move', 'auction_month', 'long_holiday', 'inflation_rate']
TARGET = 'incoming_bio_log'

X_train = df_train[FEATURES].copy()
y_train = df_train[TARGET].copy()
X_predict = df_predict[FEATURES].copy()

# Standardize features (required by some models)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_predict_scaled = scaler.transform(X_predict)

# Initialize models with tuned hyperparameters from GridSearchCV
models = {
    'Random Forest': RandomForestRegressor(
        n_estimators=200, max_depth=20, min_samples_split=5, min_samples_leaf=2, random_state=42
    ),
    'Gradient Boosting': GradientBoostingRegressor(
        n_estimators=150, learning_rate=0.1, max_depth=5, subsample=0.8, random_state=42
    ),
    'AdaBoost': AdaBoostRegressor(
        n_estimators=200, learning_rate=0.1, random_state=42
    ),
    'Stepwise Regression': LinearRegression(),  # Stepwise selection on linear base model
}

# Train models and collect predictions
predictions = {}
print("\nTraining models:")
for model_name, model in models.items():
    if model_name in VIABLE_MODELS:
        print(f"  • {model_name:25s}", end='', flush=True)
        model.fit(X_train_scaled, y_train)
        pred = model.predict(X_predict_scaled)
        predictions[model_name] = pred
        print(" ✓")

# ============================================================================
# CALCULATE WEIGHTED ENSEMBLE
# ============================================================================
print("\n" + "="*70)
print("CALCULATING WEIGHTED ENSEMBLE")
print("="*70)

ensemble_predictions = np.zeros(len(X_predict_scaled))
print("\nEnsemble calculation:")
for model_name, weight in sorted(WEIGHTS.items(), key=lambda x: x[1], reverse=True):
    ensemble_predictions += predictions[model_name] * weight
    print(f"  • {model_name:25s} × {weight:.4f}")

# ============================================================================
# PREPARE AND EXPORT DATA
# ============================================================================
print("\n" + "="*70)
print("EXPORTING RESULTS")
print("="*70)

# Select columns for export
columns_to_export = [
    'date',
    'auction_month',
    'auction_year',
    'bi_rate',
    'yield01_ibpa',
    'yield05_ibpa',
    'yield10_ibpa',
    'inflation_rate',
    'idprod_rate',
    'jkse_avg',
    'idrusd_avg',
    'awarded_bio_log',
    'incoming_mio_log',
    'awarded_mio_log',
    'number_series',
    'bid_to_cover',
    'move',
    'forh_avg',
    'dpk_bio_log',
]

df_export = df_predict[columns_to_export].copy()

# Add ensemble prediction (log scale)
df_export['incoming_bio_log'] = ensemble_predictions

# Add human-readable values (inverse log transform)
df_export['incoming_billions'] = np.exp(ensemble_predictions)
df_export['awarded_billions'] = np.exp(df_predict['awarded_bio_log'])
df_export['incoming_millions'] = np.exp(df_predict['incoming_mio_log'])
df_export['awarded_millions'] = np.exp(df_predict['awarded_mio_log'])

# Format date
df_export['date'] = pd.to_datetime(df_export['date']).dt.strftime('%Y-%m-%d')

# Save to CSV
output_file = 'database/20251224_auction_forecast.csv'
df_export.to_csv(output_file, index=False)

print(f"\n✓ Exported {len(df_export)} forecasts to {output_file}")
print(f"  Date range: {df_export['date'].min()} to {df_export['date'].max()}")
print(f"  Columns: {len(df_export.columns)}")
print(f"\nKey columns:")
print(f"  • incoming_bio_log: Weighted ensemble prediction (log scale)")
print(f"  • incoming_billions: Ensemble in billions (human-readable)")
print(f"\n✓ Export complete!")
print("="*70)
