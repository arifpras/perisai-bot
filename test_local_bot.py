#!/usr/bin/env python3
"""Run Telegram bot locally in polling mode for testing."""
import asyncio
import os
from telegram_bot import create_telegram_app

async def main():
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not set")
        return
    if not openai_key:
        print("⚠️  OPENAI_API_KEY not set - /ask_admin will not work")
    else:
        print("✅ OPENAI_API_KEY is set")
    
    print(f"🤖 Starting bot in polling mode...")
    app = create_telegram_app(bot_token)
    
    async with app:
        await app.initialize()
        await app.start()
        print("✅ Bot is running! Press Ctrl+C to stop.")
        await app.updater.start_polling()
        await asyncio.Event().wait()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped")
