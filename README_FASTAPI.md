# FastAPI wrapper for bond queries ✅

This document explains how to run the small FastAPI server to expose the bond query functionality.

Prerequisites
- Activate the project's Python venv (Python 3.12) e.g.: `source .venv/bin/activate`
- Install fastapi and uvicorn (if not already installed):

```bash
pip install fastapi uvicorn
```

Run the server

```bash
uvicorn app_fastapi:app --reload --host 127.0.0.1 --port 8000
```

Endpoints
- GET /health → {"status":"ok"}
- POST /query → body: {"q": "average yield Q1 2023", "csv": "20251215_priceyield.csv"}
- POST /chat  → body: {"q": "what's the yield of 10 year on 2 May 2023", "plot": false}
- POST /plot  → body: {"q": "10 year 2023"} (returns PNG image)
- GET /ui     → Minimal web chat UI (interactive)

Example curl

```bash
curl -s -X POST http://127.0.0.1:8000/query -H 'Content-Type: application/json' --data '{"q":"average yield Q1 2023"}' | jq
```

Chat / UI examples

```bash
# Chat (JSON response)
curl -s -X POST http://127.0.0.1:8000/chat -H 'Content-Type: application/json' --data '{"q":"yield 2023-05-02 10 year"}' | jq

# Request an aggregate and include a plot in the response (base64 image)
curl -s -X POST http://127.0.0.1:8000/chat -H 'Content-Type: application/json' --data '{"q":"average yield 2023", "plot": true}' | jq

# Or visit http://127.0.0.1:8000/ui in your browser for a small chat page
```
Notes
- The server reuses `parse_intent` and `BondDB` from `priceyield_20251223.py` and caches BondDB instances by CSV path. If you need a fresh DB instance, restart the server.
- Tests are available in `tests/test_app_fastapi.py` (run with `pytest`).
- **Forecasting**: Uses 8 models (ARIMA, ETS, RANDOM_WALK, MONTE_CARLO, MA5, VAR, PROPHET, GRU); LSTM removed.
- **Business-day aware**: "Next N observations" queries automatically skip weekends.
- **ARIMA reliability**: 3-level fallback mechanism ensures valid forecasts.

### Environment variables

- Copy `.env.example` to `.env` and fill in required secrets.
- At minimum set `TELEGRAM_BOT_TOKEN` if you want Telegram endpoints enabled.
- `.env` is git-ignored.

```bash
cp .env.example .env
sed -i 's/YOUR_TELEGRAM_BOT_TOKEN/<your-token>/' .env
```

### Docker Compose with `.env`

Docker Compose is configured to load variables from `.env`.

```bash
docker-compose up --build
# visit http://127.0.0.1:8000
```

---

## Containerization (Docker) 🐳

You can build and run the FastAPI app in a container. The container expects the CSV file (by default `20251215_priceyield.csv`) to be available in the working directory; you can mount it into the container with `-v` or copy it into the image.

1) Build the image

```bash
docker build -t bondbot:latest .
```

2) Run the container (mount local CSV into container)

```bash
docker run --rm -p 8000:8000 -v "$(pwd)/20251215_priceyield.csv:/app/20251215_priceyield.csv" bondbot:latest
```

3) Or use Docker Compose

```bash
docker-compose up --build -d
# then visit http://127.0.0.1:8000 (or call the endpoints)
```

Notes:
- The server inside the container listens on port `8000` and serves the same endpoints described above.
- If you don't mount the CSV, the image will still build but you must ensure the default CSV exists inside the image or pass a different `csv` parameter when calling the API.

---

## GitHub Container Registry (GHCR) 🏷️

If you enable the provided GitHub Actions workflow, the job will build and push the image to GitHub Container Registry under `ghcr.io/<owner>/bondbot:latest`.

Pull and run the published image (public image or authenticated if private):

```bash
# pull
docker pull ghcr.io/arifpras/bondbot:latest

# run (mount CSV as needed)
docker run --rm -p 8000:8000 -v "$(pwd)/20251215_priceyield.csv:/app/20251215_priceyield.csv" ghcr.io/arifpras/bondbot:latest
```

If the image is private, authenticate with GHCR first:

```bash
echo "${{ secrets.GHCR_PAT }}" | docker login ghcr.io -u <username> --password-stdin
```

Replace `<owner>` with your GitHub organization or username. To change the pushed tag or registry, edit `.github/workflows/docker-build.yml` accordingly.

---

## Image tag strategy 🏷️

The CI currently pushes two tags for each successful build on `main`:

- **`ghcr.io/arifpras/bondbot:latest`** — a mutable tag pointing to the latest build on `main` (convenient for quick testing).
- **`ghcr.io/arifpras/bondbot:${{ github.sha }}`** — an immutable, commit-specific tag useful for reproducible deployments and debugging.

Recommendations:
- Use the **SHA**-tagged image for deployments that require immutability: `docker run ghcr.io/arifpras/bondbot:<sha>`.
- Keep `:latest` for quick local testing or CI preview environments.
- Optionally add semver tags on releases (e.g., `v1.2.0`) by adding a tagging step to the CI or triggering builds on git tags/releases.

---
