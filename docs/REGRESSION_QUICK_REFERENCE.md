# Regression Analysis: Quick Reference

## Overview

The bot supports comprehensive time-series and econometric analysis for Indonesian government bond yields, including AR(1), multiple regression, Granger causality, VAR models, and event studies. Results include computed statistics, diagnostic tests, and economic interpretation—no vague LLM prose.

---

## Analysis Types

### 1. AR(1) Regression (Autoregressive)

**Model**: y_t = α + β y_{t-1} + ε_t

Measures how much yesterday's yield predicts today's yield (persistence).

**Query patterns**:
```
/kei regression 5 year in 2025
/kei ar1 10 year from jan 2023 to dec 2024
/kei regres 5 year
```

**Output includes**:
- Intercept (α), persistence (β), R²
- Standard errors and p-values
- Normality test (Jarque-Bera)
- Autocorrelation test (Ljung-Box)
- Heteroskedasticity test (ARCH)

**Interpretation**:
- **β ≈ 1.0**: Random walk (hard to forecast)
- **β ≈ 0.5–0.9**: Some mean reversion
- **β < 0.5**: Strong mean reversion (easier to forecast)

---

### 2. Multiple Regression

**Model**: y_t = α + β₁x₁_t + β₂x₂_t + ... + ε_t

Regresses yield on multiple independent variables (other yields, FX rates, volatility).

**Query patterns**:
```
/kei regression 5 year with 10 year and idrusd from 2023 to 2025
/kei regres 5 year with 10 year_lag1 and vix from q1 2023 to q4 2024
```

**Variables available**:
- `10 year`: 10Y bond yield
- `idrusd`: IDR/USD exchange rate
- `vix`: Global volatility index
- `[variable]_lag1`, `[variable]_lag2`, etc.: Lagged versions

**Output includes**:
- Coefficients with SE, t-stats, p-values for each regressor
- R² and adjusted R²
- F-statistic and overall model significance
- Residual correlation matrix
- Diagnostic tests (normality, autocorrelation, heteroskedasticity)

**Interpretation**:
- Coefficient sign and magnitude show directional and quantitative relationships
- p-value < 0.05: Regressor is statistically significant
- R² shows explanatory power (0 = useless, 1 = perfect)

---

### 3. Granger Causality

**Framework**: Does variable X help predict variable Y beyond Y's own history?

**Query patterns**:
```
/kei granger 5 year and idrusd from jan 2023 to dec 2024
/kei granger 5 year and 10 year from 2023 to 2025
```

**Output includes**:
- Stationarity tests (ADF) for each variable
- Granger causality test results at lags 1–5
- F-statistics and p-values for each lag
- Direction of causality (X→Y and Y→X separately)

**Interpretation**:
- p < 0.05 at lag k: X Granger-causes Y at that lag
- Granger causality ≠ true causality (just predictive Granger)
- Non-stationary series: Results may be misleading (check ADF p-values)

**Example result**:
- "5Y Yield Granger-causes IDR/USD at lags 1–5" = past yields help forecast future FX
- "IDR/USD does NOT Granger-cause 5Y at lag 1" = FX doesn't predict yields same day

---

### 4. VAR (Vector Autoregression)

**Framework**: Multi-equation system where each variable depends on lags of all variables.

**Query patterns**:
```
/kei var 5 year and 10 year and vix from 2023 to 2025
/kei var 5 year with idrusd and bi_rate in 2024
```

**Output includes**:
- Lag selection (AIC, BIC)
- Regression coefficients for each equation
- Impulse response functions (IRF): How does a shock to X affect Y over time?
- Forecast error variance decomposition (FEVD): What % of Y's variance is due to X vs Y?
- Residual correlation matrix
- Model diagnostics (log-likelihood, AIC, BIC)

**Key metrics**:
- **IRF**: Traces dynamic response of one variable to a shock in another
- **FEVD**: Variance shares at different horizons (t=0, t=1, ..., t=5)

