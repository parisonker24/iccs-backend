from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_weekly_summary(
    db: AsyncSession,
    week_start_date: str,
    tz: str = "UTC",
    status: str = "completed",
    vendor_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Return aggregated rows for each day in the 7-day window starting at `week_start_date`.

    The function returns rows with columns: date, day_label, total_sales, total_earnings, orders_count
    Uses Postgres `generate_series` in a single, efficient query.

    Parameters:
    - db: AsyncSession
    - week_start_date: ISO date string (YYYY-MM-DD) representing the start (inclusive)
    - tz: timezone used for grouping (client timezone)
    - status: order status filter
    - vendor_id: optional vendor filter
    """

    vendor_clause = "AND vendor_id = :vendor_id" if vendor_id is not None else ""

    sql = f"""
    WITH params AS (
      SELECT :week_start::date AS wstart, :tz::text AS tz
    ),
    days AS (
      SELECT generate_series(wstart, wstart + INTERVAL '6 days', INTERVAL '1 day')::date AS day FROM params
    ),
    agg AS (
      SELECT
        (created_at AT TIME ZONE 'UTC' AT TIME ZONE params.tz)::date AS day,
        SUM(total_amount)::numeric(20,2) AS total_sales,
        SUM(COALESCE(vendor_earning, total_amount))::numeric(20,2) AS total_earnings,
        COUNT(*)::int AS orders_count
      FROM orders, params
      WHERE (created_at AT TIME ZONE 'UTC' AT TIME ZONE params.tz)::date BETWEEN params.wstart AND (params.wstart + INTERVAL '6 days')
        AND status = :status
        {vendor_clause}
      GROUP BY day
    )
    SELECT to_char(d.day, 'YYYY-MM-DD') AS date, to_char(d.day, 'Dy') AS day_label,
      COALESCE(a.total_sales, 0) AS total_sales, COALESCE(a.total_earnings, 0) AS total_earnings, COALESCE(a.orders_count, 0) AS orders_count
    FROM days d
    LEFT JOIN agg a USING (day)
    ORDER BY d.day
    """

    params = {"week_start": week_start_date, "tz": tz, "status": status}
    if vendor_id is not None:
        params["vendor_id"] = vendor_id

    result = await db.execute(text(sql), params)
    rows = result.fetchall()

    # Map rows into a list of dicts
    out = []
    for r in rows:
        out.append(
            {
                "date": r[0],
                "day": r[1],
                "total_sales": float(r[2]) if r[2] is not None else 0.0,
                "total_earnings": float(r[3]) if r[3] is not None else 0.0,
                "orders_count": int(r[4]) if r[4] is not None else 0,
            }
        )

    return out
