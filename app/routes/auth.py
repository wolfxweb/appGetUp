from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
from jose import jwt, JWTError

from app.database.db import get_db
from app.models.user import User
from app.utils.auth import verify_password, get_password_hash, create_access_token, SECRET_KEY, ALGORITHM
from app.utils.email import send_password_reset_email

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
    
    # Use the provided database session
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        return None
    
    return user

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {
        "request": request,
        "user": None,  # Explicitamente passar None para o usuário
        "now": datetime.now()
    })

@router.post("/register")
async def register(
    request: Request,
    response: Response,
    email: str = Form(...),
    whatsapp: str = Form(...),
    activity_type: str = Form(...),
    password: str = Form(...),
    activation_key: str = Form(None),
    terms_accepted: bool = Form(False),
    db: Session = Depends(get_db)
):
    # Verificar se o email já está em uso
    user_exists = db.query(User).filter(User.email == email).first()
    if user_exists:
        return templates.TemplateResponse(
            "register.html", 
            {
                "request": request, 
                "error": "Email já cadastrado",
                "now": datetime.now()  # Adicionar now ao contexto
            }
        )
    
    if not terms_accepted:
        return templates.TemplateResponse(
            "register.html", 
            {
                "request": request, 
                "error": "Você deve aceitar os termos para continuar",
                "now": datetime.now()  # Adicionar now ao contexto
            }
        )
    
    # Criar novo usuário
    hashed_password = get_password_hash(password)
    new_user = User(
        email=email,
        whatsapp=whatsapp,
        activity_type=activity_type,
        password=hashed_password,
        activation_key=activation_key,
        registration_date=datetime.now(),
        terms_accepted=terms_accepted
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Criar token de acesso
    access_token = create_access_token(
        data={"sub": email}
    )
    
    # Configurar cookie com o token
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=1800,
        samesite="lax"
    )
    
    return response

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "user": None  # Explicitamente passar None para o usuário
    })

@router.post("/login")
async def login(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    
    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "Email ou senha incorretos"}
        )
    
    # Criar token de acesso
    access_token = create_access_token(
        data={"sub": user.email}
    )
    
    # Configurar cookie com o token
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=1800,
        samesite="lax"
    )
    
    return response

@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@router.post("/forgot-password")
async def forgot_password(
    request: Request,
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        return templates.TemplateResponse(
            "forgot_password.html", 
            {"request": request, "error": "Email não encontrado"}
        )
    
    # Gerar token para reset de senha
    reset_token = create_access_token(
        data={"sub": user.email, "reset": True},
        expires_delta=timedelta(hours=1)
    )
    
    # Enviar email com o token
    success = await send_password_reset_email(user.email, reset_token)
    
    if success:
        return templates.TemplateResponse(
            "forgot_password.html", 
            {"request": request, "success": "Um email com instruções foi enviado para você"}
        )
    else:
        return templates.TemplateResponse(
            "forgot_password.html", 
            {"request": request, "error": "Erro ao enviar email. Tente novamente mais tarde."}
        )

@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, token: str):
    return templates.TemplateResponse("reset_password.html", {"request": request, "token": token})

@router.post("/reset-password")
async def reset_password(
    request: Request,
    token: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        reset = payload.get("reset")
        
        if not email or not reset:
            raise HTTPException(status_code=400, detail="Token inválido")
        
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        # Atualizar senha
        hashed_password = get_password_hash(new_password)
        user.password = hashed_password
        db.commit()
        
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "success": "Senha atualizada com sucesso. Faça login com sua nova senha."}
        )
    
    except JWTError:
        return templates.TemplateResponse(
            "reset_password.html", 
            {"request": request, "error": "Token expirado ou inválido", "token": token}
        )

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response 