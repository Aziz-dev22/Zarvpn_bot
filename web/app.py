from fastapi import FastAPI, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
import aiosqlite
import shutil
import os
from panels.manager import MultiPanelManager

app = FastAPI()
panel_manager = MultiPanelManager()

@app.get("/", response_class=HTMLResponse)
async def admin_dashboard():
    async with aiosqlite.connect("zarvpn_web.db") as db:
        async with db.execute("SELECT * FROM settings") as c: settings = dict(await c.fetchall())
        async with db.execute("SELECT user_id, username, balance FROM users") as c: users = await c.fetchall()
        async with db.execute("SELECT * FROM server_settings") as c: servers = await c.fetchall()

    user_rows = "".join([f"<tr><td>{u[0]}</td><td>{u[1]}</td><td>{u[2]:,} تومان</td><td><a href='/web/user-details/{u[0]}'><button>👁️ مدیریت کاربر</button></a></td></tr>" for u in users])
    server_rows = "".join([f"<tr><td>{s[0].upper()}</td><td>{s[1]}</td><td>{s[2]}</td><td><a href='/web/delete-panel/{s[0]}'><button class='btn-danger'>قطع اتصال</button></a></td></tr>" for s in servers])

    return f"""
    <html lang="fa" dir="rtl"><head><meta charset="UTF-8"><title>مینی‌اپ مدیریت وب ZarVpn</title>
    <style>body{{font-family:Tahoma; background:#0f172a; color:#fff; padding:20px;}} .card{{background:#1e293b; padding:15px; border-radius:8px; margin-bottom:15px; border:1px solid #334155;}} button{{background:#2563eb; color:white; border:none; padding:8px 12px; border-radius:5px; cursor:pointer; font-weight:bold;}} input, select{{padding:7px; background:#334155; color:white; border:1px solid #475569; margin:4px; border-radius:5px;}} .btn-danger{{background:#dc2626;}}</style></head>
    <body>
        <h2>🌐 ابر پنل مدیریت مینی‌اپ و درگاه‌های صرافی ZarVpn</h2>
        
        <div class="card">
            <h3>🔌 دکمه‌های جداگانه اتصال به پنل‌ها با تایید هویت (بند ۱)</h3>
            <form action="/web/connect-server" method="post">
                <select name="panel_type">
                    <option value="connectix">نمایندگی کانکتیکس (Connectix)</option>
                    <option value="xui">پنل سنایی (Sanaei X-UI)</option>
                    <option value="marzban">پنل مرزبان (Marzban)</option>
                </select>
                <input type="text" name="url" placeholder="آدرس سرور (URL)" required style="width:250px;">
                <input type="text" name="user" placeholder="نام کاربری / توکن" required>
                <input type="password" name="passw" placeholder="رمز عبور">
                <button type="submit">⚡ تست اتصال و ذخیره</button>
            </form>
            <table width="100%"><tr><th>نوع پنل</th><th>آدرس</th><th>یوزرنیم</th><th>عملیات</th></tr>{server_rows}</table>
        </div>

        <div class="card">
            <h3>💳 فعال و غیرفعال‌سازی روش‌های مالی و درگاه صرافی‌ها (بند ۳ و ۵)</h3>
            <form action="/web/save-gateways" method="post">
                <p>💳 شماره کارت ادمین: <input type="text" name="card_number" value="{settings.get('card_number')}"> 
                وضعیت: <select name="card_status"><option value="on" {'selected' if settings.get('card_status')=='on' else ''}>فعال</option><option value="off" {'selected' if settings.get('card_status')=='off' else ''}>غیرفعال</option></select></p>
                
                <p>⚡ ولت تتر (TRC20): <input type="text" name="crypto_wallet" value="{settings.get('crypto_wallet')}"> 
                وضعیت: <select name="crypto_status"><option value="on" {'selected' if settings.get('crypto_status')=='on' else ''}>فعال</option><option value="off" {'selected' if settings.get('crypto_status')=='off' else ''}>غیرفعال</option></select></p>
                
                <p>🪙 مرچنت سواپ‌ولت: <input type="text" name="swap_merchant" value="{settings.get('swapwallet_merchant')}"> 
                وضعیت: <select name="swap_status"><option value="on" {'selected' if settings.get('swapwallet_status')=='on' else ''}>فعال</option><option value="off" {'selected' if settings.get('swapwallet_status')=='off' else ''}>غیرفعال</option></select></p>
                
                <p>🔗 توکن API صرافی نوبیتکس: <input type="text" name="nobitex_token" value="{settings.get('nobitex_token')}"> 
                وضعیت: <select name="nobitex_status"><option value="on" {'selected' if settings.get('nobitex_status')=='on' else ''}>فعال</option><option value="off" {'selected' if settings.get('nobitex_status')=='off' else ''}>غیرفعال</option></select></p>
                <button type="submit" style="background:#16a34a;">💾 ذخیره تغییرات درگاه‌ها</button>
            </form>
        </div>

        <div class="card">
            <h3>👥 مدیریت و شارژ کاربران سیستم (بند ۲)</h3>
            <table width="100%"><tr><th>آیدی عددی</th><th>یوزرنیم</th><th>موجودی</th><th>عملیات</th></tr>{user_rows}</table>
        </div>
    </body></html>
    """

