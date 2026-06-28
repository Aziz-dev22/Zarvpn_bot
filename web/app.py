from fastapi import FastAPI, Form, HTTPException, Query
from fastapi.responses import HTMLResponse
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
async def admin_dashboard(admin_auth_id: str = Query(None)):
    is_root_admin = (admin_auth_id is None) or (str(admin_auth_id) == str(config.ADMIN_ID))
    auth_param = f"?admin_auth_id={admin_auth_id}" if admin_auth_id else ""
    
    async with aiosqlite.connect("zarvpn_web.db") as db:
        # ساخت جدول تنظیمات در صورت عدم وجود جهت جلوگیری از ارورهای اولیه
        await db.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
        # درج مقادیر پیش‌فرض قفل کانال در صورت نبودن
        await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('channel_id', '@your_channel')")
        await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('sub_status', 'off')")
        await db.commit()

        async with db.execute("SELECT * FROM settings") as c: settings = dict(await c.fetchall())
        async with db.execute("SELECT user_id, username, balance FROM users") as c: users = await c.fetchall()
        async with db.execute("SELECT * FROM server_settings") as c: servers = await c.fetchall()
        async with db.execute("SELECT id, name, size_gb, days, price FROM plans") as c: plans = await c.fetchall()

    user_rows = "".join([f"<tr><td>{u[0]}</td><td>@{u[1]}</td><td>{u[2]:,} تومان</td><td><a href='/user-details/{u[0]}{auth_param}'><button style='padding:5px 10px;'>👁️ مدیریت هوشمند</button></a></td></tr>" for u in users])
    server_rows = "".join([f"<tr><td>{s[0].upper()}</td><td>{s[1]}</td><td>{s[2]}</td><td><a href='/delete-panel/{s[0]}{auth_param}'><button class='btn-danger' style='padding:5px 10px;'>قطع اتصال</button></a></td></tr>" for s in servers])
    
    plan_rows = ""
    for p in plans:
        plan_rows += f"""
        <tr>
            <form action="/edit-plan/{p[0]}{auth_param}" method="post">
                <td><input type="text" name="name" value="{p[1]}" required></td>
                <td><input type="number" name="size_gb" value="{p[2]}" style="width:70px;" required> GB</td>
                <td><input type="number" name="days" value="{p[3]}" style="width:70px;" required> روز</td>
                <td><input type="number" name="price" value="{p[4]}" style="width:100px;" required> تومان</td>
                <td>
                    <div style="display: flex; gap: 5px;">
                        <button type="submit" class="btn-success" style="padding:5px 10px;">💾 ثبت</button>
                        <a href="/delete-plan/{p[0]}{auth_param}" style="width:100%;"><button type="button" class="btn-danger" style="padding:5px 10px;">❌ حذف</button></a>
                    </div>
                </td>
            </form>
        </tr>
        """

    admin_setup_section = ""
    if is_root_admin:
        admin_setup_section = f"""
        <div class="card">
            <h3>🔌 تنظیمات سرورها و اتصال به پنل‌ها (مخصوص مدیریت کل)</h3>
            <form action="/connect-server{auth_param}" method="post">
                <div class="flex-row">
                    <div class="flex-cell"><select name="panel_type"><option value="connectix">نمایندگی کانکتیکس (Connectix)</option><option value="xui">پنل سنایی (X-UI)</option><option value="marzban">پنل مرزبان (Marzban)</option></select></div>
                    <div class="flex-cell"><input type="text" name="url" placeholder="آدرس سرور (URL)" required></div>
                </div>
                <div class="flex-row">
                    <div class="flex-cell"><input type="text" name="user" placeholder="نام کاربری / توکن" required></div>
                    <div class="flex-cell"><input type="password" name="passw" placeholder="رمز عبور"></div>
                </div>
                <button type="submit" class="btn-success" style="margin-top:10px;">⚡ تست اتصال ایمن و فعالسازی</button>
            </form>
            <table width="100%"><tr><th>نوع پنل</th><th>آدرس سرور</th><th>یوزرنیم</th><th>عملیات</th></tr>{server_rows}</table>
        </div>

        <div class="card">
            <h3>📣 تنظیمات کانال عضویت اجباری ربات</h3>
            <form action="/save-channel{auth_param}" method="post">
                <div class="flex-row">
                    <div class="flex-cell">
                        <label>آیدی کانال تلگرام (حتما با @ شروع شود):</label>
                        <input type="text" name="channel_id" value="{settings.get('channel_id', '@your_channel')}" required>
                    </div>
                    <div class="flex-cell">
                        <label>وضعیت قفل عضویت:</label>
                        <select name="sub_status">
                            <option value="on" {'selected' if settings.get('sub_status')=='on' else ''}>🟢 فعال (قفل اجباری)</option>
                            <option value="off" {'selected' if settings.get('sub_status')=='off' else ''}>🔴 غیرفعال (بدون قفل)</option>
                        </select>
                    </div>
                </div>
                <p style="font-size:12px; color:#94a3b8; margin: 5px 0;">⚠️ نکته مهم: ربات شما حتماً باید در کانال فوق کارمند (Admin) با دسترسی دعوت کاربران باشد تا سیستم به درستی کار کند.</p>
                <button type="submit" class="btn-success">💾 ذخیره و اعمال قفل کانال</button>
            </form>
        </div>

        <div class="card">
            <h3>💳 فعال و غیرفعال‌سازی روش‌های مالی و درگاه صرافی‌ها</h3>
            <form action="/save-gateways{auth_param}" method="post">
                <p>💳 شماره کارت ادمین: <input type="text" name="card_number" value="{settings.get('card_number', '')}"> 
                وضعیت: <select name="card_status"><option value="on" {'selected' if settings.get('card_status')=='on' else ''}>فعال</option><option value="off" {'selected' if settings.get('card_status')=='off' else ''}>غیرفعال</option></select></p>
                <p>🪙 مرچنت سواپ‌ولت: <input type="text" name="swap_merchant" value="{settings.get('swapwallet_merchant', '')}"> 
                وضعیت: <select name="swap_status"><option value="on" {'selected' if settings.get('swapwallet_status')=='on' else ''}>فعال</option><option value="off" {'selected' if settings.get('swapwallet_status')=='off' else ''}>غیرفعال</option></select></p>
                <button type="submit">💾 ذخیره تغییرات مالی</button>
            </form>
        </div>
        """

    return f"""
    <html lang="fa" dir="rtl"><head><meta charset="UTF-8"><title>ابر پنل مدیریت مینی‌اپ ZarVpn</title>
    {get_neon_style()}</head>
    <body>
        <div class="container">
            <h2>🌐 ابر پنل نئونی مدیریت مینی‌اپ و کاربران ZarVpn</h2>
            {admin_setup_section}
            
            <div class="card">
                <h3>🛍️ مدیریت محصولات و پلن‌های فروش ربات</h3>
                <form action="/add-plan{auth_param}" method="post" style="background: #1f2937; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                    <b style="font-size: 14px; color: #38bdf8;">➕ افزودن محصول جدید به ربات:</b>
                    <div class="flex-row">
                        <div class="flex-cell"><input type="text" name="name" placeholder="نام پلن (مثلا: یکماهه کاربردی)" required></div>
                        <div class="flex-cell"><input type="number" name="size_gb" placeholder="حجم (گیگابایت)" required></div>
                    </div>
                    <div class="flex-row">
                        <div class="flex-cell"><input type="number" name="days" placeholder="زمان (روز)" required></div>
                        <div class="flex-cell"><input type="number" name="price" placeholder="قیمت (تومان)" required></div>
                    </div>
                    <div class="flex-row">
                        <div class="flex-cell">
                            <select name="panel_type">
                                <option value="connectix">لوکیشن کانکتیکس</option>
                                <option value="xui">سرور مستقیم X-UI</option>
                                <option value="marzban">سرور مستقیم مرزبان</option>
                            </select>
                        </div>
                        <div class="flex-cell"><button type="submit" class="btn-success">🔵 افزودن محصول جدید</button></div>
                    </div>
                </form>
                
                <table width="100%">
                    <tr><th>نام محصول</th><th>حجم</th><th>مدت زمان</th><th>قیمت فروش</th><th>عملیات تغییر</th></tr>
                    {plan_rows if plan_rows else '<tr><td colspan="5" style="text-align:center; color:#64748b;">هیچ محصولی تعریف نشده است.</td></tr>'}
                </table>
            </div>

            <div class="card">
                <h3>👥 لیست کاربران و نمایندگان سیستم</h3>
                <table width="100%"><tr><th>آیدی عددی</th><th>یوزرنیم تلگرام</th><th>موجودی حساب</th><th>عملیات</th></tr>{user_rows}</table>
            </div>
        </div>
    </body></html>
    """

