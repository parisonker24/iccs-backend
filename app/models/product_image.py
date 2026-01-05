from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class ProductImage(Base):
    __tablename__ = "product_images"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key to canonical product
    canonical_product_id = Column(Integer, ForeignKey("canonical_products.id"), nullable=False)

    # Image details
    image_url = Column(String(500), nullable=False)  # URL or path to the image
    alt_text = Column(String(255), nullable=True)  # Alt text for accessibility
    is_primary = Column(Boolean, default=False, nullable=False)  # Is this the primary image?
    display_order = Column(Integer, default=0, nullable=False)  # Order for displaying images

    # Relationship back to canonical product
    canonical_product = relationship("CanonicalProduct", back_populates="product_images")
