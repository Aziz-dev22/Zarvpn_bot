import aiohttp
import json
import time
import uuid
import aiosqlite

class MultiPanelManager:
    async def verify_and_connect(self, panel_type, url, username, password):
        """تست ورود واقعی به پنل جهت تایید مشخصات ادمین"""
        async with aiohttp.ClientSession() as session:
            try:
                url = url.rstrip('/')
                data = {"username": username, "password": password}
                async with session.post(f"{url}/login", data=data, timeout=8) as resp:
                    if resp.status == 200: return True
            except Exception:
                return False
        return False

    async def create_account(self, panel_type, username, size_gb, days):
        """ساخت اکانت روی تمام اینباندهای پنل X-UI سنایی با حجم و زمان معین"""
        async with aiosqlite.connect("zarvpn_web.db") as db:
            async with db.execute("SELECT url, username, password FROM server_settings WHERE panel_type=?", (panel_type,)) as c:
                row = await c.fetchone()
        
        if not row:
            return {"status": "failed", "msg": "No server connected in web admin dashboard."}
            
        base_url, p_user, p_pass = row[0].rstrip('/'), row[1], row[2]

        async with aiohttp.ClientSession() as session:
            try:
                # ۱. لاگین در پنل سنایی و ذخیره سشن کوکی
                async with session.post(f"{base_url}/login", data={"username": p_user, "password": p_pass}, timeout=10) as login_resp:
                    res_login = await login_resp.json()
                    if not res_login.get("success"):
                        return {"status": "failed", "msg": "Login to X-UI panel failed"}

                total_bytes = size_gb * 1024 * 1024 * 1024
                expiry_time = int((time.time() + (days * 86400)) * 1000)
                client_id = str(uuid.uuid4())

                # ۲. دریافت لیست تمام اینباندهای فعال (Vless, Vmess, Trojan و ...)
                async with session.get(f"{base_url}/panel/inbound/list", timeout=10) as list_resp:
                    res_list = await list_resp.json()
                    inbounds = res_list.get("obj", [])

                if not inbounds:
                    return {"status": "failed", "msg": "No active inbounds found on your server."}

                # ۳. افزودن کلاینت به تک‌تک اینباندهای یافت شده سرور
                success_count = 0
                for inbound in inbounds:
                    inbound_id = inbound.get("id")
                    client_obj = {
                        "id": client_id,
                        "alterId": 0,
                        "email": username,
                        "limitIp": 2,
                        "totalGB": total_bytes,
                        "expiryTime": expiry_time,
                        "enable": True,
                        "tgId": "",
                        "subId": username
                    }
                    payload = {
                        "id": inbound_id,
                        "settings": json.dumps({"clients": [client_obj]})
                    }
                    async with session.post(f"{base_url}/panel/inbound/addClient", data=payload, timeout=5) as add_resp:
                        add_res = await add_resp.json()
                        if add_res.get("success"):
                            success_count += 1

                if success_count > 0:
                    return {"status": "success", "link": f"{base_url}/sub/{username}"}
                else:
                    return {"status": "failed", "msg": "Could not add client to any inbound"}

            except Exception as e:
                return {"status": "failed", "msg": str(e)}
