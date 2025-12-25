## Forecasting Types & Prompt Guide

There are two types of forecasting supported:

1. **Yield/Price Forecasting (Traditional Models)**
	 - Uses ARIMA, ETS, Prophet, LSTM, GRU
	 - Prompts: Use keywords like `yield`, `price`, `forecast`, `predict`, `estimate`, and specify series/tenor/date.
	 - **Examples:**
		 - `/kei forecast yield 10 year at the end of 2025`
		 - `/kei predict price 5 year 2026-03-31 use prophet`
		 - `/kei estimate yield 10 year 2025 using ets`

2. **Auction Demand Forecasting (Ensemble ML)**
	 - Uses ensemble ML models (Random Forest, Gradient Boosting, AdaBoost, etc.)
	 - Prompts: Use keywords like `auction`, `demand`, `incoming bid`, `awarded`, `bid-to-cover`, `lelang`, `permintaan`, etc.
	 - **Examples:**
		 - `/kei auction demand January 2026`
		 - `/kei forecast incoming bids Q2 2026`
		 - `/kei bid-to-cover 2025`

The bot automatically detects the type based on your prompt keywords and routes to the correct forecasting logic.
# Bond Price & Yield Assistant (FastAPI + Telegram) 🏛️

## Historic Changes

- **2025-12-25**: Forecasting now defaults to using all models (ARIMA, ETS, Prophet, LSTM, GRU) and returns an average unless a specific model is requested. Example prompts and /examples updated. Sanity check passed, deployment ready (see SANITY_CHECK_REPORT.txt).

Fast answers on Indonesian govvies: prices/yields (2023-2025), auction forecasts (through 2026), charts, and dual personas (Kei quant, Kin macro) delivered via API and Telegram.

## Quick start (local) 🚀
- Python 3.12 venv: `source .venv/bin/activate`
- Install deps: `pip install -r requirements.txt`
- Run API: `uvicorn app_fastapi:app --reload --host 127.0.0.1 --port 8000`
- Health check: `curl -s http://127.0.0.1:8000/health`

## Env vars ⚙️
- `OPENAI_API_KEY` (Kei)
- `PERPLEXITY_API_KEY` (Kin)
- `TELEGRAM_BOT_TOKEN` (bot access)
- `API_BASE_URL` (bot → FastAPI, default `http://127.0.0.1:8000`)
- `ALLOWED_USER_IDS` (comma-separated Telegram user IDs; empty = allow all)

## Data files 📊
- Bond history: `20251215_priceyield.csv`
- Auction forecasts: `20251224_auction_forecast.csv`
- Ensemble weights: `WEIGHTED_ENSEMBLE_SUMMARY.md`

## API endpoints 🔌
- GET `/health` → status
- POST `/query` → `{"q": "average yield Q1 2023", "csv": "20251215_priceyield.csv"}`
- POST `/chat`  → `{"q": "yield 10 year 2023-05-02", "plot": false, "persona": "kei|kin|both"}`
- POST `/plot`  → `{"q": "10 year 2023"}` (PNG)
- GET `/ui`     → minimal chat page

## Telegram bot 💬

### Commands
- `/kei` — Quant analyst (data-driven, ChatGPT-powered)
- `/kin` — Macro strategist (context-aware, Perplexity-powered with search)
- `/both` — Chain both personas: Kei → Kin (data first, then macro insight)
- `/examples` — Show example queries
- `/start` — Welcome message

### Query patterns
- **Single tenor**: `/kei yield 10 year 2024` or `/kei 5 year Q1 2025`
- **Multi-tenor comparison**: `/kei yield 5 and 10 years 2024` (retrieves both tenors for analysis)
- **Plot request**: Include `plot|chart|show|graph|visualize` → `/kei plot 10 year 2024` (returns chart + analysis)
- **Date formats**: Year (2024), quarter (Q1 2024), month (May 2024), specific date (6 Dec 2024)
- **Tenure range**: Average/aggregate → `/kei average yield 2024` (full year avg)


## Yield Forecasting Methods

The bot supports multiple forecasting methods for Indonesian government bond yields:
- **ARIMA**
- **ETS**
- **Prophet**
- **LSTM**
- **GRU**

**Default behavior:** If you do not specify a method, the bot will use all models and return both individual results and the average.

You can request a specific method in your query. Example queries:
- `/kei forecast yield 10 year at the end of 2025` (returns all models + average)
- `/kei forecast yield 10 year at the end of 2025 use ets` (returns only ETS)
- `/kei forecast yield 5 year December 2025 using prophet` (returns only Prophet)

If you want all models and the average, just omit the method or say "use all".

## Supported Data
- Indonesian government bond prices and yields (2023-2025): FR95-FR104 series (5Y/10Y tenors)
- Auction demand forecasts (bids, awarded, bid-to-cover) through 2026 (ensemble ML: XGBoost, Random Forest, time-series, macro features)
- Indonesian macroeconomic indicators (BI rate, inflation, etc.)

## Persona and Response Format
- **Kei**: CFA/MIT quant, concise, headline-led corporate update (HL-CU) style
- **Kin**: More verbose, explanatory, plain English (if requested)
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
- Logging: `usage_store.py` (SQLite) via metrics hooks in bot/API
- Dashboard: `streamlit-chatbot/pages/usage_dashboard.py` → run with `streamlit run streamlit-chatbot/src/app.py`

## Containerization (Docker) 🐳
- Build: `docker build -t bondbot:latest .`
- Run: `docker run --rm -p 8000:8000 -v "$(pwd)/20251215_priceyield.csv:/app/20251215_priceyield.csv" bondbot:latest`
- Compose: `docker-compose up --build -d`

## Deployment 🚢
- Render: deploy the Docker image (safer) or source build; set env vars; mount CSVs or bake them into the image.
- GHCR image (if workflow enabled): `ghcr.io/arifpras/bondbot:latest` and `:SHA`. Pull and run as above; authenticate if private.

## Tests ✅
- `pytest` (API coverage in `tests/` including `tests/test_app_fastapi.py`)