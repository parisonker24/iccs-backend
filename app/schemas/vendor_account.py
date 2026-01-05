from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime


class VendorCreate(BaseModel):
    business_name: str = Field(..., min_length=1)
    owner_name: str = Field(..., min_length=1)
    email: EmailStr
    phone_number: str = Field(..., min_length=6)
    password: str = Field(..., min_length=8)
    business_address: Optional[str] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    aadhaar_number: Optional[str] = None
    business_license_number: Optional[str] = None
    business_type: Optional[str] = None
    document_pan_url: Optional[str] = None
    document_gst_url: Optional[str] = None
    document_license_url: Optional[str] = None
    verification_timestamp: Optional[datetime] = None
    kyc_rejection_reason: Optional[str] = None
    # Banking details
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    ifsc_code: Optional[str] = None


class VendorResponse(BaseModel):
    id: UUID
    business_name: str
    owner_name: str
    email: EmailStr
    phone_number: str
    business_address: Optional[str] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    business_type: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    is_kyc_verified: bool
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VendorKYCStatus(BaseModel):
    vendor_id: UUID
    business_name: str
    is_kyc_verified: bool
    status: str
    rejection_reason: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
