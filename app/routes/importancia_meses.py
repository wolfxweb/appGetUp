from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.database import async_session
from app.routes.auth import get_current_user
from app.database.db import get_db
import logging
import json
from typing import Optional, List, Tuple
from datetime import datetime

from app.models.mes_importancia import MesImportancia
from app.models.evento_venda import EventoVenda
from app.models.basic_data import BasicData

# Configure o logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/importancia-meses")

templates = Jinja2Templates(directory="app/templates")

# Lista de eventos padrão (ordem alfabética para facilitar)
EVENTOS_PADRAO = [
    "Atividades agrícolas",
    "Carnaval",
    "Comemorações de fim-de-ano",
    "Comemorações e eventos religiosos",
    "Dia da Mulher",
    "Dia da Secretária",
    "Dia das Crianças",
    "Dia das Mães",
    "Dia dos Avós",
    "Dia dos Namorados",
    "Dia dos Pais",
    "Eventos esportivos",
    "Eventos folclóricos",
    "Festas Juninas",
    "Festas de peão (rodeios)",
    "Festivais, feiras e exposições",
    "Férias escolares/recessos",
    "Obras e empreendimentos particulares",
    "Obras públicas",
    "Períodos de muita chuva",
    "Períodos de muito calor",
    "Volta às aulas"
]

async def criar_eventos_padrao(user_id: int, session: AsyncSession):
    """Cria eventos padrão para um usuário se não existirem"""
    # Buscar todos os eventos padrão existentes
    result = await session.execute(
        select(EventoVenda).where(
            and_(
                EventoVenda.user_id == user_id,
                EventoVenda.is_padrao == True
            )
        )
    )
    eventos_padrao_existentes = result.scalars().all()
    
    # Normalizar nomes dos eventos padrão esperados (lowercase para comparação)
    eventos_padrao_esperados = {nome.lower().strip(): nome for nome in EVENTOS_PADRAO}
    
    # Agrupar eventos por nome normalizado para identificar duplicatas
    eventos_por_nome = {}
    for evento in eventos_padrao_existentes:
        nome_lower = evento.nome_evento.lower().strip()
        if nome_lower not in eventos_por_nome:
            eventos_por_nome[nome_lower] = []
        eventos_por_nome[nome_lower].append(evento)
    
    # Identificar eventos para deletar (duplicatas ou não esperados)
    eventos_para_deletar = []
    eventos_para_manter = set()
    
    for nome_lower, eventos_com_nome in eventos_por_nome.items():
        if nome_lower in eventos_padrao_esperados:
            # Evento esperado: manter apenas o primeiro, deletar os demais
            eventos_para_manter.add(nome_lower)
            if len(eventos_com_nome) > 1:
                # Manter o primeiro, deletar os duplicados
                eventos_para_deletar.extend(eventos_com_nome[1:])
        else:
            # Evento não esperado: deletar todos
            eventos_para_deletar.extend(eventos_com_nome)
    
    # Deletar duplicatas e eventos não esperados
    for evento in eventos_para_deletar:
        await session.delete(evento)
    
    if eventos_para_deletar:
        await session.commit()
        logger.info(f"Removidos {len(eventos_para_deletar)} eventos padrão duplicados/inexistentes para user_id={user_id}")
    
    # Criar apenas os eventos padrão que ainda não existem
    eventos_criados = 0
    for evento_nome in EVENTOS_PADRAO:
        nome_lower = evento_nome.lower().strip()
        if nome_lower not in eventos_para_manter:
            novo_evento = EventoVenda(
                user_id=user_id,
                nome_evento=evento_nome,
                aumenta_vendas=False,
                diminui_vendas=False,
                meses_afetados=None,
                is_padrao=True
            )
            session.add(novo_evento)
            eventos_criados += 1
    
    if eventos_criados > 0:
        await session.commit()
        logger.info(f"Criados {eventos_criados} eventos padrão para user_id={user_id}")

