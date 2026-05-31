"""Espelha registros de basic_data em analise_mensal quando ainda não existem."""
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analise_mensal import AnaliseMensal
from app.models.basic_data import BasicData


def _custo_fixo_from_basic_data(bd: BasicData) -> float:
    return float(bd.pro_labore or 0) + float(bd.other_fixed_costs or 0) + float(bd.fixed_costs or 0)


def _capacidade_from_basic_data(bd: BasicData) -> Optional[float]:
    if not bd.service_capacity:
        return None
    try:
        return float(str(bd.service_capacity).replace(",", "."))
    except (ValueError, TypeError):
        return None


def _calcular_campos_derivados(
    faturamento: float,
    gastos_vendas: float,
    custo_mercadorias: float,
    custo_fixo_total: float,
    quant_clientes: int,
) -> dict:
    """Mesma lógica de calcular_campos_analise em analise_mensal.py."""
    fat = faturamento or 0
    gv = gastos_vendas or 0
    cm = custo_mercadorias or 0
    cf = custo_fixo_total or 0
    qc = quant_clientes or 0

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


async def sync_basic_data_to_analise_mensal(user_id: int, db: AsyncSession) -> int:
    """
    Cria linhas em analise_mensal para cada basic_data do usuário
    que ainda não tem par (mes, ano) na análise mensal.
    """
    result = await db.execute(select(BasicData).where(BasicData.user_id == user_id))
    basic_rows = result.scalars().all()
    created = 0

    for bd in basic_rows:
        existing = await db.execute(
            select(AnaliseMensal).where(
                AnaliseMensal.user_id == user_id,
                AnaliseMensal.mes == bd.month,
                AnaliseMensal.ano == bd.year,
            )
        )
        if existing.scalar_one_or_none():
            continue

        fat = float(bd.sales_revenue or 0)
        gv = float(bd.sales_expenses or 0)
        cm = float(bd.input_product_expenses or 0)
        cf = _custo_fixo_from_basic_data(bd)
        qc = int(bd.clients_served or 0)
        calc = _calcular_campos_derivados(fat, gv, cm, cf, qc)

        db.add(
            AnaliseMensal(
                user_id=user_id,
                mes=bd.month,
                ano=bd.year,
                quant_clientes=qc,
                capacidade_atendimento=_capacidade_from_basic_data(bd),
                faturamento=fat,
                gastos_vendas=gv,
                custo_mercadorias=cm,
                custo_fixo_total=cf,
                corresponde_caixa=None,
                created_at=datetime.now(),
                **calc,
            )
        )
        created += 1

    if created:
        await db.commit()

    return created
