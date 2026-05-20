"""Adicionar margem_contribuicao_por_cliente e corrigir ponto_equilibrio/margem_seguranca historicos

Revision ID: add_margem_contribuicao_por_cliente
Revises: criar_tabelas_analise_mensal
Create Date: 2026-05-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = 'add_margem_contribuicao_por_cliente'
down_revision = 'criar_tabelas_analise_mensal'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adicionar nova coluna calculada
    op.add_column(
        'analise_mensal',
        sa.Column('margem_contribuicao_por_cliente', sa.Float(), nullable=True)
    )

    # Recalcular campos com fórmula correta nos registros existentes.
    # Fórmulas corrigidas:
    #   margem_bruta                  = faturamento - gastos_vendas - custo_mercadorias
    #   margem_contribuicao_por_cliente = margem_bruta / quant_clientes
    #   ponto_equilibrio (R$)         = custo_fixo_total * faturamento / margem_bruta
    #   margem_seguranca (%)          = (faturamento - ponto_equilibrio) / faturamento * 100
    conn = op.get_bind()
    conn.execute(text("""
        UPDATE analise_mensal
        SET
            margem_bruta = CASE
                WHEN faturamento IS NOT NULL AND gastos_vendas IS NOT NULL AND custo_mercadorias IS NOT NULL
                THEN faturamento - gastos_vendas - custo_mercadorias
                ELSE margem_bruta
            END,
            margem_contribuicao_por_cliente = CASE
                WHEN faturamento IS NOT NULL AND gastos_vendas IS NOT NULL
                     AND custo_mercadorias IS NOT NULL AND quant_clientes > 0
                THEN (faturamento - gastos_vendas - custo_mercadorias) / quant_clientes
                ELSE NULL
            END,
            ponto_equilibrio = CASE
                WHEN custo_fixo_total IS NOT NULL AND faturamento IS NOT NULL
                     AND (faturamento - gastos_vendas - custo_mercadorias) > 0
                THEN custo_fixo_total * faturamento / (faturamento - gastos_vendas - custo_mercadorias)
                ELSE NULL
            END,
            margem_seguranca = CASE
                WHEN faturamento > 0
                     AND custo_fixo_total IS NOT NULL
                     AND (faturamento - gastos_vendas - custo_mercadorias) > 0
                THEN ((faturamento - (custo_fixo_total * faturamento / (faturamento - gastos_vendas - custo_mercadorias)))
                      / faturamento) * 100
                ELSE NULL
            END
        WHERE faturamento IS NOT NULL
    """))


def downgrade() -> None:
    op.drop_column('analise_mensal', 'margem_contribuicao_por_cliente')
