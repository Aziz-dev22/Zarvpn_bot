from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
import aiosqlite
from panels.manager import MultiPanelManager
from core import config

app = FastAPI()
panel_manager = MultiPanelManager()

# تابع استایل نئونی مشترک تمام صفحات مینی‌آپ
def get_neon_style():
    return """
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0b0f19; color: #f1f5f9; padding: 20px; direction: rtl; text-align: right; }
        .container { max-width: 800px; margin: 0 auto; }
        h2, h3 { color: #38bdf8; text-shadow: 0 0 10px rgba(56, 189, 248, 0.3); border-bottom: 1px solid #1e293b; padding-bottom: 8px; margin-top: 25px; }
        .card { background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.5); }
        .profile-header { display: flex; align-items: center; justify-content: space-between; background: linear-gradient(135deg, #1e1b4b, #111827); border: 1px solid #312e81; border-radius: 12px; padding: 15px 20px; margin-bottom: 20px; }
        .profile-info { display: inline-block; }
        .profile-info p { margin: 5px 0; font-size: 14px; color: #94a3b8; }
        .profile-info b { color: #fff; font-size: 16px; }
        .balance-badge { background: #065f46; color: #34d399; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 14px; border: 1px solid #047857; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th { background: #1f2937; color: #94a3b8; font-size: 13px; text-align: right; padding: 12px; border-bottom: 2px solid #374151; }
        td { padding: 12px; border-bottom: 1px solid #1f2937; font-size: 14px; color: #e2e8f0; vertical-align: middle; }
        tr:hover { background: #1f2937; }
        input, select { background: #1f2937; color: #fff; border: 1px solid #374151; padding: 10px; border-radius: 8px; font-family: Tahoma; font-size: 13px; margin: 5px 0; width: 100%; box-sizing: border-box; }
        input:focus, select:focus { border-color: #38bdf8; outline: none; }
        .flex-row { display: table; width: 100%; }
        .flex-cell { display: table-cell; padding: 5px; }
        button { background: #2563eb; color: #fff; border: none; padding: 10px 16px; border-radius: 8px; cursor:pointer; font-weight: bold; font-family: Tahoma; font-size: 13px; transition: all 0.2s; width: 100%; }
        button:hover { background: #1d4ed8; box-shadow: 0 0 12px rgba(37, 99, 235, 0.4); }
        .btn-success { background: #059669; }
        .btn-success:hover { background: #047857; box-shadow: 0 0 12px rgba(5, 150, 105, 0.4); }
        .btn-danger { background: #dc2626; }
        .btn-danger:hover { background: #b91c1c; box-shadow: 0 0 12px rgba(220, 38, 38, 0.4); }
        .service-card { background: #1f2937; border: 1px solid #374151; border-radius: 10px; padding: 15px; margin-top: 10px; }
        a { text-decoration: none; }
    </style>
    """

@app.get("/", response_class=HTMLResponse)
async def admin_dashboard(admin_auth_id: int = None):
    # تفکیک دسترسی نماینده از ادمین کل
    is_root_admin = str(admin_auth_id) == str(config.ADMIN_ID) or admin_auth_id is None
    
    async with aiosqlite.connect("zarvpn_web.db") as db:
        async with db.execute("SELECT * FROM settings") as c: settings = dict(await c.fetchall())
        async with db.execute("SELECT user_id, username, balance FROM users") as c: users = await c.fetchall()
        async with db.execute("SELECT * FROM server_settings") as c: servers = await c.fetchall()
        async with db.execute("SELECT

