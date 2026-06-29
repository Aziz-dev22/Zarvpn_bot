# handlers/start.py
from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from sqlalchemy.future import select

from core.config import Config
from core.database import AsyncSessionLocal
from database.models import User

router = Router()

def get_main_keyboard(user_id: int):
    """ساخت کیبورد منوی اصلی بر اساس نقش کاربر"""
    builder = ReplyKeyboardBuilder()
    
    # دکمه‌های عمومی برای همه کاربران
    builder.button(text="🛍️ خرید اشتراک جدید")
    builder.button(text="📂 سرویس‌های من")
    builder.button(text="💳 کیف پول / شارژ")
    builder.button(text="📞 پشتیبانی و تیکت")
    
    # اگر کاربر جزو لیست ادمین‌ها بود، دکمه ورود به پنل هم اضافه شود
    if user_id in Config.ADMIN_IDS:
        builder.button(text="⚙️ ورود به پنل مدیریت وب")
        
    # چیدمان دکمه‌ها به صورت دو تایی در هر ردیف
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    telegram_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name
    
    # اتصال به دیتابیس برای بررسی و ثبت کاربر
    async with AsyncSessionLocal() as db:
        # جستجوی کاربر در دیتابیس
        result = await db.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        
        if not user:
            # اگر کاربر وجود نداشت، او را به عنوان کاربر جدید ثبت می‌کنیم
            role = "admin" if telegram_id in Config.ADMIN_IDS else "user"
            user = User(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name,
                role=role,
                balance=0.0
            )
            db.add(user)
            await db.commit()
            welcome_text = f"سلام {full_name} عزیز! به ربات **ZarVPN** خوش آمدید. ✨\nثبت نام شما با موفقیت انجام شد."
        else:
            welcome_text = f"سلام مجدد {full_name} عزیز! خوش‌آمدید. 🌹\nاز منوی زیر می‌توانید خدمات مورد نظر خود را انتخاب کنید."
            
    # ارسال پیام خوش‌آمدگویی همراه با کیبورد دکمه‌ها
    await message.answer(welcome_text, reply_markup=get_main_keyboard(telegram_id))

