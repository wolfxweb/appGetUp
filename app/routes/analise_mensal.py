from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import logging
from fastapi.responses import RedirectResponse

from app.database.db import get_db
from app.models.analise_mensal import AnaliseMensal
from app.models.custo_fixo import CustoFixo
from app.models.user import User
from app.routes.auth import get_current_user
from app.utils.analise_form_adapter import form_context_for_analise_cadastro
from app.utils.sync_basic_data_analise import sync_basic_data_to_analise_mensal

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


# ==================== SCHEMAS PYDANTIC ====================
class CustoFixoSchema(BaseModel):
    id: Optional[int] = None
    nome: str
    valor: float
    categoria: str


class AnaliseMensalSchema(BaseModel):
    mes: int
    ano: int
    quant_clientes: int
    capacidade_atendimento: Optional[float] = None
    faturamento: float
    gastos_vendas: float
    custo_mercadorias: float
    custo_fixo_total: float
    corresponde_caixa: Optional[bool] = None
    # Campos calculados
    ticket_medio: Optional[float] = None
    margem_bruta: Optional[float] = None
    margem_contribuicao_por_cliente: Optional[float] = None
    ponto_equilibrio: Optional[float] = None
    margem_seguranca: Optional[float] = None
    custo_total: Optional[float] = None
    resultado: Optional[float] = None
    percentual_margem: Optional[float] = None


def calcular_campos_analise(data: AnaliseMensalSchema) -> dict:
    """Recalcula campos derivados (espelha analise_mensal_calculos.js)."""
    fat = data.faturamento or 0
    gv = data.gastos_vendas or 0
    cm = data.custo_mercadorias or 0
    cf = data.custo_fixo_total or 0
    qc = data.quant_clientes or 0

    ticket_medio = fat / qc if qc > 0 else 0
    margem_bruta = fat - gv - cm
    margem_contribuicao_por_cliente = margem_bruta / qc if qc > 0 else 0

    margem_por_cliente = margem_bruta / qc if qc > 0 else 0
    pe_clientes = cf / margem_por_cliente if margem_bruta > 0 and margem_por_cliente > 0 else None
    pe_faturamento = pe_clientes * ticket_medio if pe_clientes is not None and ticket_medio > 0 else None

    ponto_equilibrio = pe_faturamento or 0
    margem_seguranca = None
    if pe_faturamento is not None and pe_faturamento > 0 and fat > 0:
        margem_seguranca = ((fat - pe_faturamento) / fat) * 100

    custo_total = gv + cm + cf
    resultado = fat - custo_total
    percentual_margem = (resultado / fat) * 100 if fat > 0 else 0

    return {
        "ticket_medio": ticket_medio,
        "margem_bruta": margem_bruta,
        "margem_contribuicao_por_cliente": margem_contribuicao_por_cliente,
        "ponto_equilibrio": ponto_equilibrio,
        "margem_seguranca": margem_seguranca,
        "custo_total": custo_total,
        "resultado": resultado,
        "percentual_margem": percentual_margem,
    }


def _aplicar_campos_calculados(data: AnaliseMensalSchema) -> AnaliseMensalSchema:
    calc = calcular_campos_analise(data)
    data.ticket_medio = calc["ticket_medio"]
    data.margem_bruta = calc["margem_bruta"]
    data.margem_contribuicao_por_cliente = calc["margem_contribuicao_por_cliente"]
    data.ponto_equilibrio = calc["ponto_equilibrio"]
    data.margem_seguranca = calc["margem_seguranca"]
    data.custo_total = calc["custo_total"]
    data.resultado = calc["resultado"]
    data.percentual_margem = calc["percentual_margem"]
    return data


