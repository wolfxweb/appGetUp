from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import calendar
from pydantic import BaseModel, validator, ValidationError
from typing import Optional
import logging
import os
import locale

from app.database.db import get_db
from app.models.user import User
from app.models.basic_data import BasicData
from app.models.basic_data_log import BasicDataLog
from app.routes.auth import get_current_user

router = APIRouter(prefix="/basic-data")

templates = Jinja2Templates(directory="app/templates")

# Criar a pasta logs se não existir
if not os.path.exists('app/logs'):
    os.makedirs('app/logs')

# Configuração do logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Configurar o formato do log
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Configurar o handler para arquivo
log_file = os.path.join('app', 'logs', f'basic_data_{datetime.now().strftime("%Y%m%d")}.log')
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Configurar o handler para console
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

class BasicDataInput(BaseModel):
    month: int
    year: int
    clients_served: int
    sales_revenue: float
    sales_expenses: float
    input_product_expenses: float
    fixed_costs: Optional[float] = None
    ideal_profit_margin: Optional[float] = None
    service_capacity: Optional[str] = None
    pro_labore: Optional[float] = None
    work_hours_per_week: Optional[float] = None
    other_fixed_costs: Optional[float] = None
    ideal_service_profit_margin: Optional[float] = None
    is_current: Optional[bool] = None
    @validator('sales_revenue', 'sales_expenses', 'input_product_expenses', 'fixed_costs', 'pro_labore', 'other_fixed_costs', pre=True)
    def convert_string_to_float(cls, v):
        if isinstance(v, str):
            if not v:  # Se a string estiver vazia
                return None
            # Remove espaços em branco
            v = v.strip()
            # Substitui vírgula por ponto
            v = v.replace(',', '.')
            try:
                # Converte para float
                return float(v)
            except ValueError:
                raise ValueError('Valor inválido para número decimal')
        return v

def compare_and_log_changes(db: Session, old_data_dict: dict, new_data: dict) -> list:
    """Compara os dados antigos com os novos e retorna uma lista de alterações"""
    changes = []
    
    # Mapeamento de campos para seus nomes amigáveis
    field_names = {
        'clients_served': 'Quantidade de Clientes Atendidos',
        'sales_revenue': 'Faturamento com Vendas',
        'sales_expenses': 'Gastos com Vendas',
        'input_product_expenses': 'Gastos com Insumos e Produtos',
        'fixed_costs': 'Custos Fixos',
        'ideal_profit_margin': 'Margem de Lucro Ideal',
        'service_capacity': 'Capacidade de Atendimento',
        'pro_labore': 'Pró-labore',
        'work_hours_per_week': 'Horas de Trabalho por Semana',
        'other_fixed_costs': 'Demais Custos Fixos',
        'ideal_service_profit_margin': 'Margem de Lucro Ideal (Serviços)',
        'is_current': 'É o Atual'
    }
    
    for field, new_value in new_data.items():
        if field not in old_data_dict:
            continue
            
        old_value = old_data_dict[field]  # Acessando através do índice do dicionário

        # Comparar valores
        if isinstance(old_value, float) and isinstance(new_value, float):
            # Se os valores são iguais, continue para a próxima iteração
            if abs(old_value - new_value) < 1e-9:  # Tolerância para flutuantes
                continue
            
            # Se os valores são diferentes, registra a mudança
            changes.append(f"{field_names[field]} alterado de {old_value} para {new_value}")
            logger.info(f"Alteração detectada: {field_names[field]} de {old_value} para {new_value}")
        else:
            # Comparar outros tipos
            if old_value != new_value:
                changes.append(f"{field_names[field]} alterado de {old_value} para {new_value}")
                logger.info(f"Alteração detectada: {field_names[field]} de {old_value} para {new_value}")
    
    return changes

