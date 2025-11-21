"""
Rotas para Categoria
"""
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel

from app.database.db import get_db
from app.models.user import User
from app.models.categoria import Categoria
from app.routes.auth import get_current_user

router = APIRouter(prefix="/categoria")
templates = Jinja2Templates(directory="app/templates")

class CategoriaCreate(BaseModel):
    nome: str
    codigo: str

@router.get("/api/list")
async def list_categorias(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lista todas as categorias do usuário"""
    if not current_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    result = await db.execute(
        select(Categoria).filter(Categoria.user_id == current_user.id)
    )
    categorias = result.scalars().all()
    
    return [{
        "codigo": cat.codigo,
        "nome": cat.nome,
        "user_id": cat.user_id
    } for cat in categorias]

@router.post("/api/create")
async def create_categoria(
    request: Request,
    nome: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cria uma nova categoria"""
    if not current_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    # Código será gerado automaticamente pelo auto incremento
    nova_categoria = Categoria(
        nome=nome,
        user_id=current_user.id
    )
    
    db.add(nova_categoria)
    await db.commit()
    await db.refresh(nova_categoria)
    
    return JSONResponse({
        "codigo": nova_categoria.codigo,
        "nome": nova_categoria.nome,
        "user_id": nova_categoria.user_id
    })

@router.put("/api/update/{categoria_codigo}")
async def update_categoria(
    categoria_codigo: int,
    request: Request,
    nome: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Atualiza uma categoria existente"""
    if not current_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    result = await db.execute(
        select(Categoria).filter(
            and_(
                Categoria.codigo == categoria_codigo,
                Categoria.user_id == current_user.id
            )
        )
    )
    categoria = result.scalar_one_or_none()
    
    if not categoria:
        return JSONResponse({"error": "Categoria não encontrada"}, status_code=404)
    
    # Atualizar apenas o nome (código não pode ser alterado pois é chave primária)
    categoria.nome = nome
    
    await db.commit()
    await db.refresh(categoria)
    
    return JSONResponse({
        "codigo": categoria.codigo,
        "nome": categoria.nome,
        "user_id": categoria.user_id
    })

@router.delete("/api/delete/{categoria_codigo}")
async def delete_categoria(
    categoria_codigo: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove uma categoria"""
    if not current_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    result = await db.execute(
        select(Categoria).filter(
            and_(
                Categoria.codigo == categoria_codigo,
                Categoria.user_id == current_user.id
            )
        )
    )
    categoria = result.scalar_one_or_none()
    
    if not categoria:
        return JSONResponse({"error": "Categoria não encontrada"}, status_code=404)
    
    await db.delete(categoria)
    await db.commit()
    
    return JSONResponse({"message": "Categoria removida com sucesso"})

@router.get("/api/get/{categoria_codigo}")
async def get_categoria(
    categoria_codigo: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtém uma categoria específica"""
    if not current_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    result = await db.execute(
        select(Categoria).filter(
            and_(
                Categoria.codigo == categoria_codigo,
                Categoria.user_id == current_user.id
            )
        )
    )
    categoria = result.scalar_one_or_none()
    
    if not categoria:
        return JSONResponse({"error": "Categoria não encontrada"}, status_code=404)
    
    return JSONResponse({
        "codigo": categoria.codigo,
        "nome": categoria.nome,
        "user_id": categoria.user_id
    })

