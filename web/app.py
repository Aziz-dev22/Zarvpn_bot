from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
import aiosqlite
import shutil
import os
from core.database import init_commercial_db

app = FastAPI(title="ZarVpn Ultra Admin Web Panel")

@app.on_event("startup")
async def startup_event():
    await init_commercial_db()

@app.get("/", response_class=HTMLResponse)
async def admin_dashboard():
    async with aiosqlite.connect("zarvpn_web.db") as db:
        async with db.execute("SELECT * FROM plans") as c: plans = await c.fetchall()
        async with db.execute("SELECT user_id, username, balance, used_test FROM users") as c: users = await c.fetchall()
        async with db.execute("SELECT value FROM settings WHERE key='test_status'") as c: test_status = (await c.fetchone())[0]
        async with db.execute("SELECT value FROM settings WHERE key='channel_id'") as c: ch_id = (await c.fetchone())[0]
        async with db.execute("SELECT value FROM settings WHERE key='backup_channel'") as c: b_ch = (await c.fetchone())[0]
        
    html = f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>پنل مدیریت تحت وب ZarVpn</title>
        <style>
            body {{ font-family: Tahoma; background: #111827; color: #f3f4f6; padding: 20px; }}
            .card {{ background: #1f2937; padding: 20px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #374151; }}
            input, select, button {{ padding: 8px; margin: 5px; border-radius: 5px; background: #374151; color: white; border: none; }}
            button {{ background: #3b82f6; cursor: pointer; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ padding: 10px; border-bottom: 1px solid #374151; text-align: right; }}
            .btn-danger {{ background: #ef4444; }}
        </style>
    </head>
    <body>
        <h2>🌐 پنل وب مدیریت تحت وب سیستم ZarVpn</h2>
        
        <div class="card">
            <h3>🎛️ وضعیت اکانت تست رایگان سیستم: {test_status.upper()}</h3>
            <form action="/web/toggle-test" method="post">
                <button type="submit">تغییر وضعیت دکمه تست</button>
            </form>
        </div>

        <div class="card">
            <h3>🔌 اتصال و پیکربندی پنل‌ها (مرزبان / سنایی / کانکتیکس)</h3>
            <form action="/web/connect-panel" method="post">
                <select name="panel_type">
                    <option value="connectix">نمایندگی Connectix</option>
                    <option value="xui">X-UI سنایی</option>
                    <option value="marzban">مرزبان</option>
                </select>
                <input type="text" name="url" placeholder="آدرس پنل (URL / Endpoint)" required style="width: 300px;">
                <input type="text" name="user" placeholder="نام کاربری / توکن">
                <input type="password" name="passw" placeholder="رمز عبور">
                <button type="submit">اتصال پنل</button>
            </form>
        </div>

        <div class="card">
            <h3>👥 مدیریت و شارژ کاربران</h3>
            <table>
                <tr><th>آیدی عددی</th><th>یوزرنیم</th><th>موجودی حساب</th><th>وضعیت تست</th><th>عملیات</th></tr>
    """
    for u in users:
        html += f"""<tr>
            <td>{u[0]}</td><td>{u[1]}</td><td>{u[2]:,} تومان</td><td>{"گرفته" if u[3]==1 else "نشده"}</td>
            <td>
                <form action="/web/charge-user" method="post" style="display:inline;">
                    <input type="hidden" name="uid" value="{u[0]}">
                    <input type="number" name="amount" placeholder="مقدار تومان" style="width:100px;">
                    <button type="submit">شارژ</button>
                </form>
            </td>
        </tr>"""
    html += f"""
            </table>
        </div>

        <div class="card">
            <h3>💾 پشتیبان‌گیری و بازیابی سیستم</h3>
            <a href="/web/backup/download"><button>📥 دانلود فایل پشتیبان فعلی (دیتابیس)</button></a>
            <p style="font-size:12px; color:#9ca3af;">سیستم به صورت خودکار پشتیبان‌گیری را به کانال {b_ch} نیز ارسال می‌کند.</p>
        </div>
    </body>
    </html>
    """
    return html

@app.post("/web/toggle-test")
async def web_toggle_test():
    async with aiosqlite.connect("zarvpn_web.db") as db:
        async with db.execute("SELECT value FROM settings WHERE key='test_status'") as c: cur = (await c.fetchone())[0]
        new_s = "off" if cur == "on" else "on"
        await db.execute("UPDATE settings SET value=? WHERE key='test_status'", (new_s,))
        await db.commit()
    return HTMLResponse("<script>alert('وضعیت اکانت تست تغییر کرد'); window.location.href='/';</script>")

@app.post("/web/connect-panel")
async def web_connect_panel(panel_type: str = Form(...), url: str = Form(...), user: str = Form(""), passw: str = Form("")):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("INSERT OR REPLACE INTO server_settings (panel_type, url, username, password) VALUES (?, ?, ?, ?)", (panel_type, url, user, passw))
        if panel_type == "connectix":
            await db.execute("UPDATE settings SET value=? WHERE key='connectix_token'", (user,))
            await db.execute("UPDATE settings SET value=? WHERE key='connectix_endpoint'", (url,))
        await db.commit()
    return HTMLResponse("<script>alert('پنل با موفقیت متصل/بروزرسانی شد'); window.location.href='/';</script>")

@app.post("/web/charge-user")
async def web_charge_user(uid: int = Form(...), amount: int = Form(...)):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, uid))
        await db.commit()
    return HTMLResponse("<script>alert('کاربر شارژ شد'); window.location.href='/';</script>")

@app.get("/web/backup/download")
async def web_download_backup():
    if os.path.exists("zarvpn_web.db"):
        return FileResponse("zarvpn_web.db", filename="zarvpn_backup.db")
    raise HTTPException(status_code=404, detail="فایل یافت نشد")
