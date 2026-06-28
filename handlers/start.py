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
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"

    # ۱. ثبت یا آپدیت کاربر در دیتابیس با مدیریت خطا
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)", 
            (user_id, username)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

    # ۲. ساخت دکمه‌های شیشه‌ای پایه و استاندارد برای همه کاربران
    keyboard = [
        [InlineKeyboardButton(text="🛍️ خرید اشتراک جدید", callback_query_data="buy_service")],
        [InlineKeyboardButton(text="💰 کیف پول", callback_query_data="user_wallet")]
    ]

    # ۳. بررسی وضعیت ادمین به صورت کاملاً منعطف (هم به صورت لیست و هم متن ساده)
    is_admin = False
    try:
        # بررسی اینکه آیا آیدی کاربر در متغیر ادمین‌های تنظیمات هست یا خیر
        if hasattr(settings, 'admin_id_list') and user_id in settings.admin_id_list:
            is_admin = True
        elif hasattr(settings, 'ADMIN_IDS') and str(user_id) in str(settings.ADMIN_IDS):
            is_admin = True
    except Exception:
        pass

    # ۴. اگر کاربر ادمین بود، دکمه ورود به وب‌پنل را با توکن ۱۰ دقیقه‌ای بساز
    if is_admin:
        try:
            token = jwt.encode(
                {"admin_id": user_id, "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=10)},
                settings.SECRET_KEY, 
                algorithm="HS256"
            )
            # لینک مستقیم به وب‌پنل روی پورت ۸۰۵۰ سرور شما
            web_url = f"http://178.105.165.200:8050/login/token?token={token}"
            keyboard.append([InlineKeyboardButton(text="⚙️ ورود مستقیم به پنل تحت وب", url=web_url)])
        except Exception:
            pass

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(
        "🚀 <b>به ربات زار وی‌پی‌ان خوش آمدید!</b>\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:", 
        reply_markup=markup
    )
