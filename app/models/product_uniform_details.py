from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base

class ProductUniformDetails(Base):
    __tablename__ = "product_uniform_details"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False
    )

    gender = Column(String(20), nullable=True)
    school_name = Column(String(200), nullable=True)
    fabric_type = Column(String(100), nullable=True)
    color = Column(String(100), nullable=True)

    # Example: ["XS", "S", "M", "L", "XL"]
    size_variants = Column(JSON, nullable=True)

    # Optional: {"Chest":"30","Length":"24"}
    measurements = Column(JSON, nullable=True)

    product = relationship("Product", back_populates="uniform_details")