"""
Lucrar Mais — simulação com base em Dados Básicos + cadastro (planilha Eduardo J8–J70).
"""
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.database.db import get_db
from app.models.analise_mensal import AnaliseMensal
from app.models.user import User
from app.routes.auth import get_current_user
from app.utils.sync_basic_data_analise import sync_basic_data_to_analise_mensal

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


@router.get("/lucrar-mais", response_class=HTMLResponse)
async def lucrar_mais_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user:
        return RedirectResponse(url="/login")
    if current_user.access_level == "Parceiro":
        return RedirectResponse(url="/dashboard", status_code=303)

    try:
        await sync_basic_data_to_analise_mensal(current_user.id, db)
    except Exception as e:
        logger.warning(f"Sync basic_data -> lucrar-mais: {e}")

    return templates.TemplateResponse(
        "lucrar_mais.html",
        {
            "request": request,
            "user": current_user,
            "active_page": "lucrar_mais",
        },
    )


def _basicos_dict(analise: AnaliseMensal, activity_type: str) -> dict:
    ticket = (
        (analise.faturamento / analise.quant_clientes)
        if analise.faturamento and analise.quant_clientes
        else (analise.ticket_medio or 0)
    )
    tipo = (activity_type or "").lower()
    eh_comercio = "comerc" in tipo
    return {
        "id": analise.id,
        "mes": analise.mes,
        "ano": analise.ano,
        "quant_clientes": analise.quant_clientes or 0,
        "faturamento": analise.faturamento or 0,
        "ticket_medio": ticket or 0,
        "gastos_vendas": analise.gastos_vendas or 0,
        "custo_insumos": analise.custo_mercadorias or 0,
        "custo_mao_obra": 0,
        "custo_fixo": analise.custo_fixo_total or 0,
        "eh_comercio": eh_comercio,
    }


@router.get("/lucrar-mais/api/base")
async def lucrar_mais_base(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Último Dados Básicos + dados do cadastro do usuário."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autorizado")

    try:
        await sync_basic_data_to_analise_mensal(current_user.id, db)
    except Exception as e:
        logger.warning(f"Sync: {e}")

    list_result = await db.execute(
        select(AnaliseMensal)
        .filter(AnaliseMensal.user_id == current_user.id)
        .order_by(AnaliseMensal.ano.desc(), AnaliseMensal.mes.desc())
        .limit(24)
    )
    analiticas = list(list_result.scalars().all())
    periodos = [{"id": a.id, "mes": a.mes, "ano": a.ano} for a in analiticas]
    basicos = _basicos_dict(analiticas[0], current_user.activity_type) if analiticas else None

    cadastro = {
        "capacidade": current_user.service_capacity,
        "margem_ideal": current_user.ideal_profit_margin,
        "perdas": current_user.estimated_loss_percentage,
        "activity_type": current_user.activity_type or "",
        "nome": (current_user.name or "").split()[0] if current_user.name else "",
    }

    return {"cadastro": cadastro, "basicos": basicos, "periodos": periodos}


@router.get("/lucrar-mais/api/periodo/{analise_id}")
async def lucrar_mais_periodo(
    analise_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autorizado")

    result = await db.execute(
        select(AnaliseMensal).filter(
            AnaliseMensal.id == analise_id,
            AnaliseMensal.user_id == current_user.id,
        )
    )
    analise = result.scalar_one_or_none()
    if not analise:
        raise HTTPException(status_code=404, detail="Período não encontrado")

    return _basicos_dict(analise, current_user.activity_type)
