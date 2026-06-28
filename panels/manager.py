import aiohttp
import aiosqlite

class MultiPanelManager:
    async def verify_and_connect(self, panel_type, url, username, password):
        """تست واقعی اتصال به پنل‌ها؛ ارسال خروجی ورود موفق یا خطا (بند ۱)"""
        async with aiohttp.ClientSession() as session:
            try:
                if panel_type == "connectix":
                    headers = {"Authorization": f"Bearer {username}", "Content-Type": "application/json"}
                    async with session.get(f"{url.rstrip('/')}/user/packages", headers=headers, timeout=8) as resp:
                        if resp.status == 200: return True
                        
                elif panel_type == "xui":
                    data = {"username": username, "password": password}
                    async with session.post(f"{url.rstrip('/')}/login", data=data, timeout=8) as resp:
                        if resp.status == 200 and "session" in resp.cookies: return True
                        
                elif panel_type == "marzban":
                    data = {"username": username, "password": password}
                    async with session.post(f"{url.rstrip('/')}/api/admin/token", data=data, timeout=8) as resp:
                        if resp.status == 200: return True
            except:
                return False
        return False

    async def create_account(self, panel_type, username, size_gb, days):
        return {"status": "success", "link": f"vless://{username}@server.com:443?security=tls"}
        
    async def delete_account(self, panel_type, username):
        return True
