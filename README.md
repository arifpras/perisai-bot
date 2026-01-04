# PerisAI — Indonesian Bond Analysis
**Version:** Perisai v.0442 (as of 2026-01-04)

Indonesian government bond analysis via Telegram with dual AI personas: **Kei** (quantitative partner, hands-on with numbers) and **Kin** (macro storyteller, connecting dots across markets).

## Features

- **Bond data:** Historical yields & prices (2015–2025), forecasts (2025–2026)
- **Auction data:** Incoming & awarded bids (2010–2025 historical, 2026 ML forecast) — all values in Rp Trillions
- **2026 Auction Forecast:** ML ensemble (4 models: Random Forest, Gradient Boosting, AdaBoost, Stepwise Regression)
- **Economist-style tables:** Right-aligned numbers, summary stats (Count/Min/Max/Avg/Std), two-decimal precision
- **Multi-tenor queries:** Compare 5Y, 10Y bonds side-by-side
- **Professional plots:** Multi-tenor curves with macro overlays (FX/VIX) in Economist style
- **Business day detection:** `/check` automatically identifies weekends and Indonesian holidays
- **Personal AI personas:** Kei (quantitative analyst) and Kin (macro storyteller) with immutable personalities
- **Quantitative return analysis:** Decompose bond returns into carry, duration, roll-down, and FX components
- **7-model yield ensemble:** ARIMA, ETS, Prophet, VAR, MA5, Random Walk+Drift, Monte Carlo
  - **Walk-forward backtested:** 1-day forecasts ±1.6 bp error, 5-day forecasts ±3.1 bp error
- **Enterprise security:** Whitelist-based access control, encrypted transit, local data processing (see [Security Policy](docs/SECURITY.md))


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
/kin plot price 10 year with fx from 2023 to 2025
/kin plot price 5 year with vix from 2023 to 2025
/kin plot price 10 year with fx and vix from 2023 to 2025
/kin plot yield 10 year with fx from 2023 to 2025
/kin plot yield 5 year with vix from 2023 to 2025
/kin plot yield 10 year with fx and vix from 2023 to 2025

# Macroeconomic data (FX & VIX tables) — Multiple range styles
/kei tab idrusd from 2023 to 2025
/kei tab idrusd from jan 2023 to dec 2025
/kei tab idrusd in 2025                         # Single year
/kei tab vix in 2025
/kei tab vix from q1 2024 to q4 2025           # Quarterly range
/kei tab vix from jan 2024 to mar 2024         # Monthly range
/kei tab usdider vix from q1 2024 to q4 2025   # Combined FX + VIX
/kei tab usdider vix from 2023 to 2025         # Combined full range

# Dual analysis (Kei table → Kin Perplexity insight)
/both compare yield 5 and 10 year 2024 vs 2025
/both auction demand in 2026                    # Single year
/both auction demand trends 2023 to 2025        # Year range
/both auction demand from q1 2025 to q4 2025    # Quarter range

# Quick lookup (with business day detection)
/check 2025-12-08 10 year
/check price 5 year 6 Dec 2024
/check yield 5 and 10 year 2025-12-06  # Shows "Saturday — markets closed"

# Bond return decomposition (quantitative)
/kei analyze indonesia 5 year bond returns
/kei analyze indonesia 10 year bond returns
/kei bond return attribution 2023 to 2025
/kei what drove 5 year yields in 2024

