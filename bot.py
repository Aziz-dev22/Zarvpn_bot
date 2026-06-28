import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import uvicorn

from core.config import settings
from core.database import init_db
from core.logger import logger
from handlers import start
from web_panel import app

async def run_bot():
    init_db()
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    dp.include_router(start.router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("🤖 Telegram Bot is running...")
    await dp.start_polling(bot)

def run_web():
    logger.info("🌐 Web Panel is starting...")
    uvicorn.run(app, host=settings.WEB_HOST, port=settings.WEB_PORT)

if __name__ == "__main__":
    # اجرای همزمان ربات تلگرام و وب‌پنل ادمین روی سرور
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, run_web)
    loop.run_until_complete(run_bot())
