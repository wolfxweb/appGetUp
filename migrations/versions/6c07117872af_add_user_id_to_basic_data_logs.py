"""add user_id to basic_data_logs

Revision ID: 6c07117872af
Revises: c828a81d1dcb
Create Date: 2025-06-07 09:34:34.298104

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6c07117872af'
down_revision = 'c828a81d1dcb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('basic_data_logs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_basic_data_logs_user_id_users',
            'users',
            ['user_id'], ['id'],
            ondelete='CASCADE'
        )


def downgrade() -> None:
    with op.batch_alter_table('basic_data_logs', schema=None) as batch_op:
        batch_op.drop_constraint('fk_basic_data_logs_user_id_users', type_='foreignkey')
        batch_op.drop_column('user_id') 