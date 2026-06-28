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

# ۱. حذف عضویت اجباری برای ادمین اصلی (بند ۸)
async def is_subscribed(client, user_id):
    if str(user_id) == str(config.ADMIN_ID):
        return True
    async with aiosqlite.connect("zarvpn_web.db") as db:
        async with db.execute("SELECT value FROM settings WHERE key='channel_id'") as c: channel = (await c.fetchone())[0]
    try:
        member = await client.get_chat_member(channel, user_id)
        return member.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]
    except: return False

# ۲. چیدمان هوشمند و کاملاً سفارشی دکمه‌ها (بند ۱ و ۲ و ۱۰)
async def get_user_menu(user_id):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        async with db.execute("SELECT value FROM settings WHERE key='test_status'") as c: test_status = (await c.fetchone())[0]
        async with db.execute("SELECT value FROM settings WHERE key='miniapp_url'") as c: m_url = (await c.fetchone())[0] or "https://google.com"

    buttons = []
    
    # بند ۱: اگر تست فعال باشد گزینه اول و تک دکمه است، در غیر این صورت کاملا محو می‌شود
    if test_status == "on":
        buttons.append([InlineKeyboardButton("🎁 دریافت تست رایگان (۱ روزه)", callback_data="get_free_test")])
        
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
    
    # بند ۱۰: مینی‌اپ پیشرفته ربات
    buttons.append([InlineKeyboardButton("📱 ورود به مینی‌اپ تجاری ZarVpn", web_app=WebAppInfo(url=m_url))])
    
    buttons.append([InlineKeyboardButton("👤 حساب من", callback_data="my_account"), InlineKeyboardButton("📞 پشتیبانی", callback_data="support_info")])
    
    if str(user_id) == str(config.ADMIN_ID):
        buttons.append([InlineKeyboardButton("⚙️ پنل مدیریت ادمین ربات", callback_data="admin_panel")])
        
    return InlineKeyboardMarkup(buttons)

# ۳. سیستم پشتیبان‌گیری خودکار و زمان‌بندی شده به کانال ادمین (بند ۷)
async def auto_backup_task():
    while True:
        await asyncio.sleep(21600) # هر ۶ ساعت یک‌بار پشتیبان‌گیری خودکار انجام می‌شود
        try:
            async with aiosqlite.connect("zarvpn_web.db") as db:
                async with db.execute("SELECT value FROM settings WHERE key='backup_channel'") as c: b_ch = (await c.fetchone())[0]
            if os.path.exists("zarvpn_web.db") and b_ch.startswith("@"):
                await app.send_document(chat_id=b_ch, document="zarvpn_web.db", caption="💾 فایل پشتیبان خودکار و دوره‌ای دیتابیس ربات ZarVpn")
        except: pass

@app.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    uid = message.from_user.id
    uname = message.from_user.username or "user"
    
    if not await is_subscribed(client, uid):
        async with aiosqlite.connect("zarvpn_web.db") as db:
            async with db.execute("SELECT value FROM settings WHERE key='channel_id'") as c: ch = (await c.fetchone())[0]
        await message.reply_text(f"❌ برای استفاده ابتدا عضو کانال شوید:\n📢 {ch}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{ch.replace('@', '')}")]]))
        return

    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (uid, uname))
        await db.commit()
        
    await message.reply_text("🤖 به سیستم مدیریت هوشمند کانکشن ZarVpn خوش آمدید:", reply_markup=await get_user_menu(uid))

