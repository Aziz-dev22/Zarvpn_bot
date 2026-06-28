from abc import ABC, abstractmethod

class BasePanelManager(ABC):
    """
    یک قالب پایه برای تمام پنل‌های وی‌پی‌ان (ثنایی، مرزبان و غیره)
    تمام کلاس‌های پنل باید از این کلاس ارث‌بری کنند و این متدها را داشته باشند.
    """

    @abstractmethod
    async def login(self) -> bool:
        """متد ورود به پنل و دریافت کوکی یا توکن"""
        pass

    @abstractmethod
    async def create_user(self, email: str, data_limit_gb: int, expire_days: int) -> dict | None:
        """متد ساخت یک کاربر جدید در پنل"""
        pass

    @abstractmethod
    async def delete_user(self, email: str) -> bool:
        """متd حذف کاربر از پنل"""
        pass

    @abstractmethod
    async def get_user_info(self, email: str) -> dict | None:
        """متد دریافت وضعیت حجم و زمان باقی‌مانده کاربر"""
        pass

