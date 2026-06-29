#!/bin/bash

echo "========================================"
echo "    ZarVPN Updater Script v1.0.0"
echo "========================================"

# دریافت آخرین تغییرات از گیت‌هاب
echo "[..] Fetching latest changes from GitHub..."
git pull origin main

# آپدیت کردن پیش‌نیازها در صورت تغییر
echo "[..] Updating python dependencies..."
pip install -r requirements.txt

# پیام پایان عملیات
echo "========================================"
echo " [✓] ZarVPN updated successfully!"
echo " [📌] Please restart your bot and web panel services."
echo "========================================"