@router.get("/", response_class=HTMLResponse)
async def basic_data_page(
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Buscar dados básicos do usuário com ordenação correta
        basic_data = db.query(BasicData).filter(
            BasicData.user_id == current_user.id
        ).order_by(
            BasicData.year.desc(),
            BasicData.month.desc()
        ).all()

        return templates.TemplateResponse(
            "basic_data.html",
            {
                "request": request,
                "user": current_user,
                "basic_data": basic_data
            }
        )
    except Exception as e:
        # Log do erro para debug
        print(f"Erro ao buscar dados básicos: {str(e)}")
        return templates.TemplateResponse(
            "basic_data.html",
            {
                "request": request,
                "user": current_user,
                "basic_data": [],
                "error_message": "Erro ao carregar os dados básicos"
            }
        )

@router.get("/new", response_class=HTMLResponse)
async def new_basic_data_page(
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Obter o mês e ano atual
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    # Verificar se já existe um registro para o mês atual
    existing_data = db.query(BasicData).filter(
        BasicData.user_id == current_user.id,
        BasicData.month == current_month,
        BasicData.year == current_year
    ).first()

    return templates.TemplateResponse(
        "basic_data_form.html",
        {
            "request": request,
            "user": current_user,
            "current_month": current_month,
            "current_year": current_year,
            "existing_data": existing_data
        }
    )

@router.post("/save")
async def save_basic_data(
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
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
    ideal_service_profit_margin: float = Form(None),
    is_current: str = Form(False),
    edit_mode: bool = Form(False)
):
    try:
        is_current_bool = is_current.lower() == 'true'
        logger.info(f"Processando dados básicos para usuário {current_user.id}")

        # Buscar dados básicos existentes
        existing_data = db.query(BasicData).filter(
            BasicData.user_id == current_user.id,
            BasicData.month == month,
            BasicData.year == year
        ).first()

        # Preparar os novos dados com conversão de tipos
        new_data = {
            'clients_served': clients_served,
            'sales_revenue': float(sales_revenue.replace(',', '.')) if sales_revenue else None,
            'sales_expenses': float(sales_expenses.replace(',', '.')) if sales_expenses else None,
            'input_product_expenses': float(input_product_expenses.replace(',', '.')) if input_product_expenses else None,
            'fixed_costs': float(fixed_costs.replace(',', '.')) if fixed_costs else None,
            'ideal_profit_margin': ideal_profit_margin,
            'service_capacity': service_capacity,
            'pro_labore': pro_labore,
            'work_hours_per_week': work_hours_per_week,
            'other_fixed_costs': other_fixed_costs,
            'ideal_service_profit_margin': ideal_service_profit_margin,
            'is_current': is_current_bool
        }

        if existing_data:
            logger.info(f"Registro existente encontrado para {month}/{year}")

            # Converter existing_data para um dicionário
            existing_data_dict = {
                'clients_served': existing_data.clients_served,
                'sales_revenue': existing_data.sales_revenue,
                'sales_expenses': existing_data.sales_expenses,
                'input_product_expenses': existing_data.input_product_expenses,
                'fixed_costs': existing_data.fixed_costs,
                'ideal_profit_margin': existing_data.ideal_profit_margin,
                'service_capacity': existing_data.service_capacity,
                'pro_labore': existing_data.pro_labore,
                'work_hours_per_week': existing_data.work_hours_per_week,
                'other_fixed_costs': existing_data.other_fixed_costs,
                'ideal_service_profit_margin': existing_data.ideal_service_profit_margin,
                'is_current': existing_data.is_current
            }

            # Passar o dicionário em vez do objeto
            changes = compare_and_log_changes(db, existing_data_dict, new_data)

            if changes:  # Se houver alterações
                logger.info(f"Alterações detectadas: {changes}")

                # Registrar cada alteração no log
                for change in changes:
                    log_entry = BasicDataLog(
                        basic_data_id=existing_data.id,
                        change_description=change
                    )
                    db.add(log_entry)
                    logger.info(f"Log adicionado: {change}")

                # Atualizar dados existentes
                for field, value in new_data.items():
                    setattr(existing_data, field, value)
                    logger.info(f"Campo {field} atualizado para {value}")
            else:
                logger.info("Nenhuma alteração detectada")

        else:
            logger.info("Criando novo registro")
            basic_data = BasicData(
                user_id=current_user.id,
                month=month,
                year=year,
                activity_type=current_user.activity_type,
                **new_data
            )
            db.add(basic_data)

        db.commit()
        logger.info("Dados salvos com sucesso")
        return RedirectResponse(url="/basic-data", status_code=status.HTTP_303_SEE_OTHER)

    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao salvar: {str(e)}")
        return templates.TemplateResponse(
            "basic_data_form.html",
            {
                "request": request,
                "error_message": f"Erro ao salvar: {str(e)}",
                "user": current_user,
                "month": month,
                "year": year,
                **new_data,
                "current_month": month,
                "current_year": year
            }
        )

@router.get("/edit/{data_id}", response_class=HTMLResponse)
async def edit_basic_data_page(
    request: Request,
    data_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = 1,
    per_page: int = 10
):
    # Buscar o registro específico
    basic_data = db.query(BasicData).filter(
        BasicData.id == data_id,
        BasicData.user_id == current_user.id
    ).first()

    if not basic_data:
        raise HTTPException(status_code=404, detail="Registro não encontrado")

    # Log para arquivo
    logger.info(f"Buscando logs para basic_data_id: {data_id}")

    # Buscar os logs relacionados a este registro básico
    logs = db.query(BasicDataLog).filter(
        BasicDataLog.basic_data_id == data_id
    ).order_by(
        BasicDataLog.id.desc()
    ).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    # Log para arquivo com contagem de logs encontrados
    logger.info(f"Logs encontrados: {len(logs)}")
    
    # Log detalhado de cada registro encontrado
    for log in logs:
        logger.info(f"Log ID: {log.id}, Descrição: {log.change_description}")

    # Contar total de logs para paginação
    total_logs = db.query(BasicDataLog).filter(
        BasicDataLog.basic_data_id == data_id
    ).count()

    logger.info(f"Total de logs: {total_logs}, Páginas: {(total_logs + per_page - 1) // per_page}")

    # Calcular total de páginas
    total_pages = (total_logs + per_page - 1) // per_page

    return templates.TemplateResponse(
        "basic_data_form.html",
        {
            "request": request,
            "user": current_user,
            "basic_data": basic_data,
            "edit_mode": True,
            "logs": logs,
            "current_page": page,
            "total_pages": total_pages,
            "per_page": per_page,
            "total_logs": total_logs
        }
    )

@router.post("/delete/{data_id}")
async def delete_basic_data(
    request: Request,
    data_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Buscar o registro específico
    basic_data = db.query(BasicData).filter(
        BasicData.id == data_id,
        BasicData.user_id == current_user.id
    ).first()

    if not basic_data:
        raise HTTPException(status_code=404, detail="Registro não encontrado")

    try:
        db.delete(basic_data)
        db.commit()
        return RedirectResponse(
            url="/basic-data?success_message=Registro excluído com sucesso", 
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        db.rollback()
        return RedirectResponse(
            url="/basic-data?error_message=Erro ao excluir registro", 
            status_code=status.HTTP_303_SEE_OTHER
        )

@router.get("/check/{year}/{month}")
async def check_basic_data_exists(
    year: int,
    month: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verifica se já existem dados básicos para o mês e ano especificados"""
    existing_data = db.query(BasicData).filter(
        BasicData.user_id == current_user.id,
        BasicData.year == year,
        BasicData.month == month
    ).first()
    
    return {"exists": existing_data is not None} 