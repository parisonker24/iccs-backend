from dotenv import load_dotenv
load_dotenv()  # First thing after imports

import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi import HTTPException
import sqlalchemy

from app.schemas.routers.auth import router as auth_router
from app.schemas.routers.user import router as user_router
from app.schemas.routers.vendor import router as vendor_router
from app.schemas.routers.vendor_register import router as vendor_register_router
from app.schemas.routers.vendor_kyc import router as vendor_kyc_router
from app.schemas.routers.admin_vendor_kyc import router as admin_vendor_kyc_router
try:
    from app.schemas.routers.upload_kyc import router as kyc_upload_router
except Exception as e:  # pragma: no cover - optional dependency (python-multipart)
    kyc_upload_router = None
    print(f"Skipping upload_kyc router (missing dependency?): {e}")
import time
from app.schemas.routers.category import router as category_router
from app.schemas.routers.subcategory import router as subcategory_router
from app.schemas.routers.product import router as product_router
from app.schemas.routers.inventory import router as inventory_router
from app.schemas.routers.order import router as order_router
from app.schemas.routers.reports import router as reports_router
from app.schemas.routers.dashboard import router as dashboard_router

# FastAPI App
app = FastAPI(
    title="ICCS Backend",
    description="E-commerce Backend for Stationery System",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded files from the `uploads` directory at the `/uploads` path.
# Ensure the `uploads/kyc_docs` folder exists so uploads can be saved.
ROOT_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = ROOT_DIR / "uploads"
KYCDIR = UPLOADS_DIR / "kyc_docs"
KYCDIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # If the exception is an HTTPException, preserve its status code and detail
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    # Otherwise, log and return a 500 generic response
    print(f"500 Internal Server Error: {exc}")
    import traceback
    traceback.print_exc()

    # Provide a clearer message when the database schema is not prepared
    err_text = str(exc)
    if "UndefinedTableError" in err_text or isinstance(exc, sqlalchemy.exc.ProgrammingError):
        return JSONResponse(
            status_code=500,
            content={
                "detail": (
                    "Database table missing or migrations not applied. "
                    "Run migrations (e.g. `alembic upgrade head`) or run `python create_tables.py` to create tables."
                )
            },
        )

    # Include exception text in the response to help debugging during development.
    # In production you may want to hide this detail.
    return JSONResponse(status_code=500, content={"detail": str(exc)})
# Include Routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(user_router, prefix="/users", tags=["users"])

app.include_router(vendor_router, prefix="/vendors", tags=["vendors"])
app.include_router(vendor_register_router, prefix="/vendors", tags=["vendors"])
app.include_router(vendor_kyc_router, prefix="/vendors", tags=["vendors"])
app.include_router(admin_vendor_kyc_router, prefix="/admin/vendors", tags=["admin-vendors"])
if kyc_upload_router is not None:
    app.include_router(kyc_upload_router, prefix="", tags=["uploads"])
else:
    # upload routes require `python-multipart`; skip if not available
    pass
app.include_router(category_router, prefix="/categories", tags=["categories"])
app.include_router(subcategory_router, prefix="/subcategories", tags=["subcategories"])
app.include_router(product_router, prefix="/products", tags=["products"])
app.include_router(inventory_router, prefix="/inventory", tags=["inventory"])
app.include_router(order_router, prefix="/orders", tags=["orders"])
app.include_router(reports_router, prefix="/reports", tags=["reports"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])

# Root Route
@app.get("/")
def read_root():
    return {"message": "ICCS Backend Running Successfully 🚀"}

# ------------------------------------------------------------
#  CUSTOM OPENAPI SCHEMA FOR JWT AUTH IN SWAGGER
# ------------------------------------------------------------
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    # Add security schemes: keep a simple Bearer scheme for manual entry
    # and add an OAuth2 password flow so Swagger UI can perform login
    # against `/auth/login` and automatically attach the token.
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        },
        "OAuth2Password": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/auth/token",
                    "scopes": {}
                }
            }
        }
    }

    # Apply OAuth2Password to all routes so Swagger UI's "Authorize" can
    # call the token endpoint and attach the access token to requests.
    for path in openapi_schema["paths"].values():
        for method in path.values():
            if "security" not in method:
                method["security"] = [{"OAuth2Password": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

