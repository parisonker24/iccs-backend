from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.crud.crud_inventory import (
    get_inventory,
    get_inventory_by_product,
    create_inventory,
    update_inventory,
    delete_inventory,
    get_inventory_quantity_cached
)
from app.schemas.inventory import InventoryCreate, InventoryUpdate, Inventory
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)
from sqlalchemy.future import select
from app.models.product import Product

router = APIRouter()

@router.get("/{inventory_id}", response_model=Inventory)
async def read_inventory(inventory_id: int, db: AsyncSession = Depends(get_db)):
    db_inventory = await get_inventory(db, inventory_id)
    if db_inventory is None:
        raise HTTPException(status_code=404, detail="Inventory not found")
    return db_inventory

@router.get("/product/{product_id}", response_model=Inventory)
async def read_inventory_by_product(product_id: int, db: AsyncSession = Depends(get_db)):
    db_inventory = await get_inventory_by_product(db, product_id)
    if db_inventory is None:
        raise HTTPException(status_code=404, detail="Inventory not found")
    return db_inventory

@router.post("/", response_model=Inventory)
async def create_inventory_endpoint(inventory: InventoryCreate, db: AsyncSession = Depends(get_db)):
    # Verify product exists before attempting insert to return clearer error
    result = await db.execute(select(Product).where(Product.id == inventory.product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        return await create_inventory(db, inventory)
    except IntegrityError as e:
        # Likely a foreign-key constraint (e.g., product_id doesn't exist)
        logger.warning("IntegrityError creating inventory: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid product_id or integrity error")
    except Exception as e:
        logger.error("Error creating inventory: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.put("/{inventory_id}", response_model=Inventory)
async def update_inventory_endpoint(inventory_id: int, inventory_update: InventoryUpdate, db: AsyncSession = Depends(get_db)):
    db_inventory = await update_inventory(db, inventory_id, inventory_update)
    if db_inventory is None:
        raise HTTPException(status_code=404, detail="Inventory not found")
    return db_inventory

@router.delete("/{inventory_id}")
async def delete_inventory_endpoint(inventory_id: int, db: AsyncSession = Depends(get_db)):
    db_inventory = await delete_inventory(db, inventory_id)
    if db_inventory is None:
        raise HTTPException(status_code=404, detail="Inventory not found")
    return {"detail": "Inventory deleted"}

@router.get("/quantity/{product_id}")
async def get_quantity(product_id: int, db: AsyncSession = Depends(get_db)):
    quantity = await get_inventory_quantity_cached(db, product_id)
    if quantity is None:
        raise HTTPException(status_code=404, detail="Inventory not found")
    return {"quantity": quantity}
