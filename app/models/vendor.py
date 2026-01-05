from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import uuid


class Vendor(Base):
    __tablename__ = "vendors"

    # Internal DB ID
    id = Column(Integer, primary_key=True, index=True)

    # Public API ID
    vendor_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)

    # Basic info
    name = Column(String(150), unique=True, nullable=False)
    contact_email = Column(String(200))
    phone = Column(String(50))
    address = Column(Text)

    # Approval / KYC
    status = Column(String(20), default="PENDING", index=True)
    verification = Column(String(20), default="UNVERIFIED")
    is_kyc_verified = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    products = relationship("Product", back_populates="vendor")
    canonical_products = relationship("CanonicalProduct", back_populates="vendor")
    canonical_products_minimal = relationship("CanonicalProductMinimal", back_populates="vendor")
    canonical_products_production = relationship("CanonicalProductProduction", back_populates="vendor")
