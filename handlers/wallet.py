from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.orm import Session

from core.database import SessionLocal, User, Transaction
from core.logger import logger
from handlers.start import get_main_keyboard

router = Router()

# تعریف وضعیت‌ها (States) برای دریافت مبلغ شارژ از کاربر
class WalletStates(StatesGroup):
    GET_AMOUNT = State()

@router.callback_query(F.data == "user_wallet")
async def show_wallet(callback: CallbackQuery, state: FSMContext):
    """نمایش وضعیت کیف پول و گزینه‌های شارژ"""
    await state.clear() # پاک کردن هرگونه وضعیت قبلی
    tg_id = callback.from_user.id
    
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        if not user:
            await callback.answer("❌ ابتدا ربات را مجدداً استارت کنید.", show_alert=True)
            return

        # فرمت کردن رقم موجودی به تومان به صورت ۳ رقم ۳ رقم
        formatted_balance = "{:,}".format(int(user.wallet_balance))

        text = (
            f"💳 <b>کیف پول زار وی‌پی‌ان</b>\n\n"
            f"👤 نام کاربری: {callback.from_user.full_name}\n"
            f"💰 موجودی حساب شما: <b>{formatted_balance} تومان</b>\n\n"
            f"💡 شما می‌توانید با شارژ حساب خود، هر زمان که خواستید سرویس جدید بخرید یا اشتراک‌های خود را تمدید کنید."
        )

        buttons = [
            [InlineKeyboardButton(text="➕ شارژ حساب (تومان / ریال)", callback_data="charge_irr")],
            [InlineKeyboardButton(text="🪙 شارژ حساب (رمزارز / Tether)", callback_data="charge_crypto")],
            [InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        # ویرایش پیام قبلی برای نمایش منوی کیف پول
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()

    except Exception as e:
        logger.error(f"Error in show_wallet: {str(e)}")
        await callback.answer("❌ مشکلی در دریافت اطلاعات کیف پول پیش آمد.", show_alert=True)
    finally:
        db.close()

@router.callback_query(F.data == "charge_irr")
async def process_charge_irr(callback: CallbackQuery, state: FSMContext):
    """شروع فرآیند دریافت مبلغ برای شارژ ریالی"""
    await callback.message.edit_text(
        "💵 <b>لطفاً مبلغ مورد نظر خود را برای شارژ به تومان وارد کنید:</b>\n\n"
        "⚠️ توجه: مبلغ باید به صورت عددی و به تومان باشد. (مثال: 50000)\n"
        "حداقل مبلغ شارژ: ۱۰,۰۰۰ تومان می‌باشد.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ انصراف", callback_data="user_wallet")]
        ])
    )
    # تغییر وضعیت ربات به حالت منتظر برای دریافت عدد از کاربر
    await state.set_state(WalletStates.GET_AMOUNT)
    await callback.answer()

