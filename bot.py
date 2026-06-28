import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message, WebAppInfo
import aiosqlite
from core import config
from panels.manager import MultiPanelManager

app = Client("zarvpn_bot", bot_token=config.TELEGRAM_TOKEN, api_id=23749219, api_hash="5f2bb6082cb0db48483bda1a63c6ea62")
panel_manager = MultiPanelManager()

async def get_user_menu(user_id):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        async with db.execute("SELECT value FROM settings WHERE key='test_status'") as c: test_status = (await c.fetchone())[0]
        async with db.execute("SELECT value FROM settings WHERE key='miniapp_url'") as c: m_url = (await c.fetchone())[0]
    
    buttons = []
    if test_status == "on":
        buttons.append([InlineKeyboardButton("🎁 دریافت تست رایگان (تک دکمه بالا)", callback_data="get_free_test")])
    buttons.append([InlineKeyboardButton("🛍️ خرید اشتراک جدید", callback_data="buy_menu"), InlineKeyboardButton("🛠️ مدیریت سرویس‌ها", callback_data="manage_services")])
    buttons.append([InlineKeyboardButton("💰 کیف پول و شارژ", callback_data="charge_menu"), InlineKeyboardButton("👥 زیرمجموعه‌گیری", callback_data="ref_menu")])
    
    # بند ۴: تبدیل بخش مدیریت و سرویس‌ها به مینی‌اپ شیک کاربری و ادمین
    buttons.append([InlineKeyboardButton("📱 ورود به مینی‌اپ ZarVpn", web_app=WebAppInfo(url=f"{m_url}/miniapp?user_id={user_id}"))])
    if str(user_id) == str(config.ADMIN_ID):
        buttons.append([InlineKeyboardButton("⚙️ پنل مدیریت فوق پیشرفته ادمین (مینی‌اپ)", web_app=WebAppInfo(url=f"{m_url}/"))])
        buttons.append([InlineKeyboardButton("🛠️ مدیریت ادمین (درون ربات)", callback_data="admin_bot_menu")])
    return InlineKeyboardMarkup(buttons)

@app.on_message(filters.command("start"))
async def start(c, m):
    await m.reply_text("🤖 به سیستم مدیریت یکپارچه ZarVpn خوش آمدید:", reply_markup=await get_user_menu(m.from_user.id))

