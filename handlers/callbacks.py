from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.orm import Session

from core.config import settings
from core.database import SessionLocal, Ticket, TicketMessage, User
from core.logger import logger
from handlers.start import get_main_keyboard

router = Router()

# وضعیت‌های مربوط به ساخت تیکت و پاسخ‌دهی
class TicketStates(StatesGroup):
    GET_SUBJECT = State()
    GET_MESSAGE = State()
    ADMIN_REPLY = State()


@router.callback_query(F.data == "user_tickets")
async def show_tickets_menu(callback: CallbackQuery, state: FSMContext):
    """نمایش منوی اصلی پشتیبانی و تیکت‌ها"""
    await state.clear()
    tg_id = callback.from_user.id
    
    text = (
        "🎫 <b>بخش پشتیبانی و تیکت زار وی‌پی‌ان</b>\n\n"
        "اگر سوال، مشکل یا انتقادی دارید، می‌توانید یک تیکت جدید باز کنید "
        "یا وضعیت تیکت‌های قبلی خود را بررسی کنید. پشتیبانان ما در اسرع وقت پاسخ خواهند داد."
    )
    
    buttons = [
        [InlineKeyboardButton(text="➕ ثبت تیکت جدید", callback_data="ticket_create")],
        [InlineKeyboardButton(text="🗂️ تیکت‌های اخیر من", callback_data="ticket_list_user")],
        [InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
    ]
    
    # اگر کاربر ادمین بود، دکمه مشاهده تیکت‌های در انتظار پاسخ هم اضافه شود
    if tg_id in settings.ADMIN_IDS:
        buttons.insert(2, [InlineKeyboardButton(text="📥 تیکت‌های دریافتی کاربران (ادمین)", callback_data="ticket_list_admin")])
        
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


# ================= USER: CREATE TICKET =================

@router.callback_query(F.data == "ticket_create")
async def ticket_create_start(callback: CallbackQuery, state: FSMContext):
    """گام اول ساخت تیکت: دریافت موضوع"""
    await callback.message.edit_text(
        "📝 <b>لطفاً موضوع تیکت خود را در یک جمله کوتاه ارسال کنید:</b>\n"
        "(مثال: مشکل در اتصال به سرور آلمان)",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ انصراف", callback_data="user_tickets")]])
    )
    await state.set_state(TicketStates.GET_SUBJECT)
    await callback.answer()

@router.message(TicketStates.GET_SUBJECT)
async def ticket_save_subject(message: Message, state: FSMContext):
    """گام دوم ساخت تیکت: دریافت متن پیام اصلی"""
    await state.update_data(subject=message.text.strip())
    await message.answer("✍️ <b>حالا متن کامل پیام و مشکل خود را بنویسید و ارسال کنید:</b>")
    await state.set_state(TicketStates.GET_MESSAGE)

@router.message(TicketStates.GET_MESSAGE)
async def ticket_save_final(message: Message, state: FSMContext):
    """ثبت نهایی تیکت در دیتابیس و اطلاع‌رسانی به ادمین"""
    msg_text = message.text.strip()
    data = await state.get_data()
    tg_id = message.from_user.id
    
    db: Session = SessionLocal()
    try:
        # ۱. ایجاد خود تیکت
        new_ticket = Ticket(user_id=tg_id, subject=data['subject'], status="open")
        db.add(new_ticket)
        db.commit() # کامیت برای دریافت ID تیکت
        
        # ۲. ایجاد پیام اولیه تیکت
        new_message = TicketMessage(ticket_id=new_ticket.id, sender_id=tg_id, message=msg_text)
        db.add(new_message)
        db.commit()
        
        await message.answer(
            f"✅ تیکت شما با شناسه <b>#{new_ticket.id}</b> و موضوع «{data['subject']}» ثبت شد.\n"
            f"پشتیبانان به زودی پاسخ شما را خواهند داد.",
            reply_markup=get_main_keyboard(tg_id)
        )
        
        # اطلاع‌رسانی به ادمین‌ها
        from bot import bot
        for admin_id in settings.ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id, 
                    f"🔔 <b>تیکت جدید دریافت شد!</b>\n\n"
                    f"👤 کاربر: {tg_id}\n"
                    f"🆔 شناسه تیکت: #{new_ticket.id}\n"
                    f"📋 موضوع: {data['subject']}\n"
                    f"✉️ متن: {msg_text}"
                )
            except Exception:
                pass
                
    except Exception as e:
        logger.error(f"Error creating ticket: {str(e)}")
        await message.answer("❌ متاسفانه خطایی در ثبت تیکت رخ داد.")
    finally:
        db.close()
        await state.clear()


# ================= USER: LIST TICKETS =================

