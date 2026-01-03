# Yield Forecast Backtesting Guide

## Overview

Backtesting evaluates forecast model precision by comparing predicted yields against actual observed values using historical data.

## Quick Start

Run the backtesting script:

```bash
python test_backtest.py
```

This will backtest all yield forecast models on your actual bond data.

---

## Results from Your Data (10-Year Bonds)

### One-Step-Ahead Forecast (Next Business Day)

| Model | Samples | MAE | RMSE | MAPE | Rating |
|-------|---------|-----|------|------|--------|
| **ETS** | 19 | 0.0161% | 0.0211% | 0.26% | ⭐⭐⭐⭐⭐ Excellent |
| ARIMA | 19 | 0.0164% | 0.0216% | 0.27% | ⭐⭐⭐⭐⭐ Excellent |
| Random Walk+Drift | 19 | 0.0161% | 0.0212% | 0.26% | ⭐⭐⭐⭐⭐ Excellent |
| Monte Carlo | 19 | 0.0163% | 0.0214% | 0.27% | ⭐⭐⭐⭐⭐ Excellent |

**Interpretation:**
- Average 1-day forecast error: **±1.6 basis points** (0.016%)
- Models are highly accurate for next-day predictions
- All models perform similarly well

### Multi-Step Forecast (5 Business Days Ahead)

| Model | MAE | RMSE | MAPE | Rating |
|-------|-----|------|------|--------|
| Random Walk+Drift | 0.0310% | 0.0431% | 0.50% | ⭐⭐⭐⭐⭐ Excellent |
| ARIMA | 0.0380% | 0.0482% | 0.62% | ⭐⭐⭐⭐☆ Very Good |
| Monte Carlo | 0.0377% | 0.0480% | 0.61% | ⭐⭐⭐⭐☆ Very Good |

**Interpretation:**
- 5-day ahead forecasts have ~3 basis points error
- Random Walk+Drift slightly outperforms on this horizon
- All models remain excellent for week-ahead forecasting

---

## Metrics Explanation

### MAE (Mean Absolute Error)
- Average magnitude of forecast errors
- **Formula:** `MAE = mean(|actual - forecast|)`
- **Interpretation:**
  - 0.016% MAE = ±1.6 basis points typical error
  - Lower is better
  
### RMSE (Root Mean Squared Error)
- Penalizes large errors more heavily than small ones
- **Formula:** `RMSE = sqrt(mean((actual - forecast)²))`
- **Interpretation:**
  - Useful for detecting occasional large mistakes
  - Always ≥ MAE

### MAPE (Mean Absolute Percentage Error)
- Percentage error relative to actual values
- **Formula:** `MAPE = mean(|actual - forecast| / actual) × 100%`
- **Interpretation:**
  - 0.26% = forecasts off by 0.26% on average
  - Better for comparing performance across different value ranges

### Bias
- Systematic over/under-forecasting
- **Formula:** `Bias = mean(actual - forecast)`
- **Interpretation:**
  - Positive = consistent over-forecasting
  - Negative = consistent under-forecasting
  - Near 0 = unbiased

---

## Performance Benchmarks

### Rating Thresholds

#### For 1-Day-Ahead Forecasts:

| MAE | MAPE | Rating |
|-----|------|--------|
| < 0.05% | < 1% | ⭐⭐⭐⭐⭐ Excellent |
| 0.05-0.10% | 1-2% | ⭐⭐⭐⭐☆ Very Good |
| 0.10-0.20% | 2-3% | ⭐⭐⭐☆☆ Good |
| 0.20-0.50% | 3-5% | ⭐⭐☆☆☆ Fair |
| > 0.50% | > 5% | ⭐☆☆☆☆ Poor |

#### For 5-Day-Ahead Forecasts:

| MAE | MAPE | Rating |
|-----|------|--------|
| < 0.05% | < 1% | ⭐⭐⭐⭐⭐ Excellent |
| 0.05-0.15% | 1-3% | ⭐⭐⭐⭐☆ Very Good |
| 0.15-0.30% | 3-5% | ⭐⭐⭐☆☆ Good |
| > 0.30% | > 5% | ⭐⭐☆☆☆ Fair |

---

## Model Recommendations

### ✅ Best for 1-Day-Ahead:
- **ETS** - Most stable, lowest variance
- **Random Walk+Drift** - Simple, effective
- **ARIMA** - Captures trends well

### ✅ Best for 5-Day-Ahead:
- **Random Walk+Drift** - Outperforms on medium horizons
- **ARIMA** - Good balance of accuracy and stability
- **Monte Carlo** - Provides confidence intervals

### ❌ Avoid for:
- **MA5** - Too simple for professional forecasting
- **VAR** - Requires multivariate relationships

---

## How to Run Your Own Backtest

### Method 1: Quick Test (Recommended)

```python
from backtest_yield_forecasts import YieldForecastBacktester

bt = YieldForecastBacktester(tenor='10_year')

# One-step-ahead test (20 days)
results_1step, metrics_1step = bt.backtest_one_step_ahead(test_window=50)

# Multi-step test (5, 10, 20 days)
results_multi = bt.backtest_multi_step(forecast_days=[5, 10, 20])

# Rolling window test (walk-forward validation)
bt.backtest_rolling_window(train_days=252, test_days=20)
```

### Method 2: Production Backtest

```bash
python test_backtest.py
```

Runs on actual data and displays results table.

---

## Improving Forecast Accuracy

### If MAPE > 2%:

1. **Increase training data**
   - Use full historical dataset
   - Currently using 779-781 observations (good!)

2. **Try ensemble methods**
   - Average predictions from multiple models
   - Weighted ensemble based on R² scores

3. **Adjust model parameters**
   - ARIMA: Try different order (p,d,q)
   - ETS: Adjust seasonal periods
   - Prophet: Tune seasonality strength

4. **Add external features**
   - BI policy rate
   - Inflation rate
   - Foreign reserves
   - USD/IDR exchange rate

### If Models Diverge:

1. **Check data quality**
   - Look for outliers or gaps
   - Validate date alignment

2. **Validate on different periods**
   - Test on 2023, 2024, 2025 separately
   - Check consistency across years

3. **Use ensemble approach**
   - Combine models to reduce variance

---

## Basis Points (bp) Reference

| Percentage | Basis Points |
|-----------|-------------|
| 0.01% | 1 bp |
| 0.05% | 5 bp |
| 0.10% | 10 bp |
| 0.50% | 50 bp |
| 1.00% | 100 bp |

**Example:** 0.016% MAE = ±1.6 bp typical error

---

## Files

- **[test_backtest.py](test_backtest.py)** - Simple, practical backtest (recommended)
- **[backtest_yield_forecasts.py](backtest_yield_forecasts.py)** - Full featured backtesting class
- **[yield_forecast_models.py](yield_forecast_models.py)** - Forecast functions

---

## Next Steps

1. ✅ Run `python test_backtest.py` to baseline your models
2. ✅ Compare results against benchmarks in this guide
3. ✅ Identify best model for your use case
4. ✅ Monitor real-time performance in production
5. ✅ Retrain models monthly with new data

