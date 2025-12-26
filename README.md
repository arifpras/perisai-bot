
# Bond Price & Yield Assistant (FastAPI + Telegram) 🏛️

Forecast Indonesian government bond prices, yields, and auction demand using ARIMA, ETS, Prophet, LSTM, GRU, and ensemble ML. Query via API or Telegram. Dual personas: Kei (quant), Kin (macro).

**Forecasting types:**
- Yield/Price: `/kei forecast yield 10 year at the end of 2025`, `/kei predict price 5 year 2026-03-31 use prophet`
- Auction demand: `/kei auction demand January 2026`, `/kei forecast incoming bids Q2 2026`

**/kin persona usage:**
- `/kin` gives macroeconomic, policy, and market context, or explains results in plain English.
- Examples:
	- `/kin explain impact of US rates on Indo bonds`
	- `/kin summarize auction demand drivers 2025`
	- `/kin forecast yield 10 year at the end of 2025` (macro view, HL-CU style)
	- `/kin explain FR95 price movement in plain English`

Fast answers on Indonesian govvies: prices/yields (2023-2025), auction forecasts (through 2026), charts, and dual personas (Kei quant, Kin macro) delivered via API and Telegram.

## Quick start (local) 🚀
- Python 3.12 venv: `source .venv/bin/activate`
- Install deps: `pip install -r requirements.txt`
- Run API: `uvicorn app_fastapi:app --reload --host 127.0.0.1 --port 8000`
- Health check: `curl -s http://127.0.0.1:8000/health`
	- **2025-12-25**: Forecasting now defaults to all models (ARIMA, ETS, Prophet, LSTM, GRU) and returns a table + average unless a specific model is requested.
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
	- Commands: `/kei` (quant), `/kin` (macro), `/both` (chain), `/examples`, `/start`


	- Query patterns: `/kei yield 10 year 2024`, `/kei plot 10 year 2024`, `/kei auction demand 2026`, `/kei average yield 2024`
- **Prophet**
- **LSTM**
- **GRU**
	Supported: ARIMA, ETS, Prophet, LSTM, GRU. By default, all models are used and results are shown in a table with an average and summary. To specify a model, add e.g. `use ets` to your query.
If you want all models and the average, just omit the method or say "use all".

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