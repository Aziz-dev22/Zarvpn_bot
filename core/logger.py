# core/logger.py
import logging
import os

# ایجاد پوشه لاگ در صورت عدم وجود
os.makedirs("logs", exist_ok=True)

logger = logging.getLogger("ZarVPN")
logger.setLevel(logging.INFO)

# فرمت نمایش لاگ‌ها (زمان - سطح خطا - پیام)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# هندلر برای ذخیره در فایل
file_handler = logging.FileHandler("logs/zarvpn.log", encoding="utf-8")
file_handler.setFormatter(formatter)

# هندلر برای نمایش در ترمینال
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

# اضافه کردن هندلرها به لاگر اصلی
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
