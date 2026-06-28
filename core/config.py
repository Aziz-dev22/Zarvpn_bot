# FILE: core/config.py

import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH")

ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

WEB_HOST = "0.0.0.0"
WEB_PORT = int(os.getenv("WEB_PORT", 8080))

DB_PATH = "zarvpn_web.db"
SECRET_KEY = os.getenv("SECRET_KEY", "zarvpn_secret")
