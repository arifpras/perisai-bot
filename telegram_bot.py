"""Telegram Bot Integration for Bond Price & Yield Chatbot
Handles incoming messages from Telegram and formats responses.
"""
import os
import io
import base64
import logging
import re
import time
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import statistics
from typing import Optional, List, Dict
import html as html_module
from openai import AsyncOpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import BadRequest
from telegram.constants import ParseMode
import httpx
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
try:
    import seaborn as sns
except ImportError:
    sns = None

import priceyield_20251223 as priceyield_mod
from priceyield_20251223 import BondDB, AuctionDB, parse_intent
from economist_style import (
    ECONOMIST_COLORS,
    ECONOMIST_PALETTE,
    add_economist_caption,
    apply_economist_style,
)

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Silence Prophet's optional Plotly warning (Telegram uses static PNGs, not Plotly)
try:
    logging.getLogger('prophet.plot').setLevel(logging.CRITICAL)
except Exception:
    pass

# Initialize OpenAI client
_openai_client = None
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if OPENAI_API_KEY:
    _openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
else:
    logger.warning("OPENAI_API_KEY not set - /kei persona will be unavailable")

# Perplexity configuration
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY")
PERPLEXITY_MODEL = os.environ.get("PERPLEXITY_MODEL", "sonar-pro")

# API configuration
# Prefer explicit API_BASE_URL; else use localhost with Render's PORT; else fallback to external URL
_port = os.environ.get("PORT", "8000")
API_BASE_URL = (
    os.environ.get("API_BASE_URL")
    or f"http://localhost:{_port}"
    or os.environ.get("RENDER_EXTERNAL_URL")
)

# Metrics module
try:
    from usage_store import log_query, log_error
    
    class MetricsAdapter:
        """Adapter to provide metrics.log_query and metrics.log_error interface"""
        @staticmethod
        def log_query(*args, **kwargs):
            return log_query(*args, **kwargs)
        
        @staticmethod
        def log_error(*args, **kwargs):
            return log_error(*args, **kwargs)
    
    metrics = MetricsAdapter()
except ImportError as e:
    # Fallback metrics stub if module not available
    class MetricsStub:
        def log_query(self, *args, **kwargs): pass
        def log_error(self, *args, **kwargs): pass
    metrics = MetricsStub()
    logger.warning(f"Could not import usage_store metrics - using stub: {e}")

_db_cache: Dict[str, object] = {}


def strip_markdown_emphasis(text: str) -> str:
    """Remove markdown bold/italic emphasis from text."""
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)  # Remove **bold**
    text = re.sub(r'\*([^\*]+)\*', r'\1', text)      # Remove *italic*
    text = re.sub(r'__([^_]+)__', r'\1', text)       # Remove __bold__
    text = re.sub(r'_([^_]+)_', r'\1', text)         # Remove _italic_
    return text


def html_quote_signature(text: str) -> str:
    """Wrap trailing signature lines in HTML blockquote for Telegram HTML parse mode.

    Removes all duplicate signatures (plain text and blockquote format) and ensures
    exactly one blockquote signature at the end. Handles '~ Kei', '~ Kin', or '~ Kei x Kin'.
    """
    if not isinstance(text, str) or not text:
        return text
    
    # Detect which signature should be used (prioritize 'Kei x Kin' for dual mode)
    signature_type = None
    if 'kei x kin' in text.lower() or 'kei & kin' in text.lower():
        signature_type = 'Kei x Kin'
    elif '~ kin' in text.lower():
        signature_type = 'Kin'
    elif '~ kei' in text.lower():
        signature_type = 'Kei'
    
    if not signature_type:
        return text
    
    # Remove ALL occurrences of signatures (both plain text and blockquote format)
    # This ensures no duplicates remain
    text = re.sub(r'\n*<blockquote>~\s+(Kei|Kin|Kei x Kin|Kei & Kin)</blockquote>\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\n+~\s+(Kei|Kin|Kei x Kin|Kei & Kin)\s*', '', text, flags=re.IGNORECASE)
    
    # Clean up any trailing whitespace
    text = text.rstrip()
    
    # Add exactly one signature at the end
    return f"{text}\n\n<blockquote>~ {signature_type}</blockquote>"


def convert_markdown_code_fences_to_html(text: str) -> str:
    """Convert Markdown triple-backtick code fences to HTML <pre> blocks.

    - Replaces ```...``` blocks with <pre>escaped_content</pre>
    - Escapes &, <, > inside the block to avoid HTML parsing issues.
    - Idempotent for already-converted content (no effect on <pre> blocks).
    """
    if not isinstance(text, str) or not text:
        return text

    def _escape_html(s: str) -> str:
        return (
            s.replace('&', '&amp;')
             .replace('<', '&lt;')
             .replace('>', '&gt;')
        )

    # Regex to capture code fences, optionally with a language hint on the first line
    fence_pattern = re.compile(r"```(?:[a-zA-Z0-9_+-]*\n)?(.*?)```", re.DOTALL)

    def _repl(match: re.Match) -> str:
        content = match.group(1)
        return f"<pre>{_escape_html(content).strip()}</pre>"

    return fence_pattern.sub(_repl, text)



def is_user_authorized(user_id: int) -> bool:
    """Check if a user is authorized to use the bot.
    
    If ALLOWED_USER_IDS environment variable is set (comma-separated list),
    only those users are allowed. Otherwise, all users are authorized.
    """
    allowed_users = os.environ.get("ALLOWED_USER_IDS", "")
    if not allowed_users:
        # No restriction - all users authorized
        return True
    
    # Parse comma-separated list of user IDs
    try:
        allowed_list = [int(uid.strip()) for uid in allowed_users.split(",") if uid.strip()]
        return user_id in allowed_list
    except ValueError:
        # If parsing fails, log and allow all (fail-open)
        logging.warning("Invalid ALLOWED_USER_IDS format, allowing all users")
        return True


def get_db(csv_path: str = "20251215_priceyield.csv") -> BondDB:
    """Get or create a cached BondDB instance."""
    if csv_path not in _db_cache:
        _db_cache[csv_path] = BondDB(csv_path)
    return _db_cache[csv_path]

def get_auction_db(csv_path: str = "20251224_auction_forecast.csv"):
    """Get or create a cached AuctionDB instance."""
    cache_key = f"auction_{csv_path}"
    if cache_key not in _db_cache:
        _db_cache[cache_key] = AuctionDB(csv_path)
    return _db_cache[cache_key]


def get_historical_auction_data(year: int, quarter: int) -> Optional[Dict]:
    """Load historical auction data from auction_train.csv for a specific quarter."""
    try:
        df = pd.read_csv('auction_train.csv')
        
        # Map quarter to months
        quarter_months = {1: [1, 2, 3], 2: [4, 5, 6], 3: [7, 8, 9], 4: [10, 11, 12]}
        months = quarter_months.get(quarter, [])
        
        # Filter for specific year and quarter
        mask = (df['auction_year'] == year) & (df['auction_month'].isin(months))
        quarter_data = df[mask]
        
        if quarter_data.empty:
            return None
        
        # Calculate totals (incoming_bio_log and awarded_bio_log are log base 10 of billions)
        monthly_incoming = []
        monthly_btc = []
        total_awarded = 0.0
        
        for _, row in quarter_data.iterrows():
            incoming_billions = 10 ** row['incoming_bio_log']
            incoming_trillions = incoming_billions / 1000.0
            awarded_billions = 10 ** row['awarded_bio_log'] if pd.notnull(row['awarded_bio_log']) else 0.0
            awarded_trillions = awarded_billions / 1000.0
            monthly_incoming.append({
                'month': int(row['auction_month']),
                'incoming': incoming_trillions,
                'awarded': awarded_trillions,
                'bid_to_cover': row['bid_to_cover']
            })
            monthly_btc.append(row['bid_to_cover'])
            total_awarded += awarded_trillions
        
        total_incoming = sum(m['incoming'] for m in monthly_incoming)
        avg_btc = sum(monthly_btc) / len(monthly_btc) if monthly_btc else 0
        
        return {
            'year': year,
            'quarter': quarter,
            'monthly': monthly_incoming,
            'total_incoming': total_incoming,
            'total_awarded': total_awarded,
            'avg_bid_to_cover': avg_btc
        }
    except Exception as e:
        logger.error(f"Error loading historical auction data: {e}")
        return None


def get_historical_auction_month_data(year: int, month: int) -> Optional[Dict]:
    """Load historical auction data from auction_train.csv for a specific month."""
    try:
        df = pd.read_csv('auction_train.csv')
        mask = (df['auction_year'] == year) & (df['auction_month'] == month)
        month_data = df[mask]
        if month_data.empty:
            return None
        # Single month aggregate
        incoming_vals = []
        awarded_vals = []
        btc_vals = []
        for _, row in month_data.iterrows():
            incoming_vals.append((10 ** row['incoming_bio_log']) / 1000.0)
            awarded_billions = 10 ** row['awarded_bio_log'] if pd.notnull(row['awarded_bio_log']) else 0.0
            awarded_vals.append(awarded_billions / 1000.0)
            btc_vals.append(row['bid_to_cover'])
        total_incoming = sum(incoming_vals)
        total_awarded = sum(awarded_vals)
        avg_btc = sum(btc_vals) / len(btc_vals) if btc_vals else 0
        return {
            'type': 'month',
            'year': year,
            'month': int(month),
            'monthly': [{
                'month': int(month),
                'incoming': total_incoming,
                'awarded': total_awarded,
                'bid_to_cover': avg_btc
            }],
            'total_incoming': total_incoming,
            'total_awarded': total_awarded,
            'avg_bid_to_cover': avg_btc,
        }
    except Exception as e:
        logger.error(f"Error loading historical auction month data: {e}")
        return None


def get_historical_auction_year_data(year: int) -> Optional[Dict]:
    """Load historical auction data from auction_train.csv for a year (sum of months)."""
    try:
        df = pd.read_csv('auction_train.csv')
        year_df = df[df['auction_year'] == year]
        if year_df.empty:
            return None
        monthly_vals = {}
        btc_vals = []
        for _, row in year_df.iterrows():
            m = int(row['auction_month'])
            monthly_vals.setdefault(m, {'incoming': 0.0, 'awarded': 0.0, 'btc_items': []})
            monthly_vals[m]['incoming'] += (10 ** row['incoming_bio_log']) / 1000.0
            awarded_billions = 10 ** row['awarded_bio_log'] if pd.notnull(row['awarded_bio_log']) else 0.0
            monthly_vals[m]['awarded'] += awarded_billions / 1000.0
            monthly_vals[m]['btc_items'].append(row['bid_to_cover'])
            btc_vals.append(row['bid_to_cover'])
        monthly = []
        for m in sorted(monthly_vals.keys()):
            items = monthly_vals[m]
            avg_btc_m = sum(items['btc_items']) / len(items['btc_items']) if items['btc_items'] else 0
            monthly.append({'month': m, 'incoming': items['incoming'], 'awarded': items['awarded'], 'bid_to_cover': avg_btc_m})
        total_incoming = sum(x['incoming'] for x in monthly)
        total_awarded = sum(x['awarded'] for x in monthly)
        avg_btc = sum(btc_vals) / len(btc_vals) if btc_vals else 0
        return {
            'type': 'year',
            'year': year,
            'monthly': monthly,
            'total_incoming': total_incoming,
            'total_awarded': total_awarded,
            'avg_bid_to_cover': avg_btc,
        }
    except Exception as e:
        logger.error(f"Error loading historical auction year data: {e}")
        return None


def _period_label(data: Dict) -> str:
    month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    if data.get('quarter'):
        return f"Q{int(data['quarter'])} {int(data['year'])}"
    if data.get('type') == 'month':
        return f"{month_names[int(data['month'])]} {int(data['year'])}"
    return f"{int(data['year'])}"


def load_auction_period(period: Dict) -> Optional[Dict]:
    """Load auction period data, preferring forecast (AuctionDB) and falling back to historical train CSV.
    period: {'type': 'month'|'quarter'|'year', 'year': int, 'month'?: int, 'quarter'?: int}
    Returns standardized dict: {'type','year','month?'/'quarter?','monthly':[...],'total_incoming','avg_bid_to_cover'}
    """
    try:
        auction_db = get_auction_db()
        year = int(period['year'])
        kind = period['type']
        months_map = {1: [1,2,3], 2: [4,5,6], 3: [7,8,9], 4: [10,11,12]}
        months = []
        if kind == 'month':
            months = [int(period['month'])]
        elif kind == 'quarter':
            months = months_map.get(int(period['quarter']), [])
        elif kind == 'year':
            months = list(range(1, 13))

        forecast_rows = []
        for m in months:
            intent_obj = type('obj', (object,), {
                'start_date': date(year, m, 1),
                'end_date': date(year, m, 28)
            })()
            rows = auction_db.query_forecast(intent_obj)
            if rows:
                forecast_rows.extend(rows)

        if forecast_rows:
            monthly_data = []
            total_incoming = 0.0
            total_awarded = 0.0
            btc_vals = []
            for row in forecast_rows:
                m = int(row['auction_month'])
                inc = float(row['incoming_billions'])
                awd = float(row['awarded_billions']) if row.get('awarded_billions') is not None else None
                btc = float(row['bid_to_cover']) if row.get('bid_to_cover') is not None else 0.0
                md = {'month': m, 'incoming': inc, 'bid_to_cover': btc}
                if awd is not None:
                    md['awarded'] = awd
                    total_awarded += awd
                monthly_data.append(md)
                total_incoming += inc
                btc_vals.append(btc)
            avg_btc = sum(btc_vals) / len(btc_vals) if btc_vals else 0.0
            result = {
                'type': kind,
                'year': year,
                'monthly': sorted(monthly_data, key=lambda x: x['month']),
                'total_incoming': total_incoming,
                'avg_bid_to_cover': avg_btc,
            }
            if total_awarded > 0.0:
                result['total_awarded'] = total_awarded
            if kind == 'month':
                result['month'] = months[0]
            if kind == 'quarter':
                result['quarter'] = int(period['quarter'])
            return result

        # Fallback to historical
        if kind == 'month':
            return get_historical_auction_month_data(year, int(period['month']))
        if kind == 'quarter':
            return get_historical_auction_data(year, int(period['quarter']))
        if kind == 'year':
            return get_historical_auction_year_data(year)
        return None
    except Exception as e:
        logger.error(f"Error loading auction period {period}: {e}")
        return None


def format_auction_metrics_table(periods_data: List[Dict], metrics: List[str]) -> str:
    """Economist-style table for requested metrics across periods.
    Rows: periods (month/quarter/year labels)
    Columns: one or two of ['Incoming','Awarded'] in Rp T
    """
    # Determine columns
    cols = []
    if any(m.strip().lower().startswith('incoming') for m in metrics):
        cols.append('Incoming')
    if any(m.strip().lower().startswith('awarded') for m in metrics):
        cols.append('Awarded')
    if not cols:
        cols = ['Incoming']

    # Compute widths to target a compact overall width
    # Enforce a minimum period label width of 9 and 13-char numeric columns.
    label_width = max(9, max(len(_period_label(p)) for p in periods_data))
    col_width = 13
    sep = " |"  # compact separator (2 chars)
    sep_len = len(sep)
    # Header content length = label + N*col + N*sep_len
    total_width = label_width + len(cols) * col_width + len(cols) * sep_len
    border = '─' * total_width

    # Header
    header = f"{'Period':<{label_width}}{sep}" + sep.join([f"{c:>{col_width}}" for c in cols])

    # Rows
    rows = []
    for p in periods_data:
        label = _period_label(p)
        values = []
        for c in cols:
            if c == 'Incoming':
                val = p.get('total_incoming')
            else:
                val = p.get('total_awarded')
            values.append(f"Rp {val:,.2f}T" if isinstance(val, (int, float)) else '-')
        rows.append(f"{label:<{label_width}}{sep}" + sep.join([f"{v:>{col_width}}" for v in values]))

    rows_box = "\n".join([f"│{r:<{total_width}}│" for r in rows])
    return f"""```
┌{border}┐
│{header:<{total_width}}│
├{border}┤
{rows_box}
└{border}┘
```"""


def parse_auction_table_query(q: str) -> Optional[Dict]:
    """Parse 'tab incoming/awarded bid ...' queries into metrics and periods.
    Returns {'metrics': [..], 'periods': [period_dict,...]} or None.
    Supported connectors: 'from X to Y', 'in X and Y', single 'in X'.
    Period types: month, quarter, year.
    """
    import re
    q = q.lower()
    if 'tab' not in q:
        return None
    # Metrics
    metrics = []
    if 'incoming and awarded' in q:
        metrics = ['incoming', 'awarded']
    else:
        if 'incoming' in q:
            metrics.append('incoming')
        if 'awarded' in q:
            metrics.append('awarded')
    if not metrics:
        metrics = ['incoming']

    # Period parsing helpers
    months_map = {
        'jan':1,'january':1,
        'feb':2,'february':2,
        'mar':3,'march':3,
        'apr':4,'april':4,
        'may':5,
        'jun':6,'june':6,
        'jul':7,'july':7,
        'aug':8,'august':8,
        'sep':9,'sept':9,'september':9,
        'oct':10,'october':10,
        'nov':11,'november':11,
        'dec':12,'december':12,
    }
    def parse_one_period(text: str) -> Optional[Dict]:
        text = text.strip()
        m = re.match(r'^q(\d)\s+(\d{4})$', text)
        if m:
            qn, yr = map(int, m.groups())
            return {'type': 'quarter', 'quarter': qn, 'year': yr}
        m = re.match(r'^(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|\d{1,2})\s+(\d{4})$', text)
        if m:
            mo, yr = m.groups()
            mo = months_map[mo] if mo in months_map else int(mo)
            return {'type': 'month', 'month': mo, 'year': int(yr)}
        m = re.match(r'^(\d{4})$', text)
        if m:
            return {'type': 'year', 'year': int(m.group(1))}
        return None

    periods: List[Dict] = []
    # from X to Y: expand range
    m_from = re.search(r'from\s+(.+?)\s+to\s+(.+)$', q)
    if m_from:
        p1 = parse_one_period(m_from.group(1))
        p2 = parse_one_period(m_from.group(2))
        if p1 and p2:
            # Expand range based on type
            if p1['type'] == 'year' and p2['type'] == 'year':
                y1, y2 = p1['year'], p2['year']
                periods = [{'type': 'year', 'year': y} for y in range(y1, y2 + 1)]
            elif p1['type'] == 'quarter' and p2['type'] == 'quarter':
                # Expand quarters across years if needed
                periods = []
                (y1, q1), (y2, q2) = (p1['year'], p1['quarter']), (p2['year'], p2['quarter'])
                for y in range(y1, y2 + 1):
                    q_start = q1 if y == y1 else 1
                    q_end = q2 if y == y2 else 4
                    for q in range(q_start, q_end + 1):
                        periods.append({'type': 'quarter', 'quarter': q, 'year': y})
            elif p1['type'] == 'month' and p2['type'] == 'month':
                # Expand months across years if needed
                from dateutil.relativedelta import relativedelta
                start_date = date(p1['year'], p1['month'], 1)
                end_date = date(p2['year'], p2['month'], 1)
                periods = []
                current = start_date
                while current <= end_date:
                    periods.append({'type': 'month', 'month': current.month, 'year': current.year})
                    current += relativedelta(months=1)
            else:
                # Type mismatch; just use endpoints
                periods = [p1, p2]
            return {'metrics': metrics, 'periods': periods}
    # in X and Y
    m_and = re.search(r'in\s+(.+?)\s+and\s+(.+)$', q)
    if m_and:
        p1 = parse_one_period(m_and.group(1))
        p2 = parse_one_period(m_and.group(2))
        if p1 and p2:
            periods = [p1, p2]
            return {'metrics': metrics, 'periods': periods}
    # single in X
    m_in = re.search(r'in\s+(.+)$', q)
    if m_in:
        p1 = parse_one_period(m_in.group(1))
        if p1:
            periods = [p1]
            return {'metrics': metrics, 'periods': periods}
    # fallback year-to-year without explicit 'in'
    m_years = re.findall(r'\b(\d{4})\b', q)
    if m_years and 'from' not in q and 'in' not in q:
        years = [int(y) for y in m_years][:3]
        if len(years) >= 2:
            periods = [{'type': 'year', 'year': y} for y in years]
            return {'metrics': metrics, 'periods': periods}
    return None


def format_auction_comparison_general(periods_data: List[Dict]) -> str:
    """Format comparison across two or more periods (month/quarter/year). Baseline is first period."""
    if not periods_data:
        return "No data found."
    lines = []
    month_names = ['', 'Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    # Sections per period
    for pdata in periods_data:
        label = _period_label(pdata)
        lines.append(f"<b>{label} Auction Demand:</b>")
        for m in pdata.get('monthly', []):
            lines.append(f"• {month_names[m['month']]}: Rp {m['incoming']:.2f}T | {m['bid_to_cover']:.2f}x bid-to-cover")
        lines.append(f"<b>Total:</b> Rp {pdata['total_incoming']:.2f}T | Avg BtC: {pdata['avg_bid_to_cover']:.2f}x")
        lines.append("")
    lines.append("─" * 50)
    # Changes vs baseline
    base = periods_data[0]
    for idx, pdata in enumerate(periods_data[1:], start=2):
        inc_chg = ((pdata['total_incoming'] / base['total_incoming']) - 1) * 100 if base['total_incoming'] else 0.0
        btc_chg = ((pdata['avg_bid_to_cover'] / base['avg_bid_to_cover']) - 1) * 100 if base['avg_bid_to_cover'] else 0.0
        lines.append(f"<b>Change vs { _period_label(base) } → { _period_label(pdata) }:</b>")
        lines.append(f"• Incoming bids: {inc_chg:+.1f}% (Rp {base['total_incoming']:.0f}T → Rp {pdata['total_incoming']:.0f}T)")
        lines.append(f"• Bid-to-cover: {btc_chg:+.1f}% ({base['avg_bid_to_cover']:.2f}x → {pdata['avg_bid_to_cover']:.2f}x)")
        lines.append("")
    lines.append("<blockquote>~ Kei</blockquote>")
    return "\n".join(lines)


def parse_auction_compare_query(q: str) -> Optional[List[Dict]]:
    """Parse flexible 'compare auction ... vs ...' queries.
    Supports: months (name/number), quarters, years, with 2+ periods (years up to 3).
    Returns list of period dicts or None.
    """
    import re
    q = q.lower()
    # Try quarters first to preserve existing formatting path
    m_q = re.search(r'q(\d)\s+(\d{4}).*?vs.*?q(\d)\s+(\d{4})', q)
    if m_q:
        q1, y1, q2, y2 = map(int, m_q.groups())
        return [
            {'type': 'quarter', 'quarter': q1, 'year': y1},
            {'type': 'quarter', 'quarter': q2, 'year': y2},
        ]
    # Months: names or numeric
    months_map = {
        'jan':1,'january':1,
        'feb':2,'february':2,
        'mar':3,'march':3,
        'apr':4,'april':4,
        'may':5,
        'jun':6,'june':6,
        'jul':7,'july':7,
        'aug':8,'august':8,
        'sep':9,'sept':9,'september':9,
        'oct':10,'october':10,
        'nov':11,'november':11,
        'dec':12,'december':12,
    }
    m_m = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|\d{1,2})\s+(\d{4}).*?vs.*?(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|\d{1,2})\s+(\d{4})', q)
    if m_m:
        a1, y1, a2, y2 = m_m.groups()
        def _to_month(x):
            return months_map[x] if x in months_map else int(x)
        return [
            {'type': 'month', 'month': _to_month(a1), 'year': int(y1)},
            {'type': 'month', 'month': _to_month(a2), 'year': int(y2)},
        ]
    # Years: allow 2 or 3
    m_y = re.findall(r'\b(\d{4})\b', q)
    if m_y and 'vs' in q:
        years = [int(y) for y in m_y][:3]
        if len(years) >= 2:
            return [{'type': 'year', 'year': y} for y in years]
    return None


