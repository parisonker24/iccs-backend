from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_user
from app.db.session import get_db
from app.crud import crud_user
from app.crud.crud_vendor_account import (
    get_vendor_by_email,
    update_vendor_kyc,
    get_vendor_by_id,
)
from sqlalchemy.future import select
from app.schemas.vendor_kyc import VendorKYCRequest
from pydantic import BaseModel, HttpUrl
from app.models.vendor_kyc_document import VendorKYCDocument, DocumentType
from app.models.vendor_account import VendorStatus
from app.schemas.vendor_account import VendorResponse, VendorKYCStatus
from app.models.user import UserRole
from typing import Optional

router = APIRouter()


class DocumentURLs(BaseModel):
    document_pan_url: HttpUrl
    document_gst_url: HttpUrl
    document_license_url: HttpUrl


@router.post("/kyc/submit", response_model=VendorKYCStatus)
async def submit_vendor_kyc(
    kyc_in: DocumentURLs,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit vendor KYC documents (only URLs). This will:
    - validate incoming URLs
    - prevent duplicate submissions
    - save documents into `vendor_kyc_documents`
    - set vendor account status to PENDING
    """
    # Resolve full user
    try:
        user_id = int(current_user.id)
    except Exception:
        user_id = current_user.id

    db_user = await crud_user.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unable to resolve user")

    if db_user.role != UserRole.vendor:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only vendors may submit KYC")

    # Find vendor account by email associated with the user
    vendor = await get_vendor_by_email(db, db_user.email)
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor profile not found for current user")

    # Prevent duplicate submissions: if any KYC document already exists for this vendor
    existing = await db.execute(select(VendorKYCDocument).where(VendorKYCDocument.vendor_id == vendor.id))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="KYC documents already submitted")
    if getattr(vendor, "is_kyc_verified", False):
        raise HTTPException(status_code=400, detail="KYC already verified")

    # Create VendorKYCDocument records
    docs = [
        VendorKYCDocument(vendor_id=vendor.id, document_type=DocumentType.PAN, document_url=str(kyc_in.document_pan_url)),
        VendorKYCDocument(vendor_id=vendor.id, document_type=DocumentType.GST, document_url=str(kyc_in.document_gst_url)),
        VendorKYCDocument(vendor_id=vendor.id, document_type=DocumentType.LICENSE, document_url=str(kyc_in.document_license_url)),
    ]

    try:
        for d in docs:
            db.add(d)

        # mark vendor status to PENDING (awaiting verification)
        vendor.status = VendorStatus.PENDING
        vendor.is_kyc_verified = False
        db.add(vendor)

        await db.commit()
        await db.refresh(vendor)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to submit KYC: {str(e)}")

    return {
        "vendor_id": vendor.id,
        "status": vendor.status.value if hasattr(vendor.status, 'value') else str(vendor.status),
        "is_kyc_verified": vendor.is_kyc_verified,
    }


@router.get("/kyc/status", response_model=VendorKYCStatus)
async def get_kyc_status(
    vendor_id: Optional[str] = None,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Resolve full user
    try:
        user_id = int(current_user.id)
    except Exception:
        user_id = current_user.id

    db_user = await crud_user.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unable to resolve user")

    # Admins can view any vendor by vendor_id
    if db_user.role == UserRole.admin:
        if not vendor_id:
            raise HTTPException(status_code=400, detail="vendor_id is required for admin")
        vendor = await get_vendor_by_id(db, vendor_id)
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")

    elif db_user.role == UserRole.vendor:
        # Vendor may only view their own status
        vendor = await get_vendor_by_email(db, db_user.email)
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor profile not found for current user")
        if vendor_id and str(vendor.id) != vendor_id:
            raise HTTPException(status_code=403, detail="Vendors may only view their own KYC status")

    else:
        raise HTTPException(status_code=403, detail="Only vendors or admins may view KYC status")

    return {
        "vendor_id": vendor.id,
        "business_name": vendor.business_name,
        "is_kyc_verified": vendor.is_kyc_verified,
        "status": vendor.status.value if hasattr(vendor.status, 'value') else str(vendor.status),
        "rejection_reason": vendor.kyc_rejection_reason,
        "updated_at": vendor.updated_at,
    }
