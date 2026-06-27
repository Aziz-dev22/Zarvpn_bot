from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import aiosqlite

app = FastAPI(title="ZarVpn Advance Admin Dashboard")

@app.get("/", response_class=HTMLResponse)
async def admin_dashboard():
    async with aiosqlite.connect("zarvpn_web.db") as db:
        # دریافت آمار از دیتابیس واقعی ربات
        async with db.execute("SELECT COUNT(*), SUM(balance) FROM users") as c:
            u_info = await c.fetchone()
            total_users = u_info[0] or 0
            total_balance = u_info[1] or 0
            
        async with db.execute("SELECT COUNT(*) FROM orders") as c:
            total_orders = (await c.fetchone())[0] or 0
            
        async with db.execute("SELECT user_id, username, balance FROM users ORDER BY created_at DESC LIMIT 10") as c:
            latest_users = await c.fetchall()

    # طراحی پنل گرافیکی مدرن و راست‌چین
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>داشبورد مدیریت تجاری ZarVpn</title>
        <style>
            body {{ font-family: Tahoma, Arial; background-color: #f4f6f9; color: #333; margin: 0; padding: 20px; }}
            .header {{ background: #1e293b; color: white; padding: 20px; text-align: center; border-radius: 10px; margin-bottom: 20px; }}
            .stats-container {{ display: flex; gap: 20px; justify-content: space-around; margin-bottom: 30px; }}
            .card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 30%; text-align: center; }}
            .card h3 {{ margin: 0; color: #64748b; }}
            .card p {{ font-size: 24px; font-weight: bold; color: #0f172a; margin: 10px 0 0 0; }}
            .table-container {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ border-bottom: 1px solid #e2e8f0; padding: 12px; text-align: right; }}
            th {{ background-color: #f8fafc; color: #64748b; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>🌐 ابر پنل مدیریت تحت وب تجاری سیستم ZarVpn</h2>
            <p>سیستم مانیتورینگ آنلاین دیتابیس ربات تلگرام</p>
        </div>
        
        <div class="stats-container">
            <div class="card">
                <h3>👥 کل کاربران ربات</h3>
                <p>{total_users} نفر</p>
            </div>
            <div class="card">
                <h3>🛒 کانکشن‌های صادر شده</h3>
                <p>{total_orders} عدد</p>
            </div>
            <div class="card">
                <h3>💰 کل سرمایه کاربری (کیف پول)</h3>
                <p>{total_balance:,} تومان</p>
            </div>
        </div>

        <div class="table-container">
            <h3>👥 لیست آخرین کاربران ثبت شده در سیستم:</h3>
            <table>
                <thead>
                    <tr>
                        <th>آیدی عددی تلگرام</th>
                        <th>نام کاربری</th>
                        <th>موجودی کیف پول</th>
                    </tr>
                </thead>
                <tbody>
    """
    for user in latest_users:
        html_content += f"""
                    <tr>
                        <td>{user[0]}</td>
                        <td>@{user[1]}</td>
                        <td>{user[2]:,} تومان</td>
                    </tr>
        """
        
    html_content += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    return html_content
