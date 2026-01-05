"""Add is_public column to products table

Revision ID: 1d67922a1fff
Revises: a8f5ee1366a3
Create Date: 2025-12-11 13:23:13.782618

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1d67922a1fff'
down_revision: Union[str, Sequence[str], None] = 'a8f5ee1366a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('products', sa.Column('is_public', sa.Boolean(), nullable=False, default=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('products', 'is_public')
