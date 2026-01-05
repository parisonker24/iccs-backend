import asyncio
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.crud.crud_product import create_product
from app.schemas.product import ProductCreate
from app.db.session import get_db
from app.core.config import settings

async def _test_duplicate_detection():
    # Create a test product
    product_data = ProductCreate(
        name="Test Product",
        description="This is a test product for duplicate detection",
        sku="TEST001",
        price=100.0,
        category_id=1,  # Assuming category exists
        vendor_id=1     # Assuming vendor exists
    )

    # Get database session
    from app.db.session import async_session_maker

    async with async_session_maker() as db:
        try:
            # Create first product
            print("Creating first product...")
            product1 = await create_product(db, product_data)
            print(f"First product created: {product1.name} (ID: {product1.id})")

            # Try to create duplicate
            print("Attempting to create duplicate...")
            try:
                product2 = await create_product(db, product_data)
                print("ERROR: Duplicate was allowed!")
            except Exception as e:
                print(f"Duplicate correctly blocked: {e}")

        except Exception as e:
            print(f"Error during test: {e}")


def test_duplicate_detection():
    asyncio.run(_test_duplicate_detection())


if __name__ == "__main__":
    asyncio.run(_test_duplicate_detection())
