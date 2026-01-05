from pydantic import BaseModel, ConfigDict
from typing import Optional

class InventoryBase(BaseModel):
    product_id: int
    quantity: int
    location: Optional[str] = None

class InventoryCreate(InventoryBase):
    pass

class InventoryUpdate(BaseModel):
    quantity: Optional[int] = None
    location: Optional[str] = None

class Inventory(InventoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
