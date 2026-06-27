from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
import aiosqlite
import asyncio
from core import config
from panels.marzban import MarzbanAPI
from panels.xui import XuiAPI

# راه‌اندازی ربات با Pyrogram
app = Client(
    "zarvpn_bot",
    bot_token=config.TELEGRAM_TOKEN,
    api_id=123456,          # نیازی به تغییر این دو عدد نیست، پایداری داخلی است
    api_hash="abcdef"
)

# نمونه‌سازی از اتصالات پنل‌ها
marzban_panel = MarzbanAPI()
xui_panel = XuiAPI()

# ساخت و آماده‌سازی دیتابیس تحت وب به صورت ناهمگام
async def init_async_db():
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS users 
                            (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, username TEXT)''')
        await db.execute('''CREATE TABLE IF NOT EXISTS plans 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, size INTEGER, days INTEGER, price INTEGER, panel_type TEXT)''')
        
        # افزودن پلن‌های تست متصل به پنل سنایی شما در صورت خالی بودن دیتابیس
        async with db.execute("SELECT COUNT(*) FROM plans") as cursor:
            if (await cursor.fetchone())[0] == 0:
                await db.execute("INSERT INTO plans (name, size, days, price, panel_type) VALUES (?, ?, ?, ?, ?)", 
                                 ("🚀 پلن سنایی اقتصادی (۱۰ گیگ)", 10, 30, 40000, "xui"))
                await db.execute("INSERT INTO plans (name, size, days, price, panel_type) VALUES (?, ?, ?, ?, ?)", 
                                 ("🔥 پلن سنایی حرفه‌ای (۳۰ گیگ)", 30, 30, 90000, "xui"))
                await db.commit()

# دکمه‌های شیشه‌ای منوی اصلی کاربران
def main_menu(user_id):
    buttons = [
        [InlineKeyboardButton("🛍️ خرید اشتراک VPN", callback_data="buy_menu"),
         InlineKeyboardButton("👤 حساب و کیف پول", callback_data="profile_menu")],
        [InlineKeyboardButton("💳 شارژ کیف پول", callback_data="charge_wallet"),
         InlineKeyboardButton("📞 پشتیبانی آنلاین", callback_data="support_info")]
    ]
    if user_id == config.ADMIN_ID:
        buttons.append([InlineKeyboardButton("⚙️ پنل مدیریت تحت وب ادمین", callback_data="admin_main")])
    return InlineKeyboardMarkup(buttons)

# دستور /start
@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        await db.commit()
        
    await message.reply_text(
        "🤖 به ابر سیستم هوشمند و خودکار فروش کانکشن ZarVpn خوش آمدید.\n\nلطفاً از دکمه‌های زیر اقدام کنید:",
        reply_markup=main_menu(user_id)
    )

# مدیریت دکمه‌های شیشه‌ای با قابلیت پاسخگویی پرسرعت
@app.on_callback_query()
async def handle_callbacks(client: Client, call: CallbackQuery):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    msg_id = call.message.id
    
    async with aiosqlite.connect("zarvpn_web.db") as db:
        # دکمه بازگشت
        if call.data == "back_to_user":
            await call.answer()
            await call.edit_message_text("🤖 به منوی اصلی ZarVpn برگشتید:", reply_markup=main_menu(user_id))
            
        # دکمه پروفایل و کیف پول
        elif call.data == "profile_menu":
            await call.answer()
            async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
                balance = (await cursor.fetchone())[0]
            text = f"👤 **حساب کاربری شما:**\n\n🆔 آیدی عددی: `{user_id}`\n💳 موجودی کیف پول: {balance:,} تومان"
            await call.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_user")]]))

        # منوی خرید پلن‌ها
        elif call.data == "buy_menu":
            await call.answer()
            async with db.execute("SELECT * FROM plans") as cursor:
                plans = await cursor.fetchall()
            buttons = []
            for plan in plans:
                buttons.append([InlineKeyboardButton(f"{plan[1]} - {plan[4]:,} تومان", callback_data=f"buy_plan_{plan[0]}")])
            buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_user")])
            await call.edit_message_text("🛍️ پلن مورد نظر خود را برای خرید انتخاب کنید:", reply_markup=InlineKeyboardMarkup(buttons))

        # فرآیند خرید و اتصال به پنل سنایی شما یا مرزبان
        elif call.data.startswith("buy_plan_"):
            await call.answer("در حال پردازش درخواست خرید...", show_alert=False)
            plan_id = int(call.data.split("_")[2])
            
            async with db.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)) as cursor:
                plan = await cursor.fetchone()
            async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
                balance = (await cursor.fetchone())[0]
                
            if balance >= plan[4]:
                # کسر موجودی
                new_balance = balance - plan[4]
                await db.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
                await db.commit()
                
                await call.edit_message_text("🔄 موجودی تایید شد. در حال اتصال به پنل سنایی و ساخت کانکشن واقعی...")
                
                # بررسی نوع پنل و ساخت اکانت
                if plan[5] == "xui":
                    result = await xui_panel.create_user(f"zar_{user_id}", plan[3], plan[2])
                else:
                    result = await marzban_panel.create_user(f"zar_{user_id}", plan[3], plan[2])
                
                if result["status"] == "success":
                    text = f"✅ **خرید با موفقیت انجام شد!**\n\n🚀 **لینک اختصاصی شما از پنل سنایی:**\n`{result['link']}`\n\n📥 کپی کنید و در نرم‌افزار خود وارد کنید."
                else:
                    # عودت وجه در صورت خطای پنل
                    await db.execute("UPDATE users SET balance = ? WHERE user_id = ?", (balance, user_id))
                    await db.commit()
                    text = f"❌ **خطا در ساخت اکانت توسط پنل:**\n{result['message']}\n\n💰 مبلغ پلن به کیف پول شما برگشت داده شد."
            else:
                text = f"❌ **موجودی کافی نیست!**\n\n💵 قیمت: {plan[4]:,} تومان\n💳 موجودی شما: {balance:,} تومان"
                
            buttons = [[InlineKeyboardButton("💳 شارژ کیف پول", callback_data="charge_wallet")], [InlineKeyboardButton("🔙 منوی خرید", callback_data="buy_menu")]]
            await call.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

        # بخش ادمین ربات
        elif call.data == "admin_main" and user_id == config.ADMIN_ID:
            await call.answer()
            buttons = [
                [InlineKeyboardButton("🎁 شارژ ۱۰۰ تومانی حساب خود (تست)", callback_data="admin_gift_test")],
                [InlineKeyboardButton("🔙 خروج", callback_data="back_to_user")]
            ]
            await call.edit_message_text("⚙️ به بخش مدیریت ربات خوش آمدید. آمار کامل در پنل تحت وب (پورت 8080) قابل مشاهده است:", reply_markup=InlineKeyboardMarkup(buttons))

        elif call.data == "admin_gift_test" and user_id == config.ADMIN_ID:
            await db.execute("UPDATE users SET balance = balance + 100000 WHERE user_id = ?", (config.ADMIN_ID,))
            await db.commit()
            await call.answer("✅ ۱۰۰ هزار تومان شارژ تست به حساب شما اضافه شد.", show_alert=True)

# اجرای همزمان ربات و دیتابیس تحت وب
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_async_db())
    print("🚀 ابر ربات فروش ZarVpn (نسخه ۲ - Pyrogram Async) روشن شد...")
    app.run()