**Interpretation**:
- "5Y shock: 30% response from 10Y at t=1" = curve shock spillover
- "VIX variance: 60% from yields, 40% from own shocks" = yields drive volatility

---

### 5. Event Study

**Framework**: Isolate abnormal returns around a specific event date using risk-adjusted model.

**Query patterns**:
```
/kei event study 5 year on 2025-09-08 window -5 +5 estimation 90 with market vix method risk
/kei event 10 year on 2024-12-15 window -3 +3 est 60 with market idrusd method risk
```

**Parameters**:
- `on YYYY-MM-DD`: Event date
- `window -X +Y`: Days before and after
- `estimation N`: Number of days for baseline regression
- `with market [VAR]`: Risk factor (vix, idrusd, bi_rate)
- `method risk`: Always "risk" (risk-adjusted abnormal returns)

**Output includes**:
- Estimation window regression: market model coefficients
- Event window daily abnormal returns (actual - expected based on market model)
- t-statistics for each abnormal return
- Pre-event vs post-event cumulative abnormal returns (CAR)
- Significance tests for CAR

**Interpretation**:
- AR (abnormal return) = actual change - (α + β × market factor)
- Positive AR: Yield moved up more than market factor would predict
- Significant CAR: Event had material, persistent effect on yields

---

### 6. ARIMA (Autoregressive Integrated Moving Average)

**Model**: ARIMA(p, d, q) — combines AR, differencing (I), and MA components

Integrates differencing to remove trends, useful for non-stationary series.

**Query patterns**:
```
/kei arima 5 year
/kei arima 10 year p=1 d=1 q=1 from 2023 to 2025
```

**Parameters**:
- `p`: AR order (default 1)
- `d`: Differencing order (default 1)
- `q`: MA order (default 1)

**Output includes**:
- Model coefficients and standard errors
- AIC, BIC, RMSE
- Ljung-Box autocorrelation test (p-value)
- 5-step ahead forecast

**Interpretation**:
- d=0: Use series as-is (already stationary)
- d=1: First difference (removes linear trend)
- High RMSE: Forecast uncertainty
- Low LB p-value (<0.05): Model fits well

---

### 7. GARCH (Generalized Autoregressive Conditional Heteroskedasticity)

**Model**: GARCH(p, q) — models time-varying volatility

Captures volatility clustering (calm → volatile → calm cycles).

**Query patterns**:
```
/kei garch 5 year
/kei garch 10 year p=1 q=1 from 2023 to 2025
```

**Parameters**:
- `p`: Lagged volatility terms (default 1)
- `q`: Lagged squared residual terms (default 1)

**Output includes**:
- Mean, max, min conditional volatility
- Persistence (α + β); <1 = mean-reverting volatility
- 5-day volatility forecast
- AIC, BIC, log-likelihood

**Interpretation**:
- Persistence < 1: Volatility shocks fade (mean-reverting)
- Persistence ≈ 1: Volatility is nearly permanent (long memory)
- High forecast volatility: Expect larger moves ahead

---

### 8. Cointegration (Johansen Test)

**Framework**: Tests for long-run equilibrium relationships between I(1) series

Identifies pairs/groups that move together over time (mean-reverting spread).

**Query patterns**:
```
/kei coint 5 year and 10 year from 2023 to 2025
/kei coint 5 year and idrusd in 2024
```

**Output includes**:
- Cointegrating rank (number of long-run relationships)
- Trace test statistics vs critical values (5%)
- Eigenvalues
- Cointegrating vectors (weights for each variable)

**Interpretation**:
- Rank = 1: One stationary linear combination (one equilibrium)
- Rank = 2: Two independent equilibria
- Cointegrating vector e.g. [1.5, -1]: Spread = 1.5×(5Y) - 1×(10Y) is mean-reverting

---

### 9. Rolling Regression (Time-Varying Parameters)

**Framework**: Regresses y on X using a moving window; coefficients vary over time