def format_auction_comparison(hist_data: Dict, forecast_data: Dict) -> str:
    """Format auction comparison between historical and forecast periods."""
    lines = []
    
    # Historical period
    hist_q = f"Q{hist_data['quarter']} {hist_data['year']}"
    lines.append(f"<b>{hist_q} Auction Demand (Historical):</b>")
    month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for m in hist_data['monthly']:
        month_name = month_names[m['month']]
        lines.append(f"• {month_name}: Rp {m['incoming']:,.2f}T | {m['bid_to_cover']:.2f}x bid-to-cover")
    lines.append(f"<b>Total:</b> Rp {hist_data['total_incoming']:,.2f}T | Avg BtC: {hist_data['avg_bid_to_cover']:.2f}x")
    
    lines.append("")
    
    # Forecast period
    forecast_q = f"Q{forecast_data['quarter']} {forecast_data['year']}"
    lines.append(f"<b>{forecast_q} Auction Demand (Forecast):</b>")
    for m in forecast_data['monthly']:
        month_name = month_names[m['month']]
        lines.append(f"• {month_name}: Rp {m['incoming']:,.2f}T | {m['bid_to_cover']:.2f}x bid-to-cover")
    lines.append(f"<b>Total:</b> Rp {forecast_data['total_incoming']:,.2f}T | Avg BtC: {forecast_data['avg_bid_to_cover']:.2f}x")
    
    lines.append("")
    lines.append("─" * 50)
    
    # YoY comparison
    incoming_change = ((forecast_data['total_incoming'] / hist_data['total_incoming']) - 1) * 100
    btc_change = ((forecast_data['avg_bid_to_cover'] / hist_data['avg_bid_to_cover']) - 1) * 100
    
    lines.append(f"<b>Year-over-Year Change:</b>")
    lines.append(f"• Incoming bids: {incoming_change:+.1f}% (Rp {hist_data['total_incoming']:,.0f}T → Rp {forecast_data['total_incoming']:,.0f}T)")
    lines.append(f"• Bid-to-cover: {btc_change:+.1f}% ({hist_data['avg_bid_to_cover']:.2f}x → {forecast_data['avg_bid_to_cover']:.2f}x)")
    
    lines.append("")
    lines.append("<blockquote>~ Kei</blockquote>")
    
    return "\n".join(lines)


def format_auction_historical_multi_year(start_year: int, end_year: int, dual_mode: bool = False) -> str:
    """Format historical auction data from auction_train.csv for multiple years (e.g., 2010-2024).
    Returns Economist-style table with incoming, awarded bids, and bid-to-cover ratio.
    
    Args:
        start_year: Starting year
        end_year: Ending year
        dual_mode: If True, use "Kei x Kin" signature (for /both command)
    """
    try:
        df = pd.read_csv('auction_train.csv')
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df['year'] = df['date'].dt.year
        
        # Filter for requested years
        mask = (df['year'] >= start_year) & (df['year'] <= end_year)
        df_filtered = df[mask].copy()
        
        if df_filtered.empty:
            return f"❌ No auction data available for {start_year}–{end_year}."
        
        # Reverse log10 transformation: incoming_bio_log and awarded_bio_log are LOG10 of billions
        df_filtered['incoming_bio'] = 10 ** df_filtered['incoming_bio_log']
        df_filtered['awarded_bio'] = 10 ** df_filtered['awarded_bio_log']
        
        # Group by year and sum
        yearly = df_filtered.groupby('year').agg({
            'incoming_bio': 'sum',
            'awarded_bio': 'sum'
        }).reset_index()
        
        # Calculate bid-to-cover ratio
        yearly['bid_to_cover'] = yearly['incoming_bio'] / yearly['awarded_bio']
        
        # Convert billions to trillions for display
        yearly['incoming_tri'] = yearly['incoming_bio'] / 1000.0
        yearly['awarded_tri'] = yearly['awarded_bio'] / 1000.0
        
        # Build Economist-style table (41-char width target)
        # Columns: Year | Incoming | Awarded | BtC
        # Width allocation: Year=6, Incoming=11, Awarded=11, BtC=8 (~36 chars + separators)
        lines = []
        lines.append("📊 <b>INDOGB Auction: Incoming/Awarded Bids</b>")
        lines.append(f"<b>Period:</b> {start_year}–{end_year}")
        lines.append("")
        lines.append("<pre>")
        
        header = f"{'Year':<6}|{'Incoming':<11}|{'Awarded':<11}|{'BtC':>6}"
        lines.append(header)
        lines.append("─" * 41)
        
        for _, row in yearly.iterrows():
            year_str = f"{int(row['year'])}"
            incoming_str = f"Rp {row['incoming_tri']:.1f}T"
            awarded_str = f"Rp {row['awarded_tri']:.1f}T"
            btc_str = f"{row['bid_to_cover']:.2f}x"
            
            line = f"{year_str:<6}|{incoming_str:<11}|{awarded_str:<11}|{btc_str:>6}"
            lines.append(line)
        
        lines.append("</pre>")
        lines.append("")
        
        # Summary stats
        total_incoming = yearly['incoming_tri'].sum()
        total_awarded = yearly['awarded_tri'].sum()
        avg_btc = yearly['bid_to_cover'].mean()
        
        lines.append(f"<b>Period totals:</b> Incoming Rp {total_incoming:.1f}T, Awarded Rp {total_awarded:.1f}T")
        lines.append(f"<b>Avg bid-to-cover:</b> {avg_btc:.2f}x")
        lines.append("")
        signature = "Kei x Kin" if dual_mode else "Kei"
        lines.append(f"<blockquote>~ {signature}</blockquote>")
        
        return "\n".join(lines)
        
    except Exception as e:
        logger.error(f"Error formatting historical auction data: {e}")
        return f"❌ Error loading auction data: {e}"


def parse_bond_table_query(q: str) -> Optional[Dict]:
    """Parse '/kei tab' bond table queries for yield/price data.
    Supported patterns:
    - '/kei tab yield 5 year in jan 2025'
    - '/kei tab price 5 and 10 year in q1 2025'
    - '/kei tab yield 5 year in 2025'
    - '/kei tab yield 5 and 10 year from oct 2024 to mar 2025'
    - '/kei tab price 5 and 10 year from q2 2024 to q1 2025'
    - '/kei tab yield and price 5 year in feb 2025'
    
    Returns dict: {'metrics': ['yield'|'price'|both], 'tenors': ['05_year','10_year'], 
                   'start_date': date, 'end_date': date} or None
    """
    q = q.lower()
    if 'tab' not in q:
        return None
    
    # Extract metrics: 'yield', 'price', or 'yield and price'
    metrics = []
    if 'yield and price' in q or 'price and yield' in q:
        metrics = ['yield', 'price']
    elif 'yield' in q:
        metrics = ['yield']
    elif 'price' in q:
        metrics = ['price']
    else:
        return None
    
    # Extract tenors using pattern: "X year" or "X and Y year"
    tenors = []
    # Try "X and Y year" pattern first
    and_pattern = re.search(r'(\d+)\s+and\s+(\d+)\s+years?', q)
    if and_pattern:
        t1 = f"{int(and_pattern.group(1)):02d}_year"
        t2 = f"{int(and_pattern.group(2)):02d}_year"
        tenors = [t1, t2]
    else:
        # Try single "X year" pattern (find all)
        tenor_matches = re.findall(r'(\d+)\s+years?', q)
        if tenor_matches:
            tenors = [f"{int(t):02d}_year" for t in tenor_matches]
    
    if not tenors:
        return None
    
    # Extract period: single or range
    # Helper to parse month name or quarter
    month_map = {
        'jan':1, 'january':1, 'feb':2, 'february':2, 'mar':3, 'march':3,
        'apr':4, 'april':4, 'may':5, 'jun':6, 'june':6, 'jul':7, 'july':7,
        'aug':8, 'august':8, 'sep':9, 'sept':9, 'september':9, 'oct':10,
        'october':10, 'nov':11, 'november':11, 'dec':12, 'december':12
    }
    
    def parse_period_spec(spec: str) -> Optional[tuple]:
        """Parse 'jan 2025', 'q1 2025', or '2025' into (start_date, end_date)."""
        spec = spec.strip().lower()
        
        # Quarter pattern: q1 2025
        q_match = re.match(r'q([1-4])\s+(\d{4})', spec)
        if q_match:
            q_num = int(q_match.group(1))
            year = int(q_match.group(2))
            month_start = 1 + (q_num - 1) * 3
            start = date(year, month_start, 1)
            end = start + relativedelta(months=3) - timedelta(days=1)
            return start, end
        
        # Month-year pattern: jan 2025
        m_match = re.match(r'(\w+)\s+(\d{4})', spec)
        if m_match:
            month_str = m_match.group(1)
            year = int(m_match.group(2))
            if month_str in month_map:
                month = month_map[month_str]
                start = date(year, month, 1)
                end = start + relativedelta(months=1) - timedelta(days=1)
                return start, end
        
        # Year only pattern: 2025
        if re.match(r'^\d{4}$', spec):
            year = int(spec)
            start = date(year, 1, 1)
            end = date(year, 12, 31)
            return start, end
        
        return None
    
    # "from X to Y" pattern
    from_match = re.search(r'from\s+(.+?)\s+to\s+(.+)$', q)
    if from_match:
        start_spec = from_match.group(1).strip()
        end_spec = from_match.group(2).strip()
        start_res = parse_period_spec(start_spec)
        end_res = parse_period_spec(end_spec)
        if start_res and end_res:
            return {
                'metrics': metrics,
                'tenors': tenors,
                'start_date': start_res[0],
                'end_date': end_res[1],
            }
    
    # "in X" pattern (single period)
    in_match = re.search(r'in\s+(.+)$', q)
    if in_match:
        period_spec = in_match.group(1).strip()
        period_res = parse_period_spec(period_spec)
        if period_res:
            return {
                'metrics': metrics,
                'tenors': tenors,
                'start_date': period_res[0],
                'end_date': period_res[1],
            }
    
    # Fallback: allow single period without explicit "in" (e.g., "/kei tab yield 5 year feb 2025")
    single_match = (
        re.search(r'(q[1-4]\s+\d{4})', q) or
        re.search(r'(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december)\s+\d{4}', q) or
        re.search(r'\b(\d{4})\b', q)
    )
    if single_match:
        period_spec = single_match.group(0).strip()
        period_res = parse_period_spec(period_spec)
        if period_res:
            return {
                'metrics': metrics,
                'tenors': tenors,
                'start_date': period_res[0],
                'end_date': period_res[1],
            }
    
    return None


def parse_bond_plot_query(q: str) -> Optional[Dict]:
    """Parse '/kin plot' bond plot queries.
    Same patterns as parse_bond_table_query but for plots.
    Returns dict with 'metrics', 'tenors', 'start_date', 'end_date' or None.
    """
    q = q.lower()
    if 'plot' not in q:
        return None
    
    # Remove the /kin and 'plot' prefix to avoid matching 'in' in '/kin'
    # Find where 'plot' starts and work from there
    plot_idx = q.find('plot')
    if plot_idx == -1:
        return None
    q_after_plot = q[plot_idx + 4:].strip()  # Everything after "plot"
    
    # Extract metrics: 'yield', 'price'
    metrics = []
    if 'yield' in q_after_plot:
        metrics = ['yield']
    elif 'price' in q_after_plot:
        metrics = ['price']
    else:
        return None
    
    metric = metrics[0]  # Plot one metric at a time
    
    # Extract tenors
    tenors = []
    and_pattern = re.search(r'(\d+)\s+and\s+(\d+)\s+years?', q_after_plot)
    if and_pattern:
        t1 = f"{int(and_pattern.group(1)):02d}_year"
        t2 = f"{int(and_pattern.group(2)):02d}_year"
        tenors = [t1, t2]
    else:
        tenor_matches = re.findall(r'(\d+)\s+years?', q_after_plot)
        if tenor_matches:
            tenors = [f"{int(t):02d}_year" for t in tenor_matches]
    
    if not tenors:
        return None
    
    # Helper function (same as in parse_bond_table_query)
    month_map = {
        'jan':1, 'january':1, 'feb':2, 'february':2, 'mar':3, 'march':3,
        'apr':4, 'april':4, 'may':5, 'jun':6, 'june':6, 'jul':7, 'july':7,
        'aug':8, 'august':8, 'sep':9, 'sept':9, 'september':9, 'oct':10,
        'october':10, 'nov':11, 'november':11, 'dec':12, 'december':12
    }
    
    def parse_period_spec(spec: str) -> Optional[tuple]:
        spec = spec.strip().lower()
        
        q_match = re.match(r'q([1-4])\s+(\d{4})', spec)
        if q_match:
            q_num = int(q_match.group(1))
            year = int(q_match.group(2))
            month_start = 1 + (q_num - 1) * 3
            start = date(year, month_start, 1)
            end = start + relativedelta(months=3) - timedelta(days=1)
            return start, end
        
        m_match = re.match(r'(\w+)\s+(\d{4})', spec)
        if m_match:
            month_str = m_match.group(1)
            year = int(m_match.group(2))
            if month_str in month_map:
                month = month_map[month_str]
                start = date(year, month, 1)
                end = start + relativedelta(months=1) - timedelta(days=1)
                return start, end
        
        if re.match(r'^\d{4}$', spec):
            year = int(spec)
            start = date(year, 1, 1)
            end = date(year, 12, 31)
            return start, end
        
        return None
    
    # "from X to Y" pattern
    from_match = re.search(r'from\s+(.+?)\s+to\s+(.+)$', q_after_plot)
    if from_match:
        start_spec = from_match.group(1).strip()
        end_spec = from_match.group(2).strip()
        start_res = parse_period_spec(start_spec)
        end_res = parse_period_spec(end_spec)
        if start_res and end_res:
            return {
                'metric': metric,
                'tenors': tenors,
                'start_date': start_res[0],
                'end_date': end_res[1],
            }
    
    # "in X" pattern (single period)
    in_match = re.search(r'in\s+(.+)$', q_after_plot)
    if in_match:
        period_spec = in_match.group(1).strip()
        period_res = parse_period_spec(period_spec)
        if period_res:
            return {
                'metric': metric,
                'tenors': tenors,
                'start_date': period_res[0],
                'end_date': period_res[1],
            }
    
    return None


def format_bond_metrics_table(db, start_date: date, end_date: date, metrics: List[str], tenors: List[str]) -> str:
    """Format bond yield/price data as economist-style table.
    
    Rows: dates (daily observations)
    Columns: one or more of [Yield, Price] for each tenor
    
    For single tenor + single metric: columns are dates and values
    For multi-tenor: each tenor gets its own metric columns (with summary stats)
    For multi-metric: each metric gets its own columns per tenor
    """
    # Query database for the period and tenors
    params = [start_date.isoformat(), end_date.isoformat()]
    placeholders = ','.join(['?'] * len(tenors))
    query = f"""
        SELECT obs_date, {', '.join(metrics)}, tenor
        FROM ts
        WHERE obs_date BETWEEN ? AND ? AND tenor IN ({placeholders})
        ORDER BY obs_date, tenor
    """
    params.extend(tenors)
    
    try:
        rows = db.con.execute(query, params).fetchall()
    except Exception as e:
        logger.error(f"Error querying bond data: {e}")
        return f"❌ Error querying bond data: {e}"
    
    if not rows:
        return "❌ No bond data found for the specified period and tenors."
    
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(rows, columns=['obs_date'] + metrics + ['tenor'])
    df['obs_date'] = pd.to_datetime(df['obs_date'])
    for m in metrics:
        df[m] = pd.to_numeric(df[m], errors='coerce')
    
    # Sort by date
    df = df.sort_values('obs_date').reset_index(drop=True)
    
    # Determine column layout
    if len(tenors) == 1 and len(metrics) == 1:
        # Single tenor, single metric: Date | Value
        tenor_display = tenors[0].replace('_', ' ')
        metric_cap = metrics[0].capitalize()
        header = f"{'Date':<12} | {metric_cap:>12}"
        border = '─' * 28
        
        rows_list = []
        for _, row in df.iterrows():
            date_str = row['obs_date'].strftime('%d %b %Y')
            val = row[metrics[0]]
            val_str = f"{val:.4f}" if val is not None else "N/A"
            rows_list.append(f"{date_str:<12} | {val_str:>12}")
        
        rows_text = "\n".join([f"│ {r:<{len(border)-3}}│" for r in rows_list])
        return f"""```
┌{border}┐
│ {header:<{len(border)-3}}│
├{border}┤
{rows_text}
└{border}┘
```"""
    
    elif len(tenors) > 1 and len(metrics) == 1:
        # Multiple tenors, single metric with summary stats
        metric_name = metrics[0]
        tenor_labels = [t.replace('_', ' ') for t in tenors]
        date_width = 12
        col_width = 10
        header = f"{'Date':<{date_width}} | " + " | ".join([f"{h:>{col_width}}" for h in tenor_labels])
        total_width = date_width + 3 + len(tenors) * (col_width + 3) - 3
        border = '─' * (total_width + 1)

        rows_list = []
        for _, date_group in df.groupby('obs_date'):
            date_str = date_group['obs_date'].iloc[0].strftime('%d %b %Y')
            values = []
            for tenor in tenors:
                tenor_data = date_group[date_group['tenor'] == tenor]
                if not tenor_data.empty:
                    val = tenor_data[metric_name].iloc[0]
                    val_str = f"{val:>{col_width}.2f}" if val is not None else f"{'N/A':>{col_width}}"
                else:
                    val_str = f"{'N/A':>{col_width}}"
                values.append(val_str)
            row_str = f"{date_str:<{date_width}} | " + " | ".join(values)
            rows_list.append(row_str)

        # Summary statistics per tenor
        summary_rows = []
        stats_labels = ['Count', 'Min', 'Max', 'Avg', 'Std']
        for label in stats_labels:
            vals = []
            for tenor in tenors:
                series = df[df['tenor'] == tenor][metric_name].dropna()
                if label == 'Count':
                    val_str = f"{len(series):>{col_width}d}" if len(series) > 0 else f"{'N/A':>{col_width}}"
                elif series.empty:
                    val_str = f"{'N/A':>{col_width}}"
                else:
                    if label == 'Min':
                        val = series.min()
                    elif label == 'Max':
                        val = series.max()
                    elif label == 'Avg':
                        val = series.mean()
                    else:  # Std
                        val = series.std()
                    val_str = f"{val:>{col_width}.2f}" if pd.notnull(val) else f"{'N/A':>{col_width}}"
                vals.append(val_str)
            summary_rows.append(f"{label:<{date_width}} | " + " | ".join(vals))

        data_text = "\n".join([f"│ {r:<{total_width}}│" for r in rows_list])
        summary_text = "\n".join([f"│ {r:<{total_width}}│" for r in summary_rows])
        return f"""```
┌{border}┐
│ {header:<{total_width}}│
├{border}┤
{data_text}
├{border}┤
{summary_text}
└{border}┘
```"""
    
    elif len(tenors) == 1 and len(metrics) > 1:
        # Single tenor, multiple metrics with summary stats
        date_width = 12
        col_width = 10
        metric_caps = [m.capitalize() for m in metrics]
        header = f"{'Date':<{date_width}} | " + " | ".join([f"{h:>{col_width}}" for h in metric_caps])
        total_width = date_width + 3 + len(metrics) * (col_width + 3) - 3
        border = '─' * (total_width + 1)

        rows_list = []
        for _, row in df.iterrows():
            date_str = row['obs_date'].strftime('%d %b %Y')
            vals = []
            for metric in metrics:
                val = row[metric]
                if pd.notnull(val):
                    vals.append(f"{val:>{col_width}.2f}")
                else:
                    vals.append(f"{'-':>{col_width}}")
            row_str = f"{date_str:<{date_width}} | " + " | ".join(vals)
            rows_list.append(row_str)

        # Summary statistics across the period per metric
        summary_rows = []
        stats_labels = ['Count', 'Min', 'Max', 'Avg', 'Std']
        for label in stats_labels:
            vals = []
            for metric in metrics:
                series = df[metric].dropna()
                if label == 'Count':
                    val_str = f"{len(series):>{col_width}d}" if len(series) > 0 else f"{'-':>{col_width}}"
                elif series.empty:
                    val_str = f"{'-':>{col_width}}"
                else:
                    if label == 'Min':
                        val = series.min()
                    elif label == 'Max':
                        val = series.max()
                    elif label == 'Avg':
                        val = series.mean()
                    else:  # Std
                        val = series.std()
                    val_str = f"{val:>{col_width}.2f}" if pd.notnull(val) else f"{'-':>{col_width}}"
                vals.append(val_str)
            summary_rows.append(f"{label:<{date_width}} | " + " | ".join(vals))

        data_text = "\n".join([f"│ {r:<{total_width}}│" for r in rows_list])
        summary_text = "\n".join([f"│ {r:<{total_width}}│" for r in summary_rows])
        return f"""```
┌{border}┐
│ {header:<{total_width}}│
├{border}┤
{data_text}
├{border}┤
{summary_text}
└{border}┘
```"""
    
    else:
        # Multiple tenors and multiple metrics: Tenor_Metric columns
        tenor_labels = [t.replace('_', ' ') for t in tenors]
        metric_caps = [m.capitalize() for m in metrics]
        col_headers = []
        for tenor_label in tenor_labels:
            for metric_cap in metric_caps:
                col_headers.append(f"{tenor_label} {metric_cap}")
        
        header_parts = ['Date'] + col_headers
        col_width = 12
        header = " | ".join([f"{h:<{col_width}}" if i == 0 else f"{h:>{col_width}}" for i, h in enumerate(header_parts)])
        total_width = col_width + 3 + len(col_headers) * (col_width + 3) - 3
        border = '─' * (total_width + 1)
        
        rows_list = []
        for _, date_group in df.groupby('obs_date'):
            date_str = date_group['obs_date'].iloc[0].strftime('%d %b %Y')
            values = [date_str]
            for tenor in tenors:
                for metric in metrics:
                    tenor_data = date_group[date_group['tenor'] == tenor]
                    if not tenor_data.empty:
                        val = tenor_data[metric].iloc[0]
                        val_str = f"{val:.4f}" if val is not None else "N/A"
                    else:
                        val_str = "N/A"
                    values.append(val_str)
            row_str = " | ".join([f"{values[0]:<{col_width}}"] + [f"{v:>{col_width}}" for v in values[1:]])
            rows_list.append(row_str)
        
        rows_text = "\n".join([f"│ {r:<{total_width}}│" for r in rows_list])
        return f"""```
┌{border}┐
│ {header:<{total_width}}│
├{border}┤
{rows_text}
└{border}┘
```"""


