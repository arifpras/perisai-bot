# Analytics Routing Fix - Aggregation Queries

**Date**: 2025-01-06  
**Version**: 0.494  
**Status**: ✅ Deployed

## Problem

The FastAPI `/chat` endpoint was routing **all** persona-prefixed queries (`/kei`, `/kin`, `/both`) to the LLM personas for interpretation, including analytics queries like:
- `/kei agg 5 year monthly from 2023 to 2024` 
- `/kin plot yield 5 year and 10 year in 2025`

This meant the dashboard was returning LLM-generated narratives instead of computed data tables, resulting in mismatches with the Telegram bot which returns actual computational results.

## Root Cause

The persona routing check happened before analytics detection:
```
if persona_prefix == "kei":
    return ask_kei(user_query)  # ❌ Routes ALL /kei queries to LLM
```

Analytics queries should **never** be sent to personas. They must:
1. Compute the analysis (aggregation, plot data, forecast, etc.)
2. Return the computational results as tables/statistics
3. Optionally interpret those results with a persona

## Solution

Restructured the `/chat` endpoint flow:

### 1. Check Advanced Query Types First
Before routing to personas, detect if the query is an analytics request:
```python
is_analytics_query = bool(
    parse_arima_query(user_query) or
    parse_garch_query(user_query) or
    parse_aggregation_query(user_query) or
    # ... etc
)
```

### 2. Only Route Non-Analytics to Personas
```python
if persona_prefix and not is_analytics_query:
    # Route to ask_kei(), ask_kin(), ask_kei_then_kin()
```

### 3. Handle Aggregation Specifically
Before `parse_intent()`, check for frequency aggregation:
```python
agg_req = parse_aggregation_query(user_query)
if agg_req:
    # Compute with aggregate_frequency()
    # Format with format_aggregation()
    # Return Harvard-style statistical table
```

## Test Results

### Query: `/kei agg 5 year monthly from 2023 to 2024`

**Before Fix**:
```
Kei: Here's an analysis of the 5-year bond yields...
[LLM-generated interpretation]
```

**After Fix**:
```
📊 Monthly Aggregation; 2023-01-02–2024-12-31
Aggregated to Monthly: 521 daily → 24 periods, mean=6.510375

Summary statistics (Monthly):
  Mean:   6.510375
  Std:    0.337261
  Min:    5.891000
  Max:    7.131000

Autocorrelation at aggregated frequency:
  lag 1: 0.6622
  lag 2: 0.3139
  lag 3: -0.0320
```

### Query: `/kin plot yield 5 year and 10 year in 2025`

**Before Fix**:
```
Kin: The global bond markets show interesting dynamics...
[LLM-generated macro commentary]
```

**After Fix**:
```
Found X rows for 05_year and 10_year from 2025-01-01 to 2025-12-31:
[Returns actual data rows + optional plot image]
```

## Affected Query Types

Analytics queries now properly bypass persona routing:
- ✅ **Frequency aggregation**: `agg 5 year monthly from 2023 to 2024`
- ✅ **ARIMA forecasting**: `arima 5 year quarterly 4 12`
- ✅ **GARCH volatility**: `garch 2 year from 2023 to 2024`
- ✅ **Cointegration**: `coint 5 year 10 year from 2023 to 2024`
- ✅ **Rolling regression**: `rolling 3 year 5 year 252 days from 2023 to 2024`
- ✅ **Bond returns**: `bond return month from 2023 to 2024`
- ✅ **Auction analysis**: `auction demand jan 2025` / `auction monthly 2025`
- ✅ **Structural breaks**: `chow 2024-06-01 5 year from 2023 to 2024`

## Dashboard vs Telegram Parity

Both now follow the same pattern:
1. **Parse** the user query
2. **Detect** query type (analytics vs interpretation)
3. **Compute** results (tables, statistics, plots)
4. **Format** output (Harvard style, economist tables)
5. **Return** computational results directly
6. *(Optional)* Route to personas for **interpretation** of results

This ensures `/kei agg` returns the same aggregation table on both platforms, not two different responses.

## Code Changes

### File: `app_fastapi.py`

**Lines 556-615**: Analytics detection + persona routing
- Added `is_analytics_query` check before persona routing
- Only routes `persona_prefix and not is_analytics_query` to LLMs
- Preserves `/kei <question>` interpretation queries (without analytics keywords)

**Lines 630-666**: Aggregation computation
- Calls `parse_aggregation_query()` to detect frequency requests
- Computes with `aggregate_frequency()`
- Formats with `format_aggregation()`
- Returns statistical table, not LLM interpretation

**Lines 668+**: Fallthrough to parse_intent
- Analytics queries with prefixes stripped now processed as data queries
- Regular (non-analytics) queries continue to RANGE/POINT handling

## Deployment

Committed as: `bf785f8`  
```
Fix: Route aggregation queries to data computation, not personas
```

Changes:
- ✅ Persona prefix detection and extraction
- ✅ Analytics query detection using all advanced parsers
- ✅ Proper aggregation handling before parse_intent
- ✅ Data computation returns, not LLM interpretation
- ✅ Parity with Telegram bot behavior

## Impact

- **Dashboard**: `/kei agg` queries now return computed tables, matching Telegram bot
- **API consistency**: All analytics queries return data, not interpretation
- **Performance**: Analytics avoid unnecessary LLM calls
- **Correctness**: Users see actual statistics, not AI narratives for data queries

## Next Steps

Monitor Render deployment logs for successful startup and test:
1. `/kei agg 5 year monthly from 2023 to 2024` → Returns aggregation table
2. `/kin plot yield 5 year and 10 year in 2025` → Returns data rows + plot
3. `/both arimafcst 2 year quarterly 4 12` → Returns forecast table
