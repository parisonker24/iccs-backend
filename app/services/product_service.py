from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.models.product import Product
from app.models.user import User, UserRole
from app.schemas.product import ProductOut


async def get_products_for_user(db: AsyncSession, user_id: int) -> List[ProductOut]:
    """
    Get products visible to a specific user based on their role.
    - Admin: sees all products
    - Others: see only public products
    """
    # Get user role
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalars().first()

    if not user:
        # If user not found, return only public products (safe default)
        query = select(Product).where(Product.is_public == True)
    elif user.role == UserRole.admin:
        # Admin sees all products
        query = select(Product)
    else:
        # Non-admin users see only public products
        query = select(Product).where(Product.is_public == True)

    result = await db.execute(query)
    products = result.scalars().all()

    # Convert to Pydantic models
    return [ProductOut.model_validate(product) for product in products]


async def get_filtered_products_for_matching(db: AsyncSession, user_id: int) -> List[dict]:
    """
    Get products for matching/suggestions, filtered by user visibility.
    Used for find-matches endpoint to ensure private products don't appear in suggestions for non-admins.
    """
    # Get user role
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalars().first()

    if not user:
        # If user not found, return only public products
        query = select(Product).where(Product.is_public == True)
    elif user.role == UserRole.admin:
        # Admin sees all products
        query = select(Product)
    else:
        # Non-admin users see only public products
        query = select(Product).where(Product.is_public == True)

    result = await db.execute(query)
    products = result.scalars().all()

    # Return in format expected by matching functions
    return [
        {"id": p.id, "name": p.name, "description": p.description or ""}
        for p in products
    ]
