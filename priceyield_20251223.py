# priceyield_20251223.py
# FINAL – bug-fixed intent parsing + tenor + interpolation

import re
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from typing import Optional, Literal

import duckdb
import dateparser
from dateutil.relativedelta import relativedelta
import typer
from rich import print
from rich.panel import Panel
from rich.console import Console
import pandas as pd

# -----------------------------
# CLI setup
# -----------------------------
app = typer.Typer(add_completion=False)
console = Console()
CSV_PATH_DEFAULT = "20251215_priceyield.csv"

# -----------------------------
# Intent model
# -----------------------------


@dataclass
class Intent:
    type: str
    metric: str
    series: Optional[str]
    tenor: Optional[str]  # Single tenor (backward compatibility)
    tenors: Optional[list] = None  # Multiple tenors for multi-tenor plots
    point_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    agg: Optional[str] = None
    year: Optional[int] = None
    highlight_date: Optional[date] = None
    forecast_type: Optional[str] = None  # For auction: 'incoming', 'awarded', 'bidtocover'
    forecast_model: Optional[str] = None  # For yield: 'arima', 'ets', 'prophet', 'gru'

# -----------------------------
# Regex (English + Indonesian)
# -----------------------------
SERIES_RE = re.compile(r"\bFR\d+\b", re.IGNORECASE)
# Tenor: English (year/years) + Indonesian (tahun)
TENOR_RE = re.compile(r"\b(\d+)\s*(?:years?|tahun)\b", re.IGNORECASE)
QUARTER_RE = re.compile(r"\bQ([1-4])\s*(\d{4})\b", re.IGNORECASE)
# Month-Year: English months + Indonesian months (Jan/Januari, Feb/Februari, etc.)
MONTH_YEAR_RE = re.compile(
    r"\b(Jan(?:uary|uari)?|Feb(?:ruary|ruari)?|Mar(?:ch|et)?|Apr(?:il)?|May|Mei|"
    r"Jun(?:e|i)?|Jul(?:y|i)?|Aug(?:ust|ustus)?|Sep(?:tember|tember)?|"
    r"Oct(?:ober|ober)?|Nov(?:ember)?|Des(?:ember)?|Dec(?:ember)?)\s+(\d{4})\b",
    re.IGNORECASE,
)
YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")
ISO_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
# Aggregation: English + Indonesian (rata-rata, jumlah, minimum, maksimum)
AGG_RE = re.compile(
    r"\b(avg|average|mean|rata-rata|rataan|sum|total|jumlah|jumblah|min|minimum|minima|"
    r"max|maksimum|maxima|count|hitung)\b",
    re.IGNORECASE
)

# -----------------------------
# Parsing helpers
# -----------------------------
def parse_metric(text: str):
    text_lower = text.lower()
    # English: auction, demand, incoming, awarded
    # Indonesian: lelang, permintaan, masuk, diberikan
    auction_keywords = ['auction', 'demand', 'incoming', 'awarded', 
                       'lelang', 'permintaan', 'masuk', 'diberikan']
    if any(kw in text_lower for kw in auction_keywords):
        return "auction"
    # Default to yield for bond queries (industry standard); only use price if explicitly requested
    return "price" if "price" in text_lower else "yield"

def parse_series(text: str):
    m = SERIES_RE.search(text)
    return m.group(0).upper() if m else None

def parse_tenor(text: str):
    m = TENOR_RE.search(text)
    return f"{int(m.group(1)):02d}_year" if m else None

def parse_tenors(text: str):
    """Extract all tenors mentioned in text (e.g., '5 year and 10 year' -> ['05_year', '10_year']
    Handles patterns like: '5 and 10 years', '5 year and 10 year', '5 year, 10 year', etc."""
    
    # First try to find "X and Y years" pattern (singular or plural)
    and_pattern = re.compile(r"\b(\d+)\s+and\s+(\d+)\s*years?\b", re.IGNORECASE)
    and_match = and_pattern.search(text)
    if and_match:
        tenor1 = f"{int(and_match.group(1)):02d}_year"
        tenor2 = f"{int(and_match.group(2)):02d}_year"
        return [tenor1, tenor2]
    
    # Fallback to original regex findall for other patterns
    matches = TENOR_RE.findall(text)
    if matches:
        return [f"{int(m):02d}_year" for m in matches]
    return None

