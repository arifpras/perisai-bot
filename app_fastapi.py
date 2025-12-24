"""Simple FastAPI wrapper for the bond CLI logic in 20251223_priceyield.py

Endpoints:
- GET /health
- POST /query  {"q": "average yield Q1 2023", "csv": "20251215_priceyield.csv"}
- POST /telegram/webhook - Telegram bot webhook
- GET /bot/stats - Bot traffic and metrics

This file reuses parse_intent and BondDB from the existing module.
"""
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import time
import logging

from datetime import date
import os
import io
import base64
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
try:
    import seaborn as sns
    _HAS_SEABORN = True
    _SNS_STYLE = os.environ.get("BOND_SNS_STYLE", "darkgrid")
    _SNS_CONTEXT = os.environ.get("BOND_SNS_CONTEXT", "notebook")
    _SNS_PALETTE = os.environ.get("BOND_SNS_PALETTE", "bright")
except Exception:
    _HAS_SEABORN = False

# Import parsing and DB logic from existing script (filename begins with digits so import dynamically)
import importlib.util
from pathlib import Path
_mod_path = Path(__file__).with_name("20251223_priceyield.py")
if not _mod_path.exists():
    raise RuntimeError(f"Could not find module file: {_mod_path}")
spec = importlib.util.spec_from_file_location("priceyield_mod", str(_mod_path))
priceyield_mod = importlib.util.module_from_spec(spec)
import sys
sys.modules["priceyield_mod"] = priceyield_mod
spec.loader.exec_module(priceyield_mod)
parse_intent = priceyield_mod.parse_intent
BondDB = priceyield_mod.BondDB
Intent = priceyield_mod.Intent

# Import metrics
from metrics import metrics

app = FastAPI(title="Bond Query API")

# Setup logging
logger = logging.getLogger(__name__)

# Allow local browser testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory cache of BondDB instances keyed by csv path
_DB_CACHE: Dict[str, BondDB] = {}

def get_db(csv: str) -> BondDB:
    if csv not in _DB_CACHE:
        _DB_CACHE[csv] = BondDB(csv)
    return _DB_CACHE[csv]


class QueryRequest(BaseModel):
    q: str
    csv: Optional[str] = "20251215_priceyield.csv"


class QueryResponse(BaseModel):
    intent: Dict[str, Any]
    result: Dict[str, Any]


@app.on_event("startup")
async def startup_event():
    """Initialize Telegram bot on startup."""
    if TELEGRAM_BOT_TOKEN:
        print(f"✅ TELEGRAM_BOT_TOKEN is set (length: {len(TELEGRAM_BOT_TOKEN)})")
        if _telegram_app:
            print("✅ Telegram bot initialized successfully!")
        elif _telegram_import_error:
            print(f"❌ Telegram bot import error: {_telegram_import_error}")
    else:
        print("⚠️  TELEGRAM_BOT_TOKEN not set - Telegram endpoints will return 503")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    q = req.q
    csv = req.csv
    try:
        intent: Intent = parse_intent(q)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse intent: {e}")

    db = get_db(csv)

    # POINT
    if intent.type == "POINT":
        d: date = intent.point_date
        params = [d.isoformat()]
        where = "obs_date = ?"
        if intent.tenor:
            where += " AND tenor = ?"
            params.append(intent.tenor)
        if intent.series:
            where += " AND series = ?"
            params.append(intent.series)

        q_sql = f"SELECT series, tenor, price, \"yield\" FROM ts WHERE {where} ORDER BY series LIMIT 500"
        rows = db.con.execute(q_sql, params).fetchall()
        rows_list = [dict(series=r[0], tenor=r[1], price=r[2], **{'yield': r[3]}) for r in rows]
        return QueryResponse(
            intent={"type": intent.type, "metric": intent.metric, "point_date": d.isoformat(), "series": intent.series, "tenor": intent.tenor},
            result={"type": "point_rows", "rows": rows_list, "count": len(rows_list)},
        )

    # RANGE / AGG_RANGE
    if intent.type in ("RANGE", "AGG_RANGE"):
        if not intent.agg:
            return QueryResponse(
                intent={"type": intent.type, "start_date": intent.start_date.isoformat(), "end_date": intent.end_date.isoformat()},
                result={"note": "Range detected. Provide an aggregate like 'avg' to compute an aggregation."},
            )
        val, n = db.aggregate(intent.start_date, intent.end_date, intent.metric, intent.agg, intent.series, intent.tenor)
        return QueryResponse(
            intent={"type": intent.type, "agg": intent.agg, "metric": intent.metric, "start_date": intent.start_date.isoformat(), "end_date": intent.end_date.isoformat(), "series": intent.series, "tenor": intent.tenor},
            result={"value": val, "n": n},
        )

    raise HTTPException(status_code=400, detail="Unhandled intent type")


