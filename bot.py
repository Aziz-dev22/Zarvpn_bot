import asyncio
import sys
import jwt
import datetime
import sqlite3
import os
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

    # ✅ تعریف دکمه‌های شیشه‌ای استاندارد با callback_query_data مجزا
    b1 = InlineKeyboardButton(text="🛍️ خرید اشتراک جدید", callback_query_data="buy_service")
    b2 = InlineKeyboardButton(text="💰 کیف پول", callback_query_data="user_wallet")
    keyboard = [[b1], [b2]]

    # بررسی ادمین بودن
    if str(user_id) in str(settings.ADMIN_IDS):
        try:
            token = jwt.encode(
                {"admin_id": user_id, "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=15)},
                settings.SECRET_KEY, 
                algorithm="HS256"
            )
            # 🔐 اصلاح امنیتی: به جای آی‌پی ثابت، آدرس از فایل تنظیمات سرور خوانده می‌شود
            panel_host = getattr(settings, 'WEB_HOST', '178.105.165.200')
            if panel_host == "0.0.0.0":
                panel_host = "178.105.165.200"  # آی‌پی سرور شما برای اتصال خارج از سرور
                
            web_url = f"http://{panel_host}:8050/login/token?token={token}"
            b_admin = InlineKeyboardButton(text="⚙️ ورود مستقیم به پنل تحت وب", url=web_url)
            keyboard.append([b_admin])
        except Exception as e:
            logger.error(f"Error creating admin token: {e}")

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer("🚀 <b>به ربات زار وی‌پی‌ان خوش آمدید!</b>\nلطفاً گزینه مورد نظر را انتخاب کنید:", reply_markup=markup)

# ✅ هندلر پردازش کلیک روی دکمه‌های شیشه‌ای (کالبک‌ها)
@dp.callback_query()
async def handle_callbacks(callback: CallbackQuery):
    if callback.data == "buy_service":
        await callback.message.answer("🛒 <b>بخش خرید اشتراک:</b>\nدر حال حاضر پکیجی تعریف نشده است. از پنل وب اقدام به ثبت پکیج کنید.")
    elif callback.data == "user_wallet":
        await callback.message.answer("💰 <b>کیف پول شما:</b>\nموجودی حساب شما: 0 تومان")
    
    # اعلام پایان لودینگ دکمه به تلگرام
    await callback.answer()

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
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("🤖 Telegram Bot polling started successfully.")
    await dp.start_polling(bot)

async def main():
    await asyncio.gather(
        run_web(),
        run_bot()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Application closed by user.")
