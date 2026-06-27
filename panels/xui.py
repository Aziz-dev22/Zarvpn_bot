import aiohttp
from core import config

class XuiAPI:
    def __init__(self):
        self.base_url = config.PANEL_URL.rstrip('/')
        self.username = config.WEB_USERNAME
        self.password = config.WEB_PASSWORD
        self.cookies = None

    # ورود به پنل X-UI و ذخیره کوکی سشن
    async def _login(self):
        url = f"{self.base_url}/login"
        data = {"username": self.username, "password": self.password}
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, data=data, timeout=10) as response:
                    if response.status_code == 200:
                        res_json = await response.json()
                        if res_json.get("success"):
                            self.cookies = response.cookies
                            return True
            except Exception as e:
                print(f"X-UI Login Error: {e}")
        return False

    # ساخت کلاینت جدید در X-UI
    async def create_user(self, username: str, days: int, size_gb: int, inbound_id: int = 1):
        if not self.cookies:
            await self._login()

        # در X-UI ساب‌کلاینت‌ها به یک Inbound متصل می‌شوند
        url = f"{self.base_url}/xui/API/inbounds/addClient"
        headers = {"Content-Type": "application/json"}
        
        import uuid
        client_uuid = str(uuid.uuid4())
        total_gb = size_gb * 1024 * 1024 * 1024 if size_gb > 0 else 0
        expiry_time = days * 24 * 60 * 60 * 1000 # تبدیل به میلی‌ثانیه برای X-UI

        payload = {
            "id": inbound_id,
            "settings": f'{{"clients": [{{"id": "{client_uuid}", "alterId": 0, "email": "{username}", "totalGB": {total_gb}, "expiryTime": {expiry_time}, "enable": true}}]}}'
        }

        async with aiohttp.ClientSession(cookies=self.cookies) as session:
            try:
                async with session.post(url, json=payload, headers=headers, timeout=10) as response:
                    if response.status_code == 200:
                        res_json = await response.json()
                        if res_json.get("success"):
                            # تولید لینک فرضی ساب برای X-UI
                            sub_url = f"{self.base_url}/sub/{username}"
                            return {"status": "success", "link": sub_url}
                        return {"status": "error", "message": res_json.get("msg", "خطای ناشناخته X-UI")}
            except Exception as e:
                return {"status": "error", "message": f"خطای شبکه X-UI: {str(e)}"}

