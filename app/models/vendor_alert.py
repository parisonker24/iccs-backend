from __future__ import annotations
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.db.base import Base

class VendorAlert(Base):
    __tablename__ = "vendor_alerts"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(PG_UUID(as_uuid=True), ForeignKey("vendor_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_type = Column(String(100), nullable=False)
    message = Column(String(1000), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
