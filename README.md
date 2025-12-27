
# Bond Price & Yield Assistant (Telegram Bot) 🏛️

Indonesian government bond analysis & forecasting via Telegram. Dual personas: **Kei** (quant analyst, MIT/CFA), **Kin** (macro strategist, Harvard/CFA). Fast answers on prices, yields, auctions, and policy context.

**Key Features:**
- 💹 **Bond Data** — Historical prices/yields (2023-2025), multi-tenor queries
- 📊 **Tables** — New! Clean Economist-style monospace tables with `/kei tab`
- 🔮 **Forecasting** — 7-model ensemble (ARIMA, ETS, Prophet, VAR, MA5, Random Walk, Monte Carlo)
- 📈 **Plots** — Multi-tenor yield curves with Economist styling
- 🌍 **Macro Context** — Policy, BI rates, fiscal implications via Kin persona
- ⚡ **Dual Analysis** — Chain both personas for complete insights

**Forecasting Examples:**
- `/kei forecast yield 10 year 2025-12-31`
- `/kei auction demand January 2026`
- `/kin explain impact of BI rate cuts on bond yields`
- `/both compare yields 2024 vs 2025` (Kei data → Kin insight)

## Quick Start 🚀

**Local:**
```bash
source .venv/bin/activate
pip install -r requirements.txt
python telegram_bot.py
```

**Docker:**
```bash
docker compose up
```

## Configuration ⚙️

Required environment variables:
- `OPENAI_API_KEY` — For Kei persona (ChatGPT)
- `PERPLEXITY_API_KEY` — For Kin persona (with web search)
- `TELEGRAM_BOT_TOKEN` — Bot token from BotFather

Optional:
- `ALLOWED_USER_IDS` — Comma-separated user IDs (empty = allow all)

## Telegram Commands 💬

| Command | Purpose | Example |
|---------|---------|---------|
| `/kei` | Quant analysis | `/kei yield 5 year Feb 2025` |
| `/kin` | Macro context | `/kin what is fiscal policy` |
| `/both` | Chained analysis | `/both compare 5 and 10 year 2024 vs 2025` |
| `/check` | Quick lookup | `/check 2025-12-27 10 year` |
| `/examples` | Query examples | `/examples` |
| `/start` | Welcome | `/start` |

## Table Format ✨ (NEW!)

Add `tab` or `table` to `/kei` queries for clean, professional output:

```
/kei tab yield 5 and 10 year Feb 2025

┌──────────────────────────────┐
│ Date        | 5-Year | 10-Year│
├──────────────────────────────┤
│ 01 Feb 2025 | 5.45%  | 5.62% │
│ 02 Feb 2025 | 5.46%  | 5.63% │
└──────────────────────────────┘
```

**Table query types:**
- Single tenor, multi-date: `/kei tab yield 5 year Feb 2025`
- Multi-tenor, multi-date: `/kei tab yield 5 and 10 year Feb 2025`
- **Multi-variable** (NEW): `/kei tab yield and price 5 and 10 year Feb 2025`

## Query Routing 🔀

- **→ Plots via /kin:** `/kei plot 5 year` automatically routes to Kin (better visualization)
- **→ Data via /kei:** `/kin auction demand` automatically routes to Kei (quantitative)
- **General questions → /kin:** Policy, fiscal, macro context
- **Bond data → /kei:** Yields, prices, tenors, auctions

## Data Files 📊

- `20251215_priceyield.csv` — Bond history with prices & yields
- `20251224_auction_forecast.csv` — Auction demand forecasts

## Forecasting Details 🔮

**7 Ensemble Models:**
- ARIMA, ETS, Prophet, VAR, MA5, Random Walk, Monte Carlo
- Ensemble average with outlier removal (3×MAD)
- Prophet yields clamped at zero
- Business-day horizons for "next N observations"

**Example Output:**
```
Forecast for 10-year yield (all series averaged):

Model         | Forecast
---------------------------
ARIMA        | 6.1647%
ETS          | 6.1494%
PROPHET      | 6.1829%
AVERAGE      | 6.1637%
```

## Personas 👥

| Persona | Background | Role | Powers |
|---------|-----------|------|--------|
| **Kei** | MIT/CFA Quant | Data analysis | Bond data, forecasts, tables, auctions |
| **Kin** | Harvard/CFA Macro | Context & insight | Policy, market implications, plots, web search |
| **Both** | Chained | Complete view | Kei finds data → Kin interprets |

## API Endpoints 🔌 (Legacy)

- `GET /health` — Status check
- `POST /query` — Text query with results
- `POST /chat` — Chat with persona selection
- `POST /plot` — Generate chart (PNG)

## Deployment ✅

**Pre-Deployment Validation:**
```bash
python test_predeployment.py
python test_examples_prompts.py
```

**Status:** ✅ 100% Ready for Production
- ✅ 26 pre-deployment tests passing
- ✅ 11/11 example prompts working
- ✅ All error handling complete
- ✅ 1,540 database records verified
- ✅ Economist-style formatting enabled

