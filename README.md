# Bond Price & Yield Assistant

Indonesian government bond analysis via Telegram. Dual AI personas: **Kei** (quantitative) and **Kin** (macro/policy).

## Features

- **Bond data:** Historical yields & prices (2015–2025), forecasts (2025–2026)
- **Auction data:** Incoming & awarded bids (2015 onwards, historical + forecast)
- **Economist-style tables:** Right-aligned numbers, summary stats (Count/Min/Max/Avg/Std), two-decimal precision for Min/Max/Avg
- **Range expansion:** "from 2020 to 2024" auto-expands to all years/quarters/months
- **Multi-tenor queries:** Compare 5Y, 10Y, 15Y, 20Y, 30Y bonds side-by-side
- **7-model ensemble:** ARIMA, ETS, Prophet, VAR, MA5, Random Walk, Monte Carlo
- **Professional charts:** Plotly with Economist-style aesthetics

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

| Command | Purpose | Example |
|---------|---------|---------|
| `/kei` | Quantitative analysis | `/kei tab yield 5 and 10 year from q3 2023 to q2 2024` |
| `/kin` | Macro/policy context | `/kin plot price 5 year from oct 2024 to mar 2025` |
| `/both` | Combined analysis | `/both compare 5 and 10 year 2024 vs 2025` |
| `/check` | Quick lookup | `/check 2025-12-27 10 year` |
| `/examples` | Full query reference | In-bot command for all examples |

**Format:** Add `tab` for Economist-style tables, `plot` for charts. Outputs use INDOGB titles; Kin shows a single 🌍 headline. See [examples/](examples/) for outputs.

## Bond Table Queries

Query yields and prices over any historical or forecast period with multi-tenor and multi-metric support.

**Examples:**
```bash
/kei tab yield 5 and 10 year from q3 2023 to q2 2024
/kei tab price 5 year from oct 2024 to mar 2025
/kei tab yield and price 5 year in feb 2025
/kei tab yield 5 and 10 year from 2023 to 2024
```

**Supported:**
- Tenors: 5, 10, 15, 20, 30 year
- Metrics: yield, price (single or combined)
- Periods: month names/numbers (jan, feb, 1, 2), quarters (q1–q4), years (2023)
- Ranges: "from X to Y" auto-expands (e.g., q3 2023 to q2 2024 → all 4 quarters)

Tables render with Economist-style borders, right-aligned numbers, and summary statistics (Count/Min/Max/Avg/Std). Min/Max/Avg display two decimals for clarity. See [examples/bond_tables.md](examples/bond_tables.md).

## Auction Queries

Query incoming and awarded auction bids over any historical or forecast period.

**Examples:**
```bash
/kei tab incoming bid from 2020 to 2024
/kei tab awarded bid from 2015 to 2024
/kei tab incoming and awarded bid from 2022 to 2024
/kei tab incoming bid from Q2 2025 to Q3 2026
```

**Data Sources:**
- Historical (2015–2024): `auction_train.csv` (incoming + awarded)
- Forecast (2025–2026): `20251224_auction_forecast.csv` (incoming only)

Tables auto-expand ranges (e.g., "from 2015 to 2024" yields all 10 yearly rows). Values shown in Rp Trillions. See [examples/auction_tables.md](examples/auction_tables.md).

## Bond Data Sources

- File: `20251215_priceyield.csv` — Indonesian domestic government bonds (INDOGB) price and yield time series for FR-series (e.g., FR95–FR104) across supported tenors (5Y/10Y, etc.).
- Columns: `date`, `series` (e.g., FR100), `tenor` (e.g., `10_year`), `price`, `yield`.
- Usage: Loaded by the app via DuckDB; extra columns are ignored. Do not add comment lines to the CSV header.

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

**Current Version:** `v2025.12.29-formatting-cleanup`

**Recent Updates (Dec 29, 2025):**
- ✅ Title cleanup: Removed duplicate INDOGB headers; Kin shows a single 🌍 headline
- ✅ Signature cleanup: Removed duplicate persona signatures in combined responses
- ✅ Table precision: Min/Max/Avg now use two-decimal formatting
- ✅ Comparison footer removed: Dropped redundant "Yield statistics" footer under comparison tables
- ✅ Range expansion & awarded bids retained from prior release