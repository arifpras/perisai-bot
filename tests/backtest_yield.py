#!/usr/bin/env python3
"""
Robust backtesting for yield forecasts using actual position-based indexing.
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from yield_forecast_models import (
    forecast_arima, forecast_ets, forecast_prophet,
    forecast_random_walk, forecast_monte_carlo, forecast_ma5, forecast_var
)

# Load data
df = pd.read_csv('database/20251215_priceyield.csv')
df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y')

print("╔════════════════════════════════════════════════════════════════════╗")
print("║          YIELD FORECAST BACKTEST RESULTS                          ║")
print("╚════════════════════════════════════════════════════════════════════╝")

for tenor in ['05_year', '10_year']:
    print(f"\n📊 {tenor.upper()} TENOR")
    print("=" * 80)
    
    # Get data for this tenor
    tenor_data = df[df['tenor'] == tenor].groupby('date')['yield'].mean().sort_index()
    series = pd.Series(tenor_data)
    
    print(f"✓ {len(series)} observations ({series.index[0].date()} to {series.index[-1].date()})")
    
    # ===== ONE-STEP-AHEAD: Next Position in Series =====
    print(f"\n🎯 ONE-STEP-AHEAD (forecast next position in series)")
    print("-" * 80)
    
    test_window = 30
    train_end = len(series) - test_window
    
    models = {
        'ARIMA(1,1,1)': forecast_arima,
        'ETS': forecast_ets,
        'Prophet': forecast_prophet,
        'Random Walk+Drift': forecast_random_walk,
        'Monte Carlo': forecast_monte_carlo,
        'MA5': forecast_ma5,
        'VAR': forecast_var,
    }
    
    results = {m: {'forecasts': [], 'actuals': []} for m in models}
    
    for i in range(test_window):
        train_idx = train_end + i
        if train_idx + 1 >= len(series):
            break
        
        # Training series (all data up to this point)
        train_series = series[:train_idx + 1]
        
        # Forecast for next date (position-based)
        forecast_date = series.index[train_idx + 1]
        actual_value = series.iloc[train_idx + 1]
        
        # Get forecasts
        for model_name, forecast_fn in models.items():
            try:
                forecast_val = forecast_fn(train_series, forecast_date)
                if isinstance(forecast_val, tuple):
                    forecast_val = forecast_val[0]
                
                results[model_name]['forecasts'].append(float(forecast_val))
                results[model_name]['actuals'].append(float(actual_value))
            except:
                pass
    
    # Calculate and display metrics
    print(f"\n{'Model':<20} {'MAE':<12} {'RMSE':<12} {'MAPE (%)':<12} {'Bias':<12}")
    print("-" * 80)
    
    best_mae = float('inf')
    best_model = None
    
    for model_name in models.keys():
        if len(results[model_name]['forecasts']) >= 5:  # Need at least 5 samples
            forecasts = np.array(results[model_name]['forecasts'])
            actuals = np.array(results[model_name]['actuals'])
            
            errors = actuals - forecasts
            mae = np.mean(np.abs(errors))
            rmse = np.sqrt(np.mean(errors ** 2))
            mape = np.mean(np.abs(errors / actuals) * 100)
            bias = np.mean(errors)
            
            print(f"{model_name:<20} "
                  f"{mae:<12.6f} "
                  f"{rmse:<12.6f} "
                  f"{mape:<12.2f} "
                  f"{bias:<12.6f}")
            
            if mae < best_mae:
                best_mae = mae
                best_model = model_name
    
    if best_model:
        print(f"\n🏆 Best model (lowest MAE): {best_model}")
    
    # ===== MULTI-STEP =====
    print(f"\n📈 MULTI-STEP FORECAST")
    print("-" * 80)
    
    for steps_ahead in [5, 10]:
        print(f"\n  {steps_ahead}-step ahead (approx {steps_ahead} business days):")
        
        test_indices = []
        for idx in range(100, len(series) - steps_ahead, 20):
            test_indices.append(idx)
        
        forecasts_dict = {m: [] for m in ['ARIMA(1,1,1)', 'Random Walk+Drift', 'Monte Carlo']}
        actuals_list = []
        
        for train_idx in test_indices:
            train_series = series[:train_idx + 1]
            test_idx = train_idx + steps_ahead
            
            if test_idx >= len(series):
                break
            
            forecast_date = series.index[test_idx]
            actual_val = series.iloc[test_idx]
            
            try:
                forecasts_dict['ARIMA(1,1,1)'].append(float(forecast_arima(train_series, forecast_date)[0]))
                forecasts_dict['Random Walk+Drift'].append(float(forecast_random_walk(train_series, forecast_date)))
                forecasts_dict['Monte Carlo'].append(float(forecast_monte_carlo(train_series, forecast_date)))
                actuals_list.append(float(actual_val))
            except:
                pass
        
        print(f"  {'Model':<20} {'MAE':<12} {'RMSE':<12} {'MAPE (%)':<12}")
        print("  " + "-" * 76)
        
        for model_name in ['ARIMA(1,1,1)', 'Random Walk+Drift', 'Monte Carlo']:
            if len(forecasts_dict[model_name]) >= 3:
                forecasts = np.array(forecasts_dict[model_name])
                actuals = np.array(actuals_list)
                
                errors = actuals - forecasts
                mae = np.mean(np.abs(errors))
                rmse = np.sqrt(np.mean(errors ** 2))
                mape = np.mean(np.abs(errors / actuals) * 100)
                
                print(f"  {model_name:<20} "
                      f"{mae:<12.6f} "
                      f"{rmse:<12.6f} "
                      f"{mape:<12.2f}")

print("\n" + "="*80)
print("✅ Backtesting Complete!")
print("="*80)
print("\n📌 Interpretation Guide:")
print("   MAE:  Mean Absolute Error (avg yield diff in %)")
print("   RMSE: Root Mean Squared Error (penalizes large errors)")
print("   MAPE: Mean Absolute Percentage Error (% error)")
print("   Bias: Positive = over-forecasting, Negative = under-forecasting")
print("\n   Good: MAE < 0.10%, MAPE < 2%")
print("   Fair: MAE 0.10-0.20%, MAPE 2-5%")