@app.post("/web/connect-server")
async def web_connect_server(panel_type: str = Form(...), url: str = Form(...), user: str = Form(...), passw: str = Form("")):
    success = await panel_manager.verify_and_connect(panel_type, url, user, passw)
    if not success:
        return HTMLResponse("<script>alert('❌ مشخصات اشتباه است! اطلاعات اتصال تایید نشد.'); window.location.href='/';</script>")
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("INSERT OR REPLACE INTO server_settings (panel_type, url, username, password) VALUES (?, ?, ?, ?)", (panel_type, url, user, passw))
        await db.commit()
    return HTMLResponse("<script>alert('✅ شما با موفقیت وارد شدید و پنل متصل شد.'); window.location.href='/';</script>")

@app.post("/web/save-gateways")
async def web_save_gateways(card_number: str = Form(...), card_status: str = Form(...), crypto_wallet: str = Form(...), crypto_status: str = Form(...), swap_merchant: str = Form(...), swap_status: str = Form(...), nobitex_token: str = Form(...), nobitex_status: str = Form(...)):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        updates = [('card_number', card_number), ('card_status', card_status), ('crypto_wallet', crypto_wallet), ('crypto_status', crypto_status), ('swapwallet_merchant', swap_merchant), ('swapwallet_status', swap_status), ('nobitex_token', nobitex_token), ('nobitex_status', nobitex_status)]
        for k, v in updates: await db.execute("UPDATE settings SET value=? WHERE key=?", (v, k))
        await db.commit()
    return HTMLResponse("<script>alert('تغییرات درگاه‌ها اعمال شد'); window.location.href='/';</script>")

@app.get("/web/user-details/{uid}", response_class=HTMLResponse)
async def web_user_details(uid: int):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        async with db.execute("SELECT username, balance FROM users WHERE user_id=?", (uid,)) as c: user = await c.fetchone()
        async with db.execute("SELECT id, plan_name, sub_link FROM orders WHERE user_id=?", (uid,)) as c: services = await c.fetchall()
    
    srv_html = "".join([f"<div style='background:#334155; padding:10px; margin-top:5px; border-radius:5px;'><p>📦 <b>{s[1]}</b> (کد: {s[0]})</p><p>🔗 لینک کانفیگ: <input type='text' id='l_{s[0]}' value='{s[2]}' style='width:60%;'> <button onclick=\"window.location.href='/web/change-link/{s[0]}?uid={uid}&link='+document.getElementById('l_{s[0]}').value\">تغییر</button> <a href='/web/del-srv/{s[0]}?uid={uid}'><button class='btn-danger'>حذف کامل سرویس</button></a></p></div>" for s in services])
    
    return f"""
    <html lang="fa" dir="rtl"><head><meta charset="UTF-8"><title>مدیریت {uid}</title></head>
    <body style="font-family:Tahoma; background:#0f172a; color:#fff; padding:20px;">
        <h2>👤 مدیریت کاربر: {user[0]} ({uid})</h2>
        <h3>💰 موجودی فعلی: {user[1]:,} تومان</h3>
        <form action="/web/modify-balance" method="post">
            <input type="hidden" name="uid" value="{uid}">
            <input type="number" name="amount" placeholder="مبلغ به تومان" required>
            <button type="submit" name="act" value="add" style="background:#16a34a; color:#fff; padding:7px;">➕ افزایش موجودی</button>
            <button type="submit" name="act" value="sub" style="background:#dc2626; color:#fff; padding:7px;">➖ کاهش موجودی</button>
        </form>
        <h3>🛠️ لایسنس‌ها و سرویس‌های کاربر (بند ۲):</h3>
        {srv_html if srv_html else '<p>سرویسی ندارد</p>'}
        <br><br><a href="/" style="color:#2563eb;">🔙 بازگشت</a>
    </body></html>
    """

@app.post("/web/modify-balance")
async def web_modify_balance(uid: int = Form(...), amount: int = Form(...), act: str = Form(...)):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        if act == "add": await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, uid))
        else: await db.execute("UPDATE users SET balance = max(0, balance - ?) WHERE user_id = ?", (amount, uid))
        await db.commit()
    return HTMLResponse(f"<script>alert('موجودی تغییر کرد'); window.location.href='/web/user-details/{uid}';</script>")

@app.get("/web/change-link/{oid}")
async def web_change_link(oid: int, uid: int, link: str):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("UPDATE orders SET sub_link=? WHERE id=?", (link, oid))
        await db.commit()
    return HTMLResponse(f"<script>alert('لینک تغییر کرد'); window.location.href='/web/user-details/{uid}';</script>")

@app.get("/web/del-srv/{oid}")
async def web_del_srv(oid: int, uid: int):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("DELETE FROM orders WHERE id=?", (oid,))
        await db.commit()
    return HTMLResponse(f"<script>alert('سرویس حذف شد'); window.location.href='/web/user-details/{uid}';</script>")

@app.get("/web/backup/download")
async def web_download(): return FileResponse("zarvpn_web.db")

# --- روت مینی‌اپ اختصاصی کاربران ---
@app.get("/miniapp", response_class=HTMLResponse)
async def telegram_mini_app(user_id: int):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as c:
            row = await c.fetchone(); balance = row[0] if row else 0
    return f"<html><body style='background:#000; color:#fff; font-family:sans-serif; text-align:center; padding:30px;'><h2>📱 مینی‌اپ هوشمند کاربری ZarVpn</h2><div style='background:#111; padding:20px; border-radius:10px;'><h3>💳 موجودی شما: {balance:,} تومان</h3></div></body></html>"