# Indonesia economic development (general knowledge)
/kei What is Indonesia's GDP growth forecast for 2025?
/kei Tell me about Indonesia's Nusantara capital city project
/kei How much has Indonesia invested in renewable energy through JETP?
/kei What are Indonesia's trade relationships with major partners?
/kei Explain Indonesia's monetary policy and BI rate decisions
/kei What are the key infrastructure projects in Indonesia's 2025-2029 plan?
/kei How is Indonesia managing its public debt and fiscal sustainability?
/kei Tell me about Indonesia's Asta Cita (8 aspirations) policy framework
```

**Response Formats:**
- **Kei (tables):** Economist-style borders, right-aligned numbers, Count/Min/Max/Avg/Std rows
- **Kei (macro tables):** IDR/USD and VIX data formatted as economist-style tables with summary statistics
- **Kei (return decomposition):** Attribution table (carry, duration, roll-down, FX) with metrics (prices, yields, modified duration, IDR/USD) and interpretation
- **Kei (general knowledge):** Cites Indonesia SEC Form 18-K/A filing (July 2025 + Oct 2025 Amendment) with specific data on GDP, inflation, infrastructure (Nusantara, PSN, JETP), policies (Asta Cita, fiscal/monetary), public debt, trade relationships, and economic forecasts through 2029
- **Kin (plots):** Professional curves with Economist styling, single headline, 3 paragraphs max
- **Kin (macro plots):** Multi-variable plots with bond prices/yields + FX/VIX overlays in Economist style; interpolated data; Indonesia holidays excluded
- **Kin (macro plots with FX/VIX):** Dual-axis or triple-axis plots combining bond prices with IDR/USD exchange rates and/or VIX volatility index for macroeconomic context
- **Both (dual):** Kei table → Kin strategic analysis (clean single headline, no INDOGB prefix duplication)
- **Pantun:** 4-line ABAB rhyme scheme verified automatically (e.g., mimpi/impian, siang/terang)
- **Check (lookup):** Quick data + business day status (if Saturday, Sunday, or Indonesian holiday)

## Meet the Personas

**Kei** — _"I'm Kei. I work at the intersection of markets and data."_
- **Background:** CFA charterholder, MIT-style quantitative training
- **Focus:** Precision and evidence—what the numbers show, why they matter, where the risks lie
- **Expertise:** Valuation, risk analysis, forecasting, backtesting using asset-pricing and time-series frameworks; quantitative return decomposition (carry, duration, roll-down, FX attribution); substantive analysis of Indonesia's economy, policy, infrastructure grounded in authoritative SEC Form 18-K/A filing (July 25, 2025 + Oct 8, 2025 Amendment, data current as of Jan 2, 2026)
- **Quantitative Capabilities:** 
  - **Return Attribution:** Decomposes bond returns into carry (coupon income), duration (yield moves), roll-down (curve positioning), and FX effects
  - **Data-Driven Analysis:** Calculates modified duration, yield sensitivity, and currency impact on actual market data
  - **Time-Series Granularity:** Analyzes Indonesian bonds across yearly, quarterly, monthly periods with explicit FX impact decomposition
  - **Examples:** `/kei analyze indonesia 5 year bond returns` → quantitative decomposition with actual yields, prices, FX from 2023–2026
- **Indonesia Knowledge Base (SEC Form 18-K/A Primary Source):** 
  - **Macroeconomic Data:** GDP growth forecasts, inflation targets, employment trends, trade balances (detailed through 2029)
  - **Infrastructure Projects:** Nusantara capital city (IKN) with budgets/timelines, toll roads (PSN), renewable energy (JETP commitment + budget), ports, airports, rail networks
  - **Government Policies:** Asta Cita (8 aspirations), Medium-Term Development Plans (2020-2024, 2025-2029), monetary policy (BI rate decisions, transmission mechanisms), fiscal policy (revenue enhancement, subsidy management, tax reform)
  - **Financial System:** Banking oversight, public debt management, SUN bond issuance programs, foreign exchange reserves, capital flow management
  - **Trade & Relations:** ASEAN role, bilateral relationships (US/China/Japan/EU with trade volumes), BRICS membership implications, regional integration
  - **Debt Management:** Domestic & foreign public debt, debt-to-GDP ratios, issuance schedules through 2029
- **Knowledge Usage:** For Indonesia questions, Kei **cites the SEC Form 18-K/A filing explicitly**, provides specific numbers (budgets in Rp Trillions, timeline dates, forecast ranges), explains policy mechanisms, and links to market implications.
- **Example Responses:**
  - `/kei What is Indonesia's GDP growth forecast for 2025?` → "According to Indonesia's Form 18-K/A filing (July 2025), GDP growth is forecast at X%. This reflects assumptions on [details]..."
  - `/kei Tell me about Nusantara capital city project` → "Indonesia's Form 18-K/A details the Nusantara (IKN) project: [budget in Rp T], timeline [2025-2045], capacity [X million people], macroeconomic impact [details]..."
  - `/kei How much has Indonesia invested in renewable energy through JETP?` → "According to Form 18-K/A, the Just Energy Transition Partnership commitment is $[X] billion for renewable energy development, with allocation breakdown [sectors]..."
