"""add user profile fields

Revision ID: add_user_profile_fields
Revises: create_basic_data_logs
Create Date: 2024-04-27 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'add_user_profile_fields'
down_revision = 'create_basic_data_logs'
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns to users table
    op.add_column('users', sa.Column('gender', sa.String(), nullable=True))
    op.add_column('users', sa.Column('birth_day', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('birth_month', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('married', sa.String(), nullable=True))
    op.add_column('users', sa.Column('children', sa.String(), nullable=True))
    op.add_column('users', sa.Column('grandchildren', sa.String(), nullable=True))
    op.add_column('users', sa.Column('cep', sa.String(), nullable=True))
    op.add_column('users', sa.Column('street', sa.String(), nullable=True))
    op.add_column('users', sa.Column('neighborhood', sa.String(), nullable=True))
    op.add_column('users', sa.Column('state', sa.String(), nullable=True))
    op.add_column('users', sa.Column('city', sa.String(), nullable=True))
    op.add_column('users', sa.Column('complement', sa.String(), nullable=True))
    op.add_column('users', sa.Column('company_activity', sa.String(), nullable=True))
    op.add_column('users', sa.Column('specialty_area', sa.String(), nullable=True))

def downgrade():
    # Remove the added columns
    op.drop_column('users', 'specialty_area')
    op.drop_column('users', 'company_activity')
    op.drop_column('users', 'complement')
    op.drop_column('users', 'city')
    op.drop_column('users', 'state')
    op.drop_column('users', 'neighborhood')
    op.drop_column('users', 'street')
    op.drop_column('users', 'cep')
    op.drop_column('users', 'grandchildren')
    op.drop_column('users', 'children')
    op.drop_column('users', 'married')
    op.drop_column('users', 'birth_month')
    op.drop_column('users', 'birth_day')
    op.drop_column('users', 'gender') 