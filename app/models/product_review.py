from __future__ import annotations
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from app.db.base import Base


class ProductReview(Base):
    __tablename__ = "product_reviews"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_name = Column(String(255), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    sentiment = Column(String(50), nullable=True)  # e.g. 'positive', 'neutral', 'negative'
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
