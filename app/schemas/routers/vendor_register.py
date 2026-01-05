from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from app.db.session import get_db
from app.schemas.vendor_account import VendorCreate, VendorResponse
from app.crud.crud_vendor_account import (
    get_vendor_by_email,
    get_vendor_by_phone,
    create_vendor_account,
)
from datetime import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()


@router.post("/register", response_model=VendorResponse)
async def register_vendor(vendor_in: VendorCreate, db: AsyncSession = Depends(get_db)):
    # Check uniqueness
    if await get_vendor_by_email(db, vendor_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if await get_vendor_by_phone(db, vendor_in.phone_number):
        raise HTTPException(status_code=400, detail="Phone number already registered")

    # Hash password
    hashed = pwd_context.hash(vendor_in.password)

    vendor_data = {
        "business_name": vendor_in.business_name,
        "owner_name": vendor_in.owner_name,
        "email": vendor_in.email,
        "phone_number": vendor_in.phone_number,
        "password_hash": hashed,
        "business_address": vendor_in.business_address,
        "gst_number": vendor_in.gst_number,
        "pan_number": vendor_in.pan_number,
    }

    created = await create_vendor_account(db, vendor_data=vendor_data)
    if not created:
        raise HTTPException(status_code=500, detail="Failed to create vendor")

    # Ensure ORM object fields for response (created may be ORM instance)
    # Return created vendor without password
    return created
