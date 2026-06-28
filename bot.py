import asyncio
from aiogram import Bot, Dispatcher
from core.config import settings
from core.logger import logger

# وارد کردن هندلرهای مختلف ربات شما
from handlers import start, wallet, referral
from handlers import admin as admin_handlers
from handlers import services as services_handlers

async def main():
    logger.info("Initializing database...")
    # در صورت داشتن اسکریپت اولیه دیتابیس اینجا اجرا می‌شود
    logger.info("Database initialized successfully.")

    # راه‌اندازی ربات با توکن دریافتی از کانفیگ
    bot = Bot(token=settings.BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher()

    # 🚀 ثبت روترها در دیسپچر ربات (ترتیب ثبت مهم است)
    dp.include_router(start.router)
    dp.include_router(wallet.router)
    dp.include_router(referral.router)
    dp.include_router(admin_handlers.router)    # اتصال پنل مدیریت شیشه‌ای جدید
    dp.include_router(services_handlers.router) # اتصال منوی خرید شیشه‌ای پکیج‌ها

    logger.info("Routers and handlers registered successfully.")

    try:
        # حذف وبهوک‌های احتمالی قبلی و شروع فچ کردن زنده پیام‌ها
        await bot.delete_webhook(drop_pending_updates=True)
        print("🤖 ZarVPN Bot is Online and Running...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Bot crashed: {str(e)}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
