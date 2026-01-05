from sqlalchemy import Column, Integer, String, Numeric, Boolean, ForeignKey, Text, JSON, Index
from sqlalchemy.orm import relationship
from app.db.base import Base


class CanonicalProduct(Base):
    __tablename__ = "canonical_products"

    id = Column(Integer, primary_key=True, index=True)

    # Basic product information
    name = Column(String(255), nullable=False)
    sku = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    selling_price = Column(Numeric(10, 2), nullable=False, default=0.00)

    # Classification
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    subcategory_id = Column(Integer, ForeignKey("subcategories.id"), nullable=True)

    # Vendor and visibility
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True)
    visibility = Column(Boolean, default=True, nullable=False)
    # Brand (optional)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=True)

    # SEO and meta
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(String(500), nullable=True)
    keywords = Column(JSON, nullable=True)
    slug = Column(String(255), nullable=True, unique=True, index=True)

    # Relationships
    category = relationship("Category", back_populates="canonical_products")
    subcategory = relationship("Subcategory", back_populates="canonical_products")
    vendor = relationship("Vendor", back_populates="canonical_products")
    brand = relationship("Brand", back_populates="canonical_products")

    # Related objects
    product_images = relationship(
        "ProductImage",
        back_populates="canonical_product",
        cascade="all, delete-orphan",
    )

    embeddings = relationship(
        "CanonicalProductEmbedding",
        back_populates="canonical_product",
        cascade="all, delete-orphan",
    )

    product_variants = relationship(
        "ProductVariant",
        back_populates="canonical_product",
        cascade="all, delete-orphan",
    )

    match_approvals = relationship(
        "ProductMatchApproval",
        back_populates="target_canonical_product",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index('ix_canonical_products_sku', 'sku'),
        Index('ix_canonical_products_slug', 'slug'),
    )
