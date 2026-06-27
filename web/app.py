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
        async with db.execute("SELECT * FROM plans") as c: plans = await c.fetchall()
        async with db.execute("SELECT * FROM server_settings WHERE panel_type='xui'") as c: xui_server = await c.fetchone() or ("xui", "", "", "")
        async with db.execute("SELECT * FROM server_settings WHERE panel_type='marzban'") as c: marzban_server = await c.fetchone() or ("marzban", "", "", "")
        async with db.execute("SELECT value FROM settings WHERE key='swapwallet_api'") as c: row = await c.fetchone(); swap_api = row[0] if row else ""
        async with db.execute("SELECT value FROM settings WHERE key='swapwallet_merchant'") as c: row = await c.fetchone(); swap_merchant = row[0] if row else ""
        async with db.execute("SELECT value FROM settings WHERE key='connectix_token'") as c: row = await c.fetchone(); cx_token = row[0] if row else ""
        async with db.execute("SELECT value FROM settings WHERE key='connectix_endpoint'") as c: row = await c.fetchone(); cx_endpoint = row[0] if row else "https://seller-api.connectix.vip/external/v1"
        async with db.execute("SELECT value FROM settings WHERE key='card_number'") as c: row = await c.fetchone(); card_num = row[0] if row else ""
        async with db.execute("SELECT value FROM settings WHERE key='crypto_wallet'") as c: row = await c.fetchone(); crypto_w = row[0] if row else ""
        async with db.execute("SELECT value FROM settings WHERE key='channel_id'") as c: row = await c.fetchone(); ch_id = row[0] if row else ""

    html_content = f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>تنظیمات زیرساخت ZarVpn</title>
        <style>
            body {{ font-family: Tahoma; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
            .container {{ max-width: 1100px; margin: 0 auto; }}
            .section {{ background: #1e293b; padding: 25px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #334155; }}
            input, select, button {{ padding: 10px; margin: 5px; border-radius: 8px; border: 1px solid #475569; background: #334155; color: white; }}
            button {{ background: #2563eb; cursor: pointer; border: none; font-weight: bold; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th, td {{ padding: 12px; text-align: right; border-bottom: 1px solid #334155; }}
            th {{ background: #334155; }}
            .btn-danger {{ background: #dc2626; }}
            .btn-success {{ background: #16a34a; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="section" style="text-align: center; background: linear-gradient(135deg, #1e3a8a, #2563eb);">
                <h2>⚙️ پنل تنظیمات زیرساخت و توکن‌های ربات ZarVpn</h2>
                <p>تنظیمات فنی سرورها؛ بخش کاربران و سوئیچ تست به داخل ربات تلگرام منتقل شد.</p>
            </div>

            <div class="section">
                <h3>📢 تنظیم کانال عضویت اجباری</h3>
                <form action="/settings/update-channel" method="post">
                    <input type="text" name="channel_id" placeholder="آیدی کانال با @ (مثال: @ZarVpn)" value="{ch_id}" style="width: 50%;">
                    <button type="submit" class="btn-success">ذخیره کانال</button>
                </form>
            </div>

            <div class="section">
                <h3>💳 تنظیمات کارت و ولت (واریز مستقیم)</h3>
                <form action="/settings/update-payments" method="post">
                    <input type="text" name="card" placeholder="شماره کارت ادمین" value="{card_num}" style="width: 45%;">
                    <input type="text" name="crypto" placeholder="آدرس ولت تتر TRC20" value="{crypto_w}" style="width: 45%;">
                    <button type="submit">ذخیره اطلاعات</button>
                </form>
            </div>

            <div class="section">
                <h3>🪙 تنظیمات صرافی ایرانی Swap Wallet</h3>
                <form action="/settings/update-swapwallet" method="post">
                    <input type="text" name="api_key" placeholder="کلید Token صرافی" value="{swap_api}" style="width: 45%;">
                    <input type="text" name="merchant_id" placeholder="Merchant ID" value="{swap_merchant}" style="width: 45%;">
                    <button type="submit">ذخیره درگاه</button>
                </form>
            </div>

            <div class="section">
                <h3>🔮 تنظیمات نمایندگی Connectix</h3>
                <form action="/settings/update-connectix" method="post">
                    <input type="text" name="token" placeholder="توکن API" value="{cx_token}" style="width: 45%;">
                    <input type="text" name="endpoint" value="{cx_endpoint}" style="width: 45%;">
                    <button type="submit">ذخیره نمایندگی</button>
                </form>
            </div>

            <div class="section">
                <h3>🚀 تعریف پلن‌های فروش ربات</h3>
                <form action="/plans/add" method="post">
                    <input type="text" name="name" placeholder="نام پلن" required>
                    <input type="number" name="size" placeholder="حجم (GB)" required>
                    <input type="number" name="days" placeholder="روز" required>
                    <input type="number" name="price" placeholder="قیمت (تومان)" required>
                    <select name="panel_type">
                        <option value="connectix">نمایندگی Connectix</option>
                        <option value="xui">X-UI سنایی</option>
                        <option value="marzban">مرزبان</option>
                    </select>
                    <button type="submit" class="btn-success">افزودن پلن</button>
                </form>
                <table>
                    <thead><tr><th>نام پلن</th><th>حجم</th><th>روز</th><th>قیمت</th><th>نوع پنل</th><th>عملیات</th></tr></thead>
                    <tbody>
    """
    for p in plans:
        html_content += f"<tr><td>{p[1]}</td><td>{p[2]} GB</td><td>{p[3]} روز</td><td>{p[4]:,} تومان</td><td>{p[5].upper()}</td><td><a href='/plans/delete/{p[0]}'><button class='btn-danger'>حذف</button></a></td></tr>"
    html_content += """</tbody></table></div></div></body></html>"""
    return html_content

@app.post("/settings/update-channel")
async def update_channel(channel_id: str = Form(...)):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("UPDATE settings SET value=? WHERE key='channel_id'", (channel_id,))
        await db.commit()
    return HTMLResponse("<script>alert('کانال عضویت اجباری بروزرسانی شد'); window.location.href='/';</script>")

@app.post("/settings/update-payments")
async def update_payments(card: str = Form(...), crypto: str = Form(...)):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("UPDATE settings SET value=? WHERE key='card_number'", (card,))
        await db.execute("UPDATE settings SET value=? WHERE key='crypto_wallet'", (crypto,))
        await db.commit()
    return HTMLResponse("<script>alert('اطلاعات پرداخت مستقیم ثبت شد'); window.location.href='/';</script>")

@app.post("/settings/update-connectix")
async def update_connectix(token: str = Form(...), endpoint: str = Form(...)):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("UPDATE settings SET value=? WHERE key='connectix_token'", (token,))
        await db.execute("UPDATE settings SET value=? WHERE key='connectix_endpoint'", (endpoint,))
        await db.commit()
    return HTMLResponse("<script>alert('تنظیمات نمایندگی ذخیره شد'); window.location.href='/';</script>")

@app.post("/settings/update-swapwallet")
async def update_swapwallet(api_key: str = Form(...), merchant_id: str = Form(...)):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("UPDATE settings SET value=? WHERE key='swapwallet_api'", (api_key,))
        await db.execute("UPDATE settings SET value=? WHERE key='swapwallet_merchant'", (merchant_id,))
        await db.commit()
    return HTMLResponse("<script>alert('تنظیمات درگاه ذخیره شد'); window.location.href='/';</script>")

@app.post("/plans/add")
async def add_plan(name: str = Form(...), size: int = Form(...), days: int = Form(...), price: int = Form(...), panel_type: str = Form(...)):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("INSERT INTO plans (name, size_gb, days, price, panel_type) VALUES (?, ?, ?, ?, ?)", (name, size, days, price, panel_type))
        await db.commit()
    return HTMLResponse("<script>alert('پلن اضافه شد'); window.location.href='/';</script>")

@app.get("/plans/delete/{plan_id}")
async def delete_plan(plan_id: int):
    async with aiosqlite.connect("zarvpn_web.db") as db:
        await db.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
        await db.commit()
    return HTMLResponse("<script>alert('پلن حذف شد'); window.location.href='/';</script>")