@router.get("/", response_class=HTMLResponse)
async def importancia_meses_page(
    request: Request,
    current_user = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse(
        "importancia_meses.html",
        {
            "request": request,
            "user": current_user,
            "active_page": "importancia_meses"
        }
    )

@router.get("/cadastrar", response_class=HTMLResponse)
async def importancia_meses_cadastrar_page(
    request: Request,
    current_user = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    
    # Buscar dados básicos do usuário
    async with async_session() as session:
        await criar_eventos_padrao(current_user.id, session)
        
        query = select(BasicData).where(BasicData.user_id == current_user.id).order_by(BasicData.year.desc(), BasicData.month.desc())
        result = await session.execute(query)
        basic_data_list = result.scalars().all()
    
    # Preparar lista de eventos padrão para o template
    eventos_padrao_template = []
    for i, nome in enumerate(EVENTOS_PADRAO, start=1):
        eventos_padrao_template.append({
            "id": i,
            "nome_evento": nome,
            "aumenta_vendas": False,
            "diminui_vendas": False,
            "meses_afetados": [],
            "is_padrao": True
        })
    
    return templates.TemplateResponse(
        "importancia_meses_cadastrar.html",
        {
            "request": request,
            "user": current_user,
            "basic_data_list": basic_data_list,
            "active_page": "importancia_meses",
            "eventos_padrao": eventos_padrao_template
        }
    )

@router.get("/api/basic-data")
async def get_basic_data_for_importancia(
    request: Request,
    current_user = Depends(get_current_user)
):
    """Retorna lista de Dados Básicos agrupados por ano/mês"""
    if not current_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        async with async_session() as session:
            query = select(BasicData).where(BasicData.user_id == current_user.id)
            result = await session.execute(query)
            basic_data_list = result.scalars().all()
            
            data = []
            for item in basic_data_list:
                data.append({
                    "id": item.id,
                    "year": item.year,
                    "month": item.month,
                    "clients_served": item.clients_served,  # quantidade_vendas
                    "sales_revenue": float(item.sales_revenue) if item.sales_revenue else 0
                })
            
            return JSONResponse(content=data)
    except Exception as e:
        logger.error(f"Erro ao listar dados básicos: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/api/month-importance/{year}")
async def get_month_importance(
    year: int,
    request: Request,
    current_user = Depends(get_current_user)
):
    """Retorna importância dos meses SALVOS para um ano específico"""
    if not current_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        async with async_session() as session:
            query = select(MesImportancia).where(
                and_(
                    MesImportancia.user_id == current_user.id,
                    MesImportancia.year == year
                )
            )
            result = await session.execute(query)
            meses = result.scalars().all()
            
            data = []
            for mes in meses:
                data.append({
                    "id": mes.id,
                    "year": mes.year,
                    "month": mes.month,
                    "nota_atribuida": mes.nota_atribuida,
                    "ritmo_negocio_percentual": mes.ritmo_negocio_percentual,
                    "quantidade_vendas_real": mes.quantidade_vendas_real,
                    "quantidade_vendas_estimada": mes.quantidade_vendas_estimada,
                    "peso_mes": mes.peso_mes
                })
            
            return JSONResponse(content=data)
    except Exception as e:
        logger.error(f"Erro ao buscar importância dos meses: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/api/sales-events")
async def get_sales_events(
    request: Request,
    current_user = Depends(get_current_user)
):
    """Retorna eventos do usuário"""
    if not current_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        async with async_session() as session:
            # Garantir que eventos padrão existam
            await criar_eventos_padrao(current_user.id, session)
            
            query = select(EventoVenda).where(EventoVenda.user_id == current_user.id).order_by(EventoVenda.is_padrao.desc(), EventoVenda.nome_evento.asc())
            result = await session.execute(query)
            eventos = result.scalars().all()
            
            data = []
            for evento in eventos:
                meses_afetados = evento.meses_afetados
                if isinstance(meses_afetados, str):
                    try:
                        meses_afetados = json.loads(meses_afetados)
                    except:
                        meses_afetados = []
                
                data.append({
                    "id": evento.id,
                    "nome_evento": evento.nome_evento,
                    "aumenta_vendas": evento.aumenta_vendas,
                    "diminui_vendas": evento.diminui_vendas,
                    "meses_afetados": meses_afetados if meses_afetados else [],
                    "is_padrao": evento.is_padrao
                })
            
            return JSONResponse(content=data)
    except Exception as e:
        logger.error(f"Erro ao buscar eventos: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

def calcular_ritmo_negocio(nota_atual: Optional[float], nota_anterior: Optional[float]) -> Optional[float]:
    """Calcula ritmo do negócio como razão entre notas"""
    if nota_atual is None or nota_anterior is None or nota_anterior == 0:
        return None
    return (nota_atual / nota_anterior) * 100

def calcular_quantidade_vendas(
    month: int,
    year: int,
    basic_data_dict: dict,
    ritmo_negocio: Optional[float],
    quantidade_mes_anterior: Optional[float]
) -> Tuple[Optional[float], Optional[float]]:
    """
    Calcula quantidade de vendas (real ou estimada)
    Retorna (quantidade_vendas_real, quantidade_vendas_estimada)
    """
    key = f"{year}-{month:02d}"
    
    # Se houver dados básicos para este mês/ano, usar valor real
    if key in basic_data_dict:
        return (basic_data_dict[key], None)
    
    # Se não houver dados básicos, calcular estimativa
    if ritmo_negocio is not None and quantidade_mes_anterior is not None:
        quantidade_estimada = (ritmo_negocio / 100) * quantidade_mes_anterior
        return (None, quantidade_estimada)
    
    return (None, None)

def calcular_peso_mes(
    nota_atribuida: Optional[float],
    eventos_aumentam: int,
    eventos_diminuem: int,
    ritmo_negocio: Optional[float]
) -> Optional[float]:
    """Calcula peso do mês"""
    peso_base = nota_atribuida if nota_atribuida is not None else 0
    ajuste_eventos = eventos_aumentam - eventos_diminuem
    peso_bruto = peso_base + ajuste_eventos
    
    if ritmo_negocio is not None:
        peso_final = peso_bruto * (ritmo_negocio / 100)
        return peso_final
    
    return peso_bruto if peso_bruto > 0 else None

@router.post("/api/save")
async def save_importancia_meses(
    request: Request,
    basic_data_id: int = Form(...),  # ID do dado básico selecionado
    meses_data: str = Form(...),  # JSON string com array de meses
    eventos_data: str = Form(...),  # JSON string com array de eventos
    current_user = Depends(get_current_user)
):
    """Salva importância dos meses com todos os cálculos"""
    if not current_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        meses = json.loads(meses_data)
        eventos = json.loads(eventos_data)
        
        async with async_session() as session:
            # Buscar o dado básico selecionado
            query = select(BasicData).where(
                and_(
                    BasicData.id == basic_data_id,
                    BasicData.user_id == current_user.id
                )
            )
            result = await session.execute(query)
            basic_data_selecionado = result.scalar_one_or_none()
            
            if not basic_data_selecionado:
                return JSONResponse({"error": "Dado básico não encontrado"}, status_code=404)
            
            year = basic_data_selecionado.year
            
            # Buscar todos os dados básicos para o ano (para cálculos)
            query = select(BasicData).where(
                and_(
                    BasicData.user_id == current_user.id,
                    BasicData.year == year
                )
            )
            result = await session.execute(query)
            basic_data_list = result.scalars().all()
            
            # Criar dicionário de dados básicos: {"2025-01": clients_served, ...}
            basic_data_dict = {}
            for bd in basic_data_list:
                key = f"{bd.year}-{bd.month:02d}"
                basic_data_dict[key] = float(bd.clients_served) if bd.clients_served else 0
            
            # Processar cada mês
            notas_meses = {}  # {month: nota}
            for mes_data in meses:
                month = int(mes_data.get('month'))
                nota = mes_data.get('nota_atribuida')
                if nota is not None:
                    notas_meses[month] = float(nota)
            
            # Calcular ritmo do negócio para cada mês
            ritmos = {}  # {month: ritmo}
            quantidades_real = {}  # {month: quantidade_real}
            quantidades_estimada = {}  # {month: quantidade_estimada}
            
            for month in range(1, 13):
                nota_atual = notas_meses.get(month)
                
                # Para janeiro, comparar com dezembro
                if month == 1:
                    nota_anterior = notas_meses.get(12)
                else:
                    nota_anterior = notas_meses.get(month - 1)
                
                ritmo = calcular_ritmo_negocio(nota_atual, nota_anterior)
                ritmos[month] = ritmo
                
                # Calcular quantidade de vendas
                quantidade_anterior = None
                if month == 1:
                    quantidade_anterior = quantidades_real.get(12) or quantidades_estimada.get(12)
                else:
                    quantidade_anterior = quantidades_real.get(month - 1) or quantidades_estimada.get(month - 1)
                
                quant_real, quant_est = calcular_quantidade_vendas(
                    month, year, basic_data_dict, ritmo, quantidade_anterior
                )
                quantidades_real[month] = quant_real
                quantidades_estimada[month] = quant_est
            
            # Calcular ajuste de eventos por mês
            ajustes_eventos = {}  # {month: (aumenta, diminui)}
            for month in range(1, 13):
                aumenta = 0
                diminui = 0
                
                for evento in eventos:
                    meses_afetados = evento.get('meses_afetados', [])
                    if month in meses_afetados:
                        if evento.get('aumenta_vendas'):
                            aumenta += 1
                        if evento.get('diminui_vendas'):
                            diminui += 1
                
                ajustes_eventos[month] = (aumenta, diminui)
            
            # Calcular peso de cada mês
            pesos = {}
            for month in range(1, 13):
                nota = notas_meses.get(month)
                aumenta, diminui = ajustes_eventos[month]
                ritmo = ritmos[month]
                peso = calcular_peso_mes(nota, aumenta, diminui, ritmo)
                pesos[month] = peso
            
            # Salvar/atualizar meses
            for mes_data in meses:
                month = int(mes_data.get('month'))
                nota = mes_data.get('nota_atribuida')
                
                # Buscar registro existente
                query = select(MesImportancia).where(
                    and_(
                        MesImportancia.user_id == current_user.id,
                        MesImportancia.year == year,
                        MesImportancia.month == month
                    )
                )
                result = await session.execute(query)
                mes_importancia = result.scalar_one_or_none()
                
                if mes_importancia:
                    # Atualizar
                    mes_importancia.nota_atribuida = float(nota) if nota else None
                    mes_importancia.ritmo_negocio_percentual = ritmos.get(month)
                    mes_importancia.quantidade_vendas_real = quantidades_real.get(month)
                    mes_importancia.quantidade_vendas_estimada = quantidades_estimada.get(month)
                    mes_importancia.peso_mes = pesos.get(month)
                    mes_importancia.updated_at = datetime.now()
                else:
                    # Criar novo
                    mes_importancia = MesImportancia(
                        user_id=current_user.id,
                        year=year,
                        month=month,
                        nota_atribuida=float(nota) if nota else None,
                        ritmo_negocio_percentual=ritmos.get(month),
                        quantidade_vendas_real=quantidades_real.get(month),
                        quantidade_vendas_estimada=quantidades_estimada.get(month),
                        peso_mes=pesos.get(month)
                    )
                    session.add(mes_importancia)
            
            # Salvar/atualizar eventos
            for evento_data in eventos:
                evento_id = evento_data.get('id')
                meses_afetados = evento_data.get('meses_afetados', [])
                
                if evento_id:
                    # Atualizar evento existente
                    query = select(EventoVenda).where(
                        and_(
                            EventoVenda.id == evento_id,
                            EventoVenda.user_id == current_user.id
                        )
                    )
                    result = await session.execute(query)
                    evento = result.scalar_one_or_none()
                    
                    if evento:
                        evento.aumenta_vendas = evento_data.get('aumenta_vendas', False)
                        evento.diminui_vendas = evento_data.get('diminui_vendas', False)
                        evento.meses_afetados = json.dumps(meses_afetados) if meses_afetados else None
                        evento.updated_at = datetime.now()
            
            await session.commit()
            
            return JSONResponse(content={"success": True, "message": "Dados salvos com sucesso"})
            
    except Exception as e:
        logger.error(f"Erro ao salvar importância dos meses: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.post("/api/sales-event")
async def create_sales_event(
    request: Request,
    nome_evento: str = Form(...),
    aumenta_vendas: bool = Form(False),
    diminui_vendas: bool = Form(False),
    meses_afetados: str = Form(...),  # JSON string com array de meses
    current_user = Depends(get_current_user)
):
    """Cria novo evento personalizado"""
    if not current_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        meses = json.loads(meses_afetados)
        
        async with async_session() as session:
            novo_evento = EventoVenda(
                user_id=current_user.id,
                nome_evento=nome_evento,
                aumenta_vendas=aumenta_vendas,
                diminui_vendas=diminui_vendas,
                meses_afetados=json.dumps(meses) if meses else None,
                is_padrao=False
            )
            session.add(novo_evento)
            await session.commit()
            
            return JSONResponse(content={
                "success": True,
                "id": novo_evento.id,
                "message": "Evento criado com sucesso"
            })
    except Exception as e:
        logger.error(f"Erro ao criar evento: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.delete("/api/sales-event/{event_id}")
async def delete_sales_event(
    event_id: int,
    request: Request,
    current_user = Depends(get_current_user)
):
    """Deleta evento personalizado (não padrão)"""
    if not current_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        async with async_session() as session:
            query = select(EventoVenda).where(
                and_(
                    EventoVenda.id == event_id,
                    EventoVenda.user_id == current_user.id,
                    EventoVenda.is_padrao == False  # Só pode deletar eventos personalizados
                )
            )
            result = await session.execute(query)
            evento = result.scalar_one_or_none()
            
            if not evento:
                return JSONResponse({"error": "Evento não encontrado ou não pode ser deletado"}, status_code=404)
            
            await session.delete(evento)
            await session.commit()
            
            return JSONResponse(content={"success": True, "message": "Evento deletado com sucesso"})
    except Exception as e:
        logger.error(f"Erro ao deletar evento: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)
