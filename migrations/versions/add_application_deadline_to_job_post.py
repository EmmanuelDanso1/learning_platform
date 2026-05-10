"""add application_deadline to job_post

Revision ID: deadline20260508
Revises: c2d3e4f5g6h7
Create Date: 2026-05-08 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'deadline20260508'
down_revision = 'c2d3e4f5g6h7'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('job_post', schema=None) as batch_op:
        batch_op.add_column(sa.Column('application_deadline', sa.DateTime(), nullable=True))

def downgrade():
    with op.batch_alter_table('job_post', schema=None) as batch_op:
        batch_op.drop_column('application_deadline')
