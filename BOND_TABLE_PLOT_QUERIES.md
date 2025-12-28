# Bond Table & Plot Queries Implementation

## Overview

Extended the `/kei tab` (table queries) and `/kin plot` (plot queries) capabilities to support bond yield/price data across flexible time periods. Users can now query bond data with economist-style table output and professional plots using intuitive natural language patterns.

## Features Implemented

### 1. Bond Table Queries (`/kei tab`)

**Supported Patterns:**
- Single month: `/kei tab yield 5 year in feb 2025`
- Single quarter: `/kei tab price 10 year in q3 2025`
- Single year: `/kei tab yield 5 year in 2025`
- Month range: `/kei tab yield 5 and 10 year from oct 2024 to mar 2025`
- Quarter range: `/kei tab price 5 and 10 year from q2 2024 to q1 2025`
- Year range: `/kei tab yield 5 and 10 year from 2023 to 2024`
- Multi-metric: `/kei tab yield and price 5 year in apr 2023`
- Multi-tenor: `/kei tab yield 5 and 10 year in jan 2025`

**Metrics Supported:**
- `yield` – bond yield data
- `price` – bond price data
- `yield and price` – both metrics (dual-column tables)

**Tenors Supported:**
- 5 year, 10 year, or any other tenor in the database
- Multi-tenor via "X and Y year" syntax

**Output Format:**
Economist-style bordered tables with:
- Left-aligned date columns
- Right-aligned numeric values
- Professional box-drawing characters
- Clear column headers and visual structure

### 2. Bond Plot Queries (`/kin plot`)

**Supported Patterns:**
- Single month: `/kin plot yield 5 year in jan 2025`
- Single quarter: `/kin plot price 10 year in q3 2025`
- Month range: `/kin plot yield 5 and 10 year from oct 2024 to mar 2025`
- Quarter range: `/kin plot price 5 and 10 year from q2 2024 to q1 2025`
- Year range: `/kin plot yield 5 and 10 year from 2023 to 2024`

**Output Format:**
Professional Economist-style plots with:
- Multi-tenor support (separate colored lines per tenor)
- Clean grid styling
- Proper date formatting
- Clear metric labeling (Yield %, Price values)

## Implementation Details

### Core Functions

#### `parse_bond_table_query(q: str) -> Optional[Dict]`
Parses `/kei tab` queries to extract:
- Metrics (yield/price)
- Tenors (single or multi-tenor)
- Period specifications (month/quarter/year, single or range)

Returns structured dict with:
```python
{
    'metrics': ['yield'] or ['price'] or ['yield', 'price'],
    'tenors': ['05_year', '10_year'],
    'start_date': date(2025, 1, 1),
    'end_date': date(2025, 3, 31)
}
```

#### `parse_bond_plot_query(q: str) -> Optional[Dict]`
Similar to table parser but optimized for plot queries. Handles the `/kin plot` prefix correctly by extracting the text after "plot" to avoid regex conflicts with the word "in" in "/kin".

Returns:
```python
{
    'metric': 'yield' or 'price',
    'tenors': ['05_year', '10_year'],
    'start_date': date,
    'end_date': date
}
```

#### `format_bond_metrics_table(db, start_date, end_date, metrics, tenors) -> str`
Formats bond query results as economist-style tables. Supports:
- Single tenor, single metric: Date | Value
- Multi-tenor: Date | Tenor1 | Tenor2 | ...
- Multi-metric: Date | Yield | Price
- Multi-tenor, multi-metric: Date | T1_Y | T1_P | T2_Y | T2_P | ...

All numeric columns right-aligned, dates left-aligned.

### Integration Points

**In `/kei` command (`kei_command()`):**
1. Bond table query detection via `parse_bond_table_query()`
2. Database querying via `format_bond_metrics_table()`
3. Response sent as Markdown to preserve table borders

**In `/kin` command (`kin_command()`):**
1. Bond plot query detection via `parse_bond_plot_query()`
2. Plot generation via existing `generate_plot()` function
3. Image response sent to user

### Period Parsing Logic

Both parsers implement flexible period specification:

**Month Names:** English (jan, january, feb, february, etc.) and Indonesian variants
**Quarter Format:** Q1-Q4 (maps to months: Q1=Jan-Mar, Q2=Apr-Jun, Q3=Jul-Sep, Q4=Oct-Dec)
**Year Format:** 4-digit year (Jan 1 to Dec 31)

**Date Range Calculation:**
- Single month: 1st to last day of month
- Single quarter: 1st day of first month to last day of third month
- Single year: Jan 1 to Dec 31
- Ranges: First date of start period to last date of end period

## Testing

Comprehensive test suite in `tests/test_bond_table_plot_queries.py`:

**49 Tests Covering:**
- Single/multi-tenor queries
- Single/multi-metric queries
- Month/quarter/year period specifications
- Single period and range queries
- Month name variations (short/long forms)
- Quarter parsing (Q1-Q4)
- Edge cases (missing metrics, missing tenors, non-table queries)

**All 63 tests passing:**
- 14 existing auction query tests
- 49 new bond table/plot query tests

## Examples

### Bond Yield Tables
```
/kei tab yield 5 and 10 year in feb 2025
/kei tab price 5 year from oct 2024 to mar 2025
/kei tab yield and price 10 year in q2 2025
```

### Bond Plots
```
/kin plot yield 5 and 10 year from jan 2025 to mar 2025
/kin plot price 5 year in q3 2024
/kin plot yield 5 year from 2023 to 2024
```

### Combined Usage
```
/both plot 5 and 10 year jan 2025  # Generate plot via /kin
/kei yield 10 year 2025-12-12      # Point lookup
/check 2025-12-12 5 and 10 year    # Quick check
```

## Error Handling

- Queries without "tab" or "plot" keywords: Return None (not processed)
- Missing metrics: Return None (invalid query)
- Missing tenors: Return None (invalid query)
- Missing period specification: Return None (invalid query)
- Database errors: Return error message to user
- No data found for period: Return informative error message

## Performance Considerations

- **Table queries:** Single database query per request with date/tenor filtering
- **Plot queries:** Database query + plot generation (memory-efficient with matplotlib)
- **Caching:** Leverages existing BondDB instance caching

## Future Enhancements

1. Add price-yield curves (2D analysis)
2. Support additional metrics (duration, convexity)
3. Comparison across periods (e.g., "Feb 2024 vs Feb 2025")
4. Statistical summaries (volatility, correlation)
5. Indonesian language support in period specifications