Detects structural shifts and parameter instability.

**Query patterns**:
```
/kei rolling 5 year with 10 year window=90 from 2023 to 2025
/kei rolling 5 year with 10 year and vix window=60 in 2024
```

**Parameters**:
- `window`: Size of rolling window in days (default 90)
- Predictors: Variables for regression

**Output includes**:
- Mean and std of rolling coefficients
- Time series of coefficients (if plotted)
- R² over time
- Dates of rolling windows

**Interpretation**:
- Rising coefficient: Relationship strengthening
- Volatile coefficient: Unstable relationship
- Mean coef ± std: Range of typical values

---

### 10. Structural Break Test (Chow Test)

**Framework**: Tests whether a regression's coefficients change at a break point

Detects if the AR(1) persistence changed significantly on a date.

**Query patterns**:
```
/kei chow 5 year from 2023 to 2025
/kei chow 5 year on 2025-09-08 from 2023 to 2025
```

**Parameters**:
- `on YYYY-MM-DD`: Hypothesized break date (midpoint used if not specified)

**Output includes**:
- β before and after break
- Chow F-statistic and p-value
- Significance at 5% level
- R² before/after

**Interpretation**:
- p < 0.05: Structural break is significant (coefficients changed)
- p > 0.05: No break (coefficients stable)
- ß before vs after: Direction/magnitude of shift

---

### 11. Frequency Aggregation

**Framework**: Resamples time series to different frequencies (monthly, quarterly, yearly)

Reduces noise, reveals longer-term patterns.

**Query patterns**:
```
/kei agg 5 year monthly from 2023 to 2025
/kei aggregate 10 year quarterly in 2024
```

**Frequencies**:
- `daily` (D): Keep as-is
- `weekly` (W): Last trading day of each week
- `monthly` (M): Last trading day of each month
- `quarterly` (Q): Last day of each quarter
- `yearly` (Y): End-of-year

**Output includes**:
- Aggregated values with dates
- Mean, std, min, max across periods
- Autocorrelation at aggregated frequency

**Interpretation**:
- Higher frequency → more noise
- Lower frequency → smoother, longer-term trends
- ACF patterns reveal cyclicality

---

## Query Syntax Cheat Sheet

### Tenor/Series
- `5 year`, `10 year`, `2y`, `5y`, `10y`, `fr95`, `fr104`

### Date Ranges
- `in 2025` = full year 2025
- `in q1 2025` = Q1 2025
- `from jan 2023 to dec 2024` = inclusive range
- `from 2023-01-01 to 2024-12-31` = ISO format

### Lags
- `[variable]_lag1` = 1-day lag
- `[variable]_lag2` = 2-day lag
- `[variable]_lag5` = 5-day lag

### Available Variables
- Yields: `5 year`, `10 year`, `2y`, `fr95`, etc.
- FX: `idrusd`, `idr/usd`
- Volatility: `vix`
- Macro: `bi_rate`, `inflation` (if available)

---

## Comprehensive Query Examples

### AR(1) / Autoregressive Examples

**Basic AR(1) — current year**:
```
/kei regression 5 year
/kei ar1 10 year
/kei regres 5 year in 2025
```

**AR(1) with date range**:
```
/kei regression 5 year from 2023 to 2025
/kei regression 10 year from jan 2023 to dec 2024
/kei ar1 5 year from 2024-01-01 to 2024-12-31
```

**AR(1) by quarter**:
```
/kei regression 5 year in q1 2025
/kei ar1 10 year in q2 2024
/kei regression 5 year in q4 2023 to q2 2024
```

---

### Multiple Regression Examples

**Simple: Y on one predictor**:
```
/kei regression 5 year with 10 year
/kei regres 5 year on idrusd
/kei regres 10 year with vix
```

**Multiple: Y on 2+ predictors**:
```
/kei regression 5 year with 10 year and idrusd from 2023 to 2025
/kei regres 5 year on 10 year and vix from 2023 to 2024
/kei regression 5 year with 10 year, idrusd, vix in 2024
```

