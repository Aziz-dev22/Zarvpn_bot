#!/bin/bash

clear
echo "========================================================"
echo "      اسکریپت نصب ابر سیستم فروش ZarVpn (نسخه ۲.۰)"
echo "========================================================"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

read -p "🔹 توکن ربات تلگرام: " user_token
read -p "🔹 آیدی عددی ادمین: " user_admin_id

# ذخیره در فایل .env
cat > .env <<EOF
TELEGRAM_TOKEN=$user_token
ADMIN_ID=$user_admin_id
DATABASE_URL=sqlite+aiosqlite:///./zarvpn_web.db
WEB_PORT=8080
WEB_USERNAME=admin
WEB_PASSWORD=zarvpn_admin
EOF

echo "🔄 در حال نصب سرور پیشرفته، پایتون ۳ و نیازمندی‌ها..."
sudo apt update && sudo apt install python3 python3-pip python3-venv git -y

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# ۱. ساخت سرویس ربات تلگرام
sudo bash -c "cat > /etc/systemd/system/zarvpn-bot.service <<EOF
[Unit]
Description=ZarVpn Telegram Bot
After=network.target

[Service]
User=root
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/venv/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF"

# ۲. ساخت سرویس پنل مدیریت تحت وب (FastAPI)
sudo bash -c "cat > /etc/systemd/system/zarvpn-web.service <<EOF
[Unit]
Description=ZarVpn Web Panel
After=network.target

[Service]
User=root
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/venv/bin/uvicorn web.app:app --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
EOF"

# فعال‌سازی همزمان هر دو سیستم
sudo systemctl daemon-reload
sudo systemctl enable zarvpn-bot.service zarvpn-web.service
sudo systemctl start zarvpn-bot.service zarvpn-web.service

echo ""
echo "🔥 سیستم با موفقیت نصب شد!"
echo "🤖 ربات تلگرام فعال شد."
echo "🌐 پنل تحت وب روی پورت 8080 سرور شما بالا آمد: http://YOUR_SERVER_IP:8080"
