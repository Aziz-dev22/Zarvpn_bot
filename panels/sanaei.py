# panels/sanaei.py
import aiohttp
import json

class SanaeiPanel:
    def __init__(self, api_url, username, password):
        # حذف اسلش اضافی از آخر آدرس در صورت وجود
        self.api_url = api_url.rstrip('/')
        self.username = username
        self.password = password
        self.cookies = None

    async def login(self):
        """ورود به پنل سنایی و دریافت کوکی سشن"""
        url = f"{self.api_url}/login"
        payload = {
            "username": self.username,
            "password": self.password
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=payload, timeout=10) as response:
                    if response.status == 200:
                        res_json = await response.json()
                        if res_json.get("success"):
                            # ذخیره کوکی‌ها برای درخواست‌های بعدی
                            self.cookies = response.cookies
                            return True
                    return False
        except Exception as e:
            print(f"Sanaei Login Error: {e}")
            return False

    async def add_client(self, inbound_id, email, uuid, limit_ip=0, total_gb=0, expiry_days=0):
        """ساخت یک کاربر جدید در یک اینباند مشخص"""
        if not self.cookies:
            await self.login()
            
        url = f"{self.api_url}/panel/api/inbounds/addClient"
        
        # محاسبه حجم به بایت
        total_bytes = total_gb * 1024 * 1024 * 1024 if total_gb > 0 else 0
        # محاسبه زمان انقضا به میلی‌ثانیه (Timestamp)
        import time
        expiry_time = int((time.time() + (expiry_days * 86400)) * 1000) if expiry_days > 0 else 0

        client_setting = {
            "id": uuid,
            "alterId": 0,
            "email": email,
            "limitIp": limit_ip,
            "totalGB": total_bytes,
            "expiryTime": expiry_time,
            "enable": True,
            "tgId": "",
            "subId": ""
        }
        
        payload = {
            "id": inbound_id,
            "settings": json.dumps({"clients": [client_setting]})
        }
        
        try:
            async with aiohttp.ClientSession(cookies=self.cookies) as session:
                async with session.post(url, json=payload, timeout=10) as response:
                    if response.status == 200:
                        res_json = await response.json()
                        return res_json.get("success", False)
                    return False
        except Exception as e:
            print(f"Sanaei Add Client Error: {e}")
            return False

    async def delete_client(self, inbound_id, client_uuid):
        """حذف کاربر از پنل سنایی"""
        if not self.cookies:
            await self.login()
            
        url = f"{self.api_url}/panel/api/inbounds/{inbound_id}/delClient/{client_uuid}"
        
        try:
            async with aiohttp.ClientSession(cookies=self.cookies) as session:
                async with session.post(url, timeout=10) as response:
                    if response.status == 200:
                        res_json = await response.json()
                        return res_json.get("success", False)
                    return False
        except Exception as e:
            print(f"Sanaei Delete Client Error: {e}")
            return False
