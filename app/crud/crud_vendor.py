from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from fastapi import HTTPException
from app.models.vendor import Vendor
from app.schemas.vendor import VendorCreate, VendorUpdate


async def create_vendor(db: AsyncSession, vendor_in: VendorCreate):
    # Check for duplicate name
    existing = await db.execute(select(Vendor).where(Vendor.name == vendor_in.name))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Vendor with this name already exists")

    db_vendor = Vendor(**vendor_in.dict())
    db.add(db_vendor)
    await db.commit()
    await db.refresh(db_vendor)
    return db_vendor


async def get_vendor(db: AsyncSession, vendor_id: int):
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    return result.scalars().first()


async def get_vendors(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Vendor).offset(skip).limit(limit))
    return result.scalars().all()


async def update_vendor(db: AsyncSession, vendor_id: int, vendor_in: VendorUpdate):
    # Check if vendor exists
    vendor = await get_vendor(db, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    # Check for duplicate name if updating name
    if vendor_in.name and vendor_in.name != vendor.name:
        existing = await db.execute(select(Vendor).where(Vendor.name == vendor_in.name))
        if existing.scalars().first():
            raise HTTPException(status_code=400, detail="Vendor with this name already exists")

    update_data = vendor_in.dict(exclude_unset=True)
    await db.execute(update(Vendor).where(Vendor.id == vendor_id).values(**update_data))
    await db.commit()
    return await get_vendor(db, vendor_id)


async def delete_vendor(db: AsyncSession, vendor_id: int):
    vendor = await get_vendor(db, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    await db.delete(vendor)
    await db.commit()
    return vendor
