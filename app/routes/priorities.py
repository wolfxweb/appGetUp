from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.basic_data import BasicData
from app.routes.auth import get_current_user

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

@router.get("/gestao-prioridades", response_class=HTMLResponse)
async def priorities_page(
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Buscar dados básicos do usuário
    basic_data_list = db.query(BasicData).filter(
        BasicData.user_id == current_user.id
    ).order_by(
        BasicData.year.desc(),
        BasicData.month.desc()
    ).all()

    return templates.TemplateResponse(
        "gestao_prioridades.html",
        {
            "request": request,
            "user": current_user,
            "basic_data_list": basic_data_list
        }
    ) 