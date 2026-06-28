from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
import aiosqlite
from panels.manager import MultiPanelManager

app = FastAPI()
panel_manager = MultiPanelManager()

@app.get("/", response_class=HTMLResponse)
async def web_admin_portal():
    async with aiosqlite.connect("zarvpn_web.db") as db:
        async with db.execute("SELECT * FROM settings") as c: settings = dict(await c.fetchall())
        async with db.execute("SELECT user_id, username, balance FROM users") as c: users = await c.fetchall()
    
    user_rows = "".join([f"""
    <tr>
        <td>{u[0]}</td><td>{u[1]}</td><td>{u[2]:,} تومان</td>
        <td>
            <a href="/web/user-details/{u[0]}"><button>👁️ مدیریت کاربر</button></a>
        </td>
    </tr>""" for u in users])

    return f"""
    <html lang="fa" dir="rtl"><head><meta charset="UTF-8"><title>پنل مدیریت وب ZarVpn</title>
    <style>body{{font-family:Tahoma; background:#0f172a; color:#fff; padding:20px;}} .card{{background:#1e293b; padding:15px; border-radius:8px; margin-bottom:15px;}} button{{background:#2563eb; color:white; border:none; padding:8px 12px; border-radius:5px; cursor:pointer;}} input, select{{padding:6px; background:#334155; color:white; border:none; margin:4px;}}</style></head>
    <body>
        <h2>🌐 ابر پنل مدیریت مینی‌اپ و سرور ZarVpn</h2>
        
        <div class="card">
            <h3>💳 مدیریت روش‌های پرداخت و درگاه‌های صرافی (API)</h3>
            <form action="/web/save-gateways" method="post">
                <p>شماره کارت: <input type="text" name="card_number" value="{settings.get('card_number')}"> 
                وضعیت: <select name="card_status"><option value="on" {'selected' if settings.get('card_status')=='on' else ''}>فعال</option><option value="off" {'selected' if settings.get('card_status')=='off' else ''}>غیرفعال</option></select></p>
                
                <p>آدرس ولت تتر: <input type="text" name="crypto_wallet" value="{settings.get('crypto_wallet')}"> 
                وضعیت: <select name="crypto_status"><option value="on" {'selected' if settings.get('crypto_status')=='on' else ''}>فعال</option><option value="off" {'selected' if settings.get('crypto_status')=='off' else ''}>غیرفعال</option></select></p>
                
                <p>مرچنت سواپ‌ولت: <input type="text" name="swap_merchant" value="{settings.get('swapwallet_merchant')}"> 
                وضعیت: <select name="swap_status"><option value="on" {'selected' if settings.get('swapwallet_status')=='on' else ''}>فعال</option><option value="off" {'selected' if settings.get('swapwallet_status')=='off' else ''}>غیرفعال</option></select></p>
                
                <p>توکن صرافی نوبیتکس: <input type="text" name="nobitex_token" value="{settings.get('nobitex_token')}"> 
                وضعیت: <select name="nobitex_status"><option value="on" {'selected' if settings.get('nobitex_status')=='on' else ''}>فعال</option><option value="off" {'selected' if settings.get('nobitex_status')=='off' else ''}>غیرفعال</option></select></p>
                
                <button type="submit">💾 ذخیره تنظیمات مالی</button>
            </form>
        </div>

        <div class="card">
            <h3>🔌 دکمه‌های جداگانه اتصال به سرورها (بند ۱)</h3>
            <form action="/web/connect-server" method="post">
                <select name="panel_type">
                    <option value="connectix">نمایندگی کانکتیکس (Connectix)</option>
                    <option value="xui">پنل سنایی (Sanaei X-UI)</option>
                    <option value="marzban">پنل مرزبان (Marzban)</option>
                </select>
                <input type="text" name="url" placeholder="آدرس پنل (URL)" required>
                <input type="text" name="user" placeholder="نام کاربری / توکن ادمین" required>
                <input type="password" name="passw" placeholder="رمز عبور پنل">
                <button type="submit">⚡ تست اتصال و ذخیره پنل</button>
            </form>
        </div>

        <div class="card">
            <h3>👥 لیست کاربران</h3>
            <table width="100%" border="1" style="border-collapse:collapse;">
                <tr><th>آیدی عددی</th><th>یوزرنیم</th><th>موجودی</th><th>مدیریت</th></tr>
                {user_rows}
            </table>
        </div>
    </body></html>
    """

@app.post("/web/connect-server")
async def web_connect_server(panel_type: str = Form(...), url: str = Form(...), user: str = Form(...), passw: str = Form("")):
    # بند ۱: بررسی مشخصات ورود و اعلام وضعیت مشخصات اشتباه یا ورود موفق
    success = await panel_manager.verify_and_connect(panel_type, url, user, passw)
    if not success:
        return HTMLResponse("<script>alert('❌ مشخصات اشتباه است! اتصال برقرار نشد.'); window.location.href='/';</script>")
    
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("INSERT OR REPLACE INTO server_settings (panel_type, url, username, password) VALUES (?, ?, ?, ?)", (panel_type, url, user, passw))
        await db.commit()
    return HTMLResponse("<script>alert('✅ شما با موفقیت وارد شدید و پنل متصل شد.'); window.location.href='/';</script>")

