"""merge vendor heads

Revision ID: 03a7eee73232
Revises: 9d8c7b6a5e4f, b1c2d3e4f5g6
Create Date: 2025-12-31 16:24:15.349937

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '03a7eee73232'
down_revision: Union[str, Sequence[str], None] = ('9d8c7b6a5e4f', 'b1c2d3e4f5g6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
