# Telegram Bot Setup for Bond Price & Yield Chatbot

This guide explains how to set up and deploy the Telegram bot integration.

## 🚀 Quick Setup (5 minutes)

### 1. Create Your Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` command
3. Choose a name (e.g., "DJPPR Bond Bot")
4. Choose a username (e.g., "djppr_bond_bot")
5. **Copy the token** (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Set Environment Variable

#### For Local Development:
```bash
export TELEGRAM_BOT_TOKEN="your-bot-token-here"
```

Or use a `.env` file (recommended):

```bash
cp .env.example .env
sed -i 's/YOUR_TELEGRAM_BOT_TOKEN/your-bot-token-here/' .env
```

Docker Compose will load `.env` automatically when you run `docker-compose up`.

#### For Render Cloud:
1. Go to your Render dashboard
2. Select your service (`perisai-api`)
3. Go to **Environment** tab
4. Add: `TELEGRAM_BOT_TOKEN` = `your-bot-token-here`
5. Save and redeploy

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the Server

```bash
# Local
uvicorn app_fastapi:app --host 0.0.0.0 --port 8000

# The Telegram bot will automatically start when TELEGRAM_BOT_TOKEN is set
```

### 5. Set Webhook (Production Only)

After deploying to Render, set the webhook URL:

```bash
# Visit this URL in your browser (replace with your actual domain):
https://perisai-api.onrender.com/telegram/set_webhook?webhook_url=https://perisai-api.onrender.com/telegram/webhook
```

Or use curl:
```bash
curl "https://perisai-api.onrender.com/telegram/set_webhook?webhook_url=https://perisai-api.onrender.com/telegram/webhook"
```

### 6. Test Your Bot! 🎉

1. Open Telegram
2. Search for your bot username (e.g., `@djppr_bond_bot`)
3. Send `/start`
4. Try queries:
   - `yield 10 year 2023-05-02`
   - `average yield Q1 2023`
   - `plot yield 10 year May 2023`

   ### Forecasting (tenor-only supported)

   - `forecast 10 year yield on 2025-12-17`
   - `forecast 10 year next 5 observations` (business-day aware)

   What the bot returns by default for generic yield forecasts:

   - **Tenor-only support**: If no `FRxx` series is specified, the bot averages across all series for the requested tenor per date.
   - **7 forecasting models**: ARIMA, ETS, RANDOM_WALK, MONTE_CARLO, MA5, VAR, PROPHET, plus AVERAGE (ensemble).
   - **Deep learning removed**: GRU and LSTM removed for faster deployments (~650 MB package size reduction).
   - **ARIMA reliability**: Improved 3-level fallback ensures valid forecasts always returned.
   - **Business-day horizons**: "Next N observations" automatically skip weekends (T+1=next Monday if last obs was Friday).
   - **Dual-message display**: (1) Latest 5 observations + per-horizon tables, (2) separator, (3) Kei's HL-CU analysis.
   - **Economist-style formatting**: Professional monospace tables with pipe delimiters.
   - **Ensemble average**: Computed after excluding negative values and 3×MAD outliers.
   - **Prophet safeguard**: Prophet forecasts clamped at zero to avoid negative yields.
   - **Stability**: Forecasts use the latest ~240 observations for robustness.

   Example response (single date, tenor-only):

   ```
   Forecasts for 10 year yield at 2025-12-17 (all series (averaged)):
   Model         | Forecast
   ---------------------------
   ARIMA        | 6.1647
   ETS          | 6.1494
   RANDOM_WALK  | 6.1630
   MONTE_CARLO  | 6.1474
   MA5          | 6.1746
   VAR          | 6.1648
   PROPHET      | 6.1829
   GRU          | 5.0783
   AVERAGE      | 6.1637

   Ensemble average: 6.1637
   ```

   ### Model Notes

   - **ARIMA**: 3-level fallback mechanism (get_forecast → fit.forecast → last observed value); always returns valid float.
   - **Prophet**: Forecasts clamped at 0.0 to avoid negative yields.
   - **Deep learning**: GRU and LSTM removed for faster deployments and smaller size.
   - **Ensemble**: Excludes negatives and 3×MAD outliers for robust averaging.
   - **Business days**: T+N horizons calculated using pandas.BDay (skips weekends automatically).

---

## 📱 Example Queries

### Point Queries (specific date):
- `yield 10 year 2023-05-02`
- `price 5 year on May 2 2023`
- `FR95 yield 2023-01-15`

### Range Queries (aggregation):
- `average yield Q1 2023`
- `avg yield 10 year May 2023`
- `max price 5 year 2023`

### Plot Queries (with charts):
- `plot yield 10 year 2023`
- `chart 5 year May 2023`
- `show yield Q2 2023`

---

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/telegram/webhook` | POST | Receives updates from Telegram |
| `/telegram/set_webhook` | GET | Configure webhook URL |
| `/telegram/webhook_info` | GET | Check webhook status |

---

## 🐛 Troubleshooting

### Bot not responding?

1. **Check if token is set:**
   ```bash
   curl https://perisai-api.onrender.com/health
   ```

2. **Check webhook status:**
   ```bash
   curl https://perisai-api.onrender.com/telegram/webhook_info
   ```

3. **Verify token with Telegram:**
   ```bash
   curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
   ```

### Local Development (without webhook):

For local testing, you can run the bot in polling mode instead of webhook mode. Create a separate file `run_telegram_bot.py`:

```python
import asyncio
from telegram_bot import create_telegram_app
import os

async def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not set")
        return
    
    app = create_telegram_app(token)
    
    # Remove webhook if set
    await app.bot.delete_webhook()
    
    # Start polling
    print("Starting bot in polling mode...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    # Keep running
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
```

Then run:
```bash
python run_telegram_bot.py
```

---

## 🔒 Security Notes

- ✅ Keep your bot token **secret**
- ✅ Never commit tokens to Git
- ✅ Use environment variables
- ✅ For production, restrict webhook to Telegram IPs

---

## 📊 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Show welcome message and help |
| `/examples` | Show example queries |

---

## 🚀 Deployment Checklist

- [ ] Create bot with @BotFather
- [ ] Set `TELEGRAM_BOT_TOKEN` in Render environment
- [ ] Deploy to Render
- [ ] Set webhook URL
- [ ] Test with `/start` command
- [ ] Share bot with team

---

## 📈 Usage Tips

1. **Natural language works!** Try "what's the yield of 10 year bonds on 2 May 2023"
2. **Plots are automatic** - just include "plot" or "chart" in your query
3. **Aggregations** - use "average", "max", "min" for summaries
4. **Quarters work** - try "Q1 2023" or "Q2 2023"
5. **Month names work** - "May 2023" or "January 2023"

---

## 🔄 Updates

To update the bot after code changes:

1. Push changes to Git
2. Render will auto-deploy (if connected to Git)
3. Bot automatically restarts
4. No need to reconfigure webhook

---

## 📞 Support

For issues or questions:
- Check logs in Render dashboard
- Test API endpoints with curl
- Verify webhook configuration

---

**Your Telegram bot is now ready! 🎉**

Start chatting with your bot in Telegram to get real-time bond data!
