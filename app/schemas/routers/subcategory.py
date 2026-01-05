from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.crud.crud_subcategory import (
    create_subcategory,
    get_subcategory,
    get_subcategories,
    update_subcategory,
    delete_subcategory,
)
from app.schemas.subcategory import SubcategoryCreate, SubcategoryUpdate, Subcategory

router = APIRouter()


@router.post("/", response_model=Subcategory)
async def create_subcategory_endpoint(subcategory_in: SubcategoryCreate, db: AsyncSession = Depends(get_db)):
    return await create_subcategory(db, subcategory_in)


@router.get("/{subcategory_id}", response_model=Subcategory)
async def read_subcategory(subcategory_id: int, db: AsyncSession = Depends(get_db)):
    subcategory = await get_subcategory(db, subcategory_id)
    if not subcategory:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    return subcategory


@router.get("/", response_model=List[Subcategory])
async def read_subcategories(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await get_subcategories(db, skip=skip, limit=limit)


@router.put("/{subcategory_id}", response_model=Subcategory)
async def update_subcategory_endpoint(subcategory_id: int, subcategory_in: SubcategoryUpdate, db: AsyncSession = Depends(get_db)):
    return await update_subcategory(db, subcategory_id, subcategory_in)


@router.delete("/{subcategory_id}", response_model=Subcategory)
async def delete_subcategory_endpoint(subcategory_id: int, db: AsyncSession = Depends(get_db)):
    return await delete_subcategory(db, subcategory_id)
