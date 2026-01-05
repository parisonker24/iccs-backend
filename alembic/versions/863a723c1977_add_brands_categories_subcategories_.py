
"""add_brands_categories_subcategories_tables

Revision ID: 863a723c1977
Revises: 0002_add_canonical_products
Create Date: 2025-11-30 15:00:14.416230

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '863a723c1977'
down_revision: Union[str, Sequence[str], None] = '0002_add_canonical_products'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order
    op.drop_table('subcategories')
    op.drop_table('brands')
    op.drop_table('categories')
