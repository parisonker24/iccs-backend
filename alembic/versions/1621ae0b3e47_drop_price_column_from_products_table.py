"""drop price column from products table

Revision ID: 1621ae0b3e47
Revises: 4567890ab
Create Date: 2025-12-03 09:44:56.468673

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1621ae0b3e47'
down_revision: Union[str, Sequence[str], None] = '4567890ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the 'price' column from products table if it exists
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS price;")


def downgrade() -> None:
    """Downgrade schema."""
    pass
