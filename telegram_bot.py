"""Telegram Bot Integration for Bond Price & Yield Chatbot
Handles incoming messages from Telegram and formats responses.
"""
import os
import io
import base64
import logging
import time
from typing import Optional
from openai import AsyncOpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
import html as html_module

# Import bond query logic
import importlib.util
from pathlib import Path
_mod_path = Path(__file__).with_name("20251223_priceyield.py")
spec = importlib.util.spec_from_file_location("priceyield_mod", str(_mod_path))
priceyield_mod = importlib.util.module_from_spec(spec)
import sys
sys.modules["priceyield_mod"] = priceyield_mod
spec.loader.exec_module(priceyield_mod)
parse_intent = priceyield_mod.parse_intent
BondDB = priceyield_mod.BondDB
AuctionDB = priceyield_mod.AuctionDB

# Import metrics
from metrics import metrics


# Economist styling for plots
ECONOMIST_COLORS = {
    'red': '#E3120B',
    'blue': '#0C6291',
    'teal': '#00847E',
    'gray': '#8C8C8C',
    'bg_gray': '#F0F0F0',
    'black': '#1A1A1A',
}

ECONOMIST_PALETTE = [
    ECONOMIST_COLORS['red'],
    ECONOMIST_COLORS['blue'],
    ECONOMIST_COLORS['teal'],
    ECONOMIST_COLORS['gray'],
]

def apply_economist_style(fig, ax):
    """Apply The Economist styling to a matplotlib figure."""
    ax.set_facecolor(ECONOMIST_COLORS['bg_gray'])
    fig.patch.set_facecolor('white')
    
    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    # Style bottom spine
    ax.spines['bottom'].set_color(ECONOMIST_COLORS['black'])
    ax.spines['bottom'].set_linewidth(0.5)
    
    # Horizontal gridlines only
    ax.yaxis.grid(True, color='white', linewidth=1.2, linestyle='-')
    ax.set_axisbelow(True)
    
    # Tick styling
    ax.tick_params(axis='both', which='both', length=0, labelsize=9, colors=ECONOMIST_COLORS['gray'])
    ax.xaxis.label.set_color(ECONOMIST_COLORS['gray'])
    ax.yaxis.label.set_color(ECONOMIST_COLORS['gray'])
    ax.title.set_color(ECONOMIST_COLORS['black'])

# Cache DB instances
_db_cache = {}

# OpenAI client for persona answers
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
_openai_client: Optional[AsyncOpenAI] = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
logger = logging.getLogger("telegram_bot")

# Perplexity API (HTTPX-based)
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "sonar-pro")

# API base URL for plot requests (defaults to localhost with PORT from env, or 8000)
PORT = os.getenv("PORT", "8000")
API_BASE_URL = os.getenv("API_BASE_URL", f"http://127.0.0.1:{PORT}")

# Access control: allowed user IDs (comma-separated in env var or hardcoded)
ALLOWED_USER_IDS_STR = os.getenv("ALLOWED_USER_IDS", "")
if ALLOWED_USER_IDS_STR:
    ALLOWED_USER_IDS = set(int(uid.strip()) for uid in ALLOWED_USER_IDS_STR.split(",") if uid.strip())
else:
    ALLOWED_USER_IDS = set()  # Empty = allow all users

def is_user_authorized(user_id: int) -> bool:
    """Check if user is authorized to use the bot."""
    if not ALLOWED_USER_IDS:  # Empty list means no restriction
        return True
    return user_id in ALLOWED_USER_IDS


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


def format_rows_for_telegram(rows, include_date=False):
    """Format data rows for Telegram message (monospace style)."""
    if not rows:
        return "No data found."
    
    def format_date_display(date_str):
        """Convert ISO date string to 'dd mmm yyyy' format."""
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime('%d %b %Y')
        except:
            return date_str
    
    lines = []
    for row in rows:
        if include_date:
            # RANGE query with date
            formatted_date = format_date_display(row['date'])
            lines.append(
                f"🔹 {row['series']} | {row['tenor'].replace('_', ' ')} | {formatted_date}\n"
                f"   Price: {row['price']:.2f} | Yield: {row.get('yield', 0):.2f}%"
            )
        else:
            # POINT query without date
            lines.append(
                f"🔹 {row['series']} | {row['tenor'].replace('_', ' ')}\n"
                f"   Price: {row['price']:.2f} | Yield: {row.get('yield', 0):.2f}%"
            )
    return "\n\n".join(lines)

