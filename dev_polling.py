import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from handlers import router
from config import BOT_TOKEN
from utils.logger import setup_logger

logger = setup_logger(__name__)

async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable is not set")
        sys.exit(1)
    
    logger.info("Starting Currency Rate Bot in polling mode (development)...")
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    dp = Dispatcher()
    dp.include_router(router)
    
    try:
        bot_info = await bot.get_me()
        logger.info(f"Bot started: @{bot_info.username} (ID: {bot_info.id})")
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook deleted (if was set)")
        logger.info("Starting polling... Press Ctrl+C to stop")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await bot.session.close()
        logger.info("Bot stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