@router.callback_query(F.data == "ticket_list_user")
async def ticket_list_user(callback: CallbackQuery):
    """مشاهده تیکت‌های ارسال شده توسط خود کاربر"""
    tg_id = callback.from_user.id
    db: Session = SessionLocal()
    tickets = db.query(Ticket).filter(Ticket.user_id == tg_id).order_by(Ticket.id.desc()).limit(5).all()
    db.close()
    
    if not tickets:
        await callback.answer("📥 شما هیچ تیکتی ثبت نکرده‌اید.", show_alert=True)
        return
        
    text = "🗂️ <b>لیست تیکت‌های اخیر شما:</b>\n\n"
    buttons = []
    
    status_map = {"open": "⏳ در انتظار پاسخ", "answered": "🟢 پاسخ داده شده", "closed": "🔒 بسته شده"}
    
    for tk in tickets:
        status_text = status_map.get(tk.status, tk.status)
        text += f"🆔 شناسه: <b>#{tk.id}</b>\n📋 موضوع: {tk.subject}\n وضعیت: {status_text}\n---------------------\n"
        
    buttons.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="user_tickets")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


# ================= ADMIN: MANAGEMENT TICKETS =================

@router.callback_query(F.data == "ticket_list_admin")
async def ticket_list_admin(callback: CallbackQuery):
    """لیست تیکت‌های باز برای ادمین جهت پاسخ‌گویی"""
    if callback.from_user.id not in settings.ADMIN_IDS: return
    
    db: Session = SessionLocal()
    open_tickets = db.query(Ticket).filter(Ticket.status == "open").all()
    db.close()
    
    if not open_tickets:
        await callback.answer("🎉 هیچ تیکت در انتظار پاسخی وجود ندارد!", show_alert=True)
        return
        
    text = "📥 <b>تیکت‌های در انتظار پاسخ:</b>\n\nجهت پاسخ دادن به هر تیکت، روی دکمه شیشه‌ای مربوط به آن کلیک کنید:\n\n"
    buttons = []
    
    for tk in open_tickets:
        text += f"🆔 شناسه: #{tk.id} | کاربر: {tk.user_id}\n📋 موضوع: {tk.subject}\n---------------------\n"
        buttons.append([InlineKeyboardButton(text=f"✍️ پاسخ به تیکت #{tk.id}", callback_data=f"admin_reply_tk_{tk.id}")])
        
    buttons.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="user_tickets")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data.startswith("admin_reply_tk_"))
async def admin_reply_ticket_start(callback: CallbackQuery, state: FSMContext):
    """شروع فرآیند پاسخ ادمین به تیکت خاص"""
    if callback.from_user.id not in settings.ADMIN_IDS: return
    ticket_id = int(callback.data.split("_")[3])
    
    await state.update_data(reply_ticket_id=ticket_id)
    await callback.message.edit_text(
        f"✍️ <b>پاسخ خود را برای تیکت #{ticket_id} وارد کنید:</b>\n"
        f"پیام شما مستقیماً برای کاربر ارسال خواهد شد.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ انصراف", callback_data="user_tickets")]])
    )
    await state.set_state(TicketStates.ADMIN_REPLY)
    await callback.answer()

@router.message(TicketStates.ADMIN_REPLY)
async def admin_reply_ticket_send(message: Message, state: FSMContext):
    """ثبت پاسخ ادمین و ارسال پیام مستقیم به کاربر"""
    reply_text = message.text.strip()
    data = await state.get_data()
    ticket_id = data['reply_ticket_id']
    admin_id = message.from_user.id
    
    db: Session = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            await message.answer("❌ تیکت یافت نشد یا حذف شده است.")
            return
            
        # ۱. ثبت پیام ادمین در تاریخچه تیکت
        new_msg = TicketMessage(ticket_id=ticket_id, sender_id=admin_id, message=reply_text)
        ticket.status = "answered" # تغییر وضعیت تیکت به پاسخ‌ داده شده
        db.add(new_msg)
        db.commit()
        
        # ۲. ارسال پیام زنده برای کاربر شاکی
        from bot import bot
        try:
            user_msg = (
                f"✉️ <b>پاسخ پشتیبانی برای تیکت #{ticket_id} دریافت شد:</b>\n\n"
                f"📌 موضوع: {ticket.subject}\n"
                f"💬 پاسخ پشتیبان:\n{reply_text}"
            )
            await bot.send_message(ticket.user_id, user_msg)
            await message.answer(f"✅ پاسخ شما برای تیکت #{ticket_id} ثبت و به کاربر ارسال شد.")
        except Exception:
            await message.answer(f"⚠️ پاسخ در دیتابیس ثبت شد ولی کاربر به دلیل بلاک کردن ربات پیام را دریافت نکرد.")
            
    except Exception as e:
        logger.error(f"Error in admin replying ticket: {str(e)}")
        await message.answer("❌ خطایی رخ داد.")
    finally:
        db.close()
        await state.clear()

