"""added activate and deactivate route

Revision ID: 37933028d7f7
Revises: 916f3a06f799
Create Date: 2025-12-23
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '37933028d7f7'
down_revision = '916f3a06f799'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.add_column(
            sa.Column(
                'is_active',
                sa.Boolean(),
                nullable=False,
                server_default=sa.true()
            )
        )

def downgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('is_active')

