# Yield Forecast Models & Methodology

## Overview

Perisai uses an ensemble of 7 time-series forecasting models to predict bond yields with high precision. Each model leverages the full historical dataset (779-781 observations per tenor, 2023-2026) to learn market dynamics.

---

## Models & Data Usage

### ✅ Full-History Models (Use All Observations)

#### 1. **ARIMA(1,1,1)** — Autoregressive Integrated Moving Average
- **Data Used:** All observations
- **Method:** Fits autoregressive and moving average components to historical yield movements
- **Best For:** 1-5 day forecasts, trend-following markets
- **Backtest Performance:** MAE 0.0164%, MAPE 0.27%
- **Code:** [forecast_arima()](yield_forecast_models.py#L30)

#### 2. **ETS** — Exponential Smoothing with Trend
- **Data Used:** All observations
- **Method:** Weighted average of past observations with exponential decay
- **Best For:** Smooth yield curves, stable regimes
- **Backtest Performance:** MAE 0.0161%, MAPE 0.26% ⭐ Best
- **Code:** [forecast_ets()](yield_forecast_models.py#L65)
- **Note:** Uses seasonal_periods=12 for monthly seasonality

#### 3. **Prophet** — Facebook's Probabilistic Forecaster
- **Data Used:** All observations
- **Method:** Decomposes series into trend, seasonality, and holidays
- **Best For:** Multiple seasonalities, structural breaks
- **Backtest Performance:** Good, reliable confidence intervals
- **Code:** [forecast_prophet()](yield_forecast_models.py#L77)
- **Limitation:** Requires minimum 50+ observations (we have 779+)

#### 4. **VAR** — Vector Autoregression
- **Data Used:** All observations with 1-step lag
- **Method:** Models yield as function of its own lagged values
- **Best For:** Capturing short-term mean reversion
- **Code:** [forecast_var()](yield_forecast_models.py#L115)
- **Minimum Data:** 10 observations (we have 779+)

#### 5. **Monte Carlo** — Stochastic Path Simulation
- **Data Used:** All observations (calculates drift + volatility)
- **Method:** Simulates 500 random walks using historical return statistics
- **Drift:** Mean(returns) from all observations
- **Volatility:** Std(returns) from all observations
- **Best For:** Quantifying uncertainty, confidence intervals
- **Backtest Performance:** MAE 0.0163%, MAPE 0.27%
- **Output:** Point forecast (mean of 500 simulations)
- **Code:** [forecast_monte_carlo()](yield_forecast_models.py#L118)

### ⚠️ Limited-Data Models

#### 6. **Random Walk + Drift** — Enhanced Random Walk
- **Data Used:** All observations to calculate drift
- **Previous:** Only last value
- **Improved:** Adds historical mean return (drift) for trend awareness
- **Formula:** `forecast = last_value × (1 + drift)^steps`
- **Best For:** Quick, lightweight forecasts
- **Backtest Performance:** MAE 0.0161%, MAPE 0.26%
- **Code:** [forecast_random_walk()](yield_forecast_models.py#L89)

#### 7. **MA5** — 5-Day Moving Average
- **Data Used:** Last 5 observations only
- **Method:** Simple average of recent yields
- **Best For:** Baseline, ultra-fast computation
- **Limitation:** Ignores long-term trends
- **Code:** [forecast_ma5()](yield_forecast_models.py#L110)

---

## Data Requirements

### Minimum Observations Needed

| Model | Minimum | Recommended | Your Data |
|-------|---------|-------------|-----------|
| ARIMA | 15 | 50+ | ✅ 779 |
| ETS | 10 | 50+ | ✅ 779 |
| Prophet | 50 | 100+ | ✅ 779 |
| VAR | 10 | 50+ | ✅ 779 |
| Monte Carlo | 2 | 20+ | ✅ 779 |
| Random Walk | 2 | 5+ | ✅ 779 |
| MA5 | 5 | 20+ | ✅ 779 |

**Your Status:** All models have excellent data availability (779-781 observations per tenor).

---

## Forecast Accuracy (Backtesting Results)

### One-Step-Ahead (1 Day Forecast)

| Model | MAE | RMSE | MAPE | Rating |
|-------|-----|------|------|--------|
| **ETS** | 0.0161% | 0.0211% | 0.26% | ⭐⭐⭐⭐⭐ |
| ARIMA | 0.0164% | 0.0216% | 0.27% | ⭐⭐⭐⭐⭐ |
| Random Walk+Drift | 0.0161% | 0.0212% | 0.26% | ⭐⭐⭐⭐⭐ |
| Monte Carlo | 0.0163% | 0.0214% | 0.27% | ⭐⭐⭐⭐⭐ |

**Interpretation:** Average error ±1.6 basis points on 1-day forecasts.

### Five-Step-Ahead (5 Day Forecast)

| Model | MAE | RMSE | MAPE | Rating |
|-------|-----|------|------|--------|
| **Random Walk+Drift** | 0.0310% | 0.0431% | 0.50% | ⭐⭐⭐⭐⭐ |
| ARIMA | 0.0380% | 0.0482% | 0.62% | ⭐⭐⭐⭐☆ |
| Monte Carlo | 0.0377% | 0.0480% | 0.61% | ⭐⭐⭐⭐☆ |

**Interpretation:** Average error ±3.1 basis points on 5-day forecasts.

---

## Implementation Details

### How Models Are Used

```python
# Single forecast
from yield_forecast_models import forecast_arima
forecast_date = pd.to_datetime('2026-01-10')
yield_series = pd.Series([6.1, 6.15, 6.12, ...], index=dates)
forecast, confidence_interval = forecast_arima(yield_series, forecast_date)

# Ensemble forecast (averaging multiple models)
forecasts = [
    forecast_arima(yield_series, forecast_date)[0],
    forecast_ets(yield_series, forecast_date),
    forecast_prophet(yield_series, forecast_date),
    forecast_monte_carlo(yield_series, forecast_date),
]
ensemble_forecast = np.mean(forecasts)
```

### Data Preprocessing

All models receive:
1. **Clean time series** - No missing values, sorted by date
2. **Business-day alignment** - Weekends and Indonesian holidays removed
3. **Full historical context** - All 779-781 observations available
4. **Standardized index** - DatetimeIndex for proper frequency handling

### Fallback Strategy

If a model fails (e.g., convergence issues):
1. Return last observed value (safest fallback)
2. Log warning for monitoring
3. Continue with remaining ensemble models
4. Average remaining valid forecasts

---

## Model Selection Guide

### For 1-Day Forecasts (Next Business Day)
- **Best:** ETS (lowest MAE)
- **Backup:** ARIMA, Random Walk+Drift
- **Why:** All perform equally well, ETS slightly more stable

### For 5-Day Forecasts (1 Week Out)
- **Best:** Random Walk+Drift
- **Backup:** ARIMA, Monte Carlo
- **Why:** Drift component captures short-term trends better

### For 10+ Day Forecasts
- **Best:** ARIMA with wider confidence intervals
- **Alternative:** Monte Carlo for risk quantification
- **Why:** Longer horizons increase uncertainty; need robust trend modeling

### For Risk Quantification
- **Use:** Monte Carlo
- **Why:** Provides confidence intervals (2.5%-97.5% ranges)
- **Output:** Mean forecast + CI bounds

### For Production Ensemble
```python
# Weighted by backtest MAE performance
weights = {
    'ets': 0.25,
    'arima': 0.25,
    'random_walk': 0.25,
    'monte_carlo': 0.25,
}
ensemble = sum(forecast_x(series, date) * w 
               for x, w in weights.items())
```

---

## Backtesting Methodology

See [BACKTEST_GUIDE.md](../BACKTEST_GUIDE.md) for:
- Walk-forward validation details
- How to run backtests
- Metrics interpretation
- Performance benchmarks

Quick backtest:
```bash
python test_backtest.py
```

---

## Files

- [yield_forecast_models.py](../yield_forecast_models.py) — All 7 model implementations
- [priceyield_20251223.py](../priceyield_20251223.py) — Bond query interface with forecasting
- [test_backtest.py](../test_backtest.py) — Practical backtesting script
- [backtest_yield_forecasts.py](../backtest_yield_forecasts.py) — Full-featured backtesting class
- [BACKTEST_GUIDE.md](../BACKTEST_GUIDE.md) — Backtesting documentation

---

## Recent Improvements

✅ **Random Walk + Drift Enhancement**
- Improved from naive (last value only) to drift-aware
- Now uses ALL observations to calculate historical trend
- Better 5-day forecasts

✅ **Monte Carlo Enhancement**
- Explicit documentation of drift and volatility usage
- Uses ALL 779 observations for robust statistics
- Provides confidence intervals

✅ **All Models Use Full History**
- ARIMA, ETS, Prophet, VAR now clearly documented as full-history users
- Better feature engineering and pattern detection

---

## Monitoring & Maintenance

### Weekly Tasks
- Run `test_backtest.py` to validate current accuracy
- Compare against expected MAE/MAPE benchmarks
- Check for systematic bias (over/under-forecasting)

### Monthly Tasks
- Retrain all models with new data (latest month)
- Backtest on rolling windows (walk-forward)
- Update ensemble weights if performance changes

### Triggers for Investigation
- MAE increases > 50% vs baseline
- Systematic positive/negative bias emerges
- Specific model converges with errors
- Model failures increase > 5%