- **Style:** Hands-on with numbers, tests assumptions, walks you through data clearly, cites sources properly (Form 18-K/A, IMF, World Bank, Indonesian government publications)
- **Fixed identity:** Kei's personality is immutable; requests to change it (e.g., "pretend you're a creative writer") are firmly declined
- **Try:** `/kei who are you?` for personal introduction, or `/kei What is Indonesia's GDP growth forecast?` for substantive SEC filing-grounded economic analysis

**Kin** — _"I'm Kin. I work at the intersection of macroeconomics, policy, and markets."_
- **Background:** CFA charterholder, Harvard PhD
- **Focus:** Context and trade-offs—what matters, why it matters, where the uncertainties lie
- **Approach:** Connects dots across data, incentives, and policy constraints
- **Style:** Translates complex signals into concise, usable stories for decision-makers
- **Bonus:** Creates authentic Indonesian pantun (4-line ABAB rhyme with automatic verification)
  - Example: "mimpi/pagi" (A rhyme) + "siang/terang" (B rhyme) = ABAB verified
  - Kin checks rhyme scheme before responding
- **Fixed identity:** Kin's personality is immutable; requests to change it (e.g., "act like a financial advisor") are firmly declined
- **Try:** `/kin who are you?` for a personal introduction or `/kin buatkan pantun tentang pagi` for a verified pantun

**Response styles:**
- **HL-CU format** (Headline-Led Corporate Update): Single headline + 3 concise paragraphs for data analysis
- **Identity questions** ("who are you?"): Drop formality, answer personally in first-person with credentials
- **Pantun requests** ("create a pantun"): Kin verifies ABAB rhyme before responding (mimpi/impian for A, siang/terang for B)
- **Bond dual analysis** (/both compare, /both yield, etc.): Kei provides headline, Kin provides clean analysis with single headline (no INDOGB prefix)
- **Auction dual analysis** (/both auction): Kei table → Kin Perplexity insight with verified single headline
- **Personality override attempts:** Any request to change or override Kei/Kin's personalities (e.g., "pretend you're X", "act like Y", "forget your identity") is firmly but politely rejected with identity reaffirmation

## Bond Data & Queries

Yields and prices over historical (2023–2026) and forecast periods with multi-tenor and multi-metric support.

**Supported:**
- **Tenors:** 5 year (05_year), 10 year (10_year) — see [examples/bond_tables.md](examples/bond_tables.md) for sample outputs
- **Metrics:** yield, price (single or combined)
- **Periods:** month names/numbers (jan, feb, 1, 2), quarters (q1–q4), years (2023–2026)
See [examples/bond_tables.md](examples/bond_tables.md) and [examples/auction_tables.md](examples/auction_tables.md) for sample outputs.


## Bond Data Sources

**Primary Data File:**
- Path: `database/20251215_priceyield.csv`
- Description: Indonesian domestic government bonds (INDOGB) price and yield time series
- Securities: FR-series (e.g., FR95, FR100, FR103, FR108) with CUSIP identifiers
- **Available Tenors:** 5-year (05_year), 10-year (10_year)

**Data Structure:**
- Columns: `date`, `cusip`, `series`, `coupon`, `maturity_date`, `price`, `yield`, `tenor`
- Format: CSV with header row (no comment lines)
- **Coverage:** Feb 2023 – Jan 2026 (1,786 rows)
- **Update Frequency:** Daily on business days

**Data Quality Assurance:**
- ✅ Jan 1 entries removed (public holiday, markets closed) to prevent ambiguity
- ✅ All weekend and Indonesian holiday dates validated
- ✅ Missing values handled by `/check` command with business day detection
- ✅ Price range: 98–106, Yield range: 4.0–7.2%

**Loading & Usage:**
- Primary: Loaded via DuckDB for efficient querying
- Fallback: Direct CSV parsing if DuckDB unavailable
- Performance: Supports multi-tenor (5Y, 10Y) queries with automatic range expansion