# --- Plot helper: returns PNG bytes for a range query ---
def _plot_range_to_png(db: BondDB, start_date: date, end_date: date, metric: str = 'yield', tenor: Optional[str] = None, tenors: Optional[list] = None, highlight_date: Optional[date] = None) -> bytes:
    # Query the ts view
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
        # return a tiny PNG that says 'no data'
        plt.figure(figsize=(4,2))
        plt.text(0.5,0.5,'No data', ha='center', va='center')
        buf = io.BytesIO()
        plt.axis('off')
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close()
        buf.seek(0)
        return buf.read()

    df['obs_date'] = pd.to_datetime(df['obs_date'])
    
    # Determine if multi-tenor plot
    is_multi_tenor = tenors and len(tenors) > 1

    # per-series reindex + ffill to daily frequency then average across series
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
        daily['tenor_label'] = daily['tenor'].str.replace('_', ' ').str.replace('0', '', 1)
    else:
        # Single tenor: original aggregation logic
        filled = []
        for s, g in df.groupby('series'):
            g2 = g.set_index('obs_date').reindex(all_dates)
            g2['series'] = s
            g2[['price','yield']] = g2[['price','yield']].ffill()
            filled.append(g2.reset_index().rename(columns={'index':'obs_date'}))
        filled = pd.concat(filled, ignore_index=True)
        daily = filled.groupby('obs_date')[metric].mean().reset_index()

    # Format dates for display
    def format_date(d):
        """Convert date to '1 Jan 2023' format"""
        return d.strftime('%-d %b %Y') if hasattr(d, 'strftime') else str(d)
    
    # Format tenor for display
    if is_multi_tenor:
        display_tenor = ', '.join([t.replace('_', ' ') for t in tenors])
    else:
        display_tenor = tenor.replace('_', ' ') if tenor else ''
    
    # Format title dates
    title_start = format_date(start_date)
    title_end = format_date(end_date)
    
    # Convert highlight_date to pandas Timestamp if provided
    highlight_ts = None
    if highlight_date:
        highlight_ts = pd.Timestamp(highlight_date)

    # plot (prefer seaborn if available)
    buf = io.BytesIO()
    try:
        if _HAS_SEABORN:
            sns.set_theme(style=_SNS_STYLE, context=_SNS_CONTEXT, palette=_SNS_PALETTE)
            fig, ax = plt.subplots(figsize=(10, 6))
            
            if is_multi_tenor:
                # Multi-tenor: plot separate lines for each tenor with distinct colors
                sns.lineplot(data=daily, x='obs_date', y=metric, hue='tenor_label', 
                            linewidth=2.5, ax=ax, errorbar=None, palette='Set1', legend='full')
                # Improve legend
                ax.legend(title='Tenor', fontsize=11, title_fontsize=12, 
                         loc='best', frameon=True, fancybox=True, shadow=True)
                
                # Add highlight marker if date is in the data
                if highlight_ts is not None:
                    for tenor_val in tenors:
                        tenor_label = tenor_val.replace('_', ' ').replace('0', '', 1)
                        daily_tenor = daily[daily['tenor'] == tenor_val]
                        daily_tenor['date_diff'] = (daily_tenor['obs_date'] - highlight_ts).abs()
                        if not daily_tenor.empty:
                            closest = daily_tenor.loc[daily_tenor['date_diff'].idxmin()]
                            y_val = closest[metric]
                            ax.plot(closest['obs_date'], y_val, 'r*', markersize=15, zorder=5)
            else:
                # Single tenor: original single-line plot
                sns.lineplot(data=daily, x='obs_date', y=metric, linewidth=2, ax=ax)
                
                # Highlight specific date if provided
                if highlight_ts is not None:
                    highlight_row = daily[daily['obs_date'] == highlight_ts]
                    if not highlight_row.empty:
                        highlight_date_str = format_date(highlight_date)
                        ax.plot(highlight_row['obs_date'], highlight_row[metric], 'ro', markersize=8, label=f'Highlight: {highlight_date_str}')
                        ax.legend()
            
            # Set title with formatted dates
            ax.set_title(f'{metric.capitalize()} {display_tenor} from {title_start} to {title_end}')
            ax.set_xlabel('Date')
            ax.set_ylabel(metric.capitalize())
            
            # Format x-axis dates
            from matplotlib.dates import DateFormatter
            date_formatter = DateFormatter('%-d %b %Y')
            ax.xaxis.set_major_formatter(date_formatter)
            
            fig.autofmt_xdate()
            sns.despine(ax=ax)
            fig.tight_layout()
            fig.savefig(buf, format='png')
            plt.close(fig)
        else:
            raise RuntimeError('seaborn not available')
    except Exception:
        # Fallback to plain matplotlib
        plt.figure(figsize=(8,3))
        plt.plot(daily['obs_date'], daily[metric], linestyle='-')
        
        # Highlight specific date if provided
        if highlight_date:
            highlight_row = daily[daily['obs_date'] == pd.Timestamp(highlight_date)]
            if not highlight_row.empty:
                highlight_date_str = format_date(highlight_date)
                plt.plot(highlight_row['obs_date'], highlight_row[metric], 'ro', markersize=8, label=f'Highlight: {highlight_date_str}')
                plt.legend()
        
        plt.title(f'{metric.capitalize()} {display_tenor} from {title_start} to {title_end}')
        plt.xlabel('Date')
        plt.ylabel(metric.capitalize())
        
        # Format x-axis dates
        from matplotlib.dates import DateFormatter
        date_formatter = DateFormatter('%-d %b %Y')
        plt.gca().xaxis.set_major_formatter(date_formatter)
        plt.gcf().autofmt_xdate()
        
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(buf, format='png')
        plt.close()
    buf.seek(0)
    return buf.read()


