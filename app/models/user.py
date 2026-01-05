from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, Enum
from app.db.base import Base
from sqlalchemy.orm import relationship
import enum

class UserRole(str, enum.Enum):
    admin = "admin"
    vendor = "vendor"
    customer = "customer"
    delivery_partner = "delivery_partner"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.customer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    orders = relationship("Order", back_populates="user")
