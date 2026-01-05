from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import decode_access_token, oauth2_scheme
from app.schemas.dashboard_schemas import WeeklySummaryResponse, PerDayItem, Datasets, Totals
from app.services.dashboard_service import get_weekly_summary

router = APIRouter()


async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

    # Expect token to include 'sub' (user id) and 'role' (admin/vendor)
    user = {
        "id": payload.get("sub") or payload.get("user_id"),
        "role": payload.get("role"),
    }
    return user


@router.get("/weekly-summary", response_model=WeeklySummaryResponse)
async def weekly_summary(
    tz: str = Query("UTC", description="Timezone for grouping, e.g. 'UTC' or 'America/Los_Angeles'"),
    status: str = Query("completed", description="Order status to include"),
    token_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    GET /api/dashboard/weekly-summary

    - Admin: sees global summary
    - Vendor: sees their own data (vendor id derived from token `sub`)
    - Uses last 7 days automatically (today and previous 6 days)
    """

    try:
        role = token_user.get("role")
        user_id = token_user.get("id")

        # Determine vendor scope: if vendor role, restrict to their id
        vendor_filter = None
        if role == "vendor":
            try:
                vendor_filter = int(user_id)
            except Exception:
                # fallback: leave as-is
                vendor_filter = user_id

        # compute last 7 days (start inclusive)
        # Use server-local time in requested timezone for day boundaries
        # For deterministic grouping, let service use the week_start ISO date
        from zoneinfo import ZoneInfo

        try:
            tzinfo = ZoneInfo(tz)
        except Exception:
            tzinfo = ZoneInfo("UTC")

        today = datetime.now(tzinfo).date()
        week_start_date = (today - timedelta(days=6)).isoformat()
        week_end_date = today.isoformat()

        rows = await get_weekly_summary(db=db, week_start_date=week_start_date, tz=tz, status=status, vendor_id=vendor_filter)

        labels = ["Day"]
        # Build labels Mon..Sun? Since we're returning last 7 days, labels should be the short day labels in order
        labels = [r["day"] for r in rows]

        per_day = [
            PerDayItem(
                date=r["date"],
                day=r["day"],
                total_sales=round(r["total_sales"], 2),
                total_earnings=round(r["total_earnings"], 2),
                orders_count=r["orders_count"],
            )
            for r in rows
        ]

        sales = [item.total_sales for item in per_day]
        earnings = [item.total_earnings for item in per_day]
        orders = [item.orders_count for item in per_day]

        totals = Totals(week_total_sales=round(sum(sales), 2), week_total_earnings=round(sum(earnings), 2), week_orders_count=sum(orders))

        resp = WeeklySummaryResponse(
            week_start=week_start_date,
            week_end=week_end_date,
            labels=labels,
            per_day=per_day,
            datasets=Datasets(sales=sales, earnings=earnings, orders=orders),
            totals=totals,
        )

        return resp

    except HTTPException:
        raise
    except Exception as exc:
        # Log exception in production code; return generic 500 to clients
        raise HTTPException(status_code=500, detail="Failed to compute weekly summary")
