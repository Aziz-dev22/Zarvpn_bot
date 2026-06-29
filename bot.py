import asyncio
import sys
import os
import sqlite3
import uvicorn
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from core.config import settings
from core.database import init_db
from core.logger import logger
from web_panel import app

dp = Dispatcher()
DB_PATH = os.path.join(os.path.dirname(__file__), "bot.db")

# ==================== منوی اصلی ربات تلگرام ====================

@dp.message(F.text == "/start")
async def start_cmd(message: Message):
    user_id = message.from_user.id
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)", (user_id, message.from_user.username or "User"))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Database error: {e}")

    # دکمه‌های شیشه‌ای پایه کاربر با کالبک‌های مشخص
    keyboard = [
        [InlineKeyboardButton(text="🛍️ خرید اشتراک جدید", callback_query_data="buy_service")],
        [InlineKeyboardButton(text="💰 کیف پول / شارژ حساب", callback_query_data="user_wallet")]
    ]

    # اگر کاربر ادمین بود، دکمه ورود به پنل وب به شکل یک لینک داینامیک ساده اضافه می‌شود
    if str(user_id) in str(settings.ADMIN_IDS):
        # ساخت لینک ورود داینامیک بر اساس تنظیمات هر سرور بدون هاردکد کردن آی‌پی خاص
        panel_host = getattr(settings, 'WEB_HOST', '127.0.0.1')
        if panel_host == "0.0.0.0" and hasattr(settings, 'PANEL_URL') and settings.PANEL_URL:
            panel_url = settings.PANEL_URL
        else:
            panel_url = f"http://{panel_host}:8050/login"
            
        b_admin = InlineKeyboardButton(text="⚙️ ورود به پنل مدیریت وب", url=panel_url)
        keyboard.append([b_admin])

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer("🚀 <b>به ربات زار وی‌پی‌ان خوش آمدید!</b>\nلطفاً گزینه مورد نظر را انتخاب کنید:", reply_markup=markup)


# ==================== هندلر دکمه‌های شیشه‌ای کاربران ====================

@dp.callback_query(F.data == "buy_service")
async def buy_service(callback: CallbackQuery):
    await callback.message.answer("🛒 <b>بخش خرید اشتراک:</b>\nدر حال حاضر پکیجی تعریف نشده است. لطفاً از پنل وب اقدام به ثبت پکیج کنید.")
    await callback.answer()

@dp.callback_query(F.data == "user_wallet")
async def user_wallet(callback: CallbackQuery):
    await callback.message.answer("💰 <b>کیف پول شما:</b>\nموجودی حساب شما: 0 تومان")
    await callback.answer()


# ==================== رانر موازی وب پنل و ربات ====================

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
    
    # 🧹 تخلیه اجباری صف پیام‌های قدیمی برای ست شدن دکمه‌های جدید در کلاینت تلگرام
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("🤖 Telegram Bot polling started successfully.")
    await dp.start_polling(bot)

async def main():
    # ران کردن هم‌زمان وب پنل (جهت API و مرچنت) و ربات تلگرام
    await asyncio.gather(
        run_web(),
        run_bot()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Application closed by user.")
