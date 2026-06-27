from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime

from app.database.db import get_db
from app.models.license import License
from app.models.user import User
from app.models.analise_mensal import AnaliseMensal
from app.routes.auth import get_current_user
from app.routes.analise_mensal import AnaliseMensalSchema, _aplicar_campos_calculados
from app.utils.license_activation import get_partner_license
from app.utils.analise_save import save_analise_for_user
from app.utils.analise_form_adapter import form_context_for_analise_cadastro
from app.utils.cadastro_prefill import build_cadastro_prefill

router = APIRouter(prefix="/parceiro")
templates = Jinja2Templates(directory="app/templates")


async def parceiro_required(request: Request, current_user=Depends(get_current_user)):
    if not current_user or current_user.access_level != "Parceiro":
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return current_user


@router.get("/licencas")
async def listar_licencas_parceiro(
    request: Request,
    current_user=Depends(parceiro_required),
    success_message: str = "",
    error_message: str = "",
):
    url = "/dashboard"
    if success_message:
        url += f"?success_message={success_message}"
    elif error_message:
        url += f"?error_message={error_message}"
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)


@router.get("/licencas/{license_id}/dados-basicos/lista", response_class=HTMLResponse)
async def parceiro_dados_basicos_lista(
    license_id: int,
    request: Request,
    current_user=Depends(parceiro_required),
    db: AsyncSession = Depends(get_db),
    success_message: str = "",
    ano: Optional[int] = None,
):
    license_row = await get_partner_license(db, license_id, current_user.id)

    client_result = await db.execute(
        select(User).filter(User.id == license_row.client_user_id)
    )
    client_user = client_result.scalar_one_or_none()
    if not client_user:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    years_result = await db.execute(
        select(AnaliseMensal.ano)
        .filter(AnaliseMensal.user_id == license_row.client_user_id)
        .distinct()
        .order_by(AnaliseMensal.ano.desc())
    )
    available_years = [row[0] for row in years_result.all()]

    if ano is None and available_years:
        ano = available_years[0]

    query = (
        select(AnaliseMensal)
        .filter(AnaliseMensal.user_id == license_row.client_user_id)
        .order_by(AnaliseMensal.ano.desc(), AnaliseMensal.mes.desc())
    )
    if ano is not None:
        query = query.filter(AnaliseMensal.ano == ano)

    analises_result = await db.execute(query)
    analises = analises_result.scalars().all()

    total_faturamento = sum(a.faturamento or 0 for a in analises)
    total_resultado = sum(a.resultado or 0 for a in analises)
    tickets = [a.ticket_medio for a in analises if a.ticket_medio]
    margens = [a.percentual_margem for a in analises if a.percentual_margem is not None]
    ticket_medio = sum(tickets) / len(tickets) if tickets else 0
    margem_media = sum(margens) / len(margens) if margens else 0

    return templates.TemplateResponse(
        "parceiro_dados_basicos_lista.html",
        {
            "request": request,
            "user": current_user,
            "client_user": client_user,
            "license": license_row,
            "analises": analises,
            "available_years": available_years,
            "selected_year": ano,
            "total_analises": len(analises),
            "total_faturamento": total_faturamento,
            "ticket_medio": ticket_medio,
            "margem_media": margem_media,
            "total_resultado": total_resultado,
            "success_message": success_message,
            "active_page": "parceiro_licencas",
        },
    )


