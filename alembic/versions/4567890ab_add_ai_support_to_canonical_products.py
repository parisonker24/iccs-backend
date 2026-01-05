"""Add AI support to canonical products

Revision ID: 4567890ab
Revises: 1234567890ab
Create Date: 2023-10-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '4567890ab'
down_revision: Union[str, None] = '1234567890ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Add embedding and match_confidence columns
    op.add_column('canonical_products', sa.Column('embedding', Vector(768), nullable=True))
    op.add_column('canonical_products', sa.Column('match_confidence', sa.Float(), nullable=True))


def downgrade() -> None:
    # Remove the columns
    op.drop_column('canonical_products', 'match_confidence')
    op.drop_column('canonical_products', 'embedding')

    # Optionally drop the extension if no longer needed
    # op.execute("DROP EXTENSION IF EXISTS vector")
