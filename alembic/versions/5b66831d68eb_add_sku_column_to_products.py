
"""add_sku_column_to_products

Revision ID: 5b66831d68eb
Revises: 1621ae0b3e47
Create Date: 2025-12-03 10:24:01.155903

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '5b66831d68eb'
down_revision: Union[str, Sequence[str], None] = '1621ae0b3e47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS sku VARCHAR(100);")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_products_sku ON products (sku);")


def downgrade() -> None:
    """Downgrade schema."""
    pass
