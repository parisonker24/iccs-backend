from __future__ import annotations
from enum import Enum as PyEnum
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Enum,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid


class DocumentType(PyEnum):
    PAN = "PAN"
    GST = "GST"
    LICENSE = "LICENSE"


class VendorKYCDocument(Base):
    __tablename__ = "vendor_kyc_documents"

    id = Column(Integer, primary_key=True, index=True)
    # Link to vendor_accounts.id (UUID)
    vendor_id = Column(PG_UUID(as_uuid=True), ForeignKey("vendor_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(Enum(DocumentType, name="vendor_document_type"), nullable=False)
    document_url = Column(String(1000), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship to VendorAccount model
    vendor = relationship("VendorAccount", back_populates="kyc_documents")
