import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import uvicorn

from core.config import settings
from core.database import init_db
from core.logger import logger
from handlers import start
from web_panel import app

async def run_web():
    logger.info("🌐 Starting Web Panel on port 8050...")
    config = uvicorn.Config(app, host=settings.WEB_HOST, port=settings.WEB_PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def run_bot():
    logger.info("📦 Initializing database tables...")
    init_db()
    
    if not settings.BOT_TOKEN:
        logger.critical("❌ BOT_TOKEN found empty in .env file!")
        sys.exit(1)
        
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    # ثبت روتر اصلی ربات
    dp.include_router(start.router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("🤖 Telegram Bot polling started successfully.")
    await dp.start_polling(bot)

async def main():
    # اجرای کاملاً مجزا و موازی همزمان وب‌پنل و ربات
    await asyncio.gather(
        run_web(),
        run_bot()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Application closed by user.")
