# Bond Price & Yield Assistant (FastAPI + Telegram) 🏛️

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

### Response format
- **Text answers**: Headline (with context-relevant emoji), blank line, then 3-paragraph analysis
  - 💹 Kei: Quantitative, factual, data-driven
  - 🌍 Kin: Macro context, policy implications, forward-looking
  - ⚡ Both: Data facts (Kei) + strategic interpretation (Kin)
- **Plot requests**: Chart image (minimal caption) + full analysis as separate message (no truncation)

### Local testing
```bash
python telegram_bot.py  # Requires: OPENAI_API_KEY, PERPLEXITY_API_KEY, TELEGRAM_BOT_TOKEN, API_BASE_URL
```

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