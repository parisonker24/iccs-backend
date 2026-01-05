from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.config import settings
from app.core.security import oauth2_scheme, decode_access_token, get_token_from_request
from app.core import redis as cache
import json
from datetime import time as dt_time

router = APIRouter()


@router.get("/weekly-sales")
async def weekly_sales_report(
    week_start: Optional[str] = Query(None, description="YYYY-MM-DD for the week's Monday"),
    tz: str = Query("UTC", description="Timezone for grouping, e.g. 'UTC' or 'America/Los_Angeles'"),
    status: str = Query("completed", description="Order status to include"),
    include_totals: bool = Query(True, description="Include weekly totals"),
    vendor_id: Optional[int] = Query(None, description="(Admin only) filter for a specific vendor id"),
    # Accept token from header/cookie/query for development convenience.
    # `get_token_from_request` will look in Authorization header, `access_token` cookie, or `token` query param.
    token: str = Depends(get_token_from_request),
    db: AsyncSession = Depends(get_db),
):
    """Return a Mon->Sun weekly sales summary suitable for dashboard charts.

    Role enforcement:
    - Vendor: restricted to the vendor id in the token (uses `sub` if numeric)
    - Admin: allowed to view all vendors; may optionally pass `vendor_id` to filter
    """

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    role = payload.get("role")
    token_sub = payload.get("sub") or payload.get("user_id")

    # Determine vendor scope
    vendor_filter_id = None
    if role == "vendor":
        try:
            vendor_filter_id = int(token_sub)
        except Exception:
            vendor_filter_id = token_sub
    else:
        # admin or other role: honor optional vendor_id param
        if vendor_id is not None:
            vendor_filter_id = vendor_id

    # Determine week_start (Monday) in the requested tz
    try:
        z = ZoneInfo(tz)
    except Exception:
        # zoneinfo may be unavailable on some Windows setups without the
        # `tzdata` package. Fall back to UTC using the stdlib timezone
        # object so the endpoint remains usable in those environments.
        try:
            z = ZoneInfo("UTC")
        except Exception:
            import datetime as _dt

            z = _dt.timezone.utc

    if week_start:
        try:
            week_start_date = datetime.fromisoformat(week_start).date()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid week_start format; use YYYY-MM-DD")
    else:
        today = datetime.now(z).date()
        week_start_date = today - timedelta(days=today.weekday())

    # Raw SQL using generate_series to ensure zero-days are returned
    vendor_clause = "AND vendor_id = :vendor_id" if vendor_filter_id is not None else ""

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

    params = {"week_start": week_start_date.isoformat(), "tz": tz, "status": status}
    if vendor_filter_id is not None:
        params["vendor_id"] = vendor_filter_id

    # Try to read from cache first (short TTL). Key includes week_start,tz,status and vendor scope.
    cache_key_parts = [
        "reports:weekly",
        params["week_start"],
        params["tz"],
        params["status"],
        str(params.get("vendor_id", "all")),
    ]
    cache_key = ":".join(cache_key_parts)

    rows = None
    try:
        if getattr(cache, "_redis_available", False) and cache.redis_client:
            cached = cache.redis_client.get(cache_key)
            if cached:
                # cached is JSON encoded response dict; return it directly
                return json.loads(cached)
    except Exception:
        # Fail silently and compute fresh result
        pass

    try:
        # If running against SQLite (common for local dev/tests) the
        # Postgres-specific SQL above will fail. Provide a pure-Python
        # fallback that queries a simple range of orders and aggregates
        # per-day in the requested timezone. This makes the endpoint
        # usable whether the app uses Postgres or SQLite.
        is_sqlite_url = bool(settings.DATABASE_URL and settings.DATABASE_URL.startswith("sqlite"))
        if is_sqlite_url:
            # Compute UTC window that covers the requested local week
            # Start of local week at 00:00 of week_start_date in `tz` -> to UTC
            try:
                local_zone = ZoneInfo(tz)
            except Exception:
                try:
                    local_zone = ZoneInfo("UTC")
                except Exception:
                    import datetime as _dt

                    local_zone = _dt.timezone.utc

            local_week_start = datetime.combine(week_start_date, dt_time(0, 0), tzinfo=local_zone)
            utc_week_start = local_week_start.astimezone(ZoneInfo("UTC"))
            utc_week_end = utc_week_start + timedelta(days=7)

            q = text(
                """
                SELECT created_at, total_amount, COALESCE(vendor_earning, total_amount) AS vendor_earning
                FROM orders
                WHERE created_at >= :start_utc AND created_at < :end_utc AND status = :status
                """
            )
            result = await db.execute(q, {"start_utc": utc_week_start.isoformat(), "end_utc": utc_week_end.isoformat(), "status": status})
            raw_rows = result.fetchall()

            # Build a map of date_str -> aggregated values
            agg_map = {}
            for r in raw_rows:
                created_at = r[0]
                total_amount = r[1] or 0
                vendor_earning = r[2] or total_amount

                # Normalize created_at to a datetime with UTC tzinfo if naive
                if isinstance(created_at, str):
                    try:
                        created_dt = datetime.fromisoformat(created_at)
                    except Exception:
                        # Fallback: try removing Z
                        created_dt = datetime.fromisoformat(created_at.rstrip("Z"))
                else:
                    created_dt = created_at

                if created_dt.tzinfo is None:
                    try:
                        created_dt = created_dt.replace(tzinfo=ZoneInfo("UTC"))
                    except Exception:
                        import datetime as _dt

                        created_dt = created_dt.replace(tzinfo=_dt.timezone.utc)

                # Convert to requested local tz and take the date
                local_dt = created_dt.astimezone(local_zone)
                day_key = local_dt.date().isoformat()

                ent = agg_map.setdefault(day_key, {"sales": 0.0, "earnings": 0.0, "orders": 0})
                ent["sales"] += float(total_amount)
                ent["earnings"] += float(vendor_earning)
                ent["orders"] += 1

            # Build rows in the same shape as the Postgres query would return
            rows = []
            for i in range(7):
                d = week_start_date + timedelta(days=i)
                ds = d.isoformat()
                ent = agg_map.get(ds, {"sales": 0.0, "earnings": 0.0, "orders": 0})
                rows.append((ds, d.strftime("%a"), round(ent["sales"], 2), round(ent["earnings"], 2), ent["orders"]))
        else:
            result = await db.execute(text(sql), params)
            rows = result.fetchall()
    except Exception as e:
        # If the Postgres-specific SQL fails (or we're running on SQLite),
        # attempt a pure-Python fallback aggregation. This provides a more
        # resilient endpoint that works in dev (sqlite) and in environments
        # where the fancy SQL might not be allowed or fails for some reason.
        err_msg = str(e)
        is_sqlite_url = bool(settings.DATABASE_URL and settings.DATABASE_URL.startswith("sqlite"))
        should_attempt_fallback = is_sqlite_url or any(tok in err_msg for tok in ("generate_series", "AT TIME ZONE", "INTERVAL"))

        if should_attempt_fallback:
            try:
                # Reuse the same fallback logic as the sqlite branch above.
                try:
                    local_zone = ZoneInfo(tz)
                except Exception:
                    try:
                        local_zone = ZoneInfo("UTC")
                    except Exception:
                        import datetime as _dt

                        local_zone = _dt.timezone.utc

                local_week_start = datetime.combine(week_start_date, dt_time(0, 0), tzinfo=local_zone)
                try:
                    utc_week_start = local_week_start.astimezone(ZoneInfo("UTC"))
                except Exception:
                    import datetime as _dt

                    utc_week_start = local_week_start.astimezone(_dt.timezone.utc)

                utc_week_end = utc_week_start + timedelta(days=7)

                q = text(
                    """
                    SELECT created_at, total_amount, COALESCE(vendor_earning, total_amount) AS vendor_earning
                    FROM orders
                    WHERE created_at >= :start_utc AND created_at < :end_utc AND status = :status
                    """
                )
                result = await db.execute(q, {"start_utc": utc_week_start.isoformat(), "end_utc": utc_week_end.isoformat(), "status": status})
                raw_rows = result.fetchall()

                agg_map = {}
                for r in raw_rows:
                    created_at = r[0]
                    total_amount = r[1] or 0
                    vendor_earning = r[2] or total_amount

                    if isinstance(created_at, str):
                        try:
                            created_dt = datetime.fromisoformat(created_at)
                        except Exception:
                            created_dt = datetime.fromisoformat(created_at.rstrip("Z"))
                    else:
                        created_dt = created_at

                    if created_dt.tzinfo is None:
                        try:
                            created_dt = created_dt.replace(tzinfo=ZoneInfo("UTC"))
                        except Exception:
                            import datetime as _dt

                            created_dt = created_dt.replace(tzinfo=_dt.timezone.utc)

                    local_dt = created_dt.astimezone(local_zone)
                    day_key = local_dt.date().isoformat()

                    ent = agg_map.setdefault(day_key, {"sales": 0.0, "earnings": 0.0, "orders": 0})
                    ent["sales"] += float(total_amount)
                    ent["earnings"] += float(vendor_earning)
                    ent["orders"] += 1

                rows = []
                for i in range(7):
                    d = week_start_date + timedelta(days=i)
                    ds = d.isoformat()
                    ent = agg_map.get(ds, {"sales": 0.0, "earnings": 0.0, "orders": 0})
                    rows.append((ds, d.strftime("%a"), round(ent["sales"], 2), round(ent["earnings"], 2), ent["orders"]))
            except Exception:
                # If fallback also fails (missing table, permission issues, etc.),
                # return an empty weekly series (zeroed totals) rather than
                # propagating a 500/501. This keeps the dashboard UI stable in
                # dev environments where the orders table may be absent.
                rows = []
                for i in range(7):
                    d = week_start_date + timedelta(days=i)
                    ds = d.isoformat()
                    rows.append((ds, d.strftime("%a"), 0.0, 0.0, 0))
        else:
            # Other unexpected DB errors: return a 500 with the DB error message to aid debugging.
            raise HTTPException(status_code=500, detail=f"Database error: {err_msg}")

    labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    per_day = []
    sales = []
    earnings = []
    orders = []

    for r in rows:
        date_str = r[0]
        day_label = r[1]
        total_sales = float(r[2]) if r[2] is not None else 0.0
        total_earnings = float(r[3]) if r[3] is not None else 0.0
        orders_count = int(r[4]) if r[4] is not None else 0

        per_day.append({
            "date": date_str,
            "day": day_label,
            "total_sales": round(total_sales, 2),
            "total_earnings": round(total_earnings, 2),
            "orders_count": orders_count,
        })

        sales.append(round(total_sales, 2))
        earnings.append(round(total_earnings, 2))
        orders.append(orders_count)

    resp = {
        "week_start": week_start_date.isoformat(),
        "week_end": (week_start_date + timedelta(days=6)).isoformat(),
        "labels": labels,
        "per_day": per_day,
        "datasets": {
            "sales": sales,
            "earnings": earnings,
            "orders": orders,
        },
    }

    if include_totals:
        resp["totals"] = {
            "week_total_sales": round(sum(sales), 2),
            "week_total_earnings": round(sum(earnings), 2),
            "week_orders_count": sum(orders),
        }

    # Set cache with short TTL (e.g., 120 seconds) to improve dashboard responsiveness.
    try:
        if getattr(cache, "_redis_available", False) and cache.redis_client:
            cache.redis_client.setex(cache_key, 120, json.dumps(resp))
    except Exception:
        pass

    return resp
