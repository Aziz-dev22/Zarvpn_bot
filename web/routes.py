cat << 'EOF' > web/routes.py
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.future import select
from core.database import AsyncSessionLocal
from database.models import User, InboundPanel, Gateway, Package

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="web/templates")

@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    async with AsyncSessionLocal() as db:
        users_count = await db.execute(select(User))
        panels_count = await db.execute(select(InboundPanel))
        packages_count = await db.execute(select(Package))
        
        context = {
            "request": request,
            "total_users": len(users_count.scalars().all()),
            "total_panels": len(panels_count.scalars().all()),
            "total_packages": len(packages_count.scalars().all())
        }
        # اصلاح بزرگ: استفاده از context= برای سازگاری کامل
        return templates.TemplateResponse(request=request, name="index.html", context=context)

@router.get("/panels", response_class=HTMLResponse)
async def show_panels(request: Request):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(InboundPanel))
        panels = result.scalars().all()
        return templates.TemplateResponse(
            request=request, 
            name="panels.html", 
            context={"request": request, "panels": panels}
        )

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
            name=name, panel_type=panel_type, api_url=api_url, 
            username=username, password=password, is_active=True
        )
        db.add(new_panel)
        await db.commit()
    return RedirectResponse(url="/admin/panels", status_code=303)

@router.get("/gateways", response_class=HTMLResponse)
async def show_gateways(request: Request):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Gateway))
        gateways = result.scalars().all()
        return templates.TemplateResponse(
            request=request, 
            name="gateways.html", 
            context={"request": request, "gateways": gateways}
        )
EOF
