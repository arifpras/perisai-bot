# Bond Price & Yield Assistant (FastAPI + Telegram) ✅

Fast answers on Indonesian govvies: prices/yields (2023-2025), auction forecasts (through 2026), charts, and dual personas (Kei quant, Kin macro) delivered via API and Telegram.

## Quick start (local)
- Python 3.12 venv: `source .venv/bin/activate`
- Install deps: `pip install -r requirements.txt`
- Run API: `uvicorn app_fastapi:app --reload --host 127.0.0.1 --port 8000`
- Health check: `curl -s http://127.0.0.1:8000/health`

## Env vars
- `OPENAI_API_KEY` (Kei)
- `PERPLEXITY_API_KEY` (Kin)
- `TELEGRAM_BOT_TOKEN` (bot access)
- `API_BASE_URL` (bot → FastAPI, default `http://127.0.0.1:8000`)
- `ALLOWED_USER_IDS` (comma-separated Telegram user IDs; empty = allow all)

## Data files
- Bond history: `20251215_priceyield.csv`
- Auction forecasts: `20251224_auction_forecast.csv`
- Ensemble weights: `WEIGHTED_ENSEMBLE_SUMMARY.md`

## API endpoints
- GET `/health` → status
- POST `/query` → `{"q": "average yield Q1 2023", "csv": "20251215_priceyield.csv"}`
- POST `/chat`  → `{"q": "yield 10 year 2023-05-02", "plot": false, "persona": "kei|kin|both"}`
- POST `/plot`  → `{"q": "10 year 2023"}` (PNG)
- GET `/ui`     → minimal chat page

## Telegram bot
- Commands: `/kei`, `/kin`, `/both`, `/examples`, `/start`
- Plots: include `plot|chart|show|graph|visualize` in the question
- Personas: Kei = dataset-only quant; Kin = macro strategist (search-enabled); Both = chained
- Run locally (example): `python telegram_bot.py` (ensure env vars above and API running)

## Usage logging & dashboard
- Logging: `usage_store.py` (SQLite) via metrics hooks in bot/API
- Dashboard: `streamlit-chatbot/pages/usage_dashboard.py` → run with `streamlit run streamlit-chatbot/src/app.py`

## Containerization (Docker) 🐳
- Build: `docker build -t bondbot:latest .`
- Run: `docker run --rm -p 8000:8000 -v "$(pwd)/20251215_priceyield.csv:/app/20251215_priceyield.csv" bondbot:latest`
- Compose: `docker-compose up --build -d`

## Deployment
- Render: deploy the Docker image (safer) or source build; set env vars; mount CSVs or bake them into the image.
- GHCR image (if workflow enabled): `ghcr.io/arifpras/bondbot:latest` and `:SHA`. Pull and run as above; authenticate if private.

## Tests
- `pytest` (API coverage in `tests/` including `tests/test_app_fastapi.py`)