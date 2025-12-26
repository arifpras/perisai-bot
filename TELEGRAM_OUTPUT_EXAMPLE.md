# Telegram Bot Output Example

## Query
User sends via Telegram:
```
/kei forecast yield 10 year next 5 observations
```

## Telegram Bot Response (Two Sequential Messages)

### Message 1: Economist-Style Forecast Tables

Latest 5 observations:
- 2025-12-08: 6.1910
- 2025-12-09: 6.1910
- 2025-12-10: 6.1690
- 2025-12-11: 6.1590
- 2025-12-12: 6.1630

Forecasts:
T+1 (2025-12-15): average=6.1667
```
Model         | Forecast
---------------------------
ARIMA        | 6.1672
ETS          | 6.1585
RANDOM_WALK  | 6.1630
MONTE_CARLO  | 6.1549
MA5          | 6.1746
VAR          | 6.1641
PROPHET      | 6.1854
GRU          | 5.0783
AVERAGE      | 6.1667
```

T+2 (2025-12-16): average=6.1657
```
Model         | Forecast
---------------------------
ARIMA        | 6.1660
ETS          | 6.1539
RANDOM_WALK  | 6.1630
MONTE_CARLO  | 6.1518
MA5          | 6.1746
VAR          | 6.1645
PROPHET      | 6.1865
GRU          | 5.0783
AVERAGE      | 6.1657
```

T+3 (2025-12-17): average=6.1637
```
Model         | Forecast
---------------------------
ARIMA        | 6.1647
ETS          | 6.1494
RANDOM_WALK  | 6.1630
MONTE_CARLO  | 6.1474
MA5          | 6.1746
VAR          | 6.1648
PROPHET      | 6.1829
GRU          | 5.0783
AVERAGE      | 6.1637
```

T+4 (2025-12-18): average=6.1608
```
Model         | Forecast
---------------------------
ARIMA        | 6.1635
ETS          | 6.1448
RANDOM_WALK  | 6.1630
MONTE_CARLO  | 6.1439
MA5          | 6.1746
VAR          | 6.1651
PROPHET      | 6.1732
GRU          | 5.0783
AVERAGE      | 6.1608
```

T+5 (2025-12-19): average=6.1599
```
Model         | Forecast
---------------------------
ARIMA        | 6.1623
ETS          | 6.1403
RANDOM_WALK  | 6.1630
MONTE_CARLO  | 6.1392
MA5          | 6.1746
VAR          | 6.1654
PROPHET      | 6.1769
GRU          | 5.0783
AVERAGE      | 6.1599
```

---

## Display Characteristics

### Format
- **Message 1 (Tables)**: Monospace tables using Telegram code block formatting (triple backticks)
- **Message 2 (Separator)**: Visual break ("---")
- **Message 3 (Analysis)**: Kei's HL-CU format response (headline + 3 paragraphs, plain text)
- **Per-horizon tables** — each T+ forecast date gets its own economist-style table
- **8 models** listed in consistent order: ARIMA, ETS, RANDOM_WALK, MONTE_CARLO, MA5, VAR, PROPHET, GRU
- **AVERAGE row** at bottom showing ensemble average for that horizon

### Content
**Tables Message:**
- **Latest 5 observations** displayed with dates and yields (4 decimal places)
- **T+ labels** (T+1, T+2, etc.) represent business-day offsets:
  - T+1 = next business day (Monday 2025-12-15, after last Friday 2025-12-12 observation)
  - T+2 = Tuesday 2025-12-16
  - T+3 = Wednesday 2025-12-17
  - T+4 = Thursday 2025-12-18
  - T+5 = Friday 2025-12-19
  - (Weekends automatically skipped)

**Analysis Message:**
- Kei analyzes the forecast trends and model drivers
- Cites specific values from the tables (e.g., "1.5bp decline", "ETS mean reversion", "GRU outliers")
- Highlights which models dominate the forecast
- Provides forward-looking context (policy, flows, risk levels)
- HL-CU format: headline, 3 paragraphs max, plain text, no markdown, ends with signature

### Model Behavior
- **ARIMA**: Uses fallback forecasting when primary method (get_forecast) fails on date alignment; always returns a valid forecast using fit.forecast() or last observed value
- **ETS**: Decreasing trend over horizons (6.1585 → 6.1403)
- **RANDOM_WALK**: Constant at last observed value (6.1630)
- **MONTE_CARLO**: Gentle drift (6.1549 → 6.1392)
- **MA5**: Constant (5-day moving average = 6.1746)
- **VAR**: Stable trend (6.1641 → 6.1654)
- **PROPHET**: Clamped to non-negative; slight variations (6.1854 → 6.1769)
- **GRU**: Consistent deep learning prediction (5.0783 across all horizons)
- **AVERAGE**: Ensemble average excludes negatives and 3×MAD outliers; ranges 6.1667 → 6.1599

### Telegram UX
- **Three separate messages** (not one long message):
  1. Forecast tables (monospace, code-block styled)
  2. Separator
  3. Kei's analysis (plain text HL-CU format)
- Tables render cleanly in mobile and desktop Telegram
- Easy to copy-paste forecast values separately from analysis
- Professional appearance combining data transparency + expert insight

---

## Other Query Examples

### Single-Date Forecast
**Query:**
```
/kei forecast yield 10 year 2025-12-20
```

**Output:**
```
Forecasts for 10 year yield at 2025-12-20 (all series (averaged)):
Model         | Forecast
---------------------------
ARIMA        | 6.1612
ETS          | 6.1358
RANDOM_WALK  | 6.1630
MONTE_CARLO  | 6.1347
MA5          | 6.1746
VAR          | 6.1657
PROPHET      | 6.1765
GRU          | 5.0783
AVERAGE      | 6.1612

Ensemble average: 6.1612
```

### Specific Model Only
**Query:**
```
/kei forecast yield 10 year 2025-12-20 use prophet
```

**Output:**
```
Forecast (PROPHET): 10 year yield at 2025-12-20 (all series (averaged)): 6.1765
```

---

## Technical Notes

- Tables use **pipe-delimited format** (` | `) for alignment
- **Right-alignment** of numeric values for readability
- **Header separators** (dashes) for visual clarity
- **Consistent spacing** across all tables for professional appearance
- **No HTML/markdown formatting** — plain monospace only (Telegram compatibility)
- **4 decimal precision** for yield values
