"""Adapter: AnaliseMensal <-> campos do formulário de Dados Básicos."""
from types import SimpleNamespace
from typing import Any, Optional

from app.models.analise_mensal import AnaliseMensal
from app.utils.cadastro_prefill import merge_cadastro_into_form_record


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
    cadastro_prefill: Optional[dict[str, Any]] = None,
) -> dict:
    """Contexto comum para renderizar basic_data_form em modo analise_mensal."""
    basic_data = analise_to_form_record(analise) if analise else SimpleNamespace(
        id=None,
        month=current_month,
        year=current_year,
        clients_served=0,
        sales_revenue=None,
        sales_expenses=None,
        input_product_expenses=None,
        service_capacity="",
        pro_labore=None,
        other_fixed_costs=None,
        work_hours_per_week=None,
        ideal_service_profit_margin=None,
    )

    if cadastro_prefill and not edit_mode:
        merge_cadastro_into_form_record(basic_data, cadastro_prefill)

    margin = prefill_margin
    if margin is None and cadastro_prefill:
        margin = cadastro_prefill.get("ideal_profit_margin")
    capacity = prefill_capacity
    if capacity is None and cadastro_prefill:
        capacity = cadastro_prefill.get("service_capacity")

    return {
        "persist_target": "analise_mensal",
        "edit_mode": edit_mode,
        "basic_data": basic_data,
        "current_month": analise.mes if analise else current_month,
        "current_year": analise.ano if analise else current_year,
        "prefill_margin": margin,
        "prefill_capacity": capacity,
        "cadastro_prefill": cadastro_prefill or {},
        "logs": [],
        "current_page": 1,
        "total_pages": 1,
        "per_page": 10,
        "total_logs": 0,
        "show_confirm": False,
    }
