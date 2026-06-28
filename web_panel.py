import uvicorn
import jwt
from fastapi import FastAPI, Depends, HTTPException, Form, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from core.config import settings
from core.database import get_db_connection
from panels.sanaei import SanaeiPanel
from templates.admin import HTML_TEMPLATE

app = FastAPI(title="ZarVPN Web Panel")

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
        raise HTTPException(status_code=403, detail="توکن ورود نامعتبر یا منقضی شده است.")

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
