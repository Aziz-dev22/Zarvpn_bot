from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.orm import Session

from core.config import settings
from core.database import SessionLocal, ServerPanel, Package, User
from core.logger import logger

router = Router()

# تعریف وضعیت‌ها برای ادمین (تعریف سرور و پکیج)
class AdminStates(StatesGroup):
    # مراحل اضافه کردن سرور
    ADD_SERVER_NAME = State()
    ADD_SERVER_URL = State()
    ADD_SERVER_USER = State()
    ADD_SERVER_PASS = State()
    
    # مراحل اضافه کردن پکیج
    ADD_PKG_TITLE = State()
    ADD_PKG_PRICE = State()
    ADD_PKG_VOLUME = State()
    ADD_PKG_DAYS = State()


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """منوی دکمه‌های پنل مدیریت ادمین"""
    buttons = [
        [
            InlineKeyboardButton(text="➕ افزودن سرور/پنل X-UI", callback_data="admin_add_server"),
            InlineKeyboardButton(text="🖥️ لیست سرورها", callback_data="admin_list_servers")
        ],
        [
            InlineKeyboardButton(text="➕ افزودن پکیج فروشی", callback_data="admin_add_package"),
            InlineKeyboardButton(text="📦 لیست پکیج‌ها", callback_data="admin_list_packages")
        ],
        [
            InlineKeyboardButton(text="📊 آمار کلی ربات", callback_data="admin_stats"),
            InlineKeyboardButton(text="🔙 منوی اصلی ربات", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "admin_panel")
async def show_admin_panel(callback: CallbackQuery, state: FSMContext):
    """ورود به پنل مدیریت (فقط برای ادمین‌های مجاز)"""
    await state.clear()
    tg_id = callback.from_user.id
    
    if tg_id not in settings.ADMIN_IDS:
        await callback.answer("❌ شما دسترسی به این بخش را ندارید.", show_alert=True)
        return
        
    text = "⚙️ <b>به پنل مدیریت ادمین زار وی‌پی‌ان خوش آمدید.</b>\n\nلطفاً از دکمه‌های زیر برای مدیریت ربات استفاده کنید:"
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard())
    await callback.answer()


# ================= SYSTEM ADD SERVER =================

@router.callback_query(F.data == "admin_add_server")
async def admin_add_server_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in settings.ADMIN_IDS: return
    
    await callback.message.edit_text(
        "🖥️ <b>گام اول:</b> یک نام مستعار برای این سرور وارد کنید:\n(مثال: سرور آلمان ۱)",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ انصراف", callback_data="admin_panel")]])
    )
    await state.set_state(AdminStates.ADD_SERVER_NAME)
    await callback.answer()

@router.message(AdminStates.ADD_SERVER_NAME)
async def admin_save_server_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("🔗 <b>گام دوم:</b> آدرس کامل پنل ثنایی (به همراه پورت) را وارد کنید:\n(مثال: http://185.2.3.4:2053)")
    await state.set_state(AdminStates.ADD_SERVER_URL)

@router.message(AdminStates.ADD_SERVER_URL)
async def admin_save_server_url(message: Message, state: FSMContext):
    await state.update_data(url=message.text.strip())
    await message.answer("👤 <b>گام سوم:</b> نام کاربری (Username) پنل را وارد کنید:")
    await state.set_state(AdminStates.ADD_SERVER_USER)

@router.message(AdminStates.ADD_SERVER_USER)
async def admin_save_server_user(message: Message, state: FSMContext):
    await state.update_data(username=message.text.strip())
    await message.answer("🔑 <b>گام آخر:</b> رمز عبور (Password) پنل را وارد کنید:")
    await state.set_state(AdminStates.ADD_SERVER_PASS)

@router.message(AdminStates.ADD_SERVER_PASS)
async def admin_save_server_final(message: Message, state: FSMContext):
    password = message.text.strip()
    data = await state.get_data()
    
    db: Session = SessionLocal()
    try:
        new_panel = ServerPanel(
            name=data['name'],
            panel_type="sanaei",
            url=data['url'],
            username=data['username'],
            password=password,
            is_active=True
        )
        db.add(new_panel)
        db.commit()
        await message.answer(f"✅ پنل <b>{data['name']}</b> با موفقیت در دیتابیس ثبت و فعال شد.", reply_markup=get_admin_keyboard())
    except Exception as e:
        logger.error(f"Error saving panel: {str(e)}")
        await message.answer("❌ خطایی در ذخیره پنل رخ داد.")
    finally:
        db.close()
        await state.clear()


# ================= SYSTEM ADD PACKAGE =================

@router.callback_query(F.data == "admin_add_package")
async def admin_add_package_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in settings.ADMIN_IDS: return
    
    await callback.message.edit_text(
        "📦 <b>گام اول:</b> عنوان پکیج را وارد کنید:\n(مثال: ۱ ماهه ۲۰ گیگ)",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ انصراف", callback_data="admin_panel")]])
    )
    await state.set_state(AdminStates.ADD_PKG_TITLE)
    await callback.answer()

@router.message(AdminStates.ADD_PKG_TITLE)
async def admin_save_pkg_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await message.answer("💰 <b>گام دوم:</b> قیمت پکیج را به <b>تومان</b> و فقط عدد وارد کنید:\n(مثال: 50000)")
    await state.set_state(AdminStates.ADD_PKG_PRICE)

@router.message(AdminStates.ADD_PKG_PRICE)
async def admin_save_pkg_price(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("❌ لطفاً قیمت را فقط به صورت عدد انگلیسی وارد کنید:")
        return
    await state.update_data(price=float(message.text.strip()))
    await message.answer("📊 <b>گام سوم:</b> میزان حجم مجاز را به <b>گیگابایت</b> وارد کنید (فقط عدد):\n(مثال: 20)")
    await state.set_state(AdminStates.ADD_PKG_VOLUME)

@router.message(AdminStates.ADD_PKG_VOLUME)
async def admin_save_pkg_volume(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("❌ لطفاً حجم را فقط عدد وارد کنید:")
        return
    await state.update_data(volume_gb=int(message.text.strip()))
    await message.answer("📅 <b>گام آخر:</b> تعداد روز اعتبار پکیج را وارد کنید:\n(مثال: 30)")
    await state.set_state(AdminStates.ADD_PKG_DAYS)

@router.message(AdminStates.ADD_PKG_DAYS)
async def admin_save_pkg_final(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("❌ لطفاً تعداد روز را فقط عدد وارد کنید:")
        return
    days = int(message.text.strip())
    data = await state.get_data()
    
    db: Session = SessionLocal()
    try:
        new_pkg = Package(
            title=data['title'],
            price=data['price'],
            volume_gb=data['volume_gb'],
            days=days,
            is_active=True
        )
        db.add(new_pkg)
        db.commit()
        await message.answer(f"✅ پکیج <b>{data['title']}</b> با موفقیت تعریف شد و در ربات قرار گرفت.", reply_markup=get_admin_keyboard())
    except Exception as e:
        logger.error(f"Error saving package: {str(e)}")
        await message.answer("❌ خطایی در ذخیره پکیج رخ داد.")
    finally:
        db.close()
        await state.clear()


# ================= LISTS & STATS =================

@router.callback_query(F.data == "admin_list_servers")
async def admin_list_servers(callback: CallbackQuery):
    if callback.from_user.id not in settings.ADMIN_IDS: return
    db: Session = SessionLocal()
    panels = db.query(ServerPanel).all()
    db.close()
    
    if not panels:
        await callback.answer("❌ هیچ سروری تعریف نشده است.", show_alert=True)
        return
        
    text = "🖥️ <b>لیست سرورهای متصل:</b>\n\n"
    for p in panels:
        status = "🟢 فعال" if p.is_active else "🔴 غیرفعال"
        text += f"▪️ نام: {p.name}\nآدرس: {p.url}\nوضعیت: {status}\n\n"
        
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard())

@router.callback_query(F.data == "admin_list_packages")
async def admin_list_packages(callback: CallbackQuery):
    if callback.from_user.id not in settings.ADMIN_IDS: return
    db: Session = SessionLocal()
    packages = db.query(Package).all()
    db.close()
    
    if not packages:
        await callback.answer("❌ هیچ پکیجی تعریف نشده است.", show_alert=True)
        return
        
    text = "📦 <b>لیست پکیج‌های تعریف شده:</b>\n\n"
    for pkg in packages:
        text += f"▪️ {pkg.title} | قیمت: {int(pkg.price):,} تومان | حجم: {pkg.volume_gb} گیگ | اعتبار: {pkg.days} روز\n"
        
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard())

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if callback.from_user.id not in settings.ADMIN_IDS: return
    db: Session = SessionLocal()
    total_users = db.query(User).count()
    total_servers = db.query(ServerPanel).count()
    db.close()
    
    text = (
        f"📊 <b>آمار کل سیستم زار وی‌پی‌ان</b>\n\n"
        f"👥 تعداد کل کاربران ربات: <b>{total_users} نفر</b>\n"
        f"🖥️ تعداد سرورهای متصل: <b>{total_servers} سرور</b>\n"
    )
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard())

