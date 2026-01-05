"""create vendor_accounts table and vendor_status enum

Revision ID: f2c3b4a597d1
Revises: add_product_match_approvals_table
Create Date: 2025-12-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f2c3b4a597d1'
down_revision: Union[str, Sequence[str], None] = 'add_product_match_approvals_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: create vendor_status enum and vendor_accounts table."""
    # Create vendor_status enum type
    vendor_status = sa.Enum('PENDING', 'KYC_SUBMITTED', 'ACTIVE', 'REJECTED', name='vendor_status')
    vendor_status.create(op.get_bind(), checkfirst=True)

    # Create vendor_accounts table
    op.create_table(
        'vendor_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('business_name', sa.String(length=255), nullable=False),
        sa.Column('owner_name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone_number', sa.String(length=50), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('business_address', sa.Text(), nullable=True),
        sa.Column('gst_number', sa.String(length=100), nullable=True),
        sa.Column('pan_number', sa.String(length=100), nullable=True),
        sa.Column('aadhaar_number', sa.String(length=100), nullable=True),
        sa.Column('business_license_number', sa.String(length=150), nullable=True),
        sa.Column('document_pan_url', sa.String(length=500), nullable=True),
        sa.Column('document_gst_url', sa.String(length=500), nullable=True),
        sa.Column('document_license_url', sa.String(length=500), nullable=True),
        sa.Column('is_kyc_verified', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('status', vendor_status, server_default='PENDING', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('verification_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('kyc_rejection_reason', sa.Text(), nullable=True),
    )

    # Create indexes
    op.create_index(op.f('ix_vendor_accounts_email'), 'vendor_accounts', ['email'], unique=True)
    op.create_index(op.f('ix_vendor_accounts_phone_number'), 'vendor_accounts', ['phone_number'], unique=True)
    op.create_index(op.f('ix_vendor_accounts_id'), 'vendor_accounts', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema: drop vendor_accounts table and enum."""
    # Drop indexes
    op.drop_index(op.f('ix_vendor_accounts_id'), table_name='vendor_accounts')
    op.drop_index(op.f('ix_vendor_accounts_phone_number'), table_name='vendor_accounts')
    op.drop_index(op.f('ix_vendor_accounts_email'), table_name='vendor_accounts')

    # Drop table
    op.drop_table('vendor_accounts')

    # Drop enum type
    vendor_status = sa.Enum('PENDING', 'KYC_SUBMITTED', 'ACTIVE', 'REJECTED', name='vendor_status')
    vendor_status.drop(op.get_bind(), checkfirst=True)
