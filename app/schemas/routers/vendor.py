from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from passlib.context import CryptContext
from app.db.session import get_db
from app.crud.crud_vendor_account import (
    create_vendor_account,
    get_vendor_by_id,
    get_vendors,
    update_vendor_account,
    delete_vendor_account,
)
from app.schemas.vendor_account import VendorCreate, VendorResponse

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()


@router.post("/", response_model=VendorResponse)
async def create_vendor_endpoint(vendor_in: VendorCreate, db: AsyncSession = Depends(get_db)):
    # Hash password before creating account
    hashed = pwd_context.hash(vendor_in.password)
    vendor_data = vendor_in.model_dump()
    vendor_data["password_hash"] = hashed
    # remove plain password
    vendor_data.pop("password", None)

    created = await create_vendor_account(db, vendor_data=vendor_data)
    if not created:
        raise HTTPException(status_code=500, detail="Failed to create vendor")
    return created


@router.get("/{vendor_id}", response_model=VendorResponse)
async def read_vendor(vendor_id: str, db: AsyncSession = Depends(get_db)):
    vendor = await get_vendor_by_id(db, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


@router.get("/", response_model=List[VendorResponse])
async def read_vendors(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await get_vendors(db, skip=skip, limit=limit)


@router.put("/{vendor_id}", response_model=VendorResponse)
async def update_vendor_endpoint(vendor_id: str, update_data: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    # Prevent updating password_hash directly via this endpoint
    if "password" in update_data:
        # If password provided, hash and set password_hash
        hashed = pwd_context.hash(update_data.pop("password"))
        update_data["password_hash"] = hashed

    updated = await update_vendor_account(db, vendor_id, update_data)
    return updated


@router.delete("/{vendor_id}", response_model=VendorResponse)
async def delete_vendor_endpoint(vendor_id: str, db: AsyncSession = Depends(get_db)):
    deleted = await delete_vendor_account(db, vendor_id)
    return deleted
