import aiohttp
import time
from core import config

class MarzbanAPI:
    def __init__(self):
        self.base_url = config.PANEL_URL.rstrip('/')
        self.username = config.WEB_USERNAME
        self.password = config.WEB_PASSWORD
        self.token = None
        self.token_expires = 0

    # دریافت توکن به صورت خودکار و ناهمگام
    async def _get_token(self):
        if self.token and time.time() < self.token_expires:
            return self.token

        url = f"{self.base_url}/api/admin/token"
        data = {"username": self.username, "password": self.password}
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, data=data, timeout=10) as response:
                    if response.status_code == 200:
                        res_json = await response.json()
                        self.token = res_json.get("access_token")
                        # توکن‌های مرزبان معمولاً ۲۴ ساعت اعتبار دارند؛ ما ۱ ساعت کمتر در نظر می‌گیریم
                        self.token_expires = time.time() + 82800 
                        return self.token
            except Exception as e:
                print(f"Marzban Auth Error: {e}")
        return None

    # ساخت اکانت واقعی و تحویل لینک ساب‌اسکریپشن
    async def create_user(self, username: str, days: int, size_gb: int):
        token = await self._get_token()
        if not token:
            return {"status": "error", "message": "عدم اتصال به پنل مرزبان"}

        url = f"{self.base_url}/api/user"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        expire_time = int(time.time()) + (days * 86400)
        data_limit = size_gb * 1024 * 1024 * 1024 if size_gb > 0 else 0

        payload = {
            "username": username,
            "proxies": {"vless": {}, "vmess": {}, "trojan": {}, "shadowsocks": {}},
            "expire": expire_time,
            "data_limit": data_limit
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=payload, headers=headers, timeout=10) as response:
                    if response.status_code == 200:
                        res_json = await response.json()
                        sub_url = res_json.get("subscription_url")
                        if sub_url and not sub_url.startswith("http"):
                            sub_url = f"{self.base_url}{sub_url}"
                        return {"status": "success", "link": sub_url}
                    else:
                        res_text = await response.text()
                        return {"status": "error", "message": f"خطای پنل: {res_text}"}
            except Exception as e:
                return {"status": "error", "message": f"خطای شبکه مرزبان: {str(e)}"}

