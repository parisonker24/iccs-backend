import asyncio
from sqlalchemy import text
from app.db.session import engine


async def main():
    async with engine.begin() as conn:
        # Add `sku` column if missing and create a unique index for it.
        await conn.execute(
            text("ALTER TABLE products ADD COLUMN IF NOT EXISTS sku VARCHAR(100);")
        )
        await conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_products_sku ON products (sku);"
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
