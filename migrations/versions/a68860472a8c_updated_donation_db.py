"""updated donation db

Revision ID: a68860472a8c
Revises: 303f2d94a3c8
Create Date: 2025-05-19 11:49:26.030715

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a68860472a8c'
down_revision = '303f2d94a3c8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('donation', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name', sa.String(length=120), nullable=False))
        batch_op.add_column(sa.Column('verified', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('timestamp', sa.DateTime(), nullable=True))
        batch_op.alter_column('email',
               existing_type=sa.VARCHAR(length=100),
               type_=sa.String(length=120),
               existing_nullable=False)
        batch_op.drop_column('currency')
        batch_op.drop_column('full_name')
        batch_op.drop_column('date')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('donation', schema=None) as batch_op:
        batch_op.add_column(sa.Column('date', sa.DATETIME(), nullable=True))
        batch_op.add_column(sa.Column('full_name', sa.VARCHAR(length=100), nullable=False))
        batch_op.add_column(sa.Column('currency', sa.VARCHAR(length=10), nullable=True))
        batch_op.alter_column('email',
               existing_type=sa.String(length=120),
               type_=sa.VARCHAR(length=100),
               existing_nullable=False)
        batch_op.drop_column('timestamp')
        batch_op.drop_column('verified')
        batch_op.drop_column('name')

    # ### end Alembic commands ###
