from fastapi import APIRouter, Depends, HTTPException, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.database.db import get_db
from app.models.user import User
from app.routes.dashboard import get_current_user
from app.utils.auth import get_password_hash

router = APIRouter(prefix="/admin")

templates = Jinja2Templates(directory="app/templates")

# Middleware para verificar se o usuário é administrador
async def admin_required(request: Request, current_user = Depends(get_current_user)):
    if not current_user or current_user.access_level != "Administrador":
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return current_user

# Rota para listar todos os usuários
@router.get("/users", response_class=HTMLResponse)
async def list_users(
    request: Request, 
    current_user = Depends(admin_required),
    db: Session = Depends(get_db),
    success_message: Optional[str] = None,
    error_message: Optional[str] = None
):
    users = db.query(User).all()
    return templates.TemplateResponse(
        "admin_users.html", 
        {
            "request": request, 
            "user": current_user, 
            "users": users,
            "success_message": success_message,
            "error_message": error_message
        }
    )

# Rota para adicionar um novo usuário
@router.post("/users/add", response_class=HTMLResponse)
async def add_user(
    request: Request,
    email: str = Form(...),
    whatsapp: str = Form(...),
    activity_type: str = Form(...),
    password: str = Form(...),
    status: str = Form(...),
    access_level: str = Form(...),
    current_user = Depends(admin_required),
    db: Session = Depends(get_db)
):
    # Verificar se o email já está em uso
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        return await list_users(
            request, 
            current_user, 
            db, 
            error_message=f"Email {email} já está em uso."
        )
    
    # Criar novo usuário
    hashed_password = get_password_hash(password)
    new_user = User(
        email=email,
        whatsapp=whatsapp,
        activity_type=activity_type,
        password=hashed_password,
        status=status,
        access_level=access_level,
        registration_date=datetime.now(),
        terms_accepted=True  # Admins podem criar contas sem aceitar os termos
    )
    
    # Adicionar e salvar no banco de dados
    try:
        db.add(new_user)
        db.commit()
        return RedirectResponse(
            url="/admin/users?success_message=Usuário adicionado com sucesso", 
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        db.rollback()
        return await list_users(
            request, 
            current_user, 
            db, 
            error_message=f"Erro ao adicionar usuário: {str(e)}"
        )

# Rota para editar um usuário existente
@router.post("/users/edit", response_class=HTMLResponse)
async def edit_user(
    request: Request,
    user_id: int = Form(...),
    email: str = Form(...),
    whatsapp: str = Form(...),
    activity_type: str = Form(...),
    password: str = Form(None),
    status: str = Form(...),
    access_level: str = Form(...),
    current_user = Depends(admin_required),
    db: Session = Depends(get_db)
):
    # Buscar o usuário a ser editado
    user_to_edit = db.query(User).filter(User.id == user_id).first()
    if not user_to_edit:
        return await list_users(
            request, 
            current_user, 
            db, 
            error_message=f"Usuário com ID {user_id} não encontrado."
        )
    
    # Verificar se o email já está em uso por outro usuário
    if email != user_to_edit.email:
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            return await list_users(
                request, 
                current_user, 
                db, 
                error_message=f"Email {email} já está em uso por outro usuário."
            )
    
    # Atualizar dados do usuário
    user_to_edit.email = email
    user_to_edit.whatsapp = whatsapp
    user_to_edit.activity_type = activity_type
    user_to_edit.status = status
    user_to_edit.access_level = access_level
    
    # Atualizar senha apenas se fornecida
    if password and password.strip():
        user_to_edit.password = get_password_hash(password)
    
    # Salvar alterações
    try:
        db.commit()
        return RedirectResponse(
            url="/admin/users?success_message=Usuário atualizado com sucesso", 
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        db.rollback()
        return await list_users(
            request, 
            current_user, 
            db, 
            error_message=f"Erro ao atualizar usuário: {str(e)}"
        )

# Rota para excluir um usuário
@router.post("/users/delete", response_class=HTMLResponse)
async def delete_user(
    request: Request,
    user_id: int = Form(...),
    current_user = Depends(admin_required),
    db: Session = Depends(get_db)
):
    # Não permitir excluir o próprio usuário
    if current_user.id == user_id:
        return await list_users(
            request, 
            current_user, 
            db, 
            error_message="Você não pode excluir seu próprio usuário."
        )
    
    # Buscar o usuário a ser excluído
    user_to_delete = db.query(User).filter(User.id == user_id).first()
    if not user_to_delete:
        return await list_users(
            request, 
            current_user, 
            db, 
            error_message=f"Usuário com ID {user_id} não encontrado."
        )
    
    # Excluir o usuário
    try:
        db.delete(user_to_delete)
        db.commit()
        return RedirectResponse(
            url="/admin/users?success_message=Usuário excluído com sucesso", 
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        db.rollback()
        return await list_users(
            request, 
            current_user, 
            db, 
            error_message=f"Erro ao excluir usuário: {str(e)}"
        ) 