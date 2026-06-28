from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from core.database import get_db_connection
from aiogram.exceptions import TelegramBadRequest

router = Router()

@router.message(F.text == "🛍️ خرید اشتراک جدید")
async def show_services_menu(message: Message):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, size_gb, days, price FROM packages")
    packages = cursor.fetchall()
    conn.close()
    
    if not packages:
        await message.answer("❌ در حال حاضر هیچ پکیجی برای فروش تعریف نشده است.")
        return
        
    keyboard = []
    text = "⚡ <b>لطفاً پکیج مورد نظر خود را برای خرید انتخاب کنید:</b>\n\n"
    
    for p in packages:
        text += f"🔹 <b>{p[1]}</b>\n حجم: {p[2]} گیگابایت | زمان: {p[3]} روز\n 💰 قیمت: {p[4]} تومان\n-------------------------\n"
        # اضافه کردن هر پکیج به صورت دکمه شیشه‌ای کپی مجزا
        keyboard.append([InlineKeyboardButton(text=f"🛒 خرید {p[1]}", callback_query_data=f"buy_pkg_{p[0]}")])
        
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.callback_query(F.data.startswith("buy_pkg_"))
async def process_package_order(callback: CallbackQuery):
    package_id = callback.data.split("_")[2]
    
    # در اینجا منطق کسر از کیف پول و وصل شدن به متد create_user در فایل sanaei.py شما اجرا می‌شود
    await callback.answer("🔄 در حال پردازش سفارش و ساخت کانکشن...", show_alert=True)
    
    # کدهای مربوط به ساخت نهایی در پروژه شما از این متغیر استفاده می‌کنند.
