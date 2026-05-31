"""Adapter: AnaliseMensal <-> campos do formulário de Dados Básicos."""
from types import SimpleNamespace
from typing import Optional

from app.models.analise_mensal import AnaliseMensal


def analise_to_form_record(analise: AnaliseMensal) -> SimpleNamespace:
    """Converte registro analise_mensal para objeto usado em basic_data_form.html."""
    cap = analise.capacidade_atendimento
    capacity_str = ""
    if cap is not None:
        capacity_str = str(int(cap)) if cap == int(cap) else str(cap)

    return SimpleNamespace(
        id=analise.id,
        month=analise.mes,
        year=analise.ano,
        clients_served=analise.quant_clientes if analise.quant_clientes is not None else 0,
        sales_revenue=analise.faturamento,
        sales_expenses=analise.gastos_vendas,
        input_product_expenses=analise.custo_mercadorias,
        service_capacity=capacity_str,
        pro_labore=None,
        other_fixed_costs=analise.custo_fixo_total,
        work_hours_per_week=None,
        ideal_service_profit_margin=None,
    )


def form_context_for_analise_cadastro(
    *,
    edit_mode: bool,
    analise: Optional[AnaliseMensal],
    current_month: int,
    current_year: int,
    prefill_margin=None,
    prefill_capacity=None,
) -> dict:
    """Contexto comum para renderizar basic_data_form em modo analise_mensal."""
    basic_data = analise_to_form_record(analise) if analise else None
    return {
        "persist_target": "analise_mensal",
        "edit_mode": edit_mode,
        "basic_data": basic_data,
        "current_month": analise.mes if analise else current_month,
        "current_year": analise.ano if analise else current_year,
        "prefill_margin": prefill_margin,
        "prefill_capacity": prefill_capacity,
        "logs": [],
        "current_page": 1,
        "total_pages": 1,
        "per_page": 10,
        "total_logs": 0,
        "show_confirm": False,
    }