def format_rows_for_telegram(rows, include_date=False, metric='yield', metrics=None, economist_style=False, summary_stats=None):
    """Format data rows for Telegram message (monospace style).
    - Supports single or multiple metrics (e.g., ['yield','price']).
    - economist_style: Apply Economist table formatting with borders and professional styling.
    """
    if not rows:
        return "No data found."
    metrics_list = metrics or [metric]
    import re
    def format_date_display(date_str):
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime('%d %b %Y')
        except:
            return date_str
    def normalize_tenor_display(tenor_str):
        """Normalize tenor labels: '5_year' -> '05Y', '10_year' -> '10Y' (with zero-padding for single digits)"""
        label = str(tenor_str or '').replace('_', ' ').strip()
        # Normalize patterns like '5year', '5 year', '5Yyear' to '5Y'
        label = re.sub(r'(?i)(\b\d+)\s*y(?:ear)?\b', r'\1Y', label)
        label = label.replace('Yyear', 'Y').replace('yyear', 'Y')
        # Pad single-digit years with leading zero (1Y -> 01Y, 9Y -> 09Y)
        label = re.sub(r'(?i)^(\d)Y$', r'0\1Y', label)
        return label
    tenors = sorted(set(row['tenor'] for row in rows))
    dates = sorted(set(row['date'] for row in rows if 'date' in row))
    # Single tenor, multi-date, multiple metrics → Date | m1 | m2 ...
    if include_date and len(tenors) == 1 and len(dates) > 1 and len(metrics_list) > 1:
        header = f"{'Date':<12} | " + " | ".join([f"{m.capitalize():<8}" for m in metrics_list])
        sep = '-' * (12 + 3 + len(metrics_list) * 11)
        table_rows = []
        for d in dates:
            row_vals = []
            for m in metrics_list:
                val = next((r.get(m) for r in rows if r['tenor'] == tenors[0] and r['date'] == d), None)
                row_vals.append(f"{val:.2f}" if val is not None else "-")
            table_rows.append(f"{format_date_display(d):<12} | " + " | ".join([f"{v:<8}" for v in row_vals]))
        if economist_style:
            # Width: Date (12) + " | " (3) + each metric (8) + separators between metrics (3 * (n-1))
            width = 12 + 3 + len(metrics_list) * 8 + (len(metrics_list) - 1) * 3
            border = '─' * width
            rows_with_borders = "\n".join([f"│ {row:<{width}}│" for row in table_rows])
            return f"```\n┌{border}┐\n│ {header:<{width}}│\n├{border}┤\n{rows_with_borders}\n└{border}┘\n```"
        return f"```\n{header}\n{sep}\n" + "\n".join(table_rows) + "\n```"
    # Multi-tenor, multi-date, multi-metric → Date | T1_M1 | T1_M2 | T2_M1 | T2_M2 ...
    if include_date and len(tenors) > 1 and len(dates) > 1 and len(metrics_list) > 1:
        col_headers = []
        for t in tenors:
            for m in metrics_list:
                col_headers.append(f"{normalize_tenor_display(t)}_{m.capitalize()[:1]}")
        header = f"{'Date':<12} | " + " | ".join([f"{h:<8}" for h in col_headers])
        col_width = 12 + 3 + len(col_headers) * 11
        sep = '-' * col_width
        table_rows = []
        for d in dates:
            row_vals = []
            for t in tenors:
                for m in metrics_list:
                    val = next((r.get(m) for r in rows if r['tenor'] == t and r['date'] == d), None)
                    row_vals.append(f"{val:.2f}" if val is not None else "-")
            table_rows.append(f"{format_date_display(d):<12} | " + " | ".join([f"{v:<8}" for v in row_vals]))
        if economist_style:
            border = '─' * col_width
            rows_with_borders = "\n".join([f"│ {row:<{col_width}}│" for row in table_rows])
            return f"```\n┌{border}┐\n│ {header:<{col_width}}│\n├{border}┤\n{rows_with_borders}\n└{border}┘\n```"
        return f"```\n{header}\n{sep}\n" + "\n".join(table_rows) + "\n```"
    # Multi-tenor, multi-date (single metric)
    if include_date and len(tenors) > 1 and len(dates) > 1:
        header = f"{'Date':<12} | " + " | ".join([f"{normalize_tenor_display(t):>8}" for t in tenors])
        width = 12 + len(tenors) * 11
        table_rows = []
        for d in dates:
            row_vals = []
            for t in tenors:
                val = next((r.get(metric) for r in rows if r['tenor'] == t and r['date'] == d), None)
                row_vals.append(f"{val:.2f}" if val is not None else "-")
            table_rows.append(f"{format_date_display(d):<12} | " + " | ".join([f"{v:>8}" for v in row_vals]))
        if economist_style:
            border = '─' * (width + 1)  # +1 to account for leading space in row format
            rows_with_borders = "\n".join([f"│ {row:<{width}}│" for row in table_rows])
            
            # Add summary rows if available
            if summary_stats and metric in summary_stats:
                summary_rows = []
                for stat_name in ['count', 'min', 'max', 'avg', 'std']:
                    stat_vals = []
                    for t in tenors:
                        if t in summary_stats[metric]:
                            val = summary_stats[metric][t].get(stat_name, '-')
                            if isinstance(val, float):
                                # Format float values with consistent 2 decimal places
                                if stat_name == 'count':
                                    formatted_val = f"{int(val)}"
                                elif stat_name == 'std':
                                    # Std values typically smaller, use tighter formatting
                                    formatted_val = f"{val:.2f}"
                                else:
                                    formatted_val = f"{val:.2f}"
                            else:
                                formatted_val = str(val)
                            stat_vals.append(formatted_val)
                        else:
                            stat_vals.append('-')
                    # Right-align all values in 8-char columns for perfect '|' alignment across rows
                    summary_rows.append(f"{stat_name.capitalize():<12} | " + " | ".join([f"{v:>8}" for v in stat_vals]))
                summary_with_borders = "\n".join([f"│ {row:<{width}}│" for row in summary_rows])
                return f"```\n┌{border}┐\n│ {header:<{width}}│\n├{border}┤\n{rows_with_borders}\n├{border}┤\n{summary_with_borders}\n└{border}┘\n```"
            else:
                return f"```\n┌{border}┐\n│ {header:<{width}}│\n├{border}┤\n{rows_with_borders}\n└{border}┘\n```"
        return f"```\n{header}\n{sep}\n" + "\n".join(table_rows) + "\n```"
    # Single tenor, multi-date (single metric)
    elif include_date and len(tenors) == 1 and len(dates) > 1:
        t = tenors[0]
        header = f"{'Date':<12} | {normalize_tenor_display(t):>8}"
        width = 23
        table_rows = []
        for d in dates:
            val = next((r.get(metric) for r in rows if r['tenor'] == t and r['date'] == d), None)
            table_rows.append(f"{format_date_display(d):<12} | {val:>8.2f}" if val is not None else f"{format_date_display(d):<12} | {'-':>8}")
        if economist_style:
            border = '─' * width
            rows_with_borders = "\n".join([f"│{row:<{width}}│" for row in table_rows])
            # If summary statistics are provided, append a summary section at the bottom
            if summary_stats and metric in summary_stats and t in summary_stats[metric]:
                stats = summary_stats[metric][t]
                def _fmt_stat(name):
                    v = stats.get(name, '-')
                    if isinstance(v, float):
                        return f"{v:.2f}"
                    return f"{int(v)}" if isinstance(v, int) else str(v)
                summary_rows = []
                for stat_name in ['count', 'min', 'max', 'avg', 'std']:
                    summary_rows.append(f"{stat_name.capitalize():<12} | {_fmt_stat(stat_name):>8}")
                summary_with_borders = "\n".join([f"│{row:<{width}}│" for row in summary_rows])
                return f"```\n┌{border}┐\n│{header:<{width}}│\n├{border}┤\n{rows_with_borders}\n├{border}┤\n{summary_with_borders}\n└{border}┘\n```"
            return f"```\n┌{border}┐\n│{header:<{width}}│\n├{border}┤\n{rows_with_borders}\n└{border}┘\n```"
        return f"```\n{header}\n{sep}\n" + "\n".join(table_rows) + "\n```"
    # Multi-tenor, single date
    elif not include_date and len(tenors) > 1:
        header = f"{'Tenor':<8} | {metric.capitalize():<8}"
        sep = '-' * 20
        table_rows = []
        for t in tenors:
            val = next((r.get(metric) for r in rows if r['tenor'] == t), None)
            table_rows.append(f"{normalize_tenor_display(t):<8} | {val:.2f}" if val is not None else f"{normalize_tenor_display(t):<8} | -")
        if economist_style:
            border = '─' * 20
            rows_with_borders = "\n".join([f"│{row:<20}│" for row in table_rows])
            return f"```\n┌{border}┐\n│{header:<20}│\n├{border}┤\n{rows_with_borders}\n└{border}┘\n```"
        return f"```\n{header}\n{sep}\n" + "\n".join(table_rows) + "\n```"

    # Single tenor, single date (no date column) → Tenor | Metric (even for one row)
    elif not include_date and len(tenors) == 1:
        header = f"{'Tenor':<8} | {metric.capitalize():<8}"
        t = tenors[0]
        val = next((r.get(metric) for r in rows if r['tenor'] == t), None)
        row = f"{normalize_tenor_display(t):<8} | {val:.2f}" if val is not None else f"{normalize_tenor_display(t):<8} | -"
        if economist_style:
            border = '─' * 20
            return f"```\n┌{border}┐\n│{header:<20}│\n├{border}┤\n│{row:<20}│\n└{border}┘\n```"
        else:
            sep = '-' * 20
            return f"```\n{header}\n{sep}\n{row}\n```"
    # Fallback: bullet style
    lines = []
    for row in rows:
        if include_date:
            formatted_date = format_date_display(row['date'])
            lines.append(
                f"🔹 {row['series']} | {normalize_tenor_display(row['tenor'])} | {formatted_date}\n"
                f"   Price: {row['price']:.2f} | Yield: {row.get('yield', 0):.2f}"
            )
        else:
            lines.append(
                f"🔹 {row['series']} | {normalize_tenor_display(row['tenor'])}\n"
                f"   Price: {row['price']:.2f} | Yield: {row.get('yield', 0):.2f}"
            )
    return "\n\n".join(lines)


def format_range_summary_text(rows, start_date=None, end_date=None, metric='yield', signature_persona: str = 'Kei'):
    """Generate plain-text quantitative summary for range queries.
    - Per-tenor stats: avg/min/max/std, n
    - Curve spread when exactly two tenors and metric is yield
    """
    if not rows:
        return None
    if metric not in ('yield', 'price'):
        return None
    import statistics
    
    # Helper to convert tenor display (05_year -> 5Y, 10_year -> 10Y)
    def format_tenor_display(tenor_str):
        tenor_str = str(tenor_str).lower().strip()
        if '_year' in tenor_str:
            num = tenor_str.replace('_year', '').lstrip('0')
            return f"{num}Y"
        return tenor_str
    
    tenors = sorted(set(str(r.get('tenor') or 'all') for r in rows))
    tenor_display = [format_tenor_display(t) for t in tenors]

    # Period label
    period_label = None
    try:
        if start_date and end_date:
            if start_date.year == end_date.year and start_date.month == end_date.month:
                period_label = start_date.strftime('%b-%Y')
            else:
                period_label = f"{start_date} → {end_date}"
    except Exception:
        period_label = None
    header_period = f"; {period_label}" if period_label else ""

    header = f"📊 INDOGB: {', '.join(tenor_display)} {metric.capitalize()}s{header_period}; Range, Average, Volatility"
    lines = [header, ""]

    # Per-tenor stats
    per_tenor = {}
    for row in rows:
        tenor = row.get('tenor') or 'all'
        val = row.get(metric)
        if val is None:
            continue
        per_tenor.setdefault(tenor, []).append(val)

    # Harvard-style narrative summary (<=152 chars, descriptive only)
    unit = "%" if metric == 'yield' else ""
    spread_note = ""
    tenor_stats = []
    for tenor, vals in sorted(per_tenor.items()):
        if not vals:
            continue

        tenor_label = format_tenor_display(tenor)
        avg_v = statistics.mean(vals)
        min_v = min(vals)
        max_v = max(vals)
        std_v = statistics.stdev(vals) if len(vals) > 1 else 0
        obs_count = len(vals)
        spread = max_v - min_v

        # Qualitative notes
        vol_note = "a tight range" if std_v < 0.10 else "elevated swings" if std_v > 0.30 else "moderate variation"
        spread_note = "with a wide band" if spread > 0.50 else "within a contained band"

        tenor_stats.append({
            "label": tenor_label,
            "obs": obs_count,
            "min": min_v,
            "max": max_v,
            "avg": avg_v,
            "std": std_v,
            "vol_note": vol_note,
            "spread_note": spread_note,
        })

    # Compute spread once we have tenor stats if two tenors
    spread_info = None

    # Curve spread for two tenors (yield only)
    if metric == 'yield' and len(per_tenor) == 2:
        # Pair by date when possible
        by_date = {}
        for row in rows:
            d = row.get('date')
            t = row.get('tenor')
            y = row.get('yield')
            if d is None or y is None:
                continue
            by_date.setdefault(d, {})[t] = y
        spreads = []
        ten_pair = sorted(per_tenor.keys())
        ten_pair_display = [format_tenor_display(t) for t in ten_pair]
        for d, vals in by_date.items():
            if len(vals) == 2:
                diff = vals[ten_pair[1]] - vals[ten_pair[0]]
                spreads.append(diff)
        if spreads:
            avg_s = statistics.mean(spreads)
            min_s = min(spreads)
            max_s = max(spreads)
            spread_info = f" Spread {ten_pair_display[1]}-{ten_pair_display[0]} {min_s:.2f}-{max_s:.2f}pp avg {avg_s:.2f}pp."

    # Build compact narrative
    period_text = period_label or "Selected period"
    tenor_fragments = []
    for stat in tenor_stats:
        frag = (
            f"{stat['label']} {stat['min']:.2f}-{stat['max']:.2f}{unit} "
            f"avg {stat['avg']:.2f}{unit} sd{stat['std']:.2f}{unit} ({stat['obs']} obs)"
        )
        tenor_fragments.append(frag)

    narrative = f"{period_text}: " + "; ".join(tenor_fragments)
    if spread_info:
        narrative += "." + spread_info

    # Enforce 152-char ceiling
    if len(narrative) > 152:
        narrative = narrative[:149] + "..."

    lines = [narrative]
    lines.append("")
    lines.append(f"<blockquote>~ {signature_persona}</blockquote>")
    return "\n".join(lines)

def format_models_economist_table(models: dict) -> str:
    """Format per-model forecasts into an Economist-style monospace table, including average."""
    order = [
        "arima", "ets", "random_walk", "monte_carlo", "ma5", "var", "prophet", "average"
    ]
    # Model name display mapping
    model_display = {
        "arima": "ARIMA",
        "ets": "ETS",
        "random_walk": "Random Walk",
        "monte_carlo": "Monte Carlo",
        "ma5": "Mov. Avg. 5d",
        "var": "VAR",
        "prophet": "Prophet",
        "average": "Average"
    }
    # Model column: 13 chars, separator: 3 chars, Forecast column: 13 chars
    header = f"{'Model':<13} | {'Forecast':<13}"
    total_width = 13 + 3 + 13  # 29 chars
    border = '─' * (total_width + 1)  # +1 to account for leading space in row format
    
    table_rows = []
    for m in order:
        val = models.get(m)
        if val is None:
            continue
        # Add divider before Average
        if m == "average" and table_rows:
            table_rows.append("DIVIDER")  # Placeholder for divider
        display_name = model_display.get(m, m.upper())
        if isinstance(val, float):
            table_rows.append(f"{display_name:<13} | {val:<13.4f}")
        else:
            table_rows.append(f"{display_name:<13} | {str(val):<13}")
    
    if not table_rows:
        table_rows.append("(no model outputs)")
    
    # Add right border for complete box format
    # Special handling for divider row
    formatted_rows = []
    for row in table_rows:
        if row == "DIVIDER":
            formatted_rows.append(f"├{border}┤")
        else:
            formatted_rows.append(f"│ {row:<{total_width}}│")
    rows_with_borders = "\n".join(formatted_rows)
    return f"┌{border}┐\n│ {header:<{total_width}}│\n├{border}┤\n{rows_with_borders}\n└{border}┘"


def summarize_intent_result(intent, rows_list: List[dict]) -> str:
    """Summarize computed query results for display in chat."""
    parts: List[str] = []

    # If many rows, summarize by tenor with basic stats and sample rows
    if len(rows_list) > 5:
        metric_name = getattr(intent, "metric", "value") or "value"
        grouped: Dict[str, List[dict]] = {}
        for r in rows_list:
            grouped.setdefault(r.get("tenor", "all"), []).append(r)

        for tenor_label, group_rows in grouped.items():
            metric_values = [r.get(metric_name) for r in group_rows if r.get(metric_name) is not None]
            if metric_values:
                min_val = min(metric_values)
                max_val = max(metric_values)
                avg_val = statistics.mean(metric_values)
                std_val = statistics.stdev(metric_values) if len(metric_values) > 1 else 0
                stat_line = (
                    f"{tenor_label.title()}: min {min_val:.2f}, max {max_val:.2f}, "
                    f"avg {avg_val:.2f}, std {std_val:.2f} ({len(group_rows)} obs)"
                )
                parts.append(stat_line)
            else:
                parts.append(
                    f"{tenor_label} ({len(group_rows)} records) — no numeric {metric_name} values found"
                )

            parts.append(f"  Data rows (first 5 of {len(group_rows)}):")
            for r in group_rows[:5]:
                parts.append(
                    f"    {r['series']} | {tenor_label} | {r.get('date','')} | "
                    f"Price {r.get('price','N/A')} | Yield {r.get('yield','N/A')}"
                )
    else:
        for r in rows_list[:5]:
            tenor_label = r.get("tenor", "").replace("_", " ")
            parts.append(
                f"Series {r['series']} | Tenor {tenor_label} | "
                f"Price {r.get('price','N/A')} | Yield {r.get('yield','N/A')}"
                + (f" | Date {r.get('date')}" if 'date' in r else "")
            )

    header = f"Computed rows ({len(rows_list)} total):"
    return header + "\n" + "\n".join(parts)


