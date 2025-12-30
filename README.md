# PerisAI — Indonesian Bond Analysis

Indonesian government bond analysis via Telegram with dual AI personas: **Kei** (quantitative analyst) and **Kin** (macro strategist).

## Features

- **Bond data:** Historical yields & prices (2015–2025), forecasts (2025–2026)
- **Auction data:** Incoming & awarded bids (2015 onwards, historical + forecast)
- **Economist-style tables:** Right-aligned numbers, summary stats (Count/Min/Max/Avg/Std), two-decimal precision
- **Multi-tenor queries:** Compare 5Y, 10Y, 15Y, 20Y, 30Y bonds side-by-side
- **Professional plots:** Multi-tenor curves with HL-CU format headlines and macro insights
- **Business day detection:** `/check` automatically identifies weekends and Indonesian holidays
- **Dual personas:** Kei (quant → tables), Kin (macro → plots + web search), Both (combined)
- **7-model ensemble:** ARIMA, ETS, Prophet, VAR, MA5, Random Walk, Monte Carlo for forecasts

## Quick Start

```bash
# Local
source .venv/bin/activate
pip install -r requirements.txt
python telegram_bot.py

# Docker
docker compose up
```

**Environment Variables:**
```bash
OPENAI_API_KEY=<key>
PERPLEXITY_API_KEY=<key>
TELEGRAM_BOT_TOKEN=<token>
ALLOWED_USER_IDS=<ids>  # optional
```

## Commands

### Main Analysis Personas

| Command | Role | Input | Output |
|---------|------|-------|--------|
| `/kei` | Quantitative analyst | Tables: bond/auction data | Economist-style tables with statistics |
| `/kin` | Macro strategist | Plots: bond trends over time | Charts + HL-CU headline + analysis |
| `/both` | Dual analysis | Compare/trends queries | Kei table → Kin headline + macro view |

### Utility Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `/check` | Quick single-date lookup | `/check 2025-12-08 10 year` (shows business day status) |
| `/start` | Overview & quick examples | Shows available commands & tips |
| `/examples` | Full query reference | 20+ working examples across all command types |

### Query Format

**For `/kei` (tables):**
```
/kei [tab] [metric] [tenor] from [date] to [date]
```

**For `/kin` (plots):**
```
/kin plot [metric] [tenor] from [date] to [date]
```

**For `/both` (combined):**
```
/both [compare|trends] [metric] [tenor] [date specifications]
```

**For `/check` (quick lookup):**
```
/check [date] [tenor/metric]
```

**Example commands** (all validated):

```bash
# Bond tables (Economist-style)
/kei tab yield 5 and 10 year from q3 2023 to q2 2024
/kei tab price 5 year from oct 2024 to mar 2025
/kei tab yield and price 5 year in feb 2025

# Auction tables
/kei tab incoming bid from 2020 to 2024
/kei tab awarded bid from 2015 to 2024
/kei tab incoming and awarded bid from 2022 to 2024

# Bond plots (with macro analysis)
/kin plot yield 5 and 10 year from oct 2024 to mar 2025
/kin plot price 5 year from q3 2023 to q2 2024

# Combined analysis
/both compare yield 5 and 10 year 2024 vs 2025
/both auction demand trends 2023 to 2025

# Quick lookup (with business day detection)
/check 2025-12-08 10 year
/check price 5 year 6 Dec 2024
/check yield 5 and 10 year 2025-12-06  # Shows "Saturday — markets closed"
```

**Response Formats:**
- **Kei (tables):** Economist-style borders, right-aligned numbers, Count/Min/Max/Avg/Std rows
- **Kin (plots):** Professional curves, single 🌍 headline (HL-CU format), 3 paragraphs max
- **Check (lookup):** Quick data + business day status (if Saturday, Sunday, or Indonesian holiday)

## Bond Data & Queries

Yields and prices over any historical or forecast period with multi-tenor and multi-metric support.

**Supported:**
- **Tenors:** 5, 10, 15, 20, 30 year
- **Metrics:** yield, price (single or combined)
- **Periods:** month names/numbers (jan, feb, 1, 2), quarters (q1–q4), years (2023)
- **Ranges:** "from X to Y" auto-expands (e.g., q3 2023 to q2 2024 → all 4 quarters)

See [examples/bond_tables.md](examples/bond_tables.md) for sample outputs.

## Auction Data & Queries

Incoming and awarded auction bids over historical and forecast periods.

**Data Sources:**
- Historical (2015–2024): `auction_train.csv` (incoming + awarded)
- Forecast (2025–2026): `20251224_auction_forecast.csv` (incoming only)

Tables auto-expand ranges. Values shown in Rp Trillions. See [examples/auction_tables.md](examples/auction_tables.md).

## Bond Data Sources

