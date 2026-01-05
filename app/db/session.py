from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings

"""Database async engine and session factory using settings.DATABASE_URL."""

# Use configured DATABASE_URL from settings (ensure .env / env var is correct)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
)

# single async session factory (SQLAlchemy 1.4+ / 2.x compatible)
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Dependency for FastAPI (or any async DB access)
async def get_db():
    async with async_session_maker() as session:
        yield session

# Explicit exports for consumers of this module
__all__ = ["engine", "async_session_maker", "get_db"]

# No changes required — file already exports engine, async_session_maker and get_db

