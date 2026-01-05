import time
from jose import jwt
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings


def make_token():
    payload = {"sub": "1", "role": "admin", "exp": int(time.time()) + 3600}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def test_weekly_sales_fallback_structure():
    """Ensure endpoint returns the expected weekly structure (works in sqlite/dev)."""
    client = TestClient(app)
    token = make_token()
    resp = client.get(
        "/reports/weekly-sales?tz=UTC&include_totals=true",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    data = resp.json()
    # Basic shape checks
    assert "week_start" in data
    assert "week_end" in data
    assert data.get("labels") == ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    assert isinstance(data.get("per_day"), list) and len(data.get("per_day")) == 7
    # Ensure datasets exist
    ds = data.get("datasets")
    assert "sales" in ds and "earnings" in ds and "orders" in ds
    # Totals exist when include_totals=true
    assert "totals" in data
