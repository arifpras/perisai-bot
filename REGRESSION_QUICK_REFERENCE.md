# AR(1) Regression Analysis: Quick Reference

## Overview

The bot now supports proper AR(1) regression analysis for Indonesian government bond yields. Instead of vague LLM-generated prose, you get actual computed statistics with diagnostic tests.

## What is AR(1)?

**AR(1)** (Autoregressive model of order 1) regresses today's yield on yesterday's yield:

```
y_t = α + β y_{t-1} + ε_t
```

Where:
- `y_t` = yield today
- `y_{t-1}` = yield yesterday
- `α` = intercept (drift term)
- `β` = persistence coefficient (how much yesterday affects today)
- `ε_t` = residual (unpredictable shock)

## Query Patterns

### Basic Queries

```
/kei regres yield 5 year on 5 year at t-1 in 2025
/kei regression 10 year in 2025
/kei ar1 5 year in 2025
```

### With Date Ranges

```
/kei regres yield 5 year on 5 year at t-1 from 2023 to 2025
/kei regression 10 year from jan 2023 to dec 2025
/kei ar1 5 year in q1 2025
```

### All Available Data

```
/kei regres 5 year
/kei ar1 10 year
```

## Output Format

The bot returns:

### 1. **Regression Coefficients**
- **α (intercept)**: Drift term with standard error and p-value
- **β (persistence)**: How much yesterday's yield affects today (0 to 1)
- **R²**: How much of today's variation is explained by yesterday

### 2. **Interpretation**
- **High β (0.95-1.0)**: Near random walk, little mean reversion
- **Moderate β (0.5-0.8)**: Some mean reversion
- **Low β (<0.5)**: Strong mean reversion

### 3. **Yield Characteristics**
- Average, standard deviation, min, max over the period

### 4. **Residual Diagnostics**
- **Normality test** (Jarque-Bera): Are shocks normally distributed?
- **Autocorrelation test** (Ljung-Box): Are residuals independent?
- **Heteroskedasticity test** (ARCH): Does volatility change over time?

## Example Output

```
📊 INDOGB 05 YEAR: AR(1) Regression Analysis
Period: 2025-01-02 to 2025-12-31 (256 observations)

Model: y_t = α + β y_{t-1} + ε_t

Regression Results:
  α (intercept) = 0.022088 (SE: 0.032204, p=0.4928) 
  β (persistence) = 0.995501 (SE: 0.005250, p=0.0000) ***
  R² = 0.9938 | Adjusted R² = 0.9938

Interpretation:
  • The coefficient β = 0.9955 indicates very high persistence (near unit root).
    Yesterday's yield explains 99.4% of today's yield variation.
  • Process is close to a random walk (β ≈ 1), with little mean reversion.

Yield Characteristics:
  • Average: 6.17% | Std Dev: 0.54%
  • Range: 5.30% to 7.13%

Residual Diagnostics:
  • Mean: 0.000000 (should be ~0)
  • Std Dev: 0.0422%
  • Normality: Rejected (Jarque-Bera p=0.0000)
    → Residuals have fat tails or skewness (common during regime shifts)
  • Autocorrelation: Detected (Ljung-Box p=0.0017)
    → Residuals show serial correlation; AR(1) may be insufficient
  • Heteroskedasticity: Detected (ARCH test p=0.0404)
    → Volatility clustering present (variance changes over time)

*** p<0.01, ** p<0.05, * p<0.10
```

## Interpretation Guide

### High Persistence (β > 0.95)
- **Meaning**: Yields follow a near-random walk
- **Implication**: Shocks persist for long periods; forecasting is difficult beyond 1-2 days
- **Trading**: Momentum strategies may work; mean-reversion strategies won't

### Moderate Persistence (0.5 < β < 0.95)
- **Meaning**: Yields show some mean reversion
- **Half-life**: Time for a shock to decay by 50% = -ln(2) / ln(β) days
- **Trading**: Mean-reversion strategies feasible

