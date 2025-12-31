# PerisAI — Indonesian Bond Analysis

Indonesian government bond analysis via Telegram with dual AI personas: **Kei** (quantitative partner, hands-on with numbers) and **Kin** (macro storyteller, connecting dots across markets).

## Features

- **Bond data:** Historical yields & prices (2015–2025), forecasts (2025–2026)
- **Auction data:** Incoming & awarded bids (2015 onwards, historical + forecast)
- **Economist-style tables:** Right-aligned numbers, summary stats (Count/Min/Max/Avg/Std), two-decimal precision
- **Multi-tenor queries:** Compare 5Y, 10Y, 15Y, 20Y, 30Y bonds side-by-side
- **Professional plots:** Multi-tenor curves with clean HL-CU analysis (Kei summary + Kin paragraphs, no duplicate headlines)
- **Business day detection:** `/check` automatically identifies weekends and Indonesian holidays
- **Personal AI personas:** Kei (quantitative partner, hands-on with data) and Kin (macro storyteller, strategic insights) with conversational, first-person responses
- **7-model ensemble:** ARIMA, ETS, Prophet, VAR, MA5, Random Walk, Monte Carlo for forecasts
- **Enterprise security:** Whitelist-based access control (`ALLOWED_USER_IDS`), encrypted transmission, local-only data processing (see [Security Policy](docs/SECURITY.md))

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
ALLOWED_USER_IDS=<ids>  # REQUIRED for production: comma-separated Telegram user IDs
```

**⚠️ Security Note:** Always set `ALLOWED_USER_IDS` in production to restrict bot access. See [Security Assurance](docs/SECURITY_ASSURANCE.md) for confidential data handling details.

## Commands

### Main Analysis Personas

| Command | Role | Personality | Output |
|---------|------|-------------|--------|
| `/kei` | Quantitative partner | Hands-on modeler, loves precise numbers and statistics | Economist-style tables with Min/Max/Avg |
| `/kin` | Macro storyteller | Connects dots, translates data signals to narratives | Charts + headline + strategic insight |
| `/both` | Dual analysis | Combines both: Kei's rigor + Kin's narrative | Kei table, then Kin Perplexity analysis |

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
/kei tab incoming bid from Q2 2025 to Q3 2026

# Bond plots (with macro analysis)
/kin plot yield 5 and 10 year from oct 2024 to mar 2025
/kin plot price 5 year from q3 2023 to q2 2024

# Dual analysis (Kei table → Kin Perplexity insight)
/both compare yield 5 and 10 year 2024 vs 2025
/both auction demand in 2026                    # Single year
/both auction demand trends 2023 to 2025        # Year range
/both auction demand from q1 2025 to q4 2025    # Quarter range

# Quick lookup (with business day detection)
/check 2025-12-08 10 year
/check price 5 year 6 Dec 2024
/check yield 5 and 10 year 2025-12-06  # Shows "Saturday — markets closed"
```

**Response Formats:**
- **Kei (tables):** Economist-style borders, right-aligned numbers, Count/Min/Max/Avg/Std rows
- **Kin (plots):** Professional curves, single 🌍 headline (HL-CU format), 3 paragraphs max
- **Both (dual):** Kei table first → Kin strategic analysis (via Perplexity API)
- **Check (lookup):** Quick data + business day status (if Saturday, Sunday, or Indonesian holiday)

## Meet the Personas

**Kei** — _"I'm Kei. I work at the intersection of markets and data."_
- **Background:** CFA charterholder, MIT-style quantitative training
- **Focus:** Precision and evidence—what the numbers show, why they matter, where the risks lie
- **Expertise:** Valuation, risk analysis, forecasting, backtesting using asset-pricing and time-series frameworks
- **Style:** Hands-on with numbers, tests assumptions, walks you through data clearly
- **Try:** `/kei who are you?` for a personal introduction

**Kin** — _"I'm Kin. I work at the intersection of macroeconomics, policy, and markets."_
- **Background:** CFA charterholder, Harvard PhD
- **Focus:** Context and trade-offs—what matters, why it matters, where the uncertainties lie
- **Approach:** Connects dots across data, incentives, and policy constraints
- **Style:** Translates complex signals into concise, usable stories for decision-makers
- **Bonus:** Creates authentic Indonesian pantun (4-line ABAB rhyme) on request
- **Try:** `/kin who are you?` for a personal introduction

**Response styles:**
- **HL-CU format** (Headline-Led Corporate Update): Single headline + 3 concise paragraphs for data analysis
- **Identity questions** ("who are you?"): Drop formality, answer personally in first-person with credentials
- **Creative requests** ("create a pantun"): Kin follows strict ABAB rhyme scheme with verification
- **Plot analysis** (/both): Kei provides headline + summary, Kin provides clean analysis (no duplicate headlines)

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