def parse_agg(text: str):
    m = AGG_RE.search(text)
    if not m:
        return None
    # Map English and Indonesian aggregation keywords to standard forms
    agg_map = {
        # Average
        "avg":"avg", "average":"avg", "mean":"avg",
        "rata-rata":"avg", "rataan":"avg",
        # Sum
        "sum":"sum", "total":"sum",
        "jumlah":"sum", "jumblah":"sum",
        # Min
        "min":"min", "minimum":"min", "minima":"min",
        # Max
        "max":"max", "maksimum":"max", "maxima":"max",
        # Count
        "count":"count", "hitung":"count"
    }
    return agg_map.get(m.group(1).lower())

# No need for safe_parse_date anymore—logic moved into parse_intent

def quarter_range(q, y):
    s = date(y, 1 + (q-1)*3, 1)
    e = s + relativedelta(months=3) - timedelta(days=1)
    return s, e

def monthyear_range(m, y):
    s = date(y, m, 1)
    e = s + relativedelta(months=1) - timedelta(days=1)
    return s, e

def extract_highlight_date(text: str) -> Optional[date]:
    """Extract highlight date from phrases like 'highlight 5 Jan 2023' or 'and highlight 2023-01-05'."""
    # Look for "highlight" keyword followed by a date
    highlight_pattern = r"(?:and\s+)?highlight\s+(\d{4}-\d{2}-\d{2}|\d{1,2}\s+(?:jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|september|oct|october|nov|november|dec|december)\s+\d{4})"
    match = re.search(highlight_pattern, text, re.IGNORECASE)
    if match:
        date_str = match.group(1)
        # Try ISO date first
        try:
            return date.fromisoformat(date_str)
        except ValueError:
            # Try natural language parsing
            dt = dateparser.parse(date_str, settings={"PREFER_DATES_FROM": "past"})
            if dt:
                return dt.date()
    return None


