import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyrogram.enums import ChatMemberStatus
import aiosqlite
from core import config
from core.database import init_commercial_db
from panels.connectix import ConnectixAPI

app = Client(
    "zarvpn_bot",
    bot_token=config.TELEGRAM_TOKEN,
    api_id=23749219,             
    api_hash="5f2bb6082cb0db48483bda1a63c6ea62" 
)

# تابع بررسی عضویت اجباری
async def is_subscribed(client, user_id):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        async with db.execute("SELECT value FROM settings WHERE key='channel_id'") as c: channel = (await c.fetchone())[0]
    try:
        member = await client.get_chat_member(channel, user_id)
        return member.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]
    except: return False

# منوی کاربری شیک، کوتاه و فشرده
def user_menu(user_id):
    buttons = [
        [InlineKeyboardButton("🛍️ خرید اشتراک", callback_data="buy_menu"),
         InlineKeyboardButton("🛠️ مدیریت سرویس‌ها", callback_data="manage_services")],
        [InlineKeyboardButton("💰 کیف پول و شارژ", callback_data="charge_menu"),
         InlineKeyboardButton("👥 دعوت و سود", callback_data="ref_menu")],
        [InlineKeyboardButton("🎁 دریافت تست رایگان", callback_data="get_free_test")],
        [InlineKeyboardButton("👤 حساب من", callback_data="my_account"),
         InlineKeyboardButton("📞 پشتیبانی", callback_data="support_info")]
    ]
    if str(user_id) == str(config.ADMIN_ID):
        buttons.append([InlineKeyboardButton("⚙️ پنل مدیریت ادمین ربات", callback_data="admin_panel")])
    return InlineKeyboardMarkup(buttons)

@app.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    uid = message.from_user.id
    uname = message.from_user.username or "user"
    
    if not await is_subscribed(client, uid):
        async with aiosqlite.connect("zarvpn_web.db") as db:
            async with db.execute("SELECT value FROM settings WHERE key='channel_id'") as c: ch = (await c.fetchone())[0]
        await message.reply_text(
            f"❌ **عضویت اجباری**\n\nابتدا در کانال ما عضو شوید:\n📢 {ch}\n\nسپس مجدداً ربات را /start کنید.", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{ch.replace('@', '')}")]])
        )
        return

    ref_id = 0
    if len(message.command) > 1 and message.command[1].isdigit():
        ref_id = int(message.command[1])
        if ref_id == uid: ref_id = 0 

    async with aiosqlite.connect("zarvpn_web.db") as db:
        async with db.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (uid,)) as c: is_exist = (await c.fetchone())[0]
        if is_exist == 0:
            await db.execute("INSERT INTO users (user_id, username, referred_by) VALUES (?, ?, ?)", (uid, uname, ref_id))
            if ref_id > 0:
                async with db.execute("SELECT value FROM settings WHERE key='ref_bonus'") as s: row = await s.fetchone(); bonus = int(row[0]) if row else 5000
                await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (bonus, ref_id))
                try: await client.send_message(ref_id, f"🎉 هدیه دعوت {bonus:,} تومانی به حساب شما واریز شد!")
                except: pass
            await db.commit()
            
    await message.reply_text("🤖 منوی اصلی سیستم ZarVpn:", reply_markup=user_menu(uid))

