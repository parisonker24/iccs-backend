import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.models import user, product, order, vendor, inventory  # import all models to register them with Base
from app.core.config import settings

async def create_tables():
    # Create async engine using your database URL from config
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        # Drop all tables (optional, only if you want clean slate)
        # await conn.run_sync(Base.metadata.drop_all)
        # Create all tables defined in Base's subclasses (models)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_tables())
