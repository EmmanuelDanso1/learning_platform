"""add partner table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if 'partner' not in inspect(bind).get_table_names():
        op.create_table(
            'partner',
            sa.Column('id',            sa.Integer(),     nullable=False),
            sa.Column('name',          sa.String(150),   nullable=False),
            sa.Column('description',   sa.String(255),   nullable=True),
            sa.Column('website_url',   sa.String(500),   nullable=True),
            sa.Column('logo_filename', sa.String(255),   nullable=True),
            sa.Column('is_active',     sa.Boolean(),     nullable=False, server_default=sa.true()),
            sa.Column('display_order', sa.Integer(),     nullable=False, server_default='0'),
            sa.Column('created_at',    sa.DateTime(),    nullable=True),
            sa.Column('admin_id',      sa.Integer(),     nullable=False),
            sa.ForeignKeyConstraint(['admin_id'], ['admin.id']),
            sa.PrimaryKeyConstraint('id'),
        )


def downgrade():
    op.drop_table('partner')
