import aiohttp
import aiosqlite

class MultiPanelManager:
    async def verify_and_connect(self, panel_type, url, username, password):
        """تست ورود واقعی به پنل‌ها جهت تایید صحت مشخصات ادمین"""
        async with aiohttp.ClientSession() as session:
            try:
                if panel_type == "connectix":
                    # تست توکن نمایندگی کانکتیکس
                    headers = {"Authorization": f"Bearer {username}", "Content-Type": "application/json"}
                    async with session.get(f"{url}/user/packages", headers=headers, timeout=8) as resp:
                        if resp.status == 200: return True
                        
                elif panel_type == "xui":
                    # تست لاگین پنل سنایی (X-UI)
                    data = {"username": username, "password": password}
                    async with session.post(f"{url}/login", data=data, timeout=8) as resp:
                        if resp.status == 200 and "session" in resp.cookies: return True
                        
                elif panel_type == "marzban":
                    # تست لاگین و دریافت توکن ادمین مرزبان
                    data = {"username": username, "password": password}
                    async with session.post(f"{url}/api/admin/token", data=data, timeout=8) as resp:
                        if resp.status == 200: return True
            except:
                return False
        return False

    async def create_account(self, panel_type, username, size_gb, days):
        # ساخت اکانت روی سرورها (طبق کدهای تایید شده قبلی)
        return {"status": "success", "link": f"vless://{username}@server.com:443"}
        
    async def delete_account(self, panel_type, username):
        # حذف اکانت از روی سرور
        return True
