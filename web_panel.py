import uvicorn
import jwt
import datetime
from fastapi import FastAPI, Depends, HTTPException, Form, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from core.config import settings
from core.database import get_db_connection
from panels.sanaei import SanaeiPanel
from templates.admin import HTML_TEMPLATE

app = FastAPI(title="ZarVPN Web Panel")

# قالب شیک صفحه لاگین نئومورفیسم در صورت ورود مستقیم
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ورود به ZARVPN</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/vazirmatn@3.3.0/Vazirmatn-font-face.css">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: Vazirmatn, sans-serif; }}
        body {{ background-color: #e0e8f6; display: flex; justify-content: center; align-items: center; height: 100vh; padding: 20px; }}
        .login-card {{ background: #e0e8f6; border-radius: 24px; box-shadow: 9px 9px 16px #bec8d6, -9px -9px 16px #ffffff; padding: 35px; width: 100%; max-width: 400px; text-align: center; }}
        .title {{ font-size: 22px; font-weight: bold; color: #1a2332; margin-bottom: 25px; }}
        input {{ width: 100%; padding: 12px 15px; border: none; background: #e0e8f6; border-radius: 12px; box-shadow: inset 3px 3px 6px #bec8d6, inset -3px -3px 6px #ffffff; margin-bottom: 20px; outline: none; text-align: center; }}
        button {{ width: 100%; padding: 14px; border: none; background: #e0e8f6; color: #2b6cb0; font-weight: bold; border-radius: 14px; box-shadow: 5px 5px 10px #bec8d6, -5px -5px 10px #ffffff; cursor: pointer; }}
        button:active {{ box-shadow: inset 3px 3px 6px #bec8d6, inset -3px -3px 6px #ffffff; }}
        .error {{ color: #e53e3e; margin-bottom: 15px; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="login-card">
        <div class="title">🔐 ورود به پنل مدیریت زار وی‌پی‌ان</div>
        {error_html}
        <form action="/login" method="post">
            <input type="text" name="username" placeholder="نام کاربری پنل وب" required>
            <input type="password" name="password" placeholder="کلمه عبور پنل وب" required>
            <button type="submit">ورود به حساب</button>
        </form>
    </div>
</body>
</html>
"""

@app.get("/")
async def root(request: Request):
    # اگر از قبل لاگین بود مستقیم برود داشبورد، وگرنه فرم لاگین
    token = request.cookies.get("admin_session")
    if token:
        try:
            jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            return RedirectResponse(url="/admin/dashboard")
        except Exception:
            pass
    return HTMLResponse(LOGIN_TEMPLATE.format(error_html=""))

@app.post("/login")
async def login_submit(username: str = Form(...), password: str = Form(...)):
    if username == settings.WEB_USERNAME and password == settings.WEB_PASSWORD:
        token = jwt.encode(
            {"admin_id": 0, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
            settings.SECRET_KEY, algorithm="HS256"
        )
        response = RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="admin_session", value=token, httponly=True)
        return response
    
    error_msg = "<div class='error'>❌ نام کاربری یا کلمه عبور اشتباه است.</div>"
    return HTMLResponse(LOGIN_TEMPLATE.format(error_html=error_msg))

def get_current_admin(request: Request):
    token = request.cookies.get("admin_session")
    if not token:
        raise HTTPException(status_code=401, detail="احراز هویت انجام نشده است.")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="جلسه کاری شما منقضی شده است.")

@app.get("/login/token")
async def login_with_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        response = RedirectResponse(url="/admin/dashboard")
        response.set_cookie(key="admin_session", value=token, httponly=True)
        return response
    except Exception:
        return RedirectResponse(url="/")

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def dashboard(payload: dict = Depends(get_current_admin)):
    conn = get_db_connection()
    users_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    servers = conn.execute("SELECT * FROM servers").fetchall()
    packages = conn.execute("SELECT * FROM packages").fetchall()
    
    servers_html = ""
    for s in servers:
        servers_html += f'<div class="item-row"><span>🖥️ {s["name"]} ({s["url"]})</span><a href="/admin/del-server/{s["id"]}"><button class="btn-danger" style="width:auto; padding:5px 10px; border-radius:8px;">حذف</button></a></div>'
        
    packages_html = ""
    for p in packages:
        packages_html += f'<div class="item-row"><span>📦 {p["name"]} - {p["price"]} تومان</span><a href="/admin/del-package/{p["id"]}"><button class="btn-danger" style="width:auto; padding:5px 10px; border-radius:8px;">حذف</button></a></div>'
        
    conn.close()
    
    return HTML_TEMPLATE.format(
        total_users=users_count, total_servers=len(servers),
        servers_html=servers_html, packages_html=packages_html
    )

@app.post("/admin/add-server")
async def add_server(name: str = Form(...), url: str = Form(...), username: str = Form(...), password: str = Form(...), payload: dict = Depends(get_current_admin)):
    panel = SanaeiPanel(url, username, password)
    is_valid = await panel.login()
    await panel.close()
    
    if not is_valid:
        return HTMLResponse("<h3>❌ خطا: مشخصات ورود اشتباه است یا پنل ثنایی پاسخ نداد! آدرس و پورت را چک کنید.</h3><br><a href='/admin/dashboard'>بازگشت به پنل</a>")
        
    conn = get_db_connection()
    conn.execute("INSERT INTO servers (name, url, username, password) VALUES (?, ?, ?, ?)", (name, url, username, password))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/admin/add-package")
async def add_package(name: str = Form(...), size_gb: int = Form(...), days: int = Form(...), price: int = Form(...), payload: dict = Depends(get_current_admin)):
    conn = get_db_connection()
    conn.execute("INSERT INTO packages (name, size_gb, days, price) VALUES (?, ?, ?, ?)", (name, size_gb, days, price))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/admin/del-server/{server_id}")
async def del_server(server_id: int, payload: dict = Depends(get_current_admin)):
    conn = get_db_connection()
    conn.execute("DELETE FROM servers WHERE id = ?", (server_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/admin/dashboard")

@app.get("/admin/del-package/{package_id}")
async def del_package(package_id: int, payload: dict = Depends(get_current_admin)):
    conn = get_db_connection()
    conn.execute("DELETE FROM packages WHERE id = ?", (package_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/admin/dashboard")
