from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class VendorAdminItem(BaseModel):
    vendor_id: str = Field(..., description="Unique identifier for the vendor")
    business_name: str = Field(..., description="Name of the business")
    business_type: Optional[str] = Field(None, description="Type of business")
    status: str = Field(..., description="Current status of the vendor (active, inactive, suspended)")
    verification: str = Field(..., description="Verification status (verified, pending, rejected)")
    rating: float = Field(..., description="Average rating of the vendor")
    contact_person: str = Field(..., description="Name of the contact person")
    phone: str = Field(..., description="Phone number")
    email: str = Field(..., description="Email address")
    joined_date: datetime = Field(..., description="Date when the vendor joined")
    total_products: int = Field(..., description="Total number of products listed by the vendor")
    total_orders: int = Field(..., description="Total number of orders received")
    total_revenue: float = Field(..., description="Total revenue generated")


class VendorAdminListResponse(BaseModel):
    total: int = Field(..., description="Total number of vendors matching the criteria")
    vendors: List[VendorAdminItem] = Field(..., description="List of vendor details")

    class Config:
        from_attributes = True
