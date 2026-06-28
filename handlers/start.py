import jwt
import datetime
import sqlite3
import os
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from core.config import settings

router = Router()

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bot.db")

@router.message(F.text == "/start")
async def start_cmd(message: Message):
    # ثبت کاربر در دیتابیس
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)", 
            (message.from_user.id, message.from_user.username)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

    # ساخت دکمه‌های شیشه‌ای با ساختار ۱۰۰٪ استاندارد و اجباری callback_query_data
    btn_buy = InlineKeyboardButton(text="🛍️ خرید اشتراک جدید", callback_query_data="buy_service")
    btn_wallet = InlineKeyboardButton(text="💰 کیف پول", callback_query_data="user_wallet")
    
    keyboard = [
        [btn_buy],
        [btn_wallet]
    ]

    # بررسی وضعیت ادمین برای نمایش دکمه وب‌پنل
    if message.from_user.id in settings.admin_id_list:
        token = jwt.encode(
            {"admin_id": message.from_user.id, "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=10)},
            settings.SECRET_KEY, 
            algorithm="HS256"
        )
        # ست کردن مستقیم آی‌پی سرور شما روی پورت ۸۰۵۰ برای وب‌پنل
        web_url = f"http://178.105.165.200:8050/login/token?token={token}"
        btn_admin = InlineKeyboardButton(text="⚙️ ورود مستقیم به پنل تحت وب", url=web_url)
        keyboard.append([btn_admin])

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(
        "🚀 <b>به ربات زار وی‌پی‌ان خوش آمدید!</b>\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:", 
        reply_markup=markup
    )