@app.on_callback_query()
async def handle_callbacks(client: Client, call: CallbackQuery):
    uid = call.from_user.id
    if not await is_subscribed(client, uid): 
        await call.answer("❌ ابتدا باید در کانال عضو شوید!", show_alert=True); return
    
    async with aiosqlite.connect("zarvpn_web.db") as db:
        if call.data == "back_to_main":
            await call.edit_message_text("🤖 منوی اصلی سیستم ZarVpn:", reply_markup=user_menu(uid))
            
        elif call.data == "my_account":
            async with db.execute("SELECT balance FROM users WHERE user_id = ?", (uid,)) as c: row = await c.fetchone(); balance = row[0] if row else 0
            await call.edit_message_text(f"👤 **وضعیت حساب:**\n\n🆔 آیدی عددی: `{uid}`\n💳 موجودی: {balance:,} تومان", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]))

        elif call.data == "buy_menu":
            async with db.execute("SELECT * FROM plans") as c: plans = await c.fetchall()
            buttons = []
            for p in plans:
                buttons.append([InlineKeyboardButton(f"{p[1]} ➖ {p[4]:,} تومان", callback_data=f"order_p_{p[0]}")])
            buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
            await call.edit_message_text("🛍_ انتخاب پلن اشتراک:", reply_markup=InlineKeyboardMarkup(buttons))

        elif call.data.startswith("order_p_"):
            pid = int(call.data.split("_")[2])
            async with db.execute("SELECT * FROM plans WHERE id = ?", (pid,)) as c: plan = await c.fetchone()
            async with db.execute("SELECT balance FROM users WHERE user_id = ?", (uid,)) as c: balance = (await c.fetchone())[0]
            if balance < plan[4]:
                await call.answer("❌ موجودی کافی نیست!", show_alert=True); return
            
            await call.edit_message_text("🔄 در حال صدور کانکشن...")
            if plan[5] == "connectix":
                async with db.execute("SELECT value FROM settings WHERE key='connectix_token'") as s: cx_t = (await s.fetchone())[0]
                async with db.execute("SELECT value FROM settings WHERE key='connectix_endpoint'") as s: cx_e = (await s.fetchone())[0]
                cx_api = ConnectixAPI(api_token=cx_t, endpoint=cx_e)
                res = await cx_api.create_user(f"zar_{uid}", plan[2], plan[3])
                if res["status"] == "success":
                    await db.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (plan[4], uid))
                    await db.execute("INSERT INTO orders (user_id, plan_name, sub_link, v2ray_username, panel_type) VALUES (?, ?, ?, ?, 'connectix')", (uid, plan[1], res["link"], f"zar_{uid}"))
                    await db.commit()
                    await call.message.reply_text(f"✅ **سفارش صادر شد:**\n\n`{res['link']}`")

        # 🎁 قابلیت جدید: سیستم دریافت تست رایگان کنترل‌شونده
        elif call.data == "get_free_test":
            async with db.execute("SELECT value FROM settings WHERE key='test_status'") as s: t_status = (await s.fetchone())[0]
            if t_status == "off":
                await call.answer("❌ اکانت تست موقتاً توسط ادمین غیرفعال شده است.", show_alert=True)
                return
            
            async with db.execute("SELECT used_test FROM users WHERE user_id = ?", (uid,)) as c: row = await c.fetchone(); used = row[0] if row else 0
            if used == 1:
                await call.answer("❌ شما قبلاً هدیه تست رایگان خود را دریافت کرده‌اید!", show_alert=True)
                return
            
            await call.edit_message_text("🔄 در حال صدور اکانت تست رایگان (۲ گیگابایت - ۱ روز)...")
            async with db.execute("SELECT value FROM settings WHERE key='connectix_token'") as s: cx_t = (await s.fetchone())[0]
            async with db.execute("SELECT value FROM settings WHERE key='connectix_endpoint'") as s: cx_e = (await s.fetchone())[0]
            
            cx_api = ConnectixAPI(api_token=cx_t, endpoint=cx_e)
            res = await cx_api.create_user(f"test_{uid}", 2, 1) # ایجاد اکانت تست ۲ گیگ ۱ روزه
            
            if res["status"] == "success":
                await db.execute("UPDATE users SET used_test = 1 WHERE user_id = ?", (uid,))
                await db.execute("INSERT INTO orders (user_id, plan_name, sub_link, v2ray_username, panel_type) VALUES (?, 'تست رایگان', ?, ?, 'connectix')", (uid, res["link"], f"test_{uid}"))
                await db.commit()
                await call.message.reply_text(f"🎉 **کانکشن تست با موفقیت صادر شد:**\n\n`{res['link']}`")
            else:
                await call.message.reply_text(f"❌ خطا در صدور تست سرور: {res['message']}")

        # 🛠️ مدیریت لایسنس‌های فروخته شده
        elif call.data == "manage_services":
            async with db.execute("SELECT id, plan_name FROM orders WHERE user_id = ?", (uid,)) as c: user_orders = await c.fetchall()
            if not user_orders:
                await call.answer("❌ اشتراک فعالی ندارید!", show_alert=True); return
            buttons = []
            for order in user_orders: buttons.append([InlineKeyboardButton(f"📦 {order[1]} (کد: {order[0]})", callback_data=f"srv_{order[0]}")])
            buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
            await call.edit_message_text("🛠️ لیست سرویس‌های شما:", reply_markup=InlineKeyboardMarkup(buttons))

        elif call.data.startswith("srv_"):
            order_id = int(call.data.split("_")[1])
            async with db.execute("SELECT plan_name, sub_link FROM orders WHERE id = ?", (order_id,)) as c: order = await c.fetchone()
            text = f"📦 **مدیریت سرویس شماره {order_id}**\n\n🔹 پلن: {order[0]}\n🔗 لینک اتصال:\n`{order[1]}`"
            buttons = [[InlineKeyboardButton("🔄 چنج لینک کانفیگ", callback_data=f"change_link_{order_id}"), InlineKeyboardButton("🗑️ حذف کامل", callback_data=f"delete_srv_{order_id}")], [InlineKeyboardButton("🔙 لیست", callback_data="manage_services")]]
            await call.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))

        elif call.data.startswith("change_link_"):
            order_id = int(call.data.split("_")[2])
            new_sub = f"https://seller-api.connectix.vip/sub/reset_{order_id}_{uid}"
            await db.execute("UPDATE orders SET sub_link = ? WHERE id = ?", (new_sub, order_id))
            await db.commit()
            await call.answer("✅ لینک کانفیگ تغییر کرد!", show_alert=True)
            await call.edit_message_text(f"🔄 لینک جدید:\n`{new_sub}`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data=f"srv_{order_id}")]]))

        elif call.data.startswith("delete_srv_"):
            order_id = int(call.data.split("_")[2])
            await db.execute("DELETE FROM orders WHERE id = ?", (order_id,))
            await db.commit()
            await call.answer("🗑️ سرویس حذف شد.", show_alert=True)
            await call.edit_message_text("🤖 منوی اصلی سیستم ZarVpn:", reply_markup=user_menu(uid))

        # 💳 مرکز یکپارچه مالی (کیف پول)
        elif call.data == "charge_menu":
            buttons = [[InlineKeyboardButton("🪙 درگاه صرافی سواپ‌ولت", callback_data="pay_swap")], [InlineKeyboardButton("💳 کارت به کارت", callback_data="pay_card"), InlineKeyboardButton("⚡ ارز دیجیتال", callback_data="pay_crypto")], [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]
            await call.edit_message_text("💳 روش شارژ حساب را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(buttons))

        elif call.data == "pay_swap":
            async with db.execute("SELECT value FROM settings WHERE key='swapwallet_merchant'") as c: row = await c.fetchone(); merchant_id = row[0] if row else ""
            url = f"https://swapwallet.ir/gateway/pay?merchant={merchant_id}&amount=50000&factor_id={uid}" if merchant_id else f"https://t.me/SwapWalletBot?start=pay_{uid}"
            await call.edit_message_text(f"🔗 [ورود به درگاه مستقیم صرافی]({url})", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="charge_menu")]]))

        elif call.data == "pay_card":
            async with db.execute("SELECT value FROM settings WHERE key='card_number'") as c: row = await c.fetchone(); card = row[0] if row else "ثبت نشده"
            await call.edit_message_text(f"💳 **کارت به کارت:**\n`{card}`\n\n📌 فیش را برای پشتیبانی ارسال کنید.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="charge_menu")]]))

        elif call.data == "pay_crypto":
            async with db.execute("SELECT value FROM settings WHERE key='crypto_wallet'") as c: row = await c.fetchone(); wallet = row[0] if row else "ثبت نشده"
            await call.edit_message_text(f"⚡ **تتر TRC20:**\n`{wallet}`\n\n📌 پس از واریز به پشتیبانی اطلاع دهید.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="charge_menu")]]))

        elif call.data == "ref_menu":
            bot_username = (await client.get_me()).username
            ref_link = f"https://t.me/{bot_username}?start={uid}"
            async with db.execute("SELECT COUNT(*) FROM users WHERE referred_by = ?", (uid,)) as c: count = (await c.fetchone())[0]
            await call.edit_message_text(f"👥 **زیرمجموعه‌گیری:**\n\n🔗 لینک دعوت اختصاصی:\n`{ref_link}`\n\n👥 تعداد دعوت‌ها: {count} نفر", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]))

        elif call.data == "support_info":
            await call.edit_message_text("📞 جهت پشتیبانی فیش خود را به مدیریت ارسال کنید.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]))

        # ⚙️ پنل ادمین مستقل داخل ربات همراه با سوئیچ کنترل اکانت تست
        elif call.data == "admin_panel" and str(uid) == str(config.ADMIN_ID):
            async with db.execute("SELECT value FROM settings WHERE key='test_status'") as s: t_status = (await s.fetchone())[0]
            t_button_text = "🔴 خاموش کردن اکانت تست" if t_status == "on" else "🟢 روشن کردن اکانت تست"
            
            buttons = [
                [InlineKeyboardButton("➕ شارژ دستی کاربر", callback_data="adm_charge")],
                [InlineKeyboardButton(t_button_text, callback_data="toggle_test")],
                [InlineKeyboardButton("📊 آمار سیستم", callback_data="adm_stats"), InlineKeyboardButton("🔙 خروج", callback_data="back_to_main")]
            ]
            await call.edit_message_text(f"⚙️ **پنل مدیریت ادمین ربات:**\n\nوضعیت فعلی سیستم تست رایگان: **{t_status.upper()}**", reply_markup=InlineKeyboardMarkup(buttons))

        # توابع تغییر وضعیت تست زنده توسط ادمین
        elif call.data == "toggle_test" and str(uid) == str(config.ADMIN_ID):
            async with db.execute("SELECT value FROM settings WHERE key='test_status'") as s: current = (await s.fetchone())[0]
            new_status = "off" if current == "on" else "on"
            await db.execute("UPDATE settings SET value = ? WHERE key = 'test_status'", (new_status,))
            await db.commit()
            await call.answer(f"وضعیت اکانت تست به {new_status} تغییر یافت!", show_alert=True)
            # ریلود پنل ادمین برای نمایش وضعیت جدید دکمه
            await call.edit_message_reply_markup(reply_markup=None)
            await call.data == "admin_panel" # فراخوانی مجدد لایه منو ادمین

        elif call.data == "adm_stats" and str(uid) == str(config.ADMIN_ID):
            async with db.execute("SELECT SUM(balance) FROM users") as c: total_money = (await c.fetchone())[0] or 0
            await call.answer(f"💰 کل سرمایه موجودی کاربران: {total_money:,} تومان", show_alert=True)

        elif call.data == "adm_charge" and str(uid) == str(config.ADMIN_ID):
            await call.edit_message_text("📌 دستور شارژ دستی:\n\n`/charge USERID AMOUNT`\n\nمثال:\n`/charge 1234567 50000`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")]]))

@app.on_message(filters.command("charge") & filters.user(int(config.ADMIN_ID)))
async def do_charge_cmd(client: Client, message: Message):
    if len(message.command) < 3: return
    try:
        target_id = int(message.command[1])
        amount = int(message.command[2])
        async with aiosqlite.connect("zarvpn_web.db") as db:
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, target_id))
            await db.commit()
        await message.reply_text(f"✅ کیف پول کاربر {target_id} شارژ شد.")
        try: await client.send_message(target_id, f"💳 حساب شما به مبلغ {amount:,} تومان شارژ شد.")
        except: pass
    except: pass

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_commercial_db())
    app.run()
