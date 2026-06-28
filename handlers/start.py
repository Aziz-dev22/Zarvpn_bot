import jwt
import datetime
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from core.config import settings
from core.database import get_db_connection

router = Router()

@router.message(F.text == "/start")
async def start_cmd(message: Message):
    # ثبت کاربر در دیتابیس در صورت عدم وجود
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)", 
                   (message.from_user.id, message.from_user.username))
    conn.commit()
    conn.close()

    keyboard = [
        [InlineKeyboardButton(text="🛍️ خرید اشتراک جدید", callback_query_data="buy_service")],
        [InlineKeyboardButton(text="💰 کیف پول", callback_query_data="user_wallet")]
    ]

    # اگر کاربر ادمین بود، دکمه ورود مستقیم به وب‌پنل شیک را نشان بده
    if message.from_user.id in settings.admin_id_list:
        # ساخت توکن ورود بدون پسورد با انقضای ۱۰ دقیقه
        token = jwt.encode(
            {"admin_id": message.from_user.id, "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=10)},
            settings.SECRET_KEY, algorithm="HS256"
        )
        web_url = f"http://{settings.WEB_HOST}:{settings.WEB_PORT}/login/token?token={token}"
        keyboard.append([InlineKeyboardButton(text="⚙️ ورود مستقیم به پنل تحت وب", url=web_url)])

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer("🚀 <b>به ربات ZARVPN خوش آمدید!</b>\nلطفاً یکی از گزینه‌ها را انتخاب کنید:", reply_markup=markup)