async def try_compute_bond_summary(question: str) -> Optional[str]:
    """Best-effort: parse question and compute a summary for LLM context.
    Returns None for plot queries to let plot handlers take over."""
    try:
        q_lower = question.lower()
        
        # Skip processing for plot queries - let plot handlers deal with them
        if 'plot' in q_lower:
            return None
        
        # Special handling: "forecast ... next N observations/days/points" with tenor-only support
        next_match = re.search(r"next\s+(\d+)\s+(observations?|obs|points|days)", q_lower)
        if next_match and ("forecast" in q_lower or "predict" in q_lower or "estimate" in q_lower):
            days = int(next_match.group(1))
            tenor = priceyield_mod.parse_tenor(question)
            series = priceyield_mod.parse_series(question)
            if tenor:
                db = get_db()
                metric = priceyield_mod.parse_metric(question)
                res = priceyield_mod.forecast_metric_next_days(
                    db,
                    tenor,
                    metric=metric,
                    days=days,
                    last_obs_count=5,
                    series=series if series else None,
                )
                # Format last 5 observations as table
                last_obs_data = res.get("last_obs", [])
                if last_obs_data:
                    header = f"{'Date':<13} | {metric.capitalize():<13}"
                    width = 13 + 3 + 13  # 29 chars (same as forecast table)
                    border = '─' * (width + 1)  # +1 to account for leading space in row format
                    obs_rows = []
                    for d, v in last_obs_data:
                        obs_rows.append(f"{str(d):<13} | {v:<13.4f}")
                    obs_with_borders = "\n".join([f"│ {row:<{width}}│" for row in obs_rows])
                    obs_table = f"┌{border}┐\n│ {header:<{width}}│\n├{border}┤\n{obs_with_borders}\n└{border}┘"
                    lines = [f"Latest {len(last_obs_data)} observations:", f"```\n{obs_table}\n```", ""]
                else:
                    lines = [""]
                # Format forecasts per T+ horizon using Economist-style tables
                lines.append(f"Forecasts ({metric}):")
                for item in res.get("forecasts", []):
                    avg = item.get("average")
                    avg_str = f"{avg:.4f}" if isinstance(avg, float) else str(avg)
                    header = f"{item.get('label')} ({item.get('date')}): average={avg_str}"
                    models_dict = dict(item.get("models", {}))
                    models_dict["average"] = item.get("average")
                    table = format_models_economist_table(models_dict)
                    lines.append(header)
                    # Wrap table in code fences to avoid Markdown entity parsing issues
                    lines.append(f"```\n{table}\n```")
                return "\n".join(lines)
        intent = parse_intent(question)
        rows_list = []
        
        # Handle historical auction queries for multi-year ranges (e.g., "from 2010 to 2024")
        q_auction = q_lower
        if ('auction' in q_auction or 'incoming' in q_auction or 'awarded' in q_auction or 'bid' in q_auction):
            # Check for year range pattern
            yr_range = re.search(r"from\s+(19\d{2}|20\d{2})\s+to\s+(19\d{2}|20\d{2})", q_auction)
            if yr_range:
                y_start = int(yr_range.group(1))
                y_end = int(yr_range.group(2))
                if y_start <= y_end and y_end <= 2024:  # Historical data only (forecast is separate)
                    # Use the same data source as /kei tab: load_auction_period via AuctionDB
                    # This ensures consistency across all commands
                    try:
                        periods = [{'type': 'year', 'year': y} for y in range(y_start, y_end + 1)]
                        periods_data = []
                        for p in periods:
                            pdata = load_auction_period(p)
                            if pdata:
                                periods_data.append(pdata)
                        
                        if periods_data:
                            # Use format_auction_metrics_table which uses AuctionDB (correct data)
                            metrics_list = ['incoming', 'awarded']
                            return format_auction_metrics_table(periods_data, metrics_list)
                    except Exception as e:
                        logger.warning(f"Error loading auction periods in try_compute_bond_summary: {e}")
                    # Fallback to old method if AuctionDB fails
                    return format_auction_historical_multi_year(y_start, y_end)

            # Single-month historical auction query (e.g., "in Mar 2024" or "March 2024")
            months_map = {
                'jan':1,'january':1,
                'feb':2,'february':2,
                'mar':3,'march':3,
                'apr':4,'april':4,
                'may':5,
                'jun':6,'june':6,
                'jul':7,'july':7,
                'aug':8,'august':8,
                'sep':9,'sept':9,'september':9,
                'oct':10,'october':10,
                'nov':11,'november':11,
                'dec':12,'december':12,
            }
            m_mon_in = re.search(r"\bin\s+(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december|\d{1,2})\s+(19\d{2}|20\d{2})\b", q_auction)
            m_mon_any = None
            if not m_mon_in:
                # also support month-year mention without explicit 'in'
                m_mon_any = re.search(r"\b(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december|\d{1,2})\s+(19\d{2}|20\d{2})\b", q_auction)
            m_use = m_mon_in or m_mon_any
            if m_use:
                mo_txt, yr_txt = m_use.groups()
                try:
                    mo = months_map[mo_txt] if mo_txt in months_map else int(mo_txt)
                    yr = int(yr_txt)
                    if yr <= 2024:
                        try:
                            p = {'type': 'month', 'month': mo, 'year': yr}
                            pdata = load_auction_period(p)
                            if pdata:
                                metrics_list = ['incoming', 'awarded']
                                return format_auction_metrics_table([pdata], metrics_list)
                        except Exception as e:
                            logger.warning(f"Error loading single-month auction period in try_compute_bond_summary: {e}")
                        # Fallback to historical month path if AuctionDB fails
                        try:
                            pdata = get_historical_auction_month_data(yr, mo)
                            if pdata:
                                metrics_list = ['incoming', 'awarded']
                                return format_auction_metrics_table([pdata], metrics_list)
                        except Exception:
                            pass
                except Exception:
                    pass

            # Single-year historical auction query (e.g., "in 2024" or standalone year)
            single_year = None
            in_year = re.search(r"\bin\s+(19\d{2}|20\d{2})\b", q_auction)
            if in_year:
                single_year = int(in_year.group(1))
            else:
                # Fallback: if a lone year appears and no range/in keyword, pick it if within bounds
                year_only = re.search(r"\b(19\d{2}|20\d{2})\b", q_auction)
                if year_only:
                    single_year = int(year_only.group(1))

            if single_year and single_year <= 2024:
                try:
                    p = {'type': 'year', 'year': single_year}
                    pdata = load_auction_period(p)
                    if pdata:
                        metrics_list = ['incoming', 'awarded']
                        return format_auction_metrics_table([pdata], metrics_list)
                except Exception as e:
                    logger.warning(f"Error loading single-year auction period in try_compute_bond_summary: {e}")
                # Fallback to old method if AuctionDB fails
                return format_auction_historical_multi_year(single_year, single_year)
        
        # Handle auction forecasts
        if intent.type == 'AUCTION_FORECAST':
            auction_db = get_auction_db()
            rows = auction_db.query_forecast(intent)
            if not rows:
                cov_min, cov_max = auction_db.coverage()
                cov_text = "" if not cov_min or not cov_max else f" Coverage: {cov_min} to {cov_max}."
                return f"❌ No auction forecast data available for the requested period.{cov_text}"
            # Choose metric based on forecast_type
            ftype = getattr(intent, 'forecast_type', None) or 'awarded'
            metric_field = {
                'awarded': 'awarded_billions',
                'incoming': 'incoming_billions',
                'bidtocover': 'bid_to_cover',
            }.get(ftype, 'awarded_billions')

            # Aggregate within period (month/quarter/year)
            # Build per-month stats and overall totals
            def fmt_idr_trillion(x):
                try:
                    return f"Rp {x:.2f}T"
                except:
                    return str(x)

            # Filter by date range if provided
            s = getattr(intent, 'start_date', None)
            e = getattr(intent, 'end_date', None)
            use_rows = [r for r in rows if (not s or r['date'] >= s) and (not e or r['date'] <= e)]
            if not use_rows:
                use_rows = rows

            # Group by month
            by_month = {}
            for r in use_rows:
                mkey = (r['auction_year'], r['auction_month'])
                by_month.setdefault(mkey, []).append(r)

            # Compute monthly sums/averages
            monthly_vals = []
            for (y, m), rr in sorted(by_month.items()):
                vals = [r.get(metric_field) for r in rr if r.get(metric_field) is not None]
                if not vals:
                    continue
                monthly_sum = sum(vals)
                monthly_avg_btc = None
                if metric_field != 'bid_to_cover':
                    # also compute bid-to-cover monthly average for context
                    btc_vals = [r.get('bid_to_cover') for r in rr if r.get('bid_to_cover') is not None]
                    monthly_avg_btc = statistics.mean(btc_vals) if btc_vals else None
                monthly_vals.append({
                    'year': y,
                    'month': m,
                    'value': monthly_sum,
                    'btc': monthly_avg_btc,
                })

            # Overall period aggregate
            if metric_field == 'bid_to_cover':
                overall = statistics.mean([
                    r.get('bid_to_cover') for r in use_rows if r.get('bid_to_cover') is not None
                ]) if any(r.get('bid_to_cover') is not None for r in use_rows) else None
            else:
                overall = sum([
                    r.get(metric_field) for r in use_rows if r.get(metric_field) is not None
                ]) if any(r.get(metric_field) is not None for r in use_rows) else None

            # Build summary text for LLM context
            # Period label
            period_label = None
            try:
                if s and e:
                    if s.year == e.year:
                        # Quarter format if 3-month span starting at Jan/Apr/Jul/Oct
                        q_map = {1: 'Q1', 4: 'Q2', 7: 'Q3', 10: 'Q4'}
                        if s.month in q_map and (e - s).days >= 80:
                            period_label = f"{q_map[s.month]} {s.year}"
                        else:
                            period_label = f"{s.strftime('%b %Y')}–{e.strftime('%b %Y')}"
                    else:
                        period_label = f"{s} → {e}"
            except Exception:
                period_label = None

            lines = []
            metric_name = {
                'awarded_billions': 'awarded amount',
                'incoming_billions': 'incoming bids',
                'bid_to_cover': 'bid-to-cover',
            }[metric_field]

            # Header
            if metric_field == 'bid_to_cover':
                header_main = f"📊 INDOGB: {period_label or 'Auction Period'} {metric_name}; Average"
            else:
                header_main = f"📊 INDOGB: {period_label or 'Auction Period'} {metric_name}; {fmt_idr_trillion(overall) if isinstance(overall, (int, float)) else overall} Total"
            lines.append(header_main)
            lines.append("")

            # Monthly breakdown and simple MoM
            if monthly_vals:
                # Compose breakdown line
                mon_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
                breakdown_parts = []
                for mv in monthly_vals:
                    label = f"{mon_names[mv['month']-1]} {mv['year']}"
                    val_txt = fmt_idr_trillion(mv['value']) if metric_field != 'bid_to_cover' else f"{mv['value']:.2f}x"
                    breakdown_parts.append(f"{label} {val_txt}")
                lines.append("; ".join(breakdown_parts))

                # MoM change if >=2 months and not bid_to_cover metric
                if metric_field != 'bid_to_cover' and len(monthly_vals) >= 2:
                    for i in range(1, len(monthly_vals)):
                        prev = monthly_vals[i-1]['value']
                        cur = monthly_vals[i]['value']
                        if prev and cur:
                            mom = ((cur - prev) / prev) * 100.0
                            mon_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
                            mlabel = mon_names[monthly_vals[i]['month']-1]
                            lines.append(f"MoM {mlabel}: {mom:+.1f}%")

            # Bid-to-cover context (average)
            btc_vals_all = [r.get('bid_to_cover') for r in use_rows if r.get('bid_to_cover') is not None]
            if btc_vals_all:
                btc_avg = statistics.mean(btc_vals_all)
                lines.append(f"Bid-to-cover average: {btc_avg:.2f}x")

            # Macro context hint if available in rows (BI rate, inflation)
            bi_vals = [r.get('bi_rate') for r in use_rows if r.get('bi_rate') is not None]
            inf_vals = [r.get('inflation_rate') for r in use_rows if r.get('inflation_rate') is not None]
            if bi_vals and inf_vals:
                try:
                    bi_first, bi_last = bi_vals[0], bi_vals[-1]
                    inf_first, inf_last = inf_vals[0], inf_vals[-1]
                    lines.append(
                        f"Context: BI rate {bi_first:.2f}%→{bi_last:.2f}%; inflation {inf_first:.2f}%→{inf_last:.2f}%"
                    )
                except Exception:
                    pass

            lines.append("")
            lines.append("<blockquote>~ Kei</blockquote>")
            return "\n".join(lines)
        # Handle bond data queries
        db = get_db()
        if intent.type == 'POINT':
            d = intent.point_date
            params = [d.isoformat()]
            where = 'obs_date = ?'
            # Honor multi-tenor requests (e.g., "5 year and 10 year")
            tenors_to_use = intent.tenors if getattr(intent, 'tenors', None) else ([intent.tenor] if getattr(intent, 'tenor', None) else None)
            if tenors_to_use:
                placeholders = ','.join(['?'] * len(tenors_to_use))
                where += f' AND tenor IN ({placeholders})'
                params.extend(tenors_to_use)
            if intent.series:
                where += ' AND series = ?'
                params.append(intent.series)
            rows = db.con.execute(
                f'SELECT series, tenor, price, "yield" FROM ts WHERE {where} ORDER BY series',
                params
            ).fetchall()
            rows_list = [
                dict(
                    series=r[0],
                    tenor=r[1],
                    price=round(r[2], 2) if r[2] is not None else None,
                    **{'yield': round(r[3], 2) if r[3] is not None else None}
                )
                for r in rows
            ]
            if rows_list:
                return summarize_intent_result(intent, rows_list)
        elif intent.type in ('RANGE', 'AGG_RANGE'):
            if intent.agg:
                val, n = db.aggregate(
                    intent.start_date, intent.end_date,
                    intent.metric, intent.agg,
                    intent.series, intent.tenor
                )
                return (
                    f"Aggregate result: {intent.agg.upper()} {intent.metric} = {round(val, 2) if val is not None else 'N/A'} "
                    f"(computed from {n} data points in period {intent.start_date} to {intent.end_date})"
                )
            else:
                params = [intent.start_date.isoformat(), intent.end_date.isoformat()]
                where = 'obs_date BETWEEN ? AND ?'
                tenors_to_use = intent.tenors if intent.tenors else ([intent.tenor] if intent.tenor else None)
                if tenors_to_use:
                    tenor_placeholders = ', '.join('?' * len(tenors_to_use))
                    where += f' AND tenor IN ({tenor_placeholders})'
                    params.extend(tenors_to_use)
                if intent.series:
                    where += ' AND series = ?'; params.append(intent.series)
                rows = db.con.execute(
                    f'SELECT series, tenor, obs_date, price, "yield" FROM ts WHERE {where} ORDER BY obs_date ASC, series',
                    params
                ).fetchall()
                rows_list = [
                    dict(
                        series=r[0], tenor=r[1], date=r[2].isoformat(),
                        price=round(r[3], 2) if r[3] is not None else None,
                        **{'yield': round(r[4], 2) if r[4] is not None else None}
                    ) for r in rows
                ]
                if rows_list:
                    return summarize_intent_result(intent, rows_list)
        # Yield forecasting integration
        forecast_keywords = ['forecast', 'predict', 'estimate']
        # Allow tenor-only forecasts (ignore series): require tenor + target date
        if any(kw in question.lower() for kw in forecast_keywords) and intent.metric == 'yield' and intent.tenor and intent.point_date:
            # If user specified a model, use only that model
            if intent.forecast_model:
                method = intent.forecast_model
                s = priceyield_mod.get_yield_series(db, intent.series if intent.series else None, intent.tenor)
                if len(s) < 10:
                    return f"Not enough data to forecast {intent.tenor} yield."
                try:
                    forecast = priceyield_mod.yield_forecast(s, intent.point_date, method=method)
                    tenor_txt = intent.tenor.replace('_', ' ')
                    scope = intent.series if intent.series else 'all series (averaged)'
                    return f"Forecast ({method.upper()}): {tenor_txt} yield at {intent.point_date} ({scope}): {forecast}"
                except Exception as e:
                    return f"Forecasting error ({method}): {e}"
            # Otherwise, return all model forecasts as a table + HL-CU summary
            else:
                s = priceyield_mod.get_yield_series(db, intent.series if intent.series else None, intent.tenor)
                if len(s) < 10:
                    return f"Not enough data to forecast {intent.tenor} yield."
                try:
                    forecasts = priceyield_mod.yield_forecast(s, intent.point_date, method="all")
                    # Format as Economist-style table
                    table = format_models_economist_table(forecasts)
                    # Compose HL-CU summary
                    tenor_txt = intent.tenor.replace('_',' ')
                    scope = intent.series if intent.series else 'all series (averaged)'
                    note = ""
                    avg_val = forecasts.get('average')
                    avg_str = f"{avg_val:.4f}" if isinstance(avg_val, float) else str(avg_val)
                    summary = (
                        f"Forecasts for {tenor_txt} yield at {intent.point_date} ({scope}):\n"
                        # Wrap table in code fences for safe Markdown rendering
                        f"```\n{table}\n```\n"
                        f"Ensemble average: {avg_str}{note}"
                    )
                    return summary
                except Exception as e:
                    return f"Forecasting error (all models): {e}"
    except Exception:
        return None
    return None


async def ask_kei(question: str, dual_mode: bool = False) -> str:
    """Persona /kei — world-class data scientist & econometrician.
    
    Args:
        question: The user question
        dual_mode: If True, use "Kei & Kin | Data → Insight" signature (for /both command)
    """
    if not _openai_client:
        return "⚠️ Persona /kei unavailable: OPENAI_API_KEY not configured."

    data_summary = await try_compute_bond_summary(question)
    # Truncate dataset context to prevent excessive token usage
    if data_summary and len(data_summary) > 2000:
        data_summary = data_summary[:2000] + "…"
    is_data_query = data_summary is not None

    # Short signature to reduce token footprint (HTML blockquote)
    signature_text = "\n<blockquote>~ Kei x Kin</blockquote>" if dual_mode else "\n<blockquote>~ Kei</blockquote>"

    if is_data_query:
        system_prompt = (
            "You are Kei.\n"
            "Profile: CFA charterholder, PhD (MIT). World-class data scientist with deep expertise in mathematics, statistics, econometrics, and forecasting. Lead with numbers, uncertainty ranges, and concise math; avoid narrative. Briefly name the forecasting method and key drivers when citing auction demand forecasts.\n\n"
            "LANGUAGE: Default to English. If the user explicitly asks in Indonesian, respond entirely in Indonesian.\n\n"
            "STYLE RULE — HEADLINE-LED CORPORATE UPDATE (HL-CU).\n"
            "Exactly one title line (📊 TICKER: Key Metric / Event; max 14 words), then blank line, then exactly 3 paragraphs (max 2 sentences each, ≤152 words total). Plain text only; no markdown, no bullets.\n"
            "If the user requests a different format (e.g., bullets), honor it and override HL-CU.\n"
            "Body: Emphasize factual reporting; no valuation or advice. Use contrasts (MoM vs YoY, trend vs level). Forward-looking statements must be attributed and conditional.\n"
            "Data-use constraints: Treat the provided dataset as complete even if only sample rows are shown; do not ask for more data or claim insufficient observations. When a tenor is requested, aggregate across all series for that tenor and ignore series differences.\n"
            "CRITICAL — Avoid meta-commentary: Do NOT add disclaimers, caveats, or explanations about data gaps, missing observations, or limitations in the precomputed inputs. Simply provide your analysis using the data provided without drawing attention to what's missing.\n"
            "Sources: Include one bracketed source line only if explicitly provided; otherwise omit.\n"
            f"Signature: {signature_text}.\n"
            "Prohibitions: No follow-up questions. No speculation or flourish. Do not add data not provided.\n"
            "Objective: Publication-ready response that delivers the key market signal clearly.\n\n"
            "Data access:\n- Indonesian government bond prices and yields (2023-2025): FR95–FR104 (5Y/10Y). FR = Fixing Rate bonds issued by Indonesia's government (not French bonds).\n- Auction demand forecasts through 2026: incoming bids, awarded amounts, bid-to-cover (ensemble ML: XGBoost, Random Forest, time-series) using macro features (BI rate, inflation, IP, JKSE, FX).\n- Indonesian macro indicators (BI rate, inflation, etc.).\n\n"
            "Yield forecasting supported: ARIMA, ETS, Prophet, GRU. Users may specify the method; otherwise use ARIMA by default."
        )
    else:
        system_prompt = (
            "You are Kei, a world-class quant and data scientist.\n"
            "LANGUAGE: Default to English. If the user explicitly asks in Indonesian, respond entirely in Indonesian.\n"
            "Explain economic and financial concepts using established frameworks and first principles.\n"
            "If specific data is unavailable, acknowledge limits but provide a concise, plain-text explanation.\n"
            "Avoid leaving the response empty."
        )

    messages = [{"role": "system", "content": system_prompt}]

    if is_data_query:
        messages.append({"role": "system", "content": "Constraint: no live news access; information may be outdated."})
        messages.append({"role": "system", "content": f"Precomputed quantitative inputs:\n{data_summary}"})
    else:
        messages.append({"role": "system", "content": "You have no access to live data. Provide analysis based on established economic frameworks and available public knowledge."})

    messages.append({"role": "user", "content": question})

    max_retries = 3
    for attempt in range(max_retries):
        try:
            temperature = 0.3 if is_data_query else 0.7
            # Slightly higher completion allowance to reduce empty responses
            max_tokens = 260 if is_data_query else 360
            resp = await _openai_client.chat.completions.create(
                model="gpt-5.2",
                messages=messages,
                max_completion_tokens=max_tokens,
                temperature=temperature,
            )
            content = resp.choices[0].message.content.strip() if resp.choices else ""
            if content:
                if not is_data_query and not content.startswith("📰"):
                    content = f"📰 {content}"
                # Convert any Markdown code fences to HTML <pre> for HTML parse mode
                content = convert_markdown_code_fences_to_html(content)
                return html_quote_signature(content)
            if attempt < max_retries - 1:
                logger.warning(f"Kei attempt {attempt + 1}: empty response, retrying (query_type={'data' if is_data_query else 'general'})...")
            else:
                logger.error(f"Kei: empty response after {max_retries} attempts (query_type={'data' if is_data_query else 'general'}).")
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"OpenAI error on final attempt: {e}")
                return f"⚠️ OpenAI error: {e}"
            else:
                logger.warning(f"Kei attempt {attempt + 1} failed: {e}, retrying...")
                continue

    # Final minimal fallback attempt
    try:
        # Detect if this is a plot query
        is_plot_query = any(kw in question.lower() for kw in ['plot'])
        
        if is_data_query:
            if is_plot_query:
                # For plots, provide concise visual interpretation
                minimal_system = (
                    "You are Kei. The user has just viewed a plot. Provide a concise (2-3 sentences), "
                    "professional interpretation of what the visualization likely shows based on the query. "
                    "Focus on key patterns: ranges, trends, tenor spreads, volatility. Be direct and analytical."
                )
            else:
                minimal_system = (
                    "You are Kei. Produce a concise, plain-text quantitative summary using ONLY the provided dataset context.\n"
                    "If the context is insufficient, state 'No dataset signal' with one-sentence reason. Do not return an empty response."
                )
            minimal_messages = [
                {"role": "system", "content": minimal_system},
                {"role": "system", "content": f"Dataset context:\n{data_summary or 'None'}"},
                {"role": "user", "content": question},
            ]
        else:
            minimal_system = (
                "You are Kei. Answer the user's question directly in plain text.\n"
                "If you lack specific data, provide a concise conceptual explanation. Do not leave the response empty."
            )
            minimal_messages = [
                {"role": "system", "content": minimal_system},
                {"role": "user", "content": question},
            ]

        resp2 = await _openai_client.chat.completions.create(
            model="gpt-5.2",
            messages=minimal_messages,
            max_completion_tokens=260,
            temperature=0.4,
        )
        content2 = resp2.choices[0].message.content.strip() if resp2.choices else ""
        if content2:
            content2 = convert_markdown_code_fences_to_html(content2)
            return html_quote_signature(content2)
    except Exception as e:
        logger.warning(f"Kei minimal fallback failed: {e}")

    if is_data_query:
        # For plots, provide a generic concise interpretation
        if any(kw in question.lower() for kw in ['plot']):
            fallback = "The plot shows the time series movement across the requested period. Key observations: monitor tenor spreads and volatility clustering for macro signals."
            return html_quote_signature(convert_markdown_code_fences_to_html(fallback))
        fallback = "⚠️ Kei could not analyze the bond data. Try narrowing the period, tenor, or metric (e.g., '/kei yield 10 year Jan 2025')."
        return html_quote_signature(convert_markdown_code_fences_to_html(fallback))
    else:
        fallback = (
            "📰 Kei | General Knowledge\n\n"
            "I encountered a temporary issue processing your question. This can happen for complex or ambiguous queries.\n\n"
            "Try:\n"
            "• Rephrase your question more concisely\n"
            "• Ask about specific bond data: '/kei yield 5 year 2025'\n"
            "• Use /kin for broader economic and market context\n"
            "• Use /examples for query samples"
        )
        return html_quote_signature(convert_markdown_code_fences_to_html(fallback))


