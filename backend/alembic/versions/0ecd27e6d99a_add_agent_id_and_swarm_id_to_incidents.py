"""add_agent_id_and_swarm_id_to_incidents

Revision ID: 0ecd27e6d99a
Revises: 0dc37a4543fc
Create Date: 2026-05-16 23:35:00.181465

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0ecd27e6d99a'
down_revision = '0dc37a4543fc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('incidents') as batch_op:
        batch_op.add_column(sa.Column('agent_id', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('swarm_id', sa.String(length=100), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('incidents') as batch_op:
        batch_op.drop_column('swarm_id')
        batch_op.drop_column('agent_id')
