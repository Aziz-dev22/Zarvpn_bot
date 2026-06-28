import aiohttp
import aiosqlite

class MultiPanelManager:
    @staticmethod
    async def get_credentials(panel_type):
        async with aiosqlite.connect("zarvpn_web.db") as db:
            async with db.execute("SELECT url, username, password FROM server_settings WHERE panel_type=?", (panel_type,)) as c:
                return await c.fetchone()

    async def create_account(self, panel_type, username, size_gb, days):
        creds = await self.get_credentials(panel_type)
        if panel_type == "connectix":
            # اتصال به API کانکتیکس
            async with aiosqlite.connect("zarvpn_web.db") as db:
                async with db.execute("SELECT value FROM settings WHERE key='connectix_token'") as c: token = (await c.fetchone())[0]
            url = "https://seller-api.connectix.vip/external/v1/user/create"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            data = {"username": username, "package_size": size_gb, "duration": days}
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=data, headers=headers) as resp:
                        res = await resp.json()
                        if resp.status == 200 or res.get("status") == "success":
                            return {"status": "success", "link": res.get("link")}
            except: pass
        
        elif panel_type == "xui":
            # نمونه لاگین و ساخت اکانت در پنل سنایی 
            return {"status": "success", "link": f"vless://{username}@xui-server.com:443?free_trial"}
            
        elif panel_type == "marzban":
            # نمونه لاگین و ساخت اکانت در پنل مرزبان
            return {"status": "success", "link": f"vless://{username}@marzban-node.com:443?security=xtls"}
            
        return {"status": "error", "message": "تنظیمات پنل در دیتابیس یافت نشد یا غیرفعال است."}

    async def delete_account(self, panel_type, username):
        # منطق حذف کاربر از پنل مربوطه
        return True

