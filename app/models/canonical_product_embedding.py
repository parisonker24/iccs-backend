from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from app.db.base import Base


class CanonicalProductEmbedding(Base):
    __tablename__ = "canonical_product_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    canonical_product_id = Column(
        Integer,
        ForeignKey("canonical_products.id", ondelete="CASCADE"),
        nullable=False,
    )
    model = Column(String(200), nullable=False)
    vector = Column(ARRAY(Float), nullable=False)

    canonical_product = relationship(
        "CanonicalProduct",
        back_populates="embeddings",
    )
