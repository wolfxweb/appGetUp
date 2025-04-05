from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.database.db import SessionLocal
from app.models.basic_data import BasicData
from app.models.calculator import Calculator
from app.routes.auth import get_current_user
from app.models.user import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Modelo Pydantic para validação dos dados da calculadora
class CalculatorData(BaseModel):
    basic_data_id: int
    month: int
    year: int
    product_name: str
    current_price: float
    current_margin: float
    company_margin: float
    desired_margin: float
    suggested_price: float
    price_relation: float
    competitor_price: float
    notes: Optional[str] = None

@router.get("/calculadora", response_class=HTMLResponse)
async def calculator(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Get user's basic data
    basic_data = db.query(BasicData).filter(BasicData.user_id == current_user.id).all()
    
    # Get user's calculator records
    calculator_records = db.query(Calculator).filter(
        Calculator.user_id == current_user.id
    ).order_by(Calculator.created_at.desc()).all()
    
    return templates.TemplateResponse("calculadora.html", {
        "request": request,
        "active_page": "calculadora",
        "basic_data": basic_data,
        "current_user": current_user,
        "calculator_records": calculator_records
    })

@router.post("/api/calculate-price")
async def calculate_price(
    data: dict
):
    # Extract values from the request body
    current_price = data.get("current_price")
    current_margin = data.get("current_margin")
    company_margin = data.get("company_margin")
    desired_margin = data.get("desired_margin")
    competitor_price = data.get("competitor_price")
    
    # Calculate suggested price
    suggested_price = current_price * (1 + (desired_margin - current_margin) / 100)
    
    # Calculate price relation
    price_relation = ((suggested_price - current_price) / current_price) * 100
    
    return {
        "suggestedPrice": round(suggested_price, 2),
        "priceRelation": round(price_relation, 2)
    }

@router.post("/api/save-calculator")
async def save_calculator(
    calculator_data: CalculatorData,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verificar se o basic_data_id pertence ao usuário atual
    basic_data = db.query(BasicData).filter(
        BasicData.id == calculator_data.basic_data_id,
        BasicData.user_id == current_user.id
    ).first()
    
    if not basic_data:
        raise HTTPException(status_code=404, detail="Dados básicos não encontrados")
    
    # Criar novo registro da calculadora
    new_calculator = Calculator(
        user_id=current_user.id,
        basic_data_id=calculator_data.basic_data_id,
        month=calculator_data.month,
        year=calculator_data.year,
        product_name=calculator_data.product_name,
        current_price=calculator_data.current_price,
        current_margin=calculator_data.current_margin,
        company_margin=calculator_data.company_margin,
        desired_margin=calculator_data.desired_margin,
        suggested_price=calculator_data.suggested_price,
        price_relation=calculator_data.price_relation,
        competitor_price=calculator_data.competitor_price,
        notes=calculator_data.notes
    )
    
    # Adicionar ao banco de dados
    db.add(new_calculator)
    db.commit()
    db.refresh(new_calculator)
    
    return {"success": True, "id": new_calculator.id}

@router.delete("/api/delete-calculator/{record_id}")
async def delete_calculator(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verificar se o registro existe e pertence ao usuário atual
    calculator_record = db.query(Calculator).filter(
        Calculator.id == record_id,
        Calculator.user_id == current_user.id
    ).first()
    
    if not calculator_record:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    
    # Remover o registro
    db.delete(calculator_record)
    db.commit()
    
    return {"success": True} 