def format_auction_rows_for_telegram(rows):
    """Format auction forecast rows for Telegram message."""
    if not rows:
        return "No forecast data found for the specified period."
    
    from datetime import datetime
    lines = []
    for row in rows:
        try:
            dt = datetime.fromisoformat(str(row['date']))
            date_str = dt.strftime('%b %Y')
        except:
            date_str = str(row['date'])
        
        lines.append(
            f"📊 <b>{date_str}</b>\n"
            f"   Incoming: Rp {row['incoming_billions']:.2f}T | Awarded: Rp {row['awarded_billions']:.2f}T\n"
            f"   Bid-to-Cover: {row['bid_to_cover']:.2f}x | Series: {row['number_series']}\n"
            f"   BI Rate: {row['bi_rate']:.2f}% | Inflation: {row['inflation_rate']:.2f}%"
        )
    return "\n\n".join(lines)


def summarize_intent_result(intent, rows_list):
    """Produce a short text summary of computed results for LLM context."""
    if not rows_list:
        return "No matching data found in the requested period."
    
    # Handle auction forecasts
    if intent.type == 'AUCTION_FORECAST':
        parts = []
        for row in rows_list:
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(str(row['date']))
                date_str = dt.strftime('%B %Y')
            except:
                date_str = str(row['date'])
        
            parts.append(
                f"{date_str}: Incoming demand Rp {row['incoming_billions']:.2f} trillion, "
                f"Awarded Rp {row['awarded_billions']:.2f} trillion, "
                f"Bid-to-cover {row['bid_to_cover']:.2f}x, "
                f"{row['number_series']} series, "
                f"BI rate {row['bi_rate']:.2f}%, "
                f"Inflation {row['inflation_rate']:.2f}%"
            )
    
        summary = "\n".join(parts)
    
        # Add statistics if multiple months
        if len(rows_list) > 1:
            incoming_vals = [r['incoming_billions'] for r in rows_list]
            awarded_vals = [r['awarded_billions'] for r in rows_list]
            btc_vals = [r['bid_to_cover'] for r in rows_list]
        
            import statistics
            summary += f"\n\nStatistics ({len(rows_list)} months):\n"
            summary += f"Incoming: avg Rp {statistics.mean(incoming_vals):.2f}T, range Rp {min(incoming_vals):.2f}T - Rp {max(incoming_vals):.2f}T\n"
            summary += f"Awarded: avg Rp {statistics.mean(awarded_vals):.2f}T, range Rp {min(awarded_vals):.2f}T - Rp {max(awarded_vals):.2f}T\n"
            summary += f"Bid-to-cover: avg {statistics.mean(btc_vals):.2f}x, range {min(btc_vals):.2f}x - {max(btc_vals):.2f}x"
    
        return summary
    
    parts = []
    
    # For range queries with statistics, include all rows with stats
    if intent.type == 'AGG_RANGE' or (intent.type == 'RANGE' and len(rows_list) > 1):
        # Compute statistics for the metric
        metric_values = []
        for r in rows_list:
            val = r.get(intent.metric if hasattr(intent, 'metric') and intent.metric else 'yield')
            if val is not None:
                try:
                    metric_values.append(float(val))
                except (ValueError, TypeError):
                    pass
        
        if metric_values:
            import statistics as stats_module
            metric_name = intent.metric if hasattr(intent, 'metric') and intent.metric else 'yield'
            min_val = min(metric_values)
            max_val = max(metric_values)
            avg_val = stats_module.mean(metric_values)
            std_val = stats_module.stdev(metric_values) if len(metric_values) > 1 else 0
            
            parts.append(
                f"Period: {intent.start_date} to {intent.end_date}\n"
                f"Records found: {len(rows_list)}\n"
                f"Statistics ({metric_name}): Min={min_val:.2f}, Max={max_val:.2f}, Avg={avg_val:.2f}, StdDev={std_val:.2f}\n"
                f"Data rows:"
            )
            for r in rows_list:
                if 'date' in r:
                    parts.append(
                        f"  {r['series']} | {r['tenor'].replace('_', ' ')} | {r['date']} | "
                        f"Price {r.get('price', 'N/A')} | Yield {r.get('yield', 'N/A')}"
                    )
        else:
            # Fallback: show first 3 rows
            for r in rows_list[:3]:
                parts.append(
                    f"Series {r['series']} | Tenor {r['tenor'].replace('_',' ')} | "
                    f"Price {r.get('price','N/A')} | Yield {r.get('yield','N/A')}"
                    + (f" | Date {r.get('date')}" if 'date' in r else "")
                )
    else:
        # For point queries or small result sets, show all or up to 5 rows
        for r in rows_list[:5]:
            parts.append(
                f"Series {r['series']} | Tenor {r['tenor'].replace('_',' ')} | "
                f"Price {r.get('price','N/A')} | Yield {r.get('yield','N/A')}"
                + (f" | Date {r.get('date')}" if 'date' in r else "")
            )
    
    header = f"Computed rows ({len(rows_list)} total):"
    return header + "\n" + "\n".join(parts)


