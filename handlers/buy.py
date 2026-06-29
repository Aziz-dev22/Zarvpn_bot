# handlers/buy.py
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.future import select

from core.database import AsyncSessionLocal
from database.models import InboundPanel, Package, User

router = Router()

# تعریف وضعیت‌های گام‌به‌گام خرید
class BuySteps(StatesGroup):
    choose_panel = State()
    choose_package = State()

@router.message(F.text == "🛍️ خرید اشتراک جدید")
async def start_buy_process(message: types.Message, state: FSMContext):
    async with AsyncSessionLocal() as db:
        # دریافت لیست سرورهای فعال از دیتابیس
        result = await db.execute(select(InboundPanel).where(InboundPanel.is_active == True))
        panels = result.scalars().all()
        
        if not panels:
            await message.answer("❌ در حال حاضر هیچ سرور فعالی برای خرید وجود ندارد. لطفا بعداً تلاش کنید یا به پشتیبانی پیام دهید.")
            return

        # ساخت دکمه‌های شیشه‌ای برای انتخاب سرور
        builder = InlineKeyboardBuilder()
        for panel in panels:
            builder.button(text=f"🌐 {panel.name}", callback_data=f"buy_panel_{panel.id}")
        
        builder.adjust(1)
        await message.answer("لطفاً لوکیشن یا سرور مورد نظر خود را انتخاب کنید:", reply_markup=builder.as_markup())
        await state.set_state(BuySteps.choose_panel)

@router.callback_query(F.data.startswith("buy_panel_"), BuySteps.choose_panel)
async def select_panel_callback(callback: types.CallbackQuery, state: FSMContext):
    panel_id = int(callback.data.split("_")[2])
    await state.update_data(selected_panel_id=panel_id)
    
    async with AsyncSessionLocal() as db:
        # دریافت پکیج‌های فعال از دیتابیس
        result = await db.execute(select(Package).where(Package.is_active == True))
        packages = result.scalars().all()
        
        if not packages:
            await callback.message.answer("❌ هیچ پکیج فروشی تعریف نشده است.")
            await state.clear()
            return
            
        builder = InlineKeyboardBuilder()
        for pkg in packages:
            builder.button(text=f"📦 {pkg.name} - {pkg.price:,.0f} تومان", callback_data=f"buy_pkg_{pkg.id}")
            
        builder.adjust(1)
        await callback.message.edit_text("حالا پکیج حجمی و زمانی مد نظر خود را انتخاب کنید:", reply_markup=builder.as_markup())
        await state.set_state(BuySteps.choose_package)

@router.callback_query(F.data.startswith("buy_pkg_"), BuySteps.choose_package)
async def select_package_callback(callback: types.CallbackQuery, state: FSMContext):
    pkg_id = int(callback.data.split("_")[2])
    user_data = await state.get_data()
    panel_id = user_data.get("selected_panel_id")
    
    async with AsyncSessionLocal() as db:
        # بررسی پکیج انتخاب شده
        pkg_result = await db.execute(select(Package).where(Package.id == pkg_id))
        package = pkg_result.scalar_one_or_none()
        
        # بررسی مشخصات سرور
        panel_result = await db.execute(select(InboundPanel).where(InboundPanel.id == panel_id))
        panel = panel_result.scalar_one_or_none()
        
        # بررسی موجودی کاربر
        user_result = await db.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = user_result.scalar_one_or_none()
        
        if not package or not panel or not user:
            await callback.message.edit_text("❌ خطایی در پردازش اطلاعات رخ داد. لطفاً فرآیند خرید را مجدد شروع کنید.")
            await state.clear()
            return
            
        # بررسی اجمالی فاکتور قبل از کسر موجودی یا هدایت به درگاه
        fact_text = (
            f"🧾 **پیش‌فاکتور خرید اشتراک**\n\n"
            f"🌐 سرور انتخاب شده: {panel.name}\n"
            f"📦 پکیج: {package.name}\n"
            f"⏳ اعتبار: {package.expiry_days} روز\n"
            f"💾 حجم: {package.volume_gb} گیگابایت\n"
            f"💰 مبلغ کل: {package.price:,.0f} تومان\n\n"
            f"💳 موجودی فعلی شما: {user.balance:,.0f} تومان\n"
        )
        
        builder = InlineKeyboardBuilder()
        if user.balance >= package.price:
            fact_text += "\n✅ موجودی شما کافی است. با کلیک بر روی دکمه زیر، سرویس شما ساخته خواهد شد."
            builder.button(text="🚀 پرداخت از موجودی و تحویل سرویس", callback_data=f"pay_wallet_{panel.id}_{pkg.id}")
        else:
            fact_text += "\n❌ موجودی شما کافی نیست. جهت خرید باید ابتدا کیف پول خود را شارژ کنید یا مستقیم از درگاه صرافی پرداخت کنید."
            builder.button(text="💳 شارژ آنلاین و پرداخت", callback_data=f"pay_online_{panel.id}_{pkg.id}")
            
        await callback.message.edit_text(fact_text, reply_markup=builder.as_markup())
        await state.clear() # خروج از حالت وضعیت پس از نمایش پیش فاکتور