@router.get("/licencas/{license_id}/dados-basicos", response_class=HTMLResponse)
async def parceiro_dados_basicos(
    license_id: int,
    request: Request,
    current_user=Depends(parceiro_required),
    db: AsyncSession = Depends(get_db),
):
    license_row = await get_partner_license(db, license_id, current_user.id)

    client_result = await db.execute(
        select(User).filter(User.id == license_row.client_user_id)
    )
    client_user = client_result.scalar_one_or_none()
    if not client_user:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    now = datetime.now()
    cadastro_prefill = await build_cadastro_prefill(client_user, db)
    ctx = form_context_for_analise_cadastro(
        edit_mode=False,
        analise=None,
        current_month=now.month,
        current_year=now.year,
        prefill_margin=getattr(client_user, "ideal_profit_margin", None),
        prefill_capacity=getattr(client_user, "service_capacity", None),
        cadastro_prefill=cadastro_prefill,
    )

    return templates.TemplateResponse(
        "basic_data_form.html",
        {
            "request": request,
            "user": current_user,
            "client_user": client_user,
            "partner_mode": True,
            "partner_license_id": license_id,
            "active_page": "parceiro_licencas",
            **ctx,
        },
    )


@router.get("/licencas/{license_id}/dados-basicos/{analise_id}", response_class=HTMLResponse)
async def parceiro_dados_basicos_editar(
    license_id: int,
    analise_id: int,
    request: Request,
    current_user=Depends(parceiro_required),
    db: AsyncSession = Depends(get_db),
):
    license_row = await get_partner_license(db, license_id, current_user.id)

    result = await db.execute(
        select(AnaliseMensal).filter(
            AnaliseMensal.id == analise_id,
            AnaliseMensal.user_id == license_row.client_user_id,
        )
    )
    analise = result.scalar_one_or_none()
    if not analise:
        raise HTTPException(status_code=404, detail="Análise não encontrada")

    client_result = await db.execute(
        select(User).filter(User.id == license_row.client_user_id)
    )
    client_user = client_result.scalar_one_or_none()
    if not client_user:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    cadastro_prefill = await build_cadastro_prefill(client_user, db)
    ctx = form_context_for_analise_cadastro(
        edit_mode=True,
        analise=analise,
        current_month=analise.mes,
        current_year=analise.ano,
        prefill_margin=getattr(client_user, "ideal_profit_margin", None),
        prefill_capacity=getattr(client_user, "service_capacity", None),
        cadastro_prefill=cadastro_prefill,
    )

    return templates.TemplateResponse(
        "basic_data_form.html",
        {
            "request": request,
            "user": current_user,
            "client_user": client_user,
            "partner_mode": True,
            "partner_license_id": license_id,
            "active_page": "parceiro_licencas",
            **ctx,
        },
    )


@router.post("/licencas/{license_id}/api/salvar")
async def parceiro_salvar_analise(
    license_id: int,
    data: AnaliseMensalSchema,
    current_user=Depends(parceiro_required),
    db: AsyncSession = Depends(get_db),
):
    license_row = await get_partner_license(db, license_id, current_user.id)
    client_user_id = license_row.client_user_id
    if not client_user_id:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Licença sem cliente vinculado."},
        )
    if client_user_id == current_user.id:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "Erro interno: não é permitido salvar no usuário do parceiro.",
            },
        )

    data = _aplicar_campos_calculados(data)
    try:
        result = await save_analise_for_user(db, client_user_id, data)
        result["client_user_id"] = client_user_id
        return result
    except Exception as e:
        await db.rollback()
        return {"success": False, "message": f"Erro ao salvar análise: {str(e)}"}


@router.get("/licencas/{license_id}/api/existe")
async def parceiro_existe_analise(
    license_id: int,
    mes: int,
    ano: int,
    current_user=Depends(parceiro_required),
    db: AsyncSession = Depends(get_db),
):
    license_row = await get_partner_license(db, license_id, current_user.id)
    result = await db.execute(
        select(AnaliseMensal).filter(
            AnaliseMensal.user_id == license_row.client_user_id,
            AnaliseMensal.mes == mes,
            AnaliseMensal.ano == ano,
        )
    )
    analise = result.scalar_one_or_none()
    if analise:
        return {
            "existe": True,
            "analise_id": analise.id,
            "edit_url": f"/parceiro/licencas/{license_id}/dados-basicos/{analise.id}",
        }
    return {"existe": False}
