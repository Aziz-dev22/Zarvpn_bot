from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
import aiosqlite
import os
import shutil
from datetime import datetime
from core.database import init_commercial_db

app = FastAPI(title="ZarVpn Mega Admin Panel")

@app.on_event("startup")
async def startup_event():
    await init_commercial_db()

@app.get("/", response_class=HTMLResponse)
async def admin_dashboard():
    async with aiosqlite.connect("zarvpn_web.db") as db:
        async with db.execute("SELECT COUNT(*), SUM(balance) FROM users") as c:
            u_info = await c.fetchone()
            total_users, total_balance = u_info[0] or 0, u_info[1] or 0
        async with db.execute("SELECT COUNT(*) FROM orders") as c:
            total_orders = (await c.fetchone())[0] or 0
        async with db.execute("SELECT * FROM plans") as c:
            plans = await c.fetchall()
        async with db.execute("SELECT user_id, username, balance FROM users ORDER BY created_at DESC") as c:
            users_list = await c.fetchall()
            
        async with db.execute("SELECT * FROM server_settings WHERE panel_type='xui'") as c:
            xui_server = await c.fetchone() or ("xui", "", "", "")
        async with db.execute("SELECT * FROM server_settings WHERE panel_type='marzban'") as c:
            marzban_server = await c.fetchone() or ("marzban", "", "", "")

        async with db.execute("SELECT value FROM settings WHERE key='swapwallet_api'") as c: row = await c.fetchone(); swap_api = row[0] if row else ""
        async with db.execute("SELECT value FROM settings WHERE key='swapwallet_merchant'") as c: row = await c.fetchone(); swap_merchant = row[0] if row else ""
        async with db.execute("SELECT value FROM settings WHERE key='connectix_token'") as c: row = await c.fetchone(); cx_token = row[0] if row else ""
        async with db.execute("SELECT value FROM settings WHERE key='connectix_endpoint'") as c: row = await c.fetchone(); cx_endpoint = row[0] if row else "https://seller-api.connectix.vip/external/v1"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>ابر پنل تجاری ZarVpn</title>
        <style>
            body {{ font-family: Tahoma; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ background: linear-gradient(135deg, #1e3a8a, #3b82f6); padding: 25px; border-radius: 15px; text-align: center; margin-bottom: 25px; }}
            .stats {{ display: flex; gap: 20px; margin-bottom: 25px; }}
            .card {{ background: #1e293b; padding: 20px; border-radius: 12px; width: 33%; text-align: center; border: 1px solid #334155; }}
            .card p {{ font-size: 26px; font-weight: bold; margin: 10px 0 0 0; color: #3b82f6; }}
            .section {{ background: #1e293b; padding: 25px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #334155; }}
            input, select, button {{ padding: 10px; margin: 5px; border-radius: 8px; border: 1px solid #475569; background: #334155; color: white; }}
            button {{ background: #2563eb; cursor: pointer; border: none; font-weight: bold; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th, td {{ padding: 12px; text-align: right; border-bottom: 1px solid #334155; }}
            th {{ background: #334155; color: #cbd5e1; }}
            .btn-danger {{ background: #dc2626; }}
            .btn-success {{ background: #16a34a; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>⚡ ابر پنل مدیریت تحت وب تجاری سیستم ZarVpn</h2>
                <p>مدیریت کامل مرزبان، X-UI، نمایندگی Connectix و درگاه صرافی Swap Wallet</p>
                <a href="/backup/download"><button class="btn-success">📥 پشتیبان‌گیری و دانلود دیتابیس</button></a>
            </div>

            <div class="section">
                <h3 style="color: #f59e0b;">🪙 تنظیمات اتصال به درگاه صرافی ایرانی Swap Wallet</h3>
                <form action="/settings/update-swapwallet" method="post">
                    <input type="text" name="api_key" placeholder="کلید API صرافی (Token)" value="{swap_api}" style="width: 40%;" required>
                    <input type="text" name="merchant_id" placeholder="مرچنت آیدی (Merchant ID)" value="{swap_merchant}" style="width: 30%;" required>
                    <button type="submit" class="btn-success">🔄 ذخیره درگاه Swap Wallet</button>
                </form>
            </div>

            <div class="section">
                <h3 style="color: #3b82f6;">🌐 تنظیمات و اتصال به پنل‌های V2Ray سرورها (مرزبان / X-UI)</h3>
                <h4 style="color: #3b82f6; margin-bottom: 5px;">🔧 اتصال به پنل X-UI (سنایی):</h4>
                <form action="/server-settings/update" method="post">
                    <input type="hidden" name="panel_type" value="xui">
                    <input type="text" name="url" placeholder="آدرس پنل (http://IP:PORT)" value="{xui_server[1]}" style="width: 35%;" required>
                    <input type="text" name="username" placeholder="نام کاربری پنل" value="{xui_server[2]}" required>
                    <input type="password" name="password" placeholder="رمز عبور پنل" value="{xui_server[3]}" required>
                    <button type="submit">🔗 ذخیره اتصال سنایی</button>
                </form>

                <h4 style="color: #16a34a; margin-top: 20px; margin-bottom: 5px;">🔧 اتصال به پنل مرزبان (Marzban):</h4>
                <form action="/server-settings/update" method="post">
                    <input type="hidden" name="panel_type" value="marzban">
                    <input type="text" name="url" placeholder="آدرس پنل (http://IP:PORT)" value="{marzban_server[1]}" style="width: 35%;" required>
                    <input type="text" name="username" placeholder="نام کاربری پنل" value="{marzban_server[2]}" required>
                    <input type="password" name="password" placeholder="رمز عبور پنل" value="{marzban_server[3]}" required>
                    <button type="submit" class="btn-success">🔗 ذخیره اتصال مرزبان</button>
                </form>
            </div>

            <div class="section">
                <h3 style="color: #a855f7;">🔮 تنظیمات توکن API پنل نمایندگی (Connectix)</h3>
                <form action="/settings/update-connectix" method="post">
                    <input type="text" name="token" placeholder="توکن API پنل کانکتیکس" value="{cx_token}" style="width: 50%;" required>
                    <input type="text" name="endpoint" placeholder="آدرس EndPoint پنل" value="{cx_endpoint}" style="width: 35%;" required>
                    <button type="submit" style="background: #a855f7;">🔒 ذخیره توکن نمایندگی</button>
                </form>
            </div>

            <div class="stats">
                <div class="card"><h3>👥 کل کاربران ربات</h3><p>{total_users} نفر</p></div>
                <div class="card"><h3>🛒 کانکشن‌های فروخته شده</h3><p>{total_orders} عدد</p></div>
                <div class="card"><h3>💰 موجودی کل کاربران</h3><p>{total_balance:,} تومان</p></div>
            </div>

            <div class="section">
                <h3>🚀 ایجاد پلن فروش جدید برای ربات</h3>
                <form action="/plans/add" method="post">
                    <input type="text" name="name" placeholder="نام پلن" required>
                    <input type="number" name="size" placeholder="حجم به گیگابایت" required>
                    <input type="number" name="days" placeholder="تعداد روز" required>
                    <input type="number" name="price" placeholder="قیمت به تومان" required>
                    <select name="panel_type">
                        <option value="connectix">پنل نمایندگی کانکتیکس (Connectix)</option>
                        <option value="xui">پنل ایکس یو آی (سنایی)</option>
                        <option value="marzban">پنل مرزبان</option>
                    </select>
                    <button type="submit" class="btn-success">➕ ثبت و افزودن پلن</button>
                </form>

                <table>
                    <thead>
                        <tr><th>شناسه</th><th>نام پلن</th><th>حجم</th><th>روز</th><th>قیمت</th><th>نوع اتصال</th><th>عملیات</th></tr>
                    </thead>
                    <tbody>
    """
    for p in plans:
        html_content += f"""
                        <tr>
                            <td>{p[0]}</td><td>{p[1]}</td><td>{p[2]} GB</td><td>{p[3]} روز</td><td>{p[4]:,} تومان</td><td><b>{p[5].upper()}</b></td>
                            <td><a href="/plans/delete/{p[0]}"><button class="btn-danger">حذف پلن</button></a></td>
                        </tr>
        """
    html_content += """
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

@app.post("/settings/update-connectix")
async def update_connectix(token: str = Form(...), endpoint: str = Form(...)):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('connectix_token', ?)", (token,))
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('connectix_endpoint', ?)", (endpoint,))
        await db.commit()
    return HTMLResponse("<script>alert('تنظیمات نمایندگی کانکتیکس ذخیره شد!'); window.location.href='/';</script>")

@app.post("/settings/update-swapwallet")
async def update_swapwallet(api_key: str = Form(...), merchant_id: str = Form(...)):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('swapwallet_api', ?)", (api_key,))
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('swapwallet_merchant', ?)", (merchant_id,))
        await db.commit()
    return HTMLResponse("<script>alert('تنظیمات صرافی Swap Wallet ذخیره شد!'); window.location.href='/';</script>")

@app.post("/server-settings/update")
async def update_server_settings(panel_type: str = Form(...), url: str = Form(...), username: str = Form(...), password: str = Form(...)):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("INSERT OR REPLACE INTO server_settings (panel_type, url, username, password) VALUES (?, ?, ?, ?)", (panel_type, url, username, password))
        await db.commit()
    return HTMLResponse("<script>alert('تنظیمات سرور ذخیره شد!'); window.location.href='/';</script>")

@app.post("/plans/add")
async def add_plan(name: str = Form(...), size: int = Form(...), days: int = Form(...), price: int = Form(...), panel_type: str = Form(...)):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("INSERT INTO plans (name, size_gb, days, price, panel_type) VALUES (?, ?, ?, ?, ?)", (name, size, days, price, panel_type))
        await db.commit()
    return HTMLResponse("<script>alert('پلن با موفقیت اضافه شد!'); window.location.href='/';</script>")

@app.get("/plans/delete/{plan_id}")
async def delete_plan(plan_id: int):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
        await db.commit()
    return HTMLResponse("<script>alert('پلن حذف شد!'); window.location.href='/';</script>")

@app.get("/backup/download")
async def download_backup():
    db_path = "zarvpn_web.db"
    backup_path = "backups/zarvpn_backup.db"
    if not os.path.exists("backups"): os.makedirs("backups")
    shutil.copyfile(db_path, backup_path)
    return FileResponse(path=backup_path, filename=f"zarvpn_backup_{datetime.now().strftime('%Y%m%d')}.db", media_type='application/octet-stream')
