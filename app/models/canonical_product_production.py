from sqlalchemy import Column, Integer, String, Numeric, Boolean, ForeignKey, JSON, Index, CheckConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base


class CanonicalProductProduction(Base):
    __tablename__ = "canonical_products_production"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Basic product information
    name = Column(String(255), nullable=False)  # Frontend: Product Name input field
    sku = Column(String(100), nullable=False, unique=True, index=True)  # Frontend: SKU input field, unique constraint
    selling_price = Column(Numeric(10, 2), nullable=False, default=0.00)  # Frontend: Selling Price input field, default 0.00

    # Classification
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)  # Frontend: Category dropdown
    subcategory_id = Column(Integer, ForeignKey("subcategories.id"), nullable=True)  # Frontend: Subcategory dropdown

    # Vendor and visibility
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True)  # Frontend: Vendor selection
    visibility = Column(Boolean, default=True, nullable=False)  # Frontend: Visibility toggle, default True

    # SEO fields
    meta_title = Column(String(255), nullable=True)  # Frontend: Meta Title input
    meta_description = Column(String(500), nullable=True)  # Frontend: Meta Description textarea
    keywords = Column(JSON, nullable=True)  # Frontend: Keywords input (JSON array)

    # Slug
    slug = Column(String(255), nullable=True, unique=True, index=True)  # Frontend: Slug input, unique constraint

    # Relationships
    category = relationship("Category", back_populates="canonical_products_production")
    subcategory = relationship("Subcategory", back_populates="canonical_products_production")
    vendor = relationship("Vendor", back_populates="canonical_products_production")
    # Note: Product images are stored on the main `canonical_products` table
    # and related via `ProductImage.canonical_product`. Do not create a
    # duplicate relationship here unless a separate FK exists.

    # Constraints
    __table_args__ = (
        Index('ix_canonical_products_production_sku', 'sku'),
        Index('ix_canonical_products_production_slug', 'slug'),
        CheckConstraint('selling_price >= 0', name='check_selling_price_positive'),
    )
