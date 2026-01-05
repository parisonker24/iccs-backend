from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
from app.crud.crud_category import (
    create_category,
    get_category,
    get_categories,
    update_category,
    delete_category,
)
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryOut

router = APIRouter()


@router.post("/", response_model=CategoryOut)
async def create_category_endpoint(category_in: CategoryCreate, db: AsyncSession = Depends(get_db)):
    return await create_category(db, category_in)


@router.get("/{category_id}", response_model=CategoryOut)
async def read_category(category_id: int, db: AsyncSession = Depends(get_db)):
    category = await get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.get("/", response_model=List[CategoryOut])
async def read_categories(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await get_categories(db, skip=skip, limit=limit)


@router.put("/{category_id}", response_model=CategoryOut)
async def update_category_endpoint(category_id: int, category_in: CategoryUpdate, db: AsyncSession = Depends(get_db)):
    return await update_category(db, category_id, category_in)


@router.delete("/{category_id}", response_model=CategoryOut)
async def delete_category_endpoint(category_id: int, db: AsyncSession = Depends(get_db)):
    return await delete_category(db, category_id)
