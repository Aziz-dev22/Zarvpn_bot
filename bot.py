# bot.py
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from core.config import Config
from core.database import init_db
# وارد کردن تمامی هندلرهای پروژه به صورت یکجا
from handlers import start, buy, callbacks, wallet, services, support

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

async def main():
    print("[..] Starting ZarVPN Telegram Bot...")
    await init_db()

    bot = Bot(
        token=Config.BOT_TOKEN, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()

    # ثبت نهایی تمامی روترهای ربات در دیسپچر اصلی
    dp.include_routers(
        start.router,
        buy.router,
        callbacks.router,
        wallet.router,
        services.router,
        support.router
    )

    print(f" [✓] Bot is now online and polling for messages!")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
