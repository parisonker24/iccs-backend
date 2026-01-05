from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from fastapi import HTTPException
from app.models.category import Category, CategoryStatus
from app.schemas.category import CategoryCreate, CategoryUpdate


async def create_category(db: AsyncSession, category_in: CategoryCreate):
    # Check for duplicate category_name
    existing = await db.execute(select(Category).where(Category.category_name == category_in.category_name))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Category with this name already exists")

    db_category = Category(**category_in.dict())
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category


async def get_category(db: AsyncSession, category_id: int):
    result = await db.execute(select(Category).where(Category.id == category_id))
    return result.scalars().first()


async def get_categories(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Category).offset(skip).limit(limit))
    return result.scalars().all()


async def update_category(db: AsyncSession, category_id: int, category_in: CategoryUpdate):
    # Check if category exists
    category = await get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Check for duplicate name if updating name
    if category_in.category_name and category_in.category_name != category.category_name:
        existing = await db.execute(select(Category).where(Category.category_name == category_in.category_name))
        if existing.scalars().first():
            raise HTTPException(status_code=400, detail="Category with this name already exists")

    update_data = category_in.dict(exclude_unset=True)
    await db.execute(update(Category).where(Category.id == category_id).values(**update_data))
    await db.commit()
    return await get_category(db, category_id)


async def delete_category(db: AsyncSession, category_id: int):
    # Soft delete by setting status to inactive
    category = await get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    await db.execute(update(Category).where(Category.id == category_id).values(status=CategoryStatus.inactive))
    await db.commit()
    return await get_category(db, category_id)
