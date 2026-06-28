import jwt
import datetime
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from core.config import settings
from core.database import get_db_connection

router = Router()

@router.message(F.text == "/start")
async def start_cmd(message: Message):
    # ثبت یا بروزرسانی کاربر در دیتابیس
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)", 
        (message.from_user.id, message.from_user.username)
    )
    conn.commit()
    conn.close()

    # 🚀 اصلاح دکمه‌ها: برای دکمه‌های شیشه‌ای حتماً باید کالبک یا یو‌آر‌ال ست شود تا تلگرام ایراد نگیرد
    keyboard = [
        [InlineKeyboardButton(text="🛍️ خرید اشتراک جدید", callback_query_data="buy_service")],
        [InlineKeyboardButton(text="💰 کیف پول", callback_query_data="user_wallet")]
    ]

    # اگر کاربر ادمین بود، دکمه ورود مستقیم به وب‌پنل را اضافه کن
    if message.from_user.id in settings.admin_id_list:
        # ساخت توکن ایمن با انقضای ۱۰ دقیقه برای ورود بدون پسورد
        token = jwt.encode(
            {"admin_id": message.from_user.id, "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=10)},
            settings.SECRET_KEY, 
            algorithm="HS256"
        )
        # آدرس دهی بر اساس پورت جدید ۸۰۵۰ پروژه شما
        web_url = f"http://{message.text.split()[-1] if len(message.text.split()) > 1 else '178.105.165.200'}:8050/login/token?token={token}"
        keyboard.append([InlineKeyboardButton(text="⚙️ ورود مستقیم به پنل تحت وب", url=web_url)])

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer("🚀 <b>به ربات زار وی‌پی‌ان خوش آمدید!</b>\nلطفاً یکی از گزینه‌ها را انتخاب کنید:", reply_markup=markup)
