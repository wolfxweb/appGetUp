from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt
from datetime import datetime
import logging

from app.database.db import get_db
from app.models.user import User
from app.models.license import License
from app.routes.auth import get_current_user
from app.utils.auth import SECRET_KEY, ALGORITHM, verify_password, get_password_hash

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

logger = logging.getLogger(__name__)

# Dependência para obter o usuário atual
async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não autorizado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    try:
        token_type, token_value = token.split()
        if token_type.lower() != "bearer":
            return None
        
        payload = jwt.decode(token_value, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            return None
        
    except (JWTError, ValueError):
        return None
    
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        return None
    
    return user

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Logs de depuração para verificar o usuário
    logger.warning(f"Dashboard Access - User: {current_user}")
    logger.warning(f"Dashboard Access - User Access Level: {current_user.access_level}")

    # Se o usuário não tiver uma chave de ativação, mostrar apenas a mensagem de ativação
    if not current_user.activation_key:
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "user": current_user
            }
        )

    # Para administradores, mostrar as estatísticas
    template_context = {
        "request": request,
        "user": current_user
    }

    if current_user.access_level in ["Administrador", "Administrador"]:
        total_users = await db.execute(select(User).count())
        active_licenses = await db.execute(select(License).filter(License.status == "Utilizada").count())
        available_licenses = await db.execute(select(License).filter(License.status == "Disponível").count())

        # Logs de depuração
        logger.warning(f"Dashboard Statistics - Total Users: {total_users.scalar()}")
        logger.warning(f"Dashboard Statistics - Active Licenses: {active_licenses.scalar()}")
        logger.warning(f"Dashboard Statistics - Available Licenses: {available_licenses.scalar()}")

        template_context.update({
            "total_users": total_users.scalar(),
            "active_licenses": active_licenses.scalar(),
            "available_licenses": available_licenses.scalar()
        })

    return templates.TemplateResponse(
        "dashboard.html",
        template_context
    )

@router.post("/activate-license")
async def activate_license(
    request: Request,
    activation_key: str = Form(...),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Logs de depuração
    logger.warning(f"License Activation - Current User: {current_user}")
    logger.warning(f"License Activation - Current User Email: {current_user.email}")
    logger.warning(f"License Activation - Activation Key: {activation_key}")

    # Verificar se a chave existe e está disponível
    result = await db.execute(select(License).filter(
        License.activation_key == activation_key,
        License.status == "Disponível"
    ))
    license = result.scalar_one_or_none()

    # Logs de depuração da licença
    logger.warning(f"License Activation - License Found: {license}")

    if not license:
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "user": current_user,
                "error_message": "Chave de ativação inválida ou já utilizada"
            }
        )

    # Atualizar a licença
    license.status = "Utilizada"
    license.activation_email = current_user.email
    license.activation_date = datetime.now()

    # Logs de depuração após atualização
    logger.warning(f"License Activation - Updated License Activation Email: {license.activation_email}")

    # Atualizar o usuário
    current_user.activation_key = activation_key

    await db.commit()

    # Log final
    logger.warning(f"License Activation - Completed for User: {current_user.email}")

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER) 