from sqlalchemy import Column, Integer, String, Text
from app.db.base import Base
from sqlalchemy.orm import relationship

class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    canonical_products = relationship("CanonicalProduct", back_populates="brand")
    # Relationship for regular Product entries
    products = relationship("Product", back_populates="brand")
