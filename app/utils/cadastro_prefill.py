"""Dados do cadastro do usuário para pré-preencher analise-mensal/cadastro."""
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.produto import Produto
from app.models.custo_fixo import CustoFixo
from app.models.basic_data import BasicData
from app.models.analise_mensal import AnaliseMensal


async def build_cadastro_prefill(user: User, db: AsyncSession) -> dict[str, Any]:
    """
    Monta valores que vêm do cadastro (perfil, produtos, custos fixos, último basic_data)
    e não precisam ser digitados de novo na análise mensal.
    """
    prefill: dict[str, Any] = {
        "service_capacity": getattr(user, "service_capacity", None),
        "ideal_profit_margin": getattr(user, "ideal_profit_margin", None),
        "production_hours": getattr(user, "production_hours", None),
        "estimated_loss_percentage": getattr(user, "estimated_loss_percentage", None),
        "sales_revenue": None,
        "sales_expenses": None,
        "input_product_expenses": None,
        "other_fixed_costs": None,
        "clients_served": None,
        "sources": {},
    }

    cap = prefill["service_capacity"]
    if cap is not None:
        try:
            prefill["clients_served"] = int(float(cap))
            prefill["sources"]["clients_served"] = "perfil"
        except (TypeError, ValueError):
            pass

    if prefill["service_capacity"] is not None:
        prefill["sources"]["service_capacity"] = "perfil"
    if prefill["ideal_profit_margin"] is not None:
        prefill["sources"]["ideal_profit_margin"] = "perfil"
    if prefill["production_hours"] is not None:
        prefill["sources"]["production_hours"] = "perfil"

    prod_result = await db.execute(
        select(
            func.coalesce(func.sum(Produto.faturamento_por_mercadoria), 0),
            func.coalesce(func.sum(Produto.gastos_com_vendas), 0),
            func.coalesce(func.sum(Produto.gastos_com_compras), 0),
        ).where(Produto.user_id == user.id)
    )
    fat_prod, gv_prod, cm_prod = prod_result.one()
    fat_prod = float(fat_prod or 0)
    gv_prod = float(gv_prod or 0)
    cm_prod = float(cm_prod or 0)

    if fat_prod > 0:
        prefill["sales_revenue"] = fat_prod
        prefill["sources"]["sales_revenue"] = "produtos"
    if gv_prod > 0:
        prefill["sales_expenses"] = gv_prod
        prefill["sources"]["sales_expenses"] = "produtos"
    if cm_prod > 0:
        prefill["input_product_expenses"] = cm_prod
        prefill["sources"]["input_product_expenses"] = "produtos"

    cf_result = await db.execute(
        select(func.coalesce(func.sum(CustoFixo.valor), 0)).where(CustoFixo.user_id == user.id)
    )
    cf_total = float(cf_result.scalar() or 0)
    if cf_total > 0:
        prefill["other_fixed_costs"] = cf_total
        prefill["sources"]["other_fixed_costs"] = "custos_fixos"

    bd_result = await db.execute(
        select(BasicData)
        .where(BasicData.user_id == user.id)
        .order_by(BasicData.is_current.desc(), BasicData.year.desc(), BasicData.month.desc())
        .limit(1)
    )
    basic_data = bd_result.scalar_one_or_none()
    if basic_data:
        if prefill["sales_revenue"] is None and basic_data.sales_revenue:
            prefill["sales_revenue"] = float(basic_data.sales_revenue)
            prefill["sources"]["sales_revenue"] = "dados_basicos"
        if prefill["sales_expenses"] is None and basic_data.sales_expenses:
            prefill["sales_expenses"] = float(basic_data.sales_expenses)
            prefill["sources"]["sales_expenses"] = "dados_basicos"
        if prefill["input_product_expenses"] is None and basic_data.input_product_expenses:
            prefill["input_product_expenses"] = float(basic_data.input_product_expenses)
            prefill["sources"]["input_product_expenses"] = "dados_basicos"
        if prefill["other_fixed_costs"] is None:
            other = (
                float(basic_data.other_fixed_costs or 0)
                + float(basic_data.pro_labore or 0)
                + float(basic_data.fixed_costs or 0)
            )
            if other > 0:
                prefill["other_fixed_costs"] = other
                prefill["sources"]["other_fixed_costs"] = "dados_basicos"

    loss_pct = prefill.get("estimated_loss_percentage")
    if (
        prefill["input_product_expenses"] is None
        and loss_pct is not None
        and prefill["sales_revenue"]
    ):
        try:
            prefill["input_product_expenses"] = float(prefill["sales_revenue"]) * float(loss_pct) / 100
            prefill["sources"]["input_product_expenses"] = "perfil"
        except (TypeError, ValueError):
            pass

    if any(prefill[k] is None for k in ("sales_revenue", "sales_expenses", "input_product_expenses")):
        am_result = await db.execute(
            select(AnaliseMensal)
            .where(AnaliseMensal.user_id == user.id)
            .order_by(AnaliseMensal.ano.desc(), AnaliseMensal.mes.desc())
            .limit(1)
        )
        ultima = am_result.scalar_one_or_none()
        if ultima:
            for field, attr in (
                ("sales_revenue", "faturamento"),
                ("sales_expenses", "gastos_vendas"),
                ("input_product_expenses", "custo_mercadorias"),
            ):
                if prefill[field] is None and getattr(ultima, attr, None):
                    prefill[field] = float(getattr(ultima, attr))
                    prefill["sources"][field] = "analise_anterior"
            if prefill["other_fixed_costs"] is None and ultima.custo_fixo_total:
                prefill["other_fixed_costs"] = float(ultima.custo_fixo_total)
                prefill["sources"]["other_fixed_costs"] = "analise_anterior"

    return prefill


def merge_cadastro_into_form_record(basic_data_record, cadastro_prefill: dict) -> None:
    """Preenche campos vazios do registro do formulário com dados do cadastro."""
    if not cadastro_prefill:
        return

    mapping = {
        "sales_revenue": "sales_revenue",
        "sales_expenses": "sales_expenses",
        "input_product_expenses": "input_product_expenses",
        "other_fixed_costs": "other_fixed_costs",
        "clients_served": "clients_served",
        "service_capacity": "service_capacity",
        "ideal_profit_margin": "ideal_service_profit_margin",
        "production_hours": "work_hours_per_week",
    }

    for src_key, dest_attr in mapping.items():
        val = cadastro_prefill.get(src_key)
        if val is None:
            continue
        if src_key == "service_capacity":
            val = str(int(val)) if float(val) == int(float(val)) else str(val)
        current = getattr(basic_data_record, dest_attr, None)
        if current is None or current == "" or current == 0:
            setattr(basic_data_record, dest_attr, val)
