"""create_month_importance_tables

Revision ID: create_month_importance
Revises: c828a81d1dcb
Create Date: 2025-01-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import json

# revision identifiers, used by Alembic.
revision = 'create_month_importance'
down_revision = 'c828a81d1dcb'
branch_labels = None
depends_on = None

# Lista de eventos padrão
EVENTOS_PADRAO = [
    "Atividades agrícolas",
    "Comemorações e eventos religiosos",
    "Eventos esportivos",
    "Eventos folclóricos",
    "Festas de peão (rodeios)",
    "Festivais, feiras e exposições",
    "Obras e empreendimentos particulares",
    "Obras públicas",
    "Períodos de muita chuva",
    "Períodos de muito calor",
    "Comemorações de fim-de-ano",
    "Férias escolares/recessos",
    "Volta às aulas",
    "Carnaval",
    "Dia da Mulher",
    "Dia das Mães",
    "Dia dos Namorados",
    "Festas Juninas",
    "Dia dos Avós",
    "Dia dos Pais",
    "Dia da Secretária",
    "Dia das Crianças"
]

def upgrade() -> None:
    # Criar tabela mes_importancia
    op.create_table(
        'mes_importancia',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('nota_atribuida', sa.Float(), nullable=True),
        sa.Column('ritmo_negocio_percentual', sa.Float(), nullable=True),
        sa.Column('quantidade_vendas_real', sa.Float(), nullable=True),
        sa.Column('quantidade_vendas_estimada', sa.Float(), nullable=True),
        sa.Column('peso_mes', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_mes_importancia_id', 'mes_importancia', ['id'], unique=False)
    op.create_index('ix_mes_importancia_user_id', 'mes_importancia', ['user_id'], unique=False)
    op.create_index('ix_mes_importancia_year', 'mes_importancia', ['year'], unique=False)

    # Criar tabela evento_venda
    op.create_table(
        'evento_venda',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('nome_evento', sa.String(), nullable=False),
        sa.Column('aumenta_vendas', sa.Boolean(), nullable=True),
        sa.Column('diminui_vendas', sa.Boolean(), nullable=True),
        sa.Column('meses_afetados', sa.String(), nullable=True),  # JSON string com array de meses
        sa.Column('is_padrao', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_evento_venda_id', 'evento_venda', ['id'], unique=False)
    op.create_index('ix_evento_venda_user_id', 'evento_venda', ['user_id'], unique=False)

    # Criar eventos padrão para todos os usuários existentes
    conn = op.get_bind()
    
    # Buscar todos os usuários
    result = conn.execute(sa.text("SELECT id FROM users"))
    users = result.fetchall()
    
    # Inserir eventos padrão para cada usuário
    for user_row in users:
        user_id = user_row[0]
        for evento_nome in EVENTOS_PADRAO:
            conn.execute(
                sa.text("""
                    INSERT INTO evento_venda 
                    (user_id, nome_evento, aumenta_vendas, diminui_vendas, meses_afetados, is_padrao, created_at, updated_at)
                    VALUES (:user_id, :nome_evento, 0, 0, NULL, 1, datetime('now'), datetime('now'))
                """),
                {'user_id': user_id, 'nome_evento': evento_nome}
            )
    
    conn.commit()


def downgrade() -> None:
    # Remover índices
    op.drop_index('ix_evento_venda_user_id', table_name='evento_venda')
    op.drop_index('ix_evento_venda_id', table_name='evento_venda')
    op.drop_index('ix_mes_importancia_year', table_name='mes_importancia')
    op.drop_index('ix_mes_importancia_user_id', table_name='mes_importancia')
    op.drop_index('ix_mes_importancia_id', table_name='mes_importancia')
    
    # Remover tabelas
    op.drop_table('evento_venda')
    op.drop_table('mes_importancia')

