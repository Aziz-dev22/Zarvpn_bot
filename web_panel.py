# web_panel.py
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from core.config import Config
from core.database import init_db
from web.routes import router as admin_router

# استفاده از Lifespan به جای on_event که منسوخ شده است
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[..] Checking database configurations...")
    # ساخت خودکار دیتابیس و جداول
    await init_db()
    print(f" [✓] ZarVPN Web Panel is configured for http://{Config.WEB_HOST}:{Config.WEB_PORT}")
    yield

app = FastAPI(
    title="ZarVPN Web Panel",
    description="پنل مدیریت هوشمند و ماژولار ربات فروش وی‌پی‌ان",
    version="1.0.0",
    lifespan=lifespan
)

# ایجاد پوشه استاتیک در صورت عدم وجود
os.makedirs("web/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# اتصال روت‌های بخش مدیریت
app.include_router(admin_router)

@app.get("/")
async def redirect_to_admin():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/admin")

if __name__ == "__main__":
    # اصلاح نام ماژول از web_panel.py:app به web_panel:app
    uvicorn.run(
        "web_panel:app",
        host=Config.WEB_HOST,
        port=Config.WEB_PORT,
        reload=True
    )
