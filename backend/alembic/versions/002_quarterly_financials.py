"""Add quarterly_financials table

Revision ID: 002
Revises: 001
Create Date: 2026-05-30

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'quarterly_financials',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('ticker', sa.String(10), nullable=False, index=True),
        sa.Column('fiscal_quarter', sa.String(10), nullable=False),
        sa.Column('income_statement', postgresql.JSON),
        sa.Column('balance_sheet', postgresql.JSON),
        sa.Column('cash_flow', postgresql.JSON),
        sa.Column('earnings', postgresql.JSON),
        sa.Column('fetched_at', sa.DateTime, default=sa.func.now()),
        sa.UniqueConstraint('ticker', 'fiscal_quarter', name='uq_ticker_quarter'),
    )


def downgrade() -> None:
    op.drop_table('quarterly_financials')
