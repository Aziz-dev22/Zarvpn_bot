# 🌐 تابع دریافت توکن ادمین از پنل مرزبان
def get_marzban_token():
    try:
        login_url = f"{config.PANEL_URL}/api/admin/token"
        data = {
            "username": config.PANEL_USERNAME,
            "password": config.PANEL_PASSWORD
        }
        response = requests.post(login_url, data=data, timeout=10)
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    except Exception as e:
        print(f"Error getting token: {e}")
        return None

# 🌐 تابع واقعی ساخت اکانت در مرزبان و تحویل لینک VLESS/VMess
def create_vpn_account(username, days, size_gb):
    token = get_marzban_token()
    if not token:
        return "❌ خطا در اتصال به پنل ادمین (توکن دریافت نشد)"
        
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # محاسبه زمان انقضا به فرمت Epoch/Timestamp
    import time
    expire_time = int(time.time()) + (days * 86400)
    
    # محاسبه حجم به بایت
    data_limit = size_gb * 1024 * 1024 * 1024
    
    user_url = f"{config.PANEL_URL}/api/user"
    payload = {
        "username": username,
        "proxies": {"vless": {}, "vmess": {}}, # فعال‌سازی پروتکل‌ها
        "expire": expire_time,
        "data_limit": data_limit
    }
    
    try:
        response = requests.post(user_url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            # دریافت لینک‌های اتصال (subscription url) از خروجی پنل مرزبان
            sub_url = response.json().get("subscription_url")
            # اگر ساب‌لینک مستقیم نبود، آدرس پنل را به ابتدای آن می‌چسبانیم
            if sub_url and not sub_url.startswith("http"):
                sub_url = f"{config.PANEL_URL}{sub_url}"
            return sub_url
        else:
            return f"❌ پنل خطا داد: {response.text}"
    except Exception as e:
        return f"❌ خطای شبکه: {e}"
