# Macro Series Comparison Feature (v.0455-0.456)

## Overview

The macro series comparison feature allows users to compare multiple macroeconomic time series side-by-side in economist-style formatted tables. This feature has been newly added to the Perisai bot and supports flexible query patterns for comparing IDR/USD exchange rates and VIX volatility index.

## Feature Implementation

### Components Added

#### 1. Parser: `parse_macro_comparison_query()` (telegram_bot.py, lines 2599-2716)
- **Location**: `/workspaces/perisai-bot/telegram_bot.py`
- **Function**: Parses user queries to extract series names and date ranges
- **Input**: Query string (e.g., "tab idrusd and vix in jan 2024")
- **Output**: Dictionary with `series` list and date range (`start_date`, `end_date`)
- **Supported Patterns**:
  - Month: `tab SERIES1 and SERIES2 in JAN 2024`
  - From-to range: `tab SERIES1 and SERIES2 from DEC 2023 to JAN 2024`
  - Year: `tab SERIES1 and SERIES2 in 2024`
  - Quarter: `tab SERIES1 and SERIES2 in Q1 2024`
  - ISO date: `tab SERIES1 and SERIES2 in 2024-01-15`

#### 2. Formatter: `format_macro_comparison_table()` (macro_data_tables.py, lines 327-409)
- **Location**: `/workspaces/perisai-bot/macro_data_tables.py`
- **Function**: Formats comparison data into economist-style table with statistics
- **Input**: Start date, end date, series list (e.g., `['idrusd', 'vix']`)
- **Output**: Pre-formatted text table with:
  - All business days in the specified period
  - Series data in proper numeric format (IDR/USD as integers, VIX as 2 decimals)
  - Statistics row: Count, Min, Max, Avg, Std
- **Special Features**:
  - Handles missing data (holidays) automatically
  - Validates series names (idrusd, fx, vix)
  - Deduplicates series if user specifies same series twice
  - Returns appropriate error messages for edge cases

#### 3. Handler: Macro Comparison Query Handler (telegram_bot.py, lines 5865-5897)
- **Location**: `/workspaces/perisai-bot/telegram_bot.py` in `kei_command()` function
- **Trigger**: `parse_macro_comparison_query()` returns a match
- **Flow**:
  1. Parse query with `parse_macro_comparison_query()`
  2. Create `MacroDataFormatter` instance
  3. Call `format_macro_comparison_table()` with extracted parameters
  4. Format response with headline, hook, table, and signature
  5. Send via Telegram with HTML parsing
  6. Log metrics for analytics
- **Error Handling**: Catches and logs exceptions, returns error messages to user

## Query Syntax

### Supported Series Names
- **IDR/USD**: `idrusd`, `fx` (fx is an alias)
- **VIX**: `vix`, `vix_index`

### Date Period Formats

| Format | Example | Result |
|--------|---------|--------|
| Month-Year | `jan 2024`, `january 2024` | Full calendar month |
| Quarter | `q1 2024`, `q2 2024` | Calendar quarter (3 months) |
| Year | `2024` | Full calendar year |
| ISO Date | `2024-01-15` | Single date (or full day if range) |
| From-To Range | `from dec 2023 to jan 2024` | Combined period (start month to end month) |

### Example Queries

```
/kei tab idrusd and vix in jan 2024
/kei tab vix and idrusd from dec 2023 to jan 2024
/kei tab fx and vix in q1 2024
/kei tab idrusd and vix in 2024
/kei tab vix and fx in 2024-01-15
```

## Sample Output

