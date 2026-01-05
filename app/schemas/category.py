from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.category import CategoryStatus


class CategoryCreate(BaseModel):
    category_name: str
    status: Optional[CategoryStatus] = CategoryStatus.active


class CategoryUpdate(BaseModel):
    category_name: Optional[str] = None
    status: Optional[CategoryStatus] = None


class Category(BaseModel):
    id: int
    category_name: str
    status: CategoryStatus
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


CategoryOut = Category
