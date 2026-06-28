from fastapi import FastAPI, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
import aiosqlite
import os
import shutil
from core.database import init_commercial_db

app = FastAPI(title="ZarVpn Mega Core Infrastructure")

@app.on_event("startup")
async def startup_event():
    await init_commercial_db()

# --- پنل وب مدیریت کامل ادمین ---
@app.get("/", response_class=HTMLResponse)
async def admin_dashboard():
    async with aiosqlite.connect("zarvpn_web.db") as db:
        async with db.execute("SELECT * FROM server_settings") as c: servers = await c.fetchall()
        async with db.execute("SELECT user_id, username, balance, used_test FROM users") as c: users = await c.fetchall()
        async with db.execute("SELECT value FROM settings WHERE key='test_status'") as c: test_status = (await c.fetchone())[0]
        async with db.execute("SELECT value FROM settings WHERE key='backup_channel'") as c: b_ch = (await c.fetchone())[0]

    server_rows = "".join([f"<tr><td>{s[0].upper()}</td><td>{s[1]}</td><td>{s[2]}</td></tr>" for s in servers])
    user_rows = "".join([f"""<tr>
        <td>{u[0]}</td><td>{u[1]}</td><td>{u[2]:,} تومان</td><td>{"بله" if u[3]==1 else "خیر"}</td>
        <td>
            <form action="/web/edit-user" method="post" style="display:inline;">
                <input type="hidden" name="uid" value="{u[0]}">
                <input type="number" name="new_balance" placeholder="تغییر موجودی" required style="width:100px;">
                <button type="submit">اعمال</button>
            </form>
            <a href="/web/delete-user/{u[0]}"><button class="btn-danger">حذف کاربر</button></a>
        </td>
    </tr>""" for u in users])

    html = f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head><meta charset="UTF-8"><title>پنل ادمین وب ZarVpn</title>
    <style>
        body {{ font-family: Tahoma; background: #0f172a; color: #e2e8f0; padding: 20px; }}
        .box {{ background: #1e293b; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #334155; }}
        input, select, button {{ padding: 8px; margin: 5px; border-radius: 6px; background: #334155; color: white; border: 1px solid #475569; }}
        button {{ background: #2563eb; cursor: pointer; border: none; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ padding: 10px; border-bottom: 1px solid #334155; text-align: right; }}
        th {{ background: #334155; }}
        .btn-danger {{ background: #dc2626; }}
    </style></head>
    <body>
        <h2>⚙️ پنل مدیریتی تحت وب یکپارچه ZarVpn</h2>
        
        <div class="box">
            <h3>🎛️ کنترل وضعیت لایسنس تست: {test_status.upper()}</h3>
            <form action="/web/toggle-test" method="post"><button type="submit">روشن/خاموش کردن تست رایگان</button></form>
        </div>

        <div class="box">
            <h3>🔌 متصل کردن و پیکربندی پنل‌ها (مرزبان، سنایی، کانکتیکس)</h3>
            <form action="/web/connect-panel" method="post">
                <select name="panel_type">
                    <option value="connectix">نمایندگی Connectix</option>
                    <option value="xui">X-UI سنایی</option>
                    <option value="marzban">مرزبان</option>
                </select>
                <input type="text" name="url" placeholder="آدرس سرور یا Endpoint API" required style="width:250px;">
                <input type="text" name="user" placeholder="نام کاربری / توکن ادمین">
                <input type="password" name="passw" placeholder="رمز عبور">
                <button type="submit">ذخیره و اتصال سرور</button>
            </form>
            <table><thead><tr><th>نوع پنل</th><th>آدرس اتصال</th><th>نام کاربری ادمین</th></tr></thead><tbody>{server_rows}</tbody></table>
        </div>

        <div class="box">
            <h3>👥 مدیریت و کنترل کاربران سیستم</h3>
            <table>
                <thead><tr><th>آیدی عددی</th><th>یوزرنیم</th><th>موجودی کیف پول</th><th>تست رایگان</th><th>عملیات ادمین</th></tr></thead>
                <tbody>{user_rows}</tbody>
            </table>
        </div>

        <div class="box">
            <h3>💾 مدیریت پشتیبان‌گیری و بازیابی (Backup & Restore)</h3>
            <a href="/web/backup/download"><button style="background:#16a34a;">📥 دانلود فایل دیتابیس فعلی</button></a>
            <hr style="border-color:#334155; margin:15px 0;">
            <form action="/web/backup/restore" method="post" enctype="multipart/form-data">
                <label>📤 آپلود و بازیابی دیتابیس (فایل .db): </label>
                <input type="file" name="file" required>
                <button type="submit" class="btn-danger">🔂 بازیابی دیتابیس سیستم</button>
            </form>
        </div>
    </body></html>
    """
    return HTMLResponse(html)

@app.post("/web/toggle-test")
async def web_toggle():
    async with aiosqlite.connect("zarvpn_web.db") as db:
        async with db.execute("SELECT value FROM settings WHERE key='test_status'") as c: cur = (await c.fetchone())[0]
        await db.execute("UPDATE settings SET value=? WHERE key='test_status'", ("off" if cur == "on" else "on",))
        await db.commit()
    return HTMLResponse("<script>alert('وضعیت تست تغییر کرد'); window.location.href='/';</script>")

@app.post("/web/connect-panel")
async def web_connect(panel_type: str = Form(...), url: str = Form(...), user: str = Form(""), passw: str = Form("")):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("INSERT OR REPLACE INTO server_settings (panel_type, url, username, password) VALUES (?, ?, ?, ?)", (panel_type, url, user, passw))
        await db.commit()
    return HTMLResponse("<script>alert('اتصال سرور با موفقیت ثبت شد'); window.location.href='/';</script>")

@app.post("/web/edit-user")
async def web_edit_user(uid: int = Form(...), new_balance: int = Form(...)):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, uid))
        await db.commit()
    return HTMLResponse("<script>alert('موجودی کاربر بروزرسانی شد'); window.location.href='/';</script>")

@app.get("/web/delete-user/{uid}")
async def web_delete_user(uid: int):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("DELETE FROM users WHERE user_id = ?", (uid,))
        await db.commit()
    return HTMLResponse("<script>alert('کاربر حذف شد'); window.location.href='/';</script>")

@app.get("/web/backup/download")
async def web_download():
    return FileResponse("zarvpn_web.db", filename="zarvpn_backup.db")

@app.post("/web/backup/restore")
async def web_restore(file: UploadFile = File(...)):
    with open("zarvpn_web.db", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return HTMLResponse("<script>alert('دیتابیس سیستم با موفقیت بازیابی شد. ربات را ری‌استارت کنید.'); window.location.href='/';</script>")

# --- روت مینی‌اپ اختصاصی کاربران (Telegram Mini App UI) ---
@app.get("/miniapp", response_class=HTMLResponse)
async def telegram_mini_app(user_id: int):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as c:
            row = await c.fetchone()
            balance = row[0] if row else 0
    return f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZarVpn MiniApp</title>
    <style>
        body {{ font-family: sans-serif; background: #000; color: #fff; text-align: center; padding: 20px; }}
        .card {{ background: #111; padding: 20px; border-radius: 15px; margin: 15px 0; border: 1px solid #222; }}
        .btn {{ display: block; width: 100%; padding: 12px; background: #007bff; color: white; border-radius: 10px; text-decoration: none; font-weight: bold; margin-top: 10px; }}
    </style></head>
    <body>
        <h3>📱 خوش آمدید به مینی‌اپ تجاری ZarVpn</h3>
        <div class="card">
            <h4>💰 موجودی کیف پول شما:</h4>
            <h2 style="color:#28a745;">{balance:,} تومان</h2>
        </div>
        <div class="card">
            <a href="#" class="btn">🛍️ خرید سریع اشتراک کانکشن</a>
            <a href="#" class="btn" style="background:#6c757d;">🛠️ مدیریت سرویس‌های من</a>
        </div>
    </body></html>
    """
