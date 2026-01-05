"""add_product_match_approvals_table

Revision ID: add_product_match_approvals_table
Revises: 1d67922a1fff
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_product_match_approvals_table'
down_revision: Union[str, None] = '1d67922a1fff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create product_match_approvals table
    op.create_table('product_match_approvals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_product_id', sa.Integer(), nullable=False),
        sa.Column('target_canonical_product_id', sa.Integer(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('confidence_label', sa.String(length=100), nullable=False),
        sa.Column('admin_decision', sa.String(length=20), nullable=True),  # 'approved', 'rejected', 'pending'
        sa.Column('admin_id', sa.Integer(), nullable=True),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['source_product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_canonical_product_id'], ['canonical_products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    # Create indexes
    op.create_index(op.f('ix_product_match_approvals_id'), 'product_match_approvals', ['id'], unique=False)
    op.create_index(op.f('ix_product_match_approvals_source_product_id'), 'product_match_approvals', ['source_product_id'], unique=False)
    op.create_index(op.f('ix_product_match_approvals_target_canonical_product_id'), 'product_match_approvals', ['target_canonical_product_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_product_match_approvals_target_canonical_product_id'), table_name='product_match_approvals')
    op.drop_index(op.f('ix_product_match_approvals_source_product_id'), table_name='product_match_approvals')
    op.drop_index(op.f('ix_product_match_approvals_id'), table_name='product_match_approvals')
    # Drop table
    op.drop_table('product_match_approvals')
