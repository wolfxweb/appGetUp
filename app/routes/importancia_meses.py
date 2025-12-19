from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
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
                nota=0.0,
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
    
    # Buscar dados básicos do usuário e eventos padrão
    async with async_session() as session:
        await criar_eventos_padrao(current_user.id, session)
        
        query = select(BasicData).where(BasicData.user_id == current_user.id).order_by(BasicData.year.desc(), BasicData.month.desc())
        result = await session.execute(query)
        basic_data_list = result.scalars().all()
        
        # Buscar eventos padrão reais do banco para passar ao template
        query_eventos = select(EventoVenda).where(
            and_(
                EventoVenda.user_id == current_user.id,
                EventoVenda.is_padrao == True
            )
        ).order_by(EventoVenda.nome_evento.asc())
        result_eventos = await session.execute(query_eventos)
        eventos_padrao_banco = result_eventos.scalars().all()
    
    # Preparar lista de eventos padrão para o template
    eventos_padrao_template = []
    for evento in eventos_padrao_banco:
        meses_afetados = evento.meses_afetados
        if isinstance(meses_afetados, str):
            try:
                meses_afetados = json.loads(meses_afetados)
            except:
                meses_afetados = []
        eventos_padrao_template.append({
            "id": evento.id,
            "nome_evento": evento.nome_evento,
            "nota": evento.nota if evento.nota is not None else 0.0,
            "aumenta_vendas": evento.aumenta_vendas,
            "diminui_vendas": evento.diminui_vendas,
            "meses_afetados": meses_afetados if meses_afetados else [],
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

@router.get("/api/available-years")
async def get_available_years(
    request: Request,
    current_user = Depends(get_current_user)
):
    """Retorna lista de anos disponíveis que têm dados de importância dos meses salvos"""
    if not current_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        async with async_session() as session:
            # Buscar anos únicos da tabela mes_importancia
            query = select(MesImportancia.year).where(
                MesImportancia.user_id == current_user.id
            ).distinct()
            result = await session.execute(query)
            anos = [row[0] for row in result.all() if row[0] is not None]
            
            return JSONResponse(content=sorted(anos, reverse=True))
    except Exception as e:
        logger.error(f"Erro ao buscar anos disponíveis: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

async def recalcular_importancia_meses(session: AsyncSession, year: int, user_id: int) -> List[dict]:
    """
    Recalcula importância dos meses baseado em notas atribuídas salvas e dados básicos.
    Retorna lista com dados calculados para todos os 12 meses.
    """
    # Buscar todas as notas atribuídas salvas para o ano
    query = select(MesImportancia).where(
        and_(
            MesImportancia.user_id == user_id,
            MesImportancia.year == year
        )
    )
    result = await session.execute(query)
    meses_salvos = result.scalars().all()
    
    # Criar dicionário de notas atribuídas: {month: nota}
    notas_meses = {}
    meses_map = {}  # {month: MesImportancia}
    for mes in meses_salvos:
        if mes.nota_atribuida is not None:
            notas_meses[mes.month] = float(mes.nota_atribuida)
        meses_map[mes.month] = mes
    
    # Calcular total das notas dos 12 meses (para validação)
    total_notas = sum(notas_meses.values()) if notas_meses else 0
    logger.info(f"[recalcular_importancia_meses] Ano {year}, User {user_id}: {len(meses_salvos)} meses salvos, {len(notas_meses)} com notas, Total notas: {total_notas}")
    logger.info(f"[recalcular_importancia_meses] Notas por mês: {notas_meses}")
    
    # Buscar dados básicos do ano e ano anterior (para janeiro)
    year_anterior = year - 1
    query = select(BasicData).where(
        and_(
            BasicData.user_id == user_id,
            or_(BasicData.year == year, BasicData.year == year_anterior)
        )
    )
    result = await session.execute(query)
    basic_data_list = result.scalars().all()
    
    # Criar dicionário de dados básicos: {"2025-11": clients_served, ...}
    basic_data_dict = {}
    for bd in basic_data_list:
        key = f"{bd.year}-{bd.month:02d}"
        basic_data_dict[key] = float(bd.clients_served) if bd.clients_served else 0
    
    # Buscar dezembro do ano anterior para cálculo de janeiro
    mes_importancia_ano_anterior = {}
    query_dez_ano_anterior = select(MesImportancia).where(
        and_(
            MesImportancia.user_id == user_id,
            MesImportancia.year == year_anterior,
            MesImportancia.month == 12
        )
    )
    result_dez = await session.execute(query_dez_ano_anterior)
    dez_ano_anterior = result_dez.scalar_one_or_none()
    if dez_ano_anterior:
        mes_importancia_ano_anterior[12] = {
            'nota': dez_ano_anterior.nota_atribuida,
            'quantidade_real': dez_ano_anterior.quantidade_vendas_real,
            'quantidade_estimada': dez_ano_anterior.quantidade_vendas_estimada
        }
    
    # Calcular ritmo do negócio e quantidade de vendas para cada mês
    # ESTRATÉGIA: Fazer duas passadas completas para garantir que janeiro (que depende de dezembro) seja calculado corretamente
    ritmos = {}  # {month: ritmo}
    quantidades_real = {}  # {month: quantidade_real}
    quantidades_estimada = {}  # {month: quantidade_estimada}
    
    # Fazer duas passadas completas para garantir convergência
    for passada in range(2):
        for month in range(1, 13):
            nota_atual = notas_meses.get(month)
            
            # Calcular ritmo do negócio
            if month == 1:
                # Janeiro: comparar com dezembro (do mesmo ano primeiro, depois ano anterior)
                nota_anterior = notas_meses.get(12)
                if nota_anterior is None and mes_importancia_ano_anterior.get(12):
                    nota_anterior = mes_importancia_ano_anterior[12].get('nota')
            else:
                nota_anterior = notas_meses.get(month - 1)
            
            ritmo = calcular_ritmo_negocio(nota_atual, nota_anterior)
            ritmos[month] = ritmo
            
            # Calcular quantidade de vendas
            quantidade_anterior = None
            if month == 1:
                # Janeiro: tentar usar dezembro do mesmo ano (na segunda passada já estará calculado)
                quantidade_anterior = quantidades_real.get(12) or quantidades_estimada.get(12)
                if quantidade_anterior is None and mes_importancia_ano_anterior.get(12):
                    quantidade_anterior = (mes_importancia_ano_anterior[12].get('quantidade_real') or 
                                         mes_importancia_ano_anterior[12].get('quantidade_estimada'))
            else:
                # Demais meses: usar mês anterior (já calculado)
                quantidade_anterior = quantidades_real.get(month - 1) or quantidades_estimada.get(month - 1)
            
            # Calcular quantidade de vendas (a função garante que meses com dados básicos usam valor real)
            quant_real, quant_est = calcular_quantidade_vendas(
                month, year, basic_data_dict, ritmo, quantidade_anterior
            )
            quantidades_real[month] = quant_real
            quantidades_estimada[month] = quant_est
    
    # Construir lista de resultados para todos os 12 meses
    data = []
    for month in range(1, 13):
        mes_salvo = meses_map.get(month)
        resultado = {
            "id": mes_salvo.id if mes_salvo else None,
            "year": year,
            "month": month,
            "nota_atribuida": notas_meses.get(month),
            "ritmo_negocio_percentual": ritmos.get(month),
            "quantidade_vendas_real": quantidades_real.get(month),
            "quantidade_vendas_estimada": quantidades_estimada.get(month),
            "peso_mes": mes_salvo.peso_mes if mes_salvo else None
        }
        data.append(resultado)
        if month <= 3 or month >= 11:  # Log apenas primeiros e últimos meses para não poluir
            logger.info(f"[recalcular] Mês {month}: nota={resultado['nota_atribuida']}, ritmo={resultado['ritmo_negocio_percentual']}, qtd_real={resultado['quantidade_vendas_real']}, qtd_est={resultado['quantidade_vendas_estimada']}")
    
    logger.info(f"[recalcular_importancia_meses] Retornando {len(data)} meses calculados")
    return data

@router.get("/api/month-importance/{year}")
async def get_month_importance(
    year: int,
    request: Request,
    current_user = Depends(get_current_user)
):
    """Retorna importância dos meses RECALCULADOS para um ano específico"""
    if not current_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        async with async_session() as session:
            # Recalcular todos os valores baseado nas notas atribuídas salvas
            data = await recalcular_importancia_meses(session, year, current_user.id)
            
            return JSONResponse(content=data)
    except Exception as e:
        logger.error(f"Erro ao buscar importância dos meses: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/api/basic-data/{basic_data_id}/month-importance")
async def get_month_importance_by_basic_data(
    basic_data_id: int,
    request: Request,
    current_user = Depends(get_current_user)
):
    """Retorna importância dos meses SALVOS para um dado básico específico"""
    if not current_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        async with async_session() as session:
            # Buscar o dado básico para obter o ano
            query = select(BasicData).where(
                and_(
                    BasicData.id == basic_data_id,
                    BasicData.user_id == current_user.id
                )
            )
            result = await session.execute(query)
            basic_data = result.scalar_one_or_none()
            
            if not basic_data:
                return JSONResponse({"error": "Dado básico não encontrado"}, status_code=404)
            
            year = basic_data.year
            
            # Buscar meses de importância para o ano
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
                    "nota": evento.nota if evento.nota is not None else 0.0,
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
    """
    Calcula ritmo do negócio como razão entre notas.
    Fórmula: (Nota atribuída mês atual / Nota atribuída mês anterior) * 100
    """
    if nota_atual is None or nota_anterior is None or nota_anterior == 0:
        return None
    ritmo = (nota_atual / nota_anterior) * 100
    return ritmo

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
    soma_notas_aumentam: float,
    soma_notas_diminuem: float,
    ritmo_negocio: Optional[float]
) -> Optional[float]:
    """Calcula peso do mês usando soma das notas dos eventos"""
    peso_base = nota_atribuida if nota_atribuida is not None else 0
    ajuste_eventos = soma_notas_aumentam - soma_notas_diminuem
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
            
            # Buscar todos os dados básicos para o ano e ano anterior (para cálculos de janeiro)
            year_anterior = year - 1
            query = select(BasicData).where(
                and_(
                    BasicData.user_id == current_user.id,
                    or_(BasicData.year == year, BasicData.year == year_anterior)
                )
            )
            result = await session.execute(query)
            basic_data_list = result.scalars().all()
            
            # Criar dicionário de dados básicos: {"2025-01": clients_served, ...}
            basic_data_dict = {}
            for bd in basic_data_list:
                key = f"{bd.year}-{bd.month:02d}"
                basic_data_dict[key] = float(bd.clients_served) if bd.clients_served else 0
            
            # Buscar MesImportancia do ano anterior para obter nota e quantidade de dezembro (para cálculo de janeiro)
            mes_importancia_ano_anterior = {}
            query = select(MesImportancia).where(
                and_(
                    MesImportancia.user_id == current_user.id,
                    MesImportancia.year == year_anterior,
                    MesImportancia.month == 12  # Dezembro do ano anterior
                )
            )
            result = await session.execute(query)
            dez_ano_anterior = result.scalar_one_or_none()
            if dez_ano_anterior:
                mes_importancia_ano_anterior[12] = {
                    'nota': dez_ano_anterior.nota_atribuida,
                    'quantidade_real': dez_ano_anterior.quantidade_vendas_real,
                    'quantidade_estimada': dez_ano_anterior.quantidade_vendas_estimada
                }
            
            # Calcular notas atribuídas para cada mês = soma das notas dos eventos que afetam aquele mês
            notas_meses = {}  # {month: nota}
            logger.info(f"[save_importancia_meses] Recebidos {len(eventos)} eventos no request")
            
            # Inicializar notas de todos os meses como 0
            for month in range(1, 13):
                notas_meses[month] = 0.0
            
            # Para cada evento, somar sua nota aos meses que ele afeta
            for evento in eventos:
                meses_afetados = evento.get('meses_afetados', [])
                nota_evento = float(evento.get('nota', 0) or 0)
                
                logger.info(f"[save_importancia_meses] Evento: {evento.get('nome_evento', 'sem nome')}, nota={nota_evento}, meses_afetados={meses_afetados}")
                
                # Somar a nota do evento aos meses afetados
                for month in meses_afetados:
                    if month >= 1 and month <= 12:
                        notas_meses[month] += nota_evento
            
            # Converter notas 0 para None (não salvar se não houver eventos)
            for month in range(1, 13):
                if notas_meses[month] == 0:
                    notas_meses[month] = None
            
            logger.info(f"[save_importancia_meses] Notas calculadas (soma dos eventos): {notas_meses}")
            
            # Calcular ritmo do negócio para cada mês
            ritmos = {}  # {month: ritmo}
            quantidades_real = {}  # {month: quantidade_real}
            quantidades_estimada = {}  # {month: quantidade_estimada}
            
            for month in range(1, 13):
                nota_atual = notas_meses.get(month)
                
                # Para janeiro, comparar com dezembro (do mesmo ano, ou ano anterior se não houver)
                if month == 1:
                    # Tentar usar dezembro do mesmo ano primeiro, se não existir usar do ano anterior
                    nota_anterior = notas_meses.get(12) or (mes_importancia_ano_anterior.get(12, {}).get('nota') if mes_importancia_ano_anterior else None)
                else:
                    nota_anterior = notas_meses.get(month - 1)
                
                ritmo = calcular_ritmo_negocio(nota_atual, nota_anterior)
                ritmos[month] = ritmo
                
                # Calcular quantidade de vendas
                quantidade_anterior = None
                if month == 1:
                    # Tentar usar dezembro do mesmo ano primeiro, se não existir usar do ano anterior
                    quantidade_anterior = (quantidades_real.get(12) or quantidades_estimada.get(12))
                    if quantidade_anterior is None and mes_importancia_ano_anterior.get(12):
                        quantidade_anterior = (mes_importancia_ano_anterior[12].get('quantidade_real') or 
                                             mes_importancia_ano_anterior[12].get('quantidade_estimada'))
                else:
                    quantidade_anterior = quantidades_real.get(month - 1) or quantidades_estimada.get(month - 1)
                
                quant_real, quant_est = calcular_quantidade_vendas(
                    month, year, basic_data_dict, ritmo, quantidade_anterior
                )
                quantidades_real[month] = quant_real
                quantidades_estimada[month] = quant_est
            
            # Calcular ajuste de eventos por mês (soma das notas ao invés de contagem)
            ajustes_eventos = {}  # {month: (soma_notas_aumenta, soma_notas_diminui)}
            for month in range(1, 13):
                soma_notas_aumenta = 0.0
                soma_notas_diminui = 0.0
                
                for evento in eventos:
                    meses_afetados = evento.get('meses_afetados', [])
                    if month in meses_afetados:
                        nota = float(evento.get('nota', 0) or 0)
                        if evento.get('aumenta_vendas'):
                            soma_notas_aumenta += nota
                        if evento.get('diminui_vendas'):
                            soma_notas_diminui += nota
                
                ajustes_eventos[month] = (soma_notas_aumenta, soma_notas_diminui)
            
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
                
                # Converter nota para float ou None
                nota_float = None
                if nota is not None and nota != '' and nota != 'null':
                    try:
                        nota_float = float(nota)
                        logger.info(f"[save_importancia_meses] Salvando mês {month}: nota={nota_float}")
                    except (ValueError, TypeError):
                        logger.warning(f"[save_importancia_meses] Erro ao converter nota do mês {month}: {nota}")
                        nota_float = None
                
                if mes_importancia:
                    # Atualizar
                    mes_importancia.nota_atribuida = nota_float
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
                        nota_atribuida=nota_float,
                        ritmo_negocio_percentual=ritmos.get(month),
                        quantidade_vendas_real=quantidades_real.get(month),
                        quantidade_vendas_estimada=quantidades_estimada.get(month),
                        peso_mes=pesos.get(month)
                    )
                    session.add(mes_importancia)
            
            # Salvar/atualizar eventos (sempre atualiza eventos existentes, nunca cria novos)
            for evento_data in eventos:
                evento_id = evento_data.get('id')
                meses_afetados = evento_data.get('meses_afetados', [])
                
                if evento_id:
                    # Buscar e atualizar evento existente
                    query = select(EventoVenda).where(
                        and_(
                            EventoVenda.id == evento_id,
                            EventoVenda.user_id == current_user.id
                        )
                    )
                    result = await session.execute(query)
                    evento = result.scalar_one_or_none()
                    
                    if evento:
                        # Atualizar evento existente (não criar novo)
                        evento.nota = float(evento_data.get('nota', 0) or 0)
                        evento.aumenta_vendas = evento_data.get('aumenta_vendas', False)
                        evento.diminui_vendas = evento_data.get('diminui_vendas', False)
                        evento.meses_afetados = json.dumps(meses_afetados) if meses_afetados else None
                        evento.updated_at = datetime.now()
                        logger.info(f"Evento atualizado: id={evento_id}, nome={evento.nome_evento}, nota={evento.nota}")
                    else:
                        logger.warning(f"Evento não encontrado para atualização: id={evento_id}, user_id={current_user.id}")
                else:
                    logger.warning(f"Evento sem ID recebido no salvamento: {evento_data.get('nome_evento', 'sem nome')}")
            
            await session.commit()
            
            return JSONResponse(content={"success": True, "message": "Dados salvos com sucesso"})
            
    except Exception as e:
        logger.error(f"Erro ao salvar importância dos meses: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.post("/api/sales-event")
async def create_sales_event(
    request: Request,
    nome_evento: str = Form(...),
    nota: float = Form(0.0),
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
                nota=float(nota) if nota else 0.0,
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
