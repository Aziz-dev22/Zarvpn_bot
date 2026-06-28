import sqlite3
import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

router = Router()

# مسیر استاندارد دیتابیس پروژه شما
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "bot.db")
if not os.path.exists(os.path.dirname(DB_PATH)):
    DB_PATH = "bot.db"

@router.message(F.text == "🛍️ خرید اشتراک جدید")
async def show_services_menu(message: Message):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, name, size_gb, days, price FROM packages")
        packages = cursor.fetchall()
    except sqlite3.OperationalError:
        packages = []
    conn.close()
    
    if not packages:
        await message.answer("❌ در حال حاضر هیچ پکیجی برای فروش تعریف نشده است.")
        return
        
    keyboard = []
    text = "⚡ <b>لطفاً پکیج مورد نظر خود را برای خرید انتخاب کنید:</b>\n\n"
    
    for p in packages:
        text += f"🔹 <b>{p[1]}</b>\n حجم: {p[2]} گیگابایت | زمان: {p[3]} روز\n 💰 قیمت: {p[4]} تومان\n-------------------------\n"
        keyboard.append([InlineKeyboardButton(text=f"🛒 خرید {p[1]}", callback_query_data=f"buy_pkg_{p[0]}")])
        
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.callback_query(F.data.startswith("buy_pkg_"))
async def process_package_order(callback: CallbackQuery):
    package_id = callback.data.split("_")[2]
    await callback.answer("🔄 در حال پردازش سفارش... پروژه آماده دریافت اتصال سرور است.", show_alert=True)
