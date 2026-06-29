# web/routes.py
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import AsyncSessionLocal
from database.models import User, InboundPanel, Gateway
from panels.manager import PanelManager

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="web/templates")

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    # محاسبه آمارها به صورت پویا از دیتابیس
    users_query = await db.execute(select(User))
    users = users_query.scalars().all()
    
    panels_query = await db.execute(select(InboundPanel))
    panels = panels_query.scalars().all()
    
    total_balance = sum(user.balance for user in users)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "total_users": len(users),
        "total_panels": len(panels),
        "total_balance": f"{total_balance:,.0f}"
    })

# --- مدیریت پنل‌های X-UI سنایی و مرزبان ---
@router.get("/panels", response_class=HTMLResponse)
async def list_panels(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InboundPanel))
    panels = result.scalars().all()
    return templates.TemplateResponse("panels.html", {"request": request, "panels": panels})

@router.post("/panels/add")
async def add_panel(
    name: str = Form(...),
    panel_type: str = Form(...),
    api_url: str = Form(...),
    username: str = Form(...),
    password: str = Form(...)
):
    async with AsyncSessionLocal() as db:
        new_panel = InboundPanel(
            name=name, panel_type=panel_type, api_url=api_url, username=username, password=password
        )
        # تست اتصال واقعی قبل از ذخیره نهایی
        is_connected = await PanelManager.test_connection(new_panel)
        if is_connected:
            db.add(new_panel)
            await db.commit()
    return RedirectResponse(url="/admin/panels", status_code=303)

@router.get("/panels/delete/{panel_id}")
async def delete_panel(panel_id: int):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(InboundPanel).where(InboundPanel.id == panel_id))
        panel = result.scalar_one_or_none()
        if panel:
            await db.delete(panel)
            await db.commit()
    return RedirectResponse(url="/admin/panels", status_code=303)

# --- مدیریت درگاه‌های پرداخت صرافی ایرانی ---
@router.get("/gateways", response_class=HTMLResponse)
async def list_gateways(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Gateway))
    gateways = result.scalars().all()
    return templates.TemplateResponse("gateways.html", {"request": request, "gateways": gateways})

@router.post("/gateways/add")
async def add_gateway(name: str = Form(...), api_key: str = Form(...), merchant_id: str = Form(None)):
    async with AsyncSessionLocal() as db:
        new_gw = Gateway(name=name, api_key=api_key, merchant_id=merchant_id)
        db.add(new_gw)
        await db.commit()
    return RedirectResponse(url="/admin/gateways", status_code=303)

