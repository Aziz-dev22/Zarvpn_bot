import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message, WebAppInfo
from pyrogram.enums import ChatMemberStatus
import aiosqlite
from core import config
from panels.manager import MultiPanelManager

app = Client("zarvpn_bot", bot_token=config.TELEGRAM_TOKEN, api_id=23749219, api_hash="5f2bb6082cb0db48483bda1a63c6ea62")
panel_manager = MultiPanelManager()

async def is_subscribed(client, user_id):
    if str(user_id) == str(config.ADMIN_ID): 
        return True 
        
    async with aiosqlite.connect("zarvpn_web.db") as db:
        try:
            async with db.execute("SELECT value FROM settings WHERE key='channel_id'") as c: 
                row = await c.fetchone()
                channel = row[0] if row else None
            async with db.execute("SELECT value FROM settings WHERE key='sub_status'") as c:
                row_status = await c.fetchone()
                sub_status = row_status[0] if row_status else "off"
        except Exception:
            return True
            
    if sub_status == "off" or not channel or channel == "@your_channel": 
        return True
        
    try:
        member = await client.get_chat_member(channel, user_id)
        if member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
            return True
        return False
    except Exception as e: 
        print(f"Sub check log: {e}")
        return True

async def get_user_menu(user_id):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        try:
            async with db.execute("SELECT value FROM settings WHERE key='test_status'") as c: 
                row = await c.fetchone()
                test_status = row[0] if row else "off"
        except Exception:
            test_status = "off"
        
    buttons = []
    if test_status == "on":
        buttons.append([InlineKeyboardButton("🎁 دریافت تست رایگان", callback_data="get_free_test")])
        
    buttons.append([
        InlineKeyboardButton("🛍️ خرید اشتراک جدید", callback_data="buy_menu"),
        InlineKeyboardButton("🛠️ مدیریت سرویس‌ها", callback_data="manage_services")
    ])
    
    buttons.append([
        InlineKeyboardButton("💰 کیف پول و شارژ", callback_data="charge_menu"),
        InlineKeyboardButton("👥 زیرمجموعه‌گیری", callback_data="ref_menu")
    ])
    
    # 📌 تغییر موقت مینی‌آپ به دکمه درون ربات برای جلوگیری از ارور نبود HTTPS (SSL)
    buttons.append([InlineKeyboardButton("📱 ورود به بخش کاربری", callback_data="user_panel_fallback")])
    
    if str(user_id) == str(config.ADMIN_ID):
        buttons.append([InlineKeyboardButton("⚙️ پنل وب مدیریت (اطلاعات ورود)", callback_data="admin_web_info")])
        buttons.append([InlineKeyboardButton("🛠️ پنل مدیریت (درون ربات)", callback_data="admin_bot_menu")])
    return InlineKeyboardMarkup(buttons)

@app.on_message(filters.command("start"))
async def start(c, m):
    uid = m.from_user.id
    uname = m.from_user.username or "User"
    
    # ثبت کاربر در بلوک try/except برای جلوگیری از هرگونه توقف ربات به دلیل تداخل ستون‌ها
    try:
        async with aiosqlite.connect("zarvpn_web.db") as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, username, balance, role, referred_by, used_test) VALUES (?, ?, 0, 'user', 0, 0)", 
                (uid, uname)
            )
            await db.commit()
    except Exception as e:
        print(f"Database insert log: {e}")

    if not await is_subscribed(c, uid):
        async with aiosqlite.connect("zarvpn_web.db") as db:
            try:
                async with db.execute("SELECT value FROM settings WHERE key='channel_id'") as c_db: 
                    row = await c_db.fetchone()
                    channel = row[0] if row else "@your_channel"
            except Exception:
                channel = "@your_channel"
        
        clean_channel_username = channel.replace('@', '').strip()
        # تلگرام لینک های بدون پروتکل یا حاوی آیدی پیشفرض را قبول نمیکند
        if clean_channel_username and clean_channel_username != "your_channel" and not clean_channel_username.startswith("http"):
            channel_url = f"https://t.me/{clean_channel_username}"
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("📢 ورود به کانال", url=channel_url)]])
        else:
            reply_markup = None
            
        await m.reply_text(
            f"❌ برای استفاده از خدمات ربات، ابتدا باید در کانال ما عضو شوید:\n\n📣 {channel}\n\nپس از عضویت، مجدداً دستور /start را ارسال کنید.",
            reply_markup=reply_markup
        )
        return

    await m.reply_text("🤖 به مگا سیستم فروش کانکشن خوش آمدید:", reply_markup=await get_user_menu(uid))