# -----------------------------
# Intent parser (FIXED)
# -----------------------------
def parse_intent(text: str) -> Intent:
    text_lower = text.lower()
    
    # Check for auction-related queries (English + Indonesian)
    # English: auction, demand, incoming, awarded, bid to cover
    # Indonesian: lelang, permintaan, masuk, diberikan, rasio penawaran
    auction_keywords = ['auction', 'demand', 'incoming', 'awarded', 'bid to cover', 'bid-to-cover',
                       'lelang', 'permintaan', 'masuk', 'diberikan', 'rasio penawaran', 'rasio bid']
    is_auction = any(kw in text_lower for kw in auction_keywords)
    
    if is_auction:
        # Determine forecast type (English + Indonesian)
        forecast_type = None
        if 'incoming' in text_lower or 'demand' in text_lower or 'masuk' in text_lower or 'permintaan' in text_lower:
            forecast_type = 'incoming'
        elif 'awarded' in text_lower or 'diberikan' in text_lower:
            forecast_type = 'awarded'
        elif ('bid' in text_lower or 'rasio' in text_lower) and ('cover' in text_lower or 'penawaran' in text_lower):
            forecast_type = 'bidtocover'
        
        # Parse date for auction forecast
        # Try quarter first (e.g., Q1 2026)
        qm = QUARTER_RE.search(text)
        if qm:
            s, e = quarter_range(int(qm.group(1)), int(qm.group(2)))
            return Intent(
                type="AUCTION_FORECAST",
                metric="auction",
                series=None,
                tenor=None,
                tenors=None,
                start_date=s,
                end_date=e,
                forecast_type=forecast_type,
            )
        # Try month-year first
        mm = MONTH_YEAR_RE.search(text)
        if mm:
            m = mm.group(1)[:3].lower()
            mon_map = {
                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
            }
            y = int(mm.group(2))
            s, e = monthyear_range(mon_map[m], y)
            return Intent(
                type="AUCTION_FORECAST",
                metric="auction",
                series=None,
                tenor=None,
                tenors=None,
                start_date=s,
                end_date=e,
                forecast_type=forecast_type,
            )
        
        # Try explicit year range: "from 2010 to 2024"
        yr_range = re.search(r"from\s+(19\d{2}|20\d{2})\s+to\s+(19\d{2}|20\d{2})", text_lower)
        if yr_range:
            y_start = int(yr_range.group(1))
            y_end = int(yr_range.group(2))
            if y_start <= y_end:
                return Intent(
                    type="AUCTION_FORECAST",
                    metric="auction",
                    series=None,
                    tenor=None,
                    tenors=None,
                    start_date=date(y_start, 1, 1),
                    end_date=date(y_end, 12, 31),
                    forecast_type=forecast_type,
                )

        # Try single year fallback
        ym = YEAR_RE.findall(text)
        if ym:
            years = sorted(set(int(y) for y in ym))
            y_val = years[0]
            return Intent(
                type="AUCTION_FORECAST",
                metric="auction",
                series=None,
                tenor=None,
                tenors=None,
                start_date=date(y_val, 1, 1),
                end_date=date(y_val, 12, 31),
                forecast_type=forecast_type,
            )
        
        # Default to all available forecasts
        return Intent(
            type="AUCTION_FORECAST",
            metric="auction",
            series=None,
            tenor=None,
            tenors=None,
            forecast_type=forecast_type,
        )
    
    # First, extract highlight_date before modifying the text
    highlight_date = extract_highlight_date(text)
    
    # Remove the "highlight ..." part from the text so it doesn't interfere with main date parsing
    text_for_parsing = re.sub(r'\s+(?:and\s+)?highlight\s+\d{4}-\d{2}-\d{2}|\s+(?:and\s+)?highlight\s+\d{1,2}\s+(?:jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|september|oct|october|nov|november|dec|december)\s+\d{4}', '', text, flags=re.IGNORECASE)
    
    metric = parse_metric(text_for_parsing)
    series = parse_series(text_for_parsing)
    tenor  = parse_tenor(text_for_parsing)
    tenors = parse_tenors(text_for_parsing)  # Extract all tenors
    agg    = parse_agg(text_for_parsing)

    # Extract forecasting model if specified (for yield forecast)
    forecast_model = None
    for m in ["arima", "ets", "prophet", "gru"]:
        if f"use {m}" in text_for_parsing or f"using {m}" in text_for_parsing:
            forecast_model = m
            break

    # 1) Single date (incl. relative, natural language like "2 may 2023")
    # First try ISO date
    iso_m = ISO_DATE_RE.search(text_for_parsing)
    if iso_m:
        try:
            d = date.fromisoformat(iso_m.group(0))
            return Intent(
                type="POINT",
                metric=metric,
                series=series,
                tenor=tenor,
                tenors=tenors,
                point_date=d,
                highlight_date=highlight_date,
                forecast_model=forecast_model,
            )
        except ValueError:
            pass
    
    # Then try dateparser on natural language dates
    # Extract potentially date-like segments: sequences with numbers, month names, years
    # Example: "yield 10 year 2 may 2023" -> try "2 may 2023"
    # IMPORTANT: Only match day-month-year (not month-year), which will be handled below
    day_month_year_match = re.search(
        r"\d{1,2}\s+(?:jan|january|feb|february|mar|march|apr|april|may|jun|june|"
        r"jul|july|aug|august|sep|september|oct|october|nov|november|dec|december)\s+\d{4}",
        text_for_parsing,
        re.IGNORECASE,
    )
    if day_month_year_match:
        date_str = day_month_year_match.group(0)
        dt = dateparser.parse(date_str, settings={"PREFER_DATES_FROM": "past"})
        if dt:
            return Intent(
                type="POINT",
                metric=metric,
                series=series,
                tenor=tenor,
                tenors=tenors,
                point_date=dt.date(),
                highlight_date=highlight_date,
                forecast_model=forecast_model,
            )

    # 2) Quarter
    qm = QUARTER_RE.search(text_for_parsing)
    if qm:
        s, e = quarter_range(int(qm.group(1)), int(qm.group(2)))
        return Intent(
            type="AGG_RANGE" if agg else "RANGE",
            metric=metric,
            series=series,
            tenor=tenor,
            tenors=tenors,
            start_date=s,
            end_date=e,
            agg=agg,
            highlight_date=highlight_date,
            forecast_model=forecast_model,
        )

    # 3) Month-year
    mm = MONTH_YEAR_RE.search(text_for_parsing)
    if mm:
        m = mm.group(1)[:3].lower()
        y = int(mm.group(2))
        month = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,
                 "jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}[m]
        s, e = monthyear_range(month, y)
        return Intent(
            type="AGG_RANGE" if agg else "RANGE",
            metric=metric,
            series=series,
            tenor=tenor,
            tenors=tenors,
            start_date=s,
            end_date=e,
            agg=agg,
            highlight_date=highlight_date,
            forecast_model=forecast_model,
        )

    # 4) Year-only (range even without aggregation)
    ym = YEAR_RE.findall(text_for_parsing)
    if ym:
        # Convert to integers and get min/max for range handling (e.g., "2024 and 2025")
        years = sorted(set(int(y) for y in ym))
        start_year = years[0]
        end_year = years[-1]
        return Intent(
            type="AGG_RANGE" if agg else "RANGE",
            metric=metric,
            series=series,
            tenor=tenor,
            tenors=tenors,
            start_date=date(start_year, 1, 1),
            end_date=date(end_year, 12, 31),
            agg=agg,
            highlight_date=highlight_date,
            forecast_model=forecast_model,
        )

    # 5) Fallback: if a tenor/series is provided but no date, default to YTD range
    if tenor or series:
        today = date.today()
        return Intent(
            type="AGG_RANGE" if agg else "RANGE",
            metric=metric,
            series=series,
            tenor=tenor,
            tenors=tenors,
            start_date=date(today.year, 1, 1),
            end_date=today,
            agg=agg,
            highlight_date=highlight_date,
            forecast_model=forecast_model,
        )

    raise ValueError("Could not identify a valid date or period.")

