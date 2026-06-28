#!/bin/bash
echo "=================================================="
echo "🎯 Starting ZarVPN Automatic Installation..."
echo "=================================================="

sudo apt update -y

if ! command -v uv &> /dev/null; then
    echo "📦 Installing UV Package Manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.local/bin/env
else
    echo "✅ UV Package Manager is already installed."
fi

cd ~
if [ -d "Zarvpn_bot" ]; then
    echo "🔄 Old installation found. Removing..."
    rm -rf Zarvpn_bot
fi

# کلون کردن مخزن گیت‌هاب شما
git clone https://github.com/Aziz-dev22/Zarvpn_bot.git
cd Zarvpn_bot

# ایجاد محیط مجازی امن برای اجرای پایدار پایتون ۳.۱۲
uv venv --python 3.12
source .venv/bin/activate

# دور زدن خطای کامپایل پایتون ۳.۱۴ در سرورهای جدید
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1

# نصب پیش‌نیازها
uv pip install -r requirements.txt

clear
echo "🚀 Installation complete! Starting setup..."
echo "--------------------------------------------------"
uv run python bot.py

