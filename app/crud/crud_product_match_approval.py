from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from typing import List, Optional
from app.models.product_match_approval import ProductMatchApproval
from app.schemas.product_match_approval import ProductMatchApprovalCreate, ProductMatchApprovalUpdate


async def create_match_approval(
    db: AsyncSession,
    approval_in: ProductMatchApprovalCreate
) -> ProductMatchApproval:
    """Create a new product match approval record."""
    approval_data = approval_in.dict()
    approval = ProductMatchApproval(**approval_data)
    db.add(approval)
    await db.commit()
    await db.refresh(approval)
    return approval


async def get_match_approvals(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None
) -> List[ProductMatchApproval]:
    """Get all match approvals with optional status filter."""
    query = select(ProductMatchApproval).offset(skip).limit(limit)

    if status:
        query = query.where(ProductMatchApproval.admin_decision == status)

    result = await db.execute(query)
    return result.scalars().all()


async def get_match_approval_by_id(
    db: AsyncSession,
    approval_id: int
) -> Optional[ProductMatchApproval]:
    """Get a specific match approval by ID."""
    query = select(ProductMatchApproval).where(ProductMatchApproval.id == approval_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def update_match_approval(
    db: AsyncSession,
    approval_id: int,
    approval_update: ProductMatchApprovalUpdate,
    admin_id: int
) -> Optional[ProductMatchApproval]:
    """Update a match approval with admin decision."""
    update_data = approval_update.dict()
    update_data['admin_id'] = admin_id
    update_data['updated_at'] = None  # Will be set by database

    query = (
        update(ProductMatchApproval)
        .where(ProductMatchApproval.id == approval_id)
        .values(**update_data)
        .returning(ProductMatchApproval)
    )

    result = await db.execute(query)
    await db.commit()

    updated_approval = result.scalar_one_or_none()
    if updated_approval:
        await db.refresh(updated_approval)
    return updated_approval


async def get_pending_approvals_for_product(
    db: AsyncSession,
    product_id: int
) -> List[ProductMatchApproval]:
    """Get all pending approvals for a specific product."""
    query = select(ProductMatchApproval).where(
        and_(
            ProductMatchApproval.source_product_id == product_id,
            ProductMatchApproval.admin_decision == "pending"
        )
    )
    result = await db.execute(query)
    return result.scalars().all()


async def get_approvals_by_admin(
    db: AsyncSession,
    admin_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[ProductMatchApproval]:
    """Get all approvals handled by a specific admin."""
    query = (
        select(ProductMatchApproval)
        .where(ProductMatchApproval.admin_id == admin_id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()
