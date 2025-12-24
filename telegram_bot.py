"""Telegram Bot Integration for Bond Price & Yield Chatbot
Handles incoming messages from Telegram and formats responses.
"""
import os
import io
import base64
import logging
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

# Cache DB instances
_db_cache = {}

# OpenAI client for persona answers
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
_openai_client: Optional[AsyncOpenAI] = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
logger = logging.getLogger("telegram_bot")

# Perplexity API (HTTPX-based)
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "sonar-pro")

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


def summarize_intent_result(intent, rows_list):
    """Produce a short text summary of computed results for LLM context."""
    if not rows_list:
        return "No matching data found in the requested period."
    
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
        db = get_db()
        rows_list = []

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
                if intent.tenor:
                    where += ' AND tenor = ?'; params.append(intent.tenor)
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


async def ask_kei(question: str) -> str:
    """Persona /kei — world-class data scientist & econometrician."""
    if not _openai_client:
        return "⚠️ Persona /kei unavailable: OPENAI_API_KEY not configured."

    system_prompt = (
        "You are **Kei**.\n"
        "Profile: CFA charterholder, PhD (MIT). World-class data scientist with "
        "deep expertise in mathematics, statistics, econometrics, and forecasting.\n\n"

        "Operating principles:\n"
        "- Start from data and models, not opinions.\n"
        "- Be explicit about assumptions, uncertainty, and limitations.\n"
        "- If evidence is insufficient, say so clearly.\n"
        "- Avoid speculation, narratives, and policy advocacy.\n\n"

        "Output style (MANDATORY):\n"
        "- FOR CODING/PROGRAMMING REQUESTS: Do NOT use bullets. Provide code examples in plain format with brief explanations above/below.\n"
        "- FOR ANALYTICAL REQUESTS: EXACTLY 3 OR 4 bullets. No more, no fewer.\n"
        "- Each bullet is 1-2 sentences MAX (approximately 15-20 words).\n"
        "- Blank line between each bullet.\n"
        "- ZERO bold formatting: DO NOT use **text** or bold syntax. Plain text only.\n"
        "- ZERO headings, tables, equations.\n"
        "- TOTAL response: under 130 words (accommodates trailing questions).\n"
        "- Start immediately with content. No preamble.\n"
        "- End with 'Follow-up angles: [1-2 quantitative next-step questions]' on a new line.\n\n"

        "If precomputed bond or market data are provided:\n"
        "- Treat them as given inputs.\n"
        "- Do not fabricate missing data.\n"
        "- Base conclusions strictly on those inputs.\n"
        "- Trailing questions should probe deeper into the quantitative patterns or comparisons revealed."
    )

    data_summary = await try_compute_bond_summary(question)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": "Constraint: no live news access; information may be outdated."},
    ]

    if data_summary:
        messages.append({
            "role": "system",
            "content": f"Precomputed quantitative inputs:\n{data_summary}"
        })

    messages.append({"role": "user", "content": question})

    try:
        resp = await _openai_client.chat.completions.create(
            model="gpt-5.2",
            messages=messages,
            max_completion_tokens=220,
            temperature=0.3,  # low creativity, high precision
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ OpenAI error: {e}"


async def ask_kin(question: str) -> str:
    """Persona /kin — world-class economist & synthesizer."""
    if not PERPLEXITY_API_KEY:
        return "⚠️ Persona /kin unavailable: PERPLEXITY_API_KEY not configured."

    import httpx

    system_prompt = (
        "You are Kin.\n"
        "Profile: CFA charterholder, PhD (Harvard). World-class economist and data-driven storyteller—synthesizes complex market dynamics, "
        "economic incentives, and financial data into clear, compelling narratives that drive decisions.\n\n"

        "Operating principles (STRICT):\n"
        "- ONLY use data and numbers explicitly provided. NO hallucination, speculation, or outside information.\n"
        "- When citing numbers, cite exact values from the provided data.\n"
        "- Connect data, incentives, and context with zero invention.\n"
        "- Focus on implications, risks, and trade-offs grounded in evidence.\n"
        "- Be pragmatic and decision-oriented.\n\n"

        "Output style (MANDATORY):\n"
        "- EXACTLY 3 OR 4 bullets. No more, no fewer.\n"
        "- Each bullet is 1-3 sentences (can be longer if needed for nuance).\n"
        "- Blank line between each bullet.\n"
        "- ZERO bold formatting: DO NOT use **text** or bold syntax. Plain text only.\n"
        "- ZERO headings, tables, equations, code blocks.\n"
        "- TOTAL response: under 200 words (accommodates sources and trailing questions).\n"
        "- Start immediately with bullet 1. No preamble.\n"
        "- End with 'Sources: [data series used]' on its own line.\n"
        "- Then add 'Follow-up angles: [1-2 strategic next-step questions]' on a new line.\n\n"

        "If bond or market data summaries are provided:\n"
        "- Use them as the ONLY factual basis. Do not add external information.\n"
        "- Cite specific values, dates, tenors, or ranges from the data.\n"
        "- Translate quantitative results into economic meaning.\n"
        "- Do not redo analysis already supplied; interpret and contextualize it.\n"
        "- Trailing questions should probe strategic implications or economic incentives revealed by the data."
    )

    data_summary = await try_compute_bond_summary(question)

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
    """Chain both personas: Kei analyzes data quantitatively, Kin interprets & concludes."""
    kei_answer = await ask_kei(question)
    kin_answer = await ask_kin(
        f"Based on the following quantitative analysis, interpret and conclude:\n\n{kei_answer}"
    )
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
        "📈 *Welcome to Bond Price & Yield Bot!*\n\n"
        "Ask questions about Indonesian government bonds:\n\n"
        "📊 *Example queries:*\n"
        "• `yield 10 year 2023-05-02`\n"
        "• `average yield Q1 2023`\n"
        "• `plot yield 10 year May 2023`\n"
        "• `price FR96 2023-05-15`\n\n"
        "📌 *Commands:*\n"
        "/start - Show this help\n"
        "/examples - Show more examples\n"
        "/kei <question> - Ask persona Kei (ChatGPT)\n"
        "/kin <question> - Ask persona Kin (Perplexity)\n"
        "/both <question> - Chain both personas (quantitative → interpretation)\n\n"
        "Tip: You can also type `\\kei ...` or `\\kin ...` as shortcuts.\n\n"
        "Just send your question and I'll fetch the data! 🚀"
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)


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
        "📝 *Query Examples:*\n\n"
        "*Point queries (specific date):*\n"
        "• `yield 10 year 2025-06-15`\n"
        "• `yield 5 year june 2025`\n"
        "• `FR103 price 5 year June 15 2025`\n"
        "• `FR95 yield 2024-03-20`\n\n"
        "*Range queries (with statistics):*\n"
        "• `average yield 10 year June 2025`\n"
        "• `max yield FR103 2024`\n"
        "• `min price 5 year Q4 2024`\n\n"
        "*Plot queries (with charts):*\n"
        "• `plot yield 10 year 2025`\n"
        "• `chart FR103 5 year June 2025`\n"
        "• `show price 5 year Q2 2024`\n\n"
        "💡 Tip: Use 'plot' or 'chart' to get a visual graph!\n\n"
        "🤖 *Personas:*\n"
        "• `/kei <question>` — ChatGPT (quantitative analysis)\n"
        "• `/kin <question>` — Perplexity (economic interpretation)\n"
        "• `/both <question>` — Chain both: Kei analyzes, Kin concludes\n\n"
        "📊 Data available: 2023-2025 | Series: FR95-FR104 | Tenors: 5Y, 10Y"
    )
    await update.message.reply_text(examples_text, parse_mode=ParseMode.MARKDOWN)


