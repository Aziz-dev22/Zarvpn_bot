# handlers/support.py
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.config import Config
from core.database import AsyncSessionLocal
from database.models import Ticket

router = Router()

class SupportStates(StatesGroup):
    waiting_for_msg = State()

@router.message(F.text == "📞 پشتیبانی و تیکت")
async def open_support(message: types.Message, state: FSMContext):
    support_text = (
        "📞 **بخش پشتیبانی ZarVPN**\n\n"
        "لطفاً پیام، سوال، مشکل فنی یا تصویر فیش واریزی خود را در قالب **یک پیام** ارسال کنید.\n"
        "پشتیبان‌های ما در سریع‌ترین زمان ممکن پاسخ شما را خواهند داد."
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ انصراف", callback_data="cancel_support")
    
    await message.answer(support_text, reply_markup=builder.as_markup())
    await state.set_state(SupportStates.waiting_for_msg)

@router.callback_query(F.data == "cancel_support")
async def cancel_support(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ عملیات ارسال پیام به پشتیبانی لغو شد.")

@router.message(SupportStates.waiting_for_msg)
async def receive_support_msg(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    msg_text = message.text or message.caption or "ارسال تصویر"
    photo_id = message.photo[-1].file_id if message.photo else None
    
    async with AsyncSessionLocal() as db:
        # ثبت تیکت در دیتابیس
        new_ticket = Ticket(
            user_id=user_id,
            message_text=msg_text,
            photo_id=photo_id,
            status="open"
        )
        db.add(new_ticket)
        await db.commit()
        
    await message.answer("✅ پیام شما با موفقیت به بخش پشتیبانی ارسال شد. پس از بررسی به شما پاسخ داده می‌شود.")
    
    # مطلع کردن ادمین‌ها به صورت آنی در تلگرام
    for admin_id in Config.ADMIN_IDS:
        try:
            admin_alert = (
                f"📥 **تیکت پشتیبانی جدید!**\n\n"
                f"👤 از کاربر: {message.from_user.full_name} (`{user_id}`)\n"
                f"📝 متن پیام: {msg_text}\n"
            )
            if photo_id:
                await message.bot.send_photo(chat_id=admin_id, photo=photo_id, caption=admin_alert)
            else:
                await message.bot.send_message(chat_id=admin_id, text=admin_alert)
        except Exception as e:
            print(f"Failed to alert admin {admin_id}: {e}")
            
    await state.clear()

