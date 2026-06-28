# FILE: panels/manager.py

import uuid
import random


class MultiPanelManager:

    def __init__(self):
        self.panels = ["xui", "marzban"]

    async def create_account(self, panel_type, username, days, gb):
        """
        شبیه‌سازی ساخت اکانت روی پنل
        در نسخه واقعی اینجا API XUI / Marzban وصل می‌شود
        """

        try:
            fake_link = f"https://t.me/vpn_{uuid.uuid4().hex[:10]}"

            return {
                "status": "success",
                "link": fake_link,
                "username": username,
                "expire_days": days,
                "traffic": gb
            }

        except Exception as e:
            return {
                "status": "error",
                "msg": str(e)
            }
