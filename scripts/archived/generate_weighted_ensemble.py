#!/usr/bin/env python3
"""
Generate weighted ensemble predictions using R² scores from the ML models
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, AdaBoostRegressor
from sklearn.linear_model import LinearRegression, Lasso
from tensorflow import keras
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# MODEL R² SCORES from notebook (Cell 55 - final evaluation)
# ============================================================================
r2_scores = {
    'Random Forest': 0.7753,
    'AdaBoost': 0.7697,
    'Gradient Boosting': 0.7626,
    'Stepwise Regression': 0.7588,
    # Excluded:
    # - Deep Learning: -1.2717 (worse than mean)
    # - Linear Regression: 0.7588 (duplicate with Stepwise which includes feature selection)
}

# Filter out models with R² < 0.5 (quality threshold)
min_r2_threshold = 0.5
viable_models = {m: r for m, r in r2_scores.items() if r >= min_r2_threshold}
print(f"✓ Using {len(viable_models)} viable models (R² ≥ {min_r2_threshold}, Linear Regression excluded):")
for model, r2 in viable_models.items():
    print(f"  - {model}: R² = {r2:.4f}")

# Calculate weights (normalized R² scores)
total_r2 = sum(viable_models.values())
weights = {m: r / total_r2 for m, r in viable_models.items()}
print(f"\n✓ Calculated weights (sum = {sum(weights.values()):.4f}):")
for model, w in weights.items():
    print(f"  - {model}: {w:.4f}")

# ============================================================================
# LOAD DATA AND RETRAIN MODELS
# ============================================================================
print("\n" + "="*60)
print("Loading and training models...")
print("="*60)

# Load training data
df_train = pd.read_excel('database/20251207_db01.xlsx', sheet_name='train_sbn')
df_predict = pd.read_excel('database/20251207_db01.xlsx', sheet_name='predict_sbn')

# Feature selection (from notebook)
features = ['number_series', 'dpk_bio_log', 'move', 'auction_month', 'long_holiday', 'inflation_rate']
target = 'incoming_bio_log'

X_train = df_train[features].copy()
y_train = df_train[target].copy()
X_predict = df_predict[features].copy()

# Standardize features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_predict_scaled = scaler.transform(X_predict)

# Initialize models
models = {
    'Random Forest': RandomForestRegressor(n_estimators=200, max_depth=20, random_state=42),
    'Gradient Boosting': GradientBoostingRegressor(n_estimators=150, learning_rate=0.1, max_depth=5, random_state=42),
    'AdaBoost': AdaBoostRegressor(n_estimators=200, learning_rate=0.1, random_state=42),
    'Stepwise Regression': LinearRegression(),  # Stepwise selection on linear base
}

# Train models and make predictions
predictions = {}
print("\nTraining models...")
for model_name, model in models.items():
    if model_name in viable_models:
        print(f"  Training {model_name}...", end='', flush=True)
        model.fit(X_train_scaled, y_train)
        pred = model.predict(X_predict_scaled)
        predictions[model_name] = pred
        print(f" ✓")

# ============================================================================
# CALCULATE WEIGHTED ENSEMBLE
# ============================================================================
print("\n" + "="*60)
print("Calculating weighted ensemble...")
print("="*60)

ensemble_pred = np.zeros(len(X_predict_scaled))
for model_name, weight in weights.items():
    ensemble_pred += predictions[model_name] * weight
    print(f"  {model_name} ({weight:.4f}): {predictions[model_name][:3]} ...")

print(f"\n✓ Ensemble prediction (weighted average):")
print(f"  {ensemble_pred[:5]} ...")

# ============================================================================
# EXPORT RESULTS
# ============================================================================
print("\n" + "="*60)
print("Exporting results...")
print("="*60)

# Prepare output dataframe
df_export = df_predict[['date', 'auction_month', 'auction_year', 'bi_rate', 
                          'yield01_ibpa', 'yield05_ibpa', 'yield10_ibpa', 
                          'inflation_rate', 'idprod_rate', 'jkse_avg', 'idrusd_avg',
                          'awarded_bio_log', 'incoming_mio_log', 'awarded_mio_log',
                          'number_series', 'bid_to_cover', 'move', 'forh_avg', 'dpk_bio_log']].copy()

# Add weighted ensemble prediction
df_export['incoming_bio_log_ensemble'] = ensemble_pred

# Add individual model predictions (optional, for debugging)
for model_name in predictions.keys():
    df_export[f'incoming_bio_log_{model_name.lower().replace(" ", "_")}'] = predictions[model_name]

# Add human-readable ensemble values
df_export['incoming_billions_ensemble'] = np.exp(ensemble_pred)
df_export['awarded_billions'] = np.exp(df_predict['awarded_bio_log'])

# Format date
df_export['date'] = pd.to_datetime(df_export['date']).dt.strftime('%Y-%m-%d')

# Save to CSV
output_file = 'database/20251224_auction_forecast_ensemble.csv'
df_export.to_csv(output_file, index=False)

print(f"\n✓ Exported {len(df_export)} forecasts to {output_file}")
print(f"  Date range: {df_export['date'].min()} to {df_export['date'].max()}")
print(f"  Columns: {len(df_export.columns)}")
print(f"\nKey columns:")
print(f"  - incoming_bio_log_ensemble: Weighted ensemble prediction (main)")
print(f"  - incoming_billions_ensemble: Ensemble in billions (log-transformed back)")
print(f"  - incoming_bio_log_*: Individual model predictions (for comparison)")
print(f"\n✓ Ensemble calculation complete!")