**With lagged variables**:
```
/kei regres 5 year with 10 year_lag1 and vix from jan 2023 to dec 2024
/kei regression 5 year on 10 year_lag2 and idrusd_lag1 in 2024
/kei regres 5 year with 10 year and vix_lag1 and idrusd_lag2 in q1 2025
```

**Testing curve steepness**:
```
/kei regression 5 year with 10 year from 2023 to 2025
# Coefficient on 10Y measures how much 5Y moves with 10Y (curve co-movement)
```

---

### Granger Causality Examples

**Basic causality test**:
```
/kei granger 5 year and idrusd
/kei granger 5 year and 10 year
/kei granger 10 year and vix
```

**With date range**:
```
/kei granger 5 year and idrusd from 2023 to 2025
/kei granger 5 year and 10 year from jan 2023 to dec 2024
/kei granger 10 year and vix in 2024
```

**Testing different pairs**:
```
/kei granger 5 year and idrusd from 2023 to 2024
# Does 5Y yield help forecast IDR/USD?

/kei granger idrusd and 5 year from 2023 to 2024
# Does IDR/USD help forecast 5Y yield?

/kei granger 5 year and 10 year from 2023 to 2025
# Curve causality: does 5Y lead 10Y or vice versa?
```

---

### VAR (Vector Autoregression) Examples

**Two-variable VAR**:
```
/kei var 5 year and 10 year
/kei var 5 year and idrusd from 2023 to 2025
/kei var 10 year and vix in 2024
```

**Three-variable VAR**:
```
/kei var 5 year and 10 year and vix from 2023 to 2025
/kei var 5 year and 10 year and idrusd in 2024
/kei var 5 year and idrusd and vix from 2023 to 2025
```

**Multi-variable systems**:
```
/kei var 5 year and 10 year and idrusd and vix from 2023 to 2025
# Full yield-FX-volatility system
```

---

### Event Study Examples

**Basic event study**:
```
/kei event study 5 year on 2025-09-08 window -5 +5 estimation 90 with market vix method risk
/kei event 10 year on 2024-12-15 window -3 +3 est 60 with market idrusd method risk
```

**Different windows**:
```
/kei event study 5 year on 2025-06-15 window -10 +10 est 60 with market vix method risk
# Wider window: -10 to +10 days around event

/kei event study 5 year on 2024-03-20 window -1 +1 est 90 with market idrusd method risk
# Tight window: 1 day before/after event

/kei event study 10 year on 2025-01-15 window -20 +20 est 120 with market vix method risk
# Long window with extended estimation
```

**Different risk factors**:
```
/kei event study 5 year on 2025-09-08 window -5 +5 est 90 with market vix method risk
/kei event study 5 year on 2025-09-08 window -5 +5 est 90 with market idrusd method risk
/kei event study 5 year on 2025-09-08 window -5 +5 est 90 with market bi_rate method risk
```

---

### ARIMA Examples

**Default ARIMA(1,1,1)**:
```
/kei arima 5 year
/kei arima 10 year
/kei arima 5 year in 2024
```

**Custom ARIMA orders**:
```
/kei arima 5 year p=2 d=1 q=1
# AR(2), 1st difference, MA(1)

/kei arima 10 year p=1 d=0 q=2
# AR(1), no differencing, MA(2)

/kei arima 5 year p=0 d=1 q=0
# Pure differencing (random walk with drift)
```

**With date ranges**:
```
/kei arima 5 year p=1 d=1 q=1 from 2023 to 2025
/kei arima 10 year p=2 d=1 q=1 from jan 2023 to dec 2024
/kei arima 5 year p=1 d=1 q=1 in 2024
```

---

### GARCH Examples

**Default GARCH(1,1)**:
```
/kei garch 5 year
/kei garch 10 year
/kei garch 5 year in 2024
```

