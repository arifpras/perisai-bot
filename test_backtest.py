#!/usr/bin/env python3
"""
Practical Backtesting Framework for Yield Forecasts
Tests model precision on recent historical data.
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from yield_forecast_models import (
    forecast_arima, forecast_ets, forecast_prophet,
    forecast_random_walk, forecast_monte_carlo, forecast_ma5, forecast_var
)

# Load and prepare data
df = pd.read_csv('database/20251215_priceyield.csv')
df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y')

print("╔════════════════════════════════════════════════════════════════════╗")
print("║          YIELD FORECAST BACKTEST - REAL DATA RESULTS              ║")
print("╚════════════════════════════════════════════════════════════════════╝")

for tenor in ['10_year']:  # Test on 10-year
    print(f"\n{'='*80}")
    print(f"BACKTESTING: {tenor} BOND YIELDS")
    print(f"{'='*80}")
    
    # Get data for this tenor, sorted by date
    tenor_df = df[df['tenor'] == tenor].sort_values('date')
    tenor_df = tenor_df.drop_duplicates('date', keep='first')
    series = pd.Series(tenor_df['yield'].values, index=tenor_df['date'].values)
    series = series.dropna()
    
    print(f"✓ {len(series)} valid observations")
    print(f"  Date range: {series.index[0].date()} to {series.index[-1].date()}")
    print(f"  Yield range: {series.min():.3f}% to {series.max():.3f}%")
    
    # Test parameters
    test_size = 20  # Test on last 20 points
    train_end = len(series) - test_size
    
    models = {
        'ARIMA': forecast_arima,
        'ETS': forecast_ets,
        'Random Walk+Drift': forecast_random_walk,
        'Monte Carlo': forecast_monte_carlo,
    }
    
    # ONE-STEP AHEAD TEST
    print(f"\n📍 ONE-STEP-AHEAD FORECAST (next business day)")
    print("─" * 80)
    
    results = {}
    for model_name in models:
        results[model_name] = {'errors': [], 'forecasts': [], 'actuals': []}
    
    for i in range(test_size - 1):
        train_idx = train_end + i
        test_idx = train_idx + 1
        
        # Training data
        train_series = series.iloc[:test_idx]
        
        # Forecast target date
        target_date = series.index[test_idx]
        actual_value = series.iloc[test_idx]
        
        # Get forecasts from each model
        for model_name, forecast_func in models.items():
            try:
                forecast_val = forecast_func(train_series, target_date)
                if isinstance(forecast_val, tuple):
                    forecast_val = forecast_val[0]
                forecast_val = float(forecast_val)
                
                error = actual_value - forecast_val
                results[model_name]['errors'].append(error)
                results[model_name]['forecasts'].append(forecast_val)
                results[model_name]['actuals'].append(float(actual_value))
            except Exception as e:
                pass  # Skip if forecast fails
    
    # Display results
    print(f"\n{'Model':<20} {'Samples':<10} {'MAE':<12} {'RMSE':<12} {'MAPE (%)':<12}")
    print("─" * 80)
    
    best_mae = float('inf')
    best_model = None
    
    for model_name in models:
        if len(results[model_name]['errors']) >= 5:
            errors = np.array(results[model_name]['errors'])
            actuals = np.array(results[model_name]['actuals'])
            forecasts = np.array(results[model_name]['forecasts'])
            
            n = len(errors)
            mae = np.mean(np.abs(errors))
            rmse = np.sqrt(np.mean(errors ** 2))
            mape = np.mean(np.abs(errors / actuals) * 100)
            
            print(f"{model_name:<20} {n:<10} {mae:<12.6f} {rmse:<12.6f} {mape:<12.2f}")
            
            if mae < best_mae and not np.isnan(mae):
                best_mae = mae
                best_model = model_name
    
    if best_model:
        print(f"\n🏆 Best model (lowest MAE): **{best_model}**")
        print(f"   MAE: {best_mae:.6f}% | Typical error: ±{best_mae:.2f} basis points")
    
    # MULTI-STEP TEST
    print(f"\n📊 5-STEP-AHEAD FORECAST (~1 week out)")
    print("─" * 80)
    
    # Use every 5th point for testing
    test_indices = list(range(train_end, len(series) - 5, 5))
    
    multi_results = {}
    for model_name in ['ARIMA', 'Random Walk+Drift', 'Monte Carlo']:
        multi_results[model_name] = {'errors': [], 'forecasts': [], 'actuals': []}
    
    for train_idx in test_indices:
        train_series = series.iloc[:train_idx + 1]
        test_idx = train_idx + 5
        
        if test_idx >= len(series):
            break
        
        target_date = series.index[test_idx]
        actual_value = series.iloc[test_idx]
        
        for model_name in ['ARIMA', 'Random Walk+Drift', 'Monte Carlo']:
            try:
                if model_name == 'ARIMA':
                    forecast_val = forecast_arima(train_series, target_date)[0]
                elif model_name == 'Random Walk+Drift':
                    forecast_val = forecast_random_walk(train_series, target_date)
                else:  # Monte Carlo
                    forecast_val = forecast_monte_carlo(train_series, target_date)
                
                forecast_val = float(forecast_val)
                error = actual_value - forecast_val
                
                multi_results[model_name]['errors'].append(error)
                multi_results[model_name]['forecasts'].append(forecast_val)
                multi_results[model_name]['actuals'].append(float(actual_value))
            except:
                pass
    
    print(f"\n{'Model':<20} {'Samples':<10} {'MAE':<12} {'RMSE':<12} {'MAPE (%)':<12}")
    print("─" * 80)
    
    for model_name in ['ARIMA', 'Random Walk+Drift', 'Monte Carlo']:
        if len(multi_results[model_name]['errors']) >= 2:
            errors = np.array(multi_results[model_name]['errors'])
            actuals = np.array(multi_results[model_name]['actuals'])
            
            n = len(errors)
            mae = np.mean(np.abs(errors))
            rmse = np.sqrt(np.mean(errors ** 2))
            mape = np.mean(np.abs(errors / actuals) * 100)
            
            print(f"{model_name:<20} {n:<10} {mae:<12.6f} {rmse:<12.6f} {mape:<12.2f}")

print("\n" + "="*80)
print("💡 INTERPRETATION:")
print("="*80)
print("""
MAE (Mean Absolute Error):
  • < 0.05%:  Excellent  ★★★★★
  • 0.05-0.10%: Very Good ★★★★☆
  • 0.10-0.20%: Good      ★★★☆☆
  • > 0.20%:    Fair      ★★☆☆☆

MAPE (Mean Absolute Percentage Error):
  • < 1%:  Excellent
  • 1-3%:  Good
  • 3-5%:  Fair
  • > 5%:  Needs improvement

Note: 1 basis point (bp) = 0.01%
""")
print("="*80)
