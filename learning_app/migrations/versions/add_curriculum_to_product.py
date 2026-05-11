"""add curriculum column to product

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    cols = [c['name'] for c in inspect(bind).get_columns('product')]
    if 'curriculum' not in cols:
        with op.batch_alter_table('product', schema=None) as batch_op:
            batch_op.add_column(sa.Column('curriculum', sa.String(150), nullable=True))


def downgrade():
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.drop_column('curriculum')
