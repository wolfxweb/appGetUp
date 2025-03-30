from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.database.db import get_db
from app.models.user import User
from app.utils.auth import SECRET_KEY, ALGORITHM

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
async def dashboard(request: Request, current_user = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse(
        "dashboard.html", 
        {"request": request, "user": current_user}
    ) 