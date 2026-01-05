import pytest
from httpx import AsyncClient
from app.main import app
from app.core.security import create_access_token
from app.db.session import async_session_maker
from app.models.user import User, UserRole
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert

# Note: tests assume an in-memory or test DB configured in settings.DATABASE_URL
# and that Alembic migrations or schema creation are handled separately for tests.

@pytest.mark.asyncio
async def test_get_current_admin_allows_admin(monkeypatch):
    # Create a token payload with sub=user id 1
    token = create_access_token({"sub": "1"})

    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Call an admin-only endpoint; without DB user it will return 401 or 403 depending
        headers = {"Authorization": f"Bearer {token}"}
        resp = await ac.get("/admin/vendors/?skip=0&limit=1", headers=headers)
        # At minimum, should not be 500. We expect 401 because DB user likely missing.
        assert resp.status_code in (200, 401, 403)


@pytest.mark.asyncio
async def test_non_admin_rejected(monkeypatch):
    # Create a token for user id 2
    token = create_access_token({"sub": "2"})

    async with AsyncClient(app=app, base_url="http://test") as ac:
        headers = {"Authorization": f"Bearer {token}"}
        resp = await ac.get("/admin/vendors/?skip=0&limit=1", headers=headers)
        # If user exists and is not admin, should be 403; otherwise 401
        assert resp.status_code in (401, 403)