async def ask_kin(question: str, dual_mode: bool = False) -> str:
    """Persona /kin — world-class economist & synthesizer.
    
    Args:
        question: The user question
        dual_mode: If True, use "Kei & Kin | Data → Insight" signature (for /both command)
    """
    if not PERPLEXITY_API_KEY:
        return "⚠️ Persona /kin unavailable: PERPLEXITY_API_KEY not configured."

    import httpx

    data_summary = await try_compute_bond_summary(question)

    # Two modes: strict data-only vs. full research with web search
    if data_summary:
        # MODE 1: Bond data available - strict data-only mode
        system_prompt = (
            "You are Kin.\n"
            "Profile: CFA charterholder, PhD (Harvard). World-class economist and data-driven storyteller—synthesizes complex market dynamics, economic incentives, and financial data into clear, compelling narratives that drive decisions. Because you are a CFA/Harvard macro strategist, foreground policy context and market implications, reconcile conflicting signals, and state uncertainties plainly; no price targets or advice.\n\n"

            "LANGUAGE: Default to English. If the user explicitly asks in Indonesian or requests Indonesian response, respond entirely in Indonesian.\n\n"

            "STYLE RULE — HEADLINE-LED CORPORATE UPDATE (HL-CU)\n"
            "Default format: Exactly one title line (🌍 TICKER: Key Metric / Event +X%; max 14 words), then blank line, then exactly 3 paragraphs (max 2 sentences each, ≤214 words total).\n"
            "CRITICAL FORMATTING: Use ONLY plain text. NO markdown headers (###), no bold (**), no italic (*), no underscores (_). Bullet points (-) and numbered lists are fine. Write in concise, prose, simple paragraphs.\n"
            "IMPORTANT: If the user explicitly requests bullet points, a bulleted list, plain English, or any other specific format, ALWAYS honor that request and override the HL-CU format.\n"
            "Body (Kin): Emphasize factual reporting; no valuation, recommendation, or opinion. Use contrasts where relevant (MoM vs YoY, trend vs level). Forward-looking statements must be attributed to management and framed conditionally. Write numbers and emphasis in plain text without any markdown bold or italics.\n"
            "Data-use constraints: Treat the provided dataset as complete even if only sample rows are shown; do not ask for more data or claim insufficient observations. When a tenor is requested, aggregate across all series for that tenor and ignore series differences.\n"
            "Sources: If any sources are referenced, add one line at the end in brackets with names only (no links), format: [Sources: Source A; Source B]. If none, omit the line entirely.\n"
            f"Signature: ALWAYS end your response with a blank line followed by: {'<blockquote>~ Kei x Kin</blockquote>' if dual_mode else '<blockquote>~ Kin</blockquote>'}\n"
            "Prohibitions: No follow-up questions. No speculation or narrative flourish. Do not add or infer data not explicitly provided.\n"
            "Objective: Produce a clear, publication-ready response that delivers the key market signal.\n\n"

            "Bond context: FR95-FR104 are Indonesian government bond series (Fixing Rate bonds issued by Indonesia's government), NOT French government bonds. Dataset covers Indonesian government bonds only.\n\n"
            "Bond data is provided - use it as the ONLY factual basis: cite specific values, dates, tenors, or ranges from the data. Translate quantitative results into economic meaning. Do not redo analysis already supplied; interpret and contextualize it."
        )
    else:
        # MODE 2: No bond data - enable full web search capabilities
        system_prompt = (
            "You are Kin.\n"
            "Profile: CFA charterholder, PhD (Harvard). World-class economist and data-driven storyteller—synthesizes complex market dynamics, economic incentives, and financial data into clear, compelling narratives that drive decisions. Because you are a CFA/Harvard macro strategist, foreground policy context and market implications, reconcile conflicting signals, and state uncertainties plainly; no price targets or advice.\n\n"

            "LANGUAGE: Default to English. If the user explicitly asks in Indonesian or requests Indonesian response, respond entirely in Indonesian.\n\n"

            "STYLE RULE — HEADLINE-LED CORPORATE UPDATE (HL-CU)\n"
            "Default format: Exactly one title line (🌍 TICKER: Key Metric / Event +X%; max 14 words), then blank line, then exactly 3 paragraphs (max 2 sentences each, ≤214 words total).\n"
            "CRITICAL FORMATTING: Use ONLY plain text. NO markdown headers (###), no bold (**), no italic (*), no underscores (_). Bullet points (-) and numbered lists are fine. Write in concise, prose, simple paragraphs.\n"
            "IMPORTANT: If the user explicitly requests bullet points, a bulleted list, plain English, or any other specific format, ALWAYS honor that request and override the HL-CU format.\n"
            "Body (Kin): Emphasize factual reporting; no valuation, recommendation, or opinion. Use contrasts where relevant (MoM vs YoY, trend vs level). Forward-looking statements must be attributed to management and framed conditionally. Write numbers and emphasis in plain text without any markdown bold or italics.\n"
            "Sources: If any sources are referenced, add one line at the end in brackets with names only (no links), format: [Sources: Source A; Source B]. If none, omit the line entirely.\n"
            f"Signature: ALWAYS end your response with a blank line followed by: {'<blockquote>~ Kei x Kin</blockquote>' if dual_mode else '<blockquote>~ Kin</blockquote>'}\n"
            "Prohibitions: No follow-up questions. No speculation or narrative flourish. Do not add or infer data not explicitly provided.\n"
            "Objective: Produce a clear, publication-ready response that delivers the key market signal.\n\n"

            "No bond data provided - use web search for authoritative analysis; cite real URLs when available."
        )

    messages = [{"role": "system", "content": system_prompt}]

    if data_summary:
        messages.append({
            "role": "system",
            "content": f"Available market context:\n{data_summary}"
        })

    messages.append({"role": "user", "content": question})

    try:
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": PERPLEXITY_MODEL,
            "messages": messages,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=payload,
            )
            r.raise_for_status()
            data = r.json()

        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        ) or "(empty response)"
        
        # If this is a bond query, prepend an INDOGB dataset header with period/tenor context
        try:
            intent = parse_intent(question)
            is_bond_intent = intent.type in ("POINT", "RANGE", "AGG_RANGE") and intent.metric in ("yield", "price")
        except Exception:
            is_bond_intent = False

        header = ""
        if is_bond_intent:
            tenors_to_use = intent.tenors if getattr(intent, 'tenors', None) else ([intent.tenor] if getattr(intent, 'tenor', None) else None)
            tenor_display = ", ".join(t.replace('_', ' ') for t in tenors_to_use) if tenors_to_use else "all tenors"
            metric_display = intent.metric.capitalize()
            period_label = None
            try:
                if intent.type == "POINT" and intent.point_date:
                    period_label = str(intent.point_date)
                elif intent.start_date and intent.end_date:
                    if intent.start_date.year == intent.end_date.year and intent.start_date.month == intent.end_date.month:
                        period_label = intent.start_date.strftime('%b %Y')
                    else:
                        period_label = f"{intent.start_date} to {intent.end_date}"
            except Exception:
                period_label = None
            header = f"📊 INDOGB: {metric_display} | {tenor_display}" + (f" | {period_label}" if period_label else "") + "\n\n"

        # Convert Markdown code fences to HTML <pre> before wrapping signature
        content = convert_markdown_code_fences_to_html(content)
        if header:
            content = header + content
        return html_quote_signature(content)

    except httpx.HTTPStatusError as e:
        error_detail = ""
        try:
            error_detail = f"\nAPI response: {e.response.json()}"
        except:
            error_detail = f"\nResponse text: {e.response.text[:200]}"
        return f"⚠️ Perplexity API error: {e.response.status_code} {e.response.reason_phrase}{error_detail}"
    except Exception as e:
        return f"⚠️ Perplexity error: {e}"


async def ask_kei_then_kin(question: str) -> dict:
    """Chain both personas: Kei analyzes data quantitatively, Kin interprets & concludes.
    
    Option A: Kin receives original question (for data context) + Kei's analysis.
    This ensures Kin enters MODE 1 (data-only) when data is available, and directly
    references Kei's findings for a cohesive narrative.
    """
    kei_answer = await ask_kei(question, dual_mode=True)
    # Pass original question so Kin can compute data_summary, plus Kei's analysis
    kin_prompt = (
        f"Original question: {question}\n\n"
        f"Kei's quantitative analysis:\n{kei_answer}\n\n"
        f"Based on this analysis and the original question, provide your strategic interpretation and conclusion."
    )
    kin_answer = await ask_kin(kin_prompt, dual_mode=True)
    return {
        "kei": kei_answer,
        "kin": kin_answer,
    }


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user_id = update.message.from_user.id
    if not is_user_authorized(user_id):
        await update.message.reply_text(
            "⛔ Access denied. This bot is restricted to authorized users only."
        )
        logger.warning("Unauthorized access attempt from user_id=%s", user_id)
        return
    
    welcome_text = (
        "<b>PerisAI</b> — Bond & Auction Analysis\n"
        f"© Arif P. Sulistiono {datetime.now().year}\n\n"
        "<b>Commands</b>\n"
        "💹 /kei — Quantitative analysis (data, tables, forecasts)\n"
        "🌍 /kin — Macro context (insights, plots, policy)\n"
        "⚡ /both — Combined (quant → strategic view)\n"
        "📌 /check — Quick lookup\n"
        "📚 /examples — Full query reference\n\n"
        "<b>Quick Examples</b>\n"
        "• /kei tab yield 5 and 10 year from q3 2023 to q2 2024\n"
        "• /kei tab incoming bid from 2020 to 2024\n"
        "• /kin plot yield 5 year from oct 2024 to mar 2025\n"
        "• /both compare 5 and 10 year 2024 vs 2025\n\n"
        "<i>Indonesian government bonds · Historical & forecast data</i>"
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML)


