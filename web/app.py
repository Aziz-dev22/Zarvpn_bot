from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from core import config, database

app = FastAPI(title="ZarVpn Web Admin Panel", version="2.0.0")

@app.get("/")
async def root():
    return {"status": "ZarVpn Web Server is Running", "engine": "FastAPI"}

# آدرس وب برای گرفتن بکاپ فوری
@app.get("/admin/backup")
async def trigger_backup():
    result = database.backup_database()
    return {"message": result}

# آدرس وب برای بازیابی دیتابیس
@app.post("/admin/restore")
async def trigger_restore(filename: str):
    result = database.restore_database(filename)
    return {"message": result}