```
📊 Comparison: IDR/USD & VIX

Window: 2024-01-01 to 2024-01-31

```
┌─────────────┬─────────┬───────┐
│    Date     │ IDR/USD │  VIX  │
├─────────────┼─────────┼───────┤
│ 02 Jan 2024 │  15,439 │ 13.20 │
│ 03 Jan 2024 │  15,473 │ 14.04 │
│ 04 Jan 2024 │  15,495 │ 14.13 │
│ 05 Jan 2024 │  15,525 │ 13.35 │
│ 08 Jan 2024 │  15,518 │ 13.08 │
│ 09 Jan 2024 │  15,522 │ 12.76 │
│ 10 Jan 2024 │  15,518 │ 12.69 │
│ 11 Jan 2024 │  15,568 │ 12.44 │
│ 12 Jan 2024 │  15,558 │ 12.70 │
│ 15 Jan 2024 │  15,559 │ 13.25 │
│ 16 Jan 2024 │  15,555 │ 13.84 │
│ 17 Jan 2024 │  15,592 │ 14.79 │
│ 18 Jan 2024 │  15,639 │ 14.13 │
│ 19 Jan 2024 │  15,630 │ 13.30 │
│ 22 Jan 2024 │  15,628 │ 13.19 │
│ 23 Jan 2024 │  15,627 │ 12.55 │
│ 24 Jan 2024 │  15,656 │ 13.14 │
│ 25 Jan 2024 │  15,719 │ 13.45 │
│ 26 Jan 2024 │  15,767 │ 13.26 │
│ 29 Jan 2024 │  15,829 │ 13.60 │
│ 30 Jan 2024 │  15,825 │ 13.31 │
│ 31 Jan 2024 │  15,796 │ 14.35 │
├─────────────┼─────────┼───────┤
│ Count       │      22 │    22 │
│ Min         │  15,439 │ 12.44 │
│ Max         │  15,829 │ 14.79 │
│ Avg         │  15,611 │ 13.39 │
│ Std         │     114 │  0.61 │
└─────────────┴─────────┴───────┘
```

~ Kei
```

## Data Source

- **File**: `database/20260102_daily01.csv`
- **Columns**: `date`, `idrusd`, `vix_index`
- **Coverage**: 776 rows spanning February 2023 to December 2025
- **Frequency**: Daily (business days only)

## Feature Characteristics

### Strengths
- ✅ Flexible query parsing supporting 5+ date format variations
- ✅ Automatic handling of holidays (missing data points)
- ✅ Proper numeric formatting (integers for FX, 2 decimals for VIX)
- ✅ Complete statistics (Count, Min, Max, Avg, Std per series)
- ✅ All business days displayed (no downsampling)
- ✅ Series alias support (fx → idrusd)
- ✅ HTML-safe formatting for Telegram
- ✅ Proper error handling with user-friendly messages
- ✅ Metrics logging for analytics

### Limitations
- Currently supports only 2 series at a time (idrusd and vix)
- Date ranges limited to available data (Feb 2023 - Dec 2025)
- Weekend/holiday dates are excluded from the dataset

## Testing

All components have been tested with:
- ✅ Parser: All 9+ query format variations
- ✅ Formatter: Multiple date ranges (1 month to 12 months)
- ✅ Handler: Full Telegram integration flow
- ✅ Edge cases: fx alias, series deduplication, missing data handling

## Version History

- **v.0455**: Initial implementation
  - Added `parse_macro_comparison_query()` parser
  - Added `format_macro_comparison_table()` formatter
  - Added handler in `kei_command()`
  
- **v.0456**: Bug fix
  - Fixed fx alias handling in parser
  - Ensured fx and idrusd are properly recognized as equivalent

## Related Features

This feature builds on:
- [Macro Data Tables](macro_data_tables.py): Table formatting infrastructure
- [Data Transparency Fix (v.0452)](docs/IMPLEMENTATION_SUMMARY.md): Removed downsampling for full business day coverage
- [Data Loading Fixes (v.0454)](docs/IMPLEMENTATION_SUMMARY.md): Consolidated macro data in single file

## Future Enhancements

Potential improvements for future versions:
1. Support for 3+ series comparisons
2. Custom series selection beyond idrusd/vix
3. Statistical analysis (correlation, volatility, etc.) in comparison output
4. Export to CSV/JSON format
5. Graphical visualization option
