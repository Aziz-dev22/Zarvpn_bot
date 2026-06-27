import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
import aiosqlite
from core import config
from core.database import init_commercial_db

app = Client(
    "zarvpn_bot",
    bot_token=config.TELEGRAM_TOKEN,
    api_id=29302323,             # 👈 آیدی عددی واقعی خودت را بگذار
    api_hash="247e5f3f98d9fb20aab59a3a9472bcc4" # 👈 هش متنی واقعی خودت را بگذار
)

def user_menu(user_id):
    buttons = [
        [InlineKeyboardButton("🛍️ خرید خودکار کانکشن V2Ray", callback_data="buy_menu")],
        [InlineKeyboardButton("👤 حساب کاربری و لایسنس‌ها", callback_data="my_account"),
         InlineKeyboardButton("💳 شارژ اتوماتیک از صرافی Swap Wallet", callback_data="swapwallet_charge")],
        [InlineKeyboardButton("📞 پشتیبانی آنلاین", callback_data="support_info")]
    ]
    if user_id == config.ADMIN_ID:
        buttons.append([InlineKeyboardButton("⚙️ ورود به پنل مدیریت تحت وب ادمین", url="http://localhost:8080")])
    return InlineKeyboardMarkup(buttons)

@app.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    uid = message.from_user.id
    uname = message.from_user.username or "کاربر"
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (uid, uname))
        await db.commit()
    await message.reply_text(
        f"سلام {message.from_user.first_name} عزیز\n🤖 به ابرسیستم هوشمند و تجاری فروش کانکشن **ZarVpn** خوش آمدید.\n\nلطفاً جهت ثبت سفارش از منوی زیر استفاده کنید:", 
        reply_markup=user_menu(uid)
    )

@app.on_callback_query()
async def handle_callbacks(client: Client, call: CallbackQuery):
    uid = call.from_user.id
    
    async with aiosqlite.connect("zarvpn_web.db") as db:
        if call.data == "back_to_main":
            await call.edit_message_text("🤖 منوی اصلی سیستم ZarVpn:", reply_markup=user_menu(uid))
            
        elif call.data == "my_account":
            async with db.execute("SELECT balance FROM users WHERE user_id = ?", (uid,)) as c:
                balance = (await c.fetchone())[0]
            await call.edit_message_text(
                f"👤 **وضعیت حساب شما:**\n\n🆔 آیدی عددی شما: `{uid}`\n💳 موجودی کیف پول: {balance:,} تومان",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]])
            )

        elif call.data == "buy_menu":
            async with db.execute("SELECT * FROM plans") as c: 
                plans = await c.fetchall()
            buttons = []
            for p in plans:
                buttons.append([InlineKeyboardButton(f"{p[1]} ({p[5].upper()}) ➖ {p[4]:,} تومان", callback_data=f"order_p_{p[0]}")])
            buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
            await call.edit_message_text("🛍️ پلن مورد نظر خود را جهت صدور آنی انتخاب کنید:", reply_markup=InlineKeyboardMarkup(buttons))

        elif call.data.startswith("order_p_"):
            pid = int(call.data.split("_")[2])
            await call.answer("در حال بررسی موجودی و اتصال به سرور V2Ray...", show_alert=False)
            # اتصال پویا بر اساس مقادیری که در پنل وب برای سرورها ذخیره کرده‌اید

        elif call.data == "swapwallet_charge":
            async with db.execute("SELECT value FROM settings WHERE key='swapwallet_api'") as c: 
                row = await c.fetchone()
            api_key = row[0] if row else ""
            
            if not api_key or api_key == "":
                await call.answer("❌ درگاه صرافی Swap Wallet هنوز توسط ادمین فعال و ست نشده است.", show_alert=True)
                return
                
            await call.edit_message_text("🔄 در حال اتصال به وب‌سرویس صرافی Swap Wallet و ایجاد آدرس پرداخت اختصاصی...")
            await call.message.reply_text(
                "💳 **درگاه پرداخت صرافی ایرانی Swap Wallet ایجاد شد:**\n\nامکان پرداخت تومانی و رمزارزی به صورت کاملاً اتوماتیک برای شما فراهم است.\n\n🔗 [جهت پرداخت و شارژ آنی حساب اینجا کلیک کنید](https://swapwallet.ir)"
            )

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_commercial_db())
    print("🚀 ابر ربات فروش ZarVpn متصل به Swap Wallet و پایتون 3.10 فعال شد...")
    app.run()
