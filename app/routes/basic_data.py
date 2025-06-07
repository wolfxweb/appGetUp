from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime
import logging
import os

from app.database.db import get_db
from app.models.user import User
from app.models.basic_data import BasicData
from app.models.basic_data_log import BasicDataLog
from app.routes.auth import get_current_user
from app.schemas.basic_data import BasicDataForm

router = APIRouter(prefix="/basic-data")

templates = Jinja2Templates(directory="app/templates")

# Configuração do logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Configurar o formato do log
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Configurar o handler para console
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Configurar o handler para arquivo apenas se não estiver no ambiente Vercel
if not os.environ.get('VERCEL_ENV'):
    try:
        # Criar a pasta logs se não existir
        if not os.path.exists('app/logs'):
            os.makedirs('app/logs')
            
        # Configurar o handler para arquivo
        log_file = os.path.join('app', 'logs', f'basic_data_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Não foi possível configurar o log em arquivo: {str(e)}")

@router.get("/", response_class=HTMLResponse)
async def basic_data_page(
    request: Request,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Buscar dados básicos do usuário atual
        result = await db.execute(
            select(BasicData)
            .filter(BasicData.user_id == current_user.id)
            .order_by(BasicData.year.desc(), BasicData.month.desc())
        )
        basic_data = result.scalars().all()
        
        # Log dos dados básicos antes da formatação
        logger.info(f"Dados básicos encontrados: {len(basic_data)} registros")
        for data in basic_data:
            logger.info(f"Registro ID {data.id}: month={data.month}, year={data.year}, clients_served={data.clients_served}")
            logger.info(f"Valores monetários brutos: sales_revenue={data.sales_revenue}, sales_expenses={data.sales_expenses}, input_product_expenses={data.input_product_expenses}")
            logger.info(f"Valores monetários brutos: fixed_costs={data.fixed_costs}, pro_labore={data.pro_labore}, other_fixed_costs={data.other_fixed_costs}")
            logger.info(f"Valores formatados: sales_revenue={data.sales_revenue/10}, sales_expenses={data.sales_expenses/10}, input_product_expenses={data.input_product_expenses/10}")
            logger.info(f"Valores formatados: fixed_costs={data.fixed_costs/10 if data.fixed_costs else None}, pro_labore={data.pro_labore/10 if data.pro_labore else None}, other_fixed_costs={data.other_fixed_costs/10 if data.other_fixed_costs else None}")
        
        return templates.TemplateResponse(
            "basic_data.html",
            {
                "request": request,
                "user": current_user,
                "basic_data": basic_data
            }
        )
    except Exception as e:
        logger.error(f"Erro ao buscar dados básicos: {str(e)}")
        return templates.TemplateResponse(
            "basic_data.html",
            {
                "request": request,
                "user": current_user,
                "error_message": f"Erro ao buscar dados: {str(e)}"
            }
        )

@router.post("/delete/{data_id}")
async def delete_basic_data(
    request: Request,
    data_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Verificar se o usuário está autenticado
        if not current_user:
            return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

        # Buscar o registro específico
        result = await db.execute(
            select(BasicData)
            .filter(
                BasicData.id == data_id,
                BasicData.user_id == current_user.id
            )
        )
        basic_data = result.scalar_one_or_none()
        
        if not basic_data:
            logger.error(f"Registro não encontrado para deleção: ID {data_id}")
            return RedirectResponse(
                url="/basic-data",
                status_code=status.HTTP_303_SEE_OTHER
            )
        
        # Primeiro, deletar os logs associados
        await db.execute(
            delete(BasicDataLog).where(BasicDataLog.basic_data_id == data_id)
        )
        
        # Depois, deletar o registro principal
        await db.delete(basic_data)
        await db.commit()
        
        logger.info(f"Registro ID {data_id} deletado com sucesso")
        return RedirectResponse(
            url="/basic-data",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"Erro ao deletar registro ID {data_id}: {str(e)}")
        await db.rollback()
        return RedirectResponse(
            url="/basic-data",
            status_code=status.HTTP_303_SEE_OTHER
        )

@router.post("/save", response_class=HTMLResponse)
async def save_basic_data(
    request: Request,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    month: int = Form(...),
    year: int = Form(...),
    clients_served: int = Form(...),
    sales_revenue: str = Form(...),
    sales_expenses: str = Form(...),
    input_product_expenses: str = Form(...),
    fixed_costs: str = Form(None),
    ideal_profit_margin: float = Form(None),
    service_capacity: str = Form(None),
    pro_labore: str = Form(None),
    work_hours_per_week: float = Form(None),
    other_fixed_costs: str = Form(None),
    ideal_service_profit_margin: float = Form(None)
):
    try:
        # Verificar se já existe um registro para o mesmo mês/ano
        result = await db.execute(
            select(BasicData)
            .filter(
                BasicData.user_id == current_user.id,
                BasicData.month == month,
                BasicData.year == year
            )
        )
        existing_data = result.scalar_one_or_none()
        
        if existing_data:
            return templates.TemplateResponse(
                "basic_data_form.html",
                {
                    "request": request,
                    "user": current_user,
                    "error_message": "Já existe um registro para este mês/ano. Por favor, edite o registro existente.",
                    "basic_data": existing_data,
                    "edit_mode": True
                }
            )
        
        # Função para converter valor monetário para float
        def convert_currency(value: str) -> float:
            if not value:
                return 0.0
            # Remove caracteres não numéricos e converte vírgula para ponto
            value = value.replace('R$', '').replace('$', '').replace('.', '').replace(',', '.').strip()
            return float(value) if value else 0.0
        
        # Criar novo registro
        basic_data = BasicData(
            user_id=current_user.id,
            month=month,
            year=year,
            activity_type=current_user.activity_type,
            clients_served=clients_served,
            sales_revenue=int(convert_currency(sales_revenue) * 100),  # Multiplicar por 100 para armazenar em centavos
            sales_expenses=int(convert_currency(sales_expenses) * 100),
            input_product_expenses=int(convert_currency(input_product_expenses) * 100),
            fixed_costs=int(convert_currency(fixed_costs) * 100) if fixed_costs else None,
            ideal_profit_margin=float(ideal_profit_margin) if ideal_profit_margin else None,
            service_capacity=service_capacity,
            pro_labore=int(convert_currency(pro_labore) * 100) if pro_labore else None,
            work_hours_per_week=float(work_hours_per_week) if work_hours_per_week else None,
            other_fixed_costs=int(convert_currency(other_fixed_costs) * 100) if other_fixed_costs else None,
            ideal_service_profit_margin=float(ideal_service_profit_margin) if ideal_service_profit_margin else None,
            is_current=True
        )
        
        # Desativar is_current de outros registros
        result = await db.execute(
            select(BasicData)
            .filter(
                BasicData.user_id == current_user.id,
                BasicData.is_current == True
            )
        )
        other_records = result.scalars().all()
        for record in other_records:
            record.is_current = False
        
        # Salvar novo registro
        db.add(basic_data)
        await db.commit()
        
        return RedirectResponse(
            url="/basic-data",
            status_code=status.HTTP_303_SEE_OTHER
        )
        
    except Exception as e:
        logger.error(f"Erro ao salvar dados básicos: {str(e)}")
        return templates.TemplateResponse(
            "basic_data_form.html",
            {
                "request": request,
                "user": current_user,
                "error_message": f"Erro ao salvar dados: {str(e)}"
            }
        ) 