from sqlalchemy import Column, Integer, String, Numeric, Boolean, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from app.db.base import Base


class CanonicalProductMinimal(Base):
    __tablename__ = "canonical_products_minimal"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Basic product information
    name = Column(String(255), nullable=False)
    sku = Column(String(100), nullable=False, unique=True, index=True)
    selling_price = Column(Numeric(10, 2), nullable=False)

    # Classification
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    subcategory_id = Column(Integer, ForeignKey("subcategories.id"), nullable=True)

    # Vendor and visibility
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True)
    visibility = Column(Boolean, default=True, nullable=False)

    # SEO fields
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(String(500), nullable=True)
    keywords = Column(JSON, nullable=True)

    # Slug
    slug = Column(String(255), nullable=True, unique=True, index=True)

    # Relationships
    category = relationship("Category", back_populates="canonical_products_minimal")
    subcategory = relationship("Subcategory", back_populates="canonical_products_minimal")
    vendor = relationship("Vendor", back_populates="canonical_products_minimal")

    # Indexes
    __table_args__ = (
        Index('ix_canonical_products_minimal_sku', 'sku'),
        Index('ix_canonical_products_minimal_slug', 'slug'),
    )