# -----------------------------
# DuckDB backend
# -----------------------------
class BondDB:
    def __init__(self, csv):
        self.con = duckdb.connect(":memory:")
        # Load raw timeseries
        self.con.execute(f"""
            CREATE VIEW ts_raw AS
            SELECT
                COALESCE(TRY_CAST(date AS DATE),
                         STRPTIME(CAST(date AS VARCHAR),'%d/%m/%Y')::DATE) AS obs_date,
                UPPER(series) AS series,
                tenor,
                TRY_CAST(price AS DOUBLE) AS price,
                TRY_CAST("yield" AS DOUBLE) AS "yield"
            FROM read_csv_auto('{csv}', header=True)
        """)

        # Create a view that selects the last-known price/yield per series as of each observed date.
        # Use correlated subqueries to pick the most recent non-null value <= the date (correct LOCF behavior).
        self.con.execute(f"""
            CREATE VIEW ts AS
            SELECT
                tr.obs_date,
                tr.series,
                tr.tenor,
                (
                  SELECT r.price
                  FROM ts_raw r
                  WHERE r.series = tr.series
                    AND r.obs_date <= tr.obs_date
                    AND r.price IS NOT NULL
                  ORDER BY r.obs_date DESC
                  LIMIT 1
                ) AS price,
                (
                  SELECT r."yield"
                  FROM ts_raw r
                  WHERE r.series = tr.series
                    AND r.obs_date <= tr.obs_date
                    AND r."yield" IS NOT NULL
                  ORDER BY r.obs_date DESC
                  LIMIT 1
                ) AS "yield"
            FROM (
              SELECT DISTINCT obs_date, series, tenor FROM ts_raw
            ) tr
            ORDER BY tr.series, tr.obs_date
        """)

    def aggregate(self, s, e, metric, agg, series, tenor):
        cond, params = [], [s.isoformat(), e.isoformat()]
        if series: cond.append("series=?"); params.append(series)
        if tenor:  cond.append("tenor=?");  params.append(tenor)
        where = " AND ".join(cond)
        fn = {"avg":"AVG","sum":"SUM","min":"MIN","max":"MAX","count":"COUNT"}[agg]
        q = f"""
            SELECT {fn}({metric}), COUNT({metric})
            FROM ts
            WHERE obs_date BETWEEN ? AND ?
            {("AND "+where) if where else ""}
        """
        return self.con.execute(q, params).fetchone()

    def coverage(self):
        """Return (min_date, max_date) coverage of ts_raw, or (None, None) if empty."""
        try:
            row = self.con.execute("SELECT MIN(obs_date), MAX(obs_date) FROM ts_raw").fetchone()
            if not row:
                return (None, None)
            return row[0], row[1]
        except Exception:
            return (None, None)