**Custom GARCH orders**:
```
/kei garch 5 year p=2 q=1
# GARCH(2,1): 2 lagged variance terms, 1 lagged residual squared

/kei garch 10 year p=1 q=2
# GARCH(1,2): 1 lagged variance term, 2 lagged residual squared terms
```

**With date ranges**:
```
/kei garch 5 year p=1 q=1 from 2023 to 2025
/kei garch 10 year p=1 q=1 from jan 2023 to dec 2024
/kei garch 5 year p=1 q=1 in 2024
```

---

### Cointegration Examples

**Two-variable pairs**:
```
/kei coint 5 year and 10 year
/kei coint 5 year and idrusd
/kei coint 10 year and vix
```

**Different yield pairs (curve relationships)**:
```
/kei coint 5 year and 10 year from 2023 to 2025
# Test if 5Y-10Y spread is stationary (mean-reverting)

/kei coint 5 year and 2 year in 2024
# Short-end curve mean reversion

/kei coint 2 year and 10 year from 2023 to 2025
# Full curve mean reversion
```

**Cross-asset pairs**:
```
/kei coint 5 year and idrusd from 2023 to 2025
# Yield-FX long-run relationship

/kei coint 10 year and vix from 2023 to 2024
# Bond-volatility long-run relationship
```

---

### Rolling Regression Examples

**Basic rolling regression**:
```
/kei rolling 5 year with 10 year
/kei rolling 5 year with idrusd window=90
```

**Multiple predictors with custom window**:
```
/kei rolling 5 year with 10 year window=90 from 2023 to 2025
/kei rolling 5 year with 10 year and vix window=60 in 2024
/kei rolling 5 year with 10 year and idrusd and vix window=120 from 2023 to 2025
```

**Different window sizes (shorter = more sensitive)**:
```
/kei rolling 5 year with 10 year window=30
# 30-day window: very responsive to changes

/kei rolling 5 year with 10 year window=90
# 90-day (quarterly) window: moderate sensitivity

/kei rolling 5 year with 10 year window=252
# ~1 year window: longer-term trends
```

---

### Structural Break Examples

**Default (tests midpoint)**:
```
/kei chow 5 year
/kei chow 10 year in 2024
```

**Specific break date**:
```
/kei chow 5 year on 2025-09-08
# Test for break at specific date (e.g., policy announcement)

/kei chow 10 year on 2024-12-15 from 2023 to 2025
/kei chow 5 year on 2024-06-01 in 2024
```

**Detecting regime changes**:
```
/kei chow 5 year from 2023 to 2025
# Auto-detect break at midpoint (Dec 2023)

/kei chow 5 year from 2023 to 2025 on 2024-03-20
# Test specific event date within period
```

---

### Frequency Aggregation Examples

**Monthly aggregation**:
```
/kei agg 5 year monthly
/kei agg 5 year monthly from 2023 to 2025
/kei agg 10 year monthly in 2024
```

**Different frequencies**:
```
/kei agg 5 year weekly
# Last trading day of each week

/kei agg 5 year quarterly
# End of quarter

/kei agg 5 year yearly
# End of year

/kei agg 5 year monthly
# End of month
```

**With date ranges**:
```
/kei aggregate 5 year monthly from jan 2023 to dec 2024
/kei agg 10 year quarterly from 2023 to 2025
/kei aggregate 5 year yearly in 2024
```

---

## Common Workflows

### Workflow 1: Is the yield mean-reverting?
```
Step 1: /kei regression 5 year from 2023 to 2025
        → Check if β ≈ 1.0 (random walk) or β < 0.9 (mean-reverting)

Step 2: /kei coint 5 year and 10 year from 2023 to 2025
        → Check if curve spread is stationary (mean-reverting)
```

### Workflow 2: Monitor relationship stability
```
Step 1: /kei rolling 5 year with 10 year window=90 from 2023 to 2025
        → See how curve beta changes over time

Step 2: /kei chow 5 year on [EVENT_DATE] from 2023 to 2025
        → Test for structural break at specific event
```

