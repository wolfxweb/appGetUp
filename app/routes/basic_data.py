from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import calendar
from pydantic import BaseModel, validator, ValidationError
from typing import Optional

from app.database.db import get_db
from app.models.user import User
from app.models.basic_data import BasicData
from app.routes.auth import get_current_user

router = APIRouter(prefix="/basic-data")

templates = Jinja2Templates(directory="app/templates")

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
    confirm_update: bool = Form(False)
):
    try:
        # Criar o modelo Pydantic com os dados recebidos
        data = BasicDataInput(
            month=month,
            year=year,
            clients_served=clients_served,
            sales_revenue=sales_revenue,
            sales_expenses=sales_expenses,
            input_product_expenses=input_product_expenses,
            fixed_costs=fixed_costs,
            ideal_profit_margin=ideal_profit_margin,
            service_capacity=service_capacity,
            pro_labore=pro_labore,
            work_hours_per_week=work_hours_per_week,
            other_fixed_costs=other_fixed_costs,
            ideal_service_profit_margin=ideal_service_profit_margin
        )

        # Verificar se já existe um registro para o mês/ano
        existing_data = db.query(BasicData).filter(
            BasicData.user_id == current_user.id,
            BasicData.month == data.month,
            BasicData.year == data.year
        ).first()

        if existing_data:
            # Atualizar registro existente
            basic_data = existing_data
        else:
            # Criar novo registro
            basic_data = BasicData(
                user_id=current_user.id,
                month=data.month,
                year=data.year,
                activity_type=current_user.activity_type
            )
            db.add(basic_data)

        # Atualizar campos comuns
        basic_data.clients_served = data.clients_served
        basic_data.sales_revenue = data.sales_revenue
        basic_data.sales_expenses = data.sales_expenses
        basic_data.input_product_expenses = data.input_product_expenses

        # Atualizar campos específicos baseados no tipo de atividade
        if current_user.activity_type in ["Comércio", "Indústria"]:
            basic_data.fixed_costs = data.fixed_costs
            basic_data.ideal_profit_margin = data.ideal_profit_margin
            basic_data.service_capacity = data.service_capacity
        elif current_user.activity_type == "Serviços":
            basic_data.pro_labore = data.pro_labore
            basic_data.work_hours_per_week = data.work_hours_per_week
            basic_data.other_fixed_costs = data.other_fixed_costs
            basic_data.ideal_service_profit_margin = data.ideal_service_profit_margin

        try:
            db.commit()
            return RedirectResponse(
                url="/basic-data", 
                status_code=status.HTTP_303_SEE_OTHER
            )
        except Exception as e:
            db.rollback()
            return templates.TemplateResponse(
                "basic_data_form.html",
                {
                    "request": request,
                    "user": current_user,
                    "error_message": f"Erro ao salvar dados: {str(e)}",
                    "month": data.month,
                    "year": data.year,
                    "clients_served": data.clients_served,
                    "sales_revenue": data.sales_revenue,
                    "sales_expenses": data.sales_expenses,
                    "input_product_expenses": data.input_product_expenses,
                    "fixed_costs": data.fixed_costs,
                    "ideal_profit_margin": data.ideal_profit_margin,
                    "service_capacity": data.service_capacity,
                    "pro_labore": data.pro_labore,
                    "work_hours_per_week": data.work_hours_per_week,
                    "other_fixed_costs": data.other_fixed_costs,
                    "ideal_service_profit_margin": data.ideal_service_profit_margin,
                    "current_month": data.month,
                    "current_year": data.year
                }
            )
    except ValidationError as e:
        return templates.TemplateResponse(
            "basic_data_form.html",
            {
                "request": request,
                "user": current_user,
                "error_message": "Erro de validação nos dados. Por favor, verifique os valores informados.",
                "month": month,
                "year": year,
                "clients_served": clients_served,
                "sales_revenue": sales_revenue,
                "sales_expenses": sales_expenses,
                "input_product_expenses": input_product_expenses,
                "fixed_costs": fixed_costs,
                "ideal_profit_margin": ideal_profit_margin,
                "service_capacity": service_capacity,
                "pro_labore": pro_labore,
                "work_hours_per_week": work_hours_per_week,
                "other_fixed_costs": other_fixed_costs,
                "ideal_service_profit_margin": ideal_service_profit_margin,
                "current_month": month,
                "current_year": year
            }
        )

@router.get("/edit/{data_id}", response_class=HTMLResponse)
async def edit_basic_data_page(
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

    # Obter o mês e ano atual
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    return templates.TemplateResponse(
        "basic_data_form.html",
        {
            "request": request,
            "user": current_user,
            "basic_data": basic_data,
            "current_month": current_month,
            "current_year": current_year,
            "edit_mode": True
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