# روت ذخیره تنظیمات کانال جوین اجباری
@app.post("/save-channel")
async def web_save_channel(admin_auth_id: str = Query(None), channel_id: str = Form(...), sub_status: str = Form(...)):
    auth_param = f"?admin_auth_id={admin_auth_id}" if admin_auth_id else ""
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('channel_id', ?)", (channel_id,))
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('sub_status', ?)", (sub_status,))
        await db.commit()
    return HTMLResponse(f"<script>alert('✅ تنظیمات قفل کانال با موفقیت ذخیره شد.'); window.location.href='/{auth_param}';</script>")

@app.post("/add-plan")
async def web_add_plan(admin_auth_id: str = Query(None), name: str = Form(...), size_gb: int = Form(...), days: int = Form(...), price: int = Form(...), panel_type: str = Form(...)):
    auth_param = f"?admin_auth_id={admin_auth_id}" if admin_auth_id else ""
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("INSERT INTO plans (name, size_gb, days, price, panel_type) VALUES (?, ?, ?, ?, ?)", (name, size_gb, days, price, panel_type))
        await db.commit()
    return HTMLResponse(f"<script>alert('✅ محصول جدید با موفقیت اضافه شد.'); window.location.href='/{auth_param}';</script>")

@app.post("/edit-plan/{pid}")
async def web_edit_plan(pid: int, admin_auth_id: str = Query(None), name: str = Form(...), size_gb: int = Form(...), days: int = Form(...), price: int = Form(...)):
    auth_param = f"?admin_auth_id={admin_auth_id}" if admin_auth_id else ""
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("UPDATE plans SET name=?, size_gb=?, days=?, price=? WHERE id=?", (name, size_gb, days, price, pid))
        await db.commit()
    return HTMLResponse(f"<script>alert('✅ تغییرات محصول با موفقیت ثبت شد.'); window.location.href='/{auth_param}';</script>")

