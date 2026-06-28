import httpx
import uuid
import secrets
import json
import re
from core.logger import logger
from panels.manager import BasePanelManager

class SanaeiPanel(BasePanelManager):
    def __init__(self, panel_url: str, username: str, password: str):
        self.panel_url = panel_url.rstrip("/")
        self.username = username
        self.password = password
        self.client = httpx.AsyncClient(timeout=20.0, verify=False)
        self.cookies = None

    async def login(self) -> bool:
        """
        ورود به پنل با بررسی دقیق پاسخ برای جلوگیری از تایید اشتباه مشخصات خطا
        """
        url = f"{self.panel_url}/panel/api/login"
        try:
            res = await self.client.post(url, data={"username": self.username, "password": self.password})
            
            # بررسی اینکه آیا ارتباط برقرار شده و پنل پاسخ داده است
            if res.status_code == 200:
                response_data = res.json()
                # شرط اصلی: حتماً باید فیلد success مقدار True داشته باشد
                if response_data.get("success") is True:
                    self.cookies = res.cookies
                    logger.info("Sanaei Panel login successful.")
                    return True
                else:
                    logger.warning(f"Sanaei Login rejected by panel: {response_data.get('msg', 'Wrong credentials')}")
                    return False
            
            logger.error(f"Sanaei Login HTTP error. Status: {res.status_code}")
            return False
        except Exception as e:
            logger.error(f"Sanaei Login exception: {str(e)}")
            return False

    def sanitize_client_name(self, name: str) -> str:
        sanitized = re.sub(r'[^a-zA-Z0-9]', '', name)
        if not sanitized:
            return f"user{secrets.token_hex(3)}"
        return sanitized

    async def create_user(self, email: str, data_limit_gb: int, expire_days: int) -> dict | None:
        if not self.cookies and not await self.login(): 
            return None
            
        client_uuid = str(uuid.uuid4())
        clean_name = self.sanitize_client_name(email)
        client_email = f"{clean_name}_{secrets.token_hex(2)}"
        bytes_limit = data_limit_gb * 1024 * 1024 * 1024
        expiry_time = -(expire_days * 24 * 60 * 60 * 1000)
        
        client_settings = {
            "id": client_uuid,
            "alterId": 0,
            "email": client_email,
            "limitIp": 2,
            "totalGB": bytes_limit,
            "expiryTime": expiry_time,
            "enable": True,
            "tgId": "",
            "subId": client_uuid
        }
        
        inbound_id = 1 
        payload = {
            "id": inbound_id,
            "settings": json.dumps({"clients": [client_settings]})
        }
        
        url = f"{self.panel_url}/panel/api/inbounds/addClient"
        try:
            res = await self.client.post(url, json=payload, cookies=self.cookies)
            if res.status_code == 200 and res.json().get("success") is True:
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
        url = f"{self.panel_url}/panel/api/inbounds/1/delClient/{email}"
        try:
            res = await self.client.post(url, cookies=self.cookies)
            return res.status_code == 200 and res.json().get("success") is True
        except Exception as e:
            logger.error(f"Delete client exception: {str(e)}")
            return False

    async def get_user_info(self, email: str) -> dict | None:
        if not self.cookies and not await self.login(): return None
        url = f"{self.panel_url}/panel/api/inbounds/getClientTraffics/{email}"
        try:
            res = await self.client.get(url, cookies=self.cookies)
            if res.status_code == 200 and res.json().get("success") is True:
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
