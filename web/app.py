from fastapi import FastAPI, Form, HTTPException, Response, Cookie, Query
from fastapi.responses import HTMLResponse, RedirectResponse
import aiosqlite
from panels.manager import MultiPanelManager
from core import config

app = FastAPI()
panel_manager = MultiPanelManager()

def get_neon_style():
    return """
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0b0f19; color: #f1f5f9; padding: 20px; direction: rtl; text-align: right; }
        .container { max-width: 800px; margin: 0 auto; }
        .login-box { max-width: 400px; margin: 100px auto; background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 30px; box-shadow: 0 4px 10px rgba(0,0,0,0.7); }
        h2, h3 { color: #38bdf8; text-shadow: 0 0 10px rgba(56, 189, 248, 0.3); border-bottom: 1px solid #1e293b; padding-bottom: 8px; margin-top: 25px; }
        .card { background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.5); }
        .flex-row { display: table; width: 100%; }
        .flex-cell { display: table-cell; padding: 5px; }
        input, select, textarea { background: #1f2937; color: #fff; border: 1px solid #374151; padding: 10px; border-radius: 8px; font-family: Tahoma; font-size: 13px; margin: 5px 0; width: 100%; box-sizing: border-box; }
        input:focus, select:focus { border-color: #38bdf8; outline: none; }
        button { background: #2563eb; color: #fff; border: none; padding: 10px 16px; border-radius: 8px; cursor:pointer; font-weight: bold; font-family: Tahoma; font-size: 13px; width: 100%; transition: all 0.2s; }
        button:hover { background: #1d4ed8; box-shadow: 0 0 12px rgba(37, 99, 235, 0.4); }
        .btn-success { background: #059669; }
        .btn-success:hover { background: #047857; }
        .btn-danger { background: #dc2626; }
        .btn-danger:hover { background: #b91c1c; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th { background: #1f2937; color: #94a3b8; font-size: 13px; text-align: right; padding: 12px; border-bottom: 2px solid #374151; }
        td { padding: 12px; border-bottom: 1px solid #1f2937; font-size: 14px; color: #e2e8f0; vertical-align: middle; }
        tr:hover { background: #1f2937; }
        .profile-header { display: flex; align-items: center; justify-content: space-between; background: linear-gradient(135deg, #1e1b4b, #111827); border: 1px solid #312e81; border-radius: 12px; padding: 15px 20px; margin-bottom: 20px; }
        .balance-badge { background: #065f46; color: #34d399; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 14px; border: 1px solid #047857; }
        .service-card { background: #1f2937; border: 1px solid #374151; border-radius: 10px; padding: 15px; margin-top: 10px; }
        a { text-decoration: none; }
    </style>
    """

@app.get("/login", response_class=HTMLResponse)
async def login_page(error: str = None):
    err_msg = f"<p style='color:#dc2626; font-size:13px;'>❌ {error}</p>" if error else ""
    return f"""
    <html lang="fa" dir="rtl"><head><meta charset="UTF-8"><title>ورود به پنل ZarVpn</title>{get_neon_style()}</head>
    <body>
        <div class="login-box">
            <h2 style="text-align:center; margin-top:0;">🔒 ورود به مدیریت ZarVpn</h2>
            {err_msg}
            <form action="/login" method="post">
                <label>نام کاربری:</label><input type="text" name="username" required>
                <label>رمز عبور:</label><input type="password" name="password" required>
                <button type="submit" class="btn-success" style="margin-top:15px;">📥 ورود به حساب</button>
            </form>
        </div>
    </body></html>
    """

@app.post("/login")
async def do_login(username: str = Form(...), password: str = Form(...)):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        async with db.execute("SELECT value FROM settings WHERE key='web_admin_user'") as c: u = (await c.fetchone())[0]
        async with db.execute("SELECT value FROM settings WHERE key='web_admin_pass'") as c: p = (await c.fetchone())[0]
    
    if username == u and password == p:
        res = RedirectResponse(url="/", status_code=303)
        res.set_cookie(key="admin_session", value="authenticated_zar_token", httponly=True)
        return res
    return RedirectResponse(url="/login?error=نام+کاربری+یا+رمز+عبور+اشتباه+است", status_code=303)

