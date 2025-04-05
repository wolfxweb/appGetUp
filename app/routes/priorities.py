from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.basic_data import BasicData
from app.routes.auth import get_current_user

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

@router.get("/gestao-prioridades", response_class=HTMLResponse)
async def priorities_page(
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Buscar dados básicos do usuário
    basic_data_list = db.query(BasicData).filter(
        BasicData.user_id == current_user.id
    ).order_by(
        BasicData.year.desc(),
        BasicData.month.desc()
    ).all()

    return templates.TemplateResponse(
        "gestao_prioridades.html",
        {
            "request": request,
            "user": current_user,
            "basic_data_list": basic_data_list
        }
    )

@router.get("/gestao-prioridades/api/basic-data/{basic_data_id}")
async def get_basic_data(
    basic_data_id: int,
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    try:
        # Buscar o registro específico
        basic_data = db.query(BasicData).filter(
            BasicData.id == basic_data_id,
            BasicData.user_id == current_user.id
        ).first()

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
            "service_capacity": basic_data.service_capacity or "Não definido",
            "ideal_profit_margin": safe_float(basic_data.ideal_profit_margin),
            "other_fixed_costs": safe_float(getattr(basic_data, 'other_fixed_costs', None)),
            "ideal_service_profit_margin": safe_float(getattr(basic_data, 'ideal_service_profit_margin', None))
        }

        # Adicionar campos específicos de serviço se o tipo de atividade for 'servico'
        if current_user.activity_type == 'Serviços':
            response_data.update({
                "pro_labore": safe_float(getattr(basic_data, 'pro_labore', None)),
                "weekly_hours": safe_float(getattr(basic_data, 'work_hours_per_week', None))
            })

        return response_data
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao buscar dados básicos: {str(e)}")
        return JSONResponse(
            {"error": f"Erro interno do servidor: {str(e)}"}, 
            status_code=500
        ) 