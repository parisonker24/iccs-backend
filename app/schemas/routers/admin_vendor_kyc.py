from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_user, get_current_admin
from app.db.session import get_db
from app.crud import crud_user
from app.crud.crud_vendor_account import verify_vendor_kyc
from app.schemas.vendor_admin_kyc import VendorAdminKYCRequest
from app.schemas.vendor_account import VendorKYCStatus
from app.schemas.vendor_admin_list import VendorAdminListResponse
from app.models.user import UserRole
from app.models.vendor_account import VendorAccount, VendorStatus
from app.models.vendor_kyc_document import VendorKYCDocument, DocumentType
from app.models.vendor_alert import VendorAlert
from app.models.vendor import Vendor
from app.models.product import Product
from app.models.product_review import ProductReview
from app.models.order import Order, OrderItem
from app.models.category import Category
from app.models.inventory import Inventory
from sqlalchemy.future import select
from sqlalchemy import func, or_, and_, case
from datetime import datetime, timedelta
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from uuid import UUID

router = APIRouter()


@router.post("/kyc/verify", response_model=VendorKYCStatus)
async def admin_verify_vendor_kyc(
    payload: VendorAdminKYCRequest,
    current_user = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        user_id = int(current_user.id)
    except Exception:
        user_id = current_user.id

    db_user = await crud_user.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unable to resolve user")

    if db_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins may verify KYC")

    # Map incoming status to internal action
    action = "APPROVE" if payload.status == "APPROVED" else "REJECT"

    try:
        updated = await verify_vendor_kyc(db, payload.vendor_id, action, payload.rejection_reason, admin_id=db_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify KYC: {str(e)}")

    # Return an object consistent with VendorKYCStatus schema
    return {
        "vendor_id": updated.id,
        "business_name": updated.business_name,
        "is_kyc_verified": updated.is_kyc_verified,
        "status": updated.status.value if hasattr(updated.status, 'value') else str(updated.status),
        "rejection_reason": updated.kyc_rejection_reason,
        "updated_at": updated.updated_at,
    }


@router.get("/", response_model=VendorAdminListResponse)
async def admin_list_vendors(
    search: Optional[str] = None,
    status: Optional[str] = None,
    verification: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    # only admins
    try:
        user_id = int(current_user.id)
    except Exception:
        user_id = current_user.id

    db_user = await __import__("app.crud.crud_user", fromlist=["get_user"]).get_user(db, user_id)
    if not db_user or db_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only admins may list vendors")

    # Base query for vendors
    q = select(VendorAccount)

    # Apply filters
    if search:
        like = f"%{search}%"
        q = q.where(or_(VendorAccount.business_name.ilike(like), VendorAccount.email.ilike(like), VendorAccount.phone_number.ilike(like)))

    if status:
        if status.lower() == "active":
            q = q.where(VendorAccount.status == VendorStatus.ACTIVE)
        elif status.lower() == "inactive":
            q = q.where(VendorAccount.status == VendorStatus.REJECTED)
        elif status.lower() == "suspended":
            # Assuming suspended maps to PENDING or another status; adjust as needed
            q = q.where(VendorAccount.status == VendorStatus.PENDING)

    if verification:
        if verification.lower() == "verified":
            q = q.where(VendorAccount.is_kyc_verified == True)
        elif verification.lower() == "pending":
            q = q.where(and_(VendorAccount.status == VendorStatus.PENDING, VendorAccount.is_kyc_verified == False))
        elif verification.lower() == "rejected":
            q = q.where(and_(VendorAccount.status == VendorStatus.REJECTED, VendorAccount.is_kyc_verified == False))

    # Get total count before pagination
    count_q = select(func.count()).select_from(q.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar()

    # Apply pagination
    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    vendors = result.scalars().all()

    out = []
    for v in vendors:
        # Calculate aggregates
        # Note: Assuming VendorAccount links to Vendor via email for products/orders
        # This is a simplification; adjust if there's a direct relationship
        vendor_legacy = await db.execute(select(Vendor).where(Vendor.contact_email == v.email))
        vendor_legacy = vendor_legacy.scalars().first()

        total_products = 0
        total_orders = 0
        total_revenue = 0.0

        if vendor_legacy:
            # Total products
            prod_q = select(func.count(Product.id)).where(Product.vendor_id == vendor_legacy.id)
            prod_result = await db.execute(prod_q)
            total_products = prod_result.scalar() or 0

            # Total orders and revenue (sum of order totals for products by this vendor)
            order_q = select(
                func.count(Order.id).label("order_count"),
                func.sum(Order.total_amount).label("revenue")
            ).select_from(Order).join(OrderItem, Order.id == OrderItem.order_id).join(Product, OrderItem.product_id == Product.id).where(Product.vendor_id == vendor_legacy.id)
            order_result = await db.execute(order_q)
            order_data = order_result.first()
            total_orders = order_data.order_count or 0
            total_revenue = order_data.revenue or 0.0

        # Map verification status
        verification_status = "verified" if v.is_kyc_verified else ("pending" if v.status == VendorStatus.PENDING else "rejected")

        out.append({
            "vendor_id": str(v.id),
            "business_name": v.business_name,
            "business_type": getattr(v, "business_type", None),
            "status": v.status.value if hasattr(v.status, 'value') else str(v.status),
            "verification": verification_status,
            "rating": 0.0,  # Placeholder; calculate from reviews if available
            "contact_person": v.owner_name,
            "phone": v.phone_number,
            "email": v.email,
            "joined_date": v.created_at,
            "total_products": total_products,
            "total_orders": total_orders,
            "total_revenue": total_revenue,
        })

    return {"total": total, "vendors": out}


@router.get("/stats")
async def admin_vendor_stats(current_user = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    """Return aggregated vendor statistics optimized with a single DB query."""
    try:
        user_id = int(current_user.id)
    except Exception:
        user_id = current_user.id

    db_user = await __import__("app.crud.crud_user", fromlist=["get_user"]).get_user(db, user_id)
    if not db_user or db_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only admins may view vendor stats")

    # Use SQL aggregates and conditional sums to compute all counts in one query
    stats_q = select(
        func.count().label("total_vendors"),
        func.sum(case((VendorAccount.status == VendorStatus.ACTIVE, 1), else_=0)).label("active_vendors"),
        func.sum(case((and_(VendorAccount.status == VendorStatus.PENDING, VendorAccount.is_kyc_verified == False), 1), else_=0)).label("pending_verification"),
        func.sum(case((VendorAccount.status == VendorStatus.REJECTED, 1), else_=0)).label("suspended_vendors"),
    ).select_from(VendorAccount)

    res = await db.execute(stats_q)
    row = res.first()
    if not row:
        return {
            "total_vendors": 0,
            "active_vendors": 0,
            "pending_verification": 0,
            "suspended_vendors": 0,
        }

    return {
        "total_vendors": int(row.total_vendors or 0),
        "active_vendors": int(row.active_vendors or 0),
        "pending_verification": int(row.pending_verification or 0),
        "suspended_vendors": int(row.suspended_vendors or 0),
    }


@router.get("/review/{vendor_id}")
async def admin_get_vendor_review(vendor_id: UUID, current_user = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    try:
        user_id = int(current_user.id)
    except Exception:
        user_id = current_user.id

    db_user = await __import__("app.crud.crud_user", fromlist=["get_user"]).get_user(db, user_id)
    if not db_user or db_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only admins may view vendor review")

    vendor = await db.execute(select(VendorAccount).where(VendorAccount.id == vendor_id))
    vendor = vendor.scalars().first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    # fetch uploaded documents
    docs_q = await db.execute(select(VendorKYCDocument).where(VendorKYCDocument.vendor_id == vendor.id))
    docs = docs_q.scalars().all()
    doc_list = []
    for d in docs:
        doc_list.append({
            "document_type": d.document_type.name if hasattr(d.document_type, 'name') else str(d.document_type),
            "document_url": d.document_url,
            "uploaded_at": d.uploaded_at if hasattr(d, 'uploaded_at') else None,
        })

    return {
        "vendor_id": str(vendor.id),
        "business_name": vendor.business_name,
        "business_type": vendor.business_type,
        "contact_person": vendor.owner_name,
        "phone": vendor.phone_number,
        "email": vendor.email,
        "business_address": vendor.business_address,
        "gst_number": vendor.gst_number,
        "pan_number": vendor.pan_number,
        "business_registration": vendor.business_license_number,
        "bank_name": vendor.bank_name,
        "account_number": vendor.bank_account_number,
        "ifsc_code": vendor.ifsc_code,
        "status": vendor.status.value if hasattr(vendor.status, 'value') else str(vendor.status),
        "is_kyc_verified": vendor.is_kyc_verified,
        "kyc_documents": doc_list,
    }


@router.post("/id/{vendor_id}/approve")
async def admin_approve_vendor(vendor_id: UUID, current_user = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    """Approve a vendor: mark KYC verified, set status active and save verification timestamp.

    Uses existing `verify_vendor_kyc` CRUD helper to keep behavior consistent.
    """
    try:
        user_id = int(current_user.id)
    except Exception:
        user_id = current_user.id

    db_user = await __import__("app.crud.crud_user", fromlist=["get_user"]).get_user(db, user_id)
    if not db_user or db_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only admins may approve vendors")

    try:
        updated = await verify_vendor_kyc(db, vendor_id, "APPROVE", None, admin_id=db_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve vendor: {str(e)}")

    return {
        "success": True,
        "vendor_id": str(updated.id),
        "status": updated.status.value if hasattr(updated.status, 'value') else str(updated.status),
        "is_kyc_verified": updated.is_kyc_verified,
        "approved_at": updated.verification_timestamp,
    }


class VendorRejectRequest(BaseModel):
    reason: str


@router.post("/id/{vendor_id}/reject")
async def admin_reject_vendor(vendor_id: UUID, payload: VendorRejectRequest, current_user = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    """Reject a vendor: mark KYC rejected and save rejection reason."""
    try:
        user_id = int(current_user.id)
    except Exception:
        user_id = current_user.id

    db_user = await __import__("app.crud.crud_user", fromlist=["get_user"]).get_user(db, user_id)
    if not db_user or db_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only admins may reject vendors")

    try:
        updated = await verify_vendor_kyc(db, vendor_id, "REJECT", payload.reason, admin_id=db_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reject vendor: {str(e)}")

    return {
        "success": True,
        "vendor_id": str(updated.id),
        "status": updated.status.value if hasattr(updated.status, 'value') else str(updated.status),
        "is_kyc_verified": updated.is_kyc_verified,
        "rejection_reason": updated.kyc_rejection_reason,
        "rejected_at": updated.verification_timestamp,
    }


@router.get("/id/{vendor_id}/documents")
async def admin_get_vendor_documents(vendor_id: UUID, current_user = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    """Return uploaded KYC documents for a vendor.

    Response items contain: document_type, file_url, uploaded_at
    """
    try:
        user_id = int(current_user.id)
    except Exception:
        user_id = current_user.id

    db_user = await __import__("app.crud.crud_user", fromlist=["get_user"]).get_user(db, user_id)
    if not db_user or db_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only admins may view vendor documents")

    vendor_q = await db.execute(select(VendorAccount).where(VendorAccount.id == vendor_id))
    vendor = vendor_q.scalars().first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    docs_q = await db.execute(
        select(VendorKYCDocument).where(VendorKYCDocument.vendor_id == vendor.id).order_by(VendorKYCDocument.uploaded_at.desc())
    )
    docs = docs_q.scalars().all()

    out = []
    for d in docs:
        out.append({
            "document_type": d.document_type.name if hasattr(d.document_type, 'name') else str(d.document_type),
            "file_url": d.document_url,
            "uploaded_at": d.uploaded_at if hasattr(d, 'uploaded_at') else None,
        })

    return out


@router.get("/id/{vendor_id}/reviews")
async def admin_get_vendor_reviews(vendor_id: UUID, current_user = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    """Return customer reviews for a vendor.

    Each item contains: customer_name, product_name, rating, sentiment, comment, date
    """
    try:
        user_id = int(current_user.id)
    except Exception:
        user_id = current_user.id

    db_user = await __import__("app.crud.crud_user", fromlist=["get_user"]).get_user(db, user_id)
    if not db_user or db_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only admins may view vendor reviews")

    # Resolve vendor account and legacy vendor mapping
    vendor_account_q = await db.execute(select(VendorAccount).where(VendorAccount.id == vendor_id))
    vendor_account = vendor_account_q.scalars().first()
    if not vendor_account:
        raise HTTPException(status_code=404, detail="Vendor account not found")

    vendor_legacy_q = await db.execute(select(Vendor).where(Vendor.contact_email == vendor_account.email))
    vendor_legacy = vendor_legacy_q.scalars().first()
    if not vendor_legacy:
        # No legacy vendor mapping; return empty list
        return []

    # Query reviews joined with product name
    q = select(ProductReview, Product.name).select_from(ProductReview).join(Product, Product.id == ProductReview.product_id)
    q = q.where(Product.vendor_id == vendor_legacy.id)
    q = q.order_by(ProductReview.created_at.desc())

    res = await db.execute(q)
    rows = res.all()

    out = []
    for r in rows:
        # r is a Row with (ProductReview, product_name)
        review = r[0]
        product_name = r[1]
        out.append({
            "customer_name": review.customer_name,
            "product_name": product_name,
            "rating": int(review.rating) if review.rating is not None else None,
            "sentiment": review.sentiment,
            "comment": review.comment,
            "date": review.created_at,
        })

    return out


@router.get("/id/{vendor_id}/performance/summary")
async def admin_vendor_performance_summary(vendor_id: UUID, current_user = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    """Return a performance summary for a vendor (last 30 days).

    Fields returned:
    - orders_fulfilled (last 30 days)
    - on_time_delivery_percentage (None if not computable)
    - avg_handling_time (None if not computable)
    - order_acceptance_rate
    - return_rate
    - cancellation_rate
    - customer_rating (None if not available)
    - inventory_accuracy (None if not available)

    Notes: Several metrics require additional timestamps or review data which
    are not present in the current schema; those fields return `None`.
    """
    try:
        user_id = int(current_user.id)
    except Exception:
        user_id = current_user.id

    db_user = await __import__("app.crud.crud_user", fromlist=["get_user"]).get_user(db, user_id)
    if not db_user or db_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only admins may view vendor performance summary")

    # verify vendor exists (new vendor account)
    vendor_obj = await db.execute(select(VendorAccount).where(VendorAccount.id == vendor_id))
    vendor_obj = vendor_obj.scalars().first()
    if not vendor_obj:
        raise HTTPException(status_code=404, detail="Vendor not found")

    # Map to legacy Vendor (some tables use legacy integer vendor ids)
    vendor_legacy_q = await db.execute(select(Vendor).where(Vendor.contact_email == vendor_obj.email))
    vendor_legacy = vendor_legacy_q.scalars().first()
    if vendor_legacy:
        vendor_match_id = vendor_legacy.id
    else:
        # No legacy vendor mapping; return zeros/empty metrics
        return {
            "vendor_id": str(vendor_obj.id),
            "orders_fulfilled": 0,
            "on_time_delivery_percentage": None,
            "avg_handling_time": None,
            "order_acceptance_rate": 0.0,
            "return_rate": 0.0,
            "cancellation_rate": 0.0,
            "customer_rating": None,
            "inventory_accuracy": None,
        }

    try:
        since = datetime.utcnow() - timedelta(days=30)

        # Define statuses considered not accepted
        excluded = ["cancelled", "pending", "returned", "failed"]

        q = select(
            func.count(func.distinct(Order.id)).label("total_orders"),
            func.sum(case((Order.status.in_(excluded), 0), else_=1)).label("accepted_orders"),
            func.sum(case((Order.status == 'returned', 1), else_=0)).label("returned_orders"),
            func.sum(case((Order.status == 'cancelled', 1), else_=0)).label("cancelled_orders"),
        ).select_from(Order).join(OrderItem, Order.id == OrderItem.order_id).join(Product, OrderItem.product_id == Product.id)
        # Use legacy vendor id (integer) for product/vendor joins
        q = q.where(and_(Product.vendor_id == vendor_match_id, Order.created_at >= since))

        res = await db.execute(q)
        row = res.first()
        total_orders = int(row.total_orders or 0)
        accepted_orders = int(row.accepted_orders or 0)
        returned_orders = int(row.returned_orders or 0)
        cancelled_orders = int(row.cancelled_orders or 0)

        # orders_fulfilled: treat accepted orders (not in excluded) as fulfilled
        orders_fulfilled = accepted_orders

        if total_orders > 0:
            order_acceptance_rate = round((accepted_orders / total_orders) * 100, 2)
            return_rate = round((returned_orders / total_orders) * 100, 2)
            cancellation_rate = round((cancelled_orders / total_orders) * 100, 2)
        else:
            order_acceptance_rate = 0.0
            return_rate = 0.0
            cancellation_rate = 0.0

        # The following metrics are not computable from current models
        on_time_delivery_percentage = None
        avg_handling_time = None
        customer_rating = None
        inventory_accuracy = None

        return {
            "vendor_id": str(vendor_obj.id),
            "orders_fulfilled": orders_fulfilled,
            "on_time_delivery_percentage": on_time_delivery_percentage,
            "avg_handling_time": avg_handling_time,
            "order_acceptance_rate": order_acceptance_rate,
            "return_rate": return_rate,
            "cancellation_rate": cancellation_rate,
            "customer_rating": customer_rating,
            "inventory_accuracy": inventory_accuracy,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Raise a more informative HTTPException so the client sees the error during debugging.
        raise HTTPException(status_code=500, detail=f"Performance summary error: {e}")


@router.get("/id/{vendor_id}/performance/charts")
async def admin_vendor_performance_charts(vendor_id: UUID, current_user = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    """Return structured chart data for vendor performance.

    - Order trends (last 30 days)
    - Cancellation breakdown (vendor/system/customer) — returns unknown bucket if source not available
    - Handling time distribution (not computable without timestamps)
    """
    try:
        user_id = int(current_user.id)
    except Exception:
        user_id = current_user.id

    db_user = await __import__("app.crud.crud_user", fromlist=["get_user"]).get_user(db, user_id)
    if not db_user or db_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only admins may view vendor performance charts")

    # Find vendor account and legacy vendor (by contact email)
    vendor_account_q = await db.execute(select(VendorAccount).where(VendorAccount.id == vendor_id))
    vendor_account = vendor_account_q.scalars().first()
    if not vendor_account:
        raise HTTPException(status_code=404, detail="Vendor account not found")

    vendor_legacy_q = await db.execute(select(Vendor).where(Vendor.contact_email == vendor_account.email))
    vendor_legacy = vendor_legacy_q.scalars().first()
    if not vendor_legacy:
        # No legacy vendor mapping; return empty datasets
        return {
            "order_trends": [],
            "cancellation_breakdown": {"vendor": 0, "system": 0, "customer": 0, "unknown": 0},
            "handling_time_distribution": None,
        }

    since = datetime.utcnow() - timedelta(days=30)

    # Order trends: count distinct orders per day
    day_q = select(
        func.date(Order.created_at).label("day"),
        func.count(func.distinct(Order.id)).label("count")
    ).select_from(Order).join(OrderItem, Order.id == OrderItem.order_id).join(Product, OrderItem.product_id == Product.id)
    day_q = day_q.where(and_(Product.vendor_id == vendor_legacy.id, Order.created_at >= since))
    day_q = day_q.group_by(func.date(Order.created_at)).order_by(func.date(Order.created_at))

    day_res = await db.execute(day_q)
    day_rows = day_res.all()
    # Build map for last 30 days (fill zeros)
    trends_map = { (since + timedelta(days=i)).date(): 0 for i in range(0, 31) }
    for r in day_rows:
        # r.day may be date object
        trends_map[r.day] = int(r.count or 0)

    order_trends = [{"date": d.isoformat(), "count": trends_map[d]} for d in sorted(trends_map.keys())]

    # Cancellation breakdown — we don't have cancel origin, so put all cancelled into unknown
    cancel_q = select(func.count(func.distinct(Order.id)).label("cancelled_count")).select_from(Order).join(OrderItem, Order.id == OrderItem.order_id).join(Product, OrderItem.product_id == Product.id)
    cancel_q = cancel_q.where(and_(Product.vendor_id == vendor_legacy.id, Order.created_at >= since, Order.status == 'cancelled'))
    cancel_res = await db.execute(cancel_q)
    cancelled_count = int((cancel_res.first().cancelled_count) or 0)

    cancellation_breakdown = {
        "vendor": 0,
        "system": 0,
        "customer": 0,
        "unknown": cancelled_count,
    }

    # Handling time distribution unavailable without timestamps
    handling_time_distribution = None

    return {
        "order_trends": order_trends,
        "cancellation_breakdown": cancellation_breakdown,
        "handling_time_distribution": handling_time_distribution,
    }


@router.get("/id/{vendor_id}/products/performance")
async def admin_vendor_products_performance(vendor_id: UUID, current_user = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    """Return per-product performance for a vendor.

    Fields per product:
    - product_name
    - category
    - sales (units sold)
    - fulfillment_rate (percentage of ordered units that were fulfilled)
    - return_percentage (percentage of ordered units returned)
    - stock_status (in_stock/out_of_stock/low_stock)
    """
    try:
        user_id = int(current_user.id)
    except Exception:
        user_id = current_user.id

    db_user = await __import__("app.crud.crud_user", fromlist=["get_user"]).get_user(db, user_id)
    if not db_user or db_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only admins may view product performance")

    # Resolve vendor account -> legacy vendor id
    vendor_account_q = await db.execute(select(VendorAccount).where(VendorAccount.id == vendor_id))
    vendor_account = vendor_account_q.scalars().first()
    if not vendor_account:
        raise HTTPException(status_code=404, detail="Vendor account not found")

    vendor_legacy_q = await db.execute(select(Vendor).where(Vendor.contact_email == vendor_account.email))
    vendor_legacy = vendor_legacy_q.scalars().first()
    if not vendor_legacy:
        return []

    # statuses considered NOT fulfilled
    not_fulfilled_statuses = ["cancelled", "pending", "failed"]

    # Aggregate per product
    q = select(
        Product.id.label("product_id"),
        Product.name.label("product_name"),
        Category.category_name.label("category"),
        func.coalesce(func.sum(OrderItem.quantity), 0).label("total_ordered"),
        func.coalesce(func.sum(case((Order.status.in_(not_fulfilled_statuses), 0), else_=OrderItem.quantity)), 0).label("fulfilled_units"),
        func.coalesce(func.sum(case((Order.status == 'returned', OrderItem.quantity), else_=0)), 0).label("returned_units"),
        func.coalesce(func.sum(Inventory.quantity), 0).label("stock_qty"),
    ).select_from(Product)
    q = q.join(Category, Category.id == Product.category_id, isouter=True)
    q = q.outerjoin(Inventory, Inventory.product_id == Product.id)
    q = q.outerjoin(OrderItem, OrderItem.product_id == Product.id)
    q = q.outerjoin(Order, Order.id == OrderItem.order_id)
    q = q.where(Product.vendor_id == vendor_legacy.id)
    q = q.group_by(Product.id, Product.name, Category.category_name)

    res = await db.execute(q)
    rows = res.all()

    out = []
    for r in rows:
        total_ordered = int(r.total_ordered or 0)
        fulfilled_units = int(r.fulfilled_units or 0)
        returned_units = int(r.returned_units or 0)
        stock_qty = int(r.stock_qty or 0)

        sales = fulfilled_units
        fulfillment_rate = round((fulfilled_units / total_ordered) * 100, 2) if total_ordered > 0 else 0.0
        return_percentage = round((returned_units / total_ordered) * 100, 2) if total_ordered > 0 else 0.0

        if stock_qty > 10:
            stock_status = "in_stock"
        elif stock_qty > 0:
            stock_status = "low_stock"
        else:
            stock_status = "out_of_stock"

        out.append({
            "product_name": r.product_name,
            "category": r.category,
            "sales": sales,
            "fulfillment_rate": fulfillment_rate,
            "return_percentage": return_percentage,
            "stock_status": stock_status,
        })

    return out


@router.get("/id/{vendor_id}/alerts")
async def admin_get_vendor_alerts(vendor_id: UUID, current_user = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    """Return operational alerts for a vendor.

    Each alert contains: alert_type, message, created_at
    """
    try:
        user_id = int(current_user.id)
    except Exception:
        user_id = current_user.id

    db_user = await __import__("app.crud.crud_user", fromlist=["get_user"]).get_user(db, user_id)
    if not db_user or db_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only admins may view vendor alerts")

    # Verify vendor exists
    vendor_q = await db.execute(select(VendorAccount).where(VendorAccount.id == vendor_id))
    vendor = vendor_q.scalars().first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    alerts_q = await db.execute(select(VendorAlert).where(VendorAlert.vendor_id == vendor.id).order_by(VendorAlert.created_at.desc()))
    alerts = alerts_q.scalars().all()

    out = []
    for a in alerts:
        out.append({
            "alert_type": a.alert_type,
            "message": a.message,
            "created_at": a.created_at,
        })

    return out


@router.get("/performance")
async def admin_vendors_performance(current_user = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    """Return vendor performance overview.

    Metrics returned per vendor:
    - vendor_id
    - vendor_name
    - status
    - accept_rate (percentage)
    - sla_percentage (null if not computable)
    - return_rate (percentage)
    - rating (placeholder / 0 if no reviews table)
    - tier (gold/silver/bronze)
    - performance_score (0-100)

    Notes/assumptions:
    - Accept rate is computed as (accepted_orders / total_orders) * 100.
      Orders with status in ("cancelled","pending","returned","failed") are treated as NOT accepted.
    - Return rate is (returned_orders / total_orders) * 100 where returned_orders are orders with status == 'returned'.
    - SLA percentage isn't computable from existing models (no delivery timestamps); returns null.
    - Rating is not available in current schema; returned as 0.0 placeholder.
    - performance_score is a weighted combination of accept_rate and return_rate and rating.
    """
    try:
        user_id = int(current_user.id)
    except Exception:
        user_id = current_user.id

    db_user = await __import__("app.crud.crud_user", fromlist=["get_user"]).get_user(db, user_id)
    if not db_user or db_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only admins may view vendor performance")

    # Join VendorAccount -> Product -> OrderItem -> Order and aggregate
    # Use DISTINCT on Order.id to avoid double-counting when multiple items per order
    accepted_excluded = ["cancelled", "pending", "returned", "failed"]

    q = select(
        VendorAccount.id.label("vendor_id"),
        VendorAccount.business_name.label("vendor_name"),
        VendorAccount.status.label("status"),
        func.count(func.distinct(Order.id)).label("total_orders"),
        func.sum(case((Order.status.in_(accepted_excluded), 0), else_=1)).label("accepted_orders"),
        func.sum(case((Order.status == 'returned', 1), else_=0)).label("returned_orders"),
    ).select_from(VendorAccount)
    q = q.join(Product, Product.vendor_id == VendorAccount.id, isouter=True).join(OrderItem, OrderItem.product_id == Product.id, isouter=True).join(Order, Order.id == OrderItem.order_id, isouter=True)
    q = q.group_by(VendorAccount.id, VendorAccount.business_name, VendorAccount.status)

    res = await db.execute(q)
    rows = res.all()

    out = []
    for r in rows:
        total_orders = int(r.total_orders or 0)
        accepted_orders = int(r.accepted_orders or 0)
        returned_orders = int(r.returned_orders or 0)

        if total_orders > 0:
            accept_rate = (accepted_orders / total_orders) * 100
            return_rate = (returned_orders / total_orders) * 100
        else:
            accept_rate = 0.0
            return_rate = 0.0

        # SLA not available from schema
        sla_percentage = None

        # Rating not available; placeholder
        rating = 0.0

        # Simple performance score: weighted (accept_rate 60%, (100-return_rate) 30%, rating(0-100) 10%)
        performance_score = (accept_rate * 0.6) + ((100 - return_rate) * 0.3) + (rating * 0.1)
        # Clamp
        performance_score = max(0.0, min(100.0, performance_score))

        # Tiering
        if performance_score >= 85:
            tier = "gold"
        elif performance_score >= 70:
            tier = "silver"
        else:
            tier = "bronze"

        out.append({
            "vendor_id": str(r.vendor_id),
            "vendor_name": r.vendor_name,
            "status": r.status.value if hasattr(r.status, 'value') else str(r.status),
            "accept_rate": round(accept_rate, 2),
            "sla_percentage": sla_percentage,
            "return_rate": round(return_rate, 2),
            "rating": round(rating, 2),
            "tier": tier,
            "performance_score": round(performance_score, 2),
        })

    return out


@router.get("/pending")
async def admin_pending_vendors(current_user = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    """Return vendors pending approval with document status."""
    try:
        user_id = int(current_user.id)
    except Exception:
        user_id = current_user.id

    db_user = await __import__("app.crud.crud_user", fromlist=["get_user"]).get_user(db, user_id)
    if not db_user or db_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only admins may view pending vendors")
    # Simpler, more reliable implementation:
    # 1) Query pending vendor accounts
    # 2) For each vendor, check existence of each document type
    res = await db.execute(
        select(VendorAccount).where(and_(VendorAccount.status == VendorStatus.PENDING, VendorAccount.is_kyc_verified == False))
    )
    vendors = res.scalars().all()

    out = []
    for v in vendors:
        # Check documents presence per type
        pan_q = select(func.count()).select_from(VendorKYCDocument).where(and_(VendorKYCDocument.vendor_id == v.id, VendorKYCDocument.document_type == DocumentType.PAN))
        gst_q = select(func.count()).select_from(VendorKYCDocument).where(and_(VendorKYCDocument.vendor_id == v.id, VendorKYCDocument.document_type == DocumentType.GST))
        lic_q = select(func.count()).select_from(VendorKYCDocument).where(and_(VendorKYCDocument.vendor_id == v.id, VendorKYCDocument.document_type == DocumentType.LICENSE))

        pan_res = await db.execute(pan_q)
        gst_res = await db.execute(gst_q)
        lic_res = await db.execute(lic_q)

        has_pan = bool(pan_res.scalar() or 0)
        has_gst = bool(gst_res.scalar() or 0)
        has_license = bool(lic_res.scalar() or 0)

        docs_status = {"PAN": has_pan, "GST": has_gst, "LICENSE": has_license}

        out.append({
            "vendor_id": str(v.id),
            "business_name": v.business_name,
            "business_type": getattr(v, "business_type", None),
            "contact_person": v.owner_name,
            "phone": v.phone_number,
            "email": v.email,
            "submitted_date": v.created_at,
            "documents_status": docs_status,
        })

    return out


@router.get("/id/{vendor_id}")
async def admin_get_vendor_details(vendor_id: UUID, current_user = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    """Return complete vendor details for admin review.

    Includes business information, contact details, address, GST/PAN, bank details,
    and current status & verification metadata.
    """
    try:
        user_id = int(current_user.id)
    except Exception:
        user_id = current_user.id

    db_user = await __import__("app.crud.crud_user", fromlist=["get_user"]).get_user(db, user_id)
    if not db_user or db_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only admins may view vendor details")

    vendor = await db.execute(select(VendorAccount).where(VendorAccount.id == vendor_id))
    vendor = vendor.scalars().first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    # fetch uploaded documents
    docs_q = await db.execute(select(VendorKYCDocument).where(VendorKYCDocument.vendor_id == vendor.id))
    docs = docs_q.scalars().all()
    doc_list = []
    for d in docs:
        doc_list.append({
            "document_type": d.document_type.name if hasattr(d.document_type, 'name') else str(d.document_type),
            "document_url": d.document_url,
            "uploaded_at": d.uploaded_at if hasattr(d, 'uploaded_at') else None,
        })

    return {
        "vendor_id": str(vendor.id),
        "business_name": vendor.business_name,
        "business_type": vendor.business_type,
        "contact_person": vendor.owner_name,
        "phone": vendor.phone_number,
        "email": vendor.email,
        "business_address": vendor.business_address,
        "gst_number": vendor.gst_number,
        "pan_number": vendor.pan_number,
        "bank_name": vendor.bank_name,
        "account_number": vendor.bank_account_number,
        "ifsc_code": vendor.ifsc_code,
        "status": vendor.status.value if hasattr(vendor.status, 'value') else str(vendor.status),
        "is_kyc_verified": vendor.is_kyc_verified,
        "verification_timestamp": vendor.verification_timestamp,
        "kyc_rejection_reason": vendor.kyc_rejection_reason,
        "created_at": vendor.created_at,
        "updated_at": vendor.updated_at,
        "kyc_documents": doc_list,
    }
