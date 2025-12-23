"""Run Telegram bot in polling mode for local development.

This script runs the bot without webhooks, useful for testing locally.
"""
import asyncio
from telegram_bot import create_telegram_app
import os


async def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ Error: TELEGRAM_BOT_TOKEN environment variable not set")
        print("Set it with: export TELEGRAM_BOT_TOKEN='your-token-here'")
        return
    
    print("🤖 Starting Telegram bot in polling mode...")
    print("Press Ctrl+C to stop")
    
    app = create_telegram_app(token)
    
    # Remove webhook if previously set
    await app.bot.delete_webhook()
    print("✅ Webhook removed (using polling mode)")
    
    # Initialize and start
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    
    print("✅ Bot is running! Send messages on Telegram to test.")
    
    # Keep running until interrupted
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping bot...")
        await app.stop()
        await app.shutdown()
        print("✅ Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