async def kei_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/kei <question> — ask persona Kei (ChatGPT)."""
    user_id = update.message.from_user.id
    if not is_user_authorized(user_id):
        await update.message.reply_text(
            "⛔ Access denied. This bot is restricted to authorized users only."
        )
        logger.warning("Unauthorized access attempt from user_id=%s", user_id)
        return

    question = " ".join(context.args).strip() if context.args else ""
    if not question:
        await update.message.reply_text("Usage: /kei <question>")
        return
    await context.bot.send_chat_action(chat_id=update.message.chat_id, action="typing")
    answer = await ask_kei(question)
    formatted_response = (
        "🔬 <b>Kei</b> (Quantitative Analysis)\n\n"
        f"{html_module.escape(answer)}"
    )
    await update.message.reply_text(formatted_response, parse_mode=ParseMode.HTML)


async def kin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/kin <question> — ask persona Kin (Perplexity)."""
    user_id = update.message.from_user.id
    if not is_user_authorized(user_id):
        await update.message.reply_text(
            "⛔ Access denied. This bot is restricted to authorized users only."
        )
        logger.warning("Unauthorized access attempt from user_id=%s", user_id)
        return

    question = " ".join(context.args).strip() if context.args else ""
    if not question:
        await update.message.reply_text("Usage: /kin <question>")
        return
    await context.bot.send_chat_action(chat_id=update.message.chat_id, action="typing")
    answer = await ask_kin(question)
    formatted_response = (
        "💡 <b>Kin</b> (Economic Interpretation)\n\n"
        f"{html_module.escape(answer)}"
    )
    await update.message.reply_text(formatted_response, parse_mode=ParseMode.HTML)