@app.get("/delete-plan/{pid}")
async def web_delete_plan(pid: int, admin_auth_id: str = Query(None)):
    auth_param = f"?admin_auth_id={admin_auth_id}" if admin_auth_id else ""
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("DELETE FROM plans WHERE id=?", (pid,))
        await db.commit()
    return HTMLResponse(f"<script>alert('❌ محصول از لیست فروش ربات حذف شد.'); window.location.href='/{auth_param}';</script>")

@app.get("/user-details/{uid}", response_class=HTMLResponse)
async def web_user_details(uid: int, admin_auth_id: str = Query(None)):
    auth_param = f"?admin_auth_id={admin_auth_id}" if admin_auth_id else ""
    async with aiosqlite.connect("zarvpn_web.db") as db:
        async with db.execute("SELECT username, balance FROM users WHERE user_id=?", (uid,)) as c: user = await c.fetchone()
        async with db.execute("SELECT id, plan_name, sub_link FROM orders WHERE user_id=?", (uid,)) as c: services = await c.fetchall()
    
    if not user: raise HTTPException(status_code=404, detail="User not found")
    
    srv_html = "".join([f"""
    <div class="service-card">
        <p>📦 <b>نوع سرویس:</b> {s[1]} (کد محصول: {s[0]})</p>
        <p>🔗 <b>لینک اتصال مستقیم V2Ray:</b></p>
        <input type='text' id='l_{s[0]}' value='{s[2]}' style='margin-bottom:10px;'>
        <div class="flex-row">
            <div class="flex-cell"><button onclick="window.location.href='/change-link/{s[0]}?uid={uid}&admin_auth_id={admin_auth_id or ""}&link='+encodeURIComponent(document.getElementById('l_{s[0]}').value)">💾 بروزرسانی کانفیگ</button></div>
            <div class="flex-cell"><a href='/del-srv/{s[0]}?uid={uid}&admin_auth_id={admin_auth_id or ""}'><button class='btn-danger'>❌ حذف کامل لایسنس</button></a></div>
        </div>
    </div>
    """ for s in services])
    
    return f"""
    <html lang="fa" dir="rtl"><head><meta charset="UTF-8"><title>مدیریت کاربر {uid}</title>
    {get_neon_style()}</head>
    <body>
        <div class="container">
            <h2>👤 کارت پروفایل و مدیریت شیشه‌ای کاربر</h2>
            <div class="profile-header">
                <div class="profile-info">
                    <b>👤 کاربر: @{user[0]}</b>
                    <p>🆔 شناسه عددی حساب: <code>{uid}</code></p>
                </div>
                <div class="balance-badge">💰 {user[1]:,} تومان</div>
            </div>
            <div class="card">
                <h3>🛠️ عملیات تغییر سریع موجودی</h3>
                <form action="/modify-balance{auth_param}" method="post">
                    <input type="hidden" name="uid" value="{uid}">
                    <input type="number" name="amount" placeholder="مبلغ مورد نظر را به تومان وارد کنید..." required style="margin-bottom:15px;">
                    <div class="flex-row">
                        <div class="flex-cell"><button type="submit" name="act" value="add" class="btn-success">➕ افزایش و شارژ حساب</button></div>
                        <div class="flex-cell"><button type="submit" name="act" value="sub" class="btn-danger">➖ کسر موجودی کیف پول</button></div>
                    </div>
                </form>
            </div>
            <div class="card">
                <h3>📦 سرویس‌ها و اشتراک‌های فعال این کاربر</h3>
                {srv_html if srv_html else '<p style="color:#64748b; text-align:center; padding:20px;">هیچ سرویس فعالی برای این کاربر ثبت نشده است.</p>'}
            </div>
            <div style="text-align:center; margin-top:20px;"><a href='/{auth_param}' style="color:#38bdf8; font-size:14px;">🔙 بازگشت به لیست اصلی مدیریت</a></div>
        </div>
    </body></html>
    """