@router.message(WalletStates.GET_AMOUNT)
async def receive_charge_amount(message: Message, state: FSMContext):
    """دریافت مبلغ عددی و ایجاد پیش‌فاکتور"""
    amount_text = message.text.strip()
    tg_id = message.from_user.id

    # بررسی اینکه کاربر حتما عدد وارد کرده باشد
    if not amount_text.isdigit():
        await message.answer("❌ لطفاً فقط عدد انگلیسی وارد کنید. مثلاً: 50000")
        return

    amount = int(amount_text)
    if amount < 10000:
        await message.answer("❌ حداقل مبلغ شارژ ۱۰,۰۰۰ تومان است. لطفاً مبلغ بزرگتری وارد کنید:")
        return

    db: Session = SessionLocal()
    try:
        # ایجاد یک تراکنش معلق در دیتابیس
        new_tx = Transaction(
            user_id=tg_id,
            amount=float(amount),
            gateway="Zarinpal", # به صورت پیش‌فرض زرین‌پال در نظر گرفته می‌شود
            status="pending"
        )
        db.add(new_tx)
        db.commit()

        formatted_amount = "{:,}".format(amount)
        invoice_text = (
            f"🧾 <b>پیش‌فاکتور شارژ حساب</b>\n\n"
            f"💰 مبلغ شارژ: <b>{formatted_amount} تومان</b>\n"
            f"💳 روش پرداخت: درگاه آنلاین بانکی\n\n"
            f"🔗 جهت اتصال به درگاه بانکی روی دکمه زیر کلیک کنید. پس از پرداخت، حساب شما به صورت خودکار شارژ می‌شود."
        )

        # در گام‌های بعدی که بخش وب‌پنل و مرچنت را نوشتیم، این لینک به درگاه واقعی متصل می‌شود
        # فعلاً یک دکمه شبیه‌ساز پرداخت موفق می‌گذاریم تا بتوانی عملکرد ربات را تست کنی
        buttons = [
            [InlineKeyboardButton(text="💳 اتصال به درگاه پرداخت", url=f"https://zarvpn.com/pay/{new_tx.id}")],
            [InlineKeyboardButton(text="🧪 شبیه‌ساز پرداخت موفق (تست)", callback_data=f"simulate_success_{new_tx.id}")],
            [InlineKeyboardButton(text="❌ لغو تراکنش", callback_data="user_wallet")]
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        await message.answer(invoice_text, reply_markup=keyboard)
        await state.clear() # خروج از وضعیت انتظار

    except Exception as e:
        logger.error(f"Error creating transaction: {str(e)}")
        await message.answer("❌ متاسفانه خطایی در صدور فاکتور رخ داد. دوباره تلاش کنید.")
    finally:
        db.close()

@router.callback_query(F.data.startswith("simulate_success_"))
async def simulate_payment(callback: CallbackQuery):
    """شبیه‌ساز پرداخت موفق برای تست بدون درگاه واقعی"""
    tx_id = int(callback.data.split("_")[2])
    tg_id = callback.from_user.id

    db: Session = SessionLocal()
    try:
        tx = db.query(Transaction).filter(Transaction.id == tx_id, Transaction.status == "pending").first()
        if not tx:
            await callback.answer("❌ این فاکتور منقضی شده یا قبلاً پرداخت شده است.", show_alert=True)
            return

        user = db.query(User).filter(User.telegram_id == tg_id).first()
        
        # تغییر وضعیت تراکنش و افزایش موجودی کاربر
        tx.status = "success"
        user.wallet_balance += tx.amount
        db.commit()

        formatted_amount = "{:,}".format(int(tx.amount))
        formatted_balance = "{:,}".format(int(user.wallet_balance))

        success_text = (
            f"✅ <b>پرداخت با موفقیت انجام شد!</b>\n\n"
            f"💰 مبلغ <b>{formatted_amount} تومان</b> به حساب شما اضافه شد.\n"
            f"💳 موجودی جدید شما: <b>{formatted_balance} تومان</b>"
        )
        
        await callback.message.edit_text(success_text, reply_markup=get_main_keyboard(tg_id))
        await callback.answer("🎉 حساب شما شارژ شد!", show_alert=True)

    except Exception as e:
        logger.error(f"Error in simulated payment: {str(e)}")
        await callback.answer("❌ خطایی در شبیه‌ساز رخ داد.", show_alert=True)
    finally:
        db.close()

@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: CallbackQuery):
    """کالبک دکمه بازگشت به منوی اصلی"""
    tg_id = callback.from_user.id
    welcome_text = (
        f"سلام <b>{callback.from_user.full_name}</b> عزیز، به ربات زار وی‌پی‌ان خوش آمدید! 👋\n\n"
        f"🚀 سریع‌ترین و امن‌ترین اشتراک‌های V2ray را از طریق دکمه‌های زیر مدیریت و خریداری کنید."
    )
    await callback.message.edit_text(welcome_text, reply_markup=get_main_keyboard(tg_id))
    await callback.answer()