@app.on_callback_query()
async def callbacks(client: Client, call: CallbackQuery):
    uid = call.from_user.id
    async with aiosqlite.connect("zarvpn_web.db") as db:
        if call.data == "admin_bot_menu" and str(uid) == str(config.ADMIN_ID):
            # بند ۲: نمایش دکمه مدیریت کاربران
            btns = [
                [InlineKeyboardButton("👥 مدیریت کاربران سیستم", callback_data="bot_manage_users")],
                [InlineKeyboardButton("🔌 اتصال دکمه‌ای پنل مرزبان", callback_data="bot_conn_marzban")],
                [InlineKeyboardButton("🔌 اتصال دکمه‌ای پنل سنایی", callback_data="bot_conn_xui")],
                [InlineKeyboardButton("🔌 اتصال دکمه‌ای کانکتیکس", callback_data="bot_conn_connectix")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]
            ]
            await call.edit_message_text("⚙️ منوی مدیریت درون ربات ادمین:", reply_markup=InlineKeyboardMarkup(btns))

        # بند ۲: لیست کاربران به صورت دکمه شیشه‌ای
        elif call.data == "bot_manage_users" and str(uid) == str(config.ADMIN_ID):
            async with db.execute("SELECT user_id, username FROM users LIMIT 10") as c: users = await c.fetchall()
            btns = [[InlineKeyboardButton(f"👤 {u[1]} ({u[0]})", callback_data=f"adm_usr_{u[0]}")] for u in users]
            btns.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_bot_menu")])
            await call.edit_message_text("👥 یکی از کاربران را جهت مدیریت کامل انتخاب کنید:", reply_markup=InlineKeyboardMarkup(btns))

        # بند ۲: جزئیات و دکمه‌های افزایش/کاهش و مدیریت سرویس‌های کاربر
        elif call.data.startswith("adm_usr_") and str(uid) == str(config.ADMIN_ID):
            target_id = int(call.data.split("_")[2])
            async with db.execute("SELECT username, balance FROM users WHERE user_id=?", (target_id,)) as c: usr = await c.fetchone()
            text = f"👤 کاربر: {usr[0]}\n🆔 آیدی: `{target_id}`\n💰 موجودی: {usr[1]:,} تومان"
            btns = [
                [InlineKeyboardButton("➕ افزایش موجودی", callback_data=f"b_plus_{target_id}"), InlineKeyboardButton("➖ کاهش موجودی", callback_data=f"b_minus_{target_id}")],
                [InlineKeyboardButton("📦 سرویس‌های کاربر", callback_data=f"b_srvs_{target_id}")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="bot_manage_users")]
            ]
            await call.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btns))

        # بند ۲: نمایش سرویس‌های کاربر به صورت شیشه‌ای با قابلیت حذف و تغییر
        elif call.data.startswith("b_srvs_") and str(uid) == str(config.ADMIN_ID):
            target_id = int(call.data.split("_")[2])
            async with db.execute("SELECT id, plan_name FROM orders WHERE user_id=?", (target_id,)) as c: srvs = await c.fetchall()
            btns = []
            for s in srvs:
                btns.append([InlineKeyboardButton(f"📦 {s[1]} (حذف)", callback_data=f"b_delsrv_{s[0]}_{target_id}")])
            btns.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"adm_usr_{target_id}")])
            await call.edit_message_text("🛠️ لیست سرویس‌های کاربر؛ جهت حذف روی آن کلیک کنید:", reply_markup=InlineKeyboardMarkup(btns))

        elif call.data.startswith("b_delsrv_") and str(uid) == str(config.ADMIN_ID):
            oid, target_id = int(call.data.split("_")[2]), int(call.data.split("_")[3])
            await db.execute("DELETE FROM orders WHERE id=?", (oid,))
            await db.commit()
            await call.answer("✅ سرویس حذف شد", show_alert=True)
            # بازگشت به منوی سرویس‌ها
            async with db.execute("SELECT id, plan_name FROM orders WHERE user_id=?", (target_id,)) as c: srvs = await c.fetchall()
            btns = [[InlineKeyboardButton(f"📦 {s[1]} (حذف)", callback_data=f"b_delsrv_{s[0]}_{target_id}")] for s in srvs]
            btns.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"adm_usr_{target_id}")])
            await call.edit_message_text("🛠️ لیست سرویس‌های کاربر؛ جهت حذف روی آن کلیک کنید:", reply_markup=InlineKeyboardMarkup(btns))

        # بند ۱: پیاده‌سازی گام به گام دریافت آدرس، یوزر و پسورد در ربات به کمک فیلتر ریپلای یا وضعیت آماده‌سازی می‌شود
        elif call.data in ["bot_conn_marzban", "bot_conn_xui", "bot_conn_connectix"] and str(uid) == str(config.ADMIN_ID):
            p_name = call.data.split("_")[2]
            await call.edit_message_text(f"📌 جهت اتصال دکمه‌ای به پنل {p_name.upper()}، لطفاً از دستور زیر در چت استفاده کنید تا اعتبار سنجی شود:\n\n`/connect {p_name} URL USER PASS`")

        elif call.data == "back_to_main":
            await call.edit_message_text("🤖 منوی اصلی سیستم ZarVpn:", reply_markup=await get_user_menu(uid))

# دستور فعال تایید اتصال دکمه‌ای درون ربات
@app.on_message(filters.command("connect") & filters.user(int(config.ADMIN_ID)))
async def bot_cmd_connect(client, message):
    if len(message.command) < 5: return
    ptype, url, user, password = message.command[1], message.command[2], message.command[3], message.command[4]
    
    # بند ۱: بررسی مشخصات ورود موفق یا اشتباه
    success = await panel_manager.verify_and_connect(ptype, url, user, password)
    if not success:
        await message.reply_text("❌ مشخصات اشتباه است! اطلاعات اتصال تایید نشد.")
        return
        
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("INSERT OR REPLACE INTO server_settings (panel_type, url, username, password) VALUES (?, ?, ?, ?)", (ptype, url, user, password))
        await db.commit()
    await message.reply_text("✅ شما با موفقیت وارد شدید و پنل متصل شد.")

if __name__ == "__main__":
    app.run()
