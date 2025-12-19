"""add_nota_to_evento_venda

Revision ID: add_nota_evento
Revises: 
Create Date: 2025-12-19

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_nota_evento'
down_revision = 'create_month_importance'  # Baseado na última migration relacionada
branch_labels = None
depends_on = None


def upgrade():
    # Adicionar coluna nota na tabela evento_venda
    op.add_column('evento_venda', sa.Column('nota', sa.Float(), nullable=True))
    # Atualizar registros existentes para ter nota = 0.0
    op.execute("UPDATE evento_venda SET nota = 0.0 WHERE nota IS NULL")


def downgrade():
    # Remover coluna nota da tabela evento_venda
    op.drop_column('evento_venda', 'nota')

