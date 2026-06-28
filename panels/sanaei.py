import httpx
import uuid
import secrets
from core.logger import logger
from panels.manager import BasePanelManager

class SanaeiPanel(BasePanelManager):
    def __init__(self, panel_url: str, username: str, password: str):
        # حذف اسلش آخر آدرس در صورت وجود برای جلوگیری از خرابی URLها
        self.panel_url = panel_url.rstrip("/")
        self.username = username
        self.password = password
        self.client = httpx.AsyncClient(timeout=15.0, verify=False)
        self.cookies = None

    async def login(self) -> bool:
        """ورود به پنل ثنایی و ذخیره کوکی جلسات"""
        url = f"{self.panel_url}/login"
        data = {"username": self.username, "password": self.password}
        try:
            response = await self.client.post(url, data=data)
            if response.status_code == 200 and response.json().get("success"):
                self.cookies = response.cookies
                logger.info(f"Successfully logged into Sanaei panel: {self.panel_url}")
                return True
            logger.warning(f"Failed to login to Sanaei panel: {response.text}")
            return False
        except Exception as e:
            logger.error(f"Error logging into Sanaei panel: {str(e)}")
            return False

    async def create_user(self, email: str, data_limit_gb: int, expire_days: int) -> dict | None:
        """
        ساخت یک کاربر جدید (Client) در پنل ثنایی
        توجه: این متد به صورت پیش‌فرض کاربر را به اولین Inbound با شناسه 1 اضافه می‌کند.
        """
        if not self.cookies:
            is_logged_in = await self.login()
            if not is_logged_in:
                return None

        url = f"{self.panel_url}/xui/API/inbounds/addClient"
        
        # تولید UUID و ایمیل اختصاصی و رندوم
        client_uuid = str(uuid.uuid4())
        client_email = f"{email}_{secrets.token_hex(3)}"
        
        # محاسبه حجم به بایت و زمان به میلی‌ثانیه
        bytes_limit = data_limit_gb * 1024 * 1024 * 1024
        expiry_time = -(expire_days * 24 * 60 * 60 * 1000) # مقدار منفی در ثنایی یعنی تعداد روز اعتبار از زمان اولین اتصال

        payload = {
            "id": 1, # شناسه اینباند پیش‌فرض (قابل تغییر در آینده از مدیریت)
            "settings": "{\"clients\":[{\"id\":\"" + client_uuid + "\",\"alterId\":0,\"email\":\"" + client_email + "\",\"limitIp\":2,\"totalGB\":" + str(bytes_limit) + ",\"expiryTime\":" + str(expiry_time) + ",\"enable\":true,\"tgId\":\"\",\"subId\":\"\"}]}"
        }

        try:
            response = await self.client.post(url, json=payload, cookies=self.cookies)
            result = response.json()
            if response.status_code == 200 and result.get("success"):
                logger.info(f"User {client_email} created successfully in Sanaei.")
                
                # ساخت لینک اشتراک پیش‌فرض پنل ثنایی
                sub_url = f"{self.panel_url}/sub/{client_uuid}"
                
                return {
                    "email": client_email,
                    "uuid": client_uuid,
                    "sub_url": sub_url
                }
            logger.warning(f"Failed to create user in Sanaei: {response.text}")
            return None
        except Exception as e:
            logger.error(f"Error creating user in Sanaei: {str(e)}")
            return None

    async def delete_user(self, email: str) -> bool:
        """حذف کاربر با استفاده از ایمیل او از اینباند شماره 1"""
        if not self.cookies:
            await self.login()

        # در پنل ثنایی برای حذف ابتدا باید UUID یا ایمیل کلاینت را در اینباند پیدا کرد
        # برای سادگی، API مستقیم حذف با ایمیل در ورژن‌های جدید به این شکل است:
        url = f"{self.panel_url}/xui/API/inbounds/1/delClient/{email}"
        
        try:
            response = await self.client.post(url, cookies=self.cookies)
            if response.status_code == 200 and response.json().get("success"):
                logger.info(f"User {email} deleted from Sanaei panel.")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting user {email} from Sanaei: {str(e)}")
            return False

    async def get_user_info(self, email: str) -> dict | None:
        """دریافت اطلاعات حجم مصرفی و وضعیت کاربر"""
        if not self.cookies:
            await self.login()

        url = f"{self.panel_url}/xui/API/inbounds/getClientTraffics/{email}"
        try:
            response = await self.client.get(url, cookies=self.cookies)
            result = response.json()
            if response.status_code == 200 and result.get("success"):
                data = result.get("obj", {})
                return {
                    "email": email,
                    "up": data.get("up", 0), # حجم آپلود به بایت
                    "down": data.get("down", 0), # حجم دانلود به بایت
                    "total": data.get("total", 0), # حجم کل مجاز به بایت
                    "expiry_time": data.get("expiryTime", 0), # زمان انقضا
                    "enable": data.get("enable", True)
                }
            return None
        except Exception as e:
            logger.error(f"Error getting user info {email} from Sanaei: {str(e)}")
            return None

    async def close(self):
        """بستن کانکشن httpx برای جلوگیری از نشت حافظه"""
        await self.client.aclose()

