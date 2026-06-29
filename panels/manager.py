# panels/manager.py
import aiohttp
from panels.sanaei import SanaeiPanel
# اگر مرزبان هم اضافه شود در آینده اینجا ایمپورت می‌شود

class PanelManager:
    @staticmethod
    def get_panel_client(panel_model):
        """
        بر اساس نوع پنل ذخیره شده در دیتابیس، شیء مناسب برای اتصال را برمی‌گرداند.
        """
        if panel_model.panel_type.lower() == "sanaei":
            return SanaeiPanel(panel_model.api_url, panel_model.username, panel_model.password)
        elif panel_model.panel_type.lower() == "marzban":
            # در گام‌های بعدی متد مرزبان را اینجا کامل می‌کنیم
            raise NotImplementedError("اتصال مرزبان در آپدیت بعدی اضافه می‌شود.")
        else:
            raise ValueError("نوع پنل ناشناخته است.")

    @staticmethod
    async def test_connection(panel_model):
        """تست اتصال واقعی به پنل"""
        try:
            client = PanelManager.get_panel_client(panel_model)
            return await client.login()
        except Exception as e:
            print(f"Error testing panel connection: {e}")
            return False
