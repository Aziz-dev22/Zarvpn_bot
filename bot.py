import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyrogram.enums import ChatMemberStatus
import aiosqlite
from core import config
from panels.manager import MultiPanelManager

app = Client("zarvpn_bot", bot_token=config.TELEGRAM_TOKEN, api_id=23749219, api_hash="5f2bb6082cb0db48483bda1a63c6ea62")
panel_manager = MultiPanelManager()

async def is_subscribed(client, user_id):
    """بررسی وضعیت عضویت اجباری در کانال تلگرام"""
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
        return member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]
    except Exception: 
        return True

async def get_user_menu(user_id):
    """تولید داینامیک و بدون نقص دکمه‌های منوی اصلی"""
    async with aiosqlite.connect("zarvpn_web.db") as db:
        try:
            async with db.execute("SELECT value FROM settings WHERE key='test_status'") as c: 
                row = await c.fetchone()
                test_status = row[0] if row else "off"
        except Exception: 
            test_status = "off"
        
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
    
    if str(user_id) == str(config.ADMIN_ID):
        buttons.append([InlineKeyboardButton("⚙️ ورود مستقیم به پنل تحت وب مدیریت", url=f"{m_url}/")])
        buttons.append([InlineKeyboardButton("🛠️ پنل مدیریت (درون ربات)", callback_data="admin_bot_menu")])
    return InlineKeyboardMarkup(buttons)

@app.on_message(filters.command("start"))
async def start(c, m):
    uid = m.from_user.id
    uname = m.from_user.username or "User"
    
    # ثبت کاربر در دیتابیس با مدیریت ارور ستون‌ها
    try:
        async with aiosqlite.connect("zarvpn_web.db") as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, username, balance, role, referred_by, used_test) VALUES (?, ?, 0, 'user', 0, 0)", 
                (uid, uname)
            )
            await db.commit()
    except Exception: 
        pass

    if not await is_subscribed(c, uid):
        async with aiosqlite.connect("zarvpn_web.db") as db:
            try: 
                async with db.execute("SELECT value FROM settings WHERE key='channel_id'") as c_db: 
                    channel = (await c_db.fetchone())[0]
            except Exception: 
                channel = "@your_channel"
        clean_ch = channel.replace('@', '').strip()
        
        # دکمه شیشه‌ای تایید عضویت (پس از جوین شدن کاربر دوباره چک می‌کند)
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 ورود به کانال", url=f"https://t.me/{clean_ch}")],
            [InlineKeyboardButton("✅ عضو شدم (بررسی مجدد)", callback_data="check_sub_again")]
        ]) if clean_ch else None
        
        await m.reply_text(f"❌ برای استفاده از خدمات ربات، ابتدا باید در کانال ما عضو شوید:\n\n📣 {channel}\n\nپس از عضویت، دکمه بررسی مجدد را بزنید یا دستور /start را بفرستید.", reply_markup=markup)
        return

    await m.reply_text("🤖 به مگا سیستم فروش کانکشن خوش آمدید:\n📌 منوی زیر را جهت مدیریت حساب خود انتخاب کنید:", reply_markup=await get_user_menu(uid))

