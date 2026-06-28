import asyncio
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message, WebAppInfo
from pyrogram.enums import ChatMemberStatus
import aiosqlite
from core import config
from core.database import init_commercial_db
from panels.manager import MultiPanelManager

app = Client(
    "zarvpn_bot",
    bot_token=config.TELEGRAM_TOKEN,
    api_id=23749219,             
    api_hash="5f2bb6082cb0db48483bda1a63c6ea62" 
)

panel_manager = MultiPanelManager()

# قابلیت ۸: حذف لایه عضویت اجباری برای ادمین اصلی
async def is_subscribed(client, user_id):
    if str(user_id) == str(config.ADMIN_ID):
        return True
    async with aiosqlite.connect("zarvpn_web.db") as db:
        async with db.execute("SELECT value FROM settings WHERE key='channel_id'") as c: channel = (await c.fetchone())[0]
    try:
        member = await client.get_chat_member(channel, user_id)
        return member.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]
    except: return False

# قابلیت ۱ و ۲ و ۱۰: ساخت و چیدمان دقیقاً مهندسی‌شده دکمه‌ها طبق بندهای درخواستی
async def get_user_menu(user_id):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        async with db.execute("SELECT value FROM settings WHERE key='test_status'") as c: test_status = (await c.fetchone())[0]
        async with db.execute("SELECT value FROM settings WHERE key='miniapp_url'") as c: base_m_url = (await c.fetchone())[0]

    buttons = []
    
    # بند ۱: اگر تست فعال باشد گزینه اول و تک دکمه است، در غیر این صورت کاملا محو می‌شود
    if test_status == "on":
        buttons.append([InlineKeyboardButton("🎁 دریافت تست رایگان (۲ گیگابایت)", callback_data="get_free_test")])
        
    # بند ۲: دکمه خرید گزینه دوم و مدیریت سرویس‌ها گزینه سوم به صورت جفت کنار هم زیر دکمه تست
    buttons.append([
        InlineKeyboardButton("🛍️ خرید اشتراک جدید", callback_data="buy_menu"),
        InlineKeyboardButton("🛠️ مدیریت سرویس‌ها", callback_data="manage_services")
    ])
    
    # بند ۲: دکمه کیف پول گزینه سوم مالی و زیرمجموعه‌گیری دکمه چهارم کنار هم زیر ردیف قبل
    buttons.append([
        InlineKeyboardButton("💰 کیف پول و شارژ", callback_data="charge_menu"),
        InlineKeyboardButton("👥 زیرمجموعه‌گیری", callback_data="ref_menu")
    ])
    
    # بند ۱۰: دکمه ورود به مینی‌اپ شیک سیستم همراه با انتقال شناسه کاربر
    buttons.append([InlineKeyboardButton("🚀 ورود به مینی‌اپ اختصاصی ZarVpn", web_app=WebAppInfo(url=f"{base_m_url}/miniapp?user_id={user_id}"))])
    
    buttons.append([InlineKeyboardButton("👤 حساب من", callback_data="my_account"), InlineKeyboardButton("📞 پشتیبانی", callback_data="support_info")])
    
    if str(user_id) == str(config.ADMIN_ID):
        buttons.append([InlineKeyboardButton("⚙️ پنل مدیریت ادمین ربات", callback_data="admin_panel")])
        
    return InlineKeyboardMarkup(buttons)

# بند ۷: فرآیند خودکار پشتیبان‌گیری دیتابیس به کانال معرفی شده ادمین
async def auto_backup_task():
    while True:
        await asyncio.sleep(21600) # هر ۶ ساعت بکاپ خودکار
        try:
            async with aiosqlite.connect("zarvpn_web.db") as db:
                async with db.execute("SELECT value FROM settings WHERE key='backup_channel'") as c: b_ch = (await c.fetchone())[0]
            if os.path.exists("zarvpn_web.db") and b_ch.startswith("@"):
                await app.send_document(chat_id=b_ch, document="zarvpn_web.db", caption="💾 نسخه پشتیبان زمان‌بندی شده و خودکار دیتابیس سیستم")
        except: pass

@app.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    uid = message.from_user.id
    uname = message.from_user.username or "user"
    
    if not await is_subscribed(client, uid):
        async with aiosqlite.connect("zarvpn_web.db") as db:
            async with db.execute("SELECT value FROM settings WHERE key='channel_id'") as c: ch = (await c.fetchone())[0]
        await message.reply_text(f"❌ جهت استفاده عضو کانال شوید:\n📢 {ch}")
        return

    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (uid, uname))
        await db.commit()
        
    await message.reply_text("🤖 به ابر سیستم فروش v2ray خوش آمدید:", reply_markup=await get_user_menu(uid))

