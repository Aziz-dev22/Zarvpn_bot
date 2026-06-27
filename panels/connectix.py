import aiohttp

class ConnectixAPI:
    def __init__(self, api_token: str, endpoint: str = "https://seller-api.connectix.vip/external/v1"):
        self.endpoint = endpoint.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

    async def create_user(self, username: str, size_gb: int, days: int) -> dict:
        """ارسال درخواست ساخت کانکشن واقعی به API نمایندگی کانکتیکس"""
        url = f"{self.endpoint}/user/create" # این آدرس نمونه است، بر اساس داکیومنت پنل اصلاح می‌شود
        payload = {
            "username": username,
            "data_limit_gb": size_gb,
            "expire_days": days
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=self.headers, timeout=10) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        # فرض بر این است که خروجی حاوی لینک سابسکریپشن است
                        return {"status": "success", "link": data.get("subscription_url" or "sub_link")}
                    else:
                        res_text = await response.text()
                        return {"status": "error", "message": f"خطای سرور اصلی: {res_text}"}
        except Exception as e:
            return {"status": "error", "message": f"عدم اتصال به API کانکتیکس: {str(e)}"}

