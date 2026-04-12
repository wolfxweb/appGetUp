"""Criar tabelas analise_mensal e custo_fixo

Revision ID: criar_tabelas_analise_mensal
Revises: 
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'criar_tabelas_analise_mensal'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Criar tabela custo_fixo
    op.create_table(
        'custo_fixo',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=255), nullable=False),
        sa.Column('valor', sa.Float(), nullable=False),
        sa.Column('categoria', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_custo_fixo_id', 'custo_fixo', ['id'])
    op.create_index('ix_custo_fixo_user_id', 'custo_fixo', ['user_id'])
    
    # Criar tabela analise_mensal
    op.create_table(
        'analise_mensal',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('mes', sa.Integer(), nullable=False),
        sa.Column('ano', sa.Integer(), nullable=False),
        sa.Column('capacidade_atendimento', sa.Float(), nullable=True),
        sa.Column('faturamento', sa.Float(), nullable=True),
        sa.Column('quant_clientes', sa.Integer(), nullable=True),
        sa.Column('gastos_vendas', sa.Float(), nullable=True),
        sa.Column('custo_mercadorias', sa.Float(), nullable=True),
        sa.Column('custo_fixo_total', sa.Float(), nullable=True),
        sa.Column('ticket_medio', sa.Float(), nullable=True),
        sa.Column('margem_bruta', sa.Float(), nullable=True),
        sa.Column('ponto_equilibrio', sa.Float(), nullable=True),
        sa.Column('margem_seguranca', sa.Float(), nullable=True),
        sa.Column('custo_total', sa.Float(), nullable=True),
        sa.Column('resultado', sa.Float(), nullable=True),
        sa.Column('percentual_margem', sa.Float(), nullable=True),
        sa.Column('corresponde_caixa', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'mes', 'ano', name='uq_analise_mensal_user_mes_ano')
    )
    op.create_index('ix_analise_mensal_id', 'analise_mensal', ['id'])
    op.create_index('ix_analise_mensal_user_id', 'analise_mensal', ['user_id'])
    op.create_index('ix_analise_mensal_mes', 'analise_mensal', ['mes'])
    op.create_index('ix_analise_mensal_ano', 'analise_mensal', ['ano'])


def downgrade() -> None:
    op.drop_index('ix_analise_mensal_ano', table_name='analise_mensal')
    op.drop_index('ix_analise_mensal_mes', table_name='analise_mensal')
    op.drop_index('ix_analise_mensal_user_id', table_name='analise_mensal')
    op.drop_index('ix_analise_mensal_id', table_name='analise_mensal')
    op.drop_table('analise_mensal')
    
    op.drop_index('ix_custo_fixo_user_id', table_name='custo_fixo')
    op.drop_index('ix_custo_fixo_id', table_name='custo_fixo')
    op.drop_table('custo_fixo')
