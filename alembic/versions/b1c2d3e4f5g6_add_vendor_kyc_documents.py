"""add vendor_kyc_documents table

Revision ID: b1c2d3e4f5g6
Revises: 
Create Date: 2025-12-19 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b1c2d3e4f5g6'
down_revision = 'f2c3b4a597d1'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum type for document_type
    vendor_document_type = postgresql.ENUM('PAN', 'GST', 'LICENSE', name='vendor_document_type')
    vendor_document_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'vendor_kyc_documents',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('vendor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vendor_accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_type', sa.Enum('PAN', 'GST', 'LICENSE', name='vendor_document_type'), nullable=False),
        sa.Column('document_url', sa.String(length=1000), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_vendor_kyc_documents_vendor_id', 'vendor_kyc_documents', ['vendor_id'])


def downgrade():
    op.drop_index('ix_vendor_kyc_documents_vendor_id', table_name='vendor_kyc_documents')
    op.drop_table('vendor_kyc_documents')
    # Drop enum type
    vendor_document_type = postgresql.ENUM('PAN', 'GST', 'LICENSE', name='vendor_document_type')
    vendor_document_type.drop(op.get_bind(), checkfirst=True)