@app.post('/plot')
async def plot(req: QueryRequest):
    """Return a PNG plot for a range query. Use the same natural language queries that produce a RANGE intent."""
    try:
        intent: Intent = parse_intent(req.q)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse intent: {e}")

    if intent.type not in ('RANGE','AGG_RANGE'):
        raise HTTPException(status_code=400, detail='Plot endpoint expects a RANGE query (e.g., "10 year 2023")')

    db = get_db(req.csv)
    png = _plot_range_to_png(db, intent.start_date, intent.end_date, metric=intent.metric, tenor=intent.tenor, tenors=intent.tenors)
    return StreamingResponse(io.BytesIO(png), media_type='image/png')


class ChatRequest(BaseModel):
    q: str
    csv: Optional[str] = '20251215_priceyield.csv'
    plot: Optional[bool] = False
    highlight_date: Optional[str] = None  # Optional date to highlight on plot (e.g., "2023-05-15")


@app.post('/chat')
async def chat_endpoint(req: ChatRequest):
    """Higher-level chat endpoint: returns JSON with text and optional base64 PNG if plot=True."""
    start_time = time.time()
    error_msg = None
    query_type = "unknown"
    
    try:
        intent: Intent = parse_intent(req.q)
        query_type = intent.type.lower() if intent.type else "unknown"
    except Exception as e:
        error_msg = str(e)
        metrics.log_query(0, "api", req.q, "parse_error", time.time() - start_time, False, error_msg, "api")
        raise HTTPException(status_code=400, detail=f"Could not parse intent: {e}")

    db = get_db(req.csv)

    # POINT
    if intent.type == 'POINT':
        d = intent.point_date
        params = [d.isoformat()]
        where = 'obs_date = ?'
        if intent.tenor:
            where += ' AND tenor = ?'; params.append(intent.tenor)
        if intent.series:
            where += ' AND series = ?'; params.append(intent.series)
        rows = db.con.execute(f'SELECT series, tenor, price, "yield" FROM ts WHERE {where} ORDER BY series', params).fetchall()
        rows_list = [dict(series=r[0], tenor=r[1], price=round(r[2], 2) if r[2] is not None else None, **{'yield': round(r[3], 2) if r[3] is not None else None}) for r in rows]
        text = f"Found {len(rows_list)} row(s) for {intent.tenor or 'all tenors'} on {d}:"
        return JSONResponse({"text": text, "rows": rows_list})

    # RANGE / AGG_RANGE handling (support plotting without explicit aggregation)
    # Determine whether user requested a plot by keywords or by the `plot` flag
    lower_q = (req.q or '').lower()
    plot_keywords = ('plot', 'chart', 'show', 'visualize', 'graph')
    wants_plot = bool(req.plot) or any(k in lower_q for k in plot_keywords)

    if intent.type in ('RANGE', 'AGG_RANGE'):
        # If an aggregation is present, compute it and optionally plot
        if intent.agg:
            val, n = db.aggregate(intent.start_date, intent.end_date, intent.metric, intent.agg, intent.series, intent.tenor)
            text = f"{intent.agg.upper()} {intent.metric} {intent.start_date} → {intent.end_date} = {round(val, 2) if val is not None else 'N/A'} (N={n})"
            if wants_plot:
                # Use highlight_date from intent
                highlight_date_obj = intent.highlight_date
                png = _plot_range_to_png(db, intent.start_date, intent.end_date, metric=intent.metric, tenor=intent.tenor, tenors=intent.tenors, highlight_date=highlight_date_obj)
                b64 = base64.b64encode(png).decode('ascii')
                return JSONResponse({"text": text, "image_base64": b64})
            return JSONResponse({"text": text})

        # No aggregation provided — return all individual rows for the date range
        params = [intent.start_date.isoformat(), intent.end_date.isoformat()]
        where = 'obs_date BETWEEN ? AND ?'
        if intent.tenor:
            where += ' AND tenor = ?'; params.append(intent.tenor)
        if intent.series:
            where += ' AND series = ?'; params.append(intent.series)
        rows = db.con.execute(f'SELECT series, tenor, obs_date, price, "yield" FROM ts WHERE {where} ORDER BY obs_date DESC, series', params).fetchall()
        rows_list = [dict(series=r[0], tenor=r[1], date=r[2].isoformat(), price=round(r[3], 2) if r[3] is not None else None, **{'yield': round(r[4], 2) if r[4] is not None else None}) for r in rows]
        text = f"Found {len(rows_list)} row(s) for {intent.tenor or 'all tenors'} from {intent.start_date} to {intent.end_date}:"
        
        # If the user asked for a plot, also include it
        if wants_plot:
            # Use highlight_date from intent
            highlight_date_obj = intent.highlight_date
            png = _plot_range_to_png(db, intent.start_date, intent.end_date, metric=intent.metric, tenor=intent.tenor, tenors=intent.tenors, highlight_date=highlight_date_obj)
            b64 = base64.b64encode(png).decode('ascii')
            return JSONResponse({"text": text, "rows": rows_list, "image_base64": b64})
        
        return JSONResponse({"text": text, "rows": rows_list})


