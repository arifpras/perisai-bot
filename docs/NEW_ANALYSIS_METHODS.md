# New Analysis Methods for /kei Command

## Summary

Added 6 new advanced regression and time-series analysis methods to the bot's regression capabilities. These complement the existing AR(1), multiple regression, Granger causality, VAR, and event study analyses.

---

## New Methods

### 1. ARIMA (Autoregressive Integrated Moving Average)

**Purpose**: Handle non-stationary series through differencing and forecast yields

**Query syntax**:
```
/kei arima 5 year
/kei arima 10 year p=1 d=1 q=1 from 2023 to 2025
```

**Implementation**:
- Function: `arima_model()` in regression_analysis.py
- Formatter: `format_arima()` for Harvard-style output
- Parser: `parse_arima_query()` in telegram_bot.py
- Handler: Full integration in kei_command() with data loading, error handling, logging

**Output**:
- Model coefficients with p-values
- AIC, BIC, RMSE diagnostics
- Ljung-Box autocorrelation test
- 5-step ahead forecast

---

### 2. GARCH (Generalized Autoregressive Conditional Heteroskedasticity)

**Purpose**: Model time-varying volatility and forecast yield volatility

**Query syntax**:
```
/kei garch 5 year
/kei garch 10 year p=1 q=1 from 2023 to 2025
```

**Implementation**:
- Function: `garch_volatility()` in regression_analysis.py
- Formatter: `format_garch()` for Harvard-style output
- Parser: `parse_garch_query()` in telegram_bot.py
- Handler: Full integration with arch package support
- Note: Requires `arch` package (pip install arch)

**Output**:
- Mean, max, min conditional volatility
- Persistence metric (α + β)
- 5-day volatility forecast
- AIC, BIC, log-likelihood

---

### 3. Cointegration (Johansen Test)

**Purpose**: Test for long-run equilibrium relationships between yield pairs

**Query syntax**:
```
/kei coint 5 year and 10 year from 2023 to 2025
/kei coint 5 year and idrusd in 2024
```

**Implementation**:
- Function: `cointegration_test()` in regression_analysis.py
- Formatter: `format_cointegration()` for Harvard-style output
- Parser: `parse_cointegration_query()` in telegram_bot.py
- Handler: Full integration with automatic series loading (yields, FX, VIX)

**Output**:
- Cointegrating rank
- Trace test statistics vs 5% critical values
- Eigenvalues
- Cointegrating vectors

---

### 4. Rolling Regression (Time-Varying Parameters)

**Purpose**: Detect structural shifts by regressing with moving window

**Query syntax**:
```
/kei rolling 5 year with 10 year window=90 from 2023 to 2025
/kei rolling 5 year with 10 year and vix window=60 in 2024
```

**Implementation**:
- Function: `rolling_regression()` in regression_analysis.py
- Formatter: `format_rolling_regression()` for Harvard-style output
- Parser: `parse_rolling_query()` in telegram_bot.py
- Handler: Full integration with configurable window size

**Output**:
- Mean and std of rolling coefficients over time
- Rolling R² series
- Dates of each window
- Coefficient instability indicators

---

### 5. Structural Break Test (Chow Test)

**Purpose**: Formally test whether AR(1) coefficients changed at a hypothesized break point

**Query syntax**:
```
/kei chow 5 year from 2023 to 2025
/kei chow 5 year on 2025-09-08 from 2023 to 2025
```

**Implementation**:
- Function: `structural_break_test()` in regression_analysis.py
- Formatter: `format_structural_break()` for Harvard-style output
- Parser: `parse_structural_break_query()` in telegram_bot.py
- Handler: Full integration with automatic break date detection (midpoint if not specified)

**Output**:
- Chow F-statistic and p-value
- β before and after break point
- R² before, after, and full sample
- Significance test result (5% level)

---

### 6. Frequency Aggregation

**Purpose**: Resample daily yields to weekly, monthly, quarterly, or yearly frequency

**Query syntax**:
```
/kei agg 5 year monthly from 2023 to 2025
/kei aggregate 10 year quarterly in 2024
```

**Implementation**:
- Function: `aggregate_frequency()` in regression_analysis.py
- Formatter: `format_aggregation()` for Harvard-style output
- Parser: `parse_aggregation_query()` in telegram_bot.py
- Handler: Full integration with frequency selection (D, W, M, Q, Y)

**Output**:
- Aggregated series with dates
- Summary statistics (mean, std, min, max)
- Autocorrelation at aggregated frequency
- Original vs aggregated counts

---

## Technical Details

### File Changes

**regression_analysis.py** (1159 → 1390+ lines):
- Added 6 model functions (arima_model, garch_volatility, cointegration_test, rolling_regression, structural_break_test, aggregate_frequency)
- Added 6 formatter functions (format_arima, format_garch, format_cointegration, format_rolling_regression, format_structural_break, format_aggregation)
- All formatters follow Harvard-style HL-CU format (headline + blockquoted hook + body)

**telegram_bot.py** (7925 → 8305+ lines):
- Added 6 parser functions (parse_arima_query, parse_garch_query, parse_cointegration_query, parse_rolling_query, parse_structural_break_query, parse_aggregation_query)
- Added 6 command handlers in kei_command() with:
  - Typing indicator
  - Series data loading from database
  - Error handling and validation
  - Metrics logging
  - HTML response formatting

**docs/REGRESSION_QUICK_REFERENCE.md** (377 → 650+ lines):
- Added comprehensive sections for each new method
- Query patterns and examples
- Output descriptions
- Interpretation guidelines
- Updated "Future Features" section

---

## Query Syntax Patterns

All new methods support consistent date range syntax:

```
/kei [method] [tenor] [parameters] from [start] to [end]
/kei [method] [tenor] [parameters] in [period]
```

**Date range examples**:
- `from 2023 to 2025` → Jan 1, 2023 to Dec 31, 2025
- `from jan 2023 to dec 2024` → Jan 1, 2023 to Dec 31, 2024
- `in 2025` → Full year 2025
- `in q1 2025` → Q1 2025
- `in jan 2025` → January 2025

---

## Data Sources

All methods automatically load data from:

1. **Bond yields**: `/workspaces/perisai-bot/database/` (5Y/10Y via SQL database)
2. **FX rates**: `/workspaces/perisai-bot/database/idrusd.csv` (IDR/USD)
3. **VIX**: `/workspaces/perisai-bot/database/vix.csv` (Global volatility index)

---

## Testing

All implementations:
- ✅ Pass Python syntax validation (`py_compile`)
- ✅ Handle missing data gracefully
- ✅ Validate minimum observation requirements
- ✅ Return informative error messages
- ✅ Log all queries for monitoring
- ✅ Follow consistent output formatting

---

## Dependencies

**New dependencies**:
- `arch` package (for GARCH) — `pip install arch`

**Existing dependencies**:
- `pandas`, `numpy`, `statsmodels`, `scipy`

---

## Next Steps

Users can now:
1. Model non-stationary yields with **ARIMA**
2. Forecast volatility with **GARCH**
3. Test for yield curve mean reversion via **Cointegration**
4. Monitor parameter stability via **Rolling Regression**
5. Detect regime changes via **Chow Test**
6. Analyze longer-term trends via **Frequency Aggregation**

All methods integrate seamlessly with existing `/kei` query infrastructure and Harvard-style output formatting.