# -----------------------------
# Auction Forecast DB
# -----------------------------
class AuctionDB:
    def __init__(self, csv):
        self.con = duckdb.connect(":memory:")
        # Load auction forecast data
        self.con.execute(f"""
            CREATE VIEW auction_forecast AS
            SELECT
                TRY_CAST(date AS DATE) AS forecast_date,
                auction_month,
                auction_year,
                TRY_CAST(bi_rate AS DOUBLE) AS bi_rate,
                TRY_CAST(yield01_ibpa AS DOUBLE) AS yield01_ibpa,
                TRY_CAST(yield05_ibpa AS DOUBLE) AS yield05_ibpa,
                TRY_CAST(yield10_ibpa AS DOUBLE) AS yield10_ibpa,
                TRY_CAST(inflation_rate AS DOUBLE) AS inflation_rate,
                TRY_CAST(idprod_rate AS DOUBLE) AS idprod_rate,
                TRY_CAST(incoming_billions AS DOUBLE) AS incoming_billions,
                TRY_CAST(awarded_billions AS DOUBLE) AS awarded_billions,
                TRY_CAST(bid_to_cover AS DOUBLE) AS bid_to_cover,
                TRY_CAST(number_series AS INTEGER) AS number_series,
                TRY_CAST(move AS DOUBLE) AS move,
                TRY_CAST(forh_avg AS DOUBLE) AS forh_avg
            FROM read_csv_auto('{csv}', header=True)
        """)

    def query_forecast(self, intent: Intent):
        """Query auction forecasts based on intent."""
        where_parts = []

        if intent.start_date and intent.end_date:
            where_parts.append(f"forecast_date BETWEEN '{intent.start_date}' AND '{intent.end_date}'")
        elif intent.start_date:
            where_parts.append(f"forecast_date >= '{intent.start_date}'")

        where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

        query = f"""
            SELECT
                forecast_date AS date,
                auction_month,
                auction_year,
                bi_rate,
                inflation_rate,
                incoming_billions,
                awarded_billions,
                bid_to_cover,
                number_series,
                yield01_ibpa,
                yield05_ibpa,
                yield10_ibpa
            FROM auction_forecast
            {where_clause}
            ORDER BY forecast_date
        """

        result = self.con.execute(query).fetchall()
        columns = ['date', 'auction_month', 'auction_year', 'bi_rate', 'inflation_rate',
                   'incoming_billions', 'awarded_billions', 'bid_to_cover', 'number_series',
                   'yield01_ibpa', 'yield05_ibpa', 'yield10_ibpa']
        return [dict(zip(columns, row)) for row in result]

    def coverage(self):
        """Return (min_date, max_date) coverage of auction_forecast, or (None, None) if empty."""
        try:
            row = self.con.execute("SELECT MIN(forecast_date), MAX(forecast_date) FROM auction_forecast").fetchone()
            if not row:
                return (None, None)
            return row[0], row[1]
        except Exception:
            return (None, None)

# --- Unified Yield Forecast API ---
from yield_forecast_models import (
    forecast_arima,
    forecast_ets,
    forecast_prophet,
    forecast_random_walk,
    forecast_monte_carlo,
    forecast_ma5,
    forecast_var,
)

