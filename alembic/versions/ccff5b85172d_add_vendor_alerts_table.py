"""add vendor alerts table

Revision ID: ccff5b85172d
Revises: 03a7eee73232
Create Date: 2026-01-05 13:16:15.873246

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ccff5b85172d'
down_revision: Union[str, Sequence[str], None] = '03a7eee73232'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