See [DEPLOYMENT_READINESS.md](DEPLOYMENT_READINESS.md) for full report.

## Error Handling & Fallbacks 🛡️

- Local plot generation when API unavailable
- Graceful fallbacks for missing data
- Proper error messages with no trailing errors
- Comprehensive logging and metrics

Example (next 3 observations - business days):

```
Latest 5 observations:
- 2025-12-08: 6.1910
- 2025-12-09: 6.1910
- 2025-12-10: 6.1690
- 2025-12-11: 6.1590
- 2025-12-12: 6.1630

Forecasts:
T+1 (2025-12-15): average=6.1667
T+2 (2025-12-16): average=6.1657
T+3 (2025-12-17): average=6.1637

[Full per-horizon tables with all 8 models shown in Telegram]
```

### Model Notes

- **ARIMA**: 3-level fallback mechanism (get_forecast → fit.forecast → last observed value); always returns valid float.
- **Prophet**: Forecasts clamped at 0.0 to avoid negative yields.
- **Ensemble**: Excludes negatives and 3×MAD outliers; uses 7 model outputs (no deep learning).
- **Business days**: T+N horizons calculated using `pandas.BDay` (skips weekends automatically).
- **Display format**: Economist-style monospace tables for professional presentation.

## Supported Data
- Indonesian government bond prices and yields (2023-2025): FR95-FR104 series (5Y/10Y tenors)
- Auction demand forecasts (bids, awarded, bid-to-cover) through 2026 (ensemble ML: XGBoost, Random Forest, time-series, macro features)
- Indonesian macroeconomic indicators (BI rate, inflation, etc.)

	- **Kei**: Quant (CFA/MIT). Concise, data-driven, HL-CU style. Forecasts: table of all models + summary. Custom formats on request.
	- **Kin**: Macro (CFA/Harvard). Explanatory, plain English by default. Custom formats on request.
- You can request bullet points, plain English, or HL-CU format explicitly in your query.

## Example Queries
- `/kei forecast yield 10 year at the end of 2025`
- `/kei forecast yield 10 year at the end of 2025 use ets`
- `/kei forecast yield 5 year December 2025 using prophet`
- `/kei yield 5 year Q1 2025`
- `/kei average yield 2024`
- `/kei plot 10 year 2024`
- `/kei yield 5 and 10 years 2024`
- `/kei explain FR95 price movement in plain English`
- `/kei auction demand forecast for FR102`

- `/kei yield 5 and 10 year in Jan, Feb, Mar 2025`
- `/kei yield 5 year from 1-31 Jan 2025`
- `/kei price 10 year in august 2025` → Statistics per tenor
- `/kei yield 5 and 10 years Q1 2024` → Separate stats per tenor

## Historical Table Formatting (Economist Style)

For historical and multi-tenor queries, the bot returns results as clear, aligned tables in Telegram chat, similar to professional financial publications:

```
Date         | 5 Year   | 10 Year  
-----------------------------------
2025-01-01   | 6.72%    | 7.10%    
2025-01-02   | 6.73%    | 7.11%    
...          | ...      | ...      
2025-01-31   | 7.02%    | 7.40%    
```

This format is compatible with Telegram and makes data easy to read and share.

## ARIMA/ETS Date Type Fix

ARIMA and ETS models now ensure all date calculations use pandas.Timestamp, preventing type errors in step calculation. No manual fix needed in user queries.

## Telegram Compatibility

All table and chart outputs are formatted for optimal display in Telegram, using monospace and markdown styles where appropriate.

## Usage logging & dashboard 📈
- **Activity Monitoring**: Automatic logging of all user queries
  - Telegram: `/activity` command shows health metrics, query breakdown, top users (admin-only)
  - CLI: `python3 activity_monitor.py` → formatted dashboard with statistics
  - Utilities: `python3 monitor_utils.py [export|cleanup|errors|slowest|trend]` → custom analysis
  - Database: SQLite (`usage_metrics.sqlite`) with indexed queries for fast analysis
  - Privacy: User IDs hashed with SHA256 (irreversible), usernames optional
  - See [ACTIVITY_MONITORING.md](ACTIVITY_MONITORING.md) for full documentation
  
- Legacy Streamlit dashboard: `streamlit-chatbot/pages/usage_dashboard.py` → run with `streamlit run streamlit-chatbot/src/app.py`

## Containerization (Docker) 🐳
- Build: `docker build -t bondbot:latest .`
- Run: `docker run --rm -p 8000:8000 -v "$(pwd)/20251215_priceyield.csv:/app/20251215_priceyield.csv" bondbot:latest`
- Compose: `docker-compose up --build -d`

## Deployment 🚢
- Render: deploy the Docker image (safer) or source build; set env vars; mount CSVs or bake them into the image.
- GHCR image (if workflow enabled): `ghcr.io/arifpras/bondbot:latest` and `:SHA`. Pull and run as above; authenticate if private.

## Tests ✅
- `pytest` (API coverage in `tests/` including `tests/test_app_fastapi.py`)