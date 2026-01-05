from pydantic import BaseModel, ConfigDict
from typing import Optional


class SubcategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: int


class SubcategoryCreate(SubcategoryBase):
    pass


class SubcategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None


class Subcategory(SubcategoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
