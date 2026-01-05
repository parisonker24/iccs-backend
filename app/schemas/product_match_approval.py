from pydantic import BaseModel, ConfigDict
from typing import Optional


class ProductMatchApprovalCreate(BaseModel):
    source_product_id: int
    target_canonical_product_id: Optional[int] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProductMatchApprovalUpdate(BaseModel):
    admin_decision: Optional[str] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
