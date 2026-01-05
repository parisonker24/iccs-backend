import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db.session import async_session_maker
# Import all models so SQLAlchemy mapper registry is configured
import app.models.user
import app.models.vendor
import app.models.product
import app.models.inventory
import app.models.order
from app.models.product import Product
from sqlalchemy.future import select

async def main():
    async with async_session_maker() as session:
        result = await session.execute(select(Product))
        products = result.scalars().all()
        if not products:
            print('No products found')
            return
        for p in products:
            print(f'id={p.id}, name={p.name}, price={p.price}, vendor_id={p.vendor_id}')

if __name__ == '__main__':
    asyncio.run(main())