def yield_forecast(series: pd.Series, forecast_date: date, method: str = "all", **kwargs):
    """
    Forecast yield using selected method.
    method: 'arima', 'ets', 'prophet', 'gru'
    series: pandas Series with datetime index
    forecast_date: target date for forecast
    kwargs: model-specific parameters
    """
    # Limit to the most recent 240 observations for forecasting stability
    series = series.tail(240)
    if method == "all":
        results = {}
        vals = []
        # Require minimum history for certain models; with 240 obs we allow Prophet and keep deep nets if enough data
        model_plan = ["arima", "ets", "random_walk", "monte_carlo", "ma5", "var"]
        if len(series) >= 90:
            model_plan.append("prophet")
        else:
            results["prophet"] = "skipped: need >=90 obs"

        if len(series) >= 150:
            model_plan.extend(["gru"])
        else:
            results["gru"] = "skipped: need >=150 obs"

        for m in model_plan:
            try:
                res = yield_forecast(series, forecast_date, method=m, **kwargs)
                # ARIMA returns (forecast, conf_int), others just forecast
                val = res[0] if isinstance(res, tuple) else res
                results[m] = val
                if isinstance(val, (int, float)):
                    vals.append(val)
            except Exception as e:
                results[m] = str(e)

        if vals:
            # Remove negative and MAD outlier forecasts before averaging
            ser = pd.Series(vals)
            ser = ser[ser >= 0]
            if not ser.empty:
                med = ser.median()
                mad = (ser - med).abs().median()
                if mad == 0:
                    filtered = ser.tolist()
                else:
                    filtered = ser[abs(ser - med) <= 3 * mad].tolist()
                chosen = filtered if filtered else ser.tolist()
                results["average"] = sum(chosen) / len(chosen)
            else:
                results["average"] = None
        else:
            results["average"] = None
        return results
    if method == "arima":
        return forecast_arima(series, forecast_date, **kwargs)
    elif method == "ets":
        return forecast_ets(series, forecast_date, **kwargs)
    elif method == "prophet":
        return forecast_prophet(series, forecast_date)
    elif method == "random_walk":
        return forecast_random_walk(series, forecast_date)
    elif method == "monte_carlo":
        return forecast_monte_carlo(series, forecast_date, **kwargs)
    elif method == "ma5":
        return forecast_ma5(series, forecast_date)
    elif method == "var":
        return forecast_var(series, forecast_date, **kwargs)
    else:
        raise ValueError(f"Unknown method: {method}")

def get_yield_series(db: BondDB, series: Optional[str], tenor: str) -> pd.Series:
    """Fetch yield series for a tenor. If series is None, aggregate across all series for that tenor."""
    if series:
        q = "SELECT obs_date, \"yield\" FROM ts WHERE series=? AND tenor=? ORDER BY obs_date"
        rows = db.con.execute(q, [series, tenor]).fetchall()
    else:
        # Aggregate by tenor only; average across all series per date to ignore series dimension
        q = """
            SELECT obs_date, AVG("yield") AS "yield"
            FROM ts
            WHERE tenor=?
            GROUP BY obs_date
            ORDER BY obs_date
        """
        rows = db.con.execute(q, [tenor]).fetchall()
    dates = [r[0] for r in rows]
    yields = [r[1] for r in rows]
    s = pd.Series(yields, index=pd.to_datetime(dates))
    s = s.dropna()
    return s

def get_metric_series(db: BondDB, series: Optional[str], tenor: str, metric: str = "yield") -> pd.Series:
    """Fetch price or yield series for a tenor. If series is None, aggregate across all series for that tenor."""
    metric_col = '"yield"' if metric == "yield" else "price"
    if series:
        q = f"SELECT obs_date, {metric_col} FROM ts WHERE series=? AND tenor=? ORDER BY obs_date"
        rows = db.con.execute(q, [series, tenor]).fetchall()
    else:
        # Aggregate by tenor only; average across all series per date to ignore series dimension
        q = f"""
            SELECT obs_date, AVG({metric_col}) AS metric_val
            FROM ts
            WHERE tenor=?
            GROUP BY obs_date
            ORDER BY obs_date
        """
        rows = db.con.execute(q, [tenor]).fetchall()
    dates = [r[0] for r in rows]
    values = [r[1] for r in rows]
    s = pd.Series(values, index=pd.to_datetime(dates))
    s = s.dropna()
    return s