@app.get("/", response_class=HTMLResponse)
async def admin_dashboard(admin_session: str = Cookie(None)):
    if admin_session != "authenticated_zar_token":
        return RedirectResponse(url="/login", status_code=303)
        
    async with aiosqlite.connect("zarvpn_web.db") as db:
        async with db.execute("SELECT * FROM settings") as c: settings = dict(await c.fetchall())
        async with db.execute("SELECT user_id, username, balance FROM users") as c: users = await c.fetchall()
        async with db.execute("SELECT * FROM server_settings") as c: servers = await c.fetchall()
        async with db.execute("SELECT id, name, size_gb, days, price FROM plans") as c: plans = await c.fetchall()

    user_rows = "".join([f"<tr><td>{u[0]}</td><td>@{u[1]}</td><td>{u[2]:,} تومان</td><td><a href='/user-details/{u[0]}'><button style='padding:5px 10px;'>👁️ مدیریت</button></a></td></tr>" for u in users])
    server_rows = "".join([f"<tr><td>{s[0].upper()}</td><td>{s[1]}</td><td>{s[2]}</td><td><a href='/delete-panel/{s[0]}'><button class='btn-danger' style='padding:5px 10px;'>قطع اتصال</button></a></td></tr>" for s in servers])
    
    plan_rows = ""
    for p in plans:
        plan_rows += f"<tr><form action='/edit-plan/{p[0]}' method='post'><td><input type='text' name='name' value='{p[1]}' required></td><td><input type='number' name='size_gb' value='{p[2]}' style='width:60px;' required> GB</td><td><input type='number' name='days' value='{p[3]}' style='width:60px;' required> روز</td><td><input type='number' name='price' value='{p[4]}' style='width:90px;' required> تومان</td><td><button type='submit' class='btn-success' style='padding:5px 10px;'>ثبت</button> <a href='/delete-plan/{p[0]}'><button type='button' class='btn-danger' style='padding:5px 10px;'>حذف</button></a></td></form></tr>"

    return f"""
    <html lang="fa" dir="rtl"><head><meta charset="UTF-8"><title>ابر پنل مدیریت ZarVpn</title>{get_neon_style()}</head>
    <body>
        <div class="container">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h2>🌐 ابر پنل نئونی مدیریت سیستم ZarVpn</h2>
                <a href="/logout"><button class="btn-danger" style="width:auto; padding:8px 15px;">🚪 خروج</button></a>
            </div>
            
            <div class="card">
                <h3>🔒 تغییر مشخصات ورود به همین پنل وب</h3>
                <form action="/save-web-auth" method="post">
                    <div class="flex-row">
                        <div class="flex-cell"><input type="text" name="new_user" value="{settings.get('web_admin_user', 'admin')}" placeholder="نام کاربری جدید" required></div>
                        <div class="flex-cell"><input type="password" name="new_pass" value="{settings.get('web_admin_pass', '')}" placeholder="رمز عبور جدید" required></div>
                        <div class="flex-cell"><button type="submit" class="btn-success">تغییر اطلاعات ورود</button></div>
                    </div>
                </form>
            </div>

            <div class="card">
                <h3>🔌 اتصال به سرور (X-UI سنایی / مرزبان)</h3>
                <form action="/connect-server" method="post">
                    <div class="flex-row">
                        <div class="flex-cell"><select name="panel_type"><option value="xui">پنل سنایی (X-UI)</option><option value="marzban">پنل مرزبان (Marzban)</option></select></div>
                        <div class="flex-cell"><input type="text" name="url" placeholder="آدرس سرور به همراه پورت (http://آی‌پی:پورت)" required></div>
                    </div>
                    <div class="flex-row">
                        <div class="flex-cell"><input type="text" name="user" placeholder="نام کاربری پنل سرور" required></div>
                        <div class="flex-cell"><input type="password" name="passw" placeholder="رمز عبور پنل سرور" required></div>
                    </div>
                    <button type="submit" class="btn-success" style="margin-top:10px;">⚡ تست اتصال و ذخیره پنل</button>
                </form>
                <table width="100%"><tr><th>نوع پنل</th><th>آدرس سرور</th><th>یوزرنیم</th><th>عملیات</th></tr>{server_rows}</table>
            </div>

            <div class="card">
                <h3>📣 تنظیمات کانال عضویت اجباری ربات</h3>
                <form action="/save-channel" method="post">
                    <div class="flex-row">
                        <div class="flex-cell"><input type="text" name="channel_id" value="{settings.get('channel_id', '@your_channel')}" required></div>
                        <div class="flex-cell"><select name="sub_status"><option value="on" {'selected' if settings.get('sub_status')=='on' else ''}>🟢 فعال</option><option value="off" {'selected' if settings.get('sub_status')=='off' else ''}>🔴 غیرفعال</option></select></div>
                        <div class="flex-cell"><button type="submit" class="btn-success">ذخیره قفل کانال</button></div>
                    </div>
                </form>
            </div>

            <div class="card">
                <h3>🪙 پیکربندی و درگاه صرافی ایرانی و ولت‌ها</h3>
                <form action="/save-gateways" method="post">
                    <div class="flex-row">
                        <div class="flex-cell"><label>کلید API صرافی:</label><input type="text" name="swap_api" value="{settings.get('swapwallet_api', '')}"></div>
                        <div class="flex-cell"><label>مرچنت آیدی:</label><input type="text" name="swap_merchant" value="{settings.get('swapwallet_merchant', '')}"></div>
                    </div>
                    <div class="flex-row">
                        <div class="flex-cell"><label>وب‌سرویس صرافی:</label><input type="text" name="swap_endpoint" value="{settings.get('swapwallet_endpoint', 'https://swapwallet.ir/api')}"></div>
                        <div class="flex-cell"><label>وضعیت درگاه صرافی:</label><select name="swap_status"><option value="on" {'selected' if settings.get('swapwallet_status')=='on' else ''}>فعال</option><option value="off" {'selected' if settings.get('swapwallet_status')=='off' else ''}>غیرفعال</option></select></div>
                    </div>
                    <p>💳 کارت بانکی ادمین: <input type="text" name="card_number" value="{settings.get('card_number', '')}"></p>
                    <p>⚡ ولت‌های دیجیتال (ارزهای دلخواه ادمین): <textarea name="crypto_details" rows="2">{settings.get('crypto_details', '')}</textarea></p>
                    <button type="submit" class="btn-success">💾 ذخیره تغییرات مالی</button>
                </form>
            </div>
            
            <div class="card">
                <h3>🛍️ پلن‌های فروش ربات</h3>
                <form action="/add-plan" method="post">
                    <div class="flex-row">
                        <div class="flex-cell"><input type="text" name="name" placeholder="نام محصول" required></div>
                        <div class="flex-cell"><input type="number" name="size_gb" placeholder="حجم به گیگ" required></div>
                    </div>
                    <div class="flex-row">
                        <div class="flex-cell"><input type="number" name="days" placeholder="تعداد روز" required></div>
                        <div class="flex-cell"><input type="number" name="price" placeholder="قیمت به تومان" required></div>
                        <div class="flex-cell"><select name="panel_type"><option value="xui">سرور X-UI</option><option value="marzban">سرور مرزبان</option></select></div>
                    </div>
                    <button type="submit" class="btn-success" style="margin-top:10px;">🔵 افزودن محصول جدید</button>
                </form>
                <table width="100%"><tr><th>نام محصول</th><th>حجم</th><th>زمان</th><th>قیمت فروش</th><th>عملیات</th></tr>{plan_rows}</table>
            </div>

            <div class="card">
                <h3>👥 لیست کاربران سیستم</h3>
                <table width="100%"><tr><th>آیدی</th><th>یوزرنیم</th><th>موجودی</th><th>عملیات</th></tr>{user_rows}</table>
            </div>
        </div>
    </body></html>
    """