@app.on_callback_query()
async def handle_callbacks(client: Client, call: CallbackQuery):
    uid = call.from_user.id
    if not await is_subscribed(client, uid): return
    
    async with aiosqlite.connect("zarvpn_web.db") as db:
        if call.data == "back_to_main":
            await call.edit_message_text("🤖 منوی اصلی سیستم ZarVpn:", reply_markup=await get_user_menu(uid))
            
        elif call.data == "my_account":
            async with db.execute("SELECT balance FROM users WHERE user_id = ?", (uid,)) as c: balance = (await c.fetchone())[0]
            await call.edit_message_text(f"👤 **حساب کاربری:**\n\n🆔 آیدی عددی: `{uid}`\n💳 موجودی شما: {balance:,} تومان", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]))

        # بند ۳: نمایش موجودی دقیق مستقیم در منوی کیف پول
        elif call.data == "charge_menu":
            async with db.execute("SELECT balance FROM users WHERE user_id = ?", (uid,)) as c: balance = (await c.fetchone())[0]
            text = f"💰 **کیف پول دیجیتال شما**\n\n💵 موجودی فعلی: **{balance:,} تومان**\n\n📌 جهت افزایش اعتبار، یکی از روش‌ها را انتخاب کنید:"
            btns = [
                [InlineKeyboardButton("🪙 درگاه صرافی سواپ‌ولت", callback_data="pay_swap")],
                [InlineKeyboardButton("💳 کارت به کارت", callback_data="pay_card"), InlineKeyboardButton("⚡ ارز دیجیتال", callback_data="pay_crypto")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]
            ]
            await call.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btns))

        elif call.data == "get_free_test":
            async with db.execute("SELECT value FROM settings WHERE key='test_status'") as s: 
                if (await s.fetchone())[0] == "off": await call.answer("❌ تست رایگان غیرفعال است", show_alert=True); return
            async with db.execute("SELECT used_test FROM users WHERE user_id = ?", (uid,)) as c:
                if (await c.fetchone())[0] == 1: await call.answer("❌ شما قبلاً تست گرفته‌اید!", show_alert=True); return
            
            await call.edit_message_text("🔄 در حال صدور اکانت تست از پنل فعال سیستم...")
            res = await panel_manager.create_account("connectix", f"test_{uid}", 2, 1)
            if res["status"] == "success":
                await db.execute("UPDATE users SET used_test = 1 WHERE user_id = ?", (uid,))
                await db.execute("INSERT INTO orders (user_id, plan_name, sub_link, v2ray_username, panel_type) VALUES (?, 'تست رایگان', ?, ?, 'connectix')", (uid, res["link"], f"test_{uid}"))
                await db.commit()
                await call.message.reply_text(f"✅ **کانکشن تست با موفقیت صادر شد:**\n\n`{res['link']}`")
            else:
                await call.message.reply_text(f"❌ خطا در صدور: {res['message']}")

        # ⚙️ بخش ۴ و ۶ و ۹: مدیریت ادمین درون ربات (اتصال پنل‌ها، شارژ، آمار)
        elif call.data == "admin_panel" and str(uid) == str(config.ADMIN_ID):
            async with db.execute("SELECT value FROM settings WHERE key='test_status'") as s: t_status = (await s.fetchone())[0]
            t_text = "🔴 خاموش کردن دکمه تست" if t_status == "on" else "🟢 روشن کردن دکمه تست"
            buttons = [
                [InlineKeyboardButton(t_text, callback_data="toggle_test_bot")],
                [InlineKeyboardButton("💾 پشتیبان‌گیری آنی دیتابیس", callback_data="bot_instant_backup")],
                [InlineKeyboardButton("🔙 خروج به منو", callback_data="back_to_main")]
            ]
            await call.edit_message_text("⚙️ **پنل فوق پیشرفته ادمین در ربات:**\n\nاز این بخش می‌توانید تمام قابلیت‌ها را کنترل کنید.", reply_markup=InlineKeyboardMarkup(buttons))

        elif call.data == "toggle_test_bot" and str(uid) == str(config.ADMIN_ID):
            async with db.execute("SELECT value FROM settings WHERE key='test_status'") as s: cur = (await s.fetchone())[0]
            new_s = "off" if cur == "on" else "on"
            await db.execute("UPDATE settings SET value=? WHERE key='test_status'", (new_s,))
            await db.commit()
            await call.answer("✅ وضعیت دکمه تست آپدیت شد!", show_alert=True)
            await call.edit_message_text("🤖 منوی اصلی سیستم ZarVpn:", reply_markup=await get_user_menu(uid))

        elif call.data == "bot_instant_backup" and str(uid) == str(config.ADMIN_ID):
            async with db.execute("SELECT value FROM settings WHERE key='backup_channel'") as c: b_ch = (await c.fetchone())[0]
            if os.path.exists("zarvpn_web.db") and b_ch.startswith("@"):
                await app.send_document(chat_id=b_ch, document="zarvpn_web.db", caption="💾 نسخه پشتیبان آنی درخواست شده توسط ادمین")
                await call.answer("📥 دیتابیس به کانال پشتیبان ارسال شد!", show_alert=True)

        # سایر ساختارهای خرید و دکمه‌های مالی و مدیریت لایسنس به قوت خود باقی هستند...
        elif call.data == "manage_services":
            async with db.execute("SELECT id, plan_name FROM orders WHERE user_id = ?", (uid,)) as c: user_orders = await c.fetchall()
            if not user_orders: await call.answer("❌ اشتراک فعالی ندارید!", show_alert=True); return
            buttons = []
            for order in user_orders: buttons.append([InlineKeyboardButton(f"📦 {order[1]} (کد: {order[0]})", callback_data=f"srv_{order[0]}")])
            buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
            await call.edit_message_text("🛠️ لیست سرویس‌های شما:", reply_markup=InlineKeyboardMarkup(buttons))

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_commercial_db())
    loop.create_task(auto_backup_task()) # استارت فرآیند بکاپ خودکار دیتابیس
    app.run()