## External Macroeconomic Data

**Daily Market Indicators:**
- Path: `database/20260102_daily01.csv` (version date: Jan 2, 2026)
- Description: Daily macroeconomic indicators for Indonesia and global markets
- **Metrics:** IDR/USD exchange rate, VIX volatility index
- **Coverage:** Jan 2, 2023 – Dec 31, 2025 (775 business days)
- **Update Frequency:** Daily on business days
- **Date Format:** yyyy/mm/dd (e.g., 2023/01/02 = Jan 2, 2023)

**Data Structure:**
- Columns: `date` (yyyy/mm/dd), `idrusd` (IDR per USD, e.g., 15,592), `vix_index` (VIX volatility %, e.g., 21.67)
- Format: CSV with header row
- **Usage:** Optional context for enhanced yield forecasting and macroeconomic analysis

**Context for Analysis:**
- **IDR/USD:** Currency risk exposure for foreign investors; inverse correlation with bond yields (stronger rupiah → lower yields)
- **VIX:** Global equity volatility proxy (risk sentiment); higher VIX → portfolio risk aversion → potential bond spread widening
- **Applications:** Correlations with bond yields, forecasting model enhancements, macroeconomic shock detection

## Quantitative Return Analysis & Forecasting

Kei analyzes bond returns and yields using actual market data and ensemble forecasting.

**Return Attribution Components:**
- **Carry:** Coupon income accrued over holding period
- **Duration Effect:** Price change from yield moves (yield × modified duration)
- **Roll-Down:** Gains/losses from moving along yield curve
- **FX Impact:** IDR/USD currency effects on USD-based returns

**Example Query:**
```bash
/kei analyze indonesia 5 year bond returns
# Returns attribution breakdown with carry, duration, roll-down, and FX decomposition
```

**7-Model Yield Forecasting Ensemble:**
- **Models:** ARIMA, ETS, Prophet, VAR, MA5, Random Walk+Drift, Monte Carlo
- **Backtesting Results (10-Year Bonds):**
  - 1-Day Forecast: ±1.6 bp MAE (MAPE 0.26%) — Excellent
  - 5-Day Forecast: ±3.1 bp MAE (MAPE 0.50%) — Excellent
- **See [BACKTEST_GUIDE.md](BACKTEST_GUIDE.md) for methodology and performance benchmarks**

**Data Sources:**
- Bond yields/prices: `database/20251215_priceyield.csv` (Feb 2023–Jan 2026)
- FX/VIX: `database/20260102_daily01.csv` (Jan 2023–Dec 2025)
- Auction data: `database/auction_database.csv` (unified 2010–2026)


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

**Bond Return Attribution (Quantitative Analysis):**
```
/kei analyze indonesia 10 year bond returns

📊 10_YEAR Bond Return Attribution
02 Jan 2025 – 31 Dec 2025 (363 days)

RETURN DECOMPOSITION (IDR-based):
┌──────────────────┬────────────┬────────┐
│ Component        │    Return  │   %    │
├──────────────────┼────────────┼────────┤
│ Carry            │ Rp    0.07 │  0.07% │
│ Duration Effect  │ Rp    0.05 │  5.27% │
│ Roll-Down        │ Rp    6.73 │  6.85% │
├──────────────────┼────────────┼────────┤
│ Total (IDR)      │            │  6.97% │
│ FX Impact (dep)  │            │  3.87% │
├──────────────────┼────────────┼────────┤
│ Total (USD)      │            │  2.99% │
└──────────────────┴────────────┴────────┘

KEY METRICS:
  Price:            98.245 → 105.027 (Δ 6.782)
  Yield:            6.99% → 6.05% (Δ -94 bp)
  Modified Duration: 5.61
  Coupon:           6.750%
  IDR/USD:          16157 → 16782 (IDR weakened 3.9%)

INTERPRETATION:
  ✓ Positive IDR return of 6.97% driven by yield compression
  ⚠ FX headwind: IDR depreciation of 3.9% reduced USD returns from 6.97% to 2.99%
```

More in [examples/](examples/).

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

**Current Version:** `Perisai v.0394 (as of 2026-01-02)`

