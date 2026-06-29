# bot.py
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from core.config import Config
from core.database import init_db
# در مراحل بعدی هندلرها را از اینجا وارد می‌کنیم
# from handlers import start, buy, wallet, services, admin

# تنظیمات نمایش لاگ‌ها در ترمینال برای عیب‌یابی سریع
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

async def main():
    print("[..] Starting ZarVPN Telegram Bot...")
    
    # اطمینان از اینکه جداول دیتابیس ساخته شده‌اند
    await init_db()

    # راه‌اندازی ربات با توکن دریافتی و فرمت متون به صورت HTML
    bot = Bot(
        token=Config.BOT_TOKEN, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # دیسپچر (مدیریت‌کننده رویدادهای ربات)
    dp = Dispatcher()

    # ثبت هندلرهای ربات (در گام‌های بعدی تک‌تک این فایل‌ها را می‌نویسیم)
    # dp.include_routers(
    #     start.router,
    #     buy.router,
    #     wallet.router,
    #     services.router,
    #     admin.router
    # )

    print(f" [✓] Bot is now online and polling for messages!")
    
    # شروع گوش‌به‌زنگ بودن ربات برای پیام‌های جدید
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    # اجرای حلقه ناهمزمان ربات
    asyncio.run(main())
