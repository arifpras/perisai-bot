# Quick Prompt Examples for /kei Regression Analysis

## Essential One-Liners

### Check Persistence
```
/kei regression 5 year
```
→ Is the 5Y yield a random walk or mean-reverting?

### Check Curve Co-movement
```
/kei regression 5 year with 10 year
```
→ How much does 5Y move with 10Y?

### Check Yield-FX Link
```
/kei granger 5 year and idrusd from 2023 to 2025
```
→ Do yields help predict currency moves?

### Check Volatility Model
```
/kei garch 5 year
```
→ What's the current volatility forecast?

### Check Long-run Spread
```
/kei coint 5 year and 10 year
```
→ Does the 5Y-10Y spread mean-revert?

---

## By Time Period

### Current Year Only
```
/kei regression 5 year in 2025
/kei var 5 year and 10 year
/kei garch 10 year
```

### Full Year
```
/kei regression 5 year in 2024
/kei rolling 5 year with 10 year window=90 in 2024
/kei chow 5 year in 2024
```

### Multi-Year
```
/kei regression 5 year from 2023 to 2025
/kei granger 5 year and idrusd from 2023 to 2025
/kei var 5 year and 10 year and vix from 2023 to 2025
```

### Quarterly
```
/kei regression 5 year in q1 2025
/kei regression 5 year in q2 2024
/kei rolling 5 year with 10 year window=90 in q1 2025
```

### Specific Months
```
/kei regression 5 year from jan 2023 to dec 2024
/kei garch 10 year from mar 2023 to sep 2024
/kei arima 5 year from jan 2024 to jun 2024
```

---

## By Analysis Type

### Simple Univariate
```
/kei regression 5 year
/kei arima 5 year
/kei garch 10 year
/kei agg 5 year monthly
```

### Bivariate (2 variables)
```
/kei regression 5 year with 10 year
/kei granger 5 year and idrusd
/kei coint 5 year and 10 year
/kei rolling 5 year with 10 year window=90
/kei var 5 year and 10 year
```

### Multivariate (3+ variables)
```
/kei regression 5 year with 10 year and vix and idrusd
/kei var 5 year and 10 year and vix
/kei var 5 year and 10 year and idrusd and vix
/kei rolling 5 year with 10 year and vix window=90
```

---

## By Economic Question

### "Is the yield sticky/predictable?"
```
/kei regression 5 year from 2023 to 2025
# Check β (persistence) — close to 1 = sticky, <0.8 = mean-reverting
```

### "Does the curve co-move?"
```
/kei regression 5 year with 10 year from 2023 to 2025
# Check coefficient on 10Y — high = co-move, low = diverge
```

### "Does FX drive yields?"
```
/kei granger 5 year and idrusd from 2023 to 2024
/kei regression 5 year with idrusd from 2023 to 2025
# Granger = predictive; Regression = direct linkage
```

### "Are yields and volatility linked?"
```
/kei granger 5 year and vix from 2023 to 2025
/kei var 5 year and vix from 2023 to 2025
# Check impulse response of yields to VIX shocks
```

### "Is the curve mean-reverting?"
```
/kei coint 5 year and 10 year from 2023 to 2025
# Rank > 0 = cointegrated = mean-reverting spread
```

### "Did something change?"
```
/kei chow 5 year on [DATE] from 2023 to 2025
/kei rolling 5 year with 10 year window=90 from 2023 to 2025
# Chow = formal test; Rolling = visual inspection
```

### "What's the volatility forecast?"
```
/kei garch 5 year from 2023 to 2025
# Returns 5-day volatility forecast
```

### "What about longer-term trends?"
```
/kei agg 5 year quarterly from 2023 to 2025
/kei arima 5 year p=1 d=1 q=1 from 2023 to 2025
# Aggregation = smoothing; ARIMA = trend + differencing
```

---

## By Variable Pair

### Curve Analysis
```
/kei regression 5 year with 10 year              # Co-movement
/kei coint 5 year and 10 year                    # Long-run spread
/kei granger 5 year and 10 year                  # Causality
/kei rolling 5 year with 10 year window=90       # Changing relationship
/kei var 5 year and 10 year                      # Impulse responses
```

### Yield-FX Analysis
```
/kei regression 5 year with idrusd               # Direct link
/kei granger 5 year and idrusd                   # Predictive link
/kei rolling 5 year with idrusd window=90        # Stability over time
/kei coint 5 year and idrusd                     # Long-run relationship
/kei var 5 year and idrusd                       # Shock transmission
```

### Yield-Volatility Analysis
```
/kei regression 5 year with vix                  # Current sensitivity
/kei granger 5 year and vix                      # Risk spillover
/kei rolling 5 year with vix window=90           # Time-varying sensitivity
/kei var 5 year and vix                          # Shock responses
```

