"""Telegram Bot Integration for Bond Price & Yield Chatbot
Handles incoming messages from Telegram and formats responses.
"""
import os
import io
import base64
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

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

def get_db(csv_path: str = "20251215_priceyield.csv") -> BondDB:
    """Get or create a cached BondDB instance."""
    if csv_path not in _db_cache:
        _db_cache[csv_path] = BondDB(csv_path)
    return _db_cache[csv_path]


def format_rows_for_telegram(rows, include_date=False):
    """Format data rows for Telegram message (monospace style)."""
    if not rows:
        return "No data found."
    
    lines = []
    for row in rows:
        if include_date:
            # RANGE query with date
            lines.append(
                f"🔹 {row['series']} | {row['tenor'].replace('_', ' ')} | {row['date']}\n"
                f"   Price: {row['price']:.2f} | Yield: {row.get('yield', 0):.2f}%"
            )
        else:
            # POINT query without date
            lines.append(
                f"🔹 {row['series']} | {row['tenor'].replace('_', ' ')}\n"
                f"   Price: {row['price']:.2f} | Yield: {row.get('yield', 0):.2f}%"
            )
    return "\n\n".join(lines)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
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
        "/examples - Show more examples\n\n"
        "Just send your question and I'll fetch the data! 🚀"
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)


async def examples_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /examples command."""
    examples_text = (
        "📝 *Query Examples:*\n\n"
        "*Point queries (specific date):*\n"
        "• `yield 10 year 2023-05-02`\n"
        "• `price 5 year on May 2 2023`\n"
        "• `FR95 yield 2023-01-15`\n\n"
        "*Range queries (aggregation):*\n"
        "• `average yield Q1 2023`\n"
        "• `avg yield 10 year May 2023`\n"
        "• `max price 5 year 2023`\n\n"
        "*Plot queries:*\n"
        "• `plot yield 10 year 2023`\n"
        "• `chart 5 year May 2023`\n"
        "• `show yield Q2 2023`\n\n"
        "💡 Tip: Include 'plot' or 'chart' in your query to get a visual graph!"
    )
    await update.message.reply_text(examples_text, parse_mode=ParseMode.MARKDOWN)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming text messages with bond queries."""
    user_query = update.message.text
    chat_id = update.message.chat_id
    
    # Send typing indicator
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
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
                    f'SELECT series, tenor, obs_date, price, "yield" FROM ts WHERE {where} ORDER BY obs_date DESC, series LIMIT 50',
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
                    # No plot requested - show data rows
                    response_text = f"📊 *Found {len(rows_list)} records*\n"
                    response_text += f"Period: {intent.start_date} → {intent.end_date}\n\n"
                    
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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    return application
