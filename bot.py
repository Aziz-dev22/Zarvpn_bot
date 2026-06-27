import telebot
from telebot import types
import config

bot = telebot.TeleBot(config.TELEGRAM_TOKEN)

# ساخت دکمه‌های شیشه‌ای منوی اصلی
def get_main_inline_keyboard(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn_buy = types.InlineKeyboardButton("🛍️ خرید اشتراک", callback_data="buy_sub")
    btn_profile = types.InlineKeyboardButton("👤 حساب کاربری", callback_data="user_profile")
    btn_test = types.InlineKeyboardButton("🔗 تست رایگان", callback_data="get_test")
    btn_support = types.InlineKeyboardButton("📞 پشتیبانی", callback_data="support")
    
    markup.add(btn_buy, btn_profile)
    markup.add(btn_test, btn_support)
    
    # اگر کاربر ادمین بود، دکمه شیشه‌ای مدیریت را اضافه کن
    if user_id == config.ADMIN_ID:
        btn_admin = types.InlineKeyboardButton("⚙️ پنل مدیریت ادمین", callback_data="admin_panel")
        markup.add(btn_admin)
        
    return markup

# ساخت دکمه‌های شیشه‌ای داخل پنل مدیریت
def get_admin_inline_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_stats = types.InlineKeyboardButton("📊 آمار ربات", callback_data="admin_stats")
    btn_back = types.InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")
    markup.add(btn_stats, btn_back)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id, 
        "🤖 به ربات ZarVpn خوش آمدید.\nلطفاً یکی از گزینه‌های شیشه‌ای زیر را انتخاب کنید:", 
        reply_markup=get_main_inline_keyboard(message.from_user.id)
    )

# مدیریت کلیک روی دکمه‌های شیشه‌ای (Callback Queries)
@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    user_id = call.from_user.id
    
    # دکمه خرید اشتراک
    if call.data == "buy_sub":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🔄 لیست پلن‌های VPN به‌زودی بارگذاری می‌شود...")
        
    # دکمه پنل مدیریت
    elif call.data == "admin_panel":
        bot.answer_callback_query(call.id)
        if user_id == config.ADMIN_ID:
            bot.edit_message_text(
                "⚙️ به پنل مدیریت ZarVpn خوش آمدید:",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=get_admin_inline_keyboard()
            )
        else:
            bot.send_message(call.message.chat.id, "❌ شما دسترسی به این بخش را ندارید!")
            
    # دکمه آمار ربات در پنل مدیریت
    elif call.data == "admin_stats":
        bot.answer_callback_query(call.id)
        if user_id == config.ADMIN_ID:
            text = "📈 آمار ربات شما:\n\n👥 تعداد کل کاربران: ۱ نفر\n💰 کل درآمد امروز: ۰ تومان"
            bot.send_message(call.message.chat.id, text)
            
    # دکمه بازگشت به منوی اصلی
    elif call.data == "back_to_main":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "🤖 به منوی اصلی ZarVpn برگشتید:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=get_main_inline_keyboard(user_id)
        )

print("🚀 ربات با دکمه‌های شیشه‌ای روشن شد...")
bot.infinity_polling()
