"""
Rotas para Produto
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from zoneinfo import ZoneInfo

from app.database.db import get_db
from app.models.user import User
from app.routes.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/produto", response_class=HTMLResponse)
async def produto_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Página de Produto
    """
    if not current_user:
        return RedirectResponse(url="/login")
    
    now = datetime.now(ZoneInfo("America/Sao_Paulo"))
    
    return templates.TemplateResponse("produto.html", {
        "request": request,
        "user": current_user,
        "now": now
    })

