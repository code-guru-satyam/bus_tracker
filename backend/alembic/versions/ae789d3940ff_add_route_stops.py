"""add_route_stops

Revision ID: ae789d3940ff
Revises: fa7f6c531edd
Create Date: 2026-06-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae789d3940ff'
down_revision: Union[str, Sequence[str], None] = 'fa7f6c531edd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'route_stops',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('route_id', sa.Integer(), nullable=False),
        sa.Column('stop_name', sa.String(length=120), nullable=False),
        sa.Column('latitude', sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column('longitude', sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['route_id'], ['routes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('route_id', 'sequence_number', name='uq_route_stops_route_sequence'),
    )
    op.create_index('ix_route_stops_route_id', 'route_stops', ['route_id'], unique=False)
    op.create_index('ix_route_stops_sequence_number', 'route_stops', ['sequence_number'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_route_stops_sequence_number', table_name='route_stops')
    op.drop_index('ix_route_stops_route_id', table_name='route_stops')
    op.drop_table('route_stops')
