from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class ProductVariant(Base):
    __tablename__ = "product_variants"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key to canonical product
    canonical_product_id = Column(Integer, ForeignKey("canonical_products.id"), nullable=False)

    # Variant details (for future support of size/color etc.)
    variant_type = Column(String(100), nullable=False)  # e.g., 'size', 'color'
    variant_value = Column(String(100), nullable=False)  # e.g., 'M', 'Red'

    # Variant-specific fields
    sku = Column(String(100), nullable=True, index=True)  # Variant-specific SKU
    price_adjustment = Column(Numeric(10, 2), nullable=True)  # Price adjustment for this variant
    stock_count = Column(Integer, nullable=True)  # Stock count for this variant

    # Relationship back to canonical product
    canonical_product = relationship("CanonicalProduct", back_populates="product_variants")
