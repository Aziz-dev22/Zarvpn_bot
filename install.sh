# install.py
import os
import secrets

def run_installer():
    print("="*40)
    print("    ZarVPN Installation Wizard    ")
    print("="*40)
    
    bot_token = input("1. Enter Telegram Bot Token: ").strip()
    admin_ids = input("2. Enter Admin Telegram IDs (separated by comma): ").strip()
    
    web_port = input("3. Enter Web Panel Port [Default: 8000]: ").strip() or "8000"
    web_user = input("4. Enter Admin Web Username [Default: admin]: ").strip() or "admin"
    web_pass = input("5. Enter Admin Web Password: ").strip()
    
    # تولید یک کلید سکرت امن به صورت خودکار برای سشن‌ها و JWT
    secret_key = secrets.token_hex(32)
    
    env_content = f"""# Bot Configuration
BOT_TOKEN={bot_token}
ADMIN_IDS={admin_ids}

# Web Panel Configuration
WEB_HOST=0.0.0.0
WEB_PORT={web_port}
WEB_ADMIN_USERNAME={web_user}
WEB_ADMIN_PASSWORD={web_pass}
SECRET_KEY={secret_key}

# Database
DATABASE_URL=sqlite+aiosqlite:///database/zarvpn.db
"""
    
    # ایجاد پوشه دیتابیس در صورت عدم وجود
    os.makedirs("database", exist_ok=True)
    
    with open(".env", "w", encoding="utf-8") as f:
        f.write(env_content)
        
    print("\n" + "="*40)
    print(" [✓] Configuration saved to .env successfully!")
    print("="*40)

if __name__ == "__main__":
    run_installer()
