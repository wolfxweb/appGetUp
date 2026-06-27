from datetime import datetime
from typing import Any, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analise_mensal import AnaliseMensal


async def save_analise_for_user(
    db: AsyncSession,
    user_id: int,
    data: Any,
) -> Dict[str, Any]:
    """Cria ou atualiza analise_mensal para o user_id informado (cliente)."""
    result = await db.execute(
        select(AnaliseMensal).filter(
            AnaliseMensal.user_id == user_id,
            AnaliseMensal.mes == data.mes,
            AnaliseMensal.ano == data.ano,
        )
    )
    analise_existente = result.scalar_one_or_none()

    if analise_existente:
        analise_existente.quant_clientes = data.quant_clientes
        analise_existente.capacidade_atendimento = data.capacidade_atendimento
        analise_existente.faturamento = data.faturamento
        analise_existente.gastos_vendas = data.gastos_vendas
        analise_existente.custo_mercadorias = data.custo_mercadorias
        analise_existente.custo_fixo_total = data.custo_fixo_total
        analise_existente.corresponde_caixa = data.corresponde_caixa
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
            "id": analise_existente.id,
        }

    nova_analise = AnaliseMensal(
        user_id=user_id,
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
        created_at=datetime.now(),
    )
    db.add(nova_analise)
    await db.commit()
    await db.refresh(nova_analise)
    return {
        "success": True,
        "message": "Análise criada com sucesso",
        "is_new": True,
        "id": nova_analise.id,
    }
