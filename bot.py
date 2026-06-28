import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyrogram.enums import ChatMemberStatus
import aiosqlite
from core import config

app = Client("zarvpn_bot", bot_token=config.TELEGRAM_TOKEN, api_id=23749219, api_hash="5f2bb6082cb0db48483bda1a63c6ea62")

async def is_subscribed(client, user_id):
    if str(user_id) == str(config.ADMIN_ID): return True 
    async with aiosqlite.connect("zarvpn_web.db") as db:
        try:
            async with db.execute("SELECT value FROM settings WHERE key='channel_id'") as c: row = await c.fetchone(); channel = row[0] if row else None
            async with db.execute("SELECT value FROM settings WHERE key='sub_status'") as c: row_status = await c.fetchone(); sub_status = row_status[0] if row_status else "off"
        except Exception: return True
    if sub_status == "off" or not channel or channel == "@your_channel": return True
    try:
        member = await client.get_chat_member(channel, user_id)
        return member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]
    except Exception: return True

async def get_user_menu(user_id):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        try:
            async with db.execute("SELECT value FROM settings WHERE key='test_status'") as c: row = await c.fetchone(); test_status = row[0] if row else "off"
        except Exception: test_status = "off"
        
    # 🔗 آدرس درخواستی و فیکس شده شما برای دکمه شیشه‌ای مستقیم
    m_url = "http://178.105.165.200:8080" 

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
    
    # 👑 دکمه شیشه‌ای لینک مستقیم ادمین (بدون کرش ۴۰۰ تلگرام)
    if str(user_id) == str(config.ADMIN_ID):
        buttons.append([InlineKeyboardButton("⚙️ ورود مستقیم به پنل تحت وب مدیریت", url=f"{m_url}/")])
        buttons.append([InlineKeyboardButton("🛠️ پنل مدیریت (درون ربات)", callback_data="admin_bot_menu")])
    return InlineKeyboardMarkup(buttons)

@app.on_message(filters.command("start"))
async def start(c, m):
    uid = m.from_user.id
    try:
        async with aiosqlite.connect("zarvpn_web.db") as db:
            await db.execute("INSERT OR IGNORE INTO users (user_id, username, balance, role, referred_by, used_test) VALUES (?, ?, 0, 'user', 0, 0)", (uid, m.from_user.username or "User"))
            await db.commit()
    except Exception: pass

    if not await is_subscribed(c, uid):
        async with aiosqlite.connect("zarvpn_web.db") as db:
            try: async with db.execute("SELECT value FROM settings WHERE key='channel_id'") as c_db: channel = (await c_db.fetchone())[0]
            except Exception: channel = "@your_channel"
        clean_ch = channel.replace('@', '').strip()
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("📢 ورود به کانال", url=f"https://t.me/{clean_ch}")]]) if clean_ch else None
        await m.reply_text(f"❌ ابتدا باید در کانال ما عضو شوید:\n📣 {channel}", reply_markup=markup)
        return
    await m.reply_text("🤖 به مگا سیستم فروش کانکشن خوش آمدید:", reply_markup=await get_user_menu(uid))

# بقیه منطق دکمه‌های بات تلگرام طبق کدهای تایید شده قبلی...
if __name__ == "__main__":
    app.run()
