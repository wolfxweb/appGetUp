from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
    db: AsyncSession = Depends(get_db)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    # Garantir que a data de registro esteja definida
    if not current_user.registration_date:
        current_user.registration_date = datetime.now()
        await db.commit()

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
    company_activity: str = Form(None),
    specialty_area: str = Form(None),
    name: str = Form(None),
    gender: str = Form(None),
    birth_day: int = Form(None),
    birth_month: int = Form(None),
    married: str = Form(None),
    children: str = Form(None),
    grandchildren: str = Form(None),
    cep: str = Form(None),
    street: str = Form(None),
    neighborhood: str = Form(None),
    state: str = Form(None),
    city: str = Form(None),
    complement: str = Form(None),
    activation_key: str = Form(None),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    try:
        # Garantir que a data de registro esteja definida
        if not current_user.registration_date:
            current_user.registration_date = datetime.now()

        if action == "activate" and activation_key:
            # Verificar se a chave existe e está disponível
            result = await db.execute(select(License).filter(
                License.activation_key == activation_key,
                License.status == "Disponível"
            ))
            license = result.scalar_one_or_none()

            if not license:
                return templates.TemplateResponse(
                    "profile.html",
                    {
                        "request": request,
                        "user": current_user,
                        "error": "Chave de ativação não encontrada ou já utilizada"
                    }
                )

            # Atualizar apenas o status e a data de ativação da licença
            license.status = "Utilizada"
            license.activation_date = datetime.now()
            license.activation_email = email

            # Atualizar o usuário com a chave de ativação
            current_user.activation_key = activation_key

            try:
                await db.commit()
                return templates.TemplateResponse(
                    "profile.html",
                    {
                        "request": request,
                        "user": current_user,
                        "success": "Licença ativada com sucesso!"
                    }
                )
            except Exception as e:
                await db.rollback()
                return templates.TemplateResponse(
                    "profile.html",
                    {
                        "request": request,
                        "user": current_user,
                        "error": f"Erro ao ativar a licença: {str(e)}"
                    }
                )

        elif action == "update":
            # Atualizar informações do usuário
            current_user.name = name
            current_user.whatsapp = whatsapp
            current_user.activity_type = activity_type
            current_user.company_activity = company_activity
            current_user.specialty_area = specialty_area
            current_user.gender = gender
            current_user.birth_day = birth_day
            current_user.birth_month = birth_month
            current_user.married = married
            current_user.children = children
            current_user.grandchildren = grandchildren
            current_user.cep = cep
            current_user.street = street
            current_user.neighborhood = neighborhood
            current_user.state = state
            current_user.city = city
            current_user.complement = complement

            try:
                await db.commit()
                return templates.TemplateResponse(
                    "profile.html",
                    {
                        "request": request,
                        "user": current_user,
                        "success": "Perfil atualizado com sucesso!"
                    }
                )
            except Exception as e:
                await db.rollback()
                return templates.TemplateResponse(
                    "profile.html",
                    {
                        "request": request,
                        "user": current_user,
                        "error": f"Erro ao atualizar o perfil: {str(e)}"
                    }
                )

    except Exception as e:
        await db.rollback()
        return templates.TemplateResponse(
            "profile.html",
            {
                "request": request,
                "user": current_user,
                "error": f"Erro ao processar a requisição: {str(e)}"
            }
        ) 