import asyncio
import sys
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

@dp.message(F.text == "/start")
async def start_cmd(message: Message):
    user_id = message.from_user.id

    # دکمه‌های شیشه‌ای استاندارد با کالبک دیتای معتبر
    b1 = InlineKeyboardButton(text="🛍️ خرید اشتراک جدید", callback_query_data="buy_service")
    b2 = InlineKeyboardButton(text="💰 کیف پول", callback_query_data="user_wallet")
    keyboard = [[b1], [b2]]

    # بررسی ادمین بودن (بدون هاردکد کردن آی‌پی یا توکن خودکار)
    if str(user_id) in str(settings.ADMIN_IDS):
        # ساخت لینک پنل با پورت ۸۰۵۰ بدون نیاز به آی‌پی ثابت در کد (کاملاً داینامیک برای ۱۰۰۰ سرور)
        panel_url = f"http://{settings.WEB_HOST if settings.WEB_HOST != '0.0.0.0' else '127.0.0.1'}:8050/login"
        
        # نکته: اگر کاربر بیرون از سرور مایل به ورود است، از آدرس ست شده در تنظیمات استفاده می‌شود
        if hasattr(settings, 'PANEL_URL') and settings.PANEL_URL:
            panel_url = settings.PANEL_URL
            
        b_admin = InlineKeyboardButton(text="⚙️ ورود به پنل مدیریت وب", url=panel_url)
        keyboard.append([b_admin])

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer(
        "🚀 <b>به ربات زار وی‌پی‌ان خوش آمدید!</b>\nلطفاً گزینه مورد نظر را انتخاب کنید:", 
        reply_markup=markup
    )

# هندلر پردازش دقیق کلیک روی دکمه‌ها
@dp.callback_query(F.data == "buy_service")
async def buy_service_callback(callback: CallbackQuery):
    await callback.message.answer("🛒 <b>بخش خرید اشتراک:</b>\nدر حال حاضر پکیجی تعریف نشده است. لطفاً از پنل وب اقدام به ثبت پکیج کنید.")
    await callback.answer()

@dp.callback_query(F.data == "user_wallet")
async def wallet_callback(callback: CallbackQuery):
    await callback.message.answer("💰 <b>کیف پول شما:</b>\nموجودی حساب شما: 0 تومان")
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
    
    # حل مشکل کش شدن دکمه‌های قدیمی در سرور تلگرام با پاکسازی اجباری صف
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