async def both_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/both <question> — chain both personas: Kei (quantitative) → Kin (interpretation)."""
    user_id = update.message.from_user.id
    if not is_user_authorized(user_id):
        await update.message.reply_text(
            "⛔ Access denied. This bot is restricted to authorized users only."
        )
        logger.warning("Unauthorized access attempt from user_id=%s", user_id)
        return

    question = " ".join(context.args).strip() if context.args else ""
    if not question:
        await update.message.reply_text("Usage: /both <question>")
        return
    
    await context.bot.send_chat_action(chat_id=update.message.chat_id, action="typing")
    result = await ask_kei_then_kin(question)
    
    kei_answer = result["kei"]
    kin_answer = result["kin"]
    
    response = (
        "📊 <b>Dual Persona Analysis</b>\n\n"
        "🔬 <b>Kei</b> (Quantitative Analysis)\n\n"
        f"{html_module.escape(kei_answer)}\n\n"
        "💡 <b>Kin</b> (Economic Interpretation)\n\n"
        f"{html_module.escape(kin_answer)}"
    )
    
    await update.message.reply_text(response, parse_mode=ParseMode.HTML)


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
            formatted_response = (
                "🔬 <b>Kei</b> (Quantitative Analysis)\n\n"
                f"{html_module.escape(answer)}"
            )
            await update.message.reply_text(formatted_response, parse_mode=ParseMode.HTML)
            return

        if lowered.startswith("\\kin"):
            question = user_query.strip()[4:].strip()
            if not question:
                await update.message.reply_text("Usage: \\kin <question>")
                return
            await context.bot.send_chat_action(chat_id=chat_id, action="typing")
            answer = await ask_kin(question)
            formatted_response = (
                "💡 <b>Kin</b> (Economic Interpretation)\n\n"
                f"{html_module.escape(answer)}"
            )
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
                    png = generate_plot(db, intent.start_date, intent.end_date, intent.metric, intent.tenor, intent.highlight_date)
                    await update.message.reply_photo(photo=io.BytesIO(png))
            
            else:
                # Range without aggregation - return individual rows
                params = [intent.start_date.isoformat(), intent.end_date.isoformat()]
                where = 'obs_date BETWEEN ? AND ?'
                if intent.tenor:
                    where += ' AND tenor = ?'
                    params.append(intent.tenor)
                if intent.series:
                    where += ' AND series = ?'
                    params.append(intent.series)
                
                rows = db.con.execute(
                    f'SELECT series, tenor, obs_date, price, "yield" FROM ts WHERE {where} ORDER BY obs_date ASC, series LIMIT 50',
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
                
                # If plot is requested, send plot directly without row details
                if wants_plot:
                    if len(rows_list) == 0:
                        await update.message.reply_text(
                            f"❌ No data found for {intent.tenor or 'bonds'} in this period.",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        # Send summary then plot
                        response_text = f"📊 *{intent.metric.capitalize()} Chart*\n"
                        response_text += f"Period: {intent.start_date} → {intent.end_date}\n"
                        if intent.tenor:
                            response_text += f"Tenor: {intent.tenor.replace('_', ' ')}\n"
                        if intent.highlight_date:
                            response_text += f"📍 Highlighting: {intent.highlight_date}\n"
                        response_text += f"Data points: {len(rows_list)}"
                        
                        await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)
                        
                        await context.bot.send_chat_action(chat_id=chat_id, action="upload_photo")
                        try:
                            png = generate_plot(db, intent.start_date, intent.end_date, intent.metric, intent.tenor, intent.highlight_date)
                            await update.message.reply_photo(photo=io.BytesIO(png))
                        except Exception as e:
                            await update.message.reply_text(
                                f"⚠️ Could not generate plot: {str(e)}",
                                parse_mode=ParseMode.MARKDOWN
                            )
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


def generate_plot(db, start_date, end_date, metric='yield', tenor=None, highlight_date=None):
    """Generate a plot and return PNG bytes."""
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
    if tenor:
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
    
    # Fill missing dates and aggregate
    all_dates = pd.date_range(start_date, end_date, freq='D')
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
        sns.set_theme(style='darkgrid', context='notebook', palette='bright')
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.lineplot(data=daily, x='obs_date', y=metric, linewidth=2, ax=ax)
        
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
