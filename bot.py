import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
import aiosqlite
import requests
from core import config
from panels.marzban import MarzbanAPI
from panels.xui import XuiAPI

app = Client(
    "zarvpn_bot",
    bot_token=config.TELEGRAM_TOKEN,
    api_id=29302323, # آیدی واقعی خودت
    api_hash="247e5f3f98d9fb20aab59a3a9472bcc4" # هش واقعی خودت
)

xui_panel = XuiAPI()
marzban_panel = MarzbanAPI()

def user_menu(user_id):
    buttons = [
        [InlineKeyboardButton("🛍️ خرید خودکار کانکشن V2Ray", callback_data="buy_menu")],
        [InlineKeyboardButton("👤 حساب کاربری و لایسنس‌ها", callback_data="my_account"),
         InlineKeyboardButton("🪙 شارژ خودکار کریپتو (صرافی)", callback_data="crypto_charge")],
        [InlineKeyboardButton("📞 پشتیبانی آنلاین", callback_data="support_info")]
    ]
    if user_id == config.ADMIN_ID:
        buttons.append([InlineKeyboardButton("⚙️ ورود به پنل مدیریت تحت وب", url=f"http://{config.PANEL_URL.split(':')[1]}:8080")])
    return InlineKeyboardMarkup(buttons)

@app.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    uid = message.from_user.id
    uname = message.from_user.username or "کاربر"
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (uid, uname))
        await db.commit()
    await message.reply_text("🤖 به ابرسیستم هوشمند و تجاری فروش کانکشن ZarVpn خوش آمدید:", reply_markup=user_menu(uid))

@app.on_callback_query()
async def handle_callbacks(client: Client, call: CallbackQuery):
    uid = call.from_user.id
    
    async with aiosqlite.connect("zarvpn_web.db") as db:
        if call.data == "back_to_main":
            await call.edit_message_text("🤖 منوی اصلی سیستم ZarVpn:", reply_markup=user_menu(uid))
            
        elif call.data == "buy_menu":
            async with db.execute("SELECT * FROM plans") as c: plans = await c.fetchall()
            buttons = []
            for p in plans:
                buttons.append([InlineKeyboardButton(f"{p[1]} ({p[5].upper()}) ➖ {p[4]:,} تومان", callback_data=f"order_p_{p[0]}")])
            buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
            await call.edit_message_text("🛍️ پلن مورد نظر خود را جهت صدور آنی انتخاب کنید:", reply_markup=InlineKeyboardMarkup(buttons))

        elif call.data.startswith("order_p_"):
            pid = int(call.data.split("_")[2])
            async with db.execute("SELECT * FROM plans WHERE id = ?", (pid,)) as c: plan = await c.fetchone()
            async with db.execute("SELECT balance FROM users WHERE user_id = ?", (uid,)) as c: balance = (await c.fetchone())[0]
                
            if balance < plan[4]:
                await call.answer("❌ موجودی کافی نیست! لطفاً از بخش صرافی حساب خود را شارژ کنید.", show_alert=True)
                return
                
            await call.edit_message_text("🔄 موجودی تایید شد. اتصال به سرور و ساخت اکانت...")
            v2_username = f"zar_{uid}_{pid}"
            
            res = await xui_panel.create_user(v2_username, plan[3], plan[2]) if plan[5] == "xui" else await marzban_panel.create_user(v2_username, plan[3], plan[2])
                
            if res["status"] == "success":
                await db.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (plan[4], uid))
                await db.execute("INSERT INTO orders (user_id, plan_name, sub_link, v2ray_username, panel_type) VALUES (?, ?, ?, ?, ?)", (uid, plan[1], res["link"], v2_username, plan[5]))
                await db.commit()
                await call.message.reply_text(f"✅ **خرید موفق!**\n\n📦 پلن: {plan[1]}\n🚀 **لینک کانکشن شما:**\n`{res['link']}`")
            else:
                await call.message.reply_text(f"❌ خطا در پنل سرور: {res['message']}")

        # متصل کردن خودکار ربات به API صرافی
        elif call.data == "crypto_charge":
            async with db.execute("SELECT value FROM settings WHERE key='nowpayments_api'") as c: row = await c.fetchone()
            api_key = row[0] if row else None
            
            if not api_key or api_key == "YOUR_API_KEY":
                await call.answer("❌ درگاه کریپتو توسط ادمین فعال نشده است.", show_alert=True)
                return
                
            # ارسال درخواست فاکتور نمونه به صرافی کریپتو
            await call.edit_message_text("🪙 در حال تولید لینک پرداخت کریپتو (TRX-USDT) از صرافی...")
            # در سیستم واقعی در این بخش ریکوئست به NowPayments ارسال می‌شود و لینک فاکتور پرداخت تحویل کاربر می‌گردد
            await call.message.reply_text("🔗 فاکتور صرافی ایجاد شد.\nمبلغ: 5 USDT\nآدرس پرداخت جهت شارژ اتوماتیک دیتابیس:\n`TXXXXX...`")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_commercial_db())
    app.run()

