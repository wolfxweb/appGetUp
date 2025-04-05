"""create calculator table

Revision ID: create_calculator_table
Revises: 
Create Date: 2024-03-30 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'create_calculator_table'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Criar a tabela calculator
    op.create_table(
        'calculator',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('basic_data_id', sa.Integer(), nullable=False),
        sa.Column('product_name', sa.String(), nullable=False),
        sa.Column('current_price', sa.Float(), nullable=False),
        sa.Column('current_margin', sa.Float(), nullable=False),
        sa.Column('company_margin', sa.Float(), nullable=False),
        sa.Column('desired_margin', sa.Float(), nullable=False),
        sa.Column('suggested_price', sa.Float(), nullable=False),
        sa.Column('price_relation', sa.Float(), nullable=False),
        sa.Column('competitor_price', sa.Float(), nullable=False),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['basic_data_id'], ['basic_data.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    # Criar índices para melhor performance
    op.create_index(op.f('ix_calculator_id'), 'calculator', ['id'], unique=False)
    op.create_index(op.f('ix_calculator_user_id'), 'calculator', ['user_id'], unique=False)
    op.create_index(op.f('ix_calculator_basic_data_id'), 'calculator', ['basic_data_id'], unique=False)


def downgrade():
    # Remover índices e tabela
    op.drop_index(op.f('ix_calculator_basic_data_id'), table_name='calculator')
    op.drop_index(op.f('ix_calculator_user_id'), table_name='calculator')
    op.drop_index(op.f('ix_calculator_id'), table_name='calculator')
    op.drop_table('calculator') 