### Low Persistence (β < 0.5)
- **Meaning**: Strong mean reversion
- **Implication**: Shocks quickly fade; yields return to average
- **Trading**: Mean-reversion strategies highly viable

## Diagnostic Tests Explained

### 1. Jarque-Bera (Normality Test)
- **H0**: Residuals are normally distributed
- **p < 0.05**: Reject normality → fat tails or skewness (common during crises)
- **Interpretation**: Non-normal residuals suggest extreme events happen more often than a Gaussian model predicts

### 2. Ljung-Box (Autocorrelation Test)
- **H0**: No autocorrelation in residuals
- **p < 0.05**: Residuals are correlated → AR(1) model is insufficient
- **Solution**: Consider AR(2), ARMA, or GARCH models

### 3. ARCH Test (Heteroskedasticity)
- **H0**: Constant variance over time
- **p < 0.05**: Volatility clustering detected
- **Interpretation**: Calm periods followed by volatile periods (common in bond markets)
- **Solution**: Consider GARCH models for volatility forecasting

## Use Cases

### Event Studies
Compare persistence before vs after a shock:
```
/kei regres 5 year from 1 sep 2025 to 7 sep 2025
/kei regres 5 year from 8 sep 2025 to 15 sep 2025
```

### Regime Analysis
Check if persistence changed over time:
```
/kei regres 5 year in 2023
/kei regres 5 year in 2024
/kei regres 5 year in 2025
```

### Forecasting Assessment
Understand how predictable yields are:
- **High R² + high β**: Yields are persistent but predictable short-term
- **Low R² + high β**: Random walk, hard to forecast
- **High R² + low β**: Mean-reverting, easier to forecast medium-term

## Technical Notes

- **Standard Errors**: Heteroskedasticity-robust (HC0) for valid inference even with changing volatility
- **Minimum Data**: Requires at least 10 observations (more is better)
- **Missing Values**: Automatically handled via daily averaging across bond series
- **Business Days**: Uses actual trading days, not calendar days

## Comparison with Previous Output

### Before (Vague LLM Response)
```
Using 2025 daily 5Y yields, regress y_t on y_{t-1}: y_t = α + β y_{t-1} + ε_t.
Estimated α = 0.00, β = 1.00, R² = 1.00.

Residual diagnostics: residual mean ~0 with no visible bias...
```
❌ Rounded to perfect values (α=0.00, β=1.00, R²=1.00)
❌ No actual statistics, just vague descriptions
❌ No hypothesis tests or p-values

### Now (Actual Regression Output)
```
α (intercept) = 0.022088 (SE: 0.032204, p=0.4928) 
β (persistence) = 0.995501 (SE: 0.005250, p=0.0000) ***
R² = 0.9938 | Adjusted R² = 0.9938

Normality: Rejected (Jarque-Bera p=0.0000)
Autocorrelation: Detected (Ljung-Box p=0.0017)
Heteroskedasticity: Detected (ARCH test p=0.0404)
```
✅ Real computed values with proper precision
✅ Standard errors and significance tests
✅ Formal diagnostic tests with p-values
✅ Plain English interpretation of results

## Files

- **`regression_analysis.py`**: Core regression functions
  - `ar1_regression()`: Compute regression and diagnostics
  - `format_ar1_results()`: Format output in plain English with HTML
- **`telegram_bot.py`**: Integration
  - `parse_regression_query()`: Query parser
  - Regression handler in `kei_command()` function

## Next Steps

Future enhancements could include:
- **AR(p)** models with multiple lags
- **ARMA/ARIMA** models for better fit
- **GARCH** models for volatility forecasting
- **VAR** models for multi-tenor analysis
- **Structural break tests** (Chow test, CUSUM)
- **Cointegration tests** across tenors

But for now, AR(1) provides a solid foundation for understanding yield persistence and forecasting difficulty.
