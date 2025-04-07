from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import logging
import os

from app.database.db import get_db
from app.models.user import User
from app.models.basic_data import BasicData
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

@router.get("/", response_class=HTMLResponse)
async def basic_data_page(
    request: Request,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Buscar dados básicos do usuário com ordenação correta
        result = await db.execute(
            select(BasicData)
            .filter(BasicData.user_id == current_user.id)
            .order_by(BasicData.year.desc(), BasicData.month.desc())
        )
        basic_data = result.scalars().all()

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

@router.post("/delete/{data_id}")
async def delete_basic_data(
    request: Request,
    data_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
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
    
    # Excluir o registro
    await db.delete(basic_data)
    await db.commit()
    
    return RedirectResponse(
        url="/basic-data",
        status_code=status.HTTP_303_SEE_OTHER
    ) 