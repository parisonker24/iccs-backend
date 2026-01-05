import asyncio
import sys
from pathlib import Path

# Ensure project root is on sys.path so `import app` works when running this script
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db.session import async_session_maker
import app.models.user
import app.models.vendor
import app.models.product
import app.models.inventory
import app.models.order
from app.schemas.product import ProductCreate
from app.schemas.inventory import InventoryCreate
from app.crud.crud_product import create_product
from app.crud.crud_inventory import create_inventory

async def main():
    async with async_session_maker() as db:
        prod_in = ProductCreate(name="Auto product", description="Created directly", price=4.5, vendor_id=None)
        prod = await create_product(db, prod_in)
        print('Created product:', prod.id, prod.name)

        inv_in = InventoryCreate(product_id=prod.id, quantity=10, location="Warehouse A")
        inv = await create_inventory(db, inv_in)
        print('Created inventory:', inv.id, inv.product_id, inv.quantity)

if __name__ == '__main__':
    asyncio.run(main())
