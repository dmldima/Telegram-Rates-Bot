import os
from aiogram import Bot, Dispatcher
from aiohttp import web
from handlers import router

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

bot = Bot(token=BOT_TOKEN)

def create_app() -> web.Application:
    dp = Dispatcher()
    dp.include_router(router)
    app = web.Application()
    dp.webhook.register(app)

    async def on_startup(app: web.Application):
        await bot.set_webhook(WEBHOOK_URL)

    async def on_shutdown(app: web.Application):
        await bot.delete_webhook()

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    return app

if __name__ == "__main__":
    web.run_app(create_app(), host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
