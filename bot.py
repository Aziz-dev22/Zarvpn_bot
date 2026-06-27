import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
import aiosqlite
from core import config
from core.database import init_commercial_db
from panels.connectix import ConnectixAPI

app = Client(
    "zarvpn_bot",
    bot_token=config.TELEGRAM_TOKEN,
    api_id=29302323,             # آیدی عددی واقعی شما
    api_hash="247e5f3f98d9fb20aab59a3a9472bcc4" # هش متنی واقعی شما
)

def user_menu(user_id):
    buttons = [
        [InlineKeyboardButton("🛍️ خرید خودکار کانکشن V2Ray", callback_data="buy_menu")],
        [InlineKeyboardButton("👤 حساب کاربری و لایسنس‌ها", callback_data="my_account"),
         InlineKeyboardButton("💳 شارژ اتوماتیک (Swap Wallet)", callback_data="swapwallet_charge")],
        [InlineKeyboardButton("📞 پشتیبانی آنلاین", callback_data="support_info")]
    ]
    if str(user_id) == str(config.ADMIN_ID):
        buttons.append([InlineKeyboardButton("⚙️ پنل مدیریت تحت وب ادمین", url="http://localhost:8080")])
    return InlineKeyboardMarkup(buttons)

@app.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    uid = message.from_user.id
    uname = message.from_user.username or "user"
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (uid, uname))
        await db.commit()
    await message.reply_text("🤖 به ابرسیستم هوشمند فروش خودکار ZarVpn خوش آمدید:", reply_markup=user_menu(uid))

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
                buttons.append([InlineKeyboardButton(f"{p[1]} ➖ {p[4]:,} تومان", callback_data=f"order_p_{p[0]}")])
            buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
            await call.edit_message_text("🛍️ پلن مورد نظر خود را جهت صدور آنی انتخاب کنید:", reply_markup=InlineKeyboardMarkup(buttons))

        elif call.data.startswith("order_p_"):
            pid = int(call.data.split("_")[2])
            async with db.execute("SELECT * FROM plans WHERE id = ?", (pid,)) as c: plan = await c.fetchone()
            async with db.execute("SELECT balance FROM users WHERE user_id = ?", (uid,)) as c: balance = (await c.fetchone())[0]
                
            if balance < plan[4]:
                await call.answer("❌ موجودی کیف پول شما کافی نیست!", show_alert=True)
                return
                
            await call.edit_message_text("🔄 موجودی تایید شد. اتصال به API نمایندگی Connectix و صدور لایسنس...")
            
            if plan[5] == "connectix":
                async with db.execute("SELECT value FROM settings WHERE key='connectix_token'") as s: cx_t = (await s.fetchone())[0]
                async with db.execute("SELECT value FROM settings WHERE key='connectix_endpoint'") as s: cx_e = (await s.fetchone())[0]
                
                cx_api = ConnectixAPI(api_token=cx_t, endpoint=cx_e)
                res = await cx_api.create_user(f"zar_{uid}", plan[2], plan[3])
                
                if res["status"] == "success":
                    await db.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (plan[4], uid))
                    await db.execute("INSERT INTO orders (user_id, plan_name, sub_link, v2ray_username, panel_type) VALUES (?, ?, ?, ?, 'connectix')", (uid, plan[1], res["link"], f"zar_{uid}"))
                    await db.commit()
                    await call.message.reply_text(f"✅ **سفارش شما با موفقیت در پنل نمایندگی ثبت شد!**\n\n🚀 **لینک کانکشن شما:**\n`{res['link']}`")
                else:
                    await call.message.reply_text(f"❌ خطای پنل نمایندگی: {res['message']}")

        elif call.data == "swapwallet_charge":
            swap_bot_link = f"https://t.me/SwapWalletBot?start=pay_{uid}"
            await call.edit_message_text(f"💳 **درگاه پرداخت اختصاصی ربات Swap Wallet صادر شد:**\n\n🔗 [ورود مستقیم به ربات پرداخت سواپ‌ولت]({swap_bot_link})")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_commercial_db())
    app.run()
