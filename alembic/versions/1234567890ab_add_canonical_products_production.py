"""add_canonical_products_production_table

Revision ID: 1234567890ab
Revises: 863a723c1977
Create Date: 2025-11-30 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1234567890ab'
down_revision: Union[str, Sequence[str], None] = '863a723c1977'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create canonical_products_production table
    op.create_table(
        'canonical_products_production',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('sku', sa.String(length=100), nullable=False),
        sa.Column('selling_price', sa.Numeric(precision=10, scale=2), nullable=False, default=0.00),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('subcategory_id', sa.Integer(), nullable=True),
        sa.Column('vendor_id', sa.Integer(), nullable=True),
        sa.Column('visibility', sa.Boolean(), nullable=False, default=True),
        sa.Column('meta_title', sa.String(length=255), nullable=True),
        sa.Column('meta_description', sa.String(length=500), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('slug', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
        sa.ForeignKeyConstraint(['subcategory_id'], ['subcategories.id'], ),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sku'),
        sa.UniqueConstraint('slug'),
        sa.CheckConstraint('selling_price >= 0', name='check_selling_price_positive')
    )
    # Create indexes
    op.create_index('ix_canonical_products_production_sku', 'canonical_products_production', ['sku'], unique=False)
    op.create_index('ix_canonical_products_production_slug', 'canonical_products_production', ['slug'], unique=False)
    op.create_index(op.f('ix_canonical_products_production_id'), 'canonical_products_production', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index(op.f('ix_canonical_products_production_id'), table_name='canonical_products_production')
    op.drop_index('ix_canonical_products_production_slug', table_name='canonical_products_production')
    op.drop_index('ix_canonical_products_production_sku', table_name='canonical_products_production')
    # Drop table
    op.drop_table('canonical_products_production')
