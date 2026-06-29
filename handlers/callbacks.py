# handlers/callbacks.py
import uuid
from aiogram import Router, F, types
from sqlalchemy.future import select

from core.database import AsyncSessionLocal
from database.models import User, InboundPanel, Package
from panels.manager import PanelManager

router = Router()

@router.callback_query(F.data.startswith("pay_wallet_"))
async def process_wallet_payment(callback: types.CallbackQuery):
    # تجزیه اطلاعات فرستاده شده از دکمه خرید (شناسه سرور و شناسه پکیج)
    data_parts = callback.data.split("_")
    panel_id = int(data_parts[2])
    pkg_id = int(data_parts[3])
    
    async with AsyncSessionLocal() as db:
        # دریافت اطلاعات کاربر، سرور و پکیج از دیتابیس
        user_result = await db.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = user_result.scalar_one_or_none()
        
        panel_result = await db.execute(select(InboundPanel).where(InboundPanel.id == panel_id))
        panel = panel_result.scalar_one_or_none()
        
        pkg_result = await db.execute(select(Package).where(Package.id == pkg_id))
        package = pkg_result.scalar_one_or_none()
        
        if not user or not panel or not package:
            await callback.message.edit_text("❌ خطایی در بازخوانی اطلاعات رخ داد. مجدداً تلاش کنید.")
            return

        # بررسی مجدد موجودی کیف پول برای امنیت بیشتر
        if user.balance < package.price:
            await callback.message.edit_text("❌ موجودی شما کافی نیست. لطفا ابتدا کیف پول خود را شارژ کنید.")
            return
            
        # اطلاع‌رسانی به کاربر که فرآیند ساخت شروع شده است
        await callback.message.edit_text("🔄 در حال ارتباط با سرور و ساخت کانفیگ شما... لطفا چند لحظه صبر کنید.")
        
        # تولید اطلاعات اختصاصی اکانت وی‌پی‌ان
        client_uuid = str(uuid.uuid4())
        client_email = f"Zar_{user.telegram_id}_{uuid.uuid4().hex[:4]}"
        
        try:
            # دریافت کلاینت متصل به پنل سنایی یا مرزبان از طریق پنل‌منیجر
            panel_client = PanelManager.get_panel_client(panel)
            
            # ارسال درخواست ساخت اکانت به پنل (به فرض استفاده از inbound_id پیش‌فرض شماره 1)
            # در نسخه‌های بعدی وب‌پنل ادمین می‌تواند اینباند را مشخص کند
            inbound_id = 1 
            
            is_created = await panel_client.add_client(
                inbound_id=inbound_id,
                email=client_email,
                uuid=client_uuid,
                limit_ip=2, # محدودیت دو کاربر همزمان به صورت پیش‌فرض
                total_gb=package.volume_gb,
                expiry_days=package.expiry_days
            )
            
            if is_created:
                # کسر هزینه از کیف پول کاربر در دیتابیس
                user.balance -= package.price
                await db.commit()
                
                # تولید لینک سابسکریپشن یا کانفیگ مستقیم (بر اساس استاندارد X-UI سنایی)
                # ساخت یک نمونه لینک Vless برای نمونه (با توجه به دامین ادمین)
                clean_url = panel.api_url.replace("http://", "").replace("https://", "").split(":")[0]
                vless_config = f"vless://{client_uuid}@{clean_url}:443?type=tcp&security=none#{panel.name}-{package.name}"
                
                success_text = (
                    f"🎉 **خرید شما با موفقیت انجام شد و اکانت ساخته شد!**\n\n"
                    f"🌐 سرور: {panel.name}\n"
                    f"📦 پکیج: {package.name}\n"
                    f"💰 مبلغ کسر شده: {package.price:,.0f} تومان\n"
                    f"💳 موجودی باقی‌مانده: {user.balance:,.0f} تومان\n\n"
                    f"🔑 **کانفیگ اختصاصی شما:**\n"
                    f"`{vless_config}`\n\n"
                    f"📌 جهت استفاده، کد بالا را کامل کپی کرده و در نرم‌افزار خود (v2rayNG یا Streisand) وارد کنید."
                )
                await callback.message.answer(success_text, parse_mode="Markdown")
                await callback.message.delete() # حذف پیام فاکتور قدیمی
            else:
                await callback.message.edit_text("❌ متأسفانه ارتباط با سرور برقرار نشد یا ظرفیت اینباند تکمیل است. مبلغی از شما کسر نشد و موضوع به ادمین گزارش گردید.")
                
        except Exception as e:
            print(f"Error during purchase callback: {e}")
            await callback.message.edit_text("❌ خطای فنی در ساخت اکانت رخ داد. لطفاً به پشتیبانی اطلاع دهید.")
