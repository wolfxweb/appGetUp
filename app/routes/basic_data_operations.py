from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import calendar
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

def compare_and_log_changes(db: AsyncSession, old_data_dict: dict, new_data: dict) -> list:
    """Compara os dados antigos com os novos e retorna uma lista de alterações"""
    changes = []
    
    # Configurar locale para PT-BR
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
        except:
            pass  # Se falhar, continua sem formatação
    
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
    
    # Campos monetários que precisam de formatação
    money_fields = ['sales_revenue', 'sales_expenses', 'input_product_expenses', 
                    'fixed_costs', 'pro_labore', 'other_fixed_costs']
    
    for field, new_value in new_data.items():
        if field not in old_data_dict:
            continue
            
        old_value = old_data_dict[field]

        # Comparar valores
        if field == 'is_current':
            # Formatar valores booleanos como Sim/Não
            if old_value != new_value:
                old_formatted = "Sim" if old_value else "Não"
                new_formatted = "Sim" if new_value else "Não"
                changes.append(f"{field_names[field]} alterado de {old_formatted} para {new_formatted}")
                logger.info(f"Alteração detectada: {field_names[field]} de {old_formatted} para {new_formatted}")
        elif isinstance(old_value, float) and isinstance(new_value, float):
            # Se os valores são iguais, continue para a próxima iteração
            if abs(old_value - new_value) < 1e-9:
                continue
            
            # Formatar valores monetários
            if field in money_fields:
                try:
                    old_formatted = f"R$ {old_value:.2f}".replace('.', ',')
                    new_formatted = f"R$ {new_value:.2f}".replace('.', ',')
                    changes.append(f"{field_names[field]} alterado de {old_formatted} para {new_formatted}")
                    logger.info(f"Alteração detectada: {field_names[field]} de {old_formatted} para {new_formatted}")
                except:
                    # Fallback caso a formatação falhe
                    changes.append(f"{field_names[field]} alterado de {old_value} para {new_value}")
                    logger.info(f"Alteração detectada: {field_names[field]} de {old_value} para {new_value}")
            else:
                # Para campos não monetários
                changes.append(f"{field_names[field]} alterado de {old_value} para {new_value}")
                logger.info(f"Alteração detectada: {field_names[field]} de {old_value} para {new_value}")
        else:
            # Comparar outros tipos
            if old_value != new_value:
                changes.append(f"{field_names[field]} alterado de {old_value} para {new_value}")
                logger.info(f"Alteração detectada: {field_names[field]} de {old_value} para {new_value}")
    
    return changes

