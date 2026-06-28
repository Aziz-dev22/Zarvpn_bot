import asyncio
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message, WebAppInfo
from pyrogram.enums import ChatMemberStatus
import aiosqlite
from core import config
from panels.manager import MultiPanelManager

app = Client("zarvpn_bot", bot_token=config.TELEGRAM_TOKEN, api_id=23749219, api_hash="5f2bb6082cb0db48483bda1a63c6ea62")
panel_manager = MultiPanelManager()

async def is_subscribed(client, user_id):
    # ادمین به صورت کامل از قفل کانال عبور می‌کند
    if str(user_id) == str(config.ADMIN_ID): 
        return True 
        
    async with aiosqlite.connect("zarvpn_web.db") as db:
        async with db.execute("SELECT value FROM settings WHERE key='channel_id'") as c: 
            row = await c.fetchone()
            channel = row[0] if row else None
        async with db.execute("SELECT value FROM settings WHERE key='sub_status'") as c:
            row_status = await c.fetchone()
            sub_status = row_status[0] if row_status else "off"
            
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
        async with db.execute("SELECT value FROM settings WHERE key='test_status'") as c: 
            row = await c.fetchone()
            test_status = row[0] if row else "off"
        
    server_ip = "178.105.165.200" 
    m_url = f"http://{server_ip}:8080" 

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
    
    buttons.append([InlineKeyboardButton("📱 ورود به مینی‌اپ کاربری", web_app=WebAppInfo(url=f"{m_url}/miniapp?user_id={user_id}"))])
    
    if str(user_id) == str(config.ADMIN_ID):
        buttons.append([InlineKeyboardButton("⚙️ پنل مینی‌اپ مدیریت کامل ادمین", web_app=WebAppInfo(url=f"{m_url}/?admin_auth_id={user_id}"))])
        buttons.append([InlineKeyboardButton("🛠️ پنل مدیریت (درون ربات)", callback_data="admin_bot_menu")])
    return InlineKeyboardMarkup(buttons)

@app.on_message(filters.command("start"))
async def start(c, m):
    uid = m.from_user.id
    uname = m.from_user.username or "User"
    
    # 🔥 حل باگ کرش دیتابیس: ذکر دقیق نام ستون‌ها برای جلوگیری از ارور ساختاری دیتابیس
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, balance, role, referred_by, used_test) VALUES (?, ?, 0, 'user', 0, 0)", 
            (uid, uname)
        )
        await db.commit()

    # بررسی قفل کانال عضویت اجباری
    if not await is_subscribed(c, uid):
        async with aiosqlite.connect("zarvpn_web.db") as db:
            async with db.execute("SELECT value FROM settings WHERE key='channel_id'") as c_db: 
                row = await c_db.fetchone()
                channel = row[0] if row else "@your_channel"
        
        await m.reply_text(
            f"❌ برای استفاده از خدمات ربات، ابتدا باید در کانال ما عضو شوید:\n\n📣 {channel}\n\nپس از عضویت، مجدداً دستور /start را ارسال کنید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 ورود به کانال", url=f"https://t.me/{channel.replace('@','')}")]] if channel.startswith('@') else [])
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
            
        elif call.data == "charge_menu":
            async with db.execute("SELECT balance FROM users WHERE user_id = ?", (uid,)) as c: balance = (await c.fetchone())[0]
            async with db.execute("SELECT * FROM settings") as c: settings = dict(await c.fetchall())
            
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
            async with db.execute("SELECT user_id, username FROM users LIMIT 10") as c: users = await c.fetchall()
            btns = [[InlineKeyboardButton(f"👤 {u[1]} ({u[0]})", callback_data=f"adm_usr_{u[0]}")] for u in users]
            btns.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_bot_menu")])
            await call.edit_message_text("👥 کاربر مورد نظر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(btns))

        elif call.data.startswith("adm_usr_") and str(uid) == str(config.ADMIN_ID):
            t_id = int(call.data.split("_")[2])
            async with db.execute("SELECT username, balance FROM users WHERE user_id=?", (t_id,)) as c: usr = await c.fetchone()
            text = f"👤 کاربر: {usr[0]}\n🆔 آیدی: `{t_id}`\n💰 موجودی: {usr[1]:,} تومان"
            btns = [
                [InlineKeyboardButton("➕ افزایش موجودی", callback_data=f"b_inc_{t_id}"), InlineKeyboardButton("➖ کاهش موجودی", callback_data=f"b_dec_{t_id}")],
                [InlineKeyboardButton("📦 سرویس‌های کاربر", callback_data=f"b_srv_{t_id}")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="bot_manage_users")]
            ]
            await call.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btns))

        elif call.data.startswith("b_inc_") and str(uid) == str(config.ADMIN_ID):
            t_id = int(call.data.split("_")[2])
            await db.execute("UPDATE users SET balance = balance + 50000 WHERE user_id=?", (t_id,))
            await db.commit()
            await call.answer("✅ 50,000 تومان اضافه شد", show_alert=True)
            
        elif call.data.startswith("b_dec_") and str(uid) == str(config.ADMIN_ID):
            t_id = int(call.data.split("_")[2])
            await db.execute("UPDATE users SET balance = max(0, balance - 50000) WHERE user_id=?", (t_id,))
            await db.commit()
            await call.answer("❌ 50,000 تومان کسر شد", show_alert=True)

        elif call.data in ["bot_conn_xui", "bot_conn_marzban"] and str(uid) == str(config.ADMIN_ID):
            p_name = call.data.split("_")[2]
            await call.edit_message_text(f"📌 جهت اتصال دکمه‌ای، دستور زیر را بفرستید:\n\n`/connect {p_name} URL USER PASS`")

@app.on_message(filters.command("connect") & filters.user(int(config.ADMIN_ID)))
async def bot_cmd_connect(client, message):
    if len(message.command) < 4: return
    ptype, url, user = message.command[1], message.command[2], message.command[3]
    password = message.command[4] if len(message.command) > 4 else ""
    
    success = await panel_manager.verify_and_connect(ptype, url, user, password)
    if not success:
        await message.reply_text("❌ مشخصات اشتباه است! اتصال برقرار نشد.")
        return
        
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("INSERT OR REPLACE INTO server_settings (panel_type, url, username, password) VALUES (?, ?, ?, ?)", (ptype, url, user, password))
        await db.commit()
    await message.reply_text("✅ شما با موفقیت وارد شدید و پنل متصل شد.")

if __name__ == "__main__":
    app.run()
