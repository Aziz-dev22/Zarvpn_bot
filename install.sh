#!/bin/bash

echo "========================================"
echo "    ZarVPN Automated OS Installer"
echo "========================================"

# آپدیت مخازن لینوکس و نصب پایتون و ابزارهای مورد نیاز
echo "[..] Updating system packages and installing Python..."
sudo apt update -y
sudo apt install python3 python3-pip python3-venv git -y

# ایجاد محیط مجازی پایتون برای جلوگیری از تداخل پکیج‌ها
echo "[..] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# نصب کتابخانه‌های پایتون
echo "[..] Installing required Python libraries..."
pip install --upgrade pip
pip install -r requirements.txt

# اعطای مجوز دسترسی به فایل آپدیت
chmod +x update.sh

# اجرای اسکریپت اصلی جادوگر نصب پایتون برای گرفتن توکن و پورت
echo "[..] Starting configuration wizard..."
python install.py

echo "========================================"
echo " [✓] Installation process completed!"
echo " [📌] You can now run 'python bot.py' and 'python web_panel.py'"
echo "========================================"