@router.get("/new", response_class=HTMLResponse)
async def new_basic_data_page(
    request: Request,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Obter o mês e ano atual
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    # Verificar se já existe um registro para o mês atual
    result = await db.execute(
        select(BasicData)
        .filter(
            BasicData.user_id == current_user.id,
            BasicData.month == current_month,
            BasicData.year == current_year
        )
    )
    existing_data = result.scalar_one_or_none()

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
    ideal_service_profit_margin: float = Form(None),
    is_current: str = Form(False),
    edit_mode: bool = Form(False)
):
    try:
        # Verificar se is_current é uma string ou um booleano
        if isinstance(is_current, str):
            is_current_bool = is_current.lower() == 'true'
        else:
            is_current_bool = bool(is_current)
            
        logger.info(f"Processando dados básicos para usuário {current_user.id} em modo {'edição' if edit_mode else 'criação'}")
        
        # Log dos valores recebidos antes da conversão
        logger.info(f"Valores recebidos (antes da conversão):")
        logger.info(f"- month: {month}, year: {year}, clients_served: {clients_served}")
        logger.info(f"- sales_revenue: '{sales_revenue}'")
        logger.info(f"- sales_expenses: '{sales_expenses}'")
        logger.info(f"- input_product_expenses: '{input_product_expenses}'")
        logger.info(f"- fixed_costs: '{fixed_costs}'")
        logger.info(f"- pro_labore: '{pro_labore}'")
        logger.info(f"- other_fixed_costs: '{other_fixed_costs}'")
        
        # Converter valores monetários de string para float
        sales_revenue_float = float(sales_revenue.replace('R$', '').replace('.', '').replace(',', '.').strip())
        sales_expenses_float = float(sales_expenses.replace('R$', '').replace('.', '').replace(',', '.').strip())
        input_product_expenses_float = float(input_product_expenses.replace('R$', '').replace('.', '').replace(',', '.').strip())
        
        # Converter outros valores monetários se fornecidos
        fixed_costs_float = None
        if fixed_costs:
            fixed_costs_float = float(fixed_costs.replace('R$', '').replace('.', '').replace(',', '.').strip())
            
        pro_labore_float = None
        if pro_labore:
            pro_labore_float = float(pro_labore.replace('R$', '').replace('.', '').replace(',', '.').strip())
            
        other_fixed_costs_float = None
        if other_fixed_costs:
            other_fixed_costs_float = float(other_fixed_costs.replace('R$', '').replace('.', '').replace(',', '.').strip())
        
        # Log dos valores após a conversão
        logger.info(f"Valores convertidos (após a conversão):")
        logger.info(f"- sales_revenue_float: {sales_revenue_float}")
        logger.info(f"- sales_expenses_float: {sales_expenses_float}")
        logger.info(f"- input_product_expenses_float: {input_product_expenses_float}")
        logger.info(f"- fixed_costs_float: {fixed_costs_float}")
        logger.info(f"- pro_labore_float: {pro_labore_float}")
        logger.info(f"- other_fixed_costs_float: {other_fixed_costs_float}")
        
        # Preparar os dados para atualização/inserção
        data_dict = {
            'month': month,
            'year': year,
            'clients_served': clients_served,
            'sales_revenue': sales_revenue_float,
            'sales_expenses': sales_expenses_float,
            'input_product_expenses': input_product_expenses_float,
            'fixed_costs': fixed_costs_float,
            'ideal_profit_margin': ideal_profit_margin,
            'service_capacity': service_capacity,
            'pro_labore': pro_labore_float,
            'work_hours_per_week': work_hours_per_week,
            'other_fixed_costs': other_fixed_costs_float,
            'ideal_service_profit_margin': ideal_service_profit_margin,
            'is_current': is_current_bool,
            'activity_type': current_user.activity_type
        }
        
        # Log dos dados que serão salvos
        logger.info(f"Dados que serão salvos no banco:")
        logger.info(f"- month: {data_dict['month']}, year: {data_dict['year']}, clients_served: {data_dict['clients_served']}")
        logger.info(f"- sales_revenue: {data_dict['sales_revenue']}")
        logger.info(f"- sales_expenses: {data_dict['sales_expenses']}")
        logger.info(f"- input_product_expenses: {data_dict['input_product_expenses']}")
        logger.info(f"- fixed_costs: {data_dict['fixed_costs']}")
        logger.info(f"- pro_labore: {data_dict['pro_labore']}")
        logger.info(f"- other_fixed_costs: {data_dict['other_fixed_costs']}")
        
        # Se estiver em modo de edição, buscar o registro existente pelo mês/ano
        if edit_mode:
            logger.info(f"Modo de edição ativado para mês {month}/{year}")
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
                # Armazenar dados antigos para log
                old_data_dict = {
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
                
                # Atualizar os campos
                for key, value in data_dict.items():
                    setattr(existing_data, key, value)
                
                # Registrar as alterações
                changes = compare_and_log_changes(db, old_data_dict, data_dict)
                
                # Criar log de alterações
                if changes:
                    for change in changes:
                        log_entry = BasicDataLog(
                            basic_data_id=existing_data.id,
                            change_description=change,
                            created_at=datetime.now()
                        )
                        db.add(log_entry)
                
                await db.commit()
                await db.refresh(existing_data)
                
                # Redirecionar para a página de listagem de dados básicos
                logger.info("Redirecionando para /basic-data/ após edição")
                return RedirectResponse(
                    url="/basic-data/",
                    status_code=status.HTTP_303_SEE_OTHER
                )
            else:
                logger.error(f"Registro não encontrado para edição: mês {month}/{year}")
                return templates.TemplateResponse(
                    "basic_data_form.html",
                    {
                        "request": request,
                        "user": current_user,
                        "error_message": "Registro não encontrado para edição.",
                        "current_month": month,
                        "current_year": year
                    }
                )
        else:
            # Se não estiver em modo de edição, verificar se já existe registro
            logger.info(f"Verificando se já existe registro para mês {month}/{year}")
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
                logger.warning(f"Já existe registro para mês {month}/{year}")
                return templates.TemplateResponse(
                    "basic_data_form.html",
                    {
                        "request": request,
                        "user": current_user,
                        "error_message": f"Já existe um registro para {calendar.month_name[month]}/{year}. Use a opção de edição.",
                        "current_month": month,
                        "current_year": year
                    }
                )

            # Criar novo registro
            logger.info(f"Criando novo registro para mês {month}/{year}")
            new_basic_data = BasicData(
                user_id=current_user.id,
                **data_dict
            )
            db.add(new_basic_data)
            await db.commit()
            await db.refresh(new_basic_data)
            
            logger.info(f"Registro criado com sucesso. ID: {new_basic_data.id}")
            
            # Registrar cada campo no histórico separadamente
            # Registrar mês e ano
            month_log = BasicDataLog(
                basic_data_id=new_basic_data.id,
                change_description=f"Mês/Ano definido como {calendar.month_name[month]}/{year}"
            )
            db.add(month_log)
            
            # Registrar clientes atendidos
            clients_log = BasicDataLog(
                basic_data_id=new_basic_data.id,
                change_description=f"Clientes atendidos definido como {clients_served}"
            )
            db.add(clients_log)
            
            # Registrar faturamento
            revenue_log = BasicDataLog(
                basic_data_id=new_basic_data.id,
                change_description=f"Faturamento com vendas definido como R$ {sales_revenue_float:,.2f}"
            )
            db.add(revenue_log)
            
            # Registrar gastos com vendas
            expenses_log = BasicDataLog(
                basic_data_id=new_basic_data.id,
                change_description=f"Gastos com vendas definido como R$ {sales_expenses_float:,.2f}"
            )
            db.add(expenses_log)
            
            # Registrar gastos com insumos
            input_log = BasicDataLog(
                basic_data_id=new_basic_data.id,
                change_description=f"Gastos com insumos e produtos definido como R$ {input_product_expenses_float:,.2f}"
            )
            db.add(input_log)
            
            # Registrar custos fixos (se aplicável)
            if fixed_costs_float is not None:
                fixed_costs_log = BasicDataLog(
                    basic_data_id=new_basic_data.id,
                    change_description=f"Custos fixos definido como R$ {fixed_costs_float:,.2f}"
                )
                db.add(fixed_costs_log)
            
            # Registrar margem de lucro ideal (se aplicável)
            if ideal_profit_margin is not None:
                margin_log = BasicDataLog(
                    basic_data_id=new_basic_data.id,
                    change_description=f"Margem de lucro ideal definida como {ideal_profit_margin}%"
                )
                db.add(margin_log)
            
            # Registrar capacidade de atendimento (se aplicável)
            if service_capacity:
                capacity_log = BasicDataLog(
                    basic_data_id=new_basic_data.id,
                    change_description=f"Capacidade de atendimento definida como {service_capacity}"
                )
                db.add(capacity_log)
            
            # Registrar pró-labore (se aplicável)
            if pro_labore_float is not None:
                pro_labore_log = BasicDataLog(
                    basic_data_id=new_basic_data.id,
                    change_description=f"Pró-labore definido como R$ {pro_labore_float:,.2f}"
                )
                db.add(pro_labore_log)
            
            # Registrar horas de trabalho por semana (se aplicável)
            if work_hours_per_week is not None:
                hours_log = BasicDataLog(
                    basic_data_id=new_basic_data.id,
                    change_description=f"Horas de trabalho por semana definidas como {work_hours_per_week}"
                )
                db.add(hours_log)
            
            # Registrar demais custos fixos (se aplicável)
            if other_fixed_costs_float is not None:
                other_costs_log = BasicDataLog(
                    basic_data_id=new_basic_data.id,
                    change_description=f"Demais custos fixos definidos como R$ {other_fixed_costs_float:,.2f}"
                )
                db.add(other_costs_log)
            
            # Registrar margem de lucro ideal para serviços (se aplicável)
            if ideal_service_profit_margin is not None:
                service_margin_log = BasicDataLog(
                    basic_data_id=new_basic_data.id,
                    change_description=f"Margem de lucro ideal para serviços definida como {ideal_service_profit_margin}%"
                )
                db.add(service_margin_log)
            
            # Salvar todos os logs
            await db.commit()

            # Redirecionar para a página de listagem de dados básicos
            logger.info("Redirecionando para /basic-data/")
            return RedirectResponse(
                url="/basic-data/",
                status_code=status.HTTP_303_SEE_OTHER
            )
        
    except Exception as e:
        logger.error(f"Erro ao salvar dados básicos: {str(e)}")
        return templates.TemplateResponse(
            "basic_data_form.html",
            {
                "request": request,
                "user": current_user,
                "error_message": f"Erro ao salvar dados: {str(e)}",
                "current_month": month,
                "current_year": year
            }
        )

@router.get("/edit/{data_id}", response_class=HTMLResponse)
async def edit_basic_data_page(
    request: Request,
    data_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    per_page: int = 10
):
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
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    
    # Buscar logs do registro
    result = await db.execute(
        select(BasicDataLog)
        .filter(BasicDataLog.basic_data_id == data_id)
        .order_by(BasicDataLog.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    logs = result.scalars().all()
    
    # Contar total de logs para paginação
    result = await db.execute(
        select(BasicDataLog)
        .filter(BasicDataLog.basic_data_id == data_id)
    )
    total_logs = len(result.scalars().all())
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

@router.get("/check/{year}/{month}")
async def check_basic_data_exists(
    year: int,
    month: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
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
    
    return {"exists": existing_data is not None} 