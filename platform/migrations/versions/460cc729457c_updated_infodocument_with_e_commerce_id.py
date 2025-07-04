"""updated infoDocument with e_commerce id

Revision ID: 460cc729457c
Revises: 0d73ad6bdd72
Create Date: 2025-06-29 17:57:37.307079

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '460cc729457c'
down_revision = '0d73ad6bdd72'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('info_document', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ecommerce_id', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('info_document', schema=None) as batch_op:
        batch_op.drop_column('ecommerce_id')

    # ### end Alembic commands ###