async def examples_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /examples command."""
    user_id = update.message.from_user.id
    if not is_user_authorized(user_id):
        await update.message.reply_text(
            "⛔ Access denied. This bot is restricted to authorized users only."
        )
        logger.warning("Unauthorized access attempt from user_id=%s", user_id)
        return
    
    examples_text = (
        "<b>📚 Query Examples</b>\n\n"
        
        "<b>Bond Tables (Economist-style with summary stats)</b>\n"
        "• /kei tab yield 5 and 10 year from q3 2023 to q2 2024\n"
        "• /kei tab price 5 year from oct 2024 to mar 2025\n"
        "• /kei tab yield and price 5 year in feb 2025\n"
        "• /kei tab yield 5 and 10 year from 2023 to 2024\n\n"
        
        "<b>Auction Tables (Range expansion: 'from X to Y')</b>\n"
        "• /kei tab incoming bid from 2020 to 2024\n"
        "• /kei tab awarded bid from 2015 to 2024\n"
        "• /kei tab incoming and awarded bid from 2022 to 2024\n"
        "• /kei tab incoming bid from Q2 2025 to Q3 2026\n\n"
        
        "<b>Bond Plots (Multi-tenor curves)</b>\n"
        "• /kin plot yield 5 and 10 year from oct 2024 to mar 2025\n"
        "• /kin plot price 5 year from q3 2023 to q2 2024\n"
        "• /kin plot yield 5 and 10 year from 2023 to 2024\n\n"
        
        "<b>Economic Analysis</b>\n"
        "• /kin explain impact of BI rate cuts on bond yields\n"
        "• /kin what is fiscal policy\n"
        "• /kin monetary policy framework Indonesia\n\n"
        
        "<b>Combined Analysis</b>\n"
        "• /both compare yields 5 and 10 year 2024 vs 2025\n"
        "• /both auction demand trends 2023 to 2025\n\n"
        
        "<b>Quick Lookup</b>\n"
        "• /check 2025-12-12 10 year\n"
        "• /check price 5 year 6 Dec 2024\n\n"
        
        "<b>📊 Output Formats</b>\n"
        "Tables: Economist-style borders, right-aligned numbers, summary stats (Count/Min/Max/Avg/Std)\n"
        "Plots: Professional styling, multi-tenor overlays\n\n"
        
        "<b>💡 Tips</b>\n"
        "• Ranges auto-expand: 'from 2020 to 2024' → all 5 years\n"
        "• Tenors: 5, 10, 15, 20, 30 year supported\n"
        "• Periods: months (jan, feb), quarters (q1–q4), years (2023)\n"
        "• Data: bonds 2015–2025, auctions 2015–2026"
    )
    await update.message.reply_text(examples_text, parse_mode=ParseMode.HTML)


async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /check command for quick point-date lookups."""
    start_time = time.time()
    user_id = update.message.from_user.id
    username = update.message.from_user.username or f"user_{user_id}"

    if not is_user_authorized(user_id):
        await update.message.reply_text(
            "⛔ Access denied. This bot is restricted to authorized users only."
        )
        logger.warning("Unauthorized access attempt from user_id=%s", user_id)
        metrics.log_error("/check", "Unauthorized access", user_id)
        return

    question = " ".join(context.args).strip() if context.args else ""
    if not question:
        await update.message.reply_text(
            "Usage: /check <date> [tenor/metric]\n"
            "Examples:\n"
            "/check 2025-12-12 5 and 10 year\n"
            "/check price 10 year 6 Dec 2024",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    try:
        intent = parse_intent(question)
    except Exception as e:
        logger.error(f"Intent parsing failed in /check for '{question}': {type(e).__name__}: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Could not parse that date. Try formats like 2025-12-12 or '6 Dec 2024'.",
            parse_mode=ParseMode.MARKDOWN
        )
        response_time = time.time() - start_time
        metrics.log_query(user_id, username, question, "check", response_time, False, "parse_intent_failed", "check")
        return

    if intent.type != 'POINT' or not intent.point_date:
        await update.message.reply_text(
            "❌ /check expects a single date (e.g., /check 2025-12-12 5 and 10 year).",
            parse_mode=ParseMode.MARKDOWN
        )
        response_time = time.time() - start_time
        metrics.log_query(user_id, username, question, "check", response_time, False, "not_point", "check")
        return

    d = intent.point_date
    params = [d.isoformat()]
    where = 'obs_date = ?'
    tenors_to_use = intent.tenors if getattr(intent, 'tenors', None) else ([intent.tenor] if getattr(intent, 'tenor', None) else None)
    if tenors_to_use:
        placeholders = ','.join(['?'] * len(tenors_to_use))
        where += f' AND tenor IN ({placeholders})'
        params.extend(tenors_to_use)
    if intent.series:
        where += ' AND series = ?'
        params.append(intent.series)

    db = get_db()
    rows = db.con.execute(
        f'SELECT series, tenor, obs_date, price, "yield" FROM ts WHERE {where} ORDER BY tenor, series',
        params
    ).fetchall()

    rows_list = [
        dict(
            series=r[0],
            tenor=r[1],
            date=r[2].isoformat() if hasattr(r[2], 'isoformat') else str(r[2]),
            price=round(r[3], 2) if r[3] is not None else None,
            **{'yield': round(r[4], 2) if r[4] is not None else None}
        )
        for r in rows
    ]

    response_time = time.time() - start_time

    if not rows_list:
        tenor_label = ", ".join(t.replace('_', ' ') for t in tenors_to_use) if tenors_to_use else "all tenors"
        await update.message.reply_text(
            f"❌ No bonds found for {d} ({tenor_label}).",
            parse_mode=ParseMode.MARKDOWN
        )
        metrics.log_query(user_id, username, question, "check", response_time, False, "no_data", "check")
        return

    tenor_label = ", ".join(t.replace('_', ' ') for t in tenors_to_use) if tenors_to_use else "all tenors"
    metric_label = intent.metric if getattr(intent, 'metric', None) else 'yield'
    response_lines = [
        f"📌 Quick check - {metric_label} on {d}",
        f"Tenor: {tenor_label}; Records: {len(rows_list)}"
    ]

    if any(r.get('yield') is not None for r in rows_list):
        response_lines.append("Yield")
        response_lines.append(format_rows_for_telegram(rows_list, include_date=False, metric='yield', economist_style=True))
    if any(r.get('price') is not None for r in rows_list):
        response_lines.append("Price")
        response_lines.append(format_rows_for_telegram(rows_list, include_date=False, metric='price', economist_style=True))

    await update.message.reply_text("\n\n".join(response_lines), parse_mode=ParseMode.MARKDOWN)
    metrics.log_query(user_id, username, question, "check", response_time, True, persona="check")


async def kei_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/kei <question> — ask persona Kei (ChatGPT)."""
    start_time = time.time()
    user_id = update.message.from_user.id
    username = update.message.from_user.username or f"user_{user_id}"
    
    if not is_user_authorized(user_id):
        await update.message.reply_text(
            "⛔ Access denied. This bot is restricted to authorized users only."
        )
        logger.warning("Unauthorized access attempt from user_id=%s", user_id)
        metrics.log_error("/kei", "Unauthorized access", user_id)
        return

    question = " ".join(context.args).strip() if context.args else ""
    if not question:
        await update.message.reply_text("Usage: /kei <question>")
        return
    
    # Detect 'tab' bond metric queries (yield/price data across periods)
    lower_q = question.lower()
    bond_tab_req = parse_bond_table_query(lower_q)
    if bond_tab_req:
        try:
            await context.bot.send_chat_action(chat_id=update.message.chat_id, action="typing")
        except Exception:
            pass
        try:
            db = get_db()
            table_text = format_bond_metrics_table(db, bond_tab_req['start_date'], bond_tab_req['end_date'], 
                                                   bond_tab_req['metrics'], bond_tab_req['tenors'])
            # Prepend dataset/source note to the table for clarity
            tenor_display = ", ".join(t.replace('_', ' ') for t in bond_tab_req['tenors'])
            metrics_display = " & ".join([m.capitalize() for m in bond_tab_req['metrics']])
            header = f"📊 INDOGB: {metrics_display} | {tenor_display} | {bond_tab_req['start_date']} to {bond_tab_req['end_date']}\n\n"
            await update.message.reply_text(header + table_text, parse_mode=ParseMode.MARKDOWN)
            response_time = time.time() - start_time
            metrics.log_query(user_id, username, question, "bond_tab", response_time, True, "success", "kei")
        except Exception as e:
            logger.error(f"Error processing bond table query: {e}")
            await update.message.reply_text(f"❌ Error formatting bond table: {e}")
            response_time = time.time() - start_time
            metrics.log_query(user_id, username, question, "bond_tab", response_time, False, str(e), "kei")
        return
    
    # Detect 'tab' auction metric queries (incoming/awarded totals across periods)
    lower_q = question.lower()
    tab_req = parse_auction_table_query(lower_q)
    if tab_req:
        try:
            await context.bot.send_chat_action(chat_id=update.message.chat_id, action="typing")
        except Exception:
            pass
        periods = []
        skipped_periods = []
        month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        for p in tab_req['periods']:
            pdata = load_auction_period(p)
            if not pdata:
                # Skip missing periods and collect labels
                label = (
                    f"Q{p['quarter']} {p['year']}" if p['type'] == 'quarter' else (
                        f"{month_names[p.get('month')]} {p['year']}" if p['type'] == 'month' else f"{p['year']}"
                    )
                )
                skipped_periods.append(label)
                continue  # Skip instead of returning error
            periods.append(pdata)
        
        if not periods:
            await update.message.reply_text(
                f"❌ No auction data found for any of the requested periods.",
                parse_mode=ParseMode.HTML
            )
            return
        
        table_text = format_auction_metrics_table(periods, tab_req['metrics'])
        
        # Add note about skipped periods if any
        if skipped_periods:
            skipped_msg = f"\n\n⚠️ <i>Note: {len(skipped_periods)} period(s) skipped (no data): {', '.join(skipped_periods[:5])}</i>"
            if len(skipped_periods) > 5:
                skipped_msg += f" <i>(+{len(skipped_periods) - 5} more)</i>"
        else:
            skipped_msg = ""
        
        try:
            # Send table in Markdown to render code fence/borders
            await update.message.reply_text(table_text, parse_mode=ParseMode.MARKDOWN)
            if skipped_msg:
                await update.message.reply_text(skipped_msg, parse_mode=ParseMode.HTML)
            response_time = time.time() - start_time
            metrics.log_query(user_id, username, question, "auction_tab", response_time, True, "success", "kei")
        except Exception as e:
            logger.error(f"Error sending auction table: {e}")
            await update.message.reply_text(f"❌ Error formatting response: {e}")
            response_time = time.time() - start_time
            metrics.log_query(user_id, username, question, "auction_tab", response_time, False, str(e), "kei")
        return

    # Detect auction comparison queries (quarters, months, years)
    lower_q = question.lower()
    if "compare" in lower_q and "auction" in lower_q:
        periods = parse_auction_compare_query(lower_q)
        if periods and len(periods) >= 2:
            try:
                await context.bot.send_chat_action(chat_id=update.message.chat_id, action="typing")
            except Exception:
                pass

            # If exactly two quarters, preserve existing formatting (Historical vs Forecast)
            if len(periods) == 2 and periods[0]['type'] == 'quarter' and periods[1]['type'] == 'quarter':
                q1, year1 = periods[0]['quarter'], periods[0]['year']
                q2, year2 = periods[1]['quarter'], periods[1]['year']
                hist_data = get_historical_auction_data(year1, q1)
                if not hist_data:
                    await update.message.reply_text(
                        f"❌ No historical auction data found for Q{q1} {year1}.",
                        parse_mode=ParseMode.HTML
                    )
                    return
                forecast_data = load_auction_period({'type': 'quarter', 'quarter': q2, 'year': year2})
                if not forecast_data:
                    await update.message.reply_text(
                        f"❌ No auction data found for Q{q2} {year2}.",
                        parse_mode=ParseMode.HTML
                    )
                    return
                comparison_text = format_auction_comparison(hist_data, forecast_data)
                try:
                    await update.message.reply_text(comparison_text, parse_mode=ParseMode.HTML)
                    response_time = time.time() - start_time
                    metrics.log_query(user_id, username, question, "auction_compare", response_time, True, "success", "kei")
                except Exception as e:
                    logger.error(f"Error sending auction comparison: {e}")
                    await update.message.reply_text(f"❌ Error formatting response: {e}")
                    response_time = time.time() - start_time
                    metrics.log_query(user_id, username, question, "auction_compare", response_time, False, str(e), "kei")
                return

            # Otherwise: load each period and format general comparison
            loaded = []
            for p in periods:
                pdata = load_auction_period(p)
                if not pdata:
                    label = (
                        f"Q{p['quarter']} {p['year']}" if p['type'] == 'quarter' else (
                            f"{p.get('month')} {p['year']}" if p['type'] == 'month' else f"{p['year']}"
                        )
                    )
                    await update.message.reply_text(
                        f"❌ No auction data found for {label}.",
                        parse_mode=ParseMode.HTML
                    )
                    return
                loaded.append(pdata)

            comparison_text = format_auction_comparison_general(loaded)
            try:
                await update.message.reply_text(comparison_text, parse_mode=ParseMode.HTML)
                response_time = time.time() - start_time
                metrics.log_query(user_id, username, question, "auction_compare", response_time, True, "success", "kei")
            except Exception as e:
                logger.error(f"Error sending auction comparison: {e}")
                await update.message.reply_text(f"❌ Error formatting response: {e}")
                response_time = time.time() - start_time
                metrics.log_query(user_id, username, question, "auction_compare", response_time, False, str(e), "kei")
            return
    
    # Detect if user wants a plot/chart — these are handled by /kin
    needs_plot = any(keyword in question.lower() for keyword in ["plot"])

    # Block Kei responses for general knowledge topics only
    lower_q = question.lower()
    disallowed_phrases = [
    ]
    if any(phrase in lower_q for phrase in disallowed_phrases):
        await update.message.reply_text(
            "⚠️ Kei is disabled for this query. Please use /kin instead.",
            parse_mode=ParseMode.MARKDOWN
        )
        response_time = time.time() - start_time
        metrics.log_query(user_id, username, question, "text", response_time, False, "kin_blocked", "kin")
        return
    
    try:
        await context.bot.send_chat_action(chat_id=update.message.chat_id, action="typing")
    except Exception as e:
        logger.warning(f"Failed to send typing indicator in /kei: {type(e).__name__}. Continuing anyway.")
    
    if needs_plot:
        # Auto-redirect: handle plot request via Kin persona
        try:
            import httpx
            import base64
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {"q": question, "plot": True, "persona": "kin"}
                resp = await client.post(f"{API_BASE_URL}/chat", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    data_summary = data.get("analysis", "")
                    if data.get("image"):
                        image_bytes = base64.b64decode(data["image"])
                        await update.message.reply_photo(photo=image_bytes)
                        if data_summary and data_summary.strip():
                            # Ensure HTML mode consistency: convert fences and append Kin signature
                            content = convert_markdown_code_fences_to_html(data_summary)
                            if not re.search(r"\n<blockquote>~\s+Kin</blockquote>\s*$", content):
                                content = content.rstrip() + "\n<blockquote>~ Kin</blockquote>"
                            await update.message.reply_text(content, parse_mode=ParseMode.HTML)
                    else:
                        # No image returned; send analysis in HTML with Kin signature
                        content = convert_markdown_code_fences_to_html(data_summary)
                        if not re.search(r"\n<blockquote>~\s+Kin</blockquote>\s*$", content):
                            content = content.rstrip() + "\n<blockquote>~ Kin</blockquote>"
                        await update.message.reply_text(content, parse_mode=ParseMode.HTML)
                    response_time = time.time() - start_time
                    metrics.log_query(user_id, username, question, "plot", response_time, True, "auto_redirect_kin", "kin")
                else:
                    await update.message.reply_text(f"⚠️ Error from API: {resp.status_code}")
                    response_time = time.time() - start_time
                    metrics.log_query(user_id, username, question, "plot", response_time, False, f"API error {resp.status_code}", "kin")
        except Exception as e:
            logger.error(f"Error calling /chat endpoint for auto-redirect: {e}")
            # Fallback: generate plot locally using database
            try:
                intent = parse_intent(question)
                db = get_db()
                if intent.type in ("RANGE", "AGG_RANGE"):
                    tenors_to_use = intent.tenors if intent.tenors else ([intent.tenor] if intent.tenor else None)
                    png = generate_plot(
                        db,
                        intent.start_date,
                        intent.end_date,
                        metric=intent.metric if getattr(intent, 'metric', None) else 'yield',
                        tenor=intent.tenor,
                        tenors=tenors_to_use,
                        highlight_date=getattr(intent, 'highlight_date', None)
                    )
                    await update.message.reply_photo(photo=io.BytesIO(png))
                    # Build and send quantitative summary text
                    params = [intent.start_date.isoformat(), intent.end_date.isoformat()]
                    where = 'obs_date BETWEEN ? AND ?'
                    if tenors_to_use:
                        placeholders = ','.join(['?'] * len(tenors_to_use))
                        where += f' AND tenor IN ({placeholders})'
                        params.extend(tenors_to_use)
                    elif intent.tenor:
                        where += ' AND tenor = ?'
                        params.append(intent.tenor)
                    if intent.series:
                        where += ' AND series = ?'
                        params.append(intent.series)
                    rows = db.con.execute(
                        f'SELECT series, tenor, obs_date, price, "yield" FROM ts WHERE {where} ORDER BY obs_date ASC, series',
                        params
                    ).fetchall()
                    rows_list = [
                        dict(
                            series=r[0], tenor=r[1], date=r[2].isoformat(),
                            price=round(r[3], 2) if r[3] is not None else None,
                            **{'yield': round(r[4], 2) if r[4] is not None else None}
                        ) for r in rows
                    ]
                    summary_text = format_range_summary_text(
                        rows_list,
                        start_date=intent.start_date,
                        end_date=intent.end_date,
                        metric=intent.metric if getattr(intent, 'metric', None) else 'yield',
                        signature_persona='Kin'
                    )
                    if summary_text:
                        await update.message.reply_text(summary_text, parse_mode=ParseMode.HTML)
                    response_time = time.time() - start_time
                    metrics.log_query(user_id, username, question, "plot", response_time, True, "local_fallback", "kei")
                    return
                else:
                    await update.message.reply_text("⚠️ Could not parse a plotting range. Please try again.")
                    response_time = time.time() - start_time
                    metrics.log_query(user_id, username, question, "plot", response_time, False, "parse_intent_failed", "kei")
                    return
            except Exception as e2:
                logger.error(f"Local plot fallback failed: {type(e2).__name__}: {e2}")
                await update.message.reply_text("⚠️ Error generating plot. Please try again.")
                response_time = time.time() - start_time
                metrics.log_query(user_id, username, question, "plot", response_time, False, str(e2), "kei")
                return
        return
    else:
        try:
            # If user explicitly asks for a table (e.g., "/kei tab ..."), send as monospace table
            wants_table = lower_q.startswith("tab ") or lower_q.startswith("table ") or " tab " in lower_q or " table " in lower_q
            base_question = re.sub(r"^(tab|table)\s+", "", question, flags=re.IGNORECASE) if wants_table else question
            if wants_table:
                # For tab requests, fetch and format data as a clean monospace table (matching forecast styling)
                try:
                    # Detect multi-variable queries (e.g., "yield and price; for 5 and 10 year")
                    metrics_list = []
                    if ';' in base_question or ' and ' in base_question.split('for')[0] if 'for' in base_question else ' and ' in base_question:
                        # Try to extract multiple metrics
                        if 'yield' in base_question.lower():
                            metrics_list.append('yield')
                        if 'price' in base_question.lower():
                            metrics_list.append('price')
                    
                    intent = parse_intent(base_question)
                    db = get_db()
                    if intent.type in ('RANGE', 'AGG_RANGE'):
                        # Multi-tenor or multi-date range: use table format
                        params = [intent.start_date.isoformat(), intent.end_date.isoformat()]
                        where = 'obs_date BETWEEN ? AND ?'
                        tenors_to_use = intent.tenors if intent.tenors else ([intent.tenor] if intent.tenor else None)
                        if tenors_to_use:
                            tenor_placeholders = ','.join('?' * len(tenors_to_use))
                            where += f' AND tenor IN ({tenor_placeholders})'
                            params.extend(tenors_to_use)
                        if intent.series:
                            where += ' AND series = ?'
                            params.append(intent.series)
                        rows = db.con.execute(
                            f'SELECT series, tenor, obs_date, price, "yield" FROM ts WHERE {where} ORDER BY obs_date ASC, series',
                            params
                        ).fetchall()
                        rows_list = [
                            dict(
                                series=r[0], tenor=r[1], date=r[2].isoformat(),
                                price=round(r[3], 2) if r[3] is not None else None,
                                **{'yield': round(r[4], 2) if r[4] is not None else None}
                            ) for r in rows
                        ]
                        
                        if not rows_list:
                            await update.message.reply_text(
                                f"❌ No data found for {intent.tenor or 'all tenors'} in {intent.start_date} to {intent.end_date}.",
                                parse_mode=ParseMode.MARKDOWN
                            )
                            response_time = time.time() - start_time
                            metrics.log_query(user_id, username, question, "text", response_time, False, "no_data", "kei")
                            return
                        
                        # Compute summary statistics per tenor and metric
                        import statistics
                        summary_lines = []
                        
                        def normalize_tenor_display(tenor_str):
                            """Normalize tenor labels: '5_year' -> '05Y', '10_year' -> '10Y' (with zero-padding for single digits)"""
                            label = str(tenor_str or '').replace('_', ' ').strip()
                            # Normalize patterns like '5year', '5 year', '5Yyear' to '5Y'
                            label = re.sub(r'(?i)(\b\d+)\s*y(?:ear)?\b', r'\1Y', label)
                            label = label.replace('Yyear', 'Y').replace('yyear', 'Y')
                            # Pad single-digit years with leading zero (1Y -> 01Y, 9Y -> 09Y)
                            label = re.sub(r'(?i)^(\d)Y$', r'0\1Y', label)
                            return label
                        if len(metrics_list) > 1:
                            # Format as multi-variable table
                            table_output = format_rows_for_telegram(rows_list, include_date=True, metrics=metrics_list, economist_style=True)
                            
                            # Compute stats for each tenor-metric combination
                            for m in metrics_list:
                                unit = '%' if m == 'yield' else ''
                                for t in tenors_to_use:
                                    vals = [r.get(m) for r in rows_list if r['tenor'] == t and r.get(m) is not None]
                                    if vals:
                                        avg = statistics.mean(vals)
                                        min_val = min(vals)
                                        max_val = max(vals)
                                        std_val = statistics.stdev(vals) if len(vals) > 1 else 0
                                        t_short = normalize_tenor_display(t)
                                        summary_lines.append(f"{t_short} {m}: min {min_val:.2f}, max {max_val:.2f}, avg {avg:.2f}, std {std_val:.2f}")
                            
                            tenor_display = ", ".join(normalize_tenor_display(t) for t in tenors_to_use) if tenors_to_use else "all tenors"
                            metrics_display = " & ".join([m.capitalize() for m in metrics_list])
                            header = f"📊 INDOGB: {metrics_display} | {tenor_display} | {intent.start_date} to {intent.end_date}\n\n"
                        else:
                            # Single metric
                            metric = intent.metric if getattr(intent, 'metric', None) else 'yield'
                            # Compute summary_stats per tenor for bottom-of-table stats
                            import statistics as _stats
                            _per_tenor = {}
                            for r in rows_list:
                                t = r.get('tenor') or 'all'
                                v = r.get(metric)
                                if v is None:
                                    continue
                                _per_tenor.setdefault(t, []).append(v)
                            summary_stats = {metric: {}}
                            for _t, _vals in _per_tenor.items():
                                if _vals:
                                    summary_stats[metric][_t] = {
                                        'count': len(_vals),
                                        'min': min(_vals),
                                        'max': max(_vals),
                                        'avg': _stats.mean(_vals),
                                        'std': _stats.stdev(_vals) if len(_vals) > 1 else 0,
                                    }
                            table_output = format_rows_for_telegram(
                                rows_list,
                                include_date=True,
                                metric=metric,
                                economist_style=True,
                                summary_stats=summary_stats,
                            )
                            
                            # Compute stats per tenor (kept above the table for quick glance)
                            unit = '%' if metric == 'yield' else ''
                            for t in tenors_to_use:
                                vals = [r.get(metric) for r in rows_list if r['tenor'] == t and r.get(metric) is not None]
                                if vals:
                                    avg = statistics.mean(vals)
                                    min_val = min(vals)
                                    max_val = max(vals)
                                    std_val = statistics.stdev(vals) if len(vals) > 1 else 0
                                    t_short = normalize_tenor_display(t)
                                    summary_lines.append(f"{t_short}: min {min_val:.2f}, max {max_val:.2f}, avg {avg:.2f}, std {std_val:.2f}")
                            
                            tenor_display = ", ".join(normalize_tenor_display(t) for t in tenors_to_use) if tenors_to_use else "all tenors"
                            header = f"📊 INDOGB: {metric.capitalize()} | {tenor_display} | {intent.start_date} to {intent.end_date}\n"
                        
                        # Build final message with header, table, and signature (drop duplicated top summaries)
                        response_parts = [header, table_output, "\n<blockquote>~ Kei</blockquote>"]
                        
                        full_response = "\n".join(response_parts)
                        rendered = convert_markdown_code_fences_to_html(full_response)
                        await update.message.reply_text(rendered, parse_mode=ParseMode.HTML)
                        response_time = time.time() - start_time
                        metrics.log_query(user_id, username, question, "text", response_time, True, "table_output", "kei")
                        return
                    elif intent.type == 'POINT':
                        # Single point date
                        d = intent.point_date
                        params = [d.isoformat()]
                        where = 'obs_date = ?'
                        tenors_to_use = intent.tenors if intent.tenors else ([intent.tenor] if intent.tenor else None)
                        if tenors_to_use:
                            placeholders = ','.join(['?'] * len(tenors_to_use))
                            where += f' AND tenor IN ({placeholders})'
                            params.extend(tenors_to_use)
                        if intent.series:
                            where += ' AND series = ?'
                            params.append(intent.series)
                        rows = db.con.execute(
                            f'SELECT series, tenor, price, "yield" FROM ts WHERE {where} ORDER BY series',
                            params
                        ).fetchall()
                        rows_list = [
                            dict(
                                series=r[0],
                                tenor=r[1],
                                price=round(r[2], 2) if r[2] is not None else None,
                                **{'yield': round(r[3], 2) if r[3] is not None else None}
                            )
                            for r in rows
                        ]
                        
                        if not rows_list:
                            await update.message.reply_text(
                                f"❌ No data found for {intent.tenor or 'all tenors'} on {d}.",
                                parse_mode=ParseMode.MARKDOWN
                            )
                            response_time = time.time() - start_time
                            metrics.log_query(user_id, username, question, "text", response_time, False, "no_data", "kei")
                            return
                        
                        def normalize_tenor_display(tenor_str):
                            """Normalize tenor labels: '5_year' -> '05Y', '10_year' -> '10Y' (with zero-padding for single digits)"""
                            label = str(tenor_str or '').replace('_', ' ').strip()
                            # Normalize patterns like '5year', '5 year', '5Yyear' to '5Y'
                            label = re.sub(r'(?i)(\b\d+)\s*y(?:ear)?\b', r'\1Y', label)
                            label = label.replace('Yyear', 'Y').replace('yyear', 'Y')
                            # Pad single-digit years with leading zero (1Y -> 01Y, 9Y -> 09Y)
                            label = re.sub(r'(?i)^(\d)Y$', r'0\1Y', label)
                            return label
                        
                        metric = intent.metric if getattr(intent, 'metric', None) else 'yield'
                        table_output = format_rows_for_telegram(rows_list, include_date=False, metric=metric, economist_style=True)
                        tenor_display = ", ".join(normalize_tenor_display(t) for t in tenors_to_use) if tenors_to_use else "all tenors"
                        header = f"📊 INDOGB: {metric.capitalize()} | {tenor_display} | {d}\n\n"
                        
                        full_response = header + table_output + "\n<blockquote>~ Kei</blockquote>"
                        rendered = convert_markdown_code_fences_to_html(full_response)
                        await update.message.reply_text(rendered, parse_mode=ParseMode.HTML)
                        response_time = time.time() - start_time
                        metrics.log_query(user_id, username, question, "text", response_time, True, "table_output", "kei")
                        return
                    else:
                        await update.message.reply_text(
                            "❌ Table format expects a date range or point date query. Try: '/kei tab yield 5 year Feb 2025'",
                            parse_mode=ParseMode.MARKDOWN
                        )
                        response_time = time.time() - start_time
                        metrics.log_query(user_id, username, question, "text", response_time, False, "invalid_query_type", "kei")
                        return
                except Exception as e:
                    logger.error(f"Error processing /kei tab query: {e}", exc_info=True)
                    await update.message.reply_text(
                        f"❌ Could not parse that query. Try: '/kei tab yield 5 year Feb 2025'",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    response_time = time.time() - start_time
                    metrics.log_query(user_id, username, question, "text", response_time, False, "parse_error", "kei")
                    return
            # Check if this is a "next N observations" forecast query
            next_match = re.search(r"next\s+(\d+)\s+(observations?|obs|points|days)", question.lower())
            is_forecast_next = next_match and any(kw in question.lower() for kw in ["forecast", "predict", "estimate"])
            
            # For "next N observations" forecasts, the tables are handled directly by try_compute_bond_summary
            # which calls forecast_tenor_next_days and returns formatted tables.
            # No separate ask_kei analysis for these forecasts to avoid unrelated commentary.
            if is_forecast_next:
                # Get the formatted forecast tables directly
                tables_summary = await try_compute_bond_summary(question)
                if tables_summary:
                    # Send tables only (no separate analysis message)
                    try:
                        await update.message.reply_text(
                            tables_summary,
                            parse_mode=ParseMode.MARKDOWN
                        )
                    except BadRequest:
                        # Fallback: send without Markdown parsing
                        await update.message.reply_text(tables_summary)
                    response_time = time.time() - start_time
                    metrics.log_query(user_id, username, question, "forecast", response_time, True, "forecast_next", "kei")
                    return
                else:
                    await update.message.reply_text("⚠️ Could not compute forecast. Please check your query.")
                    response_time = time.time() - start_time
                    metrics.log_query(user_id, username, question, "forecast", response_time, False, "No forecast data", "kei")
                    return
            else:
                # For other queries, just get Kei's response (which includes tables as context)
                answer = await ask_kei(question)
                if not answer or not answer.strip():
                    await update.message.reply_text("⚠️ Kei returned an empty response. Please try again.")
                    response_time = time.time() - start_time
                    metrics.log_query(user_id, username, question, "text", response_time, False, "Empty response", "kei")
                    return
                formatted_response = f"{answer}"
                await update.message.reply_text(formatted_response, parse_mode=ParseMode.HTML)
            
            response_time = time.time() - start_time
            metrics.log_query(user_id, username, question, "text", response_time, True, persona="kei")
        except Exception as e:
            logger.error(f"Error in /kei command: {e}")
            await update.message.reply_text("⚠️ Error processing query. Please try again.")
            response_time = time.time() - start_time
            try:
                metrics.log_query(user_id, username, question, "text", response_time, False, str(e), "kei")
            except Exception as log_err:
                logger.error(f"Failed to log /kei error metrics: {log_err}")
            return


async def kin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/kin <question> — ask persona Kin (Perplexity)."""
    start_time = time.time()
    user_id = update.message.from_user.id
    username = update.message.from_user.username or f"user_{user_id}"

    if not is_user_authorized(user_id):
        await update.message.reply_text(
            "⛔ Access denied. This bot is restricted to authorized users only."
        )
        logger.warning("Unauthorized access attempt from user_id=%s", user_id)
        metrics.log_error("/kin", "Unauthorized access", user_id)
        return

    question = " ".join(context.args).strip() if context.args else ""
    if not question:
        await update.message.reply_text("Usage: /kin <question>")
        return

    lower_q = question.lower()
    needs_plot = any(keyword in lower_q for keyword in ["plot"])

    try:
        await context.bot.send_chat_action(chat_id=update.message.chat_id, action="typing")
    except Exception as e:
        logger.warning(f"Failed to send typing indicator in /kin: {type(e).__name__}. Continuing anyway.")

    if needs_plot:
        # Check for bond plot query first (specific period formats)
        bond_plot_req = parse_bond_plot_query(lower_q)
        if bond_plot_req:
            try:
                db = get_db()
                cov_min, cov_max = db.coverage()
                if cov_min and cov_max:
                    if bond_plot_req['end_date'] < cov_min or bond_plot_req['start_date'] > cov_max:
                        await update.message.reply_text(
                            f"❌ No yield data in requested range. Coverage: {cov_min} to {cov_max}.",
                            parse_mode=ParseMode.HTML
                        )
                        return
                png = generate_plot(
                    db,
                    bond_plot_req['start_date'],
                    bond_plot_req['end_date'],
                    metric=bond_plot_req['metric'],
                    tenors=bond_plot_req['tenors']
                )
                await update.message.reply_photo(photo=io.BytesIO(png))
                
                # Generate Kin's analysis summary for the plot
                params = [bond_plot_req['start_date'].isoformat(), bond_plot_req['end_date'].isoformat()]
                placeholders = ','.join(['?'] * len(bond_plot_req['tenors']))
                where = f'obs_date BETWEEN ? AND ? AND tenor IN ({placeholders})'
                params.extend(bond_plot_req['tenors'])
                
                rows = db.con.execute(
                    f'SELECT series, tenor, obs_date, price, "yield" FROM ts WHERE {where} ORDER BY obs_date ASC, series',
                    params
                ).fetchall()
                if rows:
                    rows_list = [
                        dict(
                            series=r[0], tenor=r[1], date=r[2].isoformat(),
                            price=round(r[3], 2) if r[3] is not None else None,
                            **{'yield': round(r[4], 2) if r[4] is not None else None}
                        ) for r in rows
                    ]
                    # Generate quantitative summary for Kin to analyze
                    kei_summary = format_range_summary_text(
                        rows_list,
                        start_date=bond_plot_req['start_date'],
                        end_date=bond_plot_req['end_date'],
                        metric=bond_plot_req['metric'],
                        signature_persona='Kei'  # Use Kei for data summary
                    )
                    
                    # Have Kin analyze the quantitative summary
                    try:
                        kin_prompt = (
                            f"Original question: {question}\n\n"
                            f"Quantitative summary:\n{kei_summary}\n\n"
                            f"Based on this data and the original question, provide your strategic interpretation and analysis."
                        )
                        kin_answer = await ask_kin(kin_prompt, dual_mode=False)
                        if kin_answer and kin_answer.strip():
                            await update.message.reply_text(kin_answer, parse_mode=ParseMode.HTML)
                        else:
                            # Fallback: send the summary if Kin fails
                            logger.warning("Kin returned empty response, sending summary instead")
                            await update.message.reply_text(kei_summary.replace('~ Kei', '~ Kin'), parse_mode=ParseMode.HTML)
                    except Exception as kin_error:
                        logger.error(f"Error calling ask_kin: {kin_error}")
                        # Fallback: send the summary
                        await update.message.reply_text(kei_summary.replace('~ Kei', '~ Kin'), parse_mode=ParseMode.HTML)
                
                response_time = time.time() - start_time
                metrics.log_query(user_id, username, question, "bond_plot", response_time, True, "success", "kin")
            except Exception as e:
                logger.error(f"Error generating bond plot: {e}")
                await update.message.reply_text(f"❌ Error generating plot: {e}")
                response_time = time.time() - start_time
                metrics.log_query(user_id, username, question, "bond_plot", response_time, False, str(e), "kin")
            return
        
        # Fall back to general plot handling via API or local generation
        try:
            import httpx
            import base64
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {"q": question, "plot": True, "persona": "kin"}
                resp = await client.post(f"{API_BASE_URL}/chat", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    data_summary = data.get("analysis", "")
                    if data.get("image"):
                        image_bytes = base64.b64decode(data["image"])
                        await update.message.reply_photo(photo=image_bytes)
                        if data_summary and data_summary.strip():
                            analysis_html = convert_markdown_code_fences_to_html(data_summary)
                            analysis_html = html_quote_signature(f"{analysis_html}\n\n<blockquote>~ Kin</blockquote>")
                            await update.message.reply_text(analysis_html, parse_mode=ParseMode.HTML)
                    else:
                        analysis_html = convert_markdown_code_fences_to_html(data_summary)
                        analysis_html = html_quote_signature(f"{analysis_html}\n\n<blockquote>~ Kin</blockquote>")
                        await update.message.reply_text(
                            f"🌍 Kin | Economics & Strategy\n\n{analysis_html}",
                            parse_mode=ParseMode.HTML
                        )
                    response_time = time.time() - start_time
                    metrics.log_query(user_id, username, question, "plot", response_time, True, persona="kin")
                else:
                    await update.message.reply_text(f"⚠️ Error from API: {resp.status_code}")
                    response_time = time.time() - start_time
                    metrics.log_query(user_id, username, question, "plot", response_time, False, f"API error {resp.status_code}", "kin")
        except Exception as e:
            logger.error(f"Error calling /chat endpoint: {e}")
            # Fallback: generate plot locally using database
            try:
                intent = parse_intent(question)
                db = get_db()
                if intent.type in ("RANGE", "AGG_RANGE"):
                    tenors_to_use = intent.tenors if intent.tenors else ([intent.tenor] if intent.tenor else None)
                    png = generate_plot(
                        db,
                        intent.start_date,
                        intent.end_date,
                        metric=intent.metric if getattr(intent, 'metric', None) else 'yield',
                        tenor=intent.tenor,
                        tenors=tenors_to_use,
                        highlight_date=getattr(intent, 'highlight_date', None)
                    )
                    await update.message.reply_photo(photo=io.BytesIO(png))

                    # Build and send quantitative summary text
                    params = [intent.start_date.isoformat(), intent.end_date.isoformat()]
                    where = 'obs_date BETWEEN ? AND ?'
                    if tenors_to_use:
                        placeholders = ','.join(['?'] * len(tenors_to_use))
                        where += f' AND tenor IN ({placeholders})'
                        params.extend(tenors_to_use)
                    elif intent.tenor:
                        where += ' AND tenor = ?'
                        params.append(intent.tenor)
                    if intent.series:
                        where += ' AND series = ?'
                        params.append(intent.series)
                    rows = db.con.execute(
                        f'SELECT series, tenor, obs_date, price, "yield" FROM ts WHERE {where} ORDER BY obs_date ASC, series',
                        params
                    ).fetchall()
                    rows_list = [
                        dict(
                            series=r[0], tenor=r[1], date=r[2].isoformat(),
                            price=round(r[3], 2) if r[3] is not None else None,
                            **{'yield': round(r[4], 2) if r[4] is not None else None}
                        ) for r in rows
                    ]
                    # Generate quantitative summary
                    kei_summary = format_range_summary_text(
                        rows_list,
                        start_date=intent.start_date,
                        end_date=intent.end_date,
                        metric=intent.metric if getattr(intent, 'metric', None) else 'yield',
                        signature_persona='Kei'
                    )
                    
                    # Have Kin analyze the quantitative summary
                    try:
                        kin_prompt = (
                            f"Original question: {question}\n\n"
                            f"Quantitative summary:\n{kei_summary}\n\n"
                            f"Based on this data and the original question, provide your strategic interpretation and analysis."
                        )
                        kin_answer = await ask_kin(kin_prompt, dual_mode=False)
                        if kin_answer and kin_answer.strip():
                            await update.message.reply_text(kin_answer, parse_mode=ParseMode.HTML)
                        else:
                            # Fallback: send the summary if Kin fails
                            logger.warning("Kin returned empty response, sending summary instead")
                            await update.message.reply_text(kei_summary.replace('~ Kei', '~ Kin'), parse_mode=ParseMode.HTML)
                    except Exception as kin_error:
                        logger.error(f"Error calling ask_kin: {kin_error}")
                        # Fallback: send the summary
                        await update.message.reply_text(kei_summary.replace('~ Kei', '~ Kin'), parse_mode=ParseMode.HTML)
                    
                    response_time = time.time() - start_time
                    metrics.log_query(user_id, username, question, "plot", response_time, True, persona="kin")
                    return
                else:
                    await update.message.reply_text("⚠️ Could not parse a plotting range. Please try again.")
                    response_time = time.time() - start_time
                    metrics.log_query(user_id, username, question, "plot", response_time, False, "parse_intent_failed", "kin")
                    return
            except Exception as e2:
                logger.error(f"Local plot fallback failed: {type(e2).__name__}: {e2}")
                await update.message.reply_text("⚠️ Error generating plot. Please try again.")
                response_time = time.time() - start_time
                metrics.log_query(user_id, username, question, "plot", response_time, False, str(e2), "kin")
                return
        return

    # Block quantitative/forecasting topics when not plotting
    disallowed_keywords = [
        'forecast', 'predict', 'estimate'
    ]
    if any(keyword in lower_q for keyword in disallowed_keywords):
        await update.message.reply_text(
            "⚠️ Kin is disabled for this query. Please use /kei instead.",
            parse_mode=ParseMode.MARKDOWN
        )
        response_time = time.time() - start_time
        metrics.log_query(user_id, username, question, "text", response_time, False, "kei_query", "kei")
        return

    try:
        answer = await ask_kin(question)
        if not answer or not answer.strip():
            await update.message.reply_text("⚠️ Kin returned an empty response. Please try again.")
            response_time = time.time() - start_time
            metrics.log_query(user_id, username, question, "text", response_time, False, "Empty response", "kin")
            return
        # Format response for HTML display
        formatted_response = f"{answer}"
        try:
            await update.message.reply_text(formatted_response, parse_mode=ParseMode.HTML)
        except BadRequest as e:
            # Fallback: resend without parse mode if Telegram rejects HTML entities
            logger.warning(f"Kin BadRequest on HTML parse: {e}. Resending without parse mode.")
            await update.message.reply_text(formatted_response)
        response_time = time.time() - start_time
        metrics.log_query(user_id, username, question, "text", response_time, True, persona="kin")
    except Exception as e:
        logger.error(f"Error in /kin command: {e}")
        await update.message.reply_text("⚠️ Error processing query. Please try again.")
        response_time = time.time() - start_time
        try:
            metrics.log_query(user_id, username, question, "text", response_time, False, str(e), "kin")
        except Exception as log_err:
            logger.error(f"Failed to log /kin error metrics: {log_err}")
        return


async def both_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/both <question> — chain both personas: Kei (quantitative) → Kin (interpretation)."""
    start_time = time.time()
    user_id = update.message.from_user.id
    username = update.message.from_user.username or f"user_{user_id}"
    
    if not is_user_authorized(user_id):
        await update.message.reply_text(
            "⛔ Access denied. This bot is restricted to authorized users only."
        )
        logger.warning("Unauthorized access attempt from user_id=%s", user_id)
        metrics.log_error("/both", "Unauthorized access", user_id)
        return

    question = " ".join(context.args).strip() if context.args else ""
    if not question:
        await update.message.reply_text("Usage: /both <question>")
        return
    
    # Detect if user wants a plot (route through FastAPI /chat endpoint)
    needs_plot = any(keyword in question.lower() for keyword in ["plot"])
    
    try:
        await context.bot.send_chat_action(chat_id=update.message.chat_id, action="typing")
    except Exception as e:
        logger.warning(f"Failed to send typing indicator in /both: {type(e).__name__}. Continuing anyway.")

    # Fast path: try to compute quantitative summary locally (auctions/bonds) before hitting API
    # For /both, we need to chain Kei → Kin, so handle auction tables specially
    q_lower = question.lower()
    
    # Check for historical auction queries with year ranges (e.g., "from 2010 to 2024")
    is_auction_query = ('auction' in q_lower or 'incoming' in q_lower or 'awarded' in q_lower or 'bid' in q_lower)
    if is_auction_query:
        yr_range = re.search(r"from\s+(19\d{2}|20\d{2})\s+to\s+(19\d{2}|20\d{2})", q_lower)
        if yr_range:
            y_start = int(yr_range.group(1))
            y_end = int(yr_range.group(2))
            if y_start <= y_end and y_end <= 2024:
                try:
                    # Use the same data source as /kei tab: load_auction_period via AuctionDB
                    # This ensures consistency between /kei tab and /both commands
                    periods = [{'type': 'year', 'year': y} for y in range(y_start, y_end + 1)]
                    periods_data = []
                    skipped_periods = []
                    
                    for p in periods:
                        pdata = load_auction_period(p)
                        if not pdata:
                            skipped_periods.append(f"{int(p['year'])}")
                            continue
                        periods_data.append(pdata)
                    
                    if not periods_data:
                        await update.message.reply_text(
                            f"❌ No auction data found for {y_start}–{y_end}.",
                            parse_mode=ParseMode.HTML
                        )
                        response_time = time.time() - start_time
                        metrics.log_query(user_id, username, question, "text", response_time, False, "no_auction_data", "both")
                        return
                    
                    # Generate Kei's table using the same format as /kei tab
                    metrics_list = ['incoming', 'awarded']
                    kei_table = format_auction_metrics_table(periods_data, metrics_list)
                    await update.message.reply_text(kei_table, parse_mode=ParseMode.MARKDOWN)
                    
                    # Have Kin analyze the table
                    kin_prompt = (
                        f"Original question: {question}\n\n"
                        f"Kei's quantitative analysis:\n{kei_table}\n\n"
                        f"Based on this auction data table and the original question, provide your strategic interpretation and economic analysis."
                    )
                    kin_answer = await ask_kin(kin_prompt, dual_mode=True)
                    if kin_answer and kin_answer.strip():
                        await update.message.reply_text(kin_answer, parse_mode=ParseMode.HTML)
                    
                    response_time = time.time() - start_time
                    metrics.log_query(user_id, username, question, "text", response_time, True, "auction_table_both", "both")
                    return
                except Exception as e:
                    logger.error(f"Error in auction table /both: {e}", exc_info=True)
                    # Don't fall through - send error to user instead of trying API fallback
                    await update.message.reply_text(f"❌ Error processing auction data: {type(e).__name__}")
                    response_time = time.time() - start_time
                    metrics.log_query(user_id, username, question, "text", response_time, False, f"auction_error: {e}", "both")
                    return
    
    # For non-auction queries, use the general fast path
    try:
        data_summary = await try_compute_bond_summary(question)
        if data_summary:
            await update.message.reply_text(data_summary, parse_mode=ParseMode.HTML)
            response_time = time.time() - start_time
            metrics.log_query(user_id, username, question, "text", response_time, True, "local_summary", "both")
            return
    except Exception as e:
        logger.warning(f"/both local summary fast-path failed: {type(e).__name__}: {e}")
    
    if needs_plot:
        # Prefer local bond plot handling when parser succeeds, to ensure full-range data and consistent summaries
        bond_plot_req = parse_bond_plot_query(question.lower())
        if bond_plot_req:
            try:
                db = get_db()
                cov_min, cov_max = db.coverage()
                if cov_min and cov_max:
                    if bond_plot_req['end_date'] < cov_min or bond_plot_req['start_date'] > cov_max:
                        await update.message.reply_text(
                            f"❌ No yield data in requested range. Coverage: {cov_min} to {cov_max}.",
                            parse_mode=ParseMode.HTML
                        )
                        return
                png = generate_plot(
                    db,
                    bond_plot_req['start_date'],
                    bond_plot_req['end_date'],
                    metric=bond_plot_req['metric'],
                    tenors=bond_plot_req['tenors']
                )
                await update.message.reply_photo(photo=io.BytesIO(png))

                # Query data and generate summary
                params = [bond_plot_req['start_date'].isoformat(), bond_plot_req['end_date'].isoformat()]
                placeholders = ','.join(['?'] * len(bond_plot_req['tenors']))
                where = f'obs_date BETWEEN ? AND ? AND tenor IN ({placeholders})'
                params.extend(bond_plot_req['tenors'])

                rows = db.con.execute(
                    f'SELECT series, tenor, obs_date, price, "yield" FROM ts WHERE {where} ORDER BY obs_date ASC, series',
                    params
                ).fetchall()
                rows_list = [
                    dict(
                        series=r[0], tenor=r[1], date=r[2].isoformat(),
                        price=round(r[3], 2) if r[3] is not None else None,
                        **{'yield': round(r[4], 2) if r[4] is not None else None}
                    ) for r in rows
                ]

                kei_summary = format_range_summary_text(
                    rows_list,
                    start_date=bond_plot_req['start_date'],
                    end_date=bond_plot_req['end_date'],
                    metric=bond_plot_req['metric'],
                    signature_persona='Kei'
                )

                # Send Kei's summary
                await update.message.reply_text(kei_summary, parse_mode=ParseMode.HTML)

                # Attempt to get Kin's analysis, but don't fail if Perplexity is unavailable
                try:
                    kin_prompt = (
                        f"Original question: {question}\n\n"
                        f"Kei's quantitative analysis:\n{kei_summary}\n\n"
                        f"Based on this analysis and the original question, provide your strategic interpretation and conclusion."
                    )
                    kin_answer = await ask_kin(kin_prompt, dual_mode=True)
                    if kin_answer and kin_answer.strip():
                        await update.message.reply_text(kin_answer, parse_mode=ParseMode.HTML)
                except Exception as kin_err:
                    logger.warning(f"Kin analysis failed in /both plot: {type(kin_err).__name__}: {kin_err}")
                    # Continue - we already sent the Kei summary, so don't fall through to API

                response_time = time.time() - start_time
                metrics.log_query(user_id, username, question, "plot", response_time, True, "local_bond_plot", "both")
                return
            except Exception as e:
                logger.error(f"Error generating local bond plot: {e}")
                # If local path fails, continue to API

        try:
            import httpx
            import base64
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {"q": question, "plot": True, "persona": "both"}
                resp = await client.post(f"{API_BASE_URL}/chat", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    data_summary = data.get('analysis', '')
                    if data.get("image"):
                        image_bytes = base64.b64decode(data["image"])
                        await update.message.reply_photo(photo=image_bytes)
                        # Send pre-computed analysis from FastAPI (no redundant LLM calls)
                        if data_summary and data_summary.strip():
                            # Don't escape HTML blockquote tags - they're already safe from the API
                            await update.message.reply_text(
                                strip_markdown_emphasis(data_summary),
                                parse_mode=ParseMode.HTML
                            )
                    else:
                        # No image, send analysis-only response
                        await update.message.reply_text(
                            f"📊 <b>Kei & Kin | Numbers to Meaning</b>\n\n{strip_markdown_emphasis(data_summary)}",
                            parse_mode=ParseMode.HTML
                        )
                    response_time = time.time() - start_time
                    metrics.log_query(user_id, username, question, "plot", response_time, True, persona="both")
                else:
                    await update.message.reply_text(f"⚠️ Error from API: {resp.status_code}")
                    response_time = time.time() - start_time
                    metrics.log_query(user_id, username, question, "plot", response_time, False, f"API error {resp.status_code}", "both")
        except Exception as e:
            logger.error(f"Error calling /chat endpoint: {e}")
            # Fallback: generate plot locally using database
            try:
                # Try bond plot query parser first (handles "from oct 2024 to feb 2025" format)
                bond_plot_req = parse_bond_plot_query(question.lower())
                db = get_db()
                
                if bond_plot_req:
                    # Use bond plot parser result
                    cov_min, cov_max = db.coverage()
                    if cov_min and cov_max:
                        if bond_plot_req['end_date'] < cov_min or bond_plot_req['start_date'] > cov_max:
                            await update.message.reply_text(
                                f"❌ No yield data in requested range. Coverage: {cov_min} to {cov_max}.",
                                parse_mode=ParseMode.HTML
                            )
                            return
                    png = generate_plot(
                        db,
                        bond_plot_req['start_date'],
                        bond_plot_req['end_date'],
                        metric=bond_plot_req['metric'],
                        tenors=bond_plot_req['tenors']
                    )
                    await update.message.reply_photo(photo=io.BytesIO(png))
                    
                    # Query data and generate summary
                    params = [bond_plot_req['start_date'].isoformat(), bond_plot_req['end_date'].isoformat()]
                    placeholders = ','.join(['?'] * len(bond_plot_req['tenors']))
                    where = f'obs_date BETWEEN ? AND ? AND tenor IN ({placeholders})'
                    params.extend(bond_plot_req['tenors'])
                    
                    rows = db.con.execute(
                        f'SELECT series, tenor, obs_date, price, "yield" FROM ts WHERE {where} ORDER BY obs_date ASC, series',
                        params
                    ).fetchall()
                    rows_list = [
                        dict(
                            series=r[0], tenor=r[1], date=r[2].isoformat(),
                            price=round(r[3], 2) if r[3] is not None else None,
                            **{'yield': round(r[4], 2) if r[4] is not None else None}
                        ) for r in rows
                    ]
                    
                    # Generate Kei's quantitative summary with actual data
                    kei_summary = format_range_summary_text(
                        rows_list,
                        start_date=bond_plot_req['start_date'],
                        end_date=bond_plot_req['end_date'],
                        metric=bond_plot_req['metric'],
                        signature_persona='Kei'
                    )
                    
                    # Have Kin analyze Kei's summary
                    kin_prompt = (
                        f"Original question: {question}\n\n"
                        f"Kei's quantitative analysis:\n{kei_summary}\n\n"
                        f"Based on this analysis and the original question, provide your strategic interpretation and conclusion."
                    )
                    kin_answer = await ask_kin(kin_prompt, dual_mode=True)
                    if kin_answer and kin_answer.strip():
                        await update.message.reply_text(kin_answer, parse_mode=ParseMode.HTML)
                    
                    response_time = time.time() - start_time
                    metrics.log_query(user_id, username, question, "plot", response_time, True, "local_fallback_bond_plot", "both")
                    return
                
                # Fall back to parse_intent for other formats
                intent = parse_intent(question)
                if intent.type in ("RANGE", "AGG_RANGE"):
                    tenors_to_use = intent.tenors if intent.tenors else ([intent.tenor] if intent.tenor else None)
                    png = generate_plot(
                        db,
                        intent.start_date,
                        intent.end_date,
                        metric=intent.metric if getattr(intent, 'metric', None) else 'yield',
                        tenor=intent.tenor,
                        tenors=tenors_to_use,
                        highlight_date=getattr(intent, 'highlight_date', None)
                    )
                    await update.message.reply_photo(photo=io.BytesIO(png))
                    # Build and send quantitative summary text
                    params = [intent.start_date.isoformat(), intent.end_date.isoformat()]
                    where = 'obs_date BETWEEN ? AND ?'
                    if tenors_to_use:
                        placeholders = ','.join(['?'] * len(tenors_to_use))
                        where += f' AND tenor IN ({placeholders})'
                        params.extend(tenors_to_use)
                    elif intent.tenor:
                        where += ' AND tenor = ?'
                        params.append(intent.tenor)
                    if intent.series:
                        where += ' AND series = ?'
                        params.append(intent.series)
                    rows = db.con.execute(
                        f'SELECT series, tenor, obs_date, price, "yield" FROM ts WHERE {where} ORDER BY obs_date ASC, series',
                        params
                    ).fetchall()
                    rows_list = [
                        dict(
                            series=r[0], tenor=r[1], date=r[2].isoformat(),
                            price=round(r[3], 2) if r[3] is not None else None,
                            **{'yield': round(r[4], 2) if r[4] is not None else None}
                        ) for r in rows
                    ]
                    summary_text = format_range_summary_text(
                        rows_list,
                        start_date=intent.start_date,
                        end_date=intent.end_date,
                        metric=intent.metric if getattr(intent, 'metric', None) else 'yield'
                    )
                    if summary_text:
                        await update.message.reply_text(
                            f"📊 <b>Kei & Kin | Numbers to Meaning</b>\n\n{strip_markdown_emphasis(html_module.escape(summary_text))}",
                            parse_mode=ParseMode.HTML
                        )
                    response_time = time.time() - start_time
                    metrics.log_query(user_id, username, question, "plot", response_time, True, "local_fallback", "both")
                else:
                    await update.message.reply_text("⚠️ Could not parse a plotting range. Please try again.")
                    response_time = time.time() - start_time
                    metrics.log_query(user_id, username, question, "plot", response_time, False, "parse_intent_failed", "both")
            except Exception as e2:
                logger.error(f"Local plot fallback failed: {type(e2).__name__}: {e2}")
                await update.message.reply_text("⚠️ Error generating plot. Please try again.")
                response_time = time.time() - start_time
                metrics.log_query(user_id, username, question, "plot", response_time, False, str(e2), "both")
                return
    else:
        try:
            result = await ask_kei_then_kin(question)
            
            kei_answer = result["kei"]
            kin_answer = result["kin"]
            
            if not kei_answer or not kei_answer.strip():
                await update.message.reply_text("⚠️ Kei returned an empty response. Please try again.")
                response_time = time.time() - start_time
                metrics.log_query(user_id, username, question, "text", response_time, False, "Kei empty response", "both")
                return
            if not kin_answer or not kin_answer.strip():
                await update.message.reply_text("⚠️ Kin returned an empty response. Please try again.")
                response_time = time.time() - start_time
                metrics.log_query(user_id, username, question, "text", response_time, False, "Kin empty response", "both")
                return
            
            # Strip individual persona signatures from both answers
            # Remove both old-style (________) and new-style (<blockquote>) signatures
            def strip_signature(answer):
                """Remove trailing signature lines (both ________ and <blockquote> formats)."""
                # Remove all blockquote signatures (anywhere, not just end of string)
                answer = re.sub(r'<blockquote>~\s+(Kei|Kin|Kei x Kin|Kei & Kin)</blockquote>', '', answer, flags=re.IGNORECASE)
                # Remove any remaining plain text signatures (~ Kei, ~ Kin, ~ Kei x Kin)
                answer = re.sub(r'\n*~\s+(Kei|Kin|Kei x Kin|Kei & Kin)\s*$', '', answer, flags=re.IGNORECASE | re.MULTILINE)
                # Then remove old-style ________ signatures
                lines = answer.rstrip().split('\n')
                for i in range(len(lines) - 1, -1, -1):
                    if '________' in lines[i]:
                        return '\n'.join(lines[:i]).rstrip()
                return answer.rstrip()
            
            kei_clean = strip_signature(kei_answer)
            kin_clean = strip_signature(kin_answer)
            
            response = (
                "🎯 <b>Kei & Kin | Data → Insight</b>\n\n"
                f"{html_module.escape(kei_clean)}\n\n"
                "---\n\n"
                f"{html_module.escape(kin_clean)}\n\n"
                "<blockquote>~ Kei x Kin</blockquote>"
            )
            
            await update.message.reply_text(response, parse_mode=ParseMode.HTML)
            response_time = time.time() - start_time
            metrics.log_query(user_id, username, question, "text", response_time, True, persona="both")
        except Exception as e:
            logger.error(f"Error in /both command: {e}")
            await update.message.reply_text("⚠️ Error processing query. Please try again.")
            response_time = time.time() - start_time
            try:
                metrics.log_query(user_id, username, question, "text", response_time, False, str(e), "both")
            except Exception as log_err:
                logger.error(f"Failed to log /both error metrics: {log_err}")
            return


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming text messages with bond queries."""
    user_id = update.message.from_user.id
    username = update.message.from_user.username or f"user_{user_id}"
    
    if not is_user_authorized(user_id):
        await update.message.reply_text(
            "⛔ Access denied. This bot is restricted to authorized users only."
        )
        logger.warning("Unauthorized access attempt from user_id=%s", user_id)
        return
    
    user_query = update.message.text or ""
    chat_id = update.message.chat_id
    start_time = time.time()
    
    # Send typing indicator (gracefully skip if timeout occurs)
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    except Exception as e:
        logger.warning(f"Failed to send typing indicator: {type(e).__name__}: {e}. Continuing anyway.")
    
    try:
        # Persona routing: \kei (OpenAI) and \kin (Perplexity)
        lowered = user_query.strip().lower()
        if lowered.startswith("\\kei"):
            question = user_query.strip()[4:].strip()  # remove prefix
            if not question:
                await update.message.reply_text("Usage: \\kei <question>")
                return
            try:
                result = await ask_kei(question)
                if result:
                    await update.message.reply_text(result, parse_mode=ParseMode.HTML)
                else:
                    await update.message.reply_text("⚠️ Kei returned an empty response. Please try again.")
            except Exception as e:
                logger.error(f"Error handling \\kei: {e}")
                await update.message.reply_text("⚠️ Error processing query.")
            return

        if lowered.startswith("\\kin"):
            question = user_query.strip()[4:].strip()
            if not question:
                await update.message.reply_text("Usage: \\kin <question>")
                return
            try:
                await context.bot.send_chat_action(chat_id=chat_id, action="typing")
            except Exception as e:
                logger.warning(f"Failed to send typing indicator: {type(e).__name__}. Continuing anyway.")
            answer = await ask_kin(question)
            if not answer or not answer.strip():
                await update.message.reply_text("⚠️ Kin returned an empty response. Please try again.")
                return
            formatted_response = f"{html_module.escape(answer)}"
            await update.message.reply_text(formatted_response, parse_mode=ParseMode.HTML)
            return

        # Determine if user wants a plot
        lower_q = user_query.lower()
        plot_keywords = ('plot', 'chart', 'show', 'visualize', 'graph')
        wants_plot = any(k in lower_q for k in plot_keywords)
        
        # Parse the user's intent
        try:
            intent = parse_intent(user_query)
        except Exception as e:
            logger.error(f"Intent parsing failed for '{user_query}': {type(e).__name__}: {e}", exc_info=True)
            await update.message.reply_text(
                f"❌ Could not parse your query. Please try a different format.\n\nExample: 'plot yield 5 year 2025' or '/kei plot yield 5 year 2025'",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        db = get_db()
        
        # POINT query
        if intent.type == 'POINT':
            d = intent.point_date
            params = [d.isoformat()]
            where = 'obs_date = ?'
            # Honor multi-tenor requests for direct Telegram responses as well
            tenors_to_use = intent.tenors if getattr(intent, 'tenors', None) else ([intent.tenor] if getattr(intent, 'tenor', None) else None)
            if tenors_to_use:
                placeholders = ','.join(['?'] * len(tenors_to_use))
                where += f' AND tenor IN ({placeholders})'
                params.extend(tenors_to_use)
            if intent.series:
                where += ' AND series = ?'
                params.append(intent.series)
            
            rows = db.con.execute(
                f'SELECT series, tenor, price, "yield" FROM ts WHERE {where} ORDER BY series',
                params
            ).fetchall()
            
            rows_list = [
                dict(
                    series=r[0],
                    tenor=r[1],
                    price=round(r[2], 2) if r[2] is not None else None,
                    **{'yield': round(r[3], 2) if r[3] is not None else None}
                )
                for r in rows
            ]
            
            response_text = f"📊 *Found {len(rows_list)} bond(s) for {intent.tenor or 'all tenors'} on {d}:*\n\n"
            response_text += format_rows_for_telegram(rows_list, include_date=False, metric=intent.metric if hasattr(intent, 'metric') else 'yield', economist_style=True)
            
            await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)
        
        # RANGE / AGG_RANGE query
        elif intent.type in ('RANGE', 'AGG_RANGE'):
            if intent.agg:
                # Aggregation query
                val, n = db.aggregate(
                    intent.start_date, intent.end_date,
                    intent.metric, intent.agg,
                    intent.series, intent.tenor
                )
                
                response_text = (
                    f"📊 *{intent.agg.upper()} {intent.metric}*\n"
                    f"Period: {intent.start_date} → {intent.end_date}\n"
                    f"Result: *{round(val, 2) if val is not None else 'N/A'}*\n"
                    f"Data points: {n}"
                )
                
                await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)
                
                # Generate plot if requested
                if wants_plot:
                    try:
                        await context.bot.send_chat_action(chat_id=chat_id, action="upload_photo")
                    except Exception as e:
                        logger.warning(f"Failed to send upload_photo action: {type(e).__name__}. Continuing anyway.")
                    png = generate_plot(db, intent.start_date, intent.end_date, intent.metric, intent.tenor, intent.tenors, intent.highlight_date)
                    await update.message.reply_photo(photo=io.BytesIO(png))
            
            else:
                # Range without aggregation - return individual rows
                params = [intent.start_date.isoformat(), intent.end_date.isoformat()]
                where = 'obs_date BETWEEN ? AND ?'
                if intent.tenors and len(intent.tenors) > 1:
                    placeholders = ','.join(['?'] * len(intent.tenors))
                    where += f' AND tenor IN ({placeholders})'
                    params.extend(intent.tenors)
                elif intent.tenor:
                    where += ' AND tenor = ?'
                    params.append(intent.tenor)
                if intent.series:
                    where += ' AND series = ?'
                    params.append(intent.series)
                
                # Fetch without a hard limit so data_points reflects the full window
                rows = db.con.execute(
                    f'SELECT series, tenor, obs_date, price, "yield" FROM ts WHERE {where} ORDER BY obs_date ASC, series',
                    params
                ).fetchall()
                
                rows_list = [
                    dict(
                        series=r[0],
                        tenor=r[1],
                        date=r[2].isoformat(),
                        price=round(r[3], 2) if r[3] is not None else None,
                        **{'yield': round(r[4], 2) if r[4] is not None else None}
                    )
                    for r in rows
                ]
                
                # If plot is requested, route through FastAPI for consistent Economist styling and AI analysis
                if wants_plot:
                    if len(rows_list) == 0:
                        await update.message.reply_text(
                            f"❌ No data found for {intent.tenor or 'bonds'} in this period.",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        summary_text = format_range_summary_text(
                            rows_list,
                            start_date=intent.start_date,
                            end_date=intent.end_date,
                            metric=intent.metric if hasattr(intent, 'metric') else 'yield'
                        )
                        # Route through FastAPI /chat endpoint for Economist style + AI analysis
                        try:
                            import httpx
                            async with httpx.AsyncClient(timeout=60.0) as client:
                                payload = {"q": user_query, "plot": True, "persona": "kei"}
                                resp = await client.post(f"{API_BASE_URL}/chat", json=payload)
                                if resp.status_code == 200:
                                    data = resp.json()
                                    if data.get("image"):
                                        image_bytes = base64.b64decode(data["image"])
                                        await update.message.reply_photo(photo=image_bytes)
                                    # Send quant summary tailored for range queries
                                    if summary_text:
                                        await update.message.reply_text(summary_text)
                                else:
                                    error_detail = f"Status {resp.status_code}"
                                    try:
                                        error_detail += f": {resp.json().get('detail', '')}"
                                    except:
                                        pass
                                    logger.error(f"FastAPI /chat error: {error_detail}")
                                    await update.message.reply_text(f"⚠️ Error from API: {resp.status_code}")
                        except Exception as e:
                            logger.error(f"Error calling /chat endpoint for '{user_query}': {type(e).__name__}: {e}", exc_info=True)
                            await update.message.reply_text("⚠️ Error generating plot. Please try again.")
                else:
                    # No plot requested - show data rows with statistics
                    # Calculate statistics
                    # Determine metrics requested (support combined yield + price)
                    metrics_requested = []
                    lower_q = user_query.lower()
                    if 'yield' in lower_q:
                        metrics_requested.append('yield')
                    if 'price' in lower_q:
                        metrics_requested.append('price')
                    if not metrics_requested:
                        metrics_requested.append(intent.metric if hasattr(intent, 'metric') else 'yield')
                    # Deduplicate while preserving order
                    seen = set()
                    metrics_requested = [m for m in metrics_requested if not (m in seen or seen.add(m))]

                    response_text = f"📊 Found {len(rows_list)} records\n"
                    response_text += f"Period: {intent.start_date} → {intent.end_date}\n"

                    def _format_tenor_display(label: str) -> str:
                        label = str(label or '').replace('_', ' ').strip()
                        # Normalize patterns like '5year', '5 year', '5Yyear' to '5Y'
                        label = re.sub(r'(?i)(\b\d+)\s*y(?:ear)?\b', r'\1Y', label)
                        label = label.replace('Yyear', 'Y').replace('yyear', 'Y')
                        return label
                    
                    # Calculate per-tenor summaries for later use
                    import statistics
                    tenors = sorted(set(r.get('tenor') for r in rows_list))
                    summary_stats = {}  # {metric: {tenor: {count, min, max, avg, std}}}
                    for m in metrics_requested:
                        metric_values = [r.get(m) for r in rows_list if r.get(m) is not None]
                        if not metric_values:
                            continue
                        per_tenor = {}
                        for row in rows_list:
                            tenor = row.get('tenor') or 'all'
                            val = row.get(m)
                            if val is None:
                                continue
                            per_tenor.setdefault(tenor, []).append(val)
                        
                        summary_stats[m] = {}
                        for tenor, vals in per_tenor.items():
                            if vals:
                                summary_stats[m][tenor] = {
                                    'count': len(vals),
                                    'min': min(vals),
                                    'max': max(vals),
                                    'avg': statistics.mean(vals),
                                    'std': statistics.stdev(vals) if len(vals) > 1 else 0
                                }
                    
                    # Add blank line before tables
                    response_text += "\n"
                    
                    # Show all rows (or split into messages if too many)
                    if len(metrics_requested) == 1:
                        formatted_rows = format_rows_for_telegram(rows_list, include_date=True, metric=metrics_requested[0], economist_style=True, summary_stats=summary_stats)
                    else:
                        if len(tenors) == 1:
                            formatted_rows = format_rows_for_telegram(rows_list, include_date=True, metric=metrics_requested[0], metrics=metrics_requested, economist_style=True, summary_stats=summary_stats)
                        else:
                            tables = []
                            for m in metrics_requested:
                                tables.append(f"{m.capitalize()}\n" + format_rows_for_telegram(rows_list, include_date=True, metric=m, economist_style=True, summary_stats=summary_stats))
                            formatted_rows = "\n\n".join(tables)
                    
                    if len(formatted_rows) > 3500:  # Telegram message limit is 4096, leave buffer
                        # Send in multiple messages if too long
                        response_text += formatted_rows[:3500]
                        rendered = convert_markdown_code_fences_to_html(response_text)
                        await update.message.reply_text(rendered, parse_mode=ParseMode.HTML)
                        response_text = formatted_rows[3500:]
                        rendered = convert_markdown_code_fences_to_html(response_text)
                        await update.message.reply_text(rendered, parse_mode=ParseMode.HTML)
                    else:
                        response_text += formatted_rows
                        rendered = convert_markdown_code_fences_to_html(response_text)
                        await update.message.reply_text(rendered, parse_mode=ParseMode.HTML)
                
                return
        
        else:
            await update.message.reply_text(
                "❌ Sorry, I couldn't understand that query. Try `/examples` for sample queries.",
                parse_mode=ParseMode.MARKDOWN
            )
    
    except Exception as e:
        error_text = f"❌ *Error:* {str(e)}\n\nTry `/examples` for valid query formats."
        await update.message.reply_text(error_text, parse_mode=ParseMode.MARKDOWN)


def generate_plot(db, start_date, end_date, metric='yield', tenor=None, tenors=None, highlight_date=None):
    """Generate a plot and return PNG bytes. Supports single tenor or multiple tenors."""
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    try:
        import seaborn as sns
        has_seaborn = True
    except:
        has_seaborn = False
    
    params = [start_date.isoformat(), end_date.isoformat()]
    q = 'SELECT obs_date, series, tenor, price, "yield" FROM ts WHERE obs_date BETWEEN ? AND ?'
    
    # Handle multi-tenor or single tenor
    if tenors and len(tenors) > 1:
        # Multi-tenor query
        placeholders = ','.join(['?'] * len(tenors))
        q += f' AND tenor IN ({placeholders})'
        params.extend(tenors)
    elif tenor:
        # Single tenor (backward compatibility)
        q += ' AND tenor = ?'
        params.append(tenor)
    
    q += ' ORDER BY obs_date'
    df = db.con.execute(q, params).fetchdf()
    
    if df.empty:
        plt.figure(figsize=(4, 2))
        plt.text(0.5, 0.5, 'No data', ha='center', va='center')
        buf = io.BytesIO()
        plt.axis('off')
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close()
        buf.seek(0)
        return buf.read()
    
    df['obs_date'] = pd.to_datetime(df['obs_date'])
    
    # Determine if multi-tenor plot
    is_multi_tenor = tenors and len(tenors) > 1
    
    # Fill missing dates and aggregate
    all_dates = pd.date_range(start_date, end_date, freq='D')
    
    if is_multi_tenor:
        # Multi-tenor: group by tenor and date, keep separate lines
        filled = []
        for (s, t), g in df.groupby(['series', 'tenor']):
            g2 = g.set_index('obs_date').reindex(all_dates)
            g2['series'] = s
            g2['tenor'] = t
            g2[['price', 'yield']] = g2[['price', 'yield']].ffill()
            filled.append(g2.reset_index().rename(columns={'index': 'obs_date'}))
        filled = pd.concat(filled, ignore_index=True)
        # Group by tenor and date (average across series if multiple)
        daily = filled.groupby(['obs_date', 'tenor'])[metric].mean().reset_index()
        # Format tenor labels nicely for display
        daily['tenor_label'] = daily['tenor'].str.replace('_', ' ')
    else:
        # Single tenor: original aggregation logic
        filled = []
        for s, g in df.groupby('series'):
            g2 = g.set_index('obs_date').reindex(all_dates)
            g2['series'] = s
            g2[['price', 'yield']] = g2[['price', 'yield']].ffill()
            filled.append(g2.reset_index().rename(columns={'index': 'obs_date'}))
        filled = pd.concat(filled, ignore_index=True)
        daily = filled.groupby('obs_date')[metric].mean().reset_index()
    
    # Format display
    def format_date(d):
        return d.strftime('%-d %b %Y') if hasattr(d, 'strftime') else str(d)
    
    if is_multi_tenor:
        display_tenor = ', '.join([t.replace('_', ' ') for t in tenors])
    else:
        display_tenor = tenor.replace('_', ' ') if tenor else ''
    
    title_start = format_date(start_date)
    title_end = format_date(end_date)
    
    # Plot
    buf = io.BytesIO()
    
    # Convert highlight_date to pandas Timestamp if provided
    highlight_ts = None
    if highlight_date:
        # Always convert to pd.Timestamp to ensure compatibility with DatetimeArray operations
        highlight_ts = pd.Timestamp(highlight_date)

    # Axis labels and title strings
    metric_label = metric.capitalize()
    y_label = 'Yield (%)' if metric == 'yield' else metric_label
    title_top = f"{metric_label} {display_tenor}".strip()
    title_bottom = f"{title_start} to {title_end}"
    
    if has_seaborn:
        # Use a clean Economist-like look with slightly larger fonts
        sns.set_theme(style='whitegrid', context='talk', palette=ECONOMIST_PALETTE)
        fig, ax = plt.subplots(figsize=(12, 7))
        apply_economist_style(fig, ax)

        if is_multi_tenor:
            # Ensure stable color mapping per tenor
            tenor_order = sorted(daily['tenor_label'].unique())
            palette_map = {label: ECONOMIST_PALETTE[i % len(ECONOMIST_PALETTE)] for i, label in enumerate(tenor_order)}
            sns.lineplot(
                data=daily,
                x='obs_date',
                y=metric,
                hue='tenor_label',
                hue_order=tenor_order,
                linewidth=2.25,
                ax=ax,
                errorbar=None,
                palette=palette_map,
                legend='full'
            )
            ax.legend(title=None, fontsize=12, loc='upper right', frameon=False)
        else:
            sns.lineplot(data=daily, x='obs_date', y=metric, linewidth=2.25, ax=ax, color=ECONOMIST_COLORS['red'])
            leg = ax.get_legend()
            if leg:
                leg.remove()

        # Add highlight marker if date is in the data
        if highlight_ts is not None:
            if is_multi_tenor:
                highlight_rows = daily[daily['obs_date'] == highlight_ts]
                if not highlight_rows.empty:
                    for _, row in highlight_rows.iterrows():
                        ax.plot(highlight_ts, row[metric], 'k*', markersize=14, zorder=5)
                    ax.text(highlight_ts, highlight_rows[metric].mean(), f'  📍 {format_date(highlight_ts)}', fontsize=10, va='center')
            else:
                highlight_row = daily[daily['obs_date'] == highlight_ts]
                if not highlight_row.empty:
                    y_val = highlight_row[metric].iloc[0]
                    ax.plot(highlight_ts, y_val, 'k*', markersize=16, zorder=5)
                else:
                    daily['date_diff'] = (daily['obs_date'] - highlight_ts).abs()
                    closest = daily.loc[daily['date_diff'].idxmin()]
                    y_val = closest[metric]
                    ax.plot(closest['obs_date'], y_val, 'k*', markersize=16, zorder=5)

        ax.set_title(f"{title_top}\n{title_bottom}", fontsize=13, pad=14, loc='left', color=ECONOMIST_COLORS['black'])
        ax.set_xlabel('', fontsize=12)
        ax.set_ylabel(y_label, fontsize=12)

        from matplotlib.dates import DateFormatter
        date_formatter = DateFormatter('%-d %b\n%Y')
        ax.xaxis.set_major_formatter(date_formatter)
        plt.setp(ax.get_xticklabels(), rotation=0, ha='center')
        # Grid already configured by apply_economist_style() - no override needed
    else:
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.plot(daily['obs_date'], daily[metric], linewidth=2)
        
        # Add highlight marker if date is in the data
        if highlight_ts is not None:
            highlight_row = daily[daily['obs_date'] == highlight_ts]
            if not highlight_row.empty:
                y_val = highlight_row[metric].iloc[0]
                ax.plot(highlight_ts, y_val, 'r*', markersize=20,
                       label=f'📍 {format_date(highlight_ts)}', zorder=5)
                ax.legend(fontsize=10)
            else:
                # If exact date not found, find closest date
                daily['date_diff'] = (daily['obs_date'] - highlight_ts).abs()
                closest = daily.loc[daily['date_diff'].idxmin()]
                y_val = closest[metric]
                ax.plot(closest['obs_date'], y_val, 'r*', markersize=20,
                       label=f'📍 {format_date(closest["obs_date"])} (closest)', zorder=5)
                ax.legend(fontsize=10)
        
        ax.set_title(f"{title_top}\n{title_bottom}", fontsize=13, pad=14, loc='left', color=ECONOMIST_COLORS['black'])
        ax.set_xlabel('', fontsize=12)
        ax.set_ylabel(y_label, fontsize=12)
        fig.autofmt_xdate()
    
    add_economist_caption(fig)
    
    plt.savefig(buf, format='png', dpi=150, facecolor='white')
    plt.close()
    buf.seek(0)
    return buf.read()



async def activity_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /activity command - show bot usage statistics for authorized users only."""
    user_id = update.message.from_user.id
    
    # Restrict to admin/power users - check if admin ID is configured
    admin_id = os.getenv("ADMIN_USER_ID")
    is_admin = admin_id and user_id == int(admin_id)
    
    if not is_admin:
        await update.message.reply_text(
            "⛔ Activity monitoring is restricted to admin users only."
        )
        logger.warning("Unauthorized activity check attempt from user_id=%s", user_id)
        return
    
    # Import and run activity monitor
    try:
        from activity_monitor import ActivityMonitor
        
        monitor = ActivityMonitor()
        health = monitor.health_check()
        query_stats = monitor.query_stats(hours=24)
        top_users = monitor.top_users(hours=24, limit=3)
        errors = monitor.error_summary(hours=24, limit=3)
        persona_usage = monitor.persona_usage(hours=24)
        
        # Format response
        msg = "<b>📊 PerisAI Bot Activity (Last 24h)</b>\n\n"
        
        # Health metrics
        h = health['last_24h']
        msg += f"<b>Health Status</b>\n"
        msg += f"  Queries: {h['total_queries']} ({h['success_rate']:.0f}% success)\n"
        msg += f"  Latency: {h['avg_latency_ms']} ms\n"
        msg += f"  Users: {h['unique_users']} (weekly: {health['last_7d']['unique_users']})\n\n"
        
        # Query breakdown
        if query_stats:
            msg += "<b>Query Types</b>\n"
            for qtype, stats in list(query_stats.items())[:5]:
                msg += f"  {qtype}: {stats['count']} ({stats['success_rate']:.0f}%)\n"
            msg += "\n"
        
        # Persona usage
        if persona_usage:
            msg += "<b>Persona Usage</b>\n"
            total_persona_queries = sum(p['count'] for p in persona_usage.values())
            for persona, stats in sorted(persona_usage.items(), key=lambda x: x[1]['count'], reverse=True):
                pct = (stats['count'] / total_persona_queries * 100) if total_persona_queries > 0 else 0
                msg += f"  /{persona}: {stats['count']} queries ({pct:.0f}%, {stats['success_rate']:.0f}% success)\n"
            msg += "\n"
        
        # Top users
        if top_users:
            msg += "<b>Top Users</b>\n"
            for u in top_users:
                msg += f"  @{u['username']}: {u['query_count']} queries ({u['success_rate']:.0f}%)\n"
            msg += "\n"
        
        # Errors
        if errors:
            msg += "<b>Recent Errors</b>\n"
            for e in errors:
                error_txt = e['error'][:40] if e['error'] else 'Unknown'
                msg += f"  {error_txt}: {e['count']}x\n"
        else:
            msg += "<b>Recent Errors</b>\n  ✅ None\n"
        
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        logger.error(f"Error generating activity report: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ Error generating activity report: {str(e)}"
        )


def create_telegram_app(token: str) -> Application:
    """Create and configure the Telegram application with extended HTTPX timeouts."""
    from telegram.request import HTTPXRequest
    
    # Increase HTTPX timeouts to handle slow Telegram API or egress delays on Render
    # Default timeouts are ~5s, which is too short for transcontinental API calls
    request = HTTPXRequest(
        connect_timeout=15.0,    # Time to establish connection
        read_timeout=30.0,       # Time to read response (critical for slow API)
        write_timeout=10.0,      # Time to send request
        pool_timeout=15.0        # Time to get a connection from pool
    )
    
    application = Application.builder().token(token).request(request).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("examples", examples_command))
    application.add_handler(CommandHandler("check", check_command))
    application.add_handler(CommandHandler("activity", activity_command))
    # Personas
    application.add_handler(CommandHandler("kei", kei_command))
    application.add_handler(CommandHandler("kin", kin_command))
    application.add_handler(CommandHandler("both", both_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    return application
