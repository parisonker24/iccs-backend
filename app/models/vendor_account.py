from __future__ import annotations
import uuid
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Text, Boolean, DateTime, Enum, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.db.base import Base
from sqlalchemy.orm import relationship


class VendorStatus(PyEnum):
    PENDING = "PENDING"
    KYC_SUBMITTED = "KYC_SUBMITTED"
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"


class VendorAccount(Base):
    __tablename__ = "vendor_accounts"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_name = Column(String(255), nullable=False)
    owner_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone_number = Column(String(50), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    business_address = Column(Text, nullable=True)
    gst_number = Column(String(100), nullable=True)
    pan_number = Column(String(100), nullable=True)
    aadhaar_number = Column(String(100), nullable=True)
    business_license_number = Column(String(150), nullable=True)
    business_type = Column(String(100), nullable=True)

    # Document URLs for verification (optional)
    document_pan_url = Column(String(500), nullable=True)
    document_gst_url = Column(String(500), nullable=True)
    document_license_url = Column(String(500), nullable=True)
    # Banking details
    bank_name = Column(String(255), nullable=True)
    bank_account_number = Column(String(100), nullable=True)
    ifsc_code = Column(String(50), nullable=True)
    is_kyc_verified = Column(Boolean, default=False, nullable=False)
    status = Column(Enum(VendorStatus, name="vendor_status"), default=VendorStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    # KYC verification metadata
    verification_timestamp = Column(DateTime(timezone=True), nullable=True)
    kyc_rejection_reason = Column(Text, nullable=True)
    # KYC document relationship
    kyc_documents = relationship(
        "VendorKYCDocument",
        back_populates="vendor",
        cascade="all, delete-orphan",
    )
