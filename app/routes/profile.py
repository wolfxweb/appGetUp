from fastapi import APIRouter, Depends, HTTPException, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from app.database.db import get_db
from app.models.user import User
from app.routes.dashboard import get_current_user
from app.utils.auth import verify_password, get_password_hash

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request, 
    current_user = Depends(get_current_user),
    success_message: Optional[str] = None,
    error_message: Optional[str] = None
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse(
        "profile.html", 
        {
            "request": request,
            "user": current_user,
            "success_message": success_message,
            "error_message": error_message
        }
    )

@router.post("/profile/edit", response_class=HTMLResponse)
async def edit_profile(
    request: Request,
    email: str = Form(...),
    whatsapp: str = Form(...),
    activity_type: str = Form(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    # Verificar se o email já está em uso por outro usuário
    if email != current_user.email:
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            return templates.TemplateResponse(
                "profile.html", 
                {
                    "request": request,
                    "user": current_user,
                    "error_message": f"Email {email} já está em uso por outro usuário."
                }
            )
    
    # Atualizar dados do usuário
    current_user.email = email
    current_user.whatsapp = whatsapp
    current_user.activity_type = activity_type
    
    # Salvar alterações
    try:
        db.commit()
        # Obter o usuário atualizado para exibir no template
        updated_user = db.query(User).filter(User.id == current_user.id).first()
        return templates.TemplateResponse(
            "profile.html", 
            {
                "request": request,
                "user": updated_user,
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
                "error_message": f"Erro ao atualizar perfil: {str(e)}"
            }
        )

@router.post("/profile/password", response_class=HTMLResponse)
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    # Verificar se a senha atual está correta
    if not verify_password(current_password, current_user.password):
        return templates.TemplateResponse(
            "profile.html", 
            {
                "request": request,
                "user": current_user,
                "error_message": "Senha atual incorreta."
            }
        )
    
    # Verificar se as senhas novas coincidem
    if new_password != confirm_password:
        return templates.TemplateResponse(
            "profile.html", 
            {
                "request": request,
                "user": current_user,
                "error_message": "A nova senha e a confirmação não coincidem."
            }
        )
    
    # Atualizar a senha
    current_user.password = get_password_hash(new_password)
    
    # Salvar alterações
    try:
        db.commit()
        return templates.TemplateResponse(
            "profile.html", 
            {
                "request": request,
                "user": current_user,
                "success_message": "Senha alterada com sucesso!"
            }
        )
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            "profile.html", 
            {
                "request": request,
                "user": current_user,
                "error_message": f"Erro ao alterar senha: {str(e)}"
            }
        ) 