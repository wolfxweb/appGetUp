from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime

from app.database.db import get_db
from app.models.user import User
from app.models.license import License
from app.routes.auth import get_current_user
from app.utils.auth import SECRET_KEY, ALGORITHM, verify_password, get_password_hash

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

# Dependência para obter o usuário atual
async def get_current_user(request: Request, db: Session = Depends(get_db)):
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
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        return None
    
    return user

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Se o usuário não tiver uma chave de ativação, mostrar apenas a mensagem de ativação
    if not current_user.activation_key:
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "user": current_user
            }
        )

    # Para usuários com licença ativa, mostrar as estatísticas
    total_users = db.query(User).count()
    active_licenses = db.query(License).filter(License.status == "Utilizada").count()
    available_licenses = db.query(License).filter(License.status == "Disponível").count()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": current_user,
            "total_users": total_users,
            "active_licenses": active_licenses,
            "available_licenses": available_licenses
        }
    )

@router.post("/activate-license")
async def activate_license(
    request: Request,
    activation_key: str = Form(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verificar se a chave existe e está disponível
    license = db.query(License).filter(
        License.activation_key == activation_key,
        License.status == "Disponível"
    ).first()

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
    license.user_email = current_user.email
    license.activation_date = datetime.now()

    # Atualizar o usuário
    current_user.activation_key = activation_key

    db.commit()

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER) 