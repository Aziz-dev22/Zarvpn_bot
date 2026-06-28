#!/bin/bash
clear
echo "=================================================="
echo "🎯 ZarVPN Combined Setup (Bot + Web Panel)"
echo "=================================================="

sudo apt update -y
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.local/bin/env
fi

cd ~
rm -rf Zarvpn_bot
git clone https://github.com/Aziz-dev22/Zarvpn_bot.git
cd Zarvpn_bot

uv venv --python 3.12
source .venv/bin/activate
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
uv pip install -r requirements.txt

clear
echo "📝 تنظیمات پیکربندی اولیه پروژه عمومی:"
echo "--------------------------------------------------"
read -p "توکن ربات تلگرام را وارد کنید: " bot_token
read -p "آیدی عددی ادمین تلگرام را وارد کنید: " admin_ids
read -p "پورت دلخواه برای ورود به پنل تحت وب: " web_port
read -p "یوزرنیم دلخواه برای ورود به پنل تحت وب: " web_user
read -p "پسورد دلخواه برای ورود به پنل تحت وب: " web_pass

cat << EOF > .env
BOT_TOKEN="$bot_token"
ADMIN_IDS="$admin_ids"
WEB_HOST="0.0.0.0"
WEB_PORT="$web_port"
WEB_USERNAME="$web_user"
WEB_PASSWORD="$web_pass"
EOF

clear
echo "✅ پروژه با موفقیت نصب و پیکربندی شد!"
echo "🚀 در حال راه‌اندازی ربات و پنل تحت وب شیشه‌ای زار وی‌پی‌ان روی پورت خالی 8050..."
echo "--------------------------------------------------"
uv run python bot.py
