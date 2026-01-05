from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from fastapi import HTTPException
from app.models.subcategory import Subcategory
from app.models.category import Category
from app.schemas.subcategory import SubcategoryCreate, SubcategoryUpdate


async def create_subcategory(db: AsyncSession, subcategory_in: SubcategoryCreate):
    # Check if category exists
    category = await db.execute(select(Category).where(Category.id == subcategory_in.category_id))
    if not category.scalars().first():
        raise HTTPException(status_code=400, detail="Category does not exist")

    db_subcategory = Subcategory(**subcategory_in.dict())
    db.add(db_subcategory)
    await db.commit()
    await db.refresh(db_subcategory)
    return db_subcategory


async def get_subcategory(db: AsyncSession, subcategory_id: int):
    result = await db.execute(select(Subcategory).where(Subcategory.id == subcategory_id))
    return result.scalars().first()


async def get_subcategories(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Subcategory).offset(skip).limit(limit))
    return result.scalars().all()


async def update_subcategory(db: AsyncSession, subcategory_id: int, subcategory_in: SubcategoryUpdate):
    # Check if subcategory exists
    subcategory = await get_subcategory(db, subcategory_id)
    if not subcategory:
        raise HTTPException(status_code=404, detail="Subcategory not found")

    # Check if category exists if updating category_id
    if subcategory_in.category_id:
        category = await db.execute(select(Category).where(Category.id == subcategory_in.category_id))
        if not category.scalars().first():
            raise HTTPException(status_code=400, detail="Category does not exist")

    update_data = subcategory_in.dict(exclude_unset=True)
    await db.execute(update(Subcategory).where(Subcategory.id == subcategory_id).values(**update_data))
    await db.commit()
    return await get_subcategory(db, subcategory_id)


async def delete_subcategory(db: AsyncSession, subcategory_id: int):
    subcategory = await get_subcategory(db, subcategory_id)
    if not subcategory:
        raise HTTPException(status_code=404, detail="Subcategory not found")

    await db.delete(subcategory)
    await db.commit()
    return subcategory