@app.post("/save-web-auth")
async def web_save_auth(new_user: str = Form(...), new_pass: str = Form(...)):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("UPDATE settings SET value=? WHERE key='web_admin_user'", (new_user,))
        await db.execute("UPDATE settings SET value=? WHERE key='web_admin_pass'", (new_pass,))
        await db.commit()
    return HTMLResponse("<script>alert('✅ مشخصات تغییر کرد. لطفا مجدد وارد شوید.'); window.location.href='/logout';</script>")

@app.get("/logout")
async def logout():
    res = RedirectResponse(url="/login", status_code=303)
    res.delete_cookie("admin_session")
    return res

@app.post("/save-channel")
async def web_save_channel(channel_id: str = Form(...), sub_status: str = Form(...)):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("UPDATE settings SET value=? WHERE key='channel_id'", (channel_id,))
        await db.execute("UPDATE settings SET value=? WHERE key='sub_status'", (sub_status,))
        await db.commit()
    return HTMLResponse("<script>alert('✅ قفل کانال آپدیت شد.'); window.location.href='/';</script>")

@app.post("/connect-server")
async def web_connect_server(panel_type: str = Form(...), url: str = Form(...), user: str = Form(...), passw: str = Form(...)):
    success = await panel_manager.verify_and_connect(panel_type, url, user, passw)
    if not success:
        return HTMLResponse("<script>alert('❌ مشخصات اشتباه است یا پنل سرور پاسخگو نیست!'); window.location.href='/';</script>")
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("INSERT OR REPLACE INTO server_settings (panel_type, url, username, password) VALUES (?, ?, ?, ?)", (panel_type, url, user, passw))
        await db.commit()
    return HTMLResponse("<script>alert('✅ سرور با موفقیت تایید و متصل شد.'); window.location.href='/';</script>")

@app.post("/save-gateways")
async def web_save_gateways(card_number: str = Form(...), crypto_details: str = Form(...), swap_api: str = Form(...), swap_merchant: str = Form(...), swap_endpoint: str = Form(...), swap_status: str = Form(...)):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        updates = [('card_number', card_number), ('crypto_details', crypto_details), ('swapwallet_api', swap_api), ('swapwallet_merchant', swap_merchant), ('swapwallet_endpoint', swap_endpoint), ('swapwallet_status', swap_status)]
        for k, v in updates: await db.execute("UPDATE settings SET value=? WHERE key=?", (v, k))
        await db.commit()
    return HTMLResponse("<script>alert('✅ تنظیمات مالی ذخیره شدند.'); window.location.href='/';</script>")

