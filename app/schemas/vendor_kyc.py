from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from typing import Optional


class VendorKYCRequest(BaseModel):
    gst_number: str = Field(...)
    pan_number: str = Field(...)
    aadhaar_number: Optional[str] = None
    business_license_number: str = Field(...)
    document_pan_url: HttpUrl
    document_gst_url: HttpUrl
    document_license_url: HttpUrl

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "gst_number": "29ABCDE1234F1Z5",
            "pan_number": "ABCDE1234F",
            "aadhaar_number": "123412341234",
            "business_license_number": "LIC-2025-0001",
            "document_pan_url": "https://example.com/docs/pan.pdf",
            "document_gst_url": "https://example.com/docs/gst.pdf",
            "document_license_url": "https://example.com/docs/license.pdf",
        }
    })
