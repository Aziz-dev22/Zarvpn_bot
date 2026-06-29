#!/bin/bash

echo "========================================"
echo "    ZarVPN Automated OS Installer"
echo "========================================"

# ایجاد و ورود به پوشه پروژه برای دانلود نشدن فایل‌ها در روت اصلی سرور
mkdir -p Zarvpn_bot
cd Zarvpn_bot

# دانلود فایل‌های حیاتی مستقیماً از گیت‌هاب شما به درون پوشه
echo "[..] Downloading core installation files from GitHub..."
curl -sL -O https://raw.githubusercontent.com/Aziz-dev22/Zarvpn_bot/main/requirements.txt
curl -sL -O https://raw.githubusercontent.com/Aziz-dev22/Zarvpn_bot/main/install.py
curl -sL -O https://raw.githubusercontent.com/Aziz-dev22/Zarvpn_bot/main/update.sh

# آپدیت مخازن لینوکس و نصب پایتون
echo "[..] Updating system packages and installing Python..."
sudo apt update -y
sudo apt install python3 python3-pip python3-venv git -y

# ایجاد محیط مجازی پایتون
echo "[..] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# نصب کتابخانه‌های پایتون
echo "[..] Installing required Python libraries..."
pip install --upgrade pip
pip install -r requirements.txt

chmod +x update.sh

# حالا فایل وجود دارد و جادوگر بدون مشکل اجرا می‌شود
echo "[..] Starting configuration wizard..."
python install.py

echo "========================================"
echo " [✓] Installation process completed!"
echo " [📌] You can now run 'python bot.py' and 'python web_panel.py'"
echo "========================================"