### Workflow 3: Model volatility
```
Step 1: /kei garch 5 year p=1 q=1 from 2023 to 2025
        → Estimate volatility model

Step 2: /kei var 5 year and 10 year and vix from 2023 to 2025
        → See how volatility shocks propagate through curve
```

### Workflow 4: Analyze long-term patterns
```
Step 1: /kei arima 5 year p=1 d=1 q=1 from 2023 to 2025
        → Model non-stationary yield with differencing

Step 2: /kei agg 5 year quarterly from 2023 to 2025
        → View quarterly trends (smoothed)

Step 3: /kei coint 5 year and 10 year from 2023 to 2025
        → Check if spread reverts at quarterly frequency
```

### Workflow 5: Event impact analysis
```
Step 1: /kei event study 5 year on 2025-09-08 window -5 +5 est 90 with market vix method risk
        → Measure abnormal yield move around event

Step 2: /kei granger 5 year and vix from 2023 to 2025
        → Check if VIX predicts yields (test pre-existing relationship)

Step 3: /kei rolling 5 year with vix window=90 from 2023 to 2025
        → See if yield-VIX sensitivity changed after event
```

---

### 1. Harvard-Style Headline
```
📊 INDOGB 5Y: AR(1) Persistence Analysis; Jan 2023–Dec 2024
```
Brief headline with emoji, instrument, period.

### 2. Hook (Harvard-style insight)
```
📚 Blockquote: "Indonesian 5Y yields show very high persistence (β ≈ 0.99), 
indicating little mean reversion and near-random walk behavior over 2023–2024."
```
Key finding extracted from first sentence of analysis.

### 3. Body (3 paragraphs, ≤152 words)
Plain text analysis with specific numbers, no markdown or bullets.

### 4. Signature
```
<blockquote>~ Kei</blockquote>
```
HTML-formatted signature.

---

## Interpretation Examples

### High R² + High β
```
R² = 0.98, β = 0.995
```
→ Yields are very persistent and predictable short-term, but shocks last a long time.

### High R² + Low β
```
R² = 0.92, β = 0.65
```
→ Yields show mean reversion; yesterday's level predicts today with strong mean reversion.

### Low R² + High β
```
R² = 0.10, β = 0.98
```
→ Random walk with large noise; hard to forecast short-term moves.

### Granger Causality: Asymmetric
```
5Y → IDR/USD: p = 0.001 ✓ (highly significant)
IDR/USD → 5Y: p = 0.12 ✗ (not significant)
```
→ Yields lead currency; FX doesn't help forecast bonds (in this period).

### VAR: FEVD
```
5Y variance: 50% from own shocks, 50% from 10Y at t=1
```
→ Curve co-moves equally; 5Y is heavily exposed to 10Y surprises.

### Event Study: Post-Event CAR
```
CAR (t=1 to t=5) = +15.2 bp
t-stat = 2.34, p = 0.021 ✓
```
→ Yields rose abnormally (statistically significant) for 5 days post-event.

---

## Diagnostic Tests Guide

### Jarque-Bera (Normality)
- **H₀**: Residuals ~ N(0, σ²)
- **p < 0.05**: Non-normal (fat tails, skewness)
- **Implication**: Extreme moves happen more often than Gaussian model predicts

### Ljung-Box (Autocorrelation)
- **H₀**: No autocorrelation in residuals
- **p < 0.05**: Residuals are correlated; AR(1) insufficient
- **Solution**: Add lags, try ARMA, consider GARCH

### ARCH (Heteroskedasticity)
- **H₀**: Constant variance
- **p < 0.05**: Volatility clustering (calm → volatile → calm)
- **Implication**: Volatility is time-varying; consider GARCH

### ADF (Augmented Dickey-Fuller)
- **H₀**: Unit root (non-stationary)
- **p < 0.05**: Series is stationary
- **Implication**: p > 0.05 in level → use differences for Granger/VAR

---