@app.on_callback_query()
async def callbacks(client: Client, call: CallbackQuery):
    uid = call.from_user.id
    
    if not await is_subscribed(client, uid): 
        await call.answer("⚠️ شما ابتدا باید در کانال عضو شوید!", show_alert=True)
        return
    
    async with aiosqlite.connect("zarvpn_web.db") as db:
        if call.data == "back_to_main":
            await call.edit_message_text("🤖 منوی اصلی سیستم ZarVpn:", reply_markup=await get_user_menu(uid))
            
        elif call.data == "admin_web_info" and str(uid) == str(config.ADMIN_ID):
            await call.answer()
            await call.message.reply_text("🌐 **آدرس پنل تحت وب مدیریت:**\n\n🔗 http://178.105.165.200:8080/\n\n📌 نکته: به دلیل عدم وجود SSL (https)، از دکمه مینی‌آپ مستقیم حذف شده و باید از طریق مرورگر گوشی وارد آن شوید.")

        elif call.data == "user_panel_fallback":
            await call.answer("📱 این بخش به زودی فعال می‌شود. در حال حاضر از منوی دکمه‌ای ربات استفاده کنید.", show_alert=True)

        elif call.data == "charge_menu":
            try:
                async with db.execute("SELECT balance FROM users WHERE user_id = ?", (uid,)) as c: balance = (await c.fetchone())[0]
                async with db.execute("SELECT * FROM settings") as c: settings = dict(await c.fetchall())
            except Exception:
                balance, settings = 0, {}
            
            text = f"💰 **بخش مدیریت مالی کیف پول**\n\n💵 موجودی فعلی: **{balance:,} تومان**\n\n📌 روش شارژ مورد نظر را انتخاب کنید:"
            btns = []
            if settings.get('swapwallet_status') == 'on': btns.append([InlineKeyboardButton("🪙 درگاه صرافی سواپ‌ولت", callback_data="pay_swap")])
            if settings.get('card_status') == 'on': btns.append([InlineKeyboardButton("💳 کارت به کارت", callback_data="pay_card")])
            if settings.get('crypto_status') == 'on': btns.append([InlineKeyboardButton("⚡ ارز دیجیتال تتر", callback_data="pay_crypto")])
            btns.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
            await call.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btns))

        elif call.data == "admin_bot_menu" and str(uid) == str(config.ADMIN_ID):
            btns = [
                [InlineKeyboardButton("👥 لیست دکمه‌ای کاربران", callback_data="bot_manage_users")],
                [InlineKeyboardButton("🔌 اتصال به سرور (X-UI)", callback_data="bot_conn_xui")],
                [InlineKeyboardButton("🔌 اتصال به سرور (مرزبان)", callback_data="bot_conn_marzban")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]
            ]
            await call.edit_message_text("⚙️ پنل مدیریت درون ربات ادمین:", reply_markup=InlineKeyboardMarkup(btns))

        elif call.data == "bot_manage_users" and str(uid) == str(config.ADMIN_ID):
            try:
                async with db.execute("SELECT user_id, username FROM users LIMIT 10") as c: users = await c.fetchall()
                btns = [[InlineKeyboardButton(f"👤 {u[1]} ({u[0]})", callback_data=f"adm_usr_{u[0]}")] for u in users]
            except Exception:
                btns = []
            btns.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_bot_menu")])
            await call.edit_message_text("👥 کاربر مورد نظر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(btns))

if __name__ == "__main__":
    app.run()