@app.post("/modify-balance")
async def web_modify_balance(admin_auth_id: str = Query(None), uid: int = Form(...), amount: int = Form(...), act: str = Form(...)):
    auth_param = f"?admin_auth_id={admin_auth_id}" if admin_auth_id else ""
    async with aiosqlite.connect("zarvpn_web.db") as db:
        if act == "add": await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, uid))
        else: await db.execute("UPDATE users SET balance = max(0, balance - ?) WHERE user_id = ?", (amount, uid))
        await db.commit()
    return HTMLResponse(f"<script>alert('✅ تغییرات موجودی با موفقیت اعمال شد.'); window.location.href='/user-details/{uid}{auth_param}';</script>")

@app.get("/change-link/{oid}")
async def web_change_link(oid: int, uid: int, link: str, admin_auth_id: str = Query(None)):
    auth_param = f"?admin_auth_id={admin_auth_id}" if admin_auth_id else ""
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("UPDATE orders SET sub_link=? WHERE id=?", (link, oid))
        await db.commit()
    return HTMLResponse(f"<script>alert('✅ کانفیگ اصلاح شد.'); window.location.href='/user-details/{uid}{auth_param}';</script>")

@app.get("/del-srv/{oid}")
async def web_del_srv(oid: int, uid: int, admin_auth_id: str = Query(None)):
    auth_param = f"?admin_auth_id={admin_auth_id}" if admin_auth_id else ""
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("DELETE FROM orders WHERE id=?", (oid,))
        await db.commit()
    return HTMLResponse(f"<script>alert('❌ سرویس حذف شد.'); window.location.href='/user-details/{uid}{auth_param}';</script>")

@app.post("/connect-server")
async def web_connect_server(admin_auth_id: str = Query(None), panel_type: str = Form(...), url: str = Form(...), user: str = Form(...), passw: str = Form("")):
    auth_param = f"?admin_auth_id={admin_auth_id}" if admin_auth_id else ""
    success = await panel_manager.verify_and_connect(panel_type, url, user, passw)
    if not success: return HTMLResponse(f"<script>alert('❌ خطا در تایید هویت سرور!'); window.location.href='/{auth_param}';</script>")
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("INSERT OR REPLACE INTO server_settings (panel_type, url, username, password) VALUES (?, ?, ?, ?)", (panel_type, url, user, passw))
        await db.commit()
    return HTMLResponse(f"<script>alert('✅ اتصال پنل تایید و ذخیره شد.'); window.location.href='/{auth_param}';</script>")

@app.post("/save-gateways")
async def web_save_gateways(admin_auth_id: str = Query(None), card_number: str = Form(...), card_status: str = Form(...), swap_merchant: str = Form(...), swap_status: str = Form(...)):
    auth_param = f"?admin_auth_id={admin_auth_id}" if admin_auth_id else ""
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("UPDATE settings SET value=? WHERE key='card_number'", (card_number,))
        await db.execute("UPDATE settings SET value=? WHERE key='card_status'", (card_status,))
        await db.execute("UPDATE settings SET value=? WHERE key='swapwallet_merchant'", (swap_merchant,))
        await db.execute("UPDATE settings SET value=? WHERE key='swapwallet_status'", (swap_status,))
        await db.commit()
    return HTMLResponse(f"<script>alert('✅ تنظیمات درگاه‌ها ذخیره شد.'); window.location.href='/{auth_param}';</script>")

@app.get("/miniapp", response_class=HTMLResponse)
async def telegram_mini_app(user_id: int):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        async with db.execute("SELECT username, balance FROM users WHERE user_id = ?", (user_id,)) as c: row = await c.fetchone()
    username = row[0] if row else "کاربر عزیز"
    balance = row[1] if row else 0
    return f"""
    <html lang="fa" dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>ZarVpn MiniApp</title>
    {get_neon_style()}</head>
    <body style="padding: 10px;">
        <div class="profile-header">
            <div class="profile-info">
                <b>🚀 خوش آمدید، @{username}</b>
                <p>شناسه کاربری شما: {user_id}</p>
            </div>
            <div class="balance-badge">{balance:,} تومان</div>
        </div>
        <div class="card" style="text-align:center;">
            <h3 style="color:#a855f7; text-shadow: 0 0 10px rgba(168,85,247,0.3);">💎 اشتراک‌های هوشمند صادر شده</h3>
            <p style="font-size:13px; color:#64748b;">جهت تمدید یا مشاهده حجم باقی‌مانده از دکمه‌های ربات استفاده کنید.</p>
        </div>
    </body></html>
    """
