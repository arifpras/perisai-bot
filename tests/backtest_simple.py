#!/usr/bin/env python3
"""
Simple backtesting framework for yield forecasts.
Practical walk-forward validation.
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from yield_forecast_models import (
    forecast_arima, forecast_ets, forecast_prophet,
    forecast_random_walk, forecast_monte_carlo, forecast_ma5, forecast_var
)
from datetime import timedelta

# Load data
df = pd.read_csv('database/20251215_priceyield.csv')
df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y')

# Aggregate by tenor
for tenor in ['05_year', '10_year']:
    print(f"\n{'='*80}")
    print(f"BACKTESTING: {tenor} Indonesian Government Bond Yields")
    print(f"{'='*80}")
    
    # Get data for this tenor
    tenor_data = df[df['tenor'] == tenor].groupby('date')['yield'].mean().sort_index()
    series = pd.Series(tenor_data)
    
    print(f"✓ {len(series)} observations ({series.index[0].date()} to {series.index[-1].date()})")
    
    # ===== ONE-STEP-AHEAD BACKTEST (Last 20 business days) =====
    print(f"\n1️⃣  ONE-STEP-AHEAD FORECAST (Next 1 day)")
    print("─" * 80)
    
    test_window = 20
    train_end = len(series) - test_window
    
    models = {
        'ARIMA': forecast_arima,
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
        
        # Training series
        train_series = series[:train_idx]
        
        # Forecast for next day
        forecast_date = series.index[train_idx] + timedelta(days=1)
        actual_value = series.iloc[train_idx + 1]
        
        # Get forecasts from each model
        for model_name, forecast_fn in models.items():
            try:
                forecast_val = forecast_fn(train_series, forecast_date)
                if isinstance(forecast_val, tuple):
                    forecast_val = forecast_val[0]
                
                results[model_name]['forecasts'].append(forecast_val)
                results[model_name]['actuals'].append(actual_value)
            except Exception as e:
                pass
    
    # Calculate metrics
    print(f"\n{'Model':<20} {'MAE':<12} {'RMSE':<12} {'MAPE (%)':<12} {'Bias':<10}")
    print("─" * 80)
    
    for model_name in models.keys():
        if results[model_name]['forecasts']:
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
                  f"{bias:<10.6f}")
    
    # ===== MULTI-STEP FORECAST (5, 10 days ahead) =====
    print(f"\n2️⃣  MULTI-STEP FORECAST")
    print("─" * 80)
    
    for horizon_days in [5, 10]:
        print(f"\n  {horizon_days}-day ahead forecast:")
        
        forecasts_dict = {m: [] for m in ['ARIMA', 'Random Walk+Drift', 'Monte Carlo']}
        actuals_list = []
        
        # Test at different points
        for test_idx in range(train_end, len(series) - horizon_days, 5):
            train_series = series[:test_idx]
            forecast_date = series.index[test_idx] + timedelta(days=horizon_days)
            
            if forecast_date not in series.index:
                continue
            
            actual_idx = series.index.get_loc(forecast_date)
            actual_val = series.iloc[actual_idx]
            
            try:
                forecasts_dict['ARIMA'].append(forecast_arima(train_series, forecast_date)[0])
                forecasts_dict['Random Walk+Drift'].append(forecast_random_walk(train_series, forecast_date))
                forecasts_dict['Monte Carlo'].append(forecast_monte_carlo(train_series, forecast_date))
                actuals_list.append(actual_val)
            except:
                pass
        
        print(f"  {'Model':<20} {'MAE':<12} {'RMSE':<12} {'MAPE (%)':<12}")
        print("  " + "─" * 76)
        
        for model_name in ['ARIMA', 'Random Walk+Drift', 'Monte Carlo']:
            if forecasts_dict[model_name]:
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
print("✅ Backtesting complete!")
print("="*80)
