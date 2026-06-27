import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
import aiosqlite
from core import config
from core.database import init_commercial_db
from panels.marzban import MarzbanAPI
from panels.xui import XuiAPI

app = Client(
    "zarvpn_bot",
    bot_token=config.TELEGRAM_TOKEN,
    api_id=29302323, # آیدی عددی واقعی خودت را که گرفتی اینجا بذار
    api_hash="247e5f3f98d9fb20aab59a3a9472bcc4" # هش واقعی خودت را اینجا بذار
)

xui_panel = XuiAPI()
marzban_panel = MarzbanAPI()

# منوی اصلی کاربر
def user_menu(user_id):
    buttons = [
        [InlineKeyboardButton("🛍️ خرید اشتراک V2Ray", callback_data="buy_menu"),
         InlineKeyboardButton("👤 حساب و کانکشن‌های من", callback_data="my_account")],
        [InlineKeyboardButton("💳 شارژ کیف پول (کارت به کارت)", callback_data="charge_wallet"),
         InlineKeyboardButton("📞 پشتیبانی ۲۴ ساعته", callback_data="support_info")]
    ]
    if user_id == config.ADMIN_ID:
        buttons.append([InlineKeyboardButton("⚙️ پنل مدیریت هوشمند ربات", callback_data="admin_panel_main")])
    return InlineKeyboardMarkup(buttons)

@app.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    uid = message.from_user.id
    uname = message.from_user.username or "کاربر بدون آیدی"
    
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (uid, uname))
        await db.commit()
        
    await message.reply_text(
        f" سلام {message.from_user.first_name} عزیز\nبه ابر سیستم هوشمند فروش کانکشن خودکار **ZarVpn** خوش آمدید.\n\nلطفاً جهت خرید یا مدیریت کانکشن‌ها از دکمه‌های زیر استفاده کنید:",
        reply_markup=user_menu(uid)
    )

@app.on_callback_query()
async def handle_commercial_callbacks(client: Client, call: CallbackQuery):
    uid = call.from_user.id
    
    async with aiosqlite.connect("zarvpn_web.db") as db:
        if call.data == "back_to_main":
            await call.answer()
            await call.edit_message_text("🤖 منوی اصلی سیستم ZarVpn:", reply_markup=user_menu(uid))
            
        elif call.data == "my_account":
            await call.answer()
            async with db.execute("SELECT balance FROM users WHERE user_id = ?", (uid,)) as c:
                balance = (await c.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM orders WHERE user_id = ?", (uid,)) as c:
                orders_count = (await c.fetchone())[0]
                
            text = f"👤 **مشخصات حساب شما:**\n\n🆔 آیدی عددی: `{uid}`\n💳 موجودی کیف پول: {balance:,} تومان\n📦 تعداد کانکشن‌های فعال: {orders_count} عدد"
            buttons = []
            if orders_count > 0:
                buttons.append([InlineKeyboardButton("📥 دریافت مجدد لینک‌های کانکشن", callback_data="my_connections")])
            buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
            await call.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))

        elif call.data == "buy_menu":
            await call.answer()
            async with db.execute("SELECT * FROM plans") as c:
                plans = await c.fetchall()
            buttons = []
            for p in plans:
                buttons.append([InlineKeyboardButton(f"{p[1]} ➖ {p[4]:,} تومان", callback_data=f"order_p_{p[0]}")])
            buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
            await call.edit_message_text("🛍️ لیست پلن‌های فعال سرورها:\n\nپلن مورد نظر خود را انتخاب کنید تا به صورت خودکار روی پنل سنایی یا مرزبان ساخته شود:", reply_markup=InlineKeyboardMarkup(buttons))

        elif call.data.startswith("order_p_"):
            pid = int(call.data.split("_")[2])
            async with db.execute("SELECT * FROM plans WHERE id = ?", (pid,)) as c:
                plan = await c.fetchone()
            async with db.execute("SELECT balance FROM users WHERE user_id = ?", (uid,)) as c:
                balance = (await c.fetchone())[0]
                
            if balance < plan[4]:
                await call.answer("❌ موجودی کیف پول شما کافی نیست!", show_alert=True)
                return
                
            await call.edit_message_text("🔄 موجودی تایید شد. در حال برقراری ارتباط ایمن با پنل V2Ray و ساخت کانکشن اختصاصی شما...")
            
            v2_username = f"zar_{uid}_{pid}"
            if plan[5] == "xui":
                res = await xui_panel.create_user(v2_username, plan[3], plan[2])
            else:
                res = await marzban_panel.create_user(v2_username, plan[3], plan[2])
                
            if res["status"] == "success":
                new_bal = balance - plan[4]
                await db.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_bal, uid))
                await db.execute("INSERT INTO orders (user_id, plan_name, sub_link, v2ray_username, panel_type) VALUES (?, ?, ?, ?, ?)",
                                 (uid, plan[1], res["link"], v2_username, plan[5]))
                await db.commit()
                
                text = f"✅ **خرید با موفقیت انجام شد!**\n\n📌 **مشخصات سرویس:**\n📦 پلن: {plan[1]}\n⏱️ مدت زمان: {plan[3]} روز\n\n🚀 **لینک ساب‌اسکریپشن اختصاصی شما (مخصوص ثبت در برنامه):**\n`{res['link']}`"
                await call.message.reply_text(text)
            else:
                text = f"❌ **خطا در اتصال به پنل سرور:**\n{res['message']}\n\n💰 وجهی از حساب شما کسر نشد."
                await call.message.reply_text(text)

        # ⚙️ بخش پنل مدیریت حرفه‌ای داخل ربات برای ادمین
        elif call.data == "admin_panel_main" and uid == config.ADMIN_ID:
            await call.answer()
            async with db.execute("SELECT COUNT(*) FROM users") as c:
                total_users = (await c.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM orders") as c:
                total_orders = (await c.fetchone())[0]
                
            text = f"⚙️ **پنل مدیریت پیشرفته ادمین ZarVpn**\n\n👥 کل کاربران ربات: {total_users} نفر\n🛒 کل کانکشن‌های فروخته شده: {total_orders} عدد\n🌐 وضعیت پنل تحت وب: فعال (پورت 8080)"
            buttons = [
                [InlineKeyboardButton("🎁 شارژ هدیه ۱۰۰ تومانی حساب خودم", callback_data="gif_adm")],
                [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_to_main")]
            ]
            await call.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))

        elif call.data == "gif_adm" and uid == config.ADMIN_ID:
            await db.execute("UPDATE users SET balance = balance + 100000 WHERE user_id = ?", (config.ADMIN_ID,))
            await db.commit()
            await call.answer("✅ حساب شما ۱۰۰ هزار تومان شارژ تست شد!", show_alert=True)
