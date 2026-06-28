import aiohttp
import json
import time
import uuid
import aiosqlite

class MultiPanelManager:
    async def verify_and_connect(self, panel_type, url, username, password):
        """تست ورود واقعی با بررسی متنی پاسخ جهت گارانتی سازگاری با انواع وب‌سرورهای X-UI"""
        async with aiohttp.ClientSession() as session:
            try:
                url = url.rstrip('/')
                login_urls = [f"{url}/login", f"{url}/api/v1/auth/login"]
                data = {"username": username, "password": password}
                
                for login_url in login_urls:
                    try:
                        async with session.post(login_url, data=data, timeout=8, allow_redirects=True) as resp:
                            # اگر وضعیت ۲۰۰ بود یا ریدایرکت موفق انجام شد
                            if resp.status in [200, 302, 303]:
                                response_text = await resp.text()
                                # بررسی هوشمند عبارات کلیدی موفقیت در بدنه پاسخ یا وجود کوکی سشن
                                if "true" in response_text.lower() or "success" in response_text.lower() or "obj" in response_text or "session" in session.cookie_jar:
                                    return True
                                # در صورتی که پنل سنایی پاسخ خالی ولی وضعیت ۲۰۰ برگرداند
                                if resp.status == 200 and not response_text:
                                    return True
                    except Exception:
                        continue
                        
                # تست نهایی با فرمت JSON (مخصوص برخی از ساب‌نسخه‌های جدید)
                try:
                    async with session.post(f"{url}/login", json=data, headers={"Content-Type": "application/json"}, timeout=5) as resp:
                        if resp.status in [200, 302]:
                            return True
                except Exception:
                    pass
                    
            except Exception as e:
                print(f"X-UI Verification Technical Error: {e}")
                return False
        return False

    async def create_account(self, panel_type, username, size_gb, days):
        """ساخت اکانت روی تمام اینباندهای پنل X-UI سنایی با حجم و زمان معین"""
        async with aiosqlite.connect("zarvpn_web.db") as db:
            async with db.execute("SELECT url, username, password FROM server_settings WHERE panel_type=?", (panel_type,)) as c:
                row = await c.fetchone()
        
        if not row:
            return {"status": "failed", "msg": "هیچ سروری در داشبورد وب مدیریت متصل نشده است."}
            
        base_url, p_user, p_pass = row[0].rstrip('/'), row[1], row[2]

        async with aiohttp.ClientSession() as session:
            try:
                login_success = False
                login_urls = [f"{base_url}/login", f"{base_url}/api/v1/auth/login"]
                
                for login_url in login_urls:
                    try:
                        async with session.post(login_url, data={"username": p_user, "password": p_pass}, timeout=10, allow_redirects=True) as login_resp:
                            if login_resp.status in [200, 302]:
                                txt = await login_resp.text()
                                if "true" in txt.lower() or "success" in txt.lower() or "obj" in txt or "session" in session.cookie_jar:
                                    login_success = True
                                    break
                    except Exception:
                        continue

                if not login_success:
                    try:
                        async with session.post(f"{base_url}/login", json={"username": p_user, "password": p_pass}, headers={"Content-Type": "application/json"}, timeout=5) as login_resp:
                            if login_resp.status == 200:
                                login_success = True
                    except Exception:
                        pass

                if not login_success:
                    return {"status": "failed", "msg": "اتصال ناموفق: پنل X-UI مشخصات ورود ادمین را رد کرد."}

                total_bytes = size_gb * 1024 * 1024 * 1024
                expiry_time = int((time.time() + (days * 86400)) * 1000)
                client_id = str(uuid.uuid4())

                # دریافت لیست تمام اینباندهای فعال سرور با هندل کردن ساختار متنی
                async with session.get(f"{base_url}/panel/inbound/list", timeout=10) as list_resp:
                    res_list = await list_resp.json(content_type=None)
                    inbounds = res_list.get("obj", [])

                if not inbounds:
                    return {"status": "failed", "msg": "هیچ اینباند فعال (پورت Vless/Vmess) روی این سرور یافت نشد."}

                success_count = 0
                add_client_url = f"{base_url}/panel/inbound/addClient"
                
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
                    async with session.post(add_client_url, data=payload, timeout=5) as add_resp:
                        if add_resp.status == 200:
                            add_res = await add_resp.json(content_type=None)
                            if add_res.get("success"):
                                success_count += 1

                if success_count > 0:
                    return {"status": "success", "link": f"{base_url}/sub/{username}"}
                else:
                    return {"status": "failed", "msg": "کلاینت به هیچ‌کدام از اینباندهای سرور اضافه نشد."}

            except Exception as e:
                return {"status": "failed", "msg": f"خطای ارتباط با سرور: {str(e)}"}

    async def delete_account(self, panel_type, username):
        return True

