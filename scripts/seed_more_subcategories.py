import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from app.db.base import Base
from app.models.category import Category
from app.models.subcategory import Subcategory
from app.core.config import settings

async def seed_more_subcategories():
    # Create async engine using your database URL from config
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Get the existing Electronics category
        result = await session.execute(select(Category).where(Category.category_name == "Electronics"))
        category = result.scalars().first()
        if not category:
            print("Electronics category not found. Please seed categories first.")
            return

        # List of subcategories to add
        subcategories_to_add = [
            {"name": "Laptops", "description": "Portable computers"},
            {"name": "Headphones", "description": "Audio devices"},
            {"name": "Tablets", "description": "Portable tablets"},
            {"name": "Smartwatches", "description": "Wearable devices"},
            {"name": "Cameras", "description": "Digital cameras"}
        ]

        for sub_data in subcategories_to_add:
            # Check if subcategory already exists
            existing = await session.execute(select(Subcategory).where(Subcategory.name == sub_data["name"]))
            if existing.scalars().first():
                print(f"Subcategory '{sub_data['name']}' already exists.")
                continue

            subcategory = Subcategory(name=sub_data["name"], description=sub_data["description"], category_id=category.id)
            session.add(subcategory)
            await session.commit()
            await session.refresh(subcategory)
            print(f"Created subcategory: {subcategory.name} (id: {subcategory.id})")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_more_subcategories())
