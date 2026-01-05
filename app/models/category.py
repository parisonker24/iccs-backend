from sqlalchemy import Column, Integer, String, Text, DateTime, func, Enum
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum


class CategoryStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String(255), nullable=False, unique=True)
    status = Column(Enum(CategoryStatus), default=CategoryStatus.active, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    products = relationship("Product", back_populates="category")
    canonical_products = relationship("CanonicalProduct", back_populates="category")
    canonical_products_minimal = relationship("CanonicalProductMinimal", back_populates="category")
    canonical_products_production = relationship("CanonicalProductProduction", back_populates="category")
    subcategories = relationship("Subcategory", back_populates="category", cascade="all, delete-orphan")
