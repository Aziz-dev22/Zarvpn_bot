import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BOT_TOKEN: str = ""
    ADMIN_IDS: str = ""  # به صورت کاما جدا شده: 123,456
    
    # تنظیمات پنل تحت وب
    WEB_HOST: str = "0.0.0.0"
    WEB_PORT: int = 8000
    WEB_USERNAME: str = "admin"
    WEB_PASSWORD: str = "admin123"
    SECRET_KEY: str = "zarvpn_super_secret_key_2026"

    @property
    def admin_id_list(self):
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip().isdigit()]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