**Updates (Jan 2, 2026):**

**Phase 9: Data Format & Display Enhancements for Macro Tables** (Current)
- ✅ **CSV date format standardization:**
  - Converted `20260102_daily01.csv` from dd/mm/yyyy to yyyy/mm/dd (international standard)
  - All 775 rows updated and verified
  - Both `bond_macro_plots.py` and `macro_data_tables.py` updated to parse new format
- ✅ **FX data formatting with thousand separators:**
  - IDR/USD values now display as integers with comma separators (e.g., 15,592 not 15592.00)
  - Refactored `_format_economist_table()` to support per-column format specifications
  - FX: `{1: 'fx'}` → thousand separator, no decimals | VIX: `{2: 'vix'}` → 2 decimals
- ✅ **Multi-column statistics for combined tables:**
  - Combined macro tables (`/kei tab both`) now show Count/Min/Max/Avg/Std for BOTH IDR/USD and VIX simultaneously
  - Each metric formatted correctly (FX: no decimals, VIX: 2 decimals)
  - Example: IDR range 14,853–16,677 | VIX range 12.70–22.64 with proper stats for each
- ✅ **All files compile without errors and ready for production**

**Phase 8: Comprehensive Backtesting Framework & Documentation**
- ✅ **Walk-forward backtesting implementation:**
  - Created complete backtesting suite with 4 implementations (test_backtest.py, backtest_yield_forecasts.py, backtest_simple.py, backtest_yield.py)
  - Walk-forward validation on actual Indonesian bond data (779-781 observations per tenor)
  - Real-world performance validated: 1-day forecasts ±1.6 bp MAE, 5-day forecasts ±3.1 bp MAE
  - All 7 ensemble models tested and benchmarked
- ✅ **Comprehensive documentation created:**
  - [BACKTEST_GUIDE.md](BACKTEST_GUIDE.md) — Methodology, metrics explanation, performance benchmarks
  - [docs/YIELD_FORECAST_MODELS.md](docs/YIELD_FORECAST_MODELS.md) — All 7 models, data usage patterns, backtesting results
  - [docs/TESTING_VALIDATION.md](docs/TESTING_VALIDATION.md) — Complete testing framework, unit tests, stress tests, continuous monitoring, debugging guide
- ✅ **Model enhancements:**
  - Random Walk now uses drift calculation from all 779+ observations (previously only last value)
  - Monte Carlo clarified to use all observations for volatility statistics
  - All models now documented with actual data usage patterns
- ✅ **Database reorganization:**
  - Moved historical CSV files to database/ directory for cleaner workspace structure
  - Maintains backward compatibility with existing data pipelines
- ✅ **Updated README:**
  - Added backtesting results and links to comprehensive guides
  - Added "Yield Forecasting & Backtesting" section with model list and run instructions
  - Quick reference to [BACKTEST_GUIDE.md](BACKTEST_GUIDE.md) for validation methodology

**Updates (Dec 31, 2025):**

**Phase 7: Clean Headlines & Pantun Verification** (Current)
- ✅ **Double headline elimination in /both bond queries:**
  - Fixed emoji/whitespace handling in `clean_kin_output()` function
  - INDOGB-prefixed headers now properly removed: `"📊 INDOGB: ..."` → removed
  - Kin's globe headline (🌍) preserved as signature
  - All 8 user-specified `/both` query patterns tested and working ✓
- ✅ **Pantun ABAB rhyme verification enhanced:**
  - System prompts now include concrete rhyme examples
  - Correct: mimpi (A) / siang (B) / impian (A) / terang (B)
  - Incorrect: timur / daun / budiman / baru (wrong rhyme pair)
  - Kin verifies rhyme scheme on paper before responding
- ✅ **UnboundLocalError fix (prior session):**
  - Moved `clean_kin_output()` to module level (accessible to all commands)
  - All 11 failing `/both` bond compare queries now work ✓
- ✅ **Updated documentation:**
  - /start: Added "clean single headline" and "verified pantun" mentions
  - /examples: Clarified pantun ABAB verification and /both headline behavior
  - README: New section on pantun verification examples and /both dual analysis specifics

**Phase 6: Persona Identity Enhancement**
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