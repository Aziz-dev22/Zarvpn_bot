from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

from core.config import settings
from core.database import get_db_connection
from panels.sanaei import SanaeiPanel
from core.logger import logger

router = Router()

class AdminStates(StatesGroup):
    waiting_for_server_data = State()
    waiting_for_package_data = State()

def get_admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🖥️ مدیریت سرورها", callback_query_data="admin_servers")],
        [InlineKeyboardButton(text="📦 مدیریت پکیج‌ها", callback_query_data="admin_packages")],
        [InlineKeyboardButton(text="❌ بستن پنل", callback_query_data="close_admin")]
    ])

@router.message(F.text == "/admin")
async def admin_panel(message: Message):
    if message.from_user.id not in settings.ADMIN_IDS:
        return
    await message.answer("⚙️ <b>به پنل مدیریت زار وی‌پی‌ان خوش آمدید:</b>", reply_markup=get_admin_keyboard())

@router.callback_query(F.data == "admin_servers")
async def list_servers(callback: CallbackQuery):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, url FROM servers")
    servers = cursor.fetchall()
    conn.close()

    keyboard = []
    text = "🖥️ <b>لیست سرورهای متصل:</b>\n\n"
    
    if not servers:
        text += "هیچ سروری ثبت نشده است."
    for s in servers:
        text += f"🔹 نام: {s[1]}\n🔗 آدرس: {s[2]}\n\n"
        keyboard.append([InlineKeyboardButton(text=f"🗑️ حذف {s[1]}", callback_query_data=f"del_srv_{s[0]}")])
    
    keyboard.append([InlineKeyboardButton(text="➕ افزودن سرور جدید", callback_query_data="add_server")])
    keyboard.append([InlineKeyboardButton(text="🔙 بازگشت", callback_query_data="back_to_admin")])
    
    try:
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    except TelegramBadRequest:
        await callback.answer()

@router.callback_query(F.data == "add_server")
async def add_server_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📝 لطفاً اطلاعات سرور را <b>دقیقاً</b> به فرمت زیر ارسال کنید:\n\n"
        "`نام سرور|آدرس پنل با پورت|یوزرنیم|پسورد`\n\n"
        "مثال:\n`Server1|http://178.105.165.200:2054|admin|admin123`",
        parse_mode="Markdown"
    )
    await state.set_state(AdminStates.waiting_for_server_data)

@router.message(AdminStates.waiting_for_server_data)
async def save_server(message: Message, state: FSMContext):
    if message.from_user.id not in settings.ADMIN_IDS:
        return
    
    try:
        parts = message.text.split("|")
        if len(parts) != 4:
            await message.answer("❌ فرمت ارسال اشتباه است. دوباره تلاش کنید.")
            return
        
        name, url, user, password = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()
        
        status_msg = await message.answer("🔄 <b>در حال بررسی و تست اتصال به پنل ثنایی...</b>")
        
        # تست اتصال واقعی با کدهای جدید sanaei.py
        panel = SanaeiPanel(url, user, password)
        login_success = await panel.login()
        await panel.close()
        
        if not login_success:
            await status_msg.edit_text("❌ <b>خطا در اتصال!</b> مشخصات ورود، آدرس یا پورت اشتباه است و پنل درخواست را رد کرد.")
            await state.clear()
            return
            
        # ذخیره در دیتابیس در صورت تایید مشخصات
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO servers (name, url, username, password) VALUES (?, ?, ?, ?)",
            (name, url, user, password)
        )
        conn.commit()
        conn.close()
        
        await status_msg.edit_text(f"✅ سرور <b>{name}</b> با موفقیت تست، تایید و متصل شد!")
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ خطای غیرمنتظره: {str(e)}")
        await state.clear()

@router.callback_query(F.data.startswith("del_srv_"))
async def delete_server(callback: CallbackQuery):
    server_id = callback.data.split("_")[2]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM servers WHERE id = ?", (server_id,))
    conn.commit()
    conn.close()
    await callback.answer("✅ سرور حذف شد")
    await list_servers(callback)

@router.callback_query(F.data == "admin_packages")
async def list_packages(callback: CallbackQuery):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, size_gb, days, price FROM packages")
    packages = cursor.fetchall()
    conn.close()

    keyboard = []
    text = "📦 <b>لیست پکیج‌های فروشی ربات:</b>\n\n"
    
    if not packages:
        text += "هیچ پکیجی تعریف نشده است."
    for p in packages:
        text += f"📦 پکیج: {p[1]} | حجم: {p[2]} گیگ | زمان: {p[3]} روز | قیمت: {p[4]} تومان\n\n"
        keyboard.append([InlineKeyboardButton(text=f"🗑️ حذف پکیج {p[1]}", callback_query_data=f"del_pkg_{p[0]}")])
        
    keyboard.append([InlineKeyboardButton(text="➕ افزودن پکیج جدید", callback_query_data="add_package")])
    keyboard.append([InlineKeyboardButton(text="🔙 بازگشت", callback_query_data="back_to_admin")])
    
    try:
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    except TelegramBadRequest:
        await callback.answer()

@router.callback_query(F.data == "add_package")
async def add_package_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📝 اطلاعات پکیج جدید را به فرمت زیر بفرستید:\n\n"
        "`نام پکیج|حجم به گیگ|تعداد روز|قیمت به تومان`\n\n"
        "مثال:\n`پکیج نقره‌ای|30|30|50000`",
        parse_mode="Markdown"
    )
    await state.set_state(AdminStates.waiting_for_package_data)

@router.message(AdminStates.waiting_for_package_data)
async def save_package(message: Message, state: FSMContext):
    if message.from_user.id not in settings.ADMIN_IDS:
        return
    try:
        parts = message.text.split("|")
        if len(parts) != 4:
            await message.answer("❌ فرمت اشتباه است. دوباره تلاش کنید.")
            return
        
        name, size, days, price = parts[0].strip(), int(parts[1]), int(parts[2]), int(parts[3])
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO packages (name, size_gb, days, price) VALUES (?, ?, ?, ?)",
            (name, size, days, price)
        )
        conn.commit()
        conn.close()
        
        await message.answer(f"✅ پکیج <b>{name}</b> با موفقیت اضافه شد.")
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ خطا در قالب اعداد وارد شده: {str(e)}")
        await state.clear()

@router.callback_query(F.data.startswith("del_pkg_"))
async def delete_package(callback: CallbackQuery):
    pkg_id = callback.data.split("_")[2]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM packages WHERE id = ?", (pkg_id,))
    conn.commit()
    conn.close()
    await callback.answer("✅ پکیج حذف شد")
    await list_packages(callback)

@router.callback_query(F.data == "back_to_admin")
async def back_to_admin(callback: CallbackQuery):
    try:
        await callback.message.edit_text("⚙️ <b>به پنل مدیریت زار وی‌پی‌ان خوش آمدید:</b>", reply_markup=get_admin_keyboard())
    except TelegramBadRequest:
        await callback.answer()

@router.callback_query(F.data == "close_admin")
async def close_admin(callback: CallbackQuery):
    await callback.message.delete()
