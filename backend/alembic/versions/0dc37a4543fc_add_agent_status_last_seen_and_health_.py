"""add_agent_status_last_seen_and_health_history_defaults

Revision ID: 0dc37a4543fc
Revises: b2de966705b7
Create Date: 2026-05-12 20:18:09.710495+05:30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0dc37a4543fc'
down_revision: Union[str, None] = 'b2de966705b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add status and last_seen to agents table (nullable first for SQLite compatibility)
    with op.batch_alter_table('agents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(20), nullable=True))
        batch_op.add_column(sa.Column('last_seen', sa.DateTime(), nullable=True))
    
    # Update existing rows with defaults
    op.execute("UPDATE agents SET status = 'offline' WHERE status IS NULL")
    
    # Make status non-nullable and lie_rate nullable (SQLite batch mode)
    with op.batch_alter_table('agents', schema=None) as batch_op:
        batch_op.alter_column('status', existing_type=sa.String(20), nullable=False)
    
    with op.batch_alter_table('agent_health_history', schema=None) as batch_op:
        batch_op.alter_column('lie_rate', existing_type=sa.Float(), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table('agent_health_history', schema=None) as batch_op:
        batch_op.alter_column('lie_rate', existing_type=sa.Float(), nullable=False)
    
    with op.batch_alter_table('agents', schema=None) as batch_op:
        batch_op.drop_column('last_seen')
        batch_op.drop_column('status')
