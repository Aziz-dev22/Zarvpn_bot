import os
import secrets
from pathlib import Path

def run_setup():
    env_path = Path(".env")
    
    # اگر فایل از قبل وجود داشت، نیازی به ساخت مجدد نیست
    if env_path.exists():
        return

    print("="*50)
    print("Welcome to ZarVPN Bot Installation Setup")
    print("="*50)
    
    bot_token = input("Enter your Telegram Bot Token: ").strip()
    while not bot_token:
        bot_token = input("Token cannot be empty. Enter Bot Token: ").strip()
        
    admin_ids = input("Enter Admin Telegram IDs (separate multiple IDs with comma): ").strip()
    while not admin_ids:
        admin_ids = input("At least one Admin ID is required: ").strip()
    
    # تولید یک کلید سکرت رندوم برای امنیت بیشتر دیتابیس کاربر
    secret_key = secrets.token_hex(32)
    
    # ساخت دایرکتوری دیتابیس در صورت عدم وجود
    Path("database").mkdir(exist_ok=True)
    
    env_content = f"""# ZarVPN Bot Configuration
BOT_TOKEN={bot_token}
ADMIN_IDS={admin_ids}

# Database Configuration
DATABASE_URL=sqlite:///database/zarvpn.db

# Security Key
SECRET_KEY={secret_key}
"""
    
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(env_content)
        
    print("\n[✓] Configuration file (.env) created successfully!")
    print("="*50)

if __name__ == "__main__":
    run_setup()