- File: `20251215_priceyield.csv` — Indonesian domestic government bonds (INDOGB) price and yield time series for FR-series (e.g., FR95–FR104) across supported tenors (5Y/10Y, etc.).
- Columns: `date`, `series` (e.g., FR100), `tenor` (e.g., `10_year`), `price`, `yield`.
- **Data coverage:** 2015–2025 (1,536 rows after holiday cleanup)
- **Data quality:** Jan 1 entries removed (public holiday, markets closed) to prevent ambiguity
- **Usage:** Loaded by the app via DuckDB; extra columns are ignored. Do not add comment lines to the CSV header.

## Output Examples

**Bond Table (Economist-style):**
```
/kei tab yield and price 5 year Feb 2025

┌───────────────────────────────────────┐
│ Date         |      Yield |      Price│
├───────────────────────────────────────┤
│ 03 Feb 2025  |       6.88 |      98.31│
│ 04 Feb 2025  |       6.79 |      98.69│
│ ...          |        ... |        ...│
│ 28 Feb 2025  |       6.73 |      98.97│
├───────────────────────────────────────┤
│ Count        |         20 |         20│
│ Min          |       6.51 |      98.31│
│ Max          |       6.88 |      99.94│
│ Avg          |       6.63 |      99.42│
│ Std          |       0.10 |       0.45│
└───────────────────────────────────────┘
```

**Auction Table:**
```
/kei tab incoming and awarded bid from 2022 to 2024

┌─────────────────────────────────────────────────┐
│ Period         | Incoming       | Awarded       │
├─────────────────────────────────────────────────┤
│ 2022           |   Rp 1,499.19T |     Rp 569.04T│
│ 2023           |   Rp 1,648.67T |     Rp 583.06T│
│ 2024           |   Rp 1,734.87T |     Rp 770.38T│
└─────────────────────────────────────────────────┘
```

More in [examples/](examples/).

## Forecasting

7-model ensemble with outlier removal (3×MAD): ARIMA, ETS, Prophet, VAR, MA5, Random Walk, Monte Carlo.

```
Model        | Forecast
---------------------------
ARIMA        | 6.1647%
ETS          | 6.1494%
PROPHET      | 6.1829%
AVERAGE      | 6.1637%
```

## Development

**Testing:**
```bash
pytest                              # API tests
python test_predeployment.py       # Pre-deployment validation
```

**Monitoring:**
- `/activity` command (admin-only)
- `python3 activity_monitor.py`
- See [ACTIVITY_MONITORING.md](ACTIVITY_MONITORING.md)

**Docker:**
```bash
docker build -t bondbot:latest .
docker compose up
```

**Current Version:** `v2025.12.30-data-cleanup`

**Updates (Dec 30, 2025):**

**Phase 4: Data Quality & Validation** (Current)
- ✅ **Holiday data cleanup:** Removed Jan 1 entries from bond CSV (4 NaN rows)
  - 2024-01-01 and 2025-01-01 entries deleted to match public holiday calendar
  - Prevents ambiguity between "no data" (market closed) and "data exists on closed day"
- ✅ **Holiday warning on /check:** Now warns when data is found for non-business days
  - Shows: "⚠️ Note: Monday is Indonesian public holiday — data found but markets were closed"
  - Helps identify remaining data quality issues in database
- ✅ **Expanded holiday coverage:** 2024-2026 holidays updated (Eid, Nyepi, Ascension, etc.)

**Phase 3: User Experience**
- ✅ **Business day detection:** `/check` identifies weekends and Indonesian public holidays
  - Shows reason for missing data (e.g., "Saturday is Saturday — markets may be closed")
  - Covers Eid, Nyepi, Christmas, New Year, and 30+ other holidays
- ✅ **Updated /start:** Clearer command structure, mentions business day detection
- ✅ **Updated /examples:** 16+ validated example commands with all query types
- ✅ **All 16 examples tested:** Bond tables, auction tables, plots, combined analysis, quick lookup ✓

**Phase 2: Persona Enhancement**
- ✅ **HL-CU format:** Kei now uses Headline-Led Corporate Update format with CFA/MIT credentials
- ✅ **Data context enrichment:** /kin plot & /both plot include tenor statistics (min/max/avg/std) to prevent hallucination
- ✅ **Citation cleanup:** Kin no longer adds citation brackets [1][2][3]
- ✅ **Metadata cleanup:** Removed "Yield statistics (N observations)" footers
- ✅ **Format consistency:** Both personas use consistent formatting and signatures

**Phase 1: Core Fixes**
- ✅ Title cleanup: Removed duplicate headers; Kin shows single 🌍 headline
- ✅ Signature cleanup: Removed duplicates in combined responses
- ✅ Table precision: Min/Max/Avg use two-decimal formatting
- ✅ Comparison footer removed: Dropped redundant statistics headers
- ✅ Range expansion & awarded bids implemented