#!/bin/bash

clear
echo "=================================================="
echo "   به اسکریپت نصب خودکار ربات ZarVpn خوش آمدید   "
echo "=================================================="
echo ""

# دریافت اطلاعات از کاربر
read -p "🔹 لطفاً توکن ربات تلگرام خود را وارد کنید: " user_token
read -p "🔹 لطفاً آیدی عددی ادمین را وارد کنید: " user_admin_id

# بررسی خالی نبودن ورودی‌ها
if [ -z "$user_token" ] || [ -z "$user_admin_id" ]; then
    echo "❌ خطا: توکن یا آیدی عددی نمی‌تواند خالی باشد!"
    exit 1
fi

# بروزرسانی و نصب پیش‌نیازها
echo "🔄 در حال نصب پیش‌نیازهای سرور ابونتو..."
sudo apt update && sudo apt install python3 python3-pip python3-venv git -y

# ساخت محیط مجازی پایتون
echo "🌐 ساخت محیط مجازی پایتون (Venv)..."
python3 -m venv venv
source venv/bin/activate

# نصب کتابخانه‌ها
echo "📚 در حال نصب کتابخانه‌های پایتون..."
pip install -r requirements.txt

# ذخیره اطلاعات کاربر در فایل امن .env
echo "💾 در حال ذخیره تنظیمات شما..."
cat > .env <<EOF
TELEGRAM_TOKEN=$user_token
ADMIN_ID=$user_admin_id
EOF

# ساخت سرویس سیستمی برای روشن ماندن همیشگی ربات
echo "⚙️ در حال ساخت سرویس برای ماندگاری ربات..."
sudo bash -c "cat > /etc/systemd/system/zarvpn-bot.service <<EOF
[Unit]
Description=ZarVpn Telegram Bot
After=network.target

[Service]
User=root
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF"

# فعال‌سازی و استارت سرویس
sudo systemctl daemon-reload
sudo systemctl enable zarvpn-bot.service
sudo systemctl start zarvpn-bot.service

echo ""
echo "✅ تبریک! ربات ZarVpn با موفقیت نصب و در پس‌زمینه سرور روشن شد."
echo "📊 برای بررسی وضعیت ربات دستور مقابل را بزنید: systemctl status zarvpn-bot"
