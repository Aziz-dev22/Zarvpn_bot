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
        async with db.execute("SELECT value FROM settings WHERE key='nowpayments_api'") as c:
            row = await c.fetchone()
            api_key = row[0] if row else "تنظیم نشده"

    # قالب فوق پیشرفته HTML برای ادمین
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
            .card h3 {{ margin: 0; color: #94a3b8; }}
            .card p {{ font-size: 26px; font-weight: bold; margin: 10px 0 0 0; color: #3b82f6; }}
            .section {{ background: #1e293b; padding: 25px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #334155; }}
            input, select, button {{ padding: 10px; margin: 5px; border-radius: 8px; border: 1px solid #475569; background: #334155; color: white; }}
            button {{ background: #2563eb; cursor: pointer; border: none; font-weight: bold; }}
            button:hover {{ background: #1d4ed8; }}
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
                <p>مدیریت مولتی پنل (XUI / Marzban)، صرافی کریپتو و دیتابیس کاربری</p>
                <a href="/backup/download"><button class="btn-success">📥 دانلود و پشتیبان‌گیری فوری از دیتابیس</button></a>
            </div>

            <div class="stats">
                <div class="card"><h3>👥 کل کاربران ربات</h3><p>{total_users} نفر</p></div>
                <div class="card"><h3>🛒 کانکشن‌های فروخته شده</h3><p>{total_orders} عدد</p></div>
                <div class="card"><h3>💰 موجودی کل کاربران</h3><p>{total_balance:,} تومان</p></div>
            </div>

            <div class="section">
                <h3>🪙 تنظیمات اتصال به درگاه صرافی کریپتو (NowPayments)</h3>
                <form action="/settings/update-api" method="post">
                    <input type="text" name="api_key" placeholder="API Key صرافی را وارد کنید" value="{api_key}" style="width: 60%;">
                    <button type="submit">🔄 بروزرسانی API صرافی</button>
                </form>
            </div>

            <div class="section">
                <h3>🚀 ایجاد پلن فروش جدید برای ربات</h3>
                <form action="/plans/add" method="post">
                    <input type="text" name="name" placeholder="نام پلن (مثلا: پلن اقتصادی سنایی)" required>
                    <input type="number" name="size" placeholder="حجم به گیگابایت" required>
                    <input type="number" name="days" placeholder="تعداد روز" required>
                    <input type="number" name="price" placeholder="قیمت به تومان" required>
                    <select name="panel_type">
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

            <div class="section">
                <h3>👥 مدیریت و شارژ کیف پول کاربران ربات</h3>
                <form action="/users/charge" method="post">
                    <input type="number" name="user_id" placeholder="آیدی عددی تلگرام کاربر" required>
                    <input type="number" name="amount" placeholder="مبلغ شارژ (تومان) - برای کسر منفی بزنید" required>
                    <button type="submit">💳 اعمال شارژ</button>
                </form>

                <table>
                    <thead>
                        <tr><th>آیدی عددی تلگرام</th><th>نام کاربری</th><th>موجودی کیف پول</th></tr>
                    </thead>
                    <tbody>
    """
    for u in users_list:
        html_content += f"""
                        <tr><td>{u[0]}</td><td>@{u[1]}</td><td>{u[2]:,} تومان</td></tr>
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

# --- دایرکتوری توابع اکشن پنل وب ---

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

@app.post("/users/charge")
async def charge_user(user_id: int = Form(...), amount: int = Form(...)):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()
    return HTMLResponse("<script>alert('کیف پول کاربر بروزرسانی شد!'); window.location.href='/';</script>")

@app.post("/settings/update-api")
async def update_api(api_key: str = Form(...)):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('nowpayments_api', ?)", (api_key,))
        await db.commit()
    return HTMLResponse("<script>alert('تنظیمات صرافی ثبت شد!'); window.location.href='/';</script>")

@app.get("/backup/download")
async def download_backup():
    db_path = "zarvpn_web.db"
    backup_path = "backups/zarvpn_backup.db"
    if not os.path.exists("backups"): os.makedirs("backups")
    shutil.copyfile(db_path, backup_path)
    return FileResponse(path=backup_path, filename=f"zarvpn_backup_{datetime.now().strftime('%Y%m%d')}.db", media_type='application/octet-stream')
