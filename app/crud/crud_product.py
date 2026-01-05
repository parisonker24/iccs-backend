from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from typing import List, Optional
from app.models.product import Product
from app.models.subcategory import Subcategory
from app.models.user import UserRole
from app.services.embedding_service import cosine_similarity

async def create_product(db: AsyncSession, product_data: dict):
    # Validate subcategory exists
    if product_data.get("sub_category_id") is not None:
        result = await db.execute(
            select(Subcategory).where(Subcategory.id == product_data["sub_category_id"])
        )
        if not result.scalars().first():
            raise HTTPException(
                status_code=400,
                detail=f"Subcategory with id {product_data['sub_category_id']} does not exist"
            )

    new_product = Product(**product_data)

    # 🔍 Duplicate detection using cosine similarity
    if product_data.get("product_embedding") is not None:
        existing_products = await get_products(db)
        for product in existing_products:
            if product.product_embedding:
                try:
                    sim = cosine_similarity(
                        product_data["product_embedding"],
                        product.product_embedding
                    )
                    print(f"🔍 Similarity with {product.name}: {sim}")
                    if sim > 0.90:  # threshold
                        raise HTTPException(
                            status_code=400,
                            detail=f"Duplicate product detected → Similar to '{product.name}' ({sim:.2f})"
                        )
                except Exception as e:
                    print("❌ Similarity calc error:", e)
                    continue

    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product


async def get_product(db: AsyncSession, product_id: int):
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalars().first()


async def get_products(db: AsyncSession, skip: int = 0, limit: int = 1000):
    result = await db.execute(select(Product).offset(skip).limit(limit))
    return result.scalars().all()


async def get_public_products(db: AsyncSession, skip: int = 0, limit: int = 1000) -> List[Product]:
    """
    Fetch all publicly visible products.
    Optimized for storefront display; returns only is_public=True products.
    """
    query = (
        select(Product)
        .where(Product.is_public == True)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


async def get_vendor_private_products(
    db: AsyncSession,
    vendor_id: int,
    skip: int = 0,
    limit: int = 1000
) -> List[Product]:
    """
    Fetch all private (is_public=False) products for a specific vendor.
    Used for vendor dashboard to show products awaiting publication.
    """
    query = (
        select(Product)
        .where(
            (Product.vendor_id == vendor_id) &
            (Product.is_public == False)
        )
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


async def get_all_products_for_vendor(
    db: AsyncSession,
    vendor_id: int,
    skip: int = 0,
    limit: int = 1000
) -> List[Product]:
    """
    Fetch all products (public and private) belonging to a vendor.
    Used for vendor management portal; returns their complete inventory.
    """
    query = (
        select(Product)
        .where(Product.vendor_id == vendor_id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


async def get_all_products_for_admin(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 1000
) -> List[Product]:
    """
    Fetch all products in the system (public and private, all vendors).
    Used for admin moderation and reporting dashboards; no visibility filters.
    """
    query = select(Product).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


# ========== AUTHORIZATION & PERMISSION CHECKS ==========


async def can_user_access_product(
    product: Optional[Product],
    user_id: int,
    user_role: UserRole,
) -> bool:
    """
    Check if a user can access/view a product based on visibility and ownership.
    
    Rules:
    - Public products: anyone can access
    - Private products: only vendor owner or admin can access
    - Admin: always can access
    
    Args:
        product: The Product instance to check access for
        user_id: The user's ID
        user_role: The user's role (admin, vendor, customer, etc.)
    
    Returns:
        True if user can access, False otherwise
    """
    if product is None:
        return False
    
    # Admin bypasses all checks
    if user_role == UserRole.admin:
        return True
    
    # Public products are accessible to everyone
    if product.is_public:
        return True
    
    # Private products: only owner vendor can access
    if user_role == UserRole.vendor and product.vendor_id == user_id:
        return True
    
    return False


async def get_product_or_404(
    db: AsyncSession,
    product_id: int,
    user_id: int,
    user_role: UserRole,
) -> Product:
    """
    Fetch a product with access control. Raises 404 if not found or user lacks access.
    
    Args:
        db: Database session
        product_id: Product ID to fetch
        user_id: Current user's ID
        user_role: Current user's role
    
    Returns:
        Product instance if found and accessible
    
    Raises:
        HTTPException 404 if product not found or user cannot access it
    """
    product = await get_product(db, product_id)
    
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    has_access = await can_user_access_product(product, user_id, user_role)
    
    if not has_access:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    return product


async def get_product_for_update(
    db: AsyncSession,
    product_id: int,
    user_id: int,
    user_role: UserRole,
) -> Product:
    """
    Fetch a product for update/modification with strict authorization.
    
    Rules:
    - Vendor can only update their own products
    - Admin can update any product
    - Others cannot update
    
    Args:
        db: Database session
        product_id: Product ID to fetch
        user_id: Current user's ID
        user_role: Current user's role
    
    Returns:
        Product instance if user can update it
    
    Raises:
        HTTPException 404 if product not found
        HTTPException 403 if user cannot modify this product
    """
    product = await get_product(db, product_id)
    
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    # Admin can update any product
    if user_role == UserRole.admin:
        return product
    
    # Vendor can only update their own products
    if user_role == UserRole.vendor:
        if product.vendor_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify this product"
            )
        return product
    
    # Other roles cannot update products
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to modify products"
    )