# ==================== TELA PRINCIPAL (WIZARD) ====================
@router.get("/analise-mensal", response_class=HTMLResponse)
async def analise_mensal(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Tela principal do wizard de analise mensal"""
    if not current_user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login")
        
    return templates.TemplateResponse("analise_mensal.html", {
        "request": request,
        "user": current_user,
        "active_page": "analise_mensal",
        "modo_detalhe": False,
    })


# ==================== TELA DE LISTA/HISTORICO ====================
@router.get("/analise-mensal/lista", response_class=HTMLResponse)
async def analise_mensal_lista(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Tela de listagem/historico de analises mensais"""
    if not current_user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login")
        
    return templates.TemplateResponse("analise_mensal_lista.html", {
        "request": request,
        "user": current_user,
        "active_page": "analise_mensal_lista"
    })


# ==================== DADOS BÁSICOS (cadastro em analise_mensal) ====================
@router.get("/analise-mensal/cadastro", response_class=HTMLResponse)
async def analise_mensal_cadastro_novo(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Formulário de Dados Básicos (UI legada, persiste em analise_mensal)."""
    if not current_user:
        return RedirectResponse(url="/login")
    now = datetime.now()
    ctx = form_context_for_analise_cadastro(
        edit_mode=False,
        analise=None,
        current_month=now.month,
        current_year=now.year,
        prefill_margin=getattr(current_user, "ideal_profit_margin", None),
        prefill_capacity=getattr(current_user, "service_capacity", None),
    )
    return templates.TemplateResponse("basic_data_form.html", {
        "request": request,
        "user": current_user,
        "active_page": "analise_mensal_cadastro",
        **ctx,
    })


@router.get("/analise-mensal/cadastro/{analise_id}", response_class=HTMLResponse)
async def analise_mensal_cadastro_editar(
    analise_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Edição de Dados Básicos (registro em analise_mensal)."""
    if not current_user:
        return RedirectResponse(url="/login")

    result = await db.execute(
        select(AnaliseMensal).filter(
            AnaliseMensal.id == analise_id,
            AnaliseMensal.user_id == current_user.id,
        )
    )
    analise = result.scalar_one_or_none()
    if not analise:
        raise HTTPException(status_code=404, detail="Análise não encontrada")

    ctx = form_context_for_analise_cadastro(
        edit_mode=True,
        analise=analise,
        current_month=analise.mes,
        current_year=analise.ano,
    )
    return templates.TemplateResponse("basic_data_form.html", {
        "request": request,
        "user": current_user,
        "active_page": "analise_mensal_cadastro",
        **ctx,
    })


# ==================== VER ANALISE (WIZARD DETALHE) ====================
@router.get("/analise-mensal/ver/{analise_id}", response_class=HTMLResponse)
async def ver_analise_mensal(
    analise_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Wizard em modo detalhe — visualização guiada dos resultados."""
    if not current_user:
        return RedirectResponse(url="/login")

    result = await db.execute(
        select(AnaliseMensal).filter(
            AnaliseMensal.id == analise_id,
            AnaliseMensal.user_id == current_user.id,
        )
    )
    analise = result.scalar_one_or_none()
    if not analise:
        raise HTTPException(status_code=404, detail="Análise não encontrada")

    return templates.TemplateResponse("analise_mensal.html", {
        "request": request,
        "user": current_user,
        "active_page": "analise_mensal",
        "analise_id": analise_id,
        "modo_detalhe": True,
    })


# ==================== EDITAR (redireciona para cadastro rápido) ====================
@router.get("/analise-mensal/edit/{analise_id}", response_class=HTMLResponse)
async def editar_analise(
    analise_id: int,
    current_user: User = Depends(get_current_user),
):
    """Compatibilidade: edição via cadastro rápido."""
    if not current_user:
        return RedirectResponse(url="/login")
    return RedirectResponse(url=f"/analise-mensal/cadastro/{analise_id}", status_code=303)


# ==================== API: VERIFICAR SE JA EXISTE ====================
@router.get("/analise-mensal/api/existe")
async def verificar_analise_existente(
    mes: int,
    ano: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Verifica se ja existe analise para o mes/ano informado"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autorizado")
        
    try:
        result = await db.execute(
            select(AnaliseMensal).filter(
                AnaliseMensal.user_id == current_user.id,
                AnaliseMensal.mes == mes,
                AnaliseMensal.ano == ano
            )
        )
        analise = result.scalar_one_or_none()
        
        if analise:
            return {"existe": True, "analise_id": analise.id}
        return {"existe": False}
    except Exception as e:
        logger.error(f"Erro ao verificar análise existente: {str(e)}")
        return {"existe": False, "error": str(e)}



# ==================== API: ANOS DISPONIVEIS ====================
@router.get("/analise-mensal/api/available-years")
async def get_available_years(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retorna todos os anos que tem analise para o usuario"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autorizado")

    try:
        await sync_basic_data_to_analise_mensal(current_user.id, db)
    except Exception as e:
        logger.warning(f"Sync basic_data -> analise_mensal: {e}")
        
    result = await db.execute(
        select(AnaliseMensal.ano)
        .filter(AnaliseMensal.user_id == current_user.id)
        .distinct()
        .order_by(AnaliseMensal.ano.desc())
    )
    anos = [row[0] for row in result.fetchall()]
    return {"years": anos}


# ==================== API: LISTAR ANALISES ====================
@router.get("/analise-mensal/api/listar")
async def listar_analises(
    mes: Optional[int] = None,
    ano: Optional[int] = None,
    page: int = 1,
    per_page: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lista as analises do usuario com filtros e paginacao"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autorizado")

    try:
        await sync_basic_data_to_analise_mensal(current_user.id, db)
    except Exception as e:
        logger.warning(f"Sync basic_data -> analise_mensal: {e}")
        
    query = select(AnaliseMensal).filter(AnaliseMensal.user_id == current_user.id)
    
    # Aplicar filtros
    if mes:
        query = query.filter(AnaliseMensal.mes == mes)
    if ano:
        query = query.filter(AnaliseMensal.ano == ano)
    
    # Contar total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Paginar
    offset = (page - 1) * per_page
    query = query.order_by(AnaliseMensal.ano.desc(), AnaliseMensal.mes.desc())
    query = query.offset(offset).limit(per_page)
    
    result = await db.execute(query)
    analises = result.scalars().all()
    
    # Formatar resposta
    analises_list = []
    for a in analises:
        analises_list.append({
            "id": a.id,
            "mes": a.mes,
            "ano": a.ano,
            "faturamento": a.faturamento,
            "quant_clientes": a.quant_clientes,
            "ticket_medio": a.ticket_medio,
            "margem_bruta": a.margem_bruta,
            "margem_contribuicao_por_cliente": a.margem_contribuicao_por_cliente,
            "ponto_equilibrio": a.ponto_equilibrio,
            "margem_seguranca": a.margem_seguranca,
            "custo_total": a.custo_total,
            "gastos_vendas": a.gastos_vendas,
            "custo_mercadorias": a.custo_mercadorias,
            "custo_fixo_total": a.custo_fixo_total,
            "resultado": a.resultado,
            "percentual_margem": a.percentual_margem,
            "corresponde_caixa": a.corresponde_caixa,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "updated_at": a.updated_at.isoformat() if a.updated_at else None
        })
    
    return {
        "analises": analises_list,
        "total": total,
        "pagina": page,
        "por_pagina": per_page
    }

# ==================== API: CUSTOS FIXOS ====================

@router.get("/analise-mensal/api/custos-fixos")
async def listar_custos_fixos(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lista os custos fixos do usuario"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autorizado")
        
    result = await db.execute(
        select(CustoFixo).filter(CustoFixo.user_id == current_user.id)
    )
    custos = result.scalars().all()
    
    custos_list = []
    for c in custos:
        custos_list.append({
            "id": c.id,
            "nome": c.nome,
            "valor": c.valor,
            "categoria": c.categoria,
            "created_at": c.created_at.isoformat() if c.created_at else None
        })
    
    return {"custos": custos_list}


@router.post("/analise-mensal/api/custos-fixos")
async def criar_custo_fixo(
    data: CustoFixoSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cadastra um novo custo fixo"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autorizado")
    
    try:
        novo_custo = CustoFixo(
            user_id=current_user.id,
            nome=data.nome,
            valor=data.valor,
            categoria=data.categoria,
            created_at=datetime.now()
        )
        logger.info(f"Objeto criado: {novo_custo}")
        
        db.add(novo_custo)
        logger.info("Objeto adicionado à sessão")
        
        await db.commit()
        logger.info("Commit realizado")
        
        await db.refresh(novo_custo)
        logger.info(f"Objeto após refresh: {novo_custo}, id={novo_custo.id if novo_custo else 'None'}")
        
        if novo_custo is None:
            raise Exception("Falha ao salvar custo fixo - refresh retornou None")
        
        if novo_custo.id is None:
            raise Exception("Falha ao salvar custo fixo - id não foi gerado")
        
        return {
            "success": True,
            "message": "Custo fixo cadastrado com sucesso",
            "id": novo_custo.id
        }
    except Exception as e:
        logger.error(f"Erro ao criar custo fixo: {e}")
        import traceback
        logger.error(traceback.format_exc())
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/analise-mensal/api/custos-fixos/{custo_id}")
async def atualizar_custo_fixo(
    custo_id: int,
    data: CustoFixoSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Atualiza um custo fixo existente"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autorizado")
        
    result = await db.execute(
        select(CustoFixo).filter(
            CustoFixo.id == custo_id,
            CustoFixo.user_id == current_user.id
        )
    )
    custo = result.scalar_one_or_none()
    
    if not custo:
        raise HTTPException(status_code=404, detail="Custo fixo não encontrado")
    
    custo.nome = data.nome
    custo.valor = data.valor
    custo.categoria = data.categoria
    
    await db.commit()
    
    return {"success": True, "message": "Custo fixo atualizado com sucesso"}


@router.delete("/analise-mensal/api/custos-fixos/{custo_id}")
async def excluir_custo_fixo(
    custo_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Exclui um custo fixo"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autorizado")
        
    result = await db.execute(
        select(CustoFixo).filter(
            CustoFixo.id == custo_id,
            CustoFixo.user_id == current_user.id
        )
    )
    custo = result.scalar_one_or_none()
    
    if not custo:
        raise HTTPException(status_code=404, detail="Custo fixo não encontrado")
    
    await db.delete(custo)
    await db.commit()
    
    return {"success": True, "message": "Custo fixo excluído com sucesso"}



# ==================== API: SALVAR ANALISE (CRIAR OU ATUALIZAR) ====================
@router.post("/analise-mensal/api/salvar")
async def salvar_analise(
    data: AnaliseMensalSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Salva uma analise mensal.
    Se ja existe para (mes, ano, user_id), atualiza.
    Caso contrario, cria novo registro.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autorizado")

    data = _aplicar_campos_calculados(data)

    try:
        # Verificar se ja existe analise para este mes/ano
        result = await db.execute(
            select(AnaliseMensal).filter(
                AnaliseMensal.user_id == current_user.id,
                AnaliseMensal.mes == data.mes,
                AnaliseMensal.ano == data.ano
            )
        )
        analise_existente = result.scalar_one_or_none()
        
        if analise_existente:
            # ATUALIZAR registro existente
            analise_existente.quant_clientes = data.quant_clientes
            analise_existente.capacidade_atendimento = data.capacidade_atendimento
            analise_existente.faturamento = data.faturamento
            analise_existente.gastos_vendas = data.gastos_vendas
            analise_existente.custo_mercadorias = data.custo_mercadorias
            analise_existente.custo_fixo_total = data.custo_fixo_total
            analise_existente.corresponde_caixa = data.corresponde_caixa
            # Campos calculados
            analise_existente.ticket_medio = data.ticket_medio
            analise_existente.margem_bruta = data.margem_bruta
            analise_existente.margem_contribuicao_por_cliente = data.margem_contribuicao_por_cliente
            analise_existente.ponto_equilibrio = data.ponto_equilibrio
            analise_existente.margem_seguranca = data.margem_seguranca
            analise_existente.custo_total = data.custo_total
            analise_existente.resultado = data.resultado
            analise_existente.percentual_margem = data.percentual_margem
            analise_existente.updated_at = datetime.now()
            
            await db.commit()
            await db.refresh(analise_existente)
            
            return {
                "success": True,
                "message": "Análise atualizada com sucesso",
                "is_new": False,
                "id": analise_existente.id
            }
        
        else:
            # CRIAR novo registro
            nova_analise = AnaliseMensal(
                user_id=current_user.id,
                mes=data.mes,
                ano=data.ano,
                quant_clientes=data.quant_clientes,
                capacidade_atendimento=data.capacidade_atendimento,
                faturamento=data.faturamento,
                gastos_vendas=data.gastos_vendas,
                custo_mercadorias=data.custo_mercadorias,
                custo_fixo_total=data.custo_fixo_total,
                corresponde_caixa=data.corresponde_caixa,
                ticket_medio=data.ticket_medio,
                margem_bruta=data.margem_bruta,
                margem_contribuicao_por_cliente=data.margem_contribuicao_por_cliente,
                ponto_equilibrio=data.ponto_equilibrio,
                margem_seguranca=data.margem_seguranca,
                custo_total=data.custo_total,
                resultado=data.resultado,
                percentual_margem=data.percentual_margem,
                created_at=datetime.now()
            )
            
            db.add(nova_analise)
            await db.commit()
            await db.refresh(nova_analise)
            
            return {
                "success": True,
                "message": "Análise criada com sucesso",
                "is_new": True,
                "id": nova_analise.id
            }
    except Exception as e:
        logger.error(f"Erro ao salvar análise: {str(e)}")
        await db.rollback()
        return {"success": False, "message": f"Erro ao salvar análise: {str(e)}"}


# ==================== API: EXCLUIR ANALISE ====================
@router.delete("/analise-mensal/api/{analise_id}")
async def excluir_analise(
    analise_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Exclui uma analise mensal"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autorizado")
        
    result = await db.execute(
        select(AnaliseMensal).filter(
            AnaliseMensal.id == analise_id,
            AnaliseMensal.user_id == current_user.id
        )
    )
    analise = result.scalar_one_or_none()
    
    if not analise:
        raise HTTPException(status_code=404, detail="Análise não encontrada")
    
    await db.delete(analise)
    await db.commit()
    
    return {"success": True, "message": "Análise excluída com sucesso"}


# ==================== API: BUSCAR ANALISE POR ID ====================
@router.get("/analise-mensal/api/{analise_id}")
async def get_analise_by_id(
    analise_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Busca uma analise mensal pelo ID"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autorizado")
        
    try:
        result = await db.execute(
            select(AnaliseMensal).filter(
                AnaliseMensal.id == analise_id,
                AnaliseMensal.user_id == current_user.id
            )
        )
        analise = result.scalar_one_or_none()
        
        if not analise:
            raise HTTPException(status_code=404, detail="Análise não encontrada")
        
        return {
            "id": analise.id,
            "mes": analise.mes,
            "ano": analise.ano,
            "quant_clientes": analise.quant_clientes,
            "capacidade_atendimento": analise.capacidade_atendimento,
            "faturamento": analise.faturamento,
            "gastos_vendas": analise.gastos_vendas,
            "custo_mercadorias": analise.custo_mercadorias,
            "custo_fixo_total": analise.custo_fixo_total,
            "ticket_medio": analise.ticket_medio,
            "margem_bruta": analise.margem_bruta,
            "margem_contribuicao_por_cliente": analise.margem_contribuicao_por_cliente,
            "ponto_equilibrio": analise.ponto_equilibrio,
            "margem_seguranca": analise.margem_seguranca,
            "custo_total": analise.custo_total,
            "resultado": analise.resultado,
            "percentual_margem": analise.percentual_margem,
            "corresponde_caixa": analise.corresponde_caixa,
            "created_at": analise.created_at.isoformat() if analise.created_at else None,
            "updated_at": analise.updated_at.isoformat() if analise.updated_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar análise: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