@app.post("/web/save-gateways")
async def web_save_gateways(card_number: str = Form(...), card_status: str = Form(...), crypto_wallet: str = Form(...), crypto_status: str = Form(...), swap_merchant: str = Form(...), swap_status: str = Form(...), nobitex_token: str = Form(...), nobitex_status: str = Form(...)):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        updates = [('card_number', card_number), ('card_status', card_status), ('crypto_wallet', crypto_wallet), ('crypto_status', crypto_status), ('swapwallet_merchant', swap_merchant), ('swapwallet_status', swap_status), ('nobitex_token', nobitex_token), ('nobitex_status', nobitex_status)]
        for k, v in updates:
            await db.execute("UPDATE settings SET value=? WHERE key=?", (v, k))
        await db.commit()
    return HTMLResponse("<script>alert('تنظیمات مالی با موفقیت آپدیت شدند'); window.location.href='/';</script>")

# بند ۲: صفحه اختصاصی مینی‌آپ جزئیات کاربر برای مدیریت کامل ادمین
@app.get("/web/user-details/{uid}", response_class=HTMLResponse)
async def web_user_details(uid: int):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        async with db.execute("SELECT username, balance FROM users WHERE user_id=?", (uid,)) as c: user = await c.fetchone()
        async with db.execute("SELECT id, plan_name, sub_link, v2ray_username, panel_type FROM orders WHERE user_id=?", (uid,)) as c: services = await c.fetchall()
    
    if not user: return "کاربر یافت نشد"
    
    srv_rows = "".join([f"""
    <div style='background:#334155; padding:10px; margin-top:5px; border-radius:5px;'>
        <p>📦 <b>{s[1]}</b> ({s[4]}) | یوزرنیم پنل: <code>{s[3]}</code></p>
        <p>🔗 لینک ساب: <input type='text' id='link_{s[0]}' value='{s[2]}' style='width:60%;'> 
        <button onclick="window.location.href='/web/change-link/{s[0]}?new_link='+document.getElementById('link_{s[0]}').value">تغییر لینک</button>
        <a href='/web/delete-service/{s[0]}'><button style='background:#dc2626;'>حذف کامل سرویس</button></a></p>
    </div>""" for s in services])

    return f"""
    <html lang="fa" dir="rtl"><head><meta charset="UTF-8"><title>مدیریت کاربر {uid}</title></head>
    <body style="font-family:Tahoma; background:#0f172a; color:#fff; padding:20px;">
        <h2>👤 مدیریت کامل کاربر: {user[0]} ({uid})</h2>
        <h3>💰 موجودی فعلی: {user[1]:,} تومان</h3>
        
        <form action="/web/modify-balance" method="post">
            <input type="hidden" name="uid" value="{uid}">
            <input type="number" name="amount" placeholder="مقدار اعتبار به تومان" required>
            <button type="submit" name="action" value="add" style="background:#16a34a; color:white; padding:8px;">➕ افزایش موجودی</button>
            <button type="submit" name="action" value="sub" style="background:#dc2626; color:white; padding:8px;">➖ کاهش موجودی</button>
        </form>
        
        <hr style="margin:20px 0; border-color:#334155;">
        <h3>🛠️ سرویس‌ها و کانکشن‌های کاربر:</h3>
        {srv_rows if srv_rows else '<p>هیچ سرویس فعالی ندارد.</p>'}
        <br><br><a href="/" style="color:#2563eb;">🔙 بازگشت به لیست اصلی</a>
    </body></html>
    """

@app.post("/web/modify-balance")
async def web_modify_balance(uid: int = Form(...), amount: int = Form(...), action: str = Form(...)):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        if action == "add":
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, uid))
        else:
            await db.execute("UPDATE users SET balance = max(0, balance - ?) WHERE user_id = ?", (amount, uid))
        await db.commit()
    return HTMLResponse(f"<script>alert('تغییرات موجودی اعمال شد'); window.location.href='/web/user-details/{uid}';</script>")

@app.get("/web/change-link/{oid}")
async def web_change_link(oid: int, new_link: str):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("UPDATE orders SET sub_link=? WHERE id=?", (new_link, oid))
        await db.commit()
    return HTMLResponse("<script>alert('لینک کانکشن با موفقیت تغییر کرد'); window.location.href='/';</script>")

@app.get("/web/delete-service/{oid}")
async def web_delete_service(oid: int):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        async with db.execute("SELECT panel_type, v2ray_username FROM orders WHERE id=?", (oid,)) as c: row = await c.fetchone()
        if row: await panel_manager.delete_account(row[0], row[1])
        await db.execute("DELETE FROM orders WHERE id=?", (oid,))
        await db.commit()
    return HTMLResponse("<script>alert('سرویس با موفقیت حذف شد'); window.location.href='/';</script>")
