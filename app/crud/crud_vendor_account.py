from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import insert
from fastapi import HTTPException
from app.models.vendor_account import VendorAccount
from sqlalchemy import select as sa_select
import uuid


async def get_vendor_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(VendorAccount).where(VendorAccount.email == email))
    return result.scalars().first()


async def get_vendor_by_phone(db: AsyncSession, phone: str):
    result = await db.execute(select(VendorAccount).where(VendorAccount.phone_number == phone))
    return result.scalars().first()


async def create_vendor_account(db: AsyncSession, *, vendor_data: dict):
    # Expect vendor_data to already contain `password_hash`
    # Validate uniqueness
    existing = await db.execute(select(VendorAccount).where((VendorAccount.email == vendor_data.get("email")) | (VendorAccount.phone_number == vendor_data.get("phone_number"))))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Vendor with given email or phone already exists")

    stmt = insert(VendorAccount).values(**vendor_data).returning(VendorAccount)
    result = await db.execute(stmt)
    await db.commit()
    created = result.fetchone()
    if created:
        # returning gives a Row; scalars() isn't available here — fetch first element
        return created[0]
    return None


async def get_vendors(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(sa_select(VendorAccount).offset(skip).limit(limit))
    return result.scalars().all()


async def update_vendor_account(db: AsyncSession, vendor_id: str, update_data: dict):
    # vendor_id expected to be UUID string
    vendor = await get_vendor_by_id(db, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    # Only update allowed attributes
    for k, v in update_data.items():
        if hasattr(vendor, k) and k != "password_hash":
            setattr(vendor, k, v)

    db.add(vendor)
    await db.commit()
    await db.refresh(vendor)
    return vendor


async def delete_vendor_account(db: AsyncSession, vendor_id: str):
    vendor = await get_vendor_by_id(db, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    await db.delete(vendor)
    await db.commit()
    return vendor


async def update_vendor_kyc(db: AsyncSession, vendor: VendorAccount, kyc_data: dict):
    # Prevent duplicate submission: if status already KYC_SUBMITTED or already verified
    try:
        from app.models.vendor_account import VendorStatus
    except Exception:
        VendorStatus = None

    if VendorStatus and getattr(vendor, "status", None) == VendorStatus.KYC_SUBMITTED:
        raise HTTPException(status_code=400, detail="KYC already submitted")
    if getattr(vendor, "is_kyc_verified", False):
        raise HTTPException(status_code=400, detail="KYC already verified")

    # Update fields
    for k, v in kyc_data.items():
        if hasattr(vendor, k):
            setattr(vendor, k, v)

    # mark as submitted
    if VendorStatus:
        vendor.status = VendorStatus.KYC_SUBMITTED
    vendor.is_kyc_verified = False

    db.add(vendor)
    await db.commit()
    await db.refresh(vendor)
    return vendor


async def get_vendor_by_id(db: AsyncSession, vendor_id: str):
    # vendor_id is expected to be UUID string
    try:
        vid = uuid.UUID(vendor_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid vendor_id")

    result = await db.execute(sa_select(VendorAccount).where(VendorAccount.id == vid))
    return result.scalars().first()


async def verify_vendor_kyc(db: AsyncSession, vendor_id: str, action: str, rejection_reason: str | None = None, admin_id: int | None = None):
    vendor = await get_vendor_by_id(db, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    from datetime import datetime
    from app.models.vendor_account import VendorStatus

    action = action.upper()
    if action == "APPROVE":
        vendor.is_kyc_verified = True
        vendor.status = VendorStatus.ACTIVE
        vendor.kyc_rejection_reason = None
        vendor.verification_timestamp = datetime.utcnow()
    elif action == "REJECT":
        vendor.is_kyc_verified = False
        vendor.status = VendorStatus.REJECTED
        vendor.kyc_rejection_reason = rejection_reason
        vendor.verification_timestamp = datetime.utcnow()
    else:
        raise HTTPException(status_code=400, detail="Invalid action; must be APPROVE or REJECT")

    db.add(vendor)
    await db.commit()
    await db.refresh(vendor)
    return vendor
