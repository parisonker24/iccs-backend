"""add banking and business_type fields to vendor_accounts

Revision ID: 9d8c7b6a5e4f
Revises: f2c3b4a597d1
Create Date: 2025-12-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d8c7b6a5e4f'
down_revision: Union[str, Sequence[str], None] = 'f2c3b4a597d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add new columns to vendor_accounts: business_type, bank_name, bank_account_number, ifsc_code."""
    op.add_column('vendor_accounts', sa.Column('business_type', sa.String(length=100), nullable=True))
    op.add_column('vendor_accounts', sa.Column('bank_name', sa.String(length=255), nullable=True))
    op.add_column('vendor_accounts', sa.Column('bank_account_number', sa.String(length=100), nullable=True))
    op.add_column('vendor_accounts', sa.Column('ifsc_code', sa.String(length=50), nullable=True))


def downgrade() -> None:
    """Remove columns added in upgrade."""
    op.drop_column('vendor_accounts', 'ifsc_code')
    op.drop_column('vendor_accounts', 'bank_account_number')
    op.drop_column('vendor_accounts', 'bank_name')
    op.drop_column('vendor_accounts', 'business_type')
