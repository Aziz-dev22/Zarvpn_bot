import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# ایمپورت تنظیمات و لایه‌های اصلی پروژه
from core.config import settings
from core.database import init_db
from core.logger import logger

# تعریف آبجکت‌های اصلی ربات و دیسپچر
bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

async def on_startup():
    """وظایفی که هنگام روشن شدن ربات باید انجام شوند"""
    logger.info("Initializing database...")
    try:
        # ساخت جدول‌های دیتابیس در صورت عدم وجود
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        sys.exit(1)

    logger.info("ZarVPN Bot is starting up...")
    
    # اطلاع‌رسانی به ادمین‌های ربات جهت آنلاین شدن سیستم
    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, "🚀 <b>ربات زار وی‌پی‌ان با موفقیت آنلاین شد!</b>")
        except Exception:
            # اگر ادمین هنوز ربات را استارت نکرده باشد، خطا لاگ می‌شود ولی ربات متوقف نمی‌شود
            logger.warning(f"Could not send startup message to admin {admin_id}. Has the admin started the bot?")

async def on_shutdown():
    """وظایفی که هنگام خاموش شدن ربات باید انجام شوند"""
    logger.info("ZarVPN Bot is shutting down...")
    await bot.session.close()
    logger.info("Bot session closed.")

async def main():
    # ثبت متدهای استارتاپ و شات‌داون در دیسپچر
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # تایید و ثبت هندلرهای ربات (در گام‌های بعدی هندلرها را به اینجا اضافه می‌کنیم)
    # از اینجا به بعد ربات شروع به گوش دادن به پیام‌ها می‌کند
    try:
        # حذف وبهوک‌های قبلی و شروع پولینگ (Polling)
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Critical error in main loop: {str(e)}")

if __name__ == "__main__":
    # اجرای حلقه اصلی برنامه به صورت Async
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user.")

