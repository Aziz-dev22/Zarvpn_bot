import aiohttp
import json
import time
import uuid
import aiosqlite

class MultiPanelManager:
    async def create_account(self, panel_type, username, size_gb, days):
        """ساخت اکانت روی تمام اینباندهای پنل X-UI سنایی با حجم و زمان معین"""
        async with aiosqlite.connect("zarvpn_web.db") as db:
            async with db.execute("SELECT url, username, password FROM server_settings WHERE panel_type=?", (panel_type,)) as c:
                row = await c.fetchone()
        
        # اگر هنوز تنظیمات سرور وارد نشده باشد، آدرس سرور پیش‌فرض استفاده می‌شود
        if not row:
            base_url = "http://178.105.165.200:8080"
            p_user = "admin"
            p_pass = "admin"
        else:
            base_url, p_user, p_pass = row[0].rstrip('/'), row[1], row[2]

        # ایجاد Session برای ذخیره کوکی لاگین (ضروری برای X-UI)
        async with aiohttp.ClientSession() as session:
            try:
                # ۱. عملیات احراز هویت در پنل X-UI
                login_url = f"{base_url}/login"
                async with session.post(login_url, data={"username": p_user, "password": p_pass}, timeout=10) as login_resp:
                    res_login = await login_resp.json()
                    if not res_login.get("success"):
                        return {"status": "failed", "msg": "Login to X-UI panel failed"}

                # محاسبات حجم (بایت) و انقضا (میلی‌ثانیه)
                total_bytes = size_gb * 1024 * 1024 * 1024
                expiry_time = int((time.time() + (days * 86400)) * 1000)
                client_id = str(uuid.uuid4()) # تولید UUID اختصاصی برای کاربر جدید

                # ۲. دریافت لیست تمام اینباندهای سرور
                list_url = f"{base_url}/panel/inbound/list"
                async with session.get(list_url, timeout=10) as list_resp:
                    res_list = await list_resp.json()
                    if not res_list.get("success"):
                        return {"status": "failed", "msg": "Failed to fetch inbounds"}
                    inbounds = res_list.get("obj", [])

                if not inbounds:
                    return {"status": "failed", "msg": "No inbounds found on server"}

                # ۳. افزودن کلاینت به تک‌تک اینباندهای فعال (Vless, Vmess, Trojan)
                add_client_url = f"{base_url}/panel/inbound/addClient"
                success_count = 0

                for inbound in inbounds:
                    inbound_id = inbound.get("id")
                    
                    # ساختار استاندارد تنظیمات کلاینت در پنل سنایی
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
                    
                    async with session.post(add_client_url, data=payload, timeout=5) as add_resp:
                        add_res = await add_resp.json()
                        if add_res.get("success"):
                            success_count += 1

                if success_count > 0:
                    # ساب‌لینک استاندارد پنل سنایی جهت تحویل به مشتری
                    sub_link = f"{base_url}/sub/{username}"
                    return {"status": "success", "link": sub_link}
                else:
                    return {"status": "failed", "msg": "Could not add client to any inbound"}

            except Exception as e:
                print(f"X-UI API Error: {e}")
                return {"status": "failed", "msg": str(e)}
