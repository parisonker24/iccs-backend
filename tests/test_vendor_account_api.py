from fastapi.testclient import TestClient
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import pytest

from app.main import app

client = TestClient(app)


def make_vendor_obj():
    return SimpleNamespace(
        id="8f14e45f-ea1a-4c3f-9c6f-1234567890ab",
        business_name="Test Business",
        owner_name="Owner",
        email="vendor@example.com",
        phone_number="1234567890",
        business_address="Addr",
        gst_number=None,
        pan_number=None,
        is_kyc_verified=False,
        status="PENDING",
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )


def test_register_success():
    payload = {
        "business_name": "Test Business",
        "owner_name": "Owner",
        "email": "vendor@example.com",
        "phone_number": "1234567890",
        "password": "strongpassword",
    }

    # Patch async DB helpers used by the router to avoid touching a real DB
    with patch("app.schemas.routers.vendor_register.get_vendor_by_email", new_callable=AsyncMock) as mock_get_email, \
         patch("app.schemas.routers.vendor_register.get_vendor_by_phone", new_callable=AsyncMock) as mock_get_phone, \
         patch("app.schemas.routers.vendor_register.create_vendor_account", new_callable=AsyncMock) as mock_create:
        mock_get_email.return_value = None
        mock_get_phone.return_value = None
        mock_create.return_value = make_vendor_obj()

        resp = client.post("/vendors/register", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == payload["email"]
        assert data["business_name"] == payload["business_name"]


def test_register_conflict_email():
    payload = {
        "business_name": "Test Business",
        "owner_name": "Owner",
        "email": "vendor@example.com",
        "phone_number": "1234567890",
        "password": "strongpassword",
    }

    with patch("app.schemas.routers.vendor_register.get_vendor_by_email", new_callable=AsyncMock) as mock_get_email:
        mock_get_email.return_value = True
        resp = client.post("/vendors/register", json=payload)
        assert resp.status_code == 400
        assert "Email already registered" in resp.json().get("detail", "")


def test_create_vendor_endpoint_success():
    payload = {
        "business_name": "Admin Created",
        "owner_name": "Admin Owner",
        "email": "admin-vendor@example.com",
        "phone_number": "0987654321",
        "password": "anotherstrongpassword",
    }

    with patch("app.schemas.routers.vendor.create_vendor_account", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = make_vendor_obj()
        resp = client.post("/vendors/", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["business_name"] == payload["business_name"]


def test_read_vendor_not_found():
    with patch("app.schemas.routers.vendor.get_vendor_by_id", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        resp = client.get("/vendors/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


def test_read_vendor_success():
    with patch("app.schemas.routers.vendor.get_vendor_by_id", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = make_vendor_obj()
        resp = client.get("/vendors/8f14e45f-ea1a-4c3f-9c6f-1234567890ab")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "8f14e45f-ea1a-4c3f-9c6f-1234567890ab"
        assert data["business_name"] == "Test Business"
