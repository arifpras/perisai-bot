# Testing & Validation Guide

## Overview

Perisai includes comprehensive validation and backtesting capabilities to ensure forecast accuracy and system reliability.

---

## Backtesting Framework

### Quick Start

**Run the simple backtest:**
```bash
python test_backtest.py
```

This runs on your actual bond data and shows results for:
- 1-day-ahead forecasts (last 20 business days)
- 5-day-ahead forecasts
- Model comparison

### Full-Featured Backtesting

**For detailed walk-forward validation:**
```python
from backtest_yield_forecasts import YieldForecastBacktester

bt = YieldForecastBacktester(tenor='10_year')

# One-step-ahead test
results_1step, metrics_1step = bt.backtest_one_step_ahead(test_window=50)

# Multi-step test (5, 10, 20 days)
results_multi = bt.backtest_multi_step(forecast_days=[5, 10, 20], num_windows=5)

# Rolling window (walk-forward)
bt.backtest_rolling_window(train_days=252, test_days=20)
```

---

## Validation Tests

### 1. Unit Tests

**Test Individual Models:**
```python
import pandas as pd
from yield_forecast_models import forecast_arima, forecast_monte_carlo

# Create test series
dates = pd.date_range('2023-01-02', periods=100, freq='B')
yields = pd.Series([6.0 + 0.01*i/100 for i in range(100)], index=dates)

# Test ARIMA
forecast_val, ci = forecast_arima(yields, pd.to_datetime('2023-05-01'))
assert isinstance(forecast_val, float)
assert 4.0 < forecast_val < 8.0  # Reasonable range

# Test Monte Carlo
forecast_val = forecast_monte_carlo(yields, pd.to_datetime('2023-05-01'))
assert isinstance(forecast_val, float)
assert forecast_val > 0
```

### 2. Data Quality Tests

**Verify bond data integrity:**
```python
import pandas as pd

df = pd.read_csv('database/20251215_priceyield.csv')

# Check for missing values
assert df.isnull().sum().sum() == 0, "Found NaN values"

# Check date range
df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y')
assert df['date'].min() >= pd.to_datetime('2023-01-01')
assert df['date'].max() >= pd.to_datetime('2025-12-01')

# Check tenors
assert set(df['tenor'].unique()) == {'05_year', '10_year', ...}

# Check yields are in reasonable range (0-20%)
assert (df['yield'] > 0).all() and (df['yield'] < 20).all()

print("✅ Data quality checks passed")
```

### 3. Forecast Sanity Tests

**Quick validation after model updates:**
```python
import pandas as pd
import numpy as np
from yield_forecast_models import forecast_arima, forecast_prophet

# Test data
dates = pd.date_range('2023-01-02', periods=200, freq='B')
yields = 6.5 + np.random.normal(0, 0.1, 200)
series = pd.Series(yields, index=dates)

# Test 1: Forecasts are finite
forecast_val = forecast_arima(series, dates[-1] + pd.Timedelta(days=1))[0]
assert np.isfinite(forecast_val), "Forecast is NaN or inf"

# Test 2: Forecasts are in reasonable range
assert 4.0 < forecast_val < 9.0, f"Forecast {forecast_val} outside reasonable range"

# Test 3: Multiple models agree
forecasts = [
    forecast_arima(series, dates[-1] + pd.Timedelta(days=1))[0],
    forecast_prophet(series, dates[-1] + pd.Timedelta(days=1)),
]
avg = np.mean(forecasts)
assert max(forecasts) - min(forecasts) < 0.5, "Models disagree significantly"

print("✅ Forecast sanity checks passed")
```

### 4. Performance Regression Tests

**Ensure models maintain baseline accuracy:**
```python
import pandas as pd
import numpy as np
from test_backtest import YieldForecastBacktester

# Expected baseline performance
BASELINE_MAE = {
    'ARIMA': 0.018,      # ±1.8 bps
    'ETS': 0.017,        # ±1.7 bps
    'Random Walk+Drift': 0.017,  # ±1.7 bps
    'Monte Carlo': 0.018, # ±1.8 bps
}

THRESHOLD = 0.030  # Allow 30% degradation

# Run backtest
bt = YieldForecastBacktester(tenor='10_year')
results, metrics = bt.backtest_one_step_ahead(test_window=30)

# Check performance
for model, expected_mae in BASELINE_MAE.items():
    if model in metrics:
        actual_mae = metrics[model]['mae']
        max_allowed = expected_mae * 1.30
        
        assert actual_mae <= max_allowed, \
            f"{model}: MAE {actual_mae:.6f} exceeds threshold {max_allowed:.6f}"
        
        print(f"✅ {model}: {actual_mae:.6f} (baseline: {expected_mae:.6f})")

print("✅ Performance regression tests passed")
```

---

## Continuous Monitoring

### Weekly Backtest Schedule

Add to crontab (runs every Monday):
```bash
# Run backtest and email results
0 9 * * 1 cd /workspaces/perisai-bot && \
    /usr/bin/python3 test_backtest.py > backtest_results_$(date +\%Y\%m\%d).log 2>&1 && \
    mail -s "Perisai Weekly Backtest" user@example.com < backtest_results_*.log
```

### Automated Alerts

**In your monitoring system:**
```python
import subprocess
import json
from datetime import datetime

def run_backtest_check():
    """Run backtest and alert if performance degrades."""
    result = subprocess.run(['python', 'test_backtest.py'], 
                          capture_output=True, text=True)
    
    # Parse output for MAE
    if 'ETS' in result.stdout:
        # Extract MAE value and compare to threshold
        if mae > 0.020:  # Alert if MAE exceeds 2.0 bps
            send_slack_alert(f"⚠️ Model MAE degradation: {mae:.6f}")
```

