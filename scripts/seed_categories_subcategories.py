import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.models.category import Category
from app.models.subcategory import Subcategory
from app.core.config import settings

async def seed_data():
    # Create async engine using your database URL from config
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Create a sample category
        category = Category(category_name="Electronics", status="active")
        session.add(category)
        await session.commit()
        await session.refresh(category)

        # Create a sample subcategory
        subcategory = Subcategory(name="Smartphones", description="Mobile phones", category_id=category.id)
        session.add(subcategory)
        await session.commit()

        print(f"Created category: {category.category_name} (id: {category.id})")
        print(f"Created subcategory: {subcategory.name} (id: {subcategory.id})")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_data())
