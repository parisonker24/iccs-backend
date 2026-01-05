from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.inventory import Inventory
from app.schemas.inventory import InventoryCreate, InventoryUpdate
from app.core.redis import get_inventory_quantity, set_inventory_quantity, delete_inventory_quantity

async def get_inventory(db: AsyncSession, inventory_id: int):
    result = await db.execute(select(Inventory).where(Inventory.id == inventory_id))
    return result.scalars().first()

async def get_inventory_by_product(db: AsyncSession, product_id: int):
    result = await db.execute(select(Inventory).where(Inventory.product_id == product_id))
    return result.scalars().first()

async def create_inventory(db: AsyncSession, inventory: InventoryCreate):
    db_inventory = Inventory(**inventory.dict())
    db.add(db_inventory)
    await db.commit()
    await db.refresh(db_inventory)
    # Cache the quantity
    set_inventory_quantity(db_inventory.product_id, db_inventory.quantity)
    return db_inventory

async def update_inventory(db: AsyncSession, inventory_id: int, inventory_update: InventoryUpdate):
    result = await db.execute(select(Inventory).where(Inventory.id == inventory_id))
    db_inventory = result.scalars().first()
    if db_inventory:
        for key, value in inventory_update.dict(exclude_unset=True).items():
            setattr(db_inventory, key, value)
        await db.commit()
        await db.refresh(db_inventory)
        # Update cache
        set_inventory_quantity(db_inventory.product_id, db_inventory.quantity)
    return db_inventory

async def delete_inventory(db: AsyncSession, inventory_id: int):
    result = await db.execute(select(Inventory).where(Inventory.id == inventory_id))
    db_inventory = result.scalars().first()
    if db_inventory:
        await db.delete(db_inventory)
        await db.commit()
        # Remove from cache
        delete_inventory_quantity(db_inventory.product_id)
    return db_inventory

# Function to get quantity with cache
async def get_inventory_quantity_cached(db: AsyncSession, product_id: int):
    quantity = get_inventory_quantity(product_id)
    if quantity is not None:
        return quantity
    # If not in cache, get from DB and cache it
    inventory = await get_inventory_by_product(db, product_id)
    if inventory:
        set_inventory_quantity(product_id, inventory.quantity)
        return inventory.quantity
    return None
