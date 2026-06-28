import aiohttp
import json
import time
import uuid
import aiosqlite

class MultiPanelManager:
    def __init__(self):
        # هدرهای تقلید رفتار مرورگر برای دور زدن خطای 403 Forbidden
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "http://127.0.0.1:2054",
            "Referer": "http://127.0.0.1:2054/panel/inbounds"
        }

    async def verify_and_connect(self, panel_type, url, username, password):
        """تست ورود زنده به پنل با هدرهای شبیه‌ساز مرورگر و دور زدن لایه ۴۰۳"""
        async with aiohttp.ClientSession() as session:
            try:
                url = url.rstrip('/')
                login_urls = [f"{url}/login", f"{url}/api/v1/auth/login"]
                data = {"username": username, "password": password}
                
                # بروزرسانی آدرس Origin در هدرها بر اساس دامنه یا آی‌پی ورودی
                custom_headers = self.headers.copy()
                custom_headers["Origin"] = url
                custom_headers["Referer"] = f"{url}/"

                for login_url in login_urls:
                    try:
                        async with session.post(login_url, data=data, headers=custom_headers, timeout=8, allow_redirects=True) as resp:
                            if resp.status in [200, 301, 302]:
                                response_text = await resp.text()
                                # تایید ورود در صورت وجود کوکی جلسه یا کلمه true در پاسخ JSON
                                if "true" in response_text.lower() or "success" in response_text.lower() or "session" in session.cookie_jar:
                                    return True
                    except Exception:
                        continue
                return False
            except Exception:
                return False

    async def create_account(self, panel_type, username, size_gb, days):
        """ساخت اکانت روی تمامی اینباندهای فعال با شبیه‌سازی کامل سشن مرورگر"""
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
                
                custom_headers = self.headers.copy()
                custom_headers["Origin"] = base_url
                custom_headers["Referer"] = f"{base_url}/"

                for login_url in login_urls:
                    try:
                        async with session.post(login_url, data={"username": p_user, "password": p_pass}, headers=custom_headers, timeout=8, allow_redirects=True) as login_resp:
                            if login_resp.status in [200, 301, 302]:
                                set_cookie = login_resp.headers.get('Set-Cookie', '')
                                if 'session=' in set_cookie:
                                    cookie_to_use = set_cookie.split(';')[0]
                                    login_success = True
                                    break
                                elif login_resp.cookies.get('session'):
                                    cookie_to_use = f"session={login_resp.cookies['session'].value}"
                                    login_success = True
                                    break
                    except Exception:
                        continue

                if not login_success:
                    return {"status": "failed", "msg": "اتصال ناموفق: پنل X-UI سنایی درخواست بات را مسدود کرد."}

                # اعمال کوکی سشن استخراج شده به هدر درخواست‌های بعدی
                final_headers = custom_headers.copy()
                if cookie_to_use:
                    final_headers["Cookie"] = cookie_to_use
                
                final_headers["Content-Type"] = "application/json"

                total_bytes = size_gb * 1024 * 1024 * 1024
                expiry_time = int((time.time() + (days * 86400)) * 1000)
                client_id = str(uuid.uuid4())

                # دریافت لیست اینباندها با هدر و کوکی معتبر
                async with session.get(f"{base_url}/panel/inbound/list", headers=final_headers, timeout=8) as list_resp:
                    res_list = await list_resp.json(content_type=None)
                    inbounds = res_list.get("obj", [])

                if not inbounds:
                    return {"status": "failed", "msg": "هیچ اینباند فعالی روی سرور X-UI یافت نشد."}

                success_count = 0
                add_client_url = f"{base_url}/panel/inbound/addClient"
                
                # بازگرداندن هدر به حالت فرم دیتا برای متد addClient سنایی
                final_headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"

                for inbound in inbounds:
                    inbound_id = inbound.get("id")
                    client_obj = {
                        "id": client_id, "alterId": 0, "email": username, "limitIp": 2,
                        "totalGB": total_bytes, "expiryTime": expiry_time, "enable": True,
                        "tgId": "", "subId": username
                    }
                    payload = {"id": inbound_id, "settings": json.dumps({"clients": [client_obj]})}
                    
                    async with session.post(add_client_url, data=payload, headers=final_headers, timeout=5) as add_resp:
                        if add_resp.status == 200:
                            add_res = await add_resp.json(content_type=None)
                            if add_res.get("success"):
                                success_count += 1

                if success_count > 0:
                    return {"status": "success", "link": f"{base_url}/sub/{username}"}
                return {"status": "failed", "msg": "سرور X-UI کلاینت جدید را روی اینباندها نپذیرفت."}

            except Exception as e:
                return {"status": "failed", "msg": f"خطای ارتباط با API سرور: {str(e)}"}

    async def delete_account(self, panel_type, username):
        return True

