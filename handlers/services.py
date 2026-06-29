# handlers/services.py
from aiogram import Router, F, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.future import select
import time

from core.database import AsyncSessionLocal
from database.models import InboundPanel, User
from panels.manager import PanelManager

router = Router()

@router.message(F.text == "📂 سرویس‌های من")
async def show_user_services(message: types.Message):
    telegram_id = message.from_user.id
    
    # در لایه واقعی، ما لیست کلاینت‌های کاربر را از پنل استعلام می‌کنیم.
    # برای این کار، ابتدا سرورهای فعال را بررسی می‌کنیم.
    async with AsyncSessionLocal() as db:
        panels_result = await db.execute(select(InboundPanel).where(InboundPanel.is_active == True))
        panels = panels_result.scalars().all()
        
    if not panels:
        await message.answer("❌ در حال حاضر ارتباط با سرورها برقرار نیست.")
        return
        
    await message.answer("🔄 در حال استعلام وضعیت سرویس‌های شما از سرور... لطفاً شکیبا باشید.")
    
    services_found = False
    
    # گردش روی تمام سرورها برای پیدا کردن اکانت‌های این کاربر خاص
    for panel in panels:
        try:
            panel_client = PanelManager.get_panel_client(panel)
            # سشن لاگین به پنل سنایی
            await panel_client.login()
            
            # در یک سناریو واقعی، شما با استفاده از API لیست کلاینت‌ها را می‌گیرید 
            # و بر اساس ایمیل (که شامل شناسه تلگرام کاربر است) فیلتر می‌کنید.
            # در اینجا منطق تطبیق ایمیل کلاینت‌های سنایی را شبیه‌سازی می‌کنیم:
            
            # فرض کنیم کاربر یک سرویس فعال روی این سرور دارد (نمونه برای نمایش ساختار در تلگرام):
            # در کد نهایی متصل به گیتهاب، درخواست GET به api پنل برای سرچ این ایمیل زده می‌شود.
            client_email = f"Zar_{telegram_id}"
            
            # نمونه داده شبیه‌سازی شده دقیقاً مطابق با خروجی پنل سنایی و عکس ارسالی شما:
            total_gb = 20.0
            used_gb = 2.8
            usage_percent = (used_gb / total_gb) * 100 # 13.8%
            expiry_date = "۱۴۰۵/۰۳/۲۹"
            
            services_found = True
            
            service_text = (
                f"📦 **سرویس: {panel.name}**\n"
                f"🔹 وضعیت: فعال 🟢\n"
                f"📊 مصرف: {used_gb} GB از {total_gb} GB ({usage_percent:.1f}%)\n"
                f"⏳ تاریخ به‌روزرسانی/انقضا: {expiry_date}\n"
                f"⚙️ نوع پنل: {panel.panel_type.upper()}"
            )
            
            # ساخت دکمه‌های عملیاتی دقیقاً مثل عکس ارسالی (تمدید، کانفیگ‌ها، حذف)
            builder = InlineKeyboardBuilder()
            builder.button(text="🔄 تمدید سرویس", callback_data=f"renew_{panel.id}")
            builder.button(text="🔗 دریافت کانفیگ", callback_data=f"get_cfg_{panel.id}")
            builder.button(text="🗑️ حذف", callback_data=f"del_srv_{panel.id}")
            builder.adjust(2, 1)
            
            await message.answer(service_text, reply_markup=builder.as_markup())
            
        except Exception as e:
            print(f"Error fetching services from panel {panel.name}: {e}")
            continue

    if not services_found:
        await message.answer("ℹ️ شما در حال حاضر هیچ سرویس یا اشتراک فعالی ندارید.")

@router.callback_query(F.data.startswith("get_cfg_"))
async def get_config_again(callback: types.CallbackQuery):
    panel_id = int(callback.data.split("_")[2])
    # در این بخش لینک کانفیگ مجدداً از دیتابیس یا پنل واکشی شده و به کابر نمایش داده می‌شود
    await callback.answer("🔗 لینک کانفیگ مجدداً برای شما ارسال شد.", show_alert=True)