@app.on_callback_query()
async def handle_callbacks(client: Client, call: CallbackQuery):
    uid = call.from_user.id
    if not await is_subscribed(client, uid): return
    
    async with aiosqlite.connect("zarvpn_web.db") as db:
        if call.data == "back_to_main":
            await call.edit_message_text("🤖 منوی اصلی سیستم ZarVpn:", reply_markup=await get_user_menu(uid))
            
        # بند ۳: نمایش لایو موجودی دقیق کاربر داخل خود منوی کیف پول
        elif call.data == "charge_menu":
            async with db.execute("SELECT balance FROM users WHERE user_id = ?", (uid,)) as c: balance = (await c.fetchone())[0]
            text = f"💰 **بخش کیف پول دیجیتال**\n\n💵 موجودی فعلی شما: **{balance:,} تومان**\n\n📌 جهت افزایش اعتبار یکی از روش‌های زیر را انتخاب کنید:"
            btns = [
                [InlineKeyboardButton("🪙 درگاه صرافی سواپ‌ولت", callback_data="pay_swap")],
                [InlineKeyboardButton("💳 کارت به کارت", callback_data="pay_card"), InlineKeyboardButton("⚡ ارز دیجیتال", callback_data="pay_crypto")],
                [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_main")]
            ]
            await call.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btns))

        elif call.data == "get_free_test":
            async with db.execute("SELECT value FROM settings WHERE key='test_status'") as s: 
                if (await s.fetchone())[0] == "off": await call.answer("❌ اکانت تست غیرفعال شده است.", show_alert=True); return
            async with db.execute("SELECT used_test FROM users WHERE user_id = ?", (uid,)) as c:
                if (await c.fetchone())[0] == 1: await call.answer("❌ شما قبلاً تست گرفته‌اید!", show_alert=True); return
            
            await call.edit_message_text("🔄 در حال ارتباط با سرور و صدور کانکشن تست...")
            res = await panel_manager.create_account("connectix", f"test_{uid}", 2, 1)
            if res["status"] == "success":
                await db.execute("UPDATE users SET used_test = 1 WHERE user_id = ?", (uid,))
                await db.execute("INSERT INTO orders (user_id, plan_name, sub_link, v2ray_username, panel_type) VALUES (?, 'تست رایگان', ?, ?, 'connectix')", (uid, res["link"], f"test_{uid}"))
                await db.commit()
                await call.message.reply_text(f"✅ **کانکشن تست صادر شد:**\n\n`{res['link']}`")
            else:
                await call.message.reply_text(f"❌ خطای صدور سرور: {res['message']}")

        # بند ۴ و ۵ و ۶ و ۹: مدیریت کامل از درون خود ربات تلگرام توسط ادمین
        elif call.data == "admin_panel" and str(uid) == str(config.ADMIN_ID):
            async with db.execute("SELECT value FROM settings WHERE key='test_status'") as s: t_status = (await s.fetchone())[0]
            t_text = "🔴 غیرفعال‌سازی تست" if t_status == "on" else "🟢 فعال‌سازی تست"
            buttons = [
                [InlineKeyboardButton(t_text, callback_data="bot_toggle_test")],
                [InlineKeyboardButton("🔌 اتصال پنل جدید در ربات", callback_data="bot_connect_panel")],
                [InlineKeyboardButton("👥 لیست کاربران و شارژ", callback_data="bot_manage_users")],
                [InlineKeyboardButton("💾 بکاپ‌گیری و ارسال به کانال", callback_data="bot_instant_backup")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]
            ]
            await call.edit_message_text("⚙️ **پنل مدیریت ادمین درون ربات:**\n\nتمام اختیارات پنل وب در اینجا هم در دسترس شماست.", reply_markup=InlineKeyboardMarkup(buttons))

        elif call.data == "bot_toggle_test" and str(uid) == str(config.ADMIN_ID):
            async with db.execute("SELECT value FROM settings WHERE key='test_status'") as s: cur = (await s.fetchone())[0]
            await db.execute("UPDATE settings SET value=? WHERE key='test_status'", ("off" if cur == "on" else "on",))
            await db.commit()
            await call.answer("وضعیت سوئیچ تست تغییر کرد", show_alert=True)
            await call.edit_message_text("🤖 منوی اصلی سیستم ZarVpn:", reply_markup=await get_user_menu(uid))

        elif call.data == "bot_instant_backup" and str(uid) == str(config.ADMIN_ID):
            async with db.execute("SELECT value FROM settings WHERE key='backup_channel'") as c: b_ch = (await c.fetchone())[0]
            if os.path.exists("zarvpn_web.db") and b_ch.startswith("@"):
                await app.send_document(chat_id=b_ch, document="zarvpn_web.db", caption="💾 فایل پشتیبان درخواستی ادمین از درون ربات")
                await call.answer("بکاپ صادر و به کانال ارسال شد.", show_alert=True)

        elif call.data == "bot_manage_users" and str(uid) == str(config.ADMIN_ID):
            await call.edit_message_text("📌 جهت مدیریت و شارژ کاربران در ربات از این دستور استفاده کنید:\n\n`/charge USERID AMOUNT`\n\nمثال:\n`/charge 1234567 50000`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")]]))

        elif call.data == "bot_connect_panel" and str(uid) == str(config.ADMIN_ID):
            await call.edit_message_text("📌 جهت اتصال پنل جدید از طریق ربات از فرمت زیر استفاده کنید:\n\n`/connect PANEL_TYPE URL USER PASSWORD`\n\nمثال:\n`/connect xui http://1.1.1.1:8080 admin admin123`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")]]))

# هندلر دستور اتصال پنل از درون ربات
@app.on_message(filters.command("connect") & filters.user(int(config.ADMIN_ID)))
async def cmd_connect_panel(client: Client, message: Message):
    if len(message.command) < 5: return
    ptype, url, user, password = message.command[1], message.command[2], message.command[3], message.command[4]
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("INSERT OR REPLACE INTO server_settings (panel_type, url, username, password) VALUES (?, ?, ?, ?)", (ptype, url, user, password))
        await db.commit()
    await message.reply_text(f"✅ پنل {ptype.upper()} با موفقیت از طریق ربات متصل شد.")

# هندلر شارژ از درون ربات
@app.on_message(filters.command("charge") & filters.user(int(config.ADMIN_ID)))
async def cmd_charge_bot(client: Client, message: Message):
    if len(message.command) < 3: return
    target_id, amount = int(message.command[1]), int(message.command[2])
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, target_id))
        await db.commit()
    await message.reply_text("✅ عملیات تغییر موجودی انجام شد.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_commercial_db())
    loop.create_task(auto_backup_task())
    app.run()
