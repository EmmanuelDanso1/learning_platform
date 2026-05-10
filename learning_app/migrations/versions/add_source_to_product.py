"""add source column to product

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    cols = [c['name'] for c in inspect(bind).get_columns('product')]
    if 'source' not in cols:
        with op.batch_alter_table('product', schema=None) as batch_op:
            batch_op.add_column(sa.Column('source', sa.String(255), nullable=True))


def downgrade():
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.drop_column('source')
