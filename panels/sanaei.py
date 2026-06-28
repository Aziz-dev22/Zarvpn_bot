import httpx
import uuid
import secrets
import json
import re
from core.logger import logger

class SanaeiPanel:
    def __init__(self, panel_url: str, username: str, password: str):
        self.panel_url = panel_url.rstrip("/")
        self.username = username
        self.password = password
        self.client = httpx.AsyncClient(timeout=20.0, verify=False)
        self.cookies = None

    async def login(self) -> bool:
        url = f"{self.panel_url}/panel/api/login"
        try:
            res = await self.client.post(url, data={"username": self.username, "password": self.password})
            if res.status_code == 200:
                data = res.json()
                if data.get("success") is True:
                    self.cookies = res.cookies
                    return True
            return False
        except Exception as e:
            logger.error(f"Sanaei login failed: {str(e)}")
            return False

    async def create_user(self, email: str, data_limit_gb: int, expire_days: int) -> dict | None:
        if not self.cookies and not await self.login(): 
            return None
            
        client_uuid = str(uuid.uuid4())
        sanitized = re.sub(r'[^a-zA-Z0-9]', '', email)
        client_email = f"{sanitized or 'user'}_{secrets.token_hex(2)}"
        bytes_limit = data_limit_gb * 1024 * 1024 * 1024
        expiry_time = -(expire_days * 24 * 60 * 60 * 1000)
        
        client_settings = {
            "id": client_uuid, "alterId": 0, "email": client_email,
            "limitIp": 2, "totalGB": bytes_limit, "expiryTime": expiry_time,
            "enable": True, "tgId": "", "subId": client_uuid
        }
        
        payload = {"id": 1, "settings": json.dumps({"clients": [client_settings]})}
        url = f"{self.panel_url}/panel/api/inbounds/addClient"
        
        try:
            res = await self.client.post(url, json=payload, cookies=self.cookies)
            if res.status_code == 200 and res.json().get("success") is True:
                return {"email": client_email, "uuid": client_uuid, "sub_url": f"{self.panel_url}/sub/{client_uuid}"}
            return None
        except Exception as e:
            logger.error(f"Sanaei create user failed: {str(e)}")
            return None

    async def close(self):
        await self.client.aclose()
