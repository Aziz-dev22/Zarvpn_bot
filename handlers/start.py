from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from sqlalchemy.orm import Session

from core.database import SessionLocal, User
from core.logger import logger
from core.config import settings

router = Router()

def get_main_keyboard(tg_id: int) -> InlineKeyboardMarkup:
    """ساخت منوی اصلی ربات به صورت دکمه‌های شیشه‌ای"""
    buttons = [
        [
            InlineKeyboardButton(text="🛍️ خرید اشتراک جدید", callback_data="buy_service"),
            InlineKeyboardButton(text="📋 سرویس‌های من", callback_data="my_services")
        ],
        [
            InlineKeyboardButton(text="💰 کیف پول / شارژ", callback_data="user_wallet"),
            InlineKeyboardButton(text="👥 زیرمجموعه‌گیری", callback_data="user_referral")
        ],
        [
            InlineKeyboardButton(text="🎫 پشتیبانی / تیکت", callback_data="user_tickets"),
            InlineKeyboardButton(text="ℹ️ وضعیت حساب", callback_data="account_status")
        ]
    ]
    
    # اگر کاربر جزو ادمین‌ها بود، دکمه پنل مدیریت هم برایش نمایش داده شود
    if tg_id in settings.ADMIN_IDS:
        buttons.append([InlineKeyboardButton(text="⚙️ پنل مدیریت ادمین", callback_data="admin_panel")])
        
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(CommandStart())
async def cmd_start(message: Message):
    """هندلر دستور /start ربات"""
    tg_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name
    
    # استخراج کد رفرال (اگر کاربر با لینک دعوت آمده باشد، کد بعد از دستور استارت قرار می‌گیرد)
    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])

    db: Session = SessionLocal()
    try:
        # بررسی وجود کاربر در دیتابیس
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        
        if not user:
            # اگر کاربر جدید است و با لینک دعوت آمده و خودش معرف خودش نیست
            if referrer_id and referrer_id != tg_id:
                # بررسی اینکه آیا معرف خودش در سیستم وجود دارد یا نه
                referrer_exists = db.query(User).filter(User.telegram_id == referrer_id).first()
                if not referrer_exists:
                    referrer_id = None
            else:
                referrer_id = None
                
            # ثبت کاربر جدید در دیتابیس
            user = User(
                telegram_id=tg_id,
                username=username,
                full_name=full_name,
                referred_by=referrer_id
            )
            db.add(user)
            db.commit()
            logger.info(f"New user registered: {tg_id} (Referred by: {referrer_id})")
            
            # ارسال پیام خوش‌آمدگویی به معرف در صورت وجود
            if referrer_id:
                try:
                    from bot import bot
                    await bot.send_message(
                        referrer_id, 
                        f"👥 یک کاربر جدید با لینک دعوت شما عضو ربات شد!"
                    )
                except Exception:
                    pass
        else:
            # اگر کاربر از قبل بود، صرفاً اطلاعات عمومی‌اش را بروزرسانی می‌کنیم
            user.username = username
            user.full_name = full_name
            db.commit()

        # بررسی بن بودن کاربر
        if user.is_ban:
            await message.answer("❌ حساب کاربری شما در این ربات مسدود شده است.")
            return

        # متن پیام خوش‌آمدگویی منوی اصلی
        welcome_text = (
            f"سلام <b>{full_name}</b> عزیز، به ربات زار وی‌پی‌ان خوش آمدید! 👋\n\n"
            f"🚀 سریع‌ترین و امن‌ترین اشتراک‌های V2ray را از طریق دکمه‌های زیر مدیریت و خریداری کنید."
        )
        
        await message.answer(welcome_text, reply_markup=get_main_keyboard(tg_id))

    except Exception as e:
        logger.error(f"Error in start handler for user {tg_id}: {str(e)}")
        await message.answer("❌ خطایی در بارگذاری اطلاعات رخ داد. لطفاً مجدداً تلاش کنید.")
    finally:
        db.close()