## Technical Details

### Standard Errors
- **HC0 robust**: Accounts for heteroskedasticity; valid even if ARCH test fails
- Always used for reliable inference with changing volatility

### Minimum Data
- AR(1): ≥10 observations (preferably ≥60)
- Multiple regression: ≥3×(number of regressors)
- Granger causality: ≥30 for each series
- VAR: ≥50 observations
- Event study: ≥30 in estimation window

### Lags & Horizons
- **Granger**: Tests lags 1–5 unless specified
- **VAR**: Selects via AIC; typically 1–3 lags
- **Event study**: IRF/FEVD computed to 5–10 periods
- **FEVD**: Shows variance shares at each horizon

### Missing Data
- Automatically handled via daily aggregation
- If tenor unavailable, bot will report and skip
- Dates merged on trading day alignment

---

## Files & Code

### Core Modules
- **`regression_analysis.py`**: Regression, Granger, VAR, event study functions
- **`telegram_bot.py`**: Query parsing, persona integration, output formatting

### Key Functions
- `ar1_regression(series, start_date, end_date)`: AR(1) model
- `multiple_regression(y_series, X_dict, start_date, end_date)`: OLS regression
- `granger_causality_test(series_dict, maxlag, date_range)`: Granger tests
- `var_analysis(variables_dict, lags, date_range)`: VAR with IRF/FEVD
- `event_study(y_series, market_series, event_date, window, est_window)`: Event study

---

## Common Queries & Expected Output

### Query 1: Is 5Y persistent?
```
/kei regression 5 year from 2023 to 2025
```
**Expected**: β ≈ 0.99, p < 0.001, R² ≈ 0.95–0.98
**Meaning**: Yields are nearly random walk; little mean reversion

### Query 2: Do 5Y and 10Y move together?
```
/kei regression 5 year with 10 year from 2023 to 2025
```
**Expected**: β₁ (10Y coeff) ≈ 0.45–0.80, p < 0.001, R² ≈ 0.85–0.95
**Meaning**: 10Y strongly predicts 5Y; curve co-moves

### Query 3: Do currencies affect bonds?
```
/kei granger 5 year and idrusd from 2023 to 2024
```
**Expected**: 5Y → IDR/USD significant, IDR/USD → 5Y not significant
**Meaning**: Yields lead currency; carry trade feedback

### Query 4: What's the curve response to VIX?
```
/kei var 5 year and 10 year and vix from 2023 to 2025
```
**Expected**: 5Y, 10Y spike on VIX shock; VIX responds to curve moves
**Meaning**: Flight-to-safety (rates ↑) but yields also predict volatility

### Query 5: How big was the Sept 2025 surprise?
```
/kei event study 5 year on 2025-09-08 window -5 +5 estimation 90 with market vix method risk
```
**Expected**: CAR post-event ≠ 0, t-stat significant
**Meaning**: Event moved yields beyond what market volatility would explain

---

## Comparison: Before vs. After

### Before (Vague)
```
The AR(1) model shows β ≈ 1.0, indicating strong persistence. 
Residuals appear approximately normal with no obvious autocorrelation.
```
❌ Rounded (β ≈ 1.0)
❌ Vague language ("appear approximately")
❌ No test statistics

### After (Precise)
```
β = 0.995501 (SE: 0.005250, t=189.5, p < 0.0001) ***
Normality: Rejected (JB stat 155.48, p < 0.0001)
Autocorrelation: Detected (LB p = 0.0000)
```
✅ Exact values with full precision
✅ Standard errors and significance
✅ Formal test results with p-values

---

## Next Steps / Future Features

- **Multivariate GARCH**: Time-varying correlations across yields and FX
- **Wavelet analysis**: Frequency-domain decomposition of yield dynamics
- **Machine learning forecasting**: Neural networks, random forests for forecasting
- **Stress testing**: Portfolio sensitivity to rate shocks
- **Cross-asset analysis**: Equity-bond-FX correlations
