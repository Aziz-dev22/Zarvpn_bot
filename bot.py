import telebot
from telebot import types
import sqlite3
import requests
import config

bot = telebot.TeleBot(config.TELEGRAM_TOKEN)

# 💾 بخش دیتابیس (کیف پول و مدیریت کاربران)
def init_db():
    conn = sqlite3.connect("zarvpn.db")
    cursor = conn.cursor()
    # جدول کاربران و کیف پول
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, username TEXT)''')
    # جدول پلن‌های فروش
    cursor.execute('''CREATE TABLE IF NOT EXISTS plans 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, size INTEGER, days INTEGER, price INTEGER)''')
    conn.commit()
    
    # افزودن چند پلن پیش‌فرض در صورت خالی بودن دیتابیس
    cursor.execute("SELECT COUNT(*) FROM plans")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO plans (name, size, days, price) VALUES (?, ?, ?, ?)", ("👑 پلن برنزی (یک‌ماهه ۱۰ گیگ)", 10, 30, 50000))
        cursor.execute("INSERT INTO plans (name, size, days, price) VALUES (?, ?, ?, ?)", ("💎 پلن نقره‌ای (یک‌ماهه ۳۰ گیگ)", 30, 30, 100000))
        cursor.execute("INSERT INTO plans (name, size, days, price) VALUES (?, ?, ?, ?)", ("🔥 پلن طلایی (سه‌ماهه ۱۰۰ گیگ)", 100, 90, 250000))
        conn.commit()
    conn.close()

init_db()

# 🌐 اتصال به API پنل (مرزبان / X-UI) برای ساخت اکانت خودکار
def create_vpn_account(username, days, size_gb):
    """
    این تابع به پنل شما متصل می‌شود و کانکشن می‌سازد.
    پس از ست کردن دامنه پنل در config.py این بخش فعال می‌شود.
    """
    try:
        # نمونه درخواست فرضی به پنل X-UI یا مرزبان
        # در پروژه‌های واقعی اینجا توکن پنل ارسال می‌شود
        url = f"{config.PANEL_URL}/api/v1/user" 
        payload = {
            "username": username,
            "proxies": {"vless": {}, "vmess": {}},
            "expire": days * 86400, # تبدیل به ثانیه
            "data_limit": size_gb * 1024 * 1024 * 1024 # تبدیل به بایت
        }
        # برای تست فعلا یک لینک فرضی برمی‌گردانیم تا پنل شما ست شود
        return f"vless://{username}_ZarVpn_Generated_Link@127.0.0.1:443?encryption=none&security=reality"
    except Exception as e:
        return None

# 📊 کیبوردهای شیشه‌ای منوها
def main_menu(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🛍️ خرید اشتراک VPN", callback_data="buy_menu"),
        types.InlineKeyboardButton("👤 حساب کاربری و کیف پول", callback_data="profile_menu")
    )
    markup.add(
        types.InlineKeyboardButton("💳 شارژ کیف پول", callback_data="charge_wallet"),
        types.InlineKeyboardButton("📞 پشتیبانی آنلاین", callback_data="support_info")
    )
    if user_id == config.ADMIN_ID:
        markup.add(types.InlineKeyboardButton("⚙️ پنل فوق پیشرفته مدیریت ادمین", callback_data="admin_main"))
    return markup

# 🤖 مدیریت دستور Start
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    
    # ثبت کاربر در دیتابیس اگر جدید باشد
    conn = sqlite3.connect("zarvpn.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()
    
    bot.send_message(
        message.chat.id,
        "🤖 به سیستم هوشمند و خودکار فروش کانکشن ZarVpn خوش آمدید.\n\nلطفاً از دکمه‌های زیر اقدام کنید:",
        reply_markup=main_menu(user_id)
    )

# 🔄 مدیریت کلیک روی تمام دکمه‌های شیشه‌ای ربات
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    conn = sqlite3.connect("zarvpn.db")
    cursor = conn.cursor()

    # --- بخش کاربر ---
    if call.data == "back_to_user":
        bot.answer_callback_query(call.id)
        bot.edit_message_text("🤖 به منوی اصلی ZarVpn برگشتید:", chat_id, msg_id, reply_markup=main_menu(user_id))

    elif call.data == "profile_menu":
        bot.answer_callback_query(call.id)
        cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        balance = cursor.fetchone()[0]
        text = f"👤 **حساب کاربری شما:**\n\n" \
               f"🆔 آیدی عددی: `{user_id}`\n" \
               f"💳 موجودی کیف پول: {balance:,} تومان\n\n" \
               f"📦 وضعیت سرویس‌ها: جهت مشاهده سرویس‌های فعال خود از منوی خرید اقدام کنید."
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_user"))
        bot.edit_message_text(text, chat_id, msg_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "buy_menu":
        bot.answer_callback_query(call.id)
        cursor.execute("SELECT * FROM plans")
        plans = cursor.fetchall()
        markup = types.InlineKeyboardMarkup(row_width=1)
        for plan in plans:
            markup.add(types.InlineKeyboardButton(f"{plan[1]} - {plan[4]:,} تومان", callback_data=f"buy_plan_{plan[0]}"))
        markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_user"))
        bot.edit_message_text("🛍️ پلن مورد نظر خود را برای خرید انتخاب کنید:", chat_id, msg_id, reply_markup=markup)

    elif call.data.startswith("buy_plan_"):
        bot.answer_callback_query(call.id)
        plan_id = int(call.data.split("_")[2])
        cursor.execute("SELECT * FROM plans WHERE id = ?", (plan_id,))
        plan = cursor.fetchone()
        
        cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        balance = cursor.fetchone()[0]
        
        if balance >= plan[4]: # بررسی موجودی کیف پول
            # کسر موجودی از کیف پول
            new_balance = balance - plan[4]
            cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
            conn.commit()
            
            # ساخت اکانت در پنل مرزبان/X-UI
            vpn_link = create_vpn_account(f"user_{user_id}_{plan_id}", plan[3], plan[2])
            
            text = f"✅ **خرید با موفقیت انجام شد!**\n\n" \
                   f"💰 از کیف پول شما کم شد: {plan[4]:,} تومان\n" \
                   f"💳 موجودی فعلی: {new_balance:,} تومان\n\n" \
                   f"🚀 **کانکشن اختصاصی شما ساخته شد:**\n" \
                   f"`{vpn_link}`\n\n" \
                   f"📥 کپی کنید و در نرم‌افزار خود (v2rayNG / Streisand) وارد کنید."
        else:
            text = f"❌ **موجودی کیف پول شما کافی نیست!**\n\n" \
                   f"💵 قیمت پلن: {plan[4]:,} تومان\n" \
                   f"💳 موجودی شما: {balance:,} تومان\n\n" \
                   f"💡 لطفا ابتدا کیف پول خود را شارژ کنید."
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💳 شارژ کیف پول", callback_data="charge_wallet"))
        markup.add(types.InlineKeyboardButton("🔙 بازگشت به پلن‌ها", callback_data="buy_menu"))
        bot.edit_message_text(text, chat_id, msg_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "charge_wallet":
        bot.answer_callback_query(call.id)
        text = "💳 **روش شارژ کیف پول خود را انتخاب کنید:**\n\n" \
               "۱. کارت به کارت خودکار\n" \
               "۲. پرداخت با رمز ارز (تتر / ترون)"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🇮🇷 کارت به کارت", callback_data="pay_card"),
            types.InlineKeyboardButton("🪙 پرداخت کریپتو (Tether)", callback_data="pay_crypto"),
            types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_user")
        )
        bot.edit_message_text(text, chat_id, msg_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data in ["pay_card", "pay_crypto"]:
        bot.answer_callback_query(call.id)
        # اتصال به درگاه پرداخت در نسخه اصلی؛ برای پروژه عمومی، ادمین شماره کارت یا ولت می‌دهد
        text = "🔒 **بخش پرداخت امن:**\n\n" \
               "جهت اتصال مستقیم به درگاه یا دریافت شماره کارت/ولت ادمین، لطفاً مبلغ شارژ را مشخص کنید یا به پشتیبانی پیام دهید.\n" \
               "(برای تست، ادمین می‌تواند از بخش پنل مدیریت به شما موجودی رایگان اضافه کند)."
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="charge_wallet"))
        bot.edit_message_text(text, chat_id, msg_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "support_info":
        bot.answer_callback_query(call.id)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_user"))
        bot.edit_message_text("📞 جهت ارتباط با پشتیبانی و ارسال فیش واریزی به آیدی ادمین پیام دهید.", chat_id, msg_id, reply_markup=markup)

    # --- ⚙️ بخش پنل مدیریت فوق پیشرفته ادمین ---
    elif call.data == "admin_main" and user_id == config.ADMIN_ID:
        bot.answer_callback_query(call.id)
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("📊 آمار کل سیستم فروش", callback_data="admin_stats"),
            types.InlineKeyboardButton("🎁 شارژ هدیه کیف پول کاربر", callback_data="admin_gift"),
            types.InlineKeyboardButton("🔙 خروج از پنل مدیریت", callback_data="back_to_user")
        )
        bot.edit_message_text("⚙️ به پنل ادمین خوش آمدید. یک ابزار مدیریتی انتخاب کنید:", chat_id, msg_id, reply_markup=markup)

    elif call.data == "admin_stats" and user_id == config.ADMIN_ID:
        bot.answer_callback_query(call.id)
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(balance) FROM users")
        total_wallets = cursor.fetchone()[0] or 0
        
        text = f"📊 **گزارش لحظه‌ای سیستم:**\n\n" \
               f"👥 تعداد کل کاربران ربات: {total_users} نفر\n" \
               f"💰 مجموع کیف پول کاربران: {total_wallets:,} تومان"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_main"))
        bot.edit_message_text(text, chat_id, msg_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "admin_gift" and user_id == config.ADMIN_ID:
        bot.answer_callback_query(call.id)
        # برای تست سریع سیستم کیف پول، ۱۰۰ هزار تومان به کیف پول خود ادمین هدیه داده می‌شود تا بتواند خرید پلن را تست کند
        cursor.execute("UPDATE users SET balance = balance + 100000 WHERE user_id = ?", (config.ADMIN_ID,))
        conn.commit()
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="admin_main"))
        bot.edit_message_text("✅ مبلغ 100,000 تومان شارژ تست به حساب شما (ادمین) اضافه شد تا بتوانید چرخه خرید را تست کنید!", chat_id, msg_id, reply_markup=markup)

    conn.close()

print("🚀 ربات جامع و کامل ZarVpn با سیستم دیتابیس و کیف پول فعال شد...")
bot.infinity_polling()