@app.on_callback_query()
async def callbacks(client: Client, call: CallbackQuery):
    uid = call.from_user.id
    
    # بررسی عضویت دوباره در کال‌بک تایید جوین
    if call.data == "check_sub_again":
        if await is_subscribed(client, uid):
            await call.message.delete()
            await client.send_message(uid, "🤖 عضویت شما تایید شد! به سیستم خوش آمدید:", reply_markup=await get_user_menu(uid))
        else:
            await call.answer("❌ شما هنوز در کانال عضو نشده‌اید!", show_alert=True)
        return

    if not await is_subscribed(client, uid): 
        await call.answer("⚠️ ابتدا در کانال عضو شوید!", show_alert=True)
        return
    
    async with aiosqlite.connect("zarvpn_web.db") as db:
        if call.data == "back_to_main":
            await call.edit_message_text("🤖 منوی اصلی سیستم ZarVpn:", reply_markup=await get_user_menu(uid))
            
        elif call.data == "charge_menu":
            try:
                async with db.execute("SELECT balance FROM users WHERE user_id = ?", (uid,)) as c: 
                    balance = (await c.fetchone())[0]
                async with db.execute("SELECT * FROM settings") as c: 
                    settings = dict(await c.fetchall())
            except Exception: 
                balance, settings = 0, {}
            
            text = f"💰 **بخش مدیریت مالی کیف پول**\n\n💵 موجودی فعلی حساب شما: **{balance:,} تومان**\n\n📌 روش شارژ مورد نظر خود را انتخاب کنید:"
            btns = []
            if settings.get('swapwallet_status') == 'on': 
                btns.append([InlineKeyboardButton("🪙 درگاه صرافی سواپ‌ولت", callback_data="pay_swap")])
            if settings.get('card_status') == 'on': 
                btns.append([InlineKeyboardButton("💳 کارت به کارت بانکی", callback_data="pay_card")])
            if settings.get('crypto_status') == 'on': 
                btns.append([InlineKeyboardButton("⚡ ارزهای دیجیتال (ولت ادمین)", callback_data="pay_crypto")])
            btns.append([InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_main")])
            await call.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btns))

        elif call.data == "pay_card":
            try:
                async with db.execute("SELECT value FROM settings WHERE key='card_number'") as c: 
                    card = (await c.fetchone())[0]
            except Exception: 
                card = "ثبت نشده"
            await call.edit_message_text(f"💳 **واریز مستقیم کارت به کارت:**\n\nلطفاً مبلغ مورد نظر را به شماره کارت زیر واریز نمایید:\n\n`{card}`\n\n📌 پس از پرداخت، رسید واریزی را برای پشتیبانی ارسال فرمایید تا حساب شما شارژ شود.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="charge_menu")]]))

        elif call.data == "pay_crypto":
            try:
                async with db.execute("SELECT value FROM settings WHERE key='crypto_details'") as c: 
                    crypto_details = (await c.fetchone())[0]
            except Exception: 
                crypto_details = "آدرسی ثبت نشده است"
            await call.edit_message_text(f"⚡ **واریز از طریق ارزهای دیجیتال:**\n\nآدرس ولت‌های معتبر مدیریت سیستم:\n\n{crypto_details}\n\n📌 پس از انتقال، لطفا هَش تراکنش را به پشتیبانی اعلام کنید.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="charge_menu")]]))

        elif call.data == "pay_swap":
            await call.answer("⚡ اتصال به وب‌سرویس صرافی صادر شد. لطفاً منتظر فاکتور بمانید...", show_alert=True)

        elif call.data == "buy_menu":
            try:
                async with db.execute("SELECT id, name, price FROM plans") as c: 
                    plans = await c.fetchall()
            except Exception: 
                plans = []
            if not plans:
                await call.answer("❌ هیچ پلنی در حال حاضر برای فروش تعریف نشده است!", show_alert=True)
                return
            btns = [[InlineKeyboardButton(f"📦 {p[1]} | {p[2]:,} تومان", callback_data=f"buy_id_{p[0]}")] for p in plans]
            btns.append([InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_main")])
            await call.edit_message_text("🛍️ محصولات و پلن‌های سرعت بالای مگا سیستم:\n📌 پلن مورد نظر خود را جهت خرید انتخاب کنید:", reply_markup=InlineKeyboardMarkup(btns))

        # هندلر خرید یک پلن خاص و کسر از موجودی کیف پول کاربران
        elif call.data.startswith("buy_id_"):
            pid = int(call.data.split("_")[2])
            async with db.execute("SELECT name, size_gb, days, price, panel_type FROM plans WHERE id=?", (pid,)) as c:
                plan = await c.fetchone()
            async with db.execute("SELECT balance FROM users WHERE user_id=?", (uid,)) as c:
                balance = (await c.fetchone())[0]
                
            if not plan:
                await call.answer("❌ پلن یافت نشد!", show_alert=True)
                return
            if balance < plan[3]:
                await call.answer("❌ موجودی کیف پول شما کافی نیست! ابتدا حساب خود را شارژ کنید.", show_alert=True)
                return
                
            await call.answer("⚙️ در حال برقراری ارتباط با سرور و صدور کانکشن...", show_alert=True)
            v2_user = f"zar_{uid}_{pid}"
            # ساخت اکانت روی سرورها از طریق ماژول پنل منیجر
            res = await panel_manager.create_account(plan[4], v2_user, plan[1], plan[2])
            
            if res.get("status") == "success":
                # کسر موجودی و ثبت سفارش در دیتابیس
                await db.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (plan[3], uid))
                await db.execute("INSERT INTO orders (user_id, plan_name, sub_link, v2ray_username, panel_type) VALUES (?, ?, ?, ?, ?)", (uid, plan[0], res["link"], v2_user, plan[4]))
                await db.commit()
                
                success_text = f"✅ **خرید با موفقیت انجام شد!**\n\n📦 پلن: {plan[0]}\n🔗 کانکشن اختصاصی شما:\n\n`{res['link']}`\n\n📌 جهت دانلود نرم‌افزارهای اتصال لینک را در کلایِنت خود کپی کنید."
                await call.edit_message_text(success_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]]))
            else:
                await call.edit_message_text("❌ خطا در صدور کانکشن از سمت سرور! لطفا به پشتیبانی پیام دهید.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="buy_menu")]]))

        elif call.data == "manage_services":
            try:
                async with db.execute("SELECT id, plan_name FROM orders WHERE user_id=?", (uid,)) as c: 
                    srvs = await c.fetchall()
            except Exception: 
                srvs = []
            if not srvs: 
                await call.answer("❌ شما هیچ سرویس یا اشتراک فعالی در سیستم ندارید!", show_alert=True)
                return
            btns = [[InlineKeyboardButton(f"📦 {s[1]} (کد اشتراک: {s[0]})", callback_data=f"view_srv_{s[0]}")] for s in srvs]
            btns.append([InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_main")])
            await call.edit_message_text("🛠️ سرویس‌ها و کانکشن‌های خریداری شده شما:", reply_markup=InlineKeyboardMarkup(btns))

        # مشاهده جزئیات لینک یک کانکشن توسط کاربر عادی
        elif call.data.startswith("view_srv_"):
            oid = int(call.data.split("_")[2])
            async with db.execute("SELECT plan_name, sub_link FROM orders WHERE id=? AND user_id=?", (oid, uid)) as c:
                srv_info = await c.fetchone()
            if not srv_info:
                await call.answer("سرویس یافت نشد", show_alert=True)
                return
            await call.edit_message_text(f"📦 **جزییات اشتراک شماره {oid}:**\n\nنام پلن: {srv_info[0]}\n\n🔗 لینک کانفیگ:\n`{srv_info[1]}`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به لیست", callback_data="manage_services")]]))

        elif call.data == "get_free_test":
            async with db.execute("SELECT used_test FROM users WHERE user_id=?", (uid,)) as c:
                used = (await c.fetchone())[0]
            if used == 1:
                await call.answer("❌ شما قبلاً تست رایگان خود را دریافت کرده‌اید!", show_alert=True)
                return
            await call.answer("🎁 در حال تولید کانکشن تست رایگان سرور...", show_alert=True)
            v2_user = f"test_{uid}"
            res = await panel_manager.create_account("connectix", v2_user, 1, 1) # ۱ گیگ ۱ روزه تست
            if res.get("status") == "success":
                await db.execute("UPDATE users SET used_test=1 WHERE user_id=?", (uid,))
                await db.execute("INSERT INTO orders (user_id, plan_name, sub_link, v2ray_username, panel_type) VALUES (?, 'تست رایگان ۱ گیگ', ?, ?, 'connectix')", (uid, res["link"], v2_user))
                await db.commit()
                await call.edit_message_text(f"🎁 **اکانت تست رایگان شما با موفقیت صادر شد:**\n\n`{res['link']}`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]))
            else:
                await call.answer("خطا در برقراری ارتباط با سرور تست", show_alert=True)

        elif call.data == "ref_menu":
            bot_username = (await client.get_me()).username
            ref_link = f"https://t.me/{bot_username}?start={uid}"
            try:
                async with db.execute("SELECT COUNT(*) FROM users WHERE referred_by=?", (uid,)) as c: 
                    count = (await c.fetchone())[0]
            except Exception: 
                count = 0
            text = f"👥 **سیستم هوشمند درآمدزایی و زیرمجموعه‌گیری:**\n\nبا دعوت از دوستانتان به ربات ما، درصد ثابت سود شارژ یا خرید از سیستم هدیه بگیرید!\n\n🔗 **لینک دعوت اختصاصی شما:**\n`{ref_link}`\n\n👥 تعداد کاربران دعوت شده توسط شما: **{count} نفر**"
            await call.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_main")]]))

        elif call.data == "admin_bot_menu" and str(uid) == str(config.ADMIN_ID):
            btns = [
                [InlineKeyboardButton("👥 مدیریت لیست کاربران", callback_data="bot_manage_users")], 
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]
            ]
            await call.edit_message_text("⚙️ پنل مدیریت درون ربات ادمین کل سیستم:", reply_markup=InlineKeyboardMarkup(btns))

        elif call.data == "bot_manage_users" and str(uid) == str(config.ADMIN_ID):
            try:
                async with db.execute("SELECT user_id, username FROM users LIMIT 15") as c: 
                    users = await c.fetchall()
            except Exception: 
                users = []
            btns = [[InlineKeyboardButton(f"👤 {u[1]} ({u[0]})", callback_data=f"adm_usr_{u[0]}")] for u in users]
            btns.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_bot_menu")])
            await call.edit_message_text("👥 ۱۵ کاربر اخیر سیستم جهت مدیریت فوری سریع:", reply_markup=InlineKeyboardMarkup(btns))

        elif call.data.startswith("adm_usr_") and str(uid) == str(config.ADMIN_ID):
            t_id = int(call.data.split("_")[2])
            try:
                async with db.execute("SELECT username, balance FROM users WHERE user_id=?", (t_id,)) as c: 
                    usr = await c.fetchone()
            except Exception: 
                usr = ("User", 0)
            text = f"👤 کاربر محترم: @{usr[0]}\n🆔 آیدی عددی: `{t_id}`\n💰 موجودی فعلی: **{usr[1]:,} تومان**"
            btns = [
                [InlineKeyboardButton("➕ افزایش ۵۰,۰۰۰ تومان", callback_data=f"b_inc_{t_id}"), InlineKeyboardButton("➖ کاهش ۵۰,۰۰۰ تومان", callback_data=f"b_dec_{t_id}")], 
                [InlineKeyboardButton("🔙 بازگشت", callback_data="bot_manage_users")]
            ]
            await call.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btns))

        elif call.data.startswith("b_inc_") and str(uid) == str(config.ADMIN_ID):
            t_id = int(call.data.split("_")[2])
            await db.execute("UPDATE users SET balance = balance + 50000 WHERE user_id=?", (t_id,))
            await db.commit()
            await call.answer("✅ مبلغ ۵۰ هزار تومان به موجودی کاربر افزوده شد.", show_alert=True)
            
        elif call.data.startswith("b_dec_") and str(uid) == str(config.ADMIN_ID):
            t_id = int(call.data.split("_")[2])
            await db.execute("UPDATE users SET balance = max(0, balance - 50000) WHERE user_id=?", (t_id,))
            await db.commit()
            await call.answer("❌ مبلغ ۵۰ هزار تومان از موجودی کاربر کسر شد.", show_alert=True)

if __name__ == "__main__":
    app.run()
