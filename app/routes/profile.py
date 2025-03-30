from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.db import get_db
from app.models.user import User
from app.models.license import License
from app.routes.auth import get_current_user

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Garantir que a data de registro esteja definida
    if not current_user.registration_date:
        current_user.registration_date = datetime.now()
        db.commit()

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": current_user
        }
    )

@router.post("/profile/update")
async def update_profile(
    request: Request,
    action: str = Form(...),
    email: str = Form(...),
    whatsapp: str = Form(...),
    activity_type: str = Form(...),
    activation_key: str = Form(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Garantir que a data de registro esteja definida
    if not current_user.registration_date:
        current_user.registration_date = datetime.now()

    if action == "activate" and activation_key:
        # Verificar se a chave existe e está disponível
        license = db.query(License).filter(
            License.activation_key == activation_key
        ).first()

        if not license:
            return templates.TemplateResponse(
                "profile.html",
                {
                    "request": request,
                    "user": current_user,
                    "error_message": "Chave de ativação não encontrada"
                }
            )

        if license.status != "Disponível":
            return templates.TemplateResponse(
                "profile.html",
                {
                    "request": request,
                    "user": current_user,
                    "error_message": "Esta chave de ativação já foi utilizada"
                }
            )

        # Atualizar a licença
        license.status = "Utilizada"
        license.activation_email = email
        license.activation_date = datetime.now()

        # Atualizar o usuário
        current_user.activation_key = activation_key

        try:
            db.commit()
            return templates.TemplateResponse(
                "profile.html",
                {
                    "request": request,
                    "user": current_user,
                    "success_message": "Licença ativada com sucesso!"
                }
            )
        except Exception as e:
            db.rollback()
            return templates.TemplateResponse(
                "profile.html",
                {
                    "request": request,
                    "user": current_user,
                    "error_message": "Erro ao ativar a licença. Tente novamente."
                }
            )

    elif action == "update":
        # Atualizar informações básicas
        current_user.whatsapp = whatsapp
        current_user.activity_type = activity_type

        try:
            db.commit()
            return templates.TemplateResponse(
                "profile.html",
                {
                    "request": request,
                    "user": current_user,
                    "success_message": "Perfil atualizado com sucesso!"
                }
            )
        except Exception as e:
            db.rollback()
            return templates.TemplateResponse(
                "profile.html",
                {
                    "request": request,
                    "user": current_user,
                    "error_message": "Erro ao atualizar o perfil. Tente novamente."
                }
            ) 