from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import BasicData
from app.database import async_session
from app.routes.auth import get_current_user
import logging
from app.database.db import get_db
from sqlalchemy.orm import Session


# Configure o logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/diagnostico")

templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def diagnostico_page(
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    
   # print(current_user.id)
    # Buscar dados básicos do usuário
    async with async_session() as session:
        user_id =int(current_user.id)
        query = select(BasicData).where(BasicData.user_id == user_id)
        result = await session.execute(query)
        basic_data_list = result.scalars().all()

    return templates.TemplateResponse(
        "diagnostico.html",
        {
            "request": request,
            "basic_data_list": basic_data_list,
            "user": current_user
        }
    )
@router.get("/api/list-basic-data")
async def list_basic_data(
    request: Request,
    current_user = Depends(get_current_user)
):
    if not current_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        async with async_session() as session:
            query = select(BasicData).where(BasicData.user_id == current_user.id)
            result = await session.execute(query)
            basic_data_list = result.scalars().all()
            
            data = []
            for item in basic_data_list:
                data.append({
                    "id": item.id,
                    "month": item.month,
                    "year": item.year,
                    "clients_served": item.clients_served,
                    "sales_revenue": float(item.sales_revenue),
                    "is_current": item.is_current
                })
            
            return data
    except Exception as e:
        logger.error(f"Erro ao listar dados básicos: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/api/basic-data/{basic_data_id}")
async def get_basic_data(
    basic_data_id: int,
    request: Request,
    current_user = Depends(get_current_user)
):
    if not current_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    try:
        async with async_session() as session:
            query = select(BasicData).where(
                and_(
                    BasicData.id == basic_data_id,
                    BasicData.user_id == current_user.id
                )
            )
            result = await session.execute(query)
            basic_data = result.scalar_one_or_none()

            if not basic_data:
                return JSONResponse({"error": "Not found"}, status_code=404)

            # Função de segurança para converter para float
            def safe_float(value):
                if value is None:
                    return 0.0
                return float(value)

            # Retornar os dados como JSON com verificação de nulos
            response_data = {
                "id": basic_data.id,
                "clients_served": basic_data.clients_served or 0,  # Garante que não é None
                "sales_revenue": safe_float(basic_data.sales_revenue),
                "sales_expenses": safe_float(basic_data.sales_expenses),
                "fixed_costs": safe_float(basic_data.fixed_costs),
                "operational_expenses": safe_float(
                    basic_data.operational_expenses if hasattr(basic_data, 'operational_expenses') 
                    else getattr(basic_data, 'input_product_expenses', None)
                ),
                "financial_expenses": safe_float(
                    getattr(basic_data, 'financial_expenses', None)
                ),
                "taxes": safe_float(
                    getattr(basic_data, 'taxes', None)
                ),
                "other_expenses": safe_float(
                    getattr(basic_data, 'other_fixed_costs', None)
                )
            }

            # Adicionar campos específicos de serviço se o tipo de atividade for 'servico'
            if current_user.activity_type == 'Serviços':
                response_data.update({
                    "pro_labore": safe_float(getattr(basic_data, 'pro_labore', None)),
                    "weekly_hours": safe_float(getattr(basic_data, 'work_hours_per_week', None))
                })

            return response_data
    except Exception as e:
        logger.error(f"Erro ao buscar dados básicos: {str(e)}")
        return JSONResponse(
            {"error": f"Erro interno do servidor: {str(e)}"}, 
            status_code=500
        ) 