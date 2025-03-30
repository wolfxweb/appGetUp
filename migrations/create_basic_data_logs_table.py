"""create basic data logs table

Revision ID: create_basic_data_logs
Revises: 
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'create_basic_data_logs'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Criar a tabela basic_data_logs
    op.create_table(
        'basic_data_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('basic_data_id', sa.Integer(), nullable=False),
        sa.Column('change_description', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['basic_data_id'], ['basic_data.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    # Criar índice para melhor performance
    op.create_index(op.f('ix_basic_data_logs_id'), 'basic_data_logs', ['id'], unique=False)


def downgrade():
    # Remover índice e tabela
    op.drop_index(op.f('ix_basic_data_logs_id'), table_name='basic_data_logs')
    op.drop_table('basic_data_logs') 