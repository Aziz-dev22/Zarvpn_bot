import httpx
import uuid
import secrets
import json
import re
from core.logger import logger
from panels.manager import BasePanelManager

class SanaeiPanel(BasePanelManager):
    def __init__(self, panel_url: str, username: str, password: str):
        # حذف اسلش اضافه از آخر آدرس پنل
        self.panel_url = panel_url.rstrip("/")
        self.username = username
        self.password = password
        # غیرفعال کردن تایید SSL برای سازگاری با تمام سرورها و جلوگیری از ارورهای دست‌انداز گواهی
        self.client = httpx.AsyncClient(timeout=20.0, verify=False)
        self.cookies = None

    async def login(self) -> bool:
        url = f"{self.panel_url}/login"
        try:
            res = await self.client.post(url, data={"username": self.username, "password": self.password})
            if res.status_code == 200 and res.json().get("success"):
                self.cookies = res.cookies
                return True
            logger.error(f"Sanaei Login failed. Status: {res.status_code}, Response: {res.text}")
            return False
        except Exception as e:
            logger.error(f"Sanaei Login exception: {str(e)}")
            return False

    def sanitize_client_name(self, name: str) -> str:
        """
        پاکسازی نام ورودی کاربر برای اطمینان از اینکه فقط شامل حروف انگلیسی و عدد باشد.
        """
        # حذف هر کاراکتری به جز حروف انگلیسی و اعداد
        sanitized = re.sub(r'[^a-zA-Z0-9]', '', name)
        if not sanitized:
            # نام پشتیبان در صورتی که ورودی کاربر کاملاً نامعتبر بود
            return f"user{secrets.token_idx(3)}"
        return sanitized

    async def create_user(self, email: str, data_limit_gb: int, expire_days: int) -> dict | None:
        """
        ساخت کلاینت جدید با نام انتخابی مشتری و اتصال خودکار به سیستم ساب‌اسکریپشن جهت استفاده از تمام نودها و اینباندها
        """
        if not self.cookies and not await self.login(): 
            return None
            
        client_uuid = str(uuid.uuid4())
        
        # استانداردسازی نام کلاینت (فقط انگلیسی و عدد) + پسوند رندوم برای جلوگیری از مشکل تکراری بودن نام در پنل
        clean_name = self.sanitize_client_name(email)
        client_email = f"{clean_name}_{secrets.token_hex(2)}"
        
        # تبدیل حجم به بایت
        bytes_limit = data_limit_gb * 1024 * 1024 * 1024
        
        # محاسبه زمان انقضا به میلی‌ثانیه برای پنل ثنایی
        expiry_time = -(expire_days * 24 * 60 * 60 * 1000)
        
        # ساختار پکیج کلاینت با فعال بودن دسترسی کامل و ساب‌اسکریپشن
        client_settings = {
            "id": client_uuid,
            "alterId": 0,
            "email": client_email,
            "limitIp": 2, # محدودیت دو کاربره پیش‌فرض
            "totalGB": bytes_limit,
            "expiryTime": expiry_time,
            "enable": True,
            "tgId": "",
            "subId": client_uuid # ست کردن SubId برای فعال شدن ساب‌اسکریپشن روی تمام نودها
        }
        
        # ارسال کلاینت به اینباند اصلی (Inbound 1). سیستم ساب پنل ثنایی خودش کلاینت را به بقیه مسیرها متصل می‌کند.
        inbound_id = 1 
        
        payload = {
            "id": inbound_id,
            "settings": json.dumps({"clients": [client_settings]})
        }
        
        url = f"{self.panel_url}/xui/API/inbounds/addClient"
        try:
            res = await self.client.post(url, json=payload, cookies=self.cookies)
            if res.status_code == 200 and res.json().get("success"):
                # تولید لینک ساب‌اسکریپشن عمومی که تمام کانفیگ‌ها و نودها را به صورت پویا داخل خودش دارد
                sub_url = f"{self.panel_url}/sub/{client_uuid}"
                return {
                    "email": client_email, 
                    "uuid": client_uuid, 
                    "sub_url": sub_url
                }
            logger.error(f"AddClient failed. Response: {res.text}")
            return None
        except Exception as e:
            logger.error(f"AddClient exception: {str(e)}")
            return None

    async def delete_user(self, email: str) -> bool:
        if not self.cookies and not await self.login(): return False
        url = f"{self.panel_url}/xui/API/inbounds/1/delClient/{email}"
        try:
            res = await self.client.post(url, cookies=self.cookies)
            return res.status_code == 200 and res.json().get("success")
        except Exception as e:
            logger.error(f"Delete client exception: {str(e)}")
            return False

    async def get_user_info(self, email: str) -> dict | None:
        if not self.cookies and not await self.login(): return None
        url = f"{self.panel_url}/xui/API/inbounds/getClientTraffics/{email}"
        try:
            res = await self.client.get(url, cookies=self.cookies)
            if res.status_code == 200 and res.json().get("success"):
                d = res.json().get("obj", {})
                return {
                    "email": email, 
                    "up": d.get("up", 0), 
                    "down": d.get("down", 0), 
                    "total": d.get("total", 0), 
                    "expiry_time": d.get("expiryTime", 0), 
                    "enable": d.get("enable", True)
                }
            return None
        except Exception as e:
            logger.error(f"Get Client info exception: {str(e)}")
            return None

    async def close(self): 
        await self.client.aclose()