### Multi-Asset System
```
/kei var 5 year and 10 year and vix              # 3-asset system
/kei var 5 year and 10 year and idrusd           # Curve + FX
/kei var 5 year and idrusd and vix               # Yield + FX + Vol
/kei var 5 year and 10 year and idrusd and vix   # Full system
```

---

## By ARIMA Order

### Standard (default)
```
/kei arima 5 year
# ARIMA(1,1,1) — 1 lag, 1st diff, 1 MA term
```

### Non-stationary (no differencing)
```
/kei arima 5 year p=1 d=0 q=1
# Series already stationary; skip differencing
```

### Pure Random Walk
```
/kei arima 5 year p=0 d=1 q=0
# Just differencing (no AR or MA)
```

### Stronger AR Component
```
/kei arima 5 year p=2 d=1 q=1
# 2 lags of AR term — for more persistent series
```

### Stronger MA Component
```
/kei arima 5 year p=1 d=1 q=2
# 2 MA terms — for more mean-reverting series
```

---

## By GARCH Order

### Standard (default)
```
/kei garch 5 year
# GARCH(1,1) — baseline volatility model
```

### More Persistence
```
/kei garch 5 year p=2 q=1
# GARCH(2,1) — longer volatility memory
```

### More Responsiveness
```
/kei garch 5 year p=1 q=2
# GARCH(1,2) — faster reaction to shocks
```

---

## By Rolling Window

### Fast Response (30-day)
```
/kei rolling 5 year with 10 year window=30
# Captures short-term relationship changes
```

### Balanced (90-day)
```
/kei rolling 5 year with 10 year window=90
# Standard quarterly window
```

### Trend-Focused (252-day)
```
/kei rolling 5 year with 10 year window=252
# ~1 year window; ignores short-term noise
```

---

## By Frequency

### Daily (original)
```
/kei agg 5 year daily
# Keep daily frequency
```

### Weekly
```
/kei agg 5 year weekly
# Last trading day of week
```

### Monthly
```
/kei agg 5 year monthly
# Last trading day of month
```

### Quarterly
```
/kei agg 5 year quarterly
# End of quarter
```

### Yearly
```
/kei agg 5 year yearly
# End of year
```

---

## Testing Event Impact

### Before-Event Setup
```
/kei rolling 5 year with 10 year window=90 from 2023 to 2025-09-01
# Establish pre-event baseline
```

### Event Analysis
```
/kei event study 5 year on 2025-09-08 window -5 +5 est 90 with market vix method risk
# Measure abnormal return around event
```

### Post-Event Check
```
/kei rolling 5 year with 10 year window=90 from 2025-09-01 to 2025-12-31
# Did relationship change after event?
```

### Statistical Confirmation
```
/kei chow 5 year on 2025-09-08 from 2023 to 2025
# Formal test: did coefficients change?
```

---

## Quick Troubleshooting

### "Not enough data"
```
✗ /kei regression 5 year in jan 2025  # Only 20 observations
✓ /kei regression 5 year from 2023 to 2025  # 500+ observations
```

### "Variable not found"
```
✗ /kei regression 5yr  # Wrong format
✓ /kei regression 5 year  # Correct format

✗ /kei regression 5 year with rate  # Wrong variable name
✓ /kei regression 5 year with 10 year  # Correct variable
```

### "Cointegration failed"
```
✗ /kei coint 5 year and 10 year in jan 2025  # Too few obs
✓ /kei coint 5 year and 10 year from 2023 to 2025  # Enough obs
```

### "GARCH error"
```
✗ /kei garch 5 year  # (arch package not installed)
→ Install: pip install arch
✓ /kei garch 5 year  # Works after install
```

---

## Copy-Paste Templates

### Comprehensive Curve Analysis
```
/kei regression 5 year with 10 year from 2023 to 2025
/kei coint 5 year and 10 year from 2023 to 2025
/kei granger 5 year and 10 year from 2023 to 2025
/kei rolling 5 year with 10 year window=90 from 2023 to 2025
/kei var 5 year and 10 year from 2023 to 2025
```

### Full Yield-FX-Vol System
```
/kei var 5 year and 10 year and idrusd and vix from 2023 to 2025
/kei rolling 5 year with 10 year and idrusd and vix window=90 from 2023 to 2025
/kei granger 5 year and idrusd from 2023 to 2025
/kei granger 5 year and vix from 2023 to 2025
```

### Event Study Protocol
```
/kei event study 5 year on 2025-09-08 window -5 +5 est 90 with market vix method risk
/kei chow 5 year on 2025-09-08 from 2023 to 2025
/kei rolling 5 year with vix window=90 from 2023 to 2025
/kei granger 5 year and vix from 2023 to 2025
```

### Volatility Analysis Suite
```
/kei garch 5 year from 2023 to 2025
/kei garch 10 year from 2023 to 2025
/kei var 5 year and 10 year and vix from 2023 to 2025
/kei granger 5 year and vix from 2023 to 2025
```

---
