import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from core.config import settings
from core.database import init_db
from core.logger import logger
from handlers import start, wallet, referral, services, admin, callbacks

# استفاده از استوریج استاندارد برای جلوگیری از هنگی وضعیت‌ها
storage = MemoryStorage()
bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage)

async def on_startup():
    logger.info("Initializing database...")
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        sys.exit(1)

    dp.include_router(start.router)
    dp.include_router(wallet.router)
    dp.include_router(referral.router)
    dp.include_router(services.router)
    dp.include_router(admin.router)
    dp.include_router(callbacks.router)
    logger.info("Routers and handlers registered.")
    
    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, "🚀 <b>ربات زار وی‌پی‌ان آنلاین و آماده کار است!</b>")
        except Exception:
            pass

async def on_shutdown():
    await bot.session.close()

async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Critical error: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
