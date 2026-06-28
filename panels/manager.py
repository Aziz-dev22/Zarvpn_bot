import aiohttp
import json
import time
import uuid
import aiosqlite

class MultiPanelManager:
    async def verify_and_connect(self, panel_type, url, username, password):
        """تست ورود زنده به پنل برای اطمینان از صحت اطلاعات"""
        async with aiohttp.ClientSession() as session:
            try:
                url = url.rstrip('/')
                login_urls = [f"{url}/login", f"{url}/api/v1/auth/login"]
                data = {"username": username, "password": password}
                
                for login_url in login_urls:
                    try:
                        async with session.post(login_url, data=data, timeout=8, allow_redirects=True) as resp:
                            if resp.status in [200, 302]:
                                text = await resp.text()
                                if "true" in text.lower() or "success" in text.lower() or "session" in session.cookie_jar:
                                    return True
                    except Exception:
                        continue
                return False
            except Exception:
                return False

    async def create_account(self, panel_type, username, size_gb, days):
        """ساخت اکانت روی تمامی اینباندهای فعال X-UI به صورت همزمان"""
        async with aiosqlite.connect("zarvpn_web.db") as db:
            async with db.execute("SELECT url, username, password FROM server_settings WHERE panel_type=?", (panel_type,)) as c:
                row = await c.fetchone()
        
        if not row:
            return {"status": "failed", "msg": "هیچ سروری در پنل مدیریت ثبت نشده است."}
            
        base_url, p_user, p_pass = row[0].rstrip('/'), row[1], row[2]

        async with aiohttp.ClientSession() as session:
            try:
                # ۱. عملیات ورود و دریافت کوکی جلسه
                login_success = False
                login_urls = [f"{base_url}/login", f"{base_url}/api/v1/auth/login"]
                
                for login_url in login_urls:
                    try:
                        async with session.post(login_url, data={"username": p_user, "password": p_pass}, timeout=8, allow_redirects=True) as login_resp:
                            if login_resp.status in [200, 302]:
                                txt = await login_resp.text()
                                if "true" in txt.lower() or "success" in txt.lower() or "session" in session.cookie_jar:
                                    login_success = True
                                    break
                    except Exception:
                        continue

                if not login_success:
                    return {"status": "failed", "msg": "اطلاعات ورود ادمین توسط سرور X-UI رد شد."}

                # پارامترهای کلاینت جدید
                total_bytes = size_gb * 1024 * 1024 * 1024
                expiry_time = int((time.time() + (days * 86400)) * 1000)
                client_id = str(uuid.uuid4())

                # ۲. دریافت لیست تمامی پروتکل‌ها و اینباندهای فعال سرور
                async with session.get(f"{base_url}/panel/inbound/list", timeout=8) as list_resp:
                    res_list = await list_resp.json(content_type=None)
                    inbounds = res_list.get("obj", [])

                if not inbounds:
                    return {"status": "failed", "msg": "هیچ پورت یا اینباند فعالی روی سرور یافت نشد."}

                # ۳. اضافه کردن کاربر به تمامی اینباندها به صورت خودکار
                success_count = 0
                for inbound in inbounds:
                    inbound_id = inbound.get("id")
                    client_obj = {
                        "id": client_id, "alterId": 0, "email": username, "limitIp": 2,
                        "totalGB": total_bytes, "expiryTime": expiry_time, "enable": True,
                        "tgId": "", "subId": username
                    }
                    payload = {"id": inbound_id, "settings": json.dumps({"clients": [client_obj]})}
                    
                    async with session.post(f"{base_url}/panel/inbound/addClient", data=payload, timeout=5) as add_resp:
                        if add_resp.status == 200:
                            add_res = await add_resp.json(content_type=None)
                            if add_res.get("success"):
                                success_count += 1

                if success_count > 0:
                    return {"status": "success", "link": f"{base_url}/sub/{username}"}
                return {"status": "failed", "msg": "سرور اجازه افزودن کلاینت را صادر نکرد."}

            except Exception as e:
                return {"status": "failed", "msg": f"خطای ارتباطی: {str(e)}"}

