import aiohttp
import json
import time
import uuid
import aiosqlite

class MultiPanelManager:
    def __init__(self):
        # ذخیره کوکی سشن به صورت متنی برای تضمین پایداری در طول چرخه درخواست‌ها
        self.session_cookie = None

    async def verify_and_connect(self, panel_type, url, username, password):
        """تست ورود زنده به پنل و استخراج مستقیم کوکی‌های امنیتی"""
        async with aiohttp.ClientSession() as session:
            try:
                url = url.rstrip('/')
                login_urls = [f"{url}/login", f"{url}/api/v1/auth/login"]
                data = {"username": username, "password": password}
                
                for login_url in login_urls:
                    try:
                        async with session.post(login_url, data=data, timeout=8, allow_redirects=False) as resp:
                            # در اکثر نسخه‌های سنایی، لاگین موفق همراه با ریدایرکت (302) یا وضعیت 200 است
                            if resp.status in [200, 301, 302]:
                                # استخراج دستی کوکی session از هدر پاسخ برای دور زدن محدودیت‌های CookieJar
                                cookie_header = resp.headers.get('Set-Cookie', '')
                                if 'session=' in cookie_header or resp.cookies.get('session'):
                                    return True
                                
                                # بررسی متنی در صورت عدم وجود هدر مستقیم
                                text = await resp.text()
                                if "true" in text.lower() or "success" in text.lower():
                                    return True
                    except Exception:
                        continue
                return False
            except Exception:
                return False

    async def create_account(self, panel_type, username, size_gb, days):
        """ساخت اکانت همزمان روی تمام اینباندهای فعال با لایه کوکی تزریقی"""
        async with aiosqlite.connect("zarvpn_web.db") as db:
            async with db.execute("SELECT url, username, password FROM server_settings WHERE panel_type=?", (panel_type,)) as c:
                row = await c.fetchone()
        
        if not row:
            return {"status": "failed", "msg": "هیچ سروری در پنل مدیریت ثبت نشده است."}
            
        base_url, p_user, p_pass = row[0].rstrip('/'), row[1], row[2]

        async with aiohttp.ClientSession() as session:
            try:
                login_success = False
                cookie_to_use = None
                login_urls = [f"{base_url}/login", f"{base_url}/api/v1/auth/login"]
                
                for login_url in login_urls:
                    try:
                        async with session.post(login_url, data={"username": p_user, "password": p_pass}, timeout=8, allow_redirects=False) as login_resp:
                            if login_resp.status in [200, 301, 302]:
                                # ذخیره دقیق کوکی ست شده توسط وب‌سرور X-UI
                                set_cookie = login_resp.headers.get('Set-Cookie', '')
                                if 'session=' in set_cookie:
                                    cookie_to_use = set_cookie.split(';')[0]
                                    login_success = True
                                    break
                                elif login_resp.cookies.get('session'):
                                    cookie_to_use = f"session={login_resp.cookies['session'].value}"
                                    login_success = True
                                    break
                                
                                txt = await login_resp.text()
                                if "true" in txt.lower() or "success" in txt.lower():
                                    login_success = True
                                    break
                    except Exception:
                        continue

                if not login_success:
                    return {"status": "failed", "msg": "اطلاعات ورود توسط سرور X-UI رد شد. مشخصات را در پنل وب اصلاح کنید."}

                # هدر اختصاصی حاوی کوکی احراز هویت برای درخواست‌های بعدی
                headers = {}
                if cookie_to_use:
                    headers["Cookie"] = cookie_to_use

                total_bytes = size_gb * 1024 * 1024 * 1024
                expiry_time = int((time.time() + (days * 86400)) * 1000)
                client_id = str(uuid.uuid4())

                # دریافت لیست اینباندها با ارسال هدر کوکی زنده
                async with session.get(f"{base_url}/panel/inbound/list", headers=headers, timeout=8) as list_resp:
                    res_list = await list_resp.json(content_type=None)
                    inbounds = res_list.get("obj", [])

                if not inbounds:
                    return {"status": "failed", "msg": "اتصال برقرار شد اما هیچ اینباند (پورت Vless/Vmess) فعالی روی سرور X-UI وجود ندارد."}

                success_count = 0
                for inbound in inbounds:
                    inbound_id = inbound.get("id")
                    client_obj = {
                        "id": client_id, "alterId": 0, "email": username, "limitIp": 2,
                        "totalGB": total_bytes, "expiryTime": expiry_time, "enable": True,
                        "tgId": "", "subId": username
                    }
                    payload = {"id": inbound_id, "settings": json.dumps({"clients": [client_obj]})}
                    
                    async with session.post(f"{base_url}/panel/inbound/addClient", data=payload, headers=headers, timeout=5) as add_resp:
                        if add_resp.status == 200:
                            add_res = await add_resp.json(content_type=None)
                            if add_res.get("success"):
                                success_count += 1

                if success_count > 0:
                    return {"status": "success", "link": f"{base_url}/sub/{username}"}
                return {"status": "failed", "msg": "سرور X-UI درخواست افزودن کلاینت را نپذیرفت."}

            except Exception as e:
                return {"status": "failed", "msg": f"خطای ناخواسته در ارتباط با API سرور: {str(e)}"}
