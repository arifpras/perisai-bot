# Bond Price & Yield Assistant

Indonesian government bond analysis via Telegram. Dual AI personas: **Kei** (quantitative) and **Kin** (macro/policy).

**Features:**
- Historical prices/yields (2023-2025), multi-tenor queries
- 7-model ensemble forecasting (ARIMA, ETS, Prophet, VAR, MA5, Random Walk, Monte Carlo)
- Economist-style tables and charts
- Macro context and policy analysis
- Auction demand forecasts

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
| `/kei` | Quantitative analysis | `/kei yield 5 year Feb 2025` |
| `/kin` | Macro/policy context | `/kin fiscal policy impact` |
| `/both` | Combined analysis | `/both compare 5 and 10 year 2024 vs 2025` |
| `/check` | Quick lookup | `/check 2025-12-27 10 year` |

**Table Format:** Add `tab` to `/kei` queries for formatted tables with summary statistics.

## Auction Tab Queries

- Incoming totals:
	- `/kei tab incoming bid in May 2025`
	- `/kei tab incoming bid in May 2025 and Jun 2025`
	- `/kei tab incoming bid from Q2 2025 to Q2 2026`
	- `/kei tab incoming bid from 2024 to 2025`

- Awarded totals:
	- `/kei tab awarded bid from Apr 2026 to Jun 2026`

- Incoming and Awarded:
	- `/kei tab incoming and awarded bid from Q2 2026 to Q3 2026`

Tables render in Economist-style monospace with borders. Periods can be months (names or numbers), quarters (Q1–Q4), or years. Data loads forecast-first and falls back to historical where available.

## Output Format

**Tables:** Right-aligned numeric columns with summary statistics (Count/Min/Max/Avg/Std)
```
/kei tab yield 5 and 10 year Feb 2025

Date         |     05Y |     10Y  
───────────────────────────────
2025-02-01   |    5.45 |    5.62
2025-02-02   |    5.46 |    5.63

Summary Statistics:
Count        |      20 |      20
Min          |    5.42 |    5.58
Max          |    5.52 |    5.72
Avg          |    5.47 |    5.65
Std          |    0.03 |    0.04
```

**Charts:** Economist-style aesthetics (gray background, white gridlines, left-aligned typography)

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

**Current Version:** `v2025.12.28-stable-tables`