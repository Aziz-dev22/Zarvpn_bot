#!/bin/bash

echo "========================================"
echo "    ZarVPN Automated Installer (v1.0)"
echo "========================================"

# آپدیت مخازن لینوکس و نصب پایتون و ابزارهای مورد نیاز
echo "[..] Updating system packages and installing Python..."
sudo apt update -y
sudo apt install python3 python3-pip wget -y

# دانلود مستقیم و محلی فایل‌های پیش‌نیاز از گیت‌هاب شما در پوشه فعلی
echo "[..] Downloading core installation files from GitHub..."
wget -q -O requirements.txt https://raw.githubusercontent.com/Aziz-dev22/Zarvpn_bot/main/requirements.txt
wget -q -O install.py https://raw.githubusercontent.com/Aziz-dev22/Zarvpn_bot/main/install.py

# دانلود فایل آپدیت لینوکس
wget -q -O update.sh https://raw.githubusercontent.com/Aziz-dev22/Zarvpn_bot/main/update.sh
chmod +x update.sh

# نصب کتابخانه‌ها با دور زدن محدودیت لینوکس‌های جدید و اجرای جادوگر تنظیمات
echo "[..] Installing dependencies & starting configuration wizard..."
pip install -r requirements.txt --break-system-packages
python3 install.py

echo "========================================"
echo " [✓] Installation process completed!"
echo " [📌] You can now run 'python3 bot.py' and 'python3 web_panel.py'"
echo "========================================"
