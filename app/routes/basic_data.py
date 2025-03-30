from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import calendar

from app.database.db import get_db
from app.models.user import User
from app.models.basic_data import BasicData
from app.routes.auth import get_current_user

router = APIRouter(prefix="/basic-data")

templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def basic_data_page(
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Buscar dados básicos do usuário
    basic_data = db.query(BasicData).filter(
        BasicData.user_id == current_user.id
    ).order_by(BasicData.year.desc(), BasicData.month.desc()).all()

    return templates.TemplateResponse(
        "basic_data.html",
        {
            "request": request,
            "user": current_user,
            "basic_data": basic_data
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
    sales_revenue: float = Form(...),
    sales_expenses: float = Form(...),
    input_product_expenses: float = Form(...),
    fixed_costs: float = Form(None),
    ideal_profit_margin: float = Form(None),
    service_capacity: str = Form(None),
    pro_labore: float = Form(None),
    work_hours_per_week: float = Form(None),
    confirm_update: bool = Form(False)
):
    # Verificar o mês e ano
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    # Verificar se o mês selecionado é válido
    if month > current_month or year > current_year:
        return templates.TemplateResponse(
            "basic_data_form.html",
            {
                "request": request,
                "user": current_user,
                "error_message": "Não é possível cadastrar dados para meses futuros.",
                "current_month": current_month,
                "current_year": current_year
            }
        )

    # Verificar se já existe um registro para o mês
    existing_data = db.query(BasicData).filter(
        BasicData.user_id == current_user.id,
        BasicData.month == month,
        BasicData.year == year
    ).first()

    # Se já existir um registro e não houver confirmação, solicitar confirmação
    if existing_data and not confirm_update:
        return templates.TemplateResponse(
            "basic_data_form.html",
            {
                "request": request,
                "user": current_user,
                "warning_message": "Já existe um registro para este mês. Deseja substituir?",
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
                "show_confirm": True,
                "current_month": current_month,
                "current_year": current_year
            }
        )

    # Criar ou atualizar o registro
    if existing_data:
        # Atualizar registro existente
        basic_data = existing_data
    else:
        # Criar novo registro
        basic_data = BasicData(
            user_id=current_user.id,
            month=month,
            year=year,
            activity_type=current_user.activity_type
        )
        db.add(basic_data)

    # Atualizar campos comuns
    basic_data.clients_served = clients_served
    basic_data.sales_revenue = sales_revenue
    basic_data.sales_expenses = sales_expenses
    basic_data.input_product_expenses = input_product_expenses

    # Atualizar campos específicos baseados no tipo de atividade
    if current_user.activity_type in ["Comércio", "Indústria"]:
        basic_data.fixed_costs = fixed_costs
        basic_data.ideal_profit_margin = ideal_profit_margin
        basic_data.service_capacity = service_capacity
    elif current_user.activity_type == "Serviços":
        basic_data.pro_labore = pro_labore
        basic_data.work_hours_per_week = work_hours_per_week

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
                "current_month": current_month,
                "current_year": current_year
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