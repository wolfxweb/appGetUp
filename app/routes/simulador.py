"""
Rotas para o Simulador de Negócios
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.db import get_db
from app.models.user import User
from app.models.basic_data import BasicData
from app.routes.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/simulador", response_class=HTMLResponse)
async def simulador_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Página do Simulador de Negócios
    Permite ao usuário simular diferentes cenários financeiros
    """
    # Buscar dados básicos do usuário para popular o formulário
    basic_data_list = []
    if current_user:
        result = await db.execute(
            select(BasicData)
            .filter(BasicData.user_id == current_user.id)
            .order_by(BasicData.year.desc(), BasicData.month.desc())
        )
        basic_data_list = result.scalars().all()
    
    return templates.TemplateResponse("simulador.html", {
        "request": request,
        "user": current_user,
        "basic_data_list": basic_data_list
    })

