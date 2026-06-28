import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# ایمپورت تنظیمات و لایه‌های اصلی پروژه
from core.config import settings
from core.database import init_db
from core.logger import logger

# ایمپورت روترهای هندلرها
from handlers import start, wallet, referral, services, admin, callbacks

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

    # ثبت روترها (هندلرهای ربات)
    dp.include_router(start.router)
    dp.include_router(wallet.router)
    dp.include_router(referral.router)
    dp.include_router(services.router)
    dp.include_router(admin.router)
    dp.include_router(callbacks.router)
    logger.info("Routers and handlers registered.")

    logger.info("ZarVPN Bot is starting up...")
    
    # اطلاع‌رسانی به ادمین‌های ربات جهت آنلاین شدن سیستم
    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, "🚀 <b>ربات زار وی‌پی‌ان با موفقیت آنلاین شد!</b>")
        except Exception:
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

    try:
        # حذف وبهوک‌های قبلی و شروع پولینگ (Polling)
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Critical error in main loop: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user.")
