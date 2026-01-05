from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class Subcategory(Base):
    __tablename__ = "subcategories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    # Relationships
    category = relationship("Category", back_populates="subcategories")
    products = relationship("Product", back_populates="subcategory")
    canonical_products = relationship("CanonicalProduct", back_populates="subcategory")
    canonical_products_minimal = relationship("CanonicalProductMinimal", back_populates="subcategory")
    canonical_products_production = relationship("CanonicalProductProduction", back_populates="subcategory")