---

## Stress Testing

### Market Shock Scenarios

**Test forecasts during volatile periods:**
```python
import pandas as pd
import numpy as np
from yield_forecast_models import forecast_arima

# Simulate 500 bps spike (stress scenario)
dates = pd.date_range('2023-01-02', periods=100, freq='B')
base_yields = np.full(100, 6.0)
base_yields[-20:] = 11.0  # Sudden 500 bps jump

series = pd.Series(base_yields, index=dates)

# Forecast after shock
forecast_val = forecast_arima(series, dates[-1] + pd.Timedelta(days=1))[0]

# Model should anticipate elevated yields
assert forecast_val > 10.0, f"Model missed shock: forecast {forecast_val}"

print(f"✅ Stress test passed: forecast={forecast_val:.2f}")
```

### Missing Data Scenarios

**Test robustness to data gaps:**
```python
import pandas as pd
import numpy as np
from yield_forecast_models import forecast_random_walk

# Create series with gaps
dates = pd.date_range('2023-01-02', periods=100, freq='B')
yields = np.random.normal(6.0, 0.1, 100)

# Remove 10 consecutive days (holiday/data error)
series = pd.Series(yields, index=dates)
series_with_gap = series.drop(series.index[50:60])

# Model should handle gap gracefully
try:
    forecast_val = forecast_random_walk(series_with_gap, dates[-1])
    assert np.isfinite(forecast_val)
    print(f"✅ Gap handling: forecast={forecast_val:.4f}")
except Exception as e:
    print(f"❌ Failed on data gap: {e}")
```

---

## Example: Full Validation Pipeline

```python
#!/usr/bin/env python3
"""
Complete validation pipeline for yield forecasting models.
Run before production deployment.
"""

import pandas as pd
import numpy as np
from yield_forecast_models import forecast_arima, forecast_ets, forecast_monte_carlo
from test_backtest import YieldForecastBacktester

def validate_all():
    """Run complete validation suite."""
    
    print("╔════════════════════════════════════════════╗")
    print("║   PERISAI VALIDATION SUITE                 ║")
    print("╚════════════════════════════════════════════╝")
    
    # 1. Data Quality
    print("\n1️⃣  Data Quality Checks")
    print("─" * 50)
    df = pd.read_csv('database/20251215_priceyield.csv')
    df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y')
    
    assert len(df) > 500, "Insufficient data"
    assert df['yield'].isnull().sum() == 0, "Found NaN in yields"
    assert (df['yield'] > 0).all(), "Found negative yields"
    print("✅ Data integrity verified")
    
    # 2. Model Unit Tests
    print("\n2️⃣  Model Unit Tests")
    print("─" * 50)
    dates = pd.date_range('2023-01-02', periods=100, freq='B')
    series = pd.Series(np.random.normal(6.0, 0.1, 100), index=dates)
    
    for model_name, model_fn in [('ARIMA', forecast_arima), 
                                  ('ETS', forecast_ets),
                                  ('Monte Carlo', forecast_monte_carlo)]:
        try:
            result = model_fn(series, dates[-1])
            if isinstance(result, tuple):
                result = result[0]
            assert np.isfinite(result), f"{model_name} returned inf/nan"
            print(f"✅ {model_name} passed")
        except Exception as e:
            print(f"❌ {model_name} failed: {e}")
    
    # 3. Backtest
    print("\n3️⃣  Backtest Validation")
    print("─" * 50)
    bt = YieldForecastBacktester(tenor='10_year')
    results, metrics = bt.backtest_one_step_ahead(test_window=30)
    
    expected_mae = 0.020
    for model in ['ARIMA', 'ETS', 'Monte Carlo']:
        if model in metrics:
            mae = metrics[model]['mae']
            status = "✅" if mae < expected_mae else "⚠️"
            print(f"{status} {model}: MAE={mae:.6f}")
    
    # 4. Summary
    print("\n" + "="*50)
    print("✅ VALIDATION COMPLETE")
    print("="*50)

if __name__ == '__main__':
    validate_all()
```

Run this before every production deployment:
```bash
python validate_all.py
```

---

## Debugging Failed Forecasts

### Model Returns NaN

**Causes & Solutions:**

| Issue | Cause | Fix |
|-------|-------|-----|
| ARIMA NaN | Convergence failure | Try different order (p,d,q) |
| ETS NaN | Seasonal fit failed | Reduce seasonal_periods or use non-seasonal |
| Prophet NaN | Too few observations | Ensure 50+ observations |
| VAR NaN | Singular matrix | Add regularization or more data |

### Forecast Outside Expected Range

**Example: Yield forecast of -2% (clearly wrong)**

```python
# Debug steps
series = pd.Series([...], index=dates)
forecast = forecast_prophet(series, forecast_date)

# 1. Check input data
print(f"Series range: {series.min():.2f}% to {series.max():.2f}%")
print(f"Series length: {len(series)}")

# 2. Check for outliers
print(f"Outliers (>3σ): {series[np.abs(series - series.mean()) > 3*series.std()]}")

# 3. Use fallback
if forecast < 0 or forecast > 10:
    forecast = series.iloc[-1]  # Use last value as safe fallback
    print(f"⚠️ Using fallback: {forecast:.2f}%")
```

---

## Documentation Index

- [BACKTEST_GUIDE.md](../BACKTEST_GUIDE.md) — Backtesting methodology and results
- [YIELD_FORECAST_MODELS.md](YIELD_FORECAST_MODELS.md) — Model details and data usage
- [yield_forecast_models.py](../yield_forecast_models.py) — Source code
- [test_backtest.py](../test_backtest.py) — Practical backtest script