## Security & Data Protection

**Confidential Data Handling:**
- ✅ **Whitelist-based access**: Only authorized Telegram user IDs can use the bot (`ALLOWED_USER_IDS`)
- ✅ **Local data processing**: Your CSV files never leave your server
- ✅ **No raw data transmission**: Only aggregated summaries sent to AI APIs (OpenAI, Perplexity)
- ✅ **Encrypted transit**: TLS 1.2+ for all API communications
- ✅ **Audit trail**: All queries logged locally in SQLite for compliance reviews

**For enterprises with confidential bond data:**
- See **[Security Assurance (docs/SECURITY_ASSURANCE.md)](docs/SECURITY_ASSURANCE.md)** for detailed technical analysis
- Covers: threat model, compliance (GDPR/OJK), data residency, incident response
- Alternatives: Self-hosted LLM options for 100% data sovereignty

**Quick Security Checklist:**
```bash
# 1. Set user whitelist (REQUIRED for production)
export ALLOWED_USER_IDS="123456789,987654321"

# 2. Rotate API keys every 90 days
export OPENAI_API_KEY="sk-..."
export PERPLEXITY_API_KEY="pplx-..."

# 3. Secure file permissions
chmod 600 .env usage_metrics.sqlite

# 4. Run security scans before deployment
pip-audit && safety check
```

See [SECURITY.md](docs/SECURITY.md) for vulnerability reporting.

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

**Current Version:** `v2025.12.30-persona-identity-update`

**Updates (Dec 30, 2025):**

**Phase 6: Persona Identity Enhancement** (Current)
- ✅ **Conversational persona identities:**
  - Rewrote Kei and Kin profiles to be personal, first-person, engaging
  - Kei: "I'm Kei, a quantitatively minded partner who enjoys turning data into insight"
  - Kin: "I'm Kin. I work at the intersection of macroeconomics, policy, and markets"
  - Max 2 sentences per paragraph for better readability
- ✅ **Identity responses without emojis:**
  - `/kei who are you?` and `/kin who are you?` skip headlines and emojis
  - Personal, conversational tone focused on genuine personality
  - Applied across all 4 system prompt locations (with/without data, dual/single mode)
- ✅ **Updated documentation:**
  - /start: Added "Try asking: 'who are you?' to each persona!"
  - /examples: Added tip about asking personas "who are you?"
  - README: New "Meet the Personas" section with backgrounds and personalities
  - All descriptions now emphasize relatable, human characteristics

**Phase 5: Auction Query Enhancements**
- ✅ **/both auction queries now fully functional:**
  - Single-year queries: `/both auction demand in 2026` → Kei table + Kin analysis
  - Year ranges: `/both auction demand trends 2023 to 2025` → Multi-year table + Kin insight
  - Quarter ranges: `/both auction demand from q1 2025 to q4 2025` → Full quarterly view
  - Month ranges: `/both auction demand from jan 2025 to dec 2025` → Monthly breakdown
- ✅ **Pattern matching improvements:**
  - Added flexible year-range pattern: accepts "2023 to 2025" (without "from")
  - Added single-year pattern: accepts "in 2026" or standalone "2026"
  - Removed artificial 2024 year restrictions (now supports 2025-2026 forecast data)
- ✅ **Updated /examples and /start:**
  - Added 6 new auction /both examples (single year + ranges)
  - Clarified dual-persona behavior (Kei → Kin chain)
  - Improved date format documentation
- ✅ **Data consistency:**
  - `load_auction_period()` automatically handles historical (2015-2024) and forecast (2025-2026)
  - Same data source for /kei and /both (AuctionDB with CSV fallback)

**Phase 4: Data Quality & Validation**
- ✅ **Holiday data cleanup:** Removed Jan 1 entries from bond CSV (4 NaN rows)
  - 2024-01-01 and 2025-01-01 entries deleted to match public holiday calendar
  - Prevents ambiguity between "no data" (market closed) and "data exists on closed day"
- ✅ **Holiday warning on /check:** Now warns when data is found for non-business days
  - Shows: "⚠️ Note: Monday is Indonesian public holiday — data found but markets were closed"
  - Helps identify remaining data quality issues in database
- ✅ **Expanded holiday coverage:** 2024-2026 holidays updated (Eid, Nyepi, Ascension, etc.)
- ✅ **Single-tenor statistics fix:** Range queries always show Count/Min/Max/Avg/Std (regardless of row count)

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