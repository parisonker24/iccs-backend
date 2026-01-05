import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from app.db.base import Base
from app.models.category import Category
from app.models.subcategory import Subcategory
from app.core.config import settings

async def check_subcategories():
    # Create async engine using your database URL from config
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Query all subcategories
        result = await session.execute(select(Subcategory))
        subcategories = result.scalars().all()

        if subcategories:
            print("Existing subcategories:")
            for sub in subcategories:
                print(f"ID: {sub.id}, Name: {sub.name}, Category ID: {sub.category_id}")
        else:
            print("No subcategories found.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_subcategories())
