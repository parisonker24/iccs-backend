from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal


class VendorAdminKYCRequest(BaseModel):
    # vendor_id is expected to be the UUID string of the vendor account
    vendor_id: str = Field(..., description="UUID of vendor")
    # Incoming API uses `status` values Approved/Rejected; map to internal actions
    status: Literal["APPROVED", "REJECTED"] = Field(..., description="APPROVED or REJECTED")
    rejection_reason: Optional[str] = None

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "vendor_id": "8f14e45f-ea1a-4c3f-9c6f-1234567890ab",
            "status": "APPROVED",
            "rejection_reason": None,
        }
    })
