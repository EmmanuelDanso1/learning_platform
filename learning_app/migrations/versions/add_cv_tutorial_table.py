"""add cv_tutorial table

Revision ID: a1b2c3d4e5f6
Revises: 811c585b5626
Create Date: 2026-05-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = 'a1b2c3d4e5f6'
down_revision = '811c585b5626'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if 'cv_tutorial' not in inspect(bind).get_table_names():
        op.create_table(
            'cv_tutorial',
            sa.Column('id',          sa.Integer(),     nullable=False),
            sa.Column('title',       sa.String(200),   nullable=False),
            sa.Column('description', sa.Text(),        nullable=True),
            sa.Column('youtube_url', sa.String(500),   nullable=False),
            sa.Column('is_active',   sa.Boolean(),     nullable=False, server_default=sa.true()),
            sa.Column('posted_at',   sa.DateTime(),    nullable=True),
            sa.Column('admin_id',    sa.Integer(),     nullable=False),
            sa.ForeignKeyConstraint(['admin_id'], ['admin.id']),
            sa.PrimaryKeyConstraint('id'),
        )


def downgrade():
    op.drop_table('cv_tutorial')