async def try_compute_bond_summary(question: str) -> Optional[str]:
    """Best-effort: parse question and compute a summary for LLM context."""
    try:
        intent = parse_intent(question)
        rows_list = []
        
        # Handle auction forecasts
        if intent.type == 'AUCTION_FORECAST':
            auction_db = get_auction_db()
            rows_list = auction_db.query_forecast(intent)
            if rows_list:
                return summarize_intent_result(intent, rows_list)
            return None
        
        # Handle bond data queries
        db = get_db()

        if intent.type == 'POINT':
            d = intent.point_date
            params = [d.isoformat()]
            where = 'obs_date = ?'
            if intent.tenor:
                where += ' AND tenor = ?'
                params.append(intent.tenor)
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
                # Support multiple tenors: use intent.tenors if present, otherwise intent.tenor
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
    
    # Determine if this is a bond/data query or general knowledge question
    is_data_query = data_summary is not None
    
    if is_data_query:
        # For bond data queries, use strict HL-CU format (unless user requests otherwise)
        system_prompt = (
            "You are Kei.\n"
            "Profile: CFA charterholder, PhD (MIT). World-class data scientist with deep expertise in mathematics, statistics, econometrics, and forecasting. Because you are a CFA/MIT quant, lead with numbers, ranges/uncertainty, and concise math; avoid narrative or storytelling. Briefly name the forecasting method and key drivers you relied on when citing auction demand forecasts.\n\n"

            "LANGUAGE: Default to English. If the user explicitly asks in Indonesian or requests Indonesian response, respond entirely in Indonesian.\n\n"

            "STYLE RULE — HEADLINE-LED CORPORATE UPDATE (HL-CU)\n"
            "Default format: Exactly one title line (� TICKER: Key Metric / Event +X%; max 14 words), then blank line, then exactly 3 paragraphs (max 2 sentences each, ≤152 words total). Plain text only; no markdown, no bullets.\n"
            "IMPORTANT: If the user explicitly requests bullet points, a bulleted list, plain English, or any other specific format, ALWAYS honor that request and override the HL-CU format.\n"
            "Body (Kei): Emphasize factual reporting; no valuation, recommendation, or opinion. Use contrasts where relevant (MoM vs YoY, trend vs level). Forward-looking statements must be attributed to management and framed conditionally.\n"
            "Sources: Include one source line in brackets only if explicitly provided; otherwise omit entirely.\n"
            f"Signature: blank line, then '________', then blank line, then '{'Kei & Kin | Data → Insight' if dual_mode else 'Kei | Quant Research'}'.\n"
            "Prohibitions: No follow-up questions. No speculation or narrative flourish. Do not add or infer data not explicitly provided.\n"
            "Objective: Produce a scannable, publication-ready response that delivers the key market signal clearly.\n\n"

            "Data access:\n- Indonesian government bond prices and yields (2023-2025): FR95-FR104 series (5Y/10Y tenors). FR stands for Fixing Rate series, issued by Indonesia's government, NOT French government bonds.\n- Auction demand forecasts for Indonesian bonds through 2026 (incoming bids, awarded amounts, bid-to-cover ratios; generated using ensemble ML methods combining XGBoost, Random Forest, and time-series models with macroeconomic features: BI rate, inflation, industrial production, JKSE index, and FX rates)\n- Indonesian macroeconomic indicators (BI rate, inflation, etc.)\n"
        )
    else:
        # For general knowledge, use a more flexible prompt
        system_prompt = (
            "You are Kei, a world-class quant and data scientist.\n"
            "LANGUAGE: Default to English. If the user explicitly asks in Indonesian or requests Indonesian response, respond entirely in Indonesian.\n"
            "Explain economic and financial concepts clearly using established frameworks and first principles.\n"
            "If specific data is unavailable, acknowledge limits but still provide a concise, plain-text explanation.\n"
            "No special formatting is required; avoid leaving the response empty.\n"
        )
    
    # Retry logic: up to 3 attempts for empty responses
    max_retries = 3
    for attempt in range(max_retries):
        messages = [
            {"role": "system", "content": system_prompt},
        ]

        if is_data_query:
            messages.append({"role": "system", "content": "Constraint: no live news access; information may be outdated."})
            messages.append({
                "role": "system",
                "content": f"Precomputed quantitative inputs:\n{data_summary}"
            })
        else:
            messages.append({
                "role": "system",
                "content": "You have no access to live data. Provide analysis based on established economic frameworks and available public knowledge."
            })

        messages.append({"role": "user", "content": question})

        try:
            # Use lower temperature for data queries (stricter), higher for general knowledge (more flexible)
            temperature = 0.3 if is_data_query else 0.7
            # Increase token budget for general knowledge that may need more explanation
            max_tokens = 220 if is_data_query else 300
            
            resp = await _openai_client.chat.completions.create(
                model="gpt-5.2",
                messages=messages,
                max_completion_tokens=max_tokens,
                temperature=temperature,
            )
            content = resp.choices[0].message.content.strip() if resp.choices else ""
            
            if content:
                # Format general knowledge responses with HL-CU style if possible
                if not is_data_query:
                    # Ensure it has a headline
                    if not content.startswith("📰"):
                        content = f"📰 {content}"
                return content
            
            # Log retry attempt
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
    
    # Final minimal fallback attempt to avoid empty responses
    try:
        if is_data_query:
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
            max_completion_tokens=240,
            temperature=0.6,
        )
        content2 = resp2.choices[0].message.content.strip() if resp2.choices else ""
        if content2:
            return content2
    except Exception as e:
        logger.warning(f"Kei minimal fallback failed: {e}")

    # Fallback message if all attempts exhausted
    if is_data_query:
        return "⚠️ Kei could not analyze the bond data. Please try again or rephrase your query."
    else:
        # Check if question seems to be asking for data/forecast
        lower_q = question.lower()
        data_keywords = ['forecast', 'auction', 'demand', 'yield', 'price', 'bond', 'series', 'tenor']
        if any(keyword in lower_q for keyword in data_keywords):
            return (
                "⚠️ No dataset available for this query.\n\n"
                "Dataset coverage:\n"
                "• Bond prices/yields: 2023-2025 (FR95-FR104, 5Y/10Y tenors)\n"
                "• Auction forecasts: Dec 2025 - Dec 2026\n\n"
                "For data outside this range or general economic questions, try /kin instead."
            )
        return "⚠️ Kei is currently unable to provide a response. Please try rephrasing your question."


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
            "Default format: Exactly one title line (🌍 TICKER: Key Metric / Event +X%; max 14 words), then blank line, then exactly 3 paragraphs (max 2 sentences each, ≤214 words total). Plain text only; absolutely NO markdown formatting (no **, no *, no _), no bullets.\n"
            "IMPORTANT: If the user explicitly requests bullet points, a bulleted list, plain English, or any other specific format, ALWAYS honor that request and override the HL-CU format.\n"
            "Body (Kin): Emphasize factual reporting; no valuation, recommendation, or opinion. Use contrasts where relevant (MoM vs YoY, trend vs level). Forward-looking statements must be attributed to management and framed conditionally. Write numbers and emphasis in plain text without any markdown bold or italics.\n"
            "Sources: If any sources are referenced, add one line at the end in brackets with names only (no links), format: [Sources: Source A; Source B]. If none, omit the line entirely.\n"
            f"Signature: blank line, then '________', then blank line, then '{'Kei & Kin | Data → Insight' if dual_mode else 'Kin | Economics & Strategy'}'.\n"
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
            "Default format: Exactly one title line (🌍 TICKER: Key Metric / Event +X%; max 14 words), then blank line, then exactly 3 paragraphs (max 2 sentences each, ≤214 words total). Plain text only; absolutely NO markdown formatting (no **, no *, no _), no bullets.\n"
            "IMPORTANT: If the user explicitly requests bullet points, a bulleted list, plain English, or any other specific format, ALWAYS honor that request and override the HL-CU format.\n"
            "Body (Kin): Emphasize factual reporting; no valuation, recommendation, or opinion. Use contrasts where relevant (MoM vs YoY, trend vs level). Forward-looking statements must be attributed to management and framed conditionally. Write numbers and emphasis in plain text without any markdown bold or italics.\n"
            "Sources: If any sources are referenced, add one line at the end in brackets with names only (no links), format: [Sources: Source A; Source B]. If none, omit the line entirely.\n"
            f"Signature: blank line, then '________', then blank line, then '{'Kei & Kin | Data → Insight' if dual_mode else 'Kin | Economics & Strategy'}'.\n"
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

        return (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        ) or "(empty response)"

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
        "🏛️ <b>PerisAI</b>\n\n"
        "Pengelolaan Pembiayaan dan Risiko Berbasis AI\n"
        "<i>©arifpras</i>\n\n"
        "─────────────────────────────\n\n"
        "<b>Commands</b>\n"
        "/kei — Quant analyst (💹 data)\n"
        "/kin — Macro strategist (🌍 context)\n"
        "/both — Combined (⚡ insight)\n\n"
        "<b>Examples</b>\n"
        "• Yield 5 and 10 years 2025\n"
        "• Plot 10 year 2024\n"
        "• Auction demand 2026\n"
        "• Average yield 2024 vs 2025\n\n"
        "Type /examples for more\n"
        "Type /start anytime"
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
        "<b>🎯 Single Tenor (Data Queries):</b>\n"
        "/kei yield 10 year 2025\n"
        "/kei 5 year Q1 2025\n"
        "/kei price 10 year 6 Dec 2024\n"
        "/kin auction demand January 2026\n\n"
        "<b>🔀 Multi-Tenor Comparison:</b>\n"
        "/kei yield 5 and 10 years 2024\n"
        "/kin compare 5 year and 10 year 2025\n"
        "/both 5 and 10 year average 2024\n\n"
        "<b>📊 Charts & Visualizations (Command-Based, with AI Analysis):</b>\n"
        "/kei plot yield 10 year 2025 → Economist-style chart + Quant insights\n"
        "/kei chart 5 and 10 years 2024 → Multi-tenor plot + Analysis\n"
        "/kin show price 5 year 2023 → Chart + Macro context\n"
        "/both compare 5 and 10 years 2024 → Chart + Dual analysis\n\n"
        "<b>📈 Plain Message Plots (No Command Prefix):</b>\n"
        "plot 5 year 2025 → Economist-style chart\n"
        "chart 10 year 2024 → Multi-tenor plot\n"
        "show 5 and 10 years 2023 → Comparison chart\n"
        "visualize yield 2024 → Range plot\n\n"
        "<b>📈 Aggregates & Statistics:</b>\n"
        "/kei average yield 10 year 2025\n"
        "/kei max yield 2024\n"
        "/kin min price 2023\n\n"
        "<b>🏛️ Auction Forecasts:</b>\n"
        "/kei auction demand January 2026\n"
        "/kei incoming bids 2026\n"
        "/kei awarded amount Q1 2026\n"
        "/kei bid to cover February 2026\n\n"
        "<b>📅 Date Formats (all work):</b>\n"
        "Year: 2024 | Quarter: Q1 2024 | Month: May 2024 | Date: 6 Dec 2024 | ISO: 2024-12-06\n\n"
        "─────────────────────────────────────────\n\n"
        "<b>👥 Personas</b>\n\n"
        "<b>💹 /kei — Quant Analyst</b>\n"
        "• CFA charterholder, PhD (MIT)\n"
        "• Powered by: OpenAI GPT-5.2\n"
        "• Style: HL-CU format (headline + 3 paragraphs, ≤152 words)\n"
        "• Strengths: Bond data analysis, quantitative rigor, factual reporting\n"
        "• Charts: Economist-style plots with data-driven insights\n"
        "• Signature: 💹 <b>Kei | Quant Research</b>\n\n"
        "<b>🌍 /kin — Macro Strategist</b>\n"
        "• CFA charterholder, PhD (Harvard)\n"
        "• Powered by: Perplexity Sonar-Pro (with web search)\n"
        "• Style: HL-CU format (headline + 3 paragraphs, ≤214 words)\n"
        "• Strengths: Macro context, policy analysis, market implications\n"
        "• Charts: Economist-style plots with strategic interpretation\n"
        "• Signature: 🌍 <b>Kin | Economics & Strategy</b>\n\n"
        "<b>⚡ /both — Chain Analysis</b>\n"
        "• Kei (data) → Kin (interpretation)\n"
        "• Best for: Comprehensive analysis with quantitative + strategic insight\n"
        "• Charts: Economist-style plots with dual analysis (quant + macro)\n"
        "• Signature: ⚡ <b>Kei & Kin | Numbers to Meaning</b>\n\n"
        "─────────────────────────────────────────\n\n"
        "<b>📊 Data Coverage</b>\n"
        "✓ Indonesian government bond yields & prices: 2023-2025 (FR95-FR104 series, 5Y/10Y tenors)\n"
        "  - FR = Fixing Rate bonds issued by Indonesia's government, NOT French government bonds\n"
        "✓ Indonesian bond auction forecasts: Dec 2025 - Dec 2026 (demand, awarded, bid-to-cover)\n\n"
        "<b>💡 Tips:</b>\n"
        "• Use <b>plot/chart/show/graph/visualize/compare</b> to get charts\n"
        "• Command-based plots (/kei, /kin, /both) include AI-generated analysis\n"
        "• Plain message plots (no prefix) show Economist-style charts instantly\n"
        "• Use <b>5 and 10 years</b> for multi-tenor comparison\n"
        "• Use <b>average/max/min</b> for aggregates\n"
        "• Use <b>auction/demand/incoming/awarded</b> for forecasts\n"
        "• All charts: Economist style (red/blue lines, minimal design, professional appearance)\n"
        "\n\n"
        "<b>🎨 Chart Styling</b>\n"
        "All charts (command-based & plain message) feature:\n"
        "• The Economist magazine styling (trademark red & blue colors)\n"
        "• Clean, minimalist design with light gray background\n"
        "• White horizontal gridlines only (no clutter)\n"
        "• Professional typography and legend placement\n"
        "• Resolution: 150 DPI for crisp display"
    )
    await update.message.reply_text(examples_text, parse_mode=ParseMode.HTML)


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
    
    # Detect if user wants a plot/chart (route through FastAPI /chat endpoint)
    needs_plot = any(keyword in question.lower() for keyword in ["plot", "chart", "show", "graph", "visualize", "compare"])
    
    await context.bot.send_chat_action(chat_id=update.message.chat_id, action="typing")
    
    if needs_plot:
        try:
            import httpx
            import base64
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {"q": question, "plot": True}
                resp = await client.post(f"{API_BASE_URL}/chat", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    data_summary = data.get('analysis', '')
                    if data.get("image"):
                        image_bytes = base64.b64decode(data["image"])
                        # Send plot with minimal caption
                        await update.message.reply_photo(
                            photo=image_bytes,
                            caption="💹 <b>Kei | Quant Research</b>",
                            parse_mode=ParseMode.HTML
                        )
                        # Send pre-computed analysis from FastAPI (no redundant LLM call)
                        if data_summary and data_summary.strip():
                            await update.message.reply_text(
                                html_module.escape(data_summary),
                                parse_mode=ParseMode.HTML
                            )
                    else:
                        # No image, send analysis-only response
                        await update.message.reply_text(
                            f"📊 <b>Kei | Quant Research</b>\n\n{html_module.escape(data_summary)}",
                            parse_mode=ParseMode.HTML
                        )
                    response_time = time.time() - start_time
                    metrics.log_query(user_id, username, question, "plot", response_time, True, persona="kei")
                else:
                    await update.message.reply_text(f"⚠️ Error from API: {resp.status_code}")
                    response_time = time.time() - start_time
                    metrics.log_query(user_id, username, question, "plot", response_time, False, f"API error {resp.status_code}", "kei")
        except Exception as e:
            logger.error(f"Error calling /chat endpoint: {e}")
            await update.message.reply_text("⚠️ Error generating plot. Please try again.")
            response_time = time.time() - start_time
            metrics.log_query(user_id, username, question, "plot", response_time, False, str(e), "kei")
    else:
        try:
            answer = await ask_kei(question)
            if not answer or not answer.strip():
                await update.message.reply_text("⚠️ Kei returned an empty response. Please try again.")
                response_time = time.time() - start_time
                metrics.log_query(user_id, username, question, "text", response_time, False, "Empty response", "kei")
                return
            formatted_response = f"{html_module.escape(answer)}"
            await update.message.reply_text(formatted_response, parse_mode=ParseMode.HTML)
            response_time = time.time() - start_time
            metrics.log_query(user_id, username, question, "text", response_time, True, persona="kei")
        except Exception as e:
            logger.error(f"Error in /kei command: {e}")
            await update.message.reply_text("⚠️ Error processing query. Please try again.")
            response_time = time.time() - start_time
            metrics.log_query(user_id, username, question, "text", response_time, False, str(e), "kei")


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
    
    # Detect if user wants a plot/chart (route through FastAPI /chat endpoint)
    needs_plot = any(keyword in question.lower() for keyword in ["plot", "chart", "show", "graph", "visualize", "compare"])
    
    await context.bot.send_chat_action(chat_id=update.message.chat_id, action="typing")
    
    if needs_plot:
        try:
            import httpx
            import base64
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {"q": question, "plot": True, "persona": "kin"}
                resp = await client.post(f"{API_BASE_URL}/chat", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    data_summary = data.get('analysis', '')
                    if data.get("image"):
                        image_bytes = base64.b64decode(data["image"])
                        # Send plot with minimal caption
                        await update.message.reply_photo(
                            photo=image_bytes,
                            caption="🌍 <b>Kin | Economics & Strategy</b>",
                            parse_mode=ParseMode.HTML
                        )
                        # Send pre-computed analysis from FastAPI (no redundant LLM call)
                        if data_summary and data_summary.strip():
                            await update.message.reply_text(
                                html_module.escape(data_summary),
                                parse_mode=ParseMode.HTML
                            )
                    else:
                        # No image, send analysis-only response
                        await update.message.reply_text(
                            f"📊 <b>Kin | Economics & Strategy</b>\n\n{html_module.escape(data_summary)}",
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
            await update.message.reply_text("⚠️ Error generating plot. Please try again.")
            response_time = time.time() - start_time
            metrics.log_query(user_id, username, question, "plot", response_time, False, str(e), "kin")
    else:
        try:
            answer = await ask_kin(question)
            if not answer or not answer.strip():
                await update.message.reply_text("⚠️ Kin returned an empty response. Please try again.")
                response_time = time.time() - start_time
                metrics.log_query(user_id, username, question, "text", response_time, False, "Empty response", "kin")
                return
            formatted_response = f"{html_module.escape(answer)}"
            await update.message.reply_text(formatted_response, parse_mode=ParseMode.HTML)
            response_time = time.time() - start_time
            metrics.log_query(user_id, username, question, "text", response_time, True, persona="kin")
        except Exception as e:
            logger.error(f"Error in /kin command: {e}")
            await update.message.reply_text("⚠️ Error processing query. Please try again.")
            response_time = time.time() - start_time
            metrics.log_query(user_id, username, question, "text", response_time, False, str(e), "kin")


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
    
    # Detect if user wants a plot/chart (route through FastAPI /chat endpoint)
    needs_plot = any(keyword in question.lower() for keyword in ["plot", "chart", "show", "graph", "visualize", "compare"])
    
    await context.bot.send_chat_action(chat_id=update.message.chat_id, action="typing")
    
    if needs_plot:
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
                        # Send plot with minimal caption
                        await update.message.reply_photo(
                            photo=image_bytes,
                            caption="⚡ <b>Kei & Kin | Numbers to Meaning</b>",
                            parse_mode=ParseMode.HTML
                        )
                        # Send pre-computed analysis from FastAPI (no redundant LLM calls)
                        if data_summary and data_summary.strip():
                            await update.message.reply_text(
                                html_module.escape(data_summary),
                                parse_mode=ParseMode.HTML
                            )
                    else:
                        # No image, send analysis-only response
                        await update.message.reply_text(
                            f"📊 <b>Kei & Kin | Numbers to Meaning</b>\n\n{html_module.escape(data_summary)}",
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
            await update.message.reply_text("⚠️ Error generating plot. Please try again.")
            response_time = time.time() - start_time
            metrics.log_query(user_id, username, question, "plot", response_time, False, str(e), "both")
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
            
            # Strip individual persona signatures (they each end with ________ and signature line)
            # Remove the trailing signature section from both answers
            def strip_signature(answer):
                """Remove trailing ________ and persona line from response."""
                lines = answer.rstrip().split('\n')
                # Find and remove the ________ line and everything after it
                for i in range(len(lines) - 1, -1, -1):
                    if '________' in lines[i]:
                        return '\n'.join(lines[:i]).rstrip()
                return answer
            
            kei_clean = strip_signature(kei_answer)
            kin_clean = strip_signature(kin_answer)
            
            response = (
                "🎯 <b>Kei & Kin | Data → Insight</b>\n\n"
                f"{html_module.escape(kei_clean)}\n\n"
                "---\n\n"
                f"{html_module.escape(kin_clean)}\n\n"
                "________"
            )
            
            await update.message.reply_text(response, parse_mode=ParseMode.HTML)
            response_time = time.time() - start_time
            metrics.log_query(user_id, username, question, "text", response_time, True, persona="both")
        except Exception as e:
            logger.error(f"Error in /both command: {e}")
            await update.message.reply_text("⚠️ Error processing query. Please try again.")
            response_time = time.time() - start_time
            metrics.log_query(user_id, username, question, "text", response_time, False, str(e), "both")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming text messages with bond queries."""
    user_id = update.message.from_user.id
    if not is_user_authorized(user_id):
        await update.message.reply_text(
            "⛔ Access denied. This bot is restricted to authorized users only."
        )
        logger.warning("Unauthorized access attempt from user_id=%s", user_id)
        return
    
    user_query = update.message.text or ""
    chat_id = update.message.chat_id
    
    # Send typing indicator
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        # Persona routing: \kei (OpenAI) and \kin (Perplexity)
        lowered = user_query.strip().lower()
        if lowered.startswith("\\kei"):
            question = user_query.strip()[4:].strip()  # remove prefix
            if not question:
                await update.message.reply_text("Usage: \\kei <question>")
                return
            await context.bot.send_chat_action(chat_id=chat_id, action="typing")
            answer = await ask_kei(question)
            if not answer or not answer.strip():
                await update.message.reply_text("⚠️ Kei returned an empty response. Please try again.")
                return
            formatted_response = f"{html_module.escape(answer)}"
            await update.message.reply_text(formatted_response, parse_mode=ParseMode.HTML)
            return

        if lowered.startswith("\\kin"):
            question = user_query.strip()[4:].strip()
            if not question:
                await update.message.reply_text("Usage: \\kin <question>")
                return
            await context.bot.send_chat_action(chat_id=chat_id, action="typing")
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
        intent = parse_intent(user_query)
        db = get_db()
        
        # POINT query
        if intent.type == 'POINT':
            d = intent.point_date
            params = [d.isoformat()]
            where = 'obs_date = ?'
            if intent.tenor:
                where += ' AND tenor = ?'
                params.append(intent.tenor)
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
            response_text += format_rows_for_telegram(rows_list, include_date=False)
            
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
                    await context.bot.send_chat_action(chat_id=chat_id, action="upload_photo")
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
                        # Route through FastAPI /chat endpoint for Economist style + AI analysis
                        try:
                            async with httpx.AsyncClient(timeout=60.0) as client:
                                payload = {"q": user_query, "plot": True}
                                resp = await client.post(f"{API_BASE_URL}/chat", json=payload)
                                if resp.status_code == 200:
                                    data = resp.json()
                                    data_summary = data.get('analysis', '')
                                    if data.get("image"):
                                        image_bytes = base64.b64decode(data["image"])
                                        # Send plot with minimal caption
                                        await update.message.reply_photo(
                                            photo=image_bytes,
                                            caption="📊 <b>Bond Analysis Chart</b>",
                                            parse_mode=ParseMode.HTML
                                        )
                                        # Send AI analysis if available
                                        if data_summary and data_summary.strip():
                                            await update.message.reply_text(
                                                html_module.escape(data_summary),
                                                parse_mode=ParseMode.HTML
                                            )
                                    else:
                                        # No image, send analysis-only response
                                        await update.message.reply_text(
                                            f"📊 <b>Bond Analysis</b>\n\n{html_module.escape(data_summary)}",
                                            parse_mode=ParseMode.HTML
                                        )
                                else:
                                    await update.message.reply_text(f"⚠️ Error from API: {resp.status_code}")
                        except Exception as e:
                            logger.error(f"Error calling /chat endpoint: {e}")
                            await update.message.reply_text("⚠️ Error generating plot. Please try again.")
                else:
                    # No plot requested - show data rows with statistics
                    # Calculate statistics
                    metric_values = [r.get(intent.metric) for r in rows_list if r.get(intent.metric) is not None]
                    
                    response_text = f"📊 *Found {len(rows_list)} records*\n"
                    response_text += f"Period: {intent.start_date} → {intent.end_date}\n"
                    
                    if metric_values:
                        import statistics
                        min_val = min(metric_values)
                        max_val = max(metric_values)
                        avg_val = statistics.mean(metric_values)
                        std_val = statistics.stdev(metric_values) if len(metric_values) > 1 else 0
                        
                        response_text += f"\n📈 *Statistics ({intent.metric}):*\n"
                        response_text += f"Min: {min_val:.2f} | Max: {max_val:.2f}\n"
                        response_text += f"Avg: {avg_val:.2f} | StdDev: {std_val:.2f}\n"
                    
                    response_text += "\n"
                    
                    # Show all rows (or split into messages if too many)
                    formatted_rows = format_rows_for_telegram(rows_list, include_date=True)
                    
                    if len(formatted_rows) > 3500:  # Telegram message limit is 4096, leave buffer
                        # Send in multiple messages if too long
                        response_text += formatted_rows[:3500]
                        await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)
                        response_text = formatted_rows[3500:]
                        await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)
                    else:
                        response_text += formatted_rows
                    await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)
                
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
    
    if has_seaborn:
        sns.set_theme(style='whitegrid', context='notebook', palette='bright')
        fig, ax = plt.subplots(figsize=(10, 8))
        apply_economist_style(fig, ax)
        
        if is_multi_tenor:
            # Multi-tenor: plot separate lines for each tenor with distinct colors
            sns.lineplot(data=daily, x='obs_date', y=metric, hue='tenor_label', 
                        linewidth=2.5, ax=ax, errorbar=None, palette=ECONOMIST_PALETTE, legend='full')
            # Improve legend
            ax.legend(title='Tenor', fontsize=11, title_fontsize=12, 
                     loc='best', frameon=True, fancybox=True, shadow=True)
        else:
            # Single tenor: original single-line plot
            sns.lineplot(data=daily, x='obs_date', y=metric, linewidth=2.5, ax=ax, color=ECONOMIST_COLORS['red'])
        
        # Add highlight marker if date is in the data
        if highlight_ts is not None:
            if is_multi_tenor:
                # Highlight all tenors at the date
                highlight_rows = daily[daily['obs_date'] == highlight_ts]
                if not highlight_rows.empty:
                    for _, row in highlight_rows.iterrows():
                        ax.plot(highlight_ts, row[metric], 'r*', markersize=15, zorder=5)
                    ax.text(highlight_ts, highlight_rows[metric].mean(), 
                           f'  📍 {format_date(highlight_ts)}', fontsize=9, va='center')
            else:
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
        
        ax.set_title(f'{metric.capitalize()} {display_tenor} from {title_start} to {title_end}', 
                    fontsize=14, fontweight='bold', pad=20)
        if is_multi_tenor:
            # Legend already set above with better styling
            pass
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel(metric.capitalize(), fontsize=12)
        
        from matplotlib.dates import DateFormatter
        date_formatter = DateFormatter('%-d %b %Y')
        ax.xaxis.set_major_formatter(date_formatter)
        plt.gcf().autofmt_xdate()
        plt.grid(alpha=0.3)
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
        
        ax.set_title(f'{metric.capitalize()} {display_tenor} from {title_start} to {title_end}')
        ax.set_xlabel('Date')
        ax.set_ylabel(metric.capitalize())
        fig.autofmt_xdate()
        plt.grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(buf, format='png', dpi=150)
    plt.close()
    buf.seek(0)
    return buf.read()


def create_telegram_app(token: str) -> Application:
    """Create and configure the Telegram application."""
    application = Application.builder().token(token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("examples", examples_command))
    # Personas
    application.add_handler(CommandHandler("kei", kei_command))
    application.add_handler(CommandHandler("kin", kin_command))
    application.add_handler(CommandHandler("both", both_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    return application
