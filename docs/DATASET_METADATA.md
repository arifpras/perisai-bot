# Dataset Metadata: 20251215_priceyield.csv

- Scope: Indonesian domestic government bonds (INDOGB)
- Instruments: FR-series government bonds (e.g., FR95–FR104)
- Metrics: Daily end-of-day `price` and `yield`
- Tenors: 5-year, 10-year (and additional where available)
- Columns: `date`, `series`, `tenor`, `price`, `yield`
- Format: CSV with header row; no comment lines
- Ingestion: Loaded via DuckDB (`read_csv_auto`) by `BondDB` in `priceyield_20251223.py`
- Notes:
  - Extra columns are safe; they are ignored by the views used in-app.
  - Avoid changing column names; downstream queries expect the exact headers.
  - Data is used across `/kei`, `/kin`, and `/both` personas for bond price/yield queries and forecasts.
