#!/bin/bash

echo "========================================"
echo "    ZarVPN Automated OS Updater"
echo "========================================"

# ورود به محیط مجازی پایتون در صورت وجود
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# دریافت آخرین تغییرات از گیت‌هاب شما
echo "[..] Fetching latest codes from GitHub..."
git pull origin main

# آپدیت کتابخانه‌ها
echo "[..] Updating dependencies..."
pip install -r requirements.txt

echo "========================================"
echo " [✓] ZarVPN has been updated successfully!"
echo "========================================"
