"""create canonical_products and canonical_product_embeddings tables

Revision ID: 0002_add_canonical_products
Revises: 0001_add_user_role
Create Date: 2025-11-29 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0002_add_canonical_products'
down_revision = '0001_add_user_role'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create canonical_products
    op.create_table(
        'canonical_products',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('subcategory_id', sa.Integer(), nullable=True),
        sa.Column('brand_id', sa.Integer(), nullable=True),
        sa.Column('short_description', sa.String(length=500), nullable=True),
        sa.Column('long_description', sa.Text(), nullable=True),
        sa.Column('isbn', sa.String(length=100), nullable=True),
        sa.Column('sku', sa.String(length=100), nullable=True),
        sa.Column('attributes', sa.JSON(), nullable=True),
    )

    # Create canonical_product_embeddings
    op.create_table(
        'canonical_product_embeddings',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('canonical_product_id', sa.Integer(), nullable=False),
        sa.Column('model', sa.String(length=200), nullable=False),
        sa.Column('vector', postgresql.ARRAY(sa.Float()), nullable=False),
        sa.ForeignKeyConstraint(['canonical_product_id'], ['canonical_products.id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    op.drop_table('canonical_product_embeddings')
    op.drop_table('canonical_products')
