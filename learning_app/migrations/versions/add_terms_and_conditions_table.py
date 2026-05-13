"""add terms_and_conditions table

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-05-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if 'terms_and_conditions' not in inspect(bind).get_table_names():
        op.create_table(
            'terms_and_conditions',
            sa.Column('id',         sa.Integer(),  nullable=False),
            sa.Column('content',    sa.Text(),     nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('admin_id',   sa.Integer(),  nullable=False),
            sa.ForeignKeyConstraint(['admin_id'], ['admin.id']),
            sa.PrimaryKeyConstraint('id'),
        )


def downgrade():
    op.drop_table('terms_and_conditions')