def forecast_tenor_next_days(db: BondDB, tenor: str, days: int = 3, last_obs_count: int = 5, series: Optional[str] = None):
        """Return latest observations and forecasts for the next consecutive BUSINESS days for a tenor.
        Ignores series when series=None by averaging across all series per date.
        Output:
            {
                'last_obs': [(date, value), ...],
                'forecasts': [{'date': date, 'average': avg, 'models': results_dict}, ...]
            }
        """
        s = get_yield_series(db, series, tenor)
        if s.empty:
                return {'last_obs': [], 'forecasts': []}
        last_obs = list(zip(s.tail(last_obs_count).index.date.tolist(), s.tail(last_obs_count).tolist()))
        last_date = s.index.max().date()
        # Generate next business-day dates (skip weekends)
        start_bday = pd.to_datetime(last_date) + pd.offsets.BDay(1)
        bdays = pd.bdate_range(start=start_bday, periods=days)
        out = []
        for idx, target_ts in enumerate(bdays, start=1):
            target = target_ts.date()
            res = yield_forecast(s, target, method='all')
            out.append({'label': f"T+{idx}", 'date': target, 'average': res.get('average'), 'models': res})
        return {'last_obs': last_obs, 'forecasts': out}

def forecast_metric_next_days(db: BondDB, tenor: str, metric: str = "yield", days: int = 3, last_obs_count: int = 5, series: Optional[str] = None):
    """Return latest observations and forecasts for the next consecutive BUSINESS days for a tenor.
    Supports both price and yield forecasting.
    Ignores series when series=None by averaging across all series per date.
    Output:
        {
            'last_obs': [(date, value), ...],
            'forecasts': [{'date': date, 'average': avg, 'models': results_dict}, ...]
        }
    """
    s = get_metric_series(db, series, tenor, metric=metric)
    if s.empty:
        return {'last_obs': [], 'forecasts': []}
    last_obs = list(zip(s.tail(last_obs_count).index.date.tolist(), s.tail(last_obs_count).tolist()))
    last_date = s.index.max().date()
    # Generate next business-day dates (skip weekends)
    start_bday = pd.to_datetime(last_date) + pd.offsets.BDay(1)
    bdays = pd.bdate_range(start=start_bday, periods=days)
    out = []
    for idx, target_ts in enumerate(bdays, start=1):
        target = target_ts.date()
        res = yield_forecast(s, target, method='all')
        out.append({'label': f"T+{idx}", 'date': target, 'average': res.get('average'), 'models': res})
    return {'last_obs': last_obs, 'forecasts': out}
# Example usage in pipeline:
# series = 'FR100'
# tenor = '10_year'
# target_date = date(2024,12,31)
# s = get_yield_series(db, series, tenor)
# forecast = yield_forecast(s, target_date, method='arima')
# print(forecast)

# -----------------------------
# CLI
# -----------------------------
def answer(db, q):
    intent = parse_intent(q)

    if intent.type in ("RANGE","AGG_RANGE"):
        if not intent.agg:
            print(Panel(
                f"Range query detected:\n{intent.start_date} → {intent.end_date}\n"
                f"(Use 'average/sum/min/max' to aggregate)",
                title="Range"
            ))
            return

        val, n = db.aggregate(
            intent.start_date,
            intent.end_date,
            intent.metric,
            intent.agg,
            intent.series,
            intent.tenor,
        )
        print(Panel(
            f"{intent.agg.upper()} {intent.metric} "
            f"{f'({intent.series}) ' if intent.series else ''}"
            f"{f'[{intent.tenor}] ' if intent.tenor else ''}"
            f"{intent.start_date} → {intent.end_date}\n"
            f"Result: {val}\nN={n}",
            title="Aggregation"
        ))

@app.command()
def chat(csv: str = CSV_PATH_DEFAULT):
    db = BondDB(csv)
    print(Panel("Bond CLI ready. Type 'exit' to quit.", title="Ready"))
    while True:
        q = console.input("[bold cyan]You[/bold cyan]: ")
        if q.lower() in ("exit","quit"):
            break
        answer(db, q)

# Guard the Typer CLI from running inside interactive notebook kernels where
# kernel argv flags conflict with Typer/Click parsing.
if __name__ == "__main__":
    import sys
    if "ipykernel" in sys.modules:
        print("Notebook environment detected; skipping CLI app() call.")
    else:
        app()
