import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web
from handlers import router
from config import BOT_TOKEN, WEBHOOK_URL, PORT
from utils.logger import setup_logger

logger = setup_logger(__name__)

def validate_config():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable is not set")
        sys.exit(1)
    if not WEBHOOK_URL:
        logger.error("WEBHOOK_URL environment variable is not set")
        sys.exit(1)
    logger.info(f"Configuration validated. Webhook URL: {WEBHOOK_URL}")

def create_app() -> web.Application:
    validate_config()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    dp = Dispatcher()
    dp.include_router(router)
    dp["bot"] = bot
    
    webhook_path = "/webhook"
    webhook_full_url = f"{WEBHOOK_URL}{webhook_path}"
    logger.info(f"Setting up webhook at: {webhook_full_url}")
    
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    app = web.Application()
    webhook_requests_handler.register(app, path=webhook_path)
    
    async def on_startup(app: web.Application):
        try:
            await bot.set_webhook(url=webhook_full_url, drop_pending_updates=True)
            logger.info(f"Webhook set successfully: {webhook_full_url}")
            bot_info = await bot.get_me()
            logger.info(f"Bot started: @{bot_info.username} (ID: {bot_info.id})")
        except Exception as e:
            logger.error(f"Failed to set webhook: {e}", exc_info=True)
            raise
    
    async def on_shutdown(app: web.Application):
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("Webhook deleted")
            await bot.session.close()
            logger.info("Bot session closed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)
    
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    async def health_check(request: web.Request):
        return web.json_response({"status": "ok"})
    
    app.router.add_get("/health", health_check)
    app.router.add_get("/", health_check)
    return app

def main():
    try:
        logger.info("Starting Currency Rate Bot in webhook mode...")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Port: {PORT}")
        app = create_app()
        web.run_app(app, host="0.0.0.0", port=PORT, print=None, access_log=logger)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
