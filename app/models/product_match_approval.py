from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class ProductMatchApproval(Base):
	__tablename__ = "product_match_approvals"

	id = Column(Integer, primary_key=True, index=True)
	source_product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
	target_canonical_product_id = Column(Integer, ForeignKey("canonical_products.id"), nullable=True)
	admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
	admin_decision = Column(String(50), default="pending", nullable=False)
	notes = Column(Text, nullable=True)
	created_at = Column(DateTime, default=datetime.utcnow)
	updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

	# Relationships
	source_product = relationship("Product", back_populates="match_approvals")
	target_canonical_product = relationship("CanonicalProduct", back_populates="match_approvals")
	admin = relationship("User")
