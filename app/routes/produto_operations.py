"""
Rotas para Operações de Produto
"""
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional

from app.database.db import get_db
from app.models.user import User
from app.models.produto import Produto
from app.models.categoria import Categoria
from app.models.basic_data import BasicData
from app.routes.auth import get_current_user

router = APIRouter(prefix="/produto")
templates = Jinja2Templates(directory="app/templates")

@router.get("/api/list")
async def list_produtos(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lista todos os produtos do usuário"""
    if not current_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    result = await db.execute(
        select(Produto).filter(Produto.user_id == current_user.id)
    )
    produtos = result.scalars().all()
    
    return [{
        "codigo": prod.codigo,
        "nome": prod.nome,
        "categoria_codigo": prod.categoria_codigo,
        "basic_data_id": prod.basic_data_id,
        "faturamento_por_mercadoria": prod.faturamento_por_mercadoria,
        "preco_venda": prod.preco_venda,
        "custo_aquisicao": prod.custo_aquisicao,
        "percentual_faturamento": prod.percentual_faturamento,
        "quantidade_vendas": prod.quantidade_vendas,
        "gastos_com_vendas": prod.gastos_com_vendas,
        "gastos_com_compras": prod.gastos_com_compras,
        "margem_contribuicao_informada": prod.margem_contribuicao_informada,
        "margem_contribuicao_corrigida": prod.margem_contribuicao_corrigida,
        "margem_contribuicao_valor": prod.margem_contribuicao_valor,
        "custos_fixos": prod.custos_fixos,
        "ponto_equilibrio": prod.ponto_equilibrio,
        "margem_operacional": prod.margem_operacional
    } for prod in produtos]

@router.post("/api/create")
async def create_produto(
    request: Request,
    nome: str = Form(...),
    categoria_codigo: Optional[int] = Form(None),
    basic_data_id: Optional[int] = Form(None),
    faturamento_por_mercadoria: Optional[float] = Form(None),
    preco_venda: Optional[float] = Form(None),
    custo_aquisicao: Optional[float] = Form(None),
    percentual_faturamento: Optional[float] = Form(None),
    quantidade_vendas: Optional[float] = Form(None),
    gastos_com_vendas: Optional[float] = Form(None),
    gastos_com_compras: Optional[float] = Form(None),
    margem_contribuicao_informada: Optional[float] = Form(None),
    margem_contribuicao_corrigida: Optional[float] = Form(None),
    margem_contribuicao_valor: Optional[float] = Form(None),
    custos_fixos: Optional[float] = Form(None),
    ponto_equilibrio: Optional[float] = Form(None),
    margem_operacional: Optional[float] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cria um novo produto"""
    if not current_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    novo_produto = Produto(
        nome=nome,
        user_id=current_user.id,
        categoria_codigo=categoria_codigo if categoria_codigo else None,
        basic_data_id=basic_data_id if basic_data_id else None,
        faturamento_por_mercadoria=faturamento_por_mercadoria,
        preco_venda=preco_venda,
        custo_aquisicao=custo_aquisicao,
        percentual_faturamento=percentual_faturamento,
        quantidade_vendas=quantidade_vendas,
        gastos_com_vendas=gastos_com_vendas,
        gastos_com_compras=gastos_com_compras,
        margem_contribuicao_informada=margem_contribuicao_informada,
        margem_contribuicao_corrigida=margem_contribuicao_corrigida,
        margem_contribuicao_valor=margem_contribuicao_valor,
        custos_fixos=custos_fixos,
        ponto_equilibrio=ponto_equilibrio,
        margem_operacional=margem_operacional
    )
    
    db.add(novo_produto)
    await db.commit()
    await db.refresh(novo_produto)
    
    return JSONResponse({
        "codigo": novo_produto.codigo,
        "nome": novo_produto.nome,
        "categoria_codigo": novo_produto.categoria_codigo,
        "basic_data_id": novo_produto.basic_data_id
    })

@router.put("/api/update/{produto_codigo}")
async def update_produto(
    produto_codigo: int,
    request: Request,
    nome: str = Form(...),
    categoria_codigo: Optional[int] = Form(None),
    basic_data_id: Optional[int] = Form(None),
    faturamento_por_mercadoria: Optional[float] = Form(None),
    preco_venda: Optional[float] = Form(None),
    custo_aquisicao: Optional[float] = Form(None),
    percentual_faturamento: Optional[float] = Form(None),
    quantidade_vendas: Optional[float] = Form(None),
    gastos_com_vendas: Optional[float] = Form(None),
    gastos_com_compras: Optional[float] = Form(None),
    margem_contribuicao_informada: Optional[float] = Form(None),
    margem_contribuicao_corrigida: Optional[float] = Form(None),
    margem_contribuicao_valor: Optional[float] = Form(None),
    custos_fixos: Optional[float] = Form(None),
    ponto_equilibrio: Optional[float] = Form(None),
    margem_operacional: Optional[float] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Atualiza um produto existente"""
    if not current_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    result = await db.execute(
        select(Produto).filter(
            and_(
                Produto.codigo == produto_codigo,
                Produto.user_id == current_user.id
            )
        )
    )
    produto = result.scalar_one_or_none()
    
    if not produto:
        return JSONResponse({"error": "Produto não encontrado"}, status_code=404)
    
    # Atualizar campos
    produto.nome = nome
    produto.categoria_codigo = categoria_codigo if categoria_codigo else None
    produto.basic_data_id = basic_data_id if basic_data_id else None
    produto.faturamento_por_mercadoria = faturamento_por_mercadoria
    produto.preco_venda = preco_venda
    produto.custo_aquisicao = custo_aquisicao
    produto.percentual_faturamento = percentual_faturamento
    produto.quantidade_vendas = quantidade_vendas
    produto.gastos_com_vendas = gastos_com_vendas
    produto.gastos_com_compras = gastos_com_compras
    produto.margem_contribuicao_informada = margem_contribuicao_informada
    produto.margem_contribuicao_corrigida = margem_contribuicao_corrigida
    produto.margem_contribuicao_valor = margem_contribuicao_valor
    produto.custos_fixos = custos_fixos
    produto.ponto_equilibrio = ponto_equilibrio
    produto.margem_operacional = margem_operacional
    
    await db.commit()
    await db.refresh(produto)
    
    return JSONResponse({
        "codigo": produto.codigo,
        "nome": produto.nome,
        "categoria_codigo": produto.categoria_codigo,
        "basic_data_id": produto.basic_data_id
    })

@router.delete("/api/delete/{produto_codigo}")
async def delete_produto(
    produto_codigo: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove um produto"""
    if not current_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    result = await db.execute(
        select(Produto).filter(
            and_(
                Produto.codigo == produto_codigo,
                Produto.user_id == current_user.id
            )
        )
    )
    produto = result.scalar_one_or_none()
    
    if not produto:
        return JSONResponse({"error": "Produto não encontrado"}, status_code=404)
    
    await db.delete(produto)
    await db.commit()
    
    return JSONResponse({"message": "Produto removido com sucesso"})

@router.get("/api/get/{produto_codigo}")
async def get_produto(
    produto_codigo: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtém um produto específico"""
    if not current_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    result = await db.execute(
        select(Produto).filter(
            and_(
                Produto.codigo == produto_codigo,
                Produto.user_id == current_user.id
            )
        )
    )
    produto = result.scalar_one_or_none()
    
    if not produto:
        return JSONResponse({"error": "Produto não encontrado"}, status_code=404)
    
    return JSONResponse({
        "codigo": produto.codigo,
        "nome": produto.nome,
        "categoria_codigo": produto.categoria_codigo,
        "basic_data_id": produto.basic_data_id,
        "faturamento_por_mercadoria": produto.faturamento_por_mercadoria,
        "preco_venda": produto.preco_venda,
        "custo_aquisicao": produto.custo_aquisicao,
        "percentual_faturamento": produto.percentual_faturamento,
        "quantidade_vendas": produto.quantidade_vendas,
        "gastos_com_vendas": produto.gastos_com_vendas,
        "gastos_com_compras": produto.gastos_com_compras,
        "margem_contribuicao_informada": produto.margem_contribuicao_informada,
        "margem_contribuicao_corrigida": produto.margem_contribuicao_corrigida,
        "margem_contribuicao_valor": produto.margem_contribuicao_valor,
        "custos_fixos": produto.custos_fixos,
        "ponto_equilibrio": produto.ponto_equilibrio,
        "margem_operacional": produto.margem_operacional
    })

@router.get("/api/categorias")
async def list_categorias_for_produto(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lista categorias para usar no select do produto"""
    if not current_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    result = await db.execute(
        select(Categoria).filter(Categoria.user_id == current_user.id)
    )
    categorias = result.scalars().all()
    
    return [{
        "codigo": cat.codigo,
        "nome": cat.nome
    } for cat in categorias]

@router.get("/api/basic-data")
async def list_basic_data_for_produto(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lista dados básicos para usar no select do produto"""
    if not current_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    result = await db.execute(
        select(BasicData).filter(BasicData.user_id == current_user.id)
        .order_by(BasicData.year.desc(), BasicData.month.desc())
    )
    basic_data_list = result.scalars().all()
    
    return [{
        "id": bd.id,
        "month": bd.month,
        "year": bd.year,
        "display": f"{bd.month}/{bd.year}"
    } for bd in basic_data_list]

@router.get("/api/basic-data/{basic_data_id}")
async def get_basic_data_for_produto(
    basic_data_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtém dados básicos específicos para cálculos do produto"""
    if not current_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    result = await db.execute(
        select(BasicData).filter(
            and_(
                BasicData.id == basic_data_id,
                BasicData.user_id == current_user.id
            )
        )
    )
    basic_data = result.scalar_one_or_none()
    
    if not basic_data:
        return JSONResponse({"error": "Dados básicos não encontrados"}, status_code=404)
    
    def safe_float(value):
        if value is None:
            return 0.0
        return float(value)
    
    data = {
        "id": basic_data.id,
        "sales_revenue": safe_float(basic_data.sales_revenue),
        "sales_expenses": safe_float(basic_data.sales_expenses),
        "input_product_expenses": safe_float(basic_data.input_product_expenses),
        "fixed_costs": safe_float(basic_data.fixed_costs),
        "other_fixed_costs": safe_float(getattr(basic_data, 'other_fixed_costs', None)),
        "clients_served": basic_data.clients_served or 0
    }
    
    return JSONResponse(data)

@router.get("/api/curva-abc")
async def get_curva_abc(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Calcula a curva ABC dos produtos baseada no faturamento"""
    if not current_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    result = await db.execute(
        select(Produto).filter(Produto.user_id == current_user.id)
    )
    produtos = result.scalars().all()
    
    if not produtos:
        return JSONResponse({
            "curva_abc": [],
            "resumo": {
                "classe_a": {"quantidade": 0, "faturamento": 0, "percentual": 0},
                "classe_b": {"quantidade": 0, "faturamento": 0, "percentual": 0},
                "classe_c": {"quantidade": 0, "faturamento": 0, "percentual": 0}
            }
        })
    
    # Calcular faturamento total e preparar dados
    produtos_com_faturamento = []
    faturamento_total = 0
    
    for produto in produtos:
        faturamento = float(produto.faturamento_por_mercadoria or 0)
        if faturamento > 0:
            produtos_com_faturamento.append({
                "codigo": produto.codigo,
                "nome": produto.nome,
                "faturamento": faturamento,
                "percentual_faturamento": produto.percentual_faturamento or 0,
                "margem_contribuicao_valor": float(produto.margem_contribuicao_valor or 0),
                "quantidade_vendas": int(produto.quantidade_vendas or 0)
            })
            faturamento_total += faturamento
    
    # Ordenar por faturamento decrescente
    produtos_com_faturamento.sort(key=lambda x: x["faturamento"], reverse=True)
    
    # Calcular curva ABC
    curva_abc = []
    faturamento_acumulado = 0
    quantidade_total = len(produtos_com_faturamento)
    
    # Limites da curva ABC (ajustáveis)
    limite_a = 80.0  # Até 80% do faturamento = Classe A
    limite_b = 95.0  # De 80% a 95% = Classe B, acima de 95% = Classe C
    
    for i, produto in enumerate(produtos_com_faturamento):
        percentual_produto = (produto["faturamento"] / faturamento_total * 100) if faturamento_total > 0 else 0
        
        # Calcular percentual acumulado ANTES de adicionar este produto
        percentual_acumulado_antes = (faturamento_acumulado / faturamento_total * 100) if faturamento_total > 0 else 0
        
        # Adicionar o faturamento deste produto ao acumulado
        faturamento_acumulado += produto["faturamento"]
        percentual_acumulado = (faturamento_acumulado / faturamento_total * 100) if faturamento_total > 0 else 0
        
        # Classificar em A, B ou C baseado no percentual acumulado após incluir este produto
        # A classificação é baseada em onde o acumulado está após incluir este produto
        # Classe A: produtos que juntos somam até 80% do faturamento
        if percentual_acumulado <= limite_a:
            classe = "A"
        # Classe B: produtos que somam de 80% a 95% do faturamento
        elif percentual_acumulado <= limite_b:
            # Se o acumulado anterior estava abaixo de 80%, o primeiro produto que ultrapassa
            # deve ser incluído em A se o percentual acumulado não ultrapassar muito 80%
            # Permite margem de até 10% (até 90%) para garantir que produtos importantes sejam A
            if percentual_acumulado_antes < limite_a:
                # Primeiro produto que ultrapassa 80% - se não ultrapassa muito, mantém como A
                if percentual_acumulado <= 90.0:
                    classe = "A"
                else:
                    classe = "B"
            else:
                # Já estávamos acima de 80%, então é B
                classe = "B"
        # Classe C: produtos que somam acima de 95% do faturamento
        else:
            classe = "C"
        
        curva_abc.append({
            **produto,
            "percentual_acumulado": round(percentual_acumulado, 2),
            "percentual_produto": round(percentual_produto, 2),
            "classe": classe,
            "posicao": i + 1
        })
    
    # Calcular resumo por classe
    resumo = {
        "classe_a": {"quantidade": 0, "faturamento": 0, "percentual": 0},
        "classe_b": {"quantidade": 0, "faturamento": 0, "percentual": 0},
        "classe_c": {"quantidade": 0, "faturamento": 0, "percentual": 0}
    }
    
    for item in curva_abc:
        classe_key = f"classe_{item['classe'].lower()}"
        resumo[classe_key]["quantidade"] += 1
        resumo[classe_key]["faturamento"] += item["faturamento"]
    
    for classe_key in resumo:
        resumo[classe_key]["percentual"] = round(
            (resumo[classe_key]["faturamento"] / faturamento_total * 100) if faturamento_total > 0 else 0,
            2
        )
        resumo[classe_key]["faturamento"] = round(resumo[classe_key]["faturamento"], 2)
    
    return JSONResponse({
        "curva_abc": curva_abc,
        "resumo": resumo,
        "faturamento_total": round(faturamento_total, 2),
        "quantidade_total": quantidade_total
    })