# Minimal chat UI (single-file)
@app.get('/ui')
async def ui():
    html = """
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8" />
      <title>Bond Chat UI</title>
      <style>body{font-family:system-ui,Segoe UI,Helvetica,Arial;margin:20px}#chat{border:1px solid #ddd;padding:10px;height:400px;overflow:auto} .msg{margin:8px 0} .user{color:blue} .bot{color:green}</style>
    </head>
    <body>
      <h3>Bond Chat (local)</h3>
      <div id="chat"></div>
      <div style="margin-top:10px">
        <input id="q" style="width:70%" placeholder="Ask something like: what's the yield of 10 year on 2 May 2023" />
        <button id="send">Send</button>
        <label><input type="checkbox" id="plot" /> plot</label>
      </div>
      <script>
        async function postJSON(url, data){
          const r = await fetch(url, {method:'POST',headers:{'Content-Type':'application/json'}, body: JSON.stringify(data)});
          return r.json();
        }
        const chat = document.getElementById('chat');
        function addMsg(who, html){ const d=document.createElement('div'); d.className='msg '+who; d.innerHTML=html; chat.appendChild(d); chat.scrollTop = chat.scrollHeight; }
        document.getElementById('send').onclick = async ()=>{
          const q = document.getElementById('q').value; const plot = document.getElementById('plot').checked;
          if(!q) return;
          addMsg('user','<b>You:</b> '+q);
          addMsg('bot','<i>… thinking …</i>');
          try{
            const res = await postJSON('/chat',{q:q, plot:plot});
            chat.lastChild.innerHTML = '<b>Bot:</b> '+(res.text||'');
            if(res.image_base64){
              const img = new Image(); img.src = 'data:image/png;base64,'+res.image_base64; img.style.maxWidth='100%'; img.style.marginTop='8px'; chat.appendChild(img); chat.scrollTop = chat.scrollHeight;
            }
            if(res.rows){
              const pre = document.createElement('pre'); pre.textContent = JSON.stringify(res.rows, null, 2); chat.appendChild(pre); chat.scrollTop = chat.scrollHeight;
            }
          }catch(e){ chat.lastChild.innerHTML = '<b>Bot:</b> Error - '+e }
        }
      </script>
    </body>
    </html>
    """
    return HTMLResponse(html)


# ============================================
# TELEGRAM BOT INTEGRATION
# ============================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
_telegram_app = None
_telegram_import_error = None
_telegram_initialized = False

# Try to import telegram bot module at startup
try:
    if TELEGRAM_BOT_TOKEN:
        from telegram_bot import create_telegram_app
        _telegram_app = create_telegram_app(TELEGRAM_BOT_TOKEN)
except Exception as e:
    _telegram_import_error = str(e)
    print(f"⚠️  Warning: Could not initialize Telegram bot: {e}")

