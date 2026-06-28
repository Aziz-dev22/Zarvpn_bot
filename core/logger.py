import logging
import os
from logging.handlers import RotatingFileHandler

# ایجاد پوشه لاگ در صورت عدم وجود
log_dir = "database"
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, "bot.log")

# تنظیمات فرمت نمایش لاگ‌ها
log_format = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# ایجاد لاگر اصلی
logger = logging.getLogger("ZarVPN_Logger")
logger.setLevel(logging.INFO)

# ۱. هندلر برای ذخیره در فایل (حداکثر ۵ مگابایت، سپس فایل جدید می‌سازد)
file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
file_handler.setFormatter(log_format)
logger.addHandler(file_handler)

# ۲. هندلر برای نمایش زنده در ترمینال
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(log_format)
logger.addHandler(stream_handler)