@app.post("/add-plan")
async def web_add_plan(name: str = Form(...), size_gb: int = Form(...), days: int = Form(...), price: int = Form(...), panel_type: str = Form(...)):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("INSERT INTO plans (name, size_gb, days, price, panel_type) VALUES (?, ?, ?, ?, ?)", (name, size_gb, days, price, panel_type))
        await db.commit()
    return HTMLResponse("<script>alert('✅ محصول جدید اضافه شد.'); window.location.href='/';</script>")

@app.post("/edit-plan/{pid}")
async def web_edit_plan(pid: int, name: str = Form(...), size_gb: int = Form(...), days: int = Form(...), price: int = Form(...)):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("UPDATE plans SET name=?, size_gb=?, days=?, price=? WHERE id=?", (name, size_gb, days, price, pid))
        await db.commit()
    return HTMLResponse("<script>alert('✅ تغییرات ذخیره شد.'); window.location.href='/';</script>")

@app.get("/delete-plan/{pid}")
async def web_delete_plan(pid: int):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("DELETE FROM plans WHERE id=?", (pid,))
        await db.commit()
    return HTMLResponse("<script>alert('❌ محصول حذف شد.'); window.location.href='/';</script>")

@app.get("/delete-panel/{ptype}")
async def web_delete_panel(ptype: str):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("DELETE FROM server_settings WHERE panel_type=?", (ptype,))
        await db.commit()
    return HTMLResponse("<script>alert('🔌 اتصال سرور قطع شد.'); window.location.href='/';</script>")

@app.get("/user-details/{uid}", response_class=HTMLResponse)
async def web_user_details(uid: int):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        async with db.execute("SELECT username, balance FROM users WHERE user_id=?", (uid,)) as c: user = await c.fetchone()
        async with db.execute("SELECT id, plan_name, sub_link FROM orders WHERE user_id=?", (uid,)) as c: services = await c.fetchall()
    srv_html = "".join([f"<div class='service-card'><p>📦 <b>{s[1]}</b></p><input type='text' id='l_{s[0]}' value='{s[2]}'><br><button onclick=\"window.location.href='/change-link/{s[0]}?uid={uid}&link='+encodeURIComponent(document.getElementById('l_{s[0]}').value)\" style='margin-top:5px;'>بروزرسانی لینک ساب</button> <a href='/del-srv/{s[0]}?uid={uid}'><button class='btn-danger' style='margin-top:5px;'>حذف سرویس</button></a></div>" for s in services])
    return f"<html lang='fa' dir='rtl'><head><meta charset='UTF-8'>{get_neon_style()}</head><body><div class='container'><h2>👤 پروفایل: @{user[0]}</h2><div class='profile-header'><b>آیدی کاربر: {uid}</b><div class='balance-badge'>{user[1]:,} تومان</div></div><div class='card'><h3>🛠️ شارژ / کسر موجودی</h3><form action='/modify-balance' method='post'><input type='hidden' name='uid' value='{uid}'><input type='number' name='amount' required placeholder='مبلغ به تومان'><br><br><button type='submit' name='act' value='add' class='btn-success'>➕ افزایش موجودی</button><button type='submit' name='act' value='sub' class='btn-danger' style='margin-top:5px;'>➖ کاهش موجودی</button></form></div><div class='card'><h3>📦 لایسنس‌های فعال</h3>{srv_html if srv_html else 'هیچ سرویسی ندارد'}</div><br><a href='/'>🔙 بازگشت به داشبورد</a></div></body></html>"

@app.post("/modify-balance")
async def web_modify_balance(uid: int = Form(...), amount: int = Form(...), act: str = Form(...)):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        if act == "add": await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, uid))
        else: await db.execute("UPDATE users SET balance = max(0, balance - ?) WHERE user_id = ?", (amount, uid))
        await db.commit()
    return HTMLResponse(f"<script>alert('✅ موجودی ویرایش شد.'); window.location.href='/user-details/{uid}';</script>")

@app.get("/change-link/{oid}")
async def web_change_link(oid: int, uid: int, link: str):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("UPDATE orders SET sub_link=? WHERE id=?", (link, oid))
        await db.commit()
    return HTMLResponse(f"<script>alert('✅ کانفیگ تغییر کرد'); window.location.href='/user-details/{uid}';</script>")

@app.get("/del-srv/{oid}")
async def web_del_srv(oid: int, uid: int):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("DELETE FROM orders WHERE id=?", (oid,))
        await db.commit()
    return HTMLResponse(f"<script>alert('❌ سرویس حذف شد'); window.location.href='/user-details/{uid}';</script>")
