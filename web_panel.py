# web_panel.py
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

from core.config import Config
from core.database import init_db
from web.routes import router as admin_router

app = FastAPI(
    title="ZarVPN Web Panel",
    description="پنل مدیریت هوشمند و ماژولار ربات فروش وی‌پی‌ان",
    version="1.0.0"
)

# ایجاد پوشه استاتیک در صورت عدم وجود (برای فایل‌های CSS/JS احتمالی در آینده)
os.makedirs("web/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# اتصال روت‌های بخش مدیریت به برنامه اصلی
app.include_router(admin_router)

@app.on_event("startup")
async def on_startup():
    """عملیات‌هایی که زمان روشن شدن وب‌پنل باید انجام شوند"""
    print("[..] Checking database configurations...")
    # ساخت خودکار دیتابیس و جداول در صورتی که از قبل ساخته نشده باشند
    await init_db()
    print(f" [✓] ZarVPN Web Panel is running on http://{Config.WEB_HOST}:{Config.WEB_PORT}")

@app.get("/")
async def redirect_to_admin():
    """انتقال خودکار کاربر از صفحه اصلی به دشبورد مدیریت"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/admin")

if __name__ == "__main__":
    # اجرای وب‌پنل بر اساس پورت و هاستی که در فایل .env ذخیره شده است
    uvicorn.run(
        "web_panel.py:app",
        host=Config.WEB_HOST,
        port=Config.WEB_PORT,
        reload=True  # قابلیت ری‌لود خودکار برای اعمال تغییرات کدها بدون نیاز به ریستارت
    )

