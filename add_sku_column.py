import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def add_sku_column():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        # Add sku column to products table if it doesn't exist
        await conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS sku VARCHAR(100);"))
        # Add unique index on sku
        await conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_products_sku ON products (sku);"))
    await engine.dispose()
    print("SKU column added to products table.")

if __name__ == "__main__":
    asyncio.run(add_sku_column())
