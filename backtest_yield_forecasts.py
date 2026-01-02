#!/usr/bin/env python3
"""
Backtesting framework for yield forecast models.
Walk-forward validation to evaluate model precision.
"""

import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta
from yield_forecast_models import (
    forecast_arima, forecast_ets, forecast_prophet,
    forecast_random_walk, forecast_monte_carlo,
    forecast_ma5, forecast_var
)

class YieldForecastBacktester:
    """Walk-forward backtesting for yield forecasts."""
    
    def __init__(self, db_path='database/20251215_priceyield.csv', tenor='10_year'):
        """
        Args:
            db_path: Path to price/yield CSV
            tenor: Tenor to backtest ('05_year' or '10_year')
        """
        self.tenor = tenor
        self.df = pd.read_csv(db_path)
        self.df['date'] = pd.to_datetime(self.df['date'], format='%d/%m/%Y')
        
        # Filter to single tenor, aggregate across series
        tenor_data = self.df[self.df['tenor'] == tenor].groupby('date')['yield'].mean()
        self.series = pd.Series(tenor_data).sort_index()
        
        print(f"✓ Loaded {len(self.series)} observations for {tenor}")
        print(f"  Date range: {self.series.index[0].date()} to {self.series.index[-1].date()}")
    
    def _calc_metrics(self, actuals, forecasts):
        """Calculate error metrics."""
        errors = actuals - forecasts
        abs_errors = np.abs(errors)
        pct_errors = np.abs(errors / actuals) * 100
        
        return {
            'mae': np.mean(abs_errors),
            'rmse': np.sqrt(np.mean(errors ** 2)),
            'mape': np.mean(pct_errors),
            'bias': np.mean(errors),
            'std_error': np.std(errors),
            'min_error': np.min(errors),
            'max_error': np.max(errors)
        }
    
    def _format_metrics(self, metrics):
        """Format metrics for display."""
        return (
            f"MAE:  {metrics['mae']:8.6f}  "
            f"RMSE: {metrics['rmse']:8.6f}  "
            f"MAPE: {metrics['mape']:6.2f}%  "
            f"Bias: {metrics['bias']:8.6f}"
        )
    
    def backtest_one_step_ahead(self, test_window=50):
        """
        One-step-ahead forecast backtest.
        Forecast 1 day ahead using all available data.
        
        Args:
            test_window: Number of days to backtest
            
        Returns:
            DataFrame with forecast and actual values
        """
        print(f"\n{'='*80}")
        print(f"ONE-STEP-AHEAD BACKTEST (Last {test_window} days)")
        print(f"{'='*80}")
        
        # Use last test_window days
        start_idx = max(0, len(self.series) - test_window)
        test_dates = self.series.index[start_idx:]
        
        results = {}
        models = {
            'arima': forecast_arima,
            'ets': forecast_ets,
            'prophet': forecast_prophet,
            'random_walk': forecast_random_walk,
            'monte_carlo': forecast_monte_carlo,
            'ma5': forecast_ma5,
            'var': forecast_var,
        }
        
        # Initialize results for each model
        for model_name in models.keys():
            results[model_name] = {'forecast': [], 'actual': [], 'date': []}
        
        # Walk forward
        for i, test_date in enumerate(test_dates):
            # Data up to (but not including) test date
            train_series = self.series[:start_idx + i]
            
            if len(train_series) < 10:  # Need minimum data
                continue
            
            # Forecast for next day (test_date)
            forecast_date = test_date + timedelta(days=1)
            
            # Get actual value at forecast_date (next day)
            next_idx = start_idx + i + 1
            if next_idx < len(self.series):
                actual = self.series.iloc[next_idx]
            else:
                continue
            
            # Forecast with each model
            for model_name, forecast_fn in models.items():
                try:
                    if model_name == 'ma5':
                        # MA5 is too simple for walk-forward, skip
                        continue
                    forecast = forecast_fn(train_series, forecast_date)
                    if isinstance(forecast, tuple):
                        forecast = forecast[0]  # Extract point forecast if CI returned
                    
                    results[model_name]['forecast'].append(forecast)
                    results[model_name]['actual'].append(actual)
                    results[model_name]['date'].append(test_date)
                    
                except Exception as e:
                    pass  # Skip if model fails
        
        # Calculate metrics and display
        print(f"\n{'Model':<20} {'MAE':<12} {'RMSE':<12} {'MAPE':<10} {'Bias':<10}")
        print("─" * 80)
        
        metrics_summary = {}
        for model_name in models.keys():
            if not results[model_name]['forecast']:
                continue
            
            forecasts = np.array(results[model_name]['forecast'])
            actuals = np.array(results[model_name]['actual'])
            
            metrics = self._calc_metrics(actuals, forecasts)
            metrics_summary[model_name] = metrics
            
            print(f"{model_name:<20} "
                  f"{metrics['mae']:<12.6f} "
                  f"{metrics['rmse']:<12.6f} "
                  f"{metrics['mape']:<10.2f} "
                  f"{metrics['bias']:<10.6f}")
        
        return results, metrics_summary
    
    def backtest_multi_step(self, forecast_days=[5, 10, 20], num_windows=5):
        """
        Multi-step forecast backtest.
        Forecast 5, 10, 20 days ahead.
        
        Args:
            forecast_days: Days ahead to forecast
            num_windows: Number of test windows
        """
        print(f"\n{'='*80}")
        print(f"MULTI-STEP FORECAST BACKTEST")
        print(f"{'='*80}")
        
        models = {
            'arima': forecast_arima,
            'ets': forecast_ets,
            'prophet': forecast_prophet,
            'random_walk': forecast_random_walk,
            'monte_carlo': forecast_monte_carlo,
            'var': forecast_var,
        }
        
        results = {days: {} for days in forecast_days}
        
        # Test windows at regular intervals
        window_size = len(self.series) // num_windows
        test_positions = [len(self.series) - (i + 1) * window_size for i in range(num_windows)]
        
        for forecast_horizon in forecast_days:
            print(f"\n{forecast_horizon}-day forecast:")
            print("─" * 80)
            
            for model_name in models.keys():
                if model_name == 'ma5':
                    continue
                
                forecasts = []
                actuals = []
                
                for test_idx in test_positions:
                    if test_idx < 20:  # Need minimum training data
                        continue
                    
                    # Data for training
                    train_series = self.series[:test_idx]
                    
                    # Forecast date
                    forecast_date = train_series.index[-1] + timedelta(days=forecast_horizon)
                    
                    # Actual value at forecast date
                    if test_idx + forecast_horizon < len(self.series):
                        actual = self.series.iloc[test_idx + forecast_horizon]
                    else:
                        continue
                    
                    try:
                        forecast = models[model_name](train_series, forecast_date)
                        if isinstance(forecast, tuple):
                            forecast = forecast[0]
                        
                        forecasts.append(forecast)
                        actuals.append(actual)
                    except:
                        pass
                
                if forecasts:
                    metrics = self._calc_metrics(np.array(actuals), np.array(forecasts))
                    results[forecast_horizon][model_name] = metrics
                    
                    print(f"  {model_name:<18} {self._format_metrics(metrics)}")
        
        return results
    
    def backtest_rolling_window(self, train_days=252, test_days=20):
        """
        Rolling window backtest (walk-forward validation).
        Train on last N days, test on next 20 days, roll forward.
        
        Args:
            train_days: Rolling training window size (1 year = 252 days)
            test_days: Testing window size
        """
        print(f"\n{'='*80}")
        print(f"ROLLING WINDOW BACKTEST (train={train_days}d, test={test_days}d)")
        print(f"{'='*80}")
        
        models = {
            'arima': forecast_arima,
            'ets': forecast_ets,
            'prophet': forecast_prophet,
            'random_walk': forecast_random_walk,
            'monte_carlo': forecast_monte_carlo,
            'ma5': forecast_ma5,
            'var': forecast_var,
        }
        
        metrics_by_model = {m: [] for m in models.keys()}
        
        # Create rolling windows
        num_windows = (len(self.series) - train_days - test_days) // test_days
        
        for w in range(num_windows):
            start = w * test_days
            train_end = start + train_days
            test_end = train_end + test_days
            
            if test_end > len(self.series):
                break
            
            train_series = self.series[start:train_end]
            test_dates = self.series.index[train_end:test_end]
            
            # One-step-ahead forecasts in test window
            forecasts_dict = {m: [] for m in models.keys()}
            actuals_list = []
            
            for i, test_date in enumerate(test_dates[:-1]):
                forecast_date = test_dates[i + 1]
                actual = self.series.iloc[train_end + i + 1]
                
                for model_name, forecast_fn in models.items():
                    try:
                        forecast = forecast_fn(train_series, forecast_date)
                        if isinstance(forecast, tuple):
                            forecast = forecast[0]
                        forecasts_dict[model_name].append(forecast)
                    except:
                        pass
                
                actuals_list.append(actual)
            
            # Calculate metrics for this window
            if actuals_list:
                for model_name in models.keys():
                    if forecasts_dict[model_name]:
                        metrics = self._calc_metrics(
                            np.array(actuals_list),
                            np.array(forecasts_dict[model_name])
                        )
                        metrics_by_model[model_name].append(metrics)
        
        # Average metrics across windows
        print(f"\n{'Model':<20} {'MAE':<12} {'RMSE':<12} {'MAPE':<10}")
        print("─" * 80)
        
        for model_name in models.keys():
            if metrics_by_model[model_name]:
                # Average across windows
                avg_metrics = {
                    'mae': np.mean([m['mae'] for m in metrics_by_model[model_name]]),
                    'rmse': np.mean([m['rmse'] for m in metrics_by_model[model_name]]),
                    'mape': np.mean([m['mape'] for m in metrics_by_model[model_name]]),
                }
                
                print(f"{model_name:<20} "
                      f"{avg_metrics['mae']:<12.6f} "
                      f"{avg_metrics['rmse']:<12.6f} "
                      f"{avg_metrics['mape']:<10.2f}")


if __name__ == '__main__':
    # Run backtests
    bt = YieldForecastBacktester(tenor='10_year')
    
    # Test 1: One-step-ahead
    results_1step, metrics_1step = bt.backtest_one_step_ahead(test_window=50)
    
    # Test 2: Multi-step
    results_multi = bt.backtest_multi_step(forecast_days=[5, 10, 20], num_windows=5)
    
    # Test 3: Rolling window
    bt.backtest_rolling_window(train_days=252, test_days=20)
    
    print("\n" + "="*80)
    print("✓ Backtesting complete")
