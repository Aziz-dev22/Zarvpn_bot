# handlers/wallet.py
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.future import select

from core.database import AsyncSessionLocal
from database.models import User, Gateway

router = Router()

# وضعیت‌های ماشین حالت برای گرفتن مبلغ شارژ
class WalletStates(StatesGroup):
    amount = State()

@router.message(F.text == "💳 کیف پول / شارژ")
async def show_wallet(message: types.Message):
    async with AsyncSessionLocal() as db:
        # دریافت اطلاعات و موجودی کاربر از دیتابیس
        result = await db.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar_one_or_none()
        
        if not user:
            await message.answer("❌ حساب کاربری شما یافت نشد. لطفاً مجدداً ربات را /start کنید.")
            return
            
        wallet_text = (
            f"💳 **وضعیت کیف پول شما**\n\n"
            f"👤 نام کاربری: {user.full_name}\n"
            f"💰 موجودی فعلی: **{user.balance:,.0f} تومان**\n\n"
            f"📌 شما با شارژ کیف پول خود می‌توانید هر زمان که خواستید بدون معطلی اشتراک جدید خریداری کنید یا سرویس‌های خود را تمدید کنید."
        )
        
        builder = InlineKeyboardBuilder()
        builder.button(text="➕ افزایش موجودی / شارژ حساب", callback_data="charge_wallet")
        
        await message.answer(wallet_text, reply_markup=builder.as_markup())

@router.callback_query(F.data == "charge_wallet")
async def ask_charge_amount(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "💵 **مبلغ مورد نظر خود را جهت شارژ وارد کنید:**\n\n"
        "لطفاً مبلغ را به **تومان** و به صورت عدد انگلیسی بفرستید (مثال: 50000)"
    )
    await state.set_state(WalletStates.amount)

@router.message(WalletStates.amount)
async def process_charge_amount(message: types.Message, state: FSMContext):
    amount_str = message.text.strip()
    
    # بررسی عددی بودن ورودی کاربر
    if not amount_str.isdigit():
        await message.answer("❌ لطفاً فقط عدد وارد کنید. به عنوان مثال: 100000")
        return
        
    amount = float(amount_str)
    if amount < 10000:
        await message.answer("❌ حداقل مبلغ شارژ حساب 10,000 تومان می‌باشد. لطفا مبلغ بالاتری وارد کنید:")
        return
        
    await state.update_data(charge_amount=amount)
    
    async with AsyncSessionLocal() as db:
        # بررسی درگاه‌های صرافی و پرداخت فعال ثبت شده در وب پنل
        result = await db.execute(select(Gateway).where(Gateway.is_active == True))
        gateways = result.scalars().all()
        
        builder = InlineKeyboardBuilder()
        
        if gateways:
            # نمایش درگاه‌های فعال متصل به صرافی‌های ایرانی
            for gw in gateways:
                builder.button(text=f"💳 درگاه آنلاین {gw.name}", callback_data=f"pay_gw_{gw.id}")
        else:
            # اگر درگاهی در وب‌پنل فعال نبود، گزینه پیش‌فرض کارت به کارت دستی ظاهر می‌شود
            builder.button(text="🏦 واریز کارت به کارت (دستی)", callback_data="pay_manual_card")
            
        builder.adjust(1)
        
        await message.answer(
            f"🧾 **درخواست شارژ حساب**\n\n"
            f"💰 مبلغ درخواستی: {amount:,.0f} تومان\n\n"
            f"🔄 لطفاً روش پرداخت مورد نظر خود را انتخاب کنید:",
            reply_markup=builder.as_markup()
        )
        await state.clear() # خروج از حالت انتظار

@router.callback_query(F.data == "pay_manual_card")
async def process_manual_card(callback: types.CallbackQuery):
    # این بخش اطلاعات کارت به کارت ادمین را به همراه راهنمای تیکت نشان می‌دهد
    card_info = (
        "📌 **راهنمای واریز کارت به کارت دستی**\n\n"
        "لطفاً مبلغ مورد نظر را به شماره کارت زیر واریز نمایید:\n\n"
        "💳 شماره کارت: `۶۰۳۷-۹۹۷۹-۱۲۳۴-۵۶۷۸`\n"
        "👤 به نام: مدیریت ZarVPN\n\n"
        "⚠️ **مهم:** پس از واریز، حتماً تصویر فیش واریزی خود را به همراه شناسه کاربری تلگرام خود از طریق بخش **پشتیبانی و تیکت** برای ما ارسال کنید تا حساب شما شارژ شود."
    )
    await callback.message.edit_text(card_info, parse_mode="Markdown")
