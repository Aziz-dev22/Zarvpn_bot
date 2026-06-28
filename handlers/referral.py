from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import Session

from core.database import SessionLocal, User
from core.logger import logger

router = Router()

@router.callback_query(F.data == "user_referral")
async def show_referral_panel(callback: CallbackQuery):
    """نمایش منوی زیرمجموعه‌گیری و تعداد افراد دعوت شده"""
    tg_id = callback.from_user.id
    
    # دریافت آیدی اسکپ‌آوت ربات برای ساخت لینک دعوت اختصاصی
    bot_user = await callback.message.bot.get_me()
    bot_username = bot_user.username
    
    # ساخت لینک دعوت اختصاصی کاربر
    referral_link = f"https://t.me/{bot_username}?start={tg_id}"

    db: Session = SessionLocal()
    try:
        # شمارش تعداد زیرمجموعه‌های این کاربر
        invited_count = db.query(User).filter(User.referred_by == tg_id).count()
        
        # دریافت اطلاعات خود کاربر برای نمایش هدیه‌ها در آینده (مثلاً سیستم درصد سود)
        user = db.query(User).filter(User.telegram_id == tg_id).first()

        text = (
            f"👥 <b>سیستم کسب درآمد و زیرمجموعه‌گیری زار وی‌پی‌ان</b>\n\n"
            f"🎯 با دعوت دوستان خود به ربات، از خرید‌های آن‌ها هدیه بگیرید!\n\n"
            f"📊 <b>آمار شما:</b>\n"
            f"👤 تعداد افراد دعوت شده توسط شما: <b>{invited_count} نفر</b>\n\n"
            f"🔗 <b>لینک دعوت اختصاصی شما:</b>\n"
            f"<code>{referral_link}</code>\n\n"
            f"💡 کافی است لینک بالا را کپی کرده و برای دوستان خود بفرستید. به محض ورود آن‌ها به ربات، سیستم آن‌ها را به عنوان زیرمجموعه شما شناسایی خواهد کرد."
        )

        buttons = [
            [
                # دکمه اشتراک‌گذاری مستقیم در تلگرام
                InlineKeyboardButton(
                    text="🔗 اشتراک‌گذاری لینک با دوستان", 
                    url=f"https://t.me/share/url?url={referral_link}&text=سلام!%20با%20این%20لینک%20عضو%20ربات%20زار%20وی‌پی‌ان%20شو%20و%20از%20اینترنت%20پر سرعت%20و%20امن%20استفاده%20کن!%20🚀"
                )
            ],
            [InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        await callback.message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
        await callback.answer()

    except Exception as e:
        logger.error(f"Error in show_referral_panel for user {tg_id}: {str(e)}")
        await callback.answer("❌ مشکلی در دریافت اطلاعات زیرمجموعه‌گیری پیش آمد.", show_alert=True)
    finally:
        db.close()
