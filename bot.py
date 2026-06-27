import telebot
from telebot import types
import config

# راه‌اندازی ربات با توکن امن
bot = telebot.TeleBot(config.TELEGRAM_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    # دکمه‌های منوی اصلی کاربران
    btn1 = types.KeyboardButton("🛍️ خرید اشتراک")
    btn2 = types.KeyboardButton("👤 حساب کاربری")
    btn3 = types.KeyboardButton("🔗 دریافت تست رایگان")
    btn4 = types.KeyboardButton("📞 پشتیبانی")
    
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    
    # اگر کاربر ادمین بود، دکمه مدیریت را هم نشان بده
    if user_id == config.ADMIN_ID:
        btn_admin = types.KeyboardButton("⚙️ پنل مدیریت")
        markup.add(btn_admin)

    bot.send_message(
        message.chat.id, 
        "سلام! به ربات ZarVpn خوش آمدید. لطفاً یک گزینه را انتخاب کنید:", 
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == "🛍️ خرید اشتراک")
def buy_subscription(message):
    bot.send_message(message.chat.id, "🔄 لیست پلن‌های VPN به‌زودی بارگذاری می‌شود...")

print("🚀 ربات ZarVpn با موفقیت روشن شد...")
bot.infinity_polling()
import telebot
from telebot import types
import config

# راه‌اندازی ربات با توکن امن
bot = telebot.TeleBot(config.TELEGRAM_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    # دکمه‌های منوی اصلی کاربران
    btn1 = types.KeyboardButton("🛍️ خرید اشتراک")
    btn2 = types.KeyboardButton("👤 حساب کاربری")
    btn3 = types.KeyboardButton("🔗 دریافت تست رایگان")
    btn4 = types.KeyboardButton("📞 پشتیبانی")
    
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    
    # اگر کاربر ادمین بود، دکمه مدیریت را هم نشان بده
    if user_id == config.ADMIN_ID:
        btn_admin = types.KeyboardButton("⚙️ پنل مدیریت")
        markup.add(btn_admin)

    bot.send_message(
        message.chat.id, 
        "سلام! به ربات ZarVpn خوش آمدید. لطفاً یک گزینه را انتخاب کنید:", 
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == "🛍️ خرید اشتراک")
def buy_subscription(message):
    bot.send_message(message.chat.id, "🔄 لیست پلن‌های VPN به‌زودی بارگذاری می‌شود...")

print("🚀 ربات ZarVpn با موفقیت روشن شد...")
bot.infinity_polling()

