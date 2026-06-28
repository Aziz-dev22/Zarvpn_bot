from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from core.database import SessionLocal, User, Package, Subscription, ServerPanel
from core.logger import logger
from panels.sanaei import SanaeiPanel
from handlers.start import get_main_keyboard

router = Router()

@router.callback_query(F.data == "buy_service")
async def show_packages(callback: CallbackQuery):
    """نمایش لیست پکیج‌های فروشی موجود در دیتابیس"""
    tg_id = callback.from_user.id
    
    db: Session = SessionLocal()
    try:
        # دریافت پکیج‌های فعال از دیتابیس
        packages = db.query(Package).filter(Package.is_active == True).all()
        
        if not packages:
            await callback.message.edit_text(
                "❌ در حال حاضر هیچ پکیج سرویسی توسط مدیریت تعریف نشده است.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_main")]
                ])
            )
            return

        text = "🛍️ <b>لیست پکیج‌های اشتراک زار وی‌پی‌ان</b>\n\nلطفاً یکی از پلن‌های زیر را جهت خرید انتخاب کنید:"
        
        buttons = []
        for pkg in packages:
            formatted_price = "{:,}".format(int(pkg.price))
            # ساخت یک دکمه برای هر پکیج
            buttons.append([
                InlineKeyboardButton(
                    text=f"📦 {pkg.title} - {formatted_price} تومان", 
                    callback_data=f"select_pkg_{pkg.id}"
                )
            ])
            
        buttons.append([InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="back_to_main")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing packages: {str(e)}")
        await callback.answer("❌ خطایی در دریافت لیست پکیج‌ها رخ داد.", show_alert=True)
    finally:
        db.close()


@router.callback_query(F.data.startswith("select_pkg_"))
async def process_package_purchase(callback: CallbackQuery):
    """پردازش خرید پکیج انتخابی و اتصال به پنل X-UI"""
    pkg_id = int(callback.data.split("_")[2])
    tg_id = callback.from_user.id

    db: Session = SessionLocal()
    try:
        # ۱. بررسی وجود پکیج
        pkg = db.query(Package).filter(Package.id == pkg_id).first()
        if not pkg:
            await callback.answer("❌ این پکیج دیگر موجود نیست.", show_alert=True)
            return

        # ۲. بررسی موجودی کاربر
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        if user.wallet_balance < pkg.price:
            formatted_needed = "{:,}".format(int(pkg.price - user.wallet_balance))
            await callback.answer(
                f"❌ موجودی کیف پول شما کافی نیست!\nبرای خرید این پلن به {formatted_needed} تومان شارژ بیشتر نیاز دارید.", 
                show_alert=True
            )
            return

        # ۳. پیدا کردن یک پنل فعال برای ساخت کانکشن
        panel_info = db.query(ServerPanel).filter(ServerPanel.is_active == True, ServerPanel.panel_type == "sanaei").first()
        if not panel_info:
            await callback.answer("❌ در حال حاضر سرور فعالی برای خرید در دسترس نیست. به پشتیبانی اطلاع دهید.", show_alert=True)
            return

        # ارسال پیام در حال پردازش به کاربر
        await callback.message.edit_text("⏳ <b>در حال برقراری ارتباط با سرور و ایجاد اشتراک شما... لطفاً صبوری کنید.</b>")

        # ۴. اتصال به API پنل ثنایی و ساخت کلاینت
        panel_api = SanaeiPanel(panel_url=panel_info.url, username=panel_info.username, password=panel_info.password)
        
        # استفاده از آیدی تلگرام به عنوان پایه نام کاربری در پنل
        account_email = f"usr_{tg_id}"
        
        panel_user = await panel_api.create_user(
            email=account_email, 
            data_limit_gb=pkg.volume_gb, 
            expire_days=pkg.days
        )
        await panel_api.close()

        if not panel_user:
            await callback.message.edit_text(
                "❌ متاسفانه ارتباط با سرور قطع شد و امکان ساخت اشتراک وجود نداشت. وجهی از حساب شما کسر نشد.",
                reply_markup=get_main_keyboard(tg_id)
            )
            return

        # ۵. کسر وجه از کیف پول و ثبت در دیتابیس ربات
        user.wallet_balance -= pkg.price
        
        expire_date = datetime.utcnow() + timedelta(days=pkg.days)
        
        new_sub = Subscription(
            user_id=tg_id,
            panel_id=panel_info.id,
            email_in_panel=panel_user["email"],
            uuid=panel_user["uuid"],
            sub_url=panel_user["sub_url"],
            expire_at=expire_date
        )
        db.add(new_sub)
        db.commit()

        # ۶. تحویل اشتراک به کاربر
        success_text = (
            f"🎉 <b>اشتراک شما با موفقیت ساخته شد!</b>\n\n"
            f"📦 نام پلن: {pkg.title}\n"
            f"⏳ مدت اعتبار: {pkg.days} روز\n"
            f"📊 حجم مجاز: {pkg.volume_gb} گیگابایت\n\n"
            f"🔗 <b>لینک اشتراک اختصاصی شما (V2ray Sub):</b>\n"
            f"<code>{panel_user['sub_url']}</code>\n\n"
            f"⚠️ این لینک را در نرم‌افزارهای خود (v2rayNG, Nekobox, Shadowrocket) وارد کنید. لینک را در اختیار دیگران قرار ندهید."
        )
        
        await callback.message.edit_text(success_text, reply_markup=get_main_keyboard(tg_id))
        logger.info(f"User {tg_id} successfully bought package {pkg.title}")

    except Exception as e:
        logger.error(f"Error in processing purchase: {str(e)}")
        await callback.message.edit_text("❌ خطایی در فرآیند خرید رخ داد. لطفاً دوباره تلاش کنید.")
    finally:
        db.close()


@router.callback_query(F.data == "my_services")
async def show_my_services(callback: CallbackQuery):
    """نمایش لیست اشتراک‌های خریداری شده توسط کاربر"""
    tg_id = callback.from_user.id
    
    db: Session = SessionLocal()
    try:
        subs = db.query(Subscription).filter(Subscription.user_id == tg_id).all()
        
        if not subs:
            await callback.answer("📋 شما هنوز هیچ اشتراک فعالی خریداری نکرده‌اید.", show_alert=True)
            return

        text = "📋 <b>لیست سرویس‌های خریداری شده شما:</b>\n\n"
        
        buttons = []
        for index, sub in enumerate(subs, start=1):
            text += f"{index}. 📧 کد اشتراک: <code>{sub.email_in_panel}</code>\n"
            if sub.expire_at:
                # تبدیل تاریخ انقضا به فرمت خوانا
                text += f"📅 تاریخ انقضا: {sub.expire_at.strftime('%Y-%m-%d')}\n"
            text += f"🔗 لینک ساب: <code>{sub.sub_url}</code>\n"
            text += "----------------------------------\n"
            
        buttons.append([InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="back_to_main")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing user services: {str(e)}")
        await callback.answer("❌ خطایی در بارگذاری سرویس‌ها رخ داد.", show_alert=True)
    finally:
        db.close()

