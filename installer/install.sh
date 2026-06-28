#!/bin/bash
# FILE: installer/install.sh

echo "=============================="
echo "     ZARVPN PRO INSTALLER"
echo "=============================="

read -p "BOT TOKEN: " BOT_TOKEN
read -p "API ID: " API_ID
read -p "API HASH: " API_HASH
read -p "ADMIN ID: " ADMIN_ID
read -p "WEB PORT: " WEB_PORT

cat > .env <<EOF
BOT_TOKEN=$BOT_TOKEN
API_ID=$API_ID
API_HASH=$API_HASH
ADMIN_ID=$ADMIN_ID
WEB_PORT=$WEB_PORT
SECRET_KEY=zarvpn_secret
EOF

echo "Installing dependencies..."

apt update -y
apt install python3 python3-pip -y

pip3 install pyrogram tgcrypto flask aiosqlite

echo "Starting bot..."

python3 run.py