def get_telegram_app():
    """Get the Telegram application instance."""
    return _telegram_app


async def ensure_telegram_initialized():
    """Ensure Telegram application is initialized before processing updates."""
    global _telegram_initialized
    telegram_app = get_telegram_app()
    if telegram_app and not _telegram_initialized:
        try:
            await telegram_app.initialize()
            _telegram_initialized = True
        except Exception as e:
            print(f"⚠️  Error initializing Telegram app: {e}")
            raise


@app.post('/telegram/webhook')
async def telegram_webhook(request: Request):
    """Webhook endpoint for Telegram bot updates."""
    if not TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=503, detail="Telegram bot not configured. Set TELEGRAM_BOT_TOKEN environment variable.")
    
    telegram_app = get_telegram_app()
    if not telegram_app:
        raise HTTPException(status_code=503, detail="Telegram app not initialized")
    
    try:
        # Ensure app is initialized
        await ensure_telegram_initialized()
        
        from telegram import Update
        update_data = await request.json()
        update = Update.de_json(update_data, telegram_app.bot)
        await telegram_app.process_update(update)
        return {"ok": True}
    except Exception as e:
        print(f"❌ Webhook error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing update: {str(e)}")


@app.get('/telegram/set_webhook')
async def set_telegram_webhook(webhook_url: str):
    """Set the webhook URL for the Telegram bot. Call this once after deployment.
    
    Example: GET /telegram/set_webhook?webhook_url=https://perisai-api.onrender.com/telegram/webhook
    """
    if not TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=503, detail="Telegram bot not configured. Set TELEGRAM_BOT_TOKEN environment variable.")
    
    telegram_app = get_telegram_app()
    if not telegram_app:
        raise HTTPException(status_code=503, detail="Telegram app not initialized")
    
    try:
        await telegram_app.bot.set_webhook(webhook_url)
        info = await telegram_app.bot.get_webhook_info()
        return {
            "status": "ok",
            "webhook_url": info.url,
            "pending_update_count": info.pending_update_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error setting webhook: {str(e)}")


@app.get('/telegram/webhook_info')
async def get_webhook_info():
    """Get current webhook configuration."""
    if not TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=503, detail="Telegram bot not configured")
    
    telegram_app = get_telegram_app()
    if not telegram_app:
        raise HTTPException(status_code=503, detail="Telegram app not initialized")
    
    try:
        info = await telegram_app.bot.get_webhook_info()
        return {
            "url": info.url,
            "has_custom_certificate": info.has_custom_certificate,
            "pending_update_count": info.pending_update_count,
            "last_error_date": info.last_error_date,
            "last_error_message": info.last_error_message,
            "max_connections": info.max_connections,
            "allowed_updates": info.allowed_updates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting webhook info: {str(e)}")


@app.get("/bot/sample-data")
async def bot_sample_data():
    """Populate dashboard with sample data for demo purposes."""
    import random
    from datetime import datetime, timedelta
    
    # Sample queries
    sample_questions = [
        "yield 10 year 2025",
        "chart yield 5 year and 10 year June 2025",
        "average yield 10 year 2024",
        "auction demand January 2026",
        "plot yield FR95 2025",
        "price 5 year March 2025",
        "bid to cover Q1 2026",
    ]
    
    sample_personas = ["kei", "kin", "both"]
    sample_types = ["text", "plot"]
    
    # Add 20 sample queries
    for i in range(20):
        query = random.choice(sample_questions)
        persona = random.choice(sample_personas)
        qtype = random.choice(sample_types)
        response_time = random.uniform(100, 3000)
        success = random.random() > 0.2  # 80% success rate
        
        username = f"user_{random.randint(1000, 5000)}"
        user_id = random.randint(100000000, 999999999)
        
        metrics.log_query(
            user_id, 
            username, 
            query, 
            qtype, 
            response_time,
            success,
            error=None if success else "Sample error",
            persona=persona
        )
    
    return {"status": "Sample data loaded", "queries_added": 20}


@app.get("/bot/stats")
async def bot_stats():
    """Get bot traffic and performance metrics (JSON)."""
    return metrics.get_stats()


@app.get("/bot/dashboard")
async def bot_dashboard():
    """Get bot traffic dashboard (HTML)."""
    return HTMLResponse(content=metrics.get_html_dashboard())


@app.get("/bot/stats/user/{user_id}")
async def bot_user_stats(user_id: int):
    """Get stats for a specific user."""
    return metrics.get_user_stats(user_id)


if __name__ == "__main__":
    uvicorn.run("app_fastapi:app", host="127.0.0.1", port=8000, reload